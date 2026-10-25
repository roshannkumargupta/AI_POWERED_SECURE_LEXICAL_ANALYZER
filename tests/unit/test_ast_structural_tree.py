from __future__ import annotations

import subprocess
from pathlib import Path

from apsla.languages import registry
from apsla.models_v2 import DiagnosticV2, ToolStatus
from apsla.parsing_v2 import (
    _tool_diagnostics,
    ast_node_view,
    build_ast_view,
    build_token_projection,
    parse_source,
    run_semantic_checks,
)
from apsla.server import tool_runner
from apsla.server.app import _stage_only, app
from apsla.server.schemas import AnalyzeRequest

VALID = {
    "python": "def add(a, b):\n    return a + b\n",
    "java": "class Example { int add(int a, int b) { return a + b; } }\n",
    "cpp": "int add(int a, int b) { return a + b; }\n",
    "javascript": "function add(a, b) { return a + b; }\n",
}
BROKEN = {
    "python": "def broken(:\n    pass\n",
    "java": "class Broken { void f( { }\n",
    "cpp": "int broken( { return 0; }\n",
    "javascript": "function broken( { return 0; }\n",
}
MISSING_DELIMITERS = {
    "python": "value = (1 + 2\n",
    "java": "class A { int f(){ return 1 } }",
    "cpp": "int f(){ return 1 }",
    "javascript": "function f( { return 1; }",
}


def _run_no_wait(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("Expected the syntax route to complete without an event-loop suspension")


def test_real_parsers_accept_valid_programs_for_all_languages() -> None:
    for language, source in VALID.items():
        outcome = parse_source(language, source, f"valid-{language}")
        assert outcome.tree is not None, (language, outcome.reason)
        assert not outcome.diagnostics, (language, outcome.diagnostics)
        assert outcome.status == "ok"


def test_malformed_statements_produce_source_located_diagnostics() -> None:
    for language, source in BROKEN.items():
        outcome = parse_source(language, source, f"broken-{language}")
        assert outcome.diagnostics, (language, outcome)
        assert all(item.category == "syntax" for item in outcome.diagnostics)
        assert all(item.range.start_line >= 1 and item.range.start_col >= 1 for item in outcome.diagnostics)
        if language == "python":
            assert outcome.diagnostics[0].produced_by == "python.ast"
            assert outcome.diagnostics[0].certainty == "definitive"
        else:
            assert all(item.certainty == "incomplete" for item in outcome.diagnostics)


def test_missing_delimiters_and_required_terminators_are_reported() -> None:
    for language, source in MISSING_DELIMITERS.items():
        outcome = parse_source(language, source, f"missing-{language}")
        assert outcome.diagnostics, language
        assert all(item.range.start_line >= 1 for item in outcome.diagnostics)
    for language in ("java", "cpp"):
        source = "class A { int f(){ return 1 } }" if language == "java" else "int f(){ return 1 }"
        outcome = parse_source(language, source, f"terminator-{language}")
        assert any(";" in item.message for item in outcome.diagnostics)


def test_ast_shape_ranges_children_and_on_demand_expansion() -> None:
    language = "javascript"
    source = 'const face = "😀";\nfunction f(){ return face; }\n'
    outcome = parse_source(language, source, "ast-shape")
    tokens = build_token_projection(registry.get(language), source, language, "ast-shape")
    view = build_ast_view(outcome, "ast-shape", tokens, [], max_depth=20, max_nodes=1000)
    assert view is not None and view.nodes
    nodes = {node.id: node for node in view.nodes}
    for node in view.nodes:
        assert 1 <= node.range.start_line <= len(source.splitlines()) + 1
        assert node.range.start_col >= 1 and node.range.end_col >= 1
        if node.parent_id and node.parent_id in nodes:
            parent = nodes[node.parent_id]
            assert (node.range.start_line, node.range.start_col) >= (parent.range.start_line, parent.range.start_col)
            assert (node.range.end_line, node.range.end_col) <= (parent.range.end_line, parent.range.end_col)
    face = next(node for node in view.nodes if node.type in {"string", "string_fragment"} and "😀" in node.text_preview)
    assert face.range.start_col >= 1
    assert face.range.end_col - face.range.start_col == 4  # quote + UTF-16 surrogate pair + quote
    expanded = ast_node_view("ast-shape", face.id, max_depth=2, max_nodes=10)
    assert expanded is not None and expanded.root_id == face.id


def test_ast_limits_report_truncation() -> None:
    language = "python"
    source = "def f(a, b, c):\n    x = (a + b) * c\n    return x\n"
    outcome = parse_source(language, source, "ast-limits")
    view = build_ast_view(outcome, "ast-limits", [], [], max_depth=1, max_nodes=2)
    assert view is not None
    assert view.truncated
    assert len(view.nodes) <= 2


def test_python_uses_tree_sitter_for_a_partial_tree_when_ast_fails() -> None:
    outcome = parse_source("python", "def f(:\n  return 1\n", "python-broken")
    assert outcome.tree_kind == "tree_sitter"
    assert outcome.tree is not None
    assert any(tool.name == "tree-sitter-python" and tool.executed for tool in outcome.tools)


def test_missing_semantic_tools_are_unavailable_not_clean(monkeypatch) -> None:
    monkeypatch.setenv("PATH", "")
    diagnostics, tools, warnings = run_semantic_checks("python", "x = missing\n", "missing-tools")
    assert diagnostics == []
    assert tools and all(tool.status == "unavailable" and not tool.executed for tool in tools)
    assert warnings and all("Check unavailable" in warning for warning in warnings)


def test_tool_output_adapter_emits_unified_semantic_diagnostic() -> None:
    items = _tool_diagnostics(
        "ruff", "python", "print(missing)\n",
        {"parsed": [{"code": "F821", "message": "Undefined name", "location": {"row": 1, "column": 7}, "end_location": {"row": 1, "column": 14}}]},
        "diag-sample",
    )
    assert len(items) == 1
    assert isinstance(items[0], DiagnosticV2)
    assert items[0].category == "semantic"
    assert items[0].produced_by == "ruff"
    assert items[0].certainty == "heuristic"


def test_compiler_and_type_checker_output_adapters_keep_locations() -> None:
    java = _tool_diagnostics(
        "javac", "java", "class X {\n void f() {\n missing();\n }\n}", {"stderr": "X.java:3: error: cannot find symbol\n"}, "javac-id"
    )
    cpp = _tool_diagnostics(
        "g++", "cpp", "int x;\nint y;", {"stderr": "input.cpp:2:7: error: expected ';'\n"}, "gpp-id"
    )
    mypy = _tool_diagnostics(
        "mypy", "python", "x = 1\ny = 2\nz = 3\nw = 4", {"stderr": "input.py:4:2: error: Incompatible types [assignment]\n"}, "mypy-id"
    )
    assert java[0].range.start_line == 3 and java[0].range.start_col == 1
    assert cpp[0].range.start_line == 2 and cpp[0].range.start_col == 7
    assert mypy[0].range.start_line == 4 and mypy[0].certainty == "heuristic"


def test_syntax_error_does_not_change_valid_lexical_tokens() -> None:
    language = "cpp"
    source = "int value = ;\n"
    lexer_tokens = registry.get(language).lex(source)
    outcome = parse_source(language, source, "syntax-vs-lex")
    assert outcome.diagnostics
    assert all(token.kind != "ERROR" for token in lexer_tokens)


def test_syntax_endpoint_returns_ast_for_each_language() -> None:
    assert "/api/ast/{analysis_id}/node/{node_id}" in app.openapi()["paths"]
    for language, source in VALID.items():
        response = _run_no_wait(
            _stage_only(
                AnalyzeRequest(
                    source=source, language=language, source_version=1,
                    include_ast=True, ast_max_nodes=100, ast_max_depth=6,
                ),
                "syntax",
            )
        )
        assert response.ast is not None, (language, response.omissions)
        assert response.ast.nodes
        assert response.syntax_status.status == "ok"
        assert response.semantic_status.status in {"incomplete", "unavailable"}
        assert response.tools
    for language, source in BROKEN.items():
        response = _run_no_wait(
            _stage_only(
                AnalyzeRequest(source=source, language=language, source_version=2, include_ast=True),
                "syntax",
            )
        )
        assert response.diagnostics
        assert response.ast is not None
        assert response.syntax_status.status == "issues"
        assert response.lexical_status.status in {"ok", "issues"}


def test_syntax_errors_leave_recognized_tokens_lexically_valid_for_each_language() -> None:
    invalid_statements = {
        "python": "value = 1 +\n",
        "java": "class X { int value = ; }",
        "cpp": "int value = ;",
        "javascript": "const value = ;",
    }
    for language, source in invalid_statements.items():
        response = _run_no_wait(
            _stage_only(
                AnalyzeRequest(source=source, language=language, source_version=8), "syntax"
            )
        )
        assert response.syntax_status.status == "issues"
        assert response.lexical_status.status == "ok"
        assert all(token.lexical_status == "valid" for token in response.tokens)


def test_javac_profile_uses_public_class_filename(monkeypatch, tmp_path) -> None:
    observed: dict[str, object] = {}
    monkeypatch.setattr(tool_runner, "network_sandbox_available", lambda: True)
    monkeypatch.setattr(tool_runner.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(tool_runner, "detect_tool", lambda name: ToolStatus(name=name, kind="compiler", available=True, version="test", status="ok"))
    monkeypatch.setattr(tool_runner.shutil, "which", lambda _name: "javac-test.exe")

    def fake_run(argv, **_kwargs):
        observed["argv"] = argv
        observed["source"] = (Path(argv[-1])).read_text(encoding="utf-8")
        return 0, b"", b""

    monkeypatch.setattr(tool_runner, "_run_capped", fake_run)
    status, _ = tool_runner.execute_static_tool("javac", "public class PublicApi {}", "java")
    assert status.executed
    argv = observed["argv"]
    assert isinstance(argv, list)
    assert argv[-1].endswith("PublicApi.java")
    assert "-proc:none" in argv


def test_semantic_runner_reports_timeout_and_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(tool_runner, "network_sandbox_available", lambda: True)
    monkeypatch.setattr(tool_runner.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(tool_runner, "detect_tool", lambda name: ToolStatus(name=name, kind="analyzer", available=True, version="test", status="ok"))
    monkeypatch.setattr(tool_runner.shutil, "which", lambda _name: "ruff-test.exe")
    monkeypatch.setattr(tool_runner, "_run_capped", lambda *_a, **_k: (_ for _ in ()).throw(subprocess.TimeoutExpired(["ruff"], 0.01)))
    timeout_status, _ = tool_runner.execute_static_tool("ruff", "x = 1", "python", timeout=0.01)
    assert timeout_status.status == "timeout" and timeout_status.executed

    monkeypatch.setattr(tool_runner, "_run_capped", lambda *_a, **_k: (2, b"[]", b"failed"))
    failed_status, _ = tool_runner.execute_static_tool("ruff", "x = 1", "python")
    assert failed_status.status == "failed" and failed_status.executed
