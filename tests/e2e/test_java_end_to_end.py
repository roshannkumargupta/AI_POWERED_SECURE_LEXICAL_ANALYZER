"""End-to-end API integration tests for Java language plugin."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apsla.server.app import app
from apsla.server.cache import ANALYSIS_CACHE

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JAVA_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "java"


@pytest.fixture(autouse=True)
def clean_cache():
    """Clear server cache before each test."""
    ANALYSIS_CACHE.clear()
    yield
    ANALYSIS_CACHE.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_languages_endpoint_includes_java(client: TestClient) -> None:
    """Verify /api/languages dynamically includes Java plugin."""
    resp = client.get("/api/languages")
    assert resp.status_code == 200
    languages = resp.json()
    java_lang = next((lang for lang in languages if lang["id"] == "java"), None)
    assert java_lang is not None
    assert ".java" in java_lang["extensions"]
    assert java_lang["monaco_id"] == "java"


def test_samples_endpoint_includes_java_samples(client: TestClient) -> None:
    """Verify /api/samples lists Java samples."""
    resp = client.get("/api/samples")
    assert resp.status_code == 200
    samples = resp.json()
    java_samples = [s for s in samples if s.get("language") == "java"]
    assert len(java_samples) >= 4
    sample_ids = [s["id"] for s in java_samples]
    assert "java-vuln-sqli-servlet" in sample_ids
    assert "java-vuln-deserialization" in sample_ids
    assert "java-adv-trojan-source" in sample_ids
    assert "java-safe-prepared-statement" in sample_ids


def test_analyze_java_sqli_servlet_e2e(client: TestClient) -> None:
    """Verify end-to-end analysis of vulnerable Java servlet with taint path and fix."""
    fixture_path = JAVA_FIXTURES / "vulnerable" / "sqli_servlet.java"
    source = fixture_path.read_text(encoding="utf-8")

    payload = {
        "source": source,
        "language": "java",
        "filename": "sqli_servlet.java",
        "options": {"ml": False, "fixes": True},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    findings = [f for f in data["findings"] if f["rule_id"] == "APS-JV-INJ-002"]
    assert len(findings) == 1
    f = findings[0]
    assert f["severity"] == "critical"  # Taint confirmed boosted

    # Taint path checks
    taint_path = f["taint_path"]
    assert len(taint_path) >= 3
    assert taint_path[0]["step"] == "source"
    assert taint_path[-1]["step"] == "sink"

    # Fix checks
    fixes = f["fixes"]
    assert len(fixes) >= 1
    verified_fix = next((fx for fx in fixes if fx["verification"]["verified"]), None)
    assert verified_fix is not None
    assert len(verified_fix["edits"]) >= 1


def test_analyze_java_safe_prepared_statement_e2e(client: TestClient) -> None:
    """Verify safe PreparedStatement Java code reports 0 findings and score 100."""
    fixture_path = JAVA_FIXTURES / "safe" / "sqli_prepared_statement.java"
    source = fixture_path.read_text(encoding="utf-8")

    payload = {
        "source": source,
        "language": "java",
        "filename": "sqli_prepared_statement.java",
        "options": {"ml": False, "fixes": True},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    active_findings = [f for f in data["findings"] if not f["suppressed"]]
    assert len(active_findings) == 0
    assert data["summary"]["score"] == 100


def test_analyze_java_trojan_source_e2e(client: TestClient) -> None:
    """Verify Trojan Source in Java is detected by APS-JV-UNI-001 or APS-ALL-UNI-001."""
    fixture_path = JAVA_FIXTURES / "adversarial" / "adv_trojan_source_bidi.java"
    source = fixture_path.read_text(encoding="utf-8")

    payload = {
        "source": source,
        "language": "java",
        "filename": "adv_trojan_source_bidi.java",
        "options": {"ml": False, "fixes": True},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    uni_findings = [
        f
        for f in data["findings"]
        if f["rule_id"] in ("APS-JV-UNI-001", "APS-ALL-UNI-001") and not f["suppressed"]
    ]
    assert len(uni_findings) >= 1
