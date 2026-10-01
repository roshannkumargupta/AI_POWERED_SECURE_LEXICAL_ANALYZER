"""End-to-end API tests for C and C++ analysis and remediation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apsla.server.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_cpp_api_analyze_strcpy_argv(client: TestClient):
    """Verify /api/analyze detects buffer overflow with taint path and verified fix in C code."""
    code = (
        "#include <stdio.h>\n"
        "#include <string.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32];\n"
        "    char *src = argv[1];\n"
        "    strcpy(dest, src);\n"
        "    return 0;\n"
        "}\n"
    )
    payload = {
        "source": code,
        "language": "cpp",
        "filename": "strcpy_argv.c",
        "options": {"fixes": True, "ml": False},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "cpp"
    assert "findings" in data
    vuln_findings = [f for f in data["findings"] if f["rule_id"] == "APS-CP-MEM-001"]
    assert len(vuln_findings) == 1
    f = vuln_findings[0]
    assert len(f["taint_path"]) >= 2
    assert len(f["fixes"]) >= 1
    assert f["fixes"][0]["verification"]["verified"] is True
    assert "snprintf" in f["fixes"][0]["edits"][0]["new_text"]


def test_cpp_api_samples(client: TestClient):
    """Verify /api/samples returns C/C++ bundled sample items."""
    resp = client.get("/api/samples?language=cpp")
    assert resp.status_code == 200
    samples = resp.json()
    assert len(samples) == 5
    sample_ids = {s["id"] for s in samples}
    assert "cpp-vuln-strcpy-argv" in sample_ids
    assert "cpp-vuln-format-string" in sample_ids
    assert "cpp-vuln-cmd-injection" in sample_ids
    assert "cpp-adv-trojan-source" in sample_ids
    assert "cpp-safe-snprintf" in sample_ids


def test_cpp_api_fix_all(client: TestClient):
    """Verify /api/fix/all remediates C/C++ buffer overflow with snprintf."""
    code = (
        "#include <stdio.h>\n"
        "#include <string.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32];\n"
        "    char *src = argv[1];\n"
        "    strcpy(dest, src);\n"
        "    return 0;\n"
        "}\n"
    )
    payload = {
        "source": code,
        "language": "cpp",
        "filename": "strcpy_argv.c",
        "allow_review": True,
    }
    resp = client.post("/api/fix-all", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "snprintf" in data["new_source"]
    assert len(data["applied"]) >= 1
