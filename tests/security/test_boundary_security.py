from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
from fastapi import HTTPException

from apsla.agents.provider_v2 import redact_prompt
from apsla.server import app as app_module
from apsla.server.security_limits import (
    MAX_REQUEST_BYTES,
    clear_rate_state,
    neutralize_controls,
    rate_allowed,
    request_group,
    safe_filename_label,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.security
def test_ingress_helpers_enforce_rate_groups_and_bounds():
    assert MAX_REQUEST_BYTES == 1024 * 1024
    assert request_group("/api/analyze") == "analysis"
    assert request_group("/api/ai/explain") == "ai"
    assert request_group("/api/agent-safety/run") == "safety"
    clear_rate_state()


@pytest.mark.security
def test_token_and_finding_limits_return_structured_codes():
    with pytest.raises(HTTPException) as token_error:
        app_module._enforce_analysis_limits(100_001, 0)
    assert token_error.value.status_code == 413
    assert token_error.value.detail["code"] == "TOKEN_LIMIT_EXCEEDED"
    with pytest.raises(HTTPException) as finding_error:
        app_module._enforce_analysis_limits(0, 2_001)
    assert finding_error.value.status_code == 413
    assert finding_error.value.detail["code"] == "FINDING_LIMIT_EXCEEDED"
    assert all(rate_allowed("security-test", "ai", 1.0) for _ in range(8))
    assert not rate_allowed("security-test", "ai", 1.0)
    assert rate_allowed("another-client", "ai", 1.0)
    clear_rate_state()


@pytest.mark.security
def test_session_cookie_headers_and_consent_isolation():
    fake_a, fake_b = "client-session-a-123456", "client-session-b-123456"
    token_a = app_module._request_session.set("opaque-browser-session-A")
    try:
        session_a = app_module._session_key(fake_a)
        app_module.REMOTE_CONSENTS.add(session_a)
    finally:
        app_module._request_session.reset(token_a)
    token_b = app_module._request_session.set("opaque-browser-session-B")
    try:
        session_b = app_module._session_key(fake_b)
    finally:
        app_module._request_session.reset(token_b)
    assert session_a == "opaque-browser-session-A"
    assert session_b == "opaque-browser-session-B"
    assert session_a not in {fake_a, fake_b} and session_b not in {fake_a, fake_b}
    assert session_a in app_module.REMOTE_CONSENTS
    assert session_b not in app_module.REMOTE_CONSENTS
    app_module.REMOTE_CONSENTS.discard(session_a)
    middleware_source = (ROOT / "src/apsla/server/app.py").read_text(encoding="utf-8")
    assert 'samesite="strict"' in middleware_source
    assert "httponly=True" in middleware_source
    assert "SECURELEX_BIND_HOST" in middleware_source
    assert "compare_digest" in middleware_source
    assert "@app.exception_handler(HTTPException)" in middleware_source


@pytest.mark.security
def test_host_origin_rejected_and_structured_size_error():
    source = (ROOT / "src/apsla/server/app.py").read_text(encoding="utf-8")
    assert "HOST_REJECTED" in source and "ORIGIN_REJECTED" in source
    assert "REQUEST_TOO_LARGE" in source and "MAX_REQUEST_BYTES" in source
    assert "RATE_LIMITED" in source


@pytest.mark.security
def test_filename_labels_never_retain_client_paths_and_controls_are_neutralized():
    assert safe_filename_label(r"..\..\evil file.py") == "evil_file.py"
    sanitized = neutralize_controls("ok\x1b[31mred\x00\u202e")
    assert "\x1b" not in sanitized and "\x00" not in sanitized and "\u202e" not in sanitized


@pytest.mark.security
def test_provider_secret_redaction():
    assert "[REDACTED]" in redact_prompt("api_key=secret123")
    assert "secret123" not in redact_prompt("api_key=secret123")


@pytest.mark.security
def test_backend_no_submitted_code_execution_primitives_outside_written_allowlist():
    """Run-time model.eval is inference mode; Python source uses ast.parse, never eval/exec."""
    roots = [ROOT / "src" / "apsla" / name for name in ("server", "diagnostics", "fixes", "agents")]
    forbidden_imports = {"pickle"}
    for root in roots:
        for file in root.rglob("*.py"):
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = (
                        {item.name.split(".")[0] for item in node.names}
                        if isinstance(node, ast.Import)
                        else {node.module.split(".")[0] if node.module else ""}
                    )
                    assert not (names & forbidden_imports), f"pickle import: {file}:{node.lineno}"
                if not isinstance(node, ast.Call):
                    continue
                called = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                assert called not in {"eval", "exec", "compile"}, (
                    f"forbidden call {called}: {file}:{node.lineno}"
                )
                if isinstance(node.func, ast.Attribute) and node.func.attr == "system":
                    assert not (
                        isinstance(node.func.value, ast.Name) and node.func.value.id == "os"
                    ), f"os.system: {file}:{node.lineno}"
                if called in {"import_module", "__import__"}:
                    pytest.fail(f"dynamic import: {file}:{node.lineno}")
                if called in {"run", "Popen", "call", "check_call", "check_output"}:
                    assert not any(
                        keyword.arg == "shell"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is True
                        for keyword in node.keywords
                    ), f"shell=True: {file}:{node.lineno}"


@pytest.mark.security
def test_frontend_rendering_does_not_use_html_injection_sinks():
    source = "\n".join(
        file.read_text(encoding="utf-8")
        for file in (ROOT / "web" / "src").rglob("*.tsx")
        if "/test/" not in file.as_posix()
    )
    assert not re.search(r"dangerouslySetInnerHTML|\.innerHTML\s*=", source)
    hostile = '<img onerror="alert(1)"> javascript:alert(1) \u202e'
    assert neutralize_controls(hostile) == hostile.replace("\u202e", "")


@pytest.mark.security
def test_patch_hostility_is_rejected_without_mutating_source():
    from apsla.fixes.patch_v2 import PatchProposalV2, source_sha256, validate_proposal
    from apsla.models import Edit, Range

    source = "value = 1\n"
    malformed = PatchProposalV2(
        source_hash=source_sha256(source),
        source_version=4,
        target_finding_id="finding-1",
        origin="ai",
        edits=[
            Edit(
                range=Range(start_line=999999, start_col=1, end_line=999999, end_col=2),
                new_text="; import os; os.system('echo inert')",
            )
        ],
    )
    with pytest.raises(ValueError):
        validate_proposal(source, 4, malformed)
    assert source == "value = 1\n"
