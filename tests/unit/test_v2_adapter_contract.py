from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from apsla.models import AnalysisResult
from apsla.models_v2 import AnalysisResultV2, adapt_analysis_result, result_matches_source
from apsla.pipeline import Analyzer
from apsla.server import tool_runner
from apsla.server.tool_runner import ToolStatus, detect_tool, execute_static_tool

FIXTURE_SOURCES = sorted(
    path
    for suffix in ("*.py", "*.java", "*.js", "*.cpp")
    for path in (Path(__file__).parents[1] / "fixtures").rglob(suffix)
)


def test_v2_schema_round_trip_and_hash_validation() -> None:
    source = "x = 'ok'\n"
    legacy = Analyzer().analyze(source, language="python", options={"fixes": False, "ml": False})
    v2 = adapt_analysis_result(
        source,
        legacy,
        7,
        plugin=__import__("apsla.languages.registry", fromlist=["get"]).get("python"),
        elapsed_ms=0.25,
    )
    restored = AnalysisResultV2.model_validate_json(v2.model_dump_json())
    assert restored.model_dump() == v2.model_dump()
    assert restored.source_hash == hashlib.sha256(source.encode()).hexdigest()
    assert restored.source_version == 7
    assert restored.timing["total_ms"] == 0.25
    with pytest.raises(ValidationError):
        AnalysisResultV2.model_validate({**v2.model_dump(), "source_hash": "not-a-sha256"})


def test_offsets_are_available_in_utf16_and_codepoints() -> None:
    source = "emoji = '😀'\n"
    legacy = Analyzer().analyze(source, language="python", options={"fixes": False, "ml": False})
    from apsla.languages import registry

    adapted = adapt_analysis_result(source, legacy, 1, plugin=registry.get("python"))
    emoji = next(token for token in adapted.tokens if "😀" in token.lexeme)
    assert emoji.start_offset == emoji.start_offset_codepoint
    assert (
        emoji.end_offset - emoji.start_offset
        == emoji.end_offset_codepoint - emoji.start_offset_codepoint + 1
    )
    assert emoji.start_line == 1 and emoji.start_column >= 1


def test_adapter_does_not_mutate_or_change_legacy_response() -> None:
    source = "value = input()\neval(value)\n"
    old = Analyzer().analyze(source, language="python", options={"fixes": False, "ml": False})
    before = old.model_dump()
    from apsla.languages import registry

    adapted = adapt_analysis_result(source, old, 3, plugin=registry.get("python"))
    assert old.model_dump() == before
    from fastapi.encoders import jsonable_encoder

    assert jsonable_encoder(old) == old.model_dump(mode="json")
    assert isinstance(adapted, AnalysisResultV2)
    assert len(adapted.security_findings) == len([f for f in old.findings if f.kind == "security"])


def test_source_version_and_hash_both_gate_stale_results() -> None:
    source = "print(1)"
    legacy = AnalysisResult(language="python", filename="sample.py")
    from apsla.languages import registry

    result = adapt_analysis_result(source, legacy, 10, plugin=registry.get("python"))
    assert result_matches_source(result, source, 10)
    assert not result_matches_source(result, source + " ", 10)
    assert not result_matches_source(result, source, 11)


def test_stage_filter_and_token_inclusion_are_applied_by_adapter() -> None:
    source = "value = input()\neval(value)\n"
    old = Analyzer().analyze(source, language="python", options={"fixes": False, "ml": False})
    from apsla.languages import registry

    result = adapt_analysis_result(
        source,
        old,
        9,
        plugin=registry.get("python"),
        stages=["security"],
        include_tokens=False,
    )
    assert result.tokens == []
    assert result.security_findings
    assert not result.syntax_diagnostics
    assert not result.semantic_diagnostics
    assert any("stages filters" in omission for omission in result.omissions)
    empty = adapt_analysis_result(
        source, old, 9, plugin=registry.get("python"), stages=[], include_tokens=True
    )
    assert empty.tokens == []
    assert empty.security_findings == []
    assert empty.tools == []


def test_detection_respects_a_monkeypatched_empty_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tool_runner.shutil, "which", lambda executable, path=None: None)
    found = detect_tool("ruff", path="")
    assert found.available is False
    assert found.status == "unavailable"
    assert found.reason


def test_external_execution_fails_closed_without_network_sandbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tool_runner,
        "detect_tool",
        lambda name: ToolStatus(
            name=name, kind="analyzer", available=True, version="test", status="ok"
        ),
    )
    monkeypatch.setattr(tool_runner, "network_sandbox_available", lambda: False)
    status, parsed = execute_static_tool("ruff", "x = 1", "python")
    assert status.status == "unavailable"
    assert not status.executed
    assert "network-isolated" in (status.reason or "")
    assert parsed == {}


def test_static_tool_uses_safe_argv_and_never_executes_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    marker = tmp_path / "should-not-exist.txt"
    source = f"open({str(marker)!r}, 'w').write('executed')\n; & | $() `"
    monkeypatch.setattr(
        tool_runner,
        "detect_tool",
        lambda name: ToolStatus(
            name=name, kind="analyzer", available=True, version="test", status="ok"
        ),
    )
    monkeypatch.setattr(tool_runner.shutil, "which", lambda executable: sys.executable)
    monkeypatch.setattr(tool_runner.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(tool_runner, "network_sandbox_available", lambda: True)
    seen: dict[str, object] = {}

    def fake_run(argv, *, cwd, env, timeout):
        seen["argv"] = argv
        seen["cwd"] = cwd
        seen["env"] = env
        seen["timeout"] = timeout
        assert Path(argv[-1]).read_text(encoding="utf-8") == source
        return 0, b"ok", b""

    monkeypatch.setattr(tool_runner, "_run_capped", fake_run)
    hostile_filename = "name; & | $() `whoami`.py"
    status, parsed = execute_static_tool("ruff", source, "python", filename=hostile_filename)
    assert status.status == "ok" and status.executed
    assert parsed == {
        "parsed": {"parse_error": "Tool output was not valid JSON."},
        "stdout": "ok",
        "stderr": "",
    }
    assert isinstance(seen["argv"], list)
    assert hostile_filename not in seen["argv"]
    assert Path(seen["argv"][-1]).name == "input.py"
    assert str(seen["cwd"]) != str(tmp_path)
    assert "OPENAI_API_KEY" not in seen["env"]
    assert not marker.exists()


def test_static_tool_timeout_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tool_runner,
        "detect_tool",
        lambda name: ToolStatus(
            name=name, kind="analyzer", available=True, version="test", status="ok"
        ),
    )
    monkeypatch.setattr(tool_runner.shutil, "which", lambda executable: sys.executable)
    import tempfile

    monkeypatch.setattr(tempfile, "tempdir", str(Path.cwd()))
    monkeypatch.setattr(tool_runner, "network_sandbox_available", lambda: True)

    def timeout(*args, **kwargs):
        raise tool_runner.subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(tool_runner, "_run_capped", timeout)
    status, _ = execute_static_tool("ruff", "x = 1", "python", timeout=0.01)
    assert status.status == "timeout"
    assert status.executed


def test_process_pipe_caps_and_timeout_are_enforced() -> None:
    code = "import sys; sys.stdout.write('x'*100000); sys.stderr.write('y'*100000)"
    returncode, stdout, stderr = tool_runner._run_capped(
        [sys.executable, "-c", code], cwd=Path.cwd(), env=tool_runner._clean_env(), timeout=5
    )
    assert returncode == 0
    assert len(stdout) == tool_runner.MAX_OUTPUT_BYTES
    assert len(stderr) == tool_runner.MAX_OUTPUT_BYTES
    with pytest.raises(tool_runner.subprocess.TimeoutExpired):
        tool_runner._run_capped(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            cwd=Path.cwd(),
            env=tool_runner._clean_env(),
            timeout=0.05,
        )


def test_python_fixture_adaptation_retains_legacy_analysis() -> None:
    fixture = (
        Path(__file__).parents[1] / "fixtures" / "python" / "vulnerable" / "cmd_injection_flask.py"
    )
    source = fixture.read_text(encoding="utf-8")
    legacy = Analyzer().analyze(
        source, language="python", filename=fixture.name, options={"fixes": False, "ml": False}
    )
    from apsla.languages import registry

    adapted = adapt_analysis_result(source, legacy, 21, plugin=registry.get("python"))
    legacy_findings = [finding for finding in legacy.findings if finding.kind == "security"]
    assert len(adapted.security_findings) == len(legacy_findings)
    assert all(item.cwe and item.tool_provenance for item in adapted.security_findings)


@pytest.mark.parametrize(
    "fixture",
    FIXTURE_SOURCES,
    ids=lambda path: path.relative_to(Path(__file__).parents[1]).as_posix(),
)
def test_adapter_preserves_old_pipeline_semantics_for_each_fixture(fixture: Path) -> None:
    source = fixture.read_text(encoding="utf-8")
    language = fixture.parents[2].name
    if language == "cpp":
        language = "cpp"
    old_result = Analyzer().analyze(
        source,
        language=language,
        filename=fixture.name,
        options={"fixes": False, "ml": False},
    )
    before = old_result.model_dump()
    from apsla.languages import registry

    adapted = adapt_analysis_result(source, old_result, 1, plugin=registry.get(language))
    assert old_result.model_dump() == before
    assert len(adapted.security_findings) == len(
        [f for f in old_result.findings if f.kind == "security"]
    )
    assert adapted.source_hash == hashlib.sha256(source.encode("utf-8")).hexdigest()
    assert adapted.language == old_result.language


def test_v2_endpoints_are_registered_in_openapi() -> None:
    from apsla.server.app import app

    paths = app.openapi()["paths"]
    assert "/api/capabilities" in paths
    assert "/api/analyze" in paths
    for stage in ("lexical", "syntax", "security", "quality"):
        assert f"/api/analyze/{stage}" in paths
    response_schema = paths["/api/analyze"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert {item["$ref"].rsplit("/", 1)[-1] for item in response_schema["oneOf"]} == {
        "AnalysisResult",
        "AnalysisResultV2",
    }
    assert all(
        not operation.get("parameters")
        for path, operation in paths.items()
        if path.startswith("/api/analyze/")
        for operation in operation.values()
        if isinstance(operation, dict)
    )
    stage_schema = app.openapi()["components"]["schemas"]["StageAnalysisResponse"]["properties"]
    assert stage_schema["diagnostics"]["items"]["$ref"].endswith("/DiagnosticV2")
    assert stage_schema["findings"]["items"]["$ref"].endswith("/SecurityFindingV2")
    assert stage_schema["tools"]["items"]["$ref"].endswith("/ToolStatus")


def test_capabilities_builder_reports_discovered_adapter_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    app_module = importlib.import_module("apsla.server.app")
    from apsla.models_v2 import ToolStatus

    monkeypatch.setattr(
        app_module,
        "detect_all_tools",
        lambda: [
            ToolStatus(
                name="ruff", kind="analyzer", available=True, version="ruff test", status="ok"
            )
        ],
    )
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = app_module.build_capabilities()
    assert response.version
    assert {language.id for language in response.languages} == {
        "python",
        "java",
        "javascript",
        "cpp",
    }
    assert response.tools[0].name == "ruff" and response.tools[0].available
    assert response.ai["provider"] == "groq"
    assert response.ai["processing_location"] == "remote"
    assert response.ai["configured"] is False
    assert "Add GROQ_API_KEY to your .env file and restart" in response.ai["setup_message"]


def test_v2_request_requires_client_source_version() -> None:
    from pydantic import ValidationError

    from apsla.server.schemas import AnalyzeRequest

    with pytest.raises(ValidationError):
        AnalyzeRequest.model_validate({"source": "x=1", "language": "python", "api_version": 2})
    assert AnalyzeRequest.model_validate({"source": "x=1", "language": "python"}).api_version == 1


def test_part_7_4_wording_is_centralized_exactly() -> None:
    from apsla import status_wording

    assert {
        status_wording.FINDING_DETECTED,
        status_wording.POTENTIAL_VULNERABILITY,
        status_wording.CONFIRMED_BY_RULE_OR_TEST,
        status_wording.NO_FINDINGS_DETECTED,
        status_wording.ANALYSIS_INCOMPLETE,
        status_wording.CHECK_UNAVAILABLE,
    } == {
        "Finding detected.",
        "Potential vulnerability.",
        "Confirmed by the specified rule or test.",
        "No findings detected by checks run.",
        "Analysis incomplete.",
        "Check unavailable.",
    }


def test_existing_source_size_limit_is_enforced() -> None:
    from fastapi import HTTPException

    from apsla.server.app import MAX_SOURCE_BYTES, _validate_payload_size

    _validate_payload_size("x" * MAX_SOURCE_BYTES)
    with pytest.raises(HTTPException) as error:
        _validate_payload_size("x" * (MAX_SOURCE_BYTES + 1))
    assert error.value.status_code == 413
