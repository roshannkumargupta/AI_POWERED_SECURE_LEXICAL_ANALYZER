"""End-to-end API integration tests for JavaScript language plugin."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apsla.server.app import app
from apsla.server.cache import ANALYSIS_CACHE

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JS_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "javascript"


@pytest.fixture(autouse=True)
def clean_cache():
    """Clear server cache before each test."""
    ANALYSIS_CACHE.clear()
    yield
    ANALYSIS_CACHE.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_languages_endpoint_includes_javascript(client: TestClient) -> None:
    """Verify /api/languages dynamically includes JavaScript plugin."""
    resp = client.get("/api/languages")
    assert resp.status_code == 200
    languages = resp.json()
    js_lang = next((lang for lang in languages if lang["id"] == "javascript"), None)
    assert js_lang is not None
    assert ".js" in js_lang["extensions"]
    assert ".mjs" in js_lang["extensions"]
    assert ".cjs" in js_lang["extensions"]
    assert ".jsx" in js_lang["extensions"]
    assert js_lang["monaco_id"] == "javascript"


def test_samples_endpoint_includes_javascript_samples(client: TestClient) -> None:
    """Verify /api/samples lists JavaScript samples."""
    resp = client.get("/api/samples")
    assert resp.status_code == 200
    samples = resp.json()
    js_samples = [s for s in samples if s.get("language") == "javascript"]
    assert len(js_samples) >= 4
    sample_ids = [s["id"] for s in js_samples]
    assert "js-vuln-express-cmd-injection" in sample_ids
    assert "js-vuln-dom-xss" in sample_ids
    assert "js-adv-trojan-source" in sample_ids
    assert "js-safe-text-content" in sample_ids


def test_analyze_javascript_dom_xss_e2e(client: TestClient) -> None:
    """Verify end-to-end analysis of vulnerable DOM XSS with taint path and fix."""
    fixture_path = JS_FIXTURES / "vulnerable" / "dom_xss.js"
    source = fixture_path.read_text(encoding="utf-8")

    payload = {
        "source": source,
        "language": "javascript",
        "filename": "dom_xss.js",
        "options": {"ml": False, "fixes": True},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    findings = [f for f in data["findings"] if f["rule_id"] == "APS-JS-XSS-001"]
    assert len(findings) >= 1
    f = findings[0]
    assert f["severity"] in ("high", "critical")

    # Fix checks
    fixes = f["fixes"]
    assert len(fixes) >= 1
    verified_fix = next((fx for fx in fixes if fx["verification"]["verified"]), None)
    assert verified_fix is not None
    assert len(verified_fix["edits"]) >= 1


def test_analyze_javascript_sqli_template_literal_e2e(client: TestClient) -> None:
    """Verify end-to-end analysis of SQL injection via template literal."""
    fixture_path = JS_FIXTURES / "vulnerable" / "sqli_template_literal.js"
    source = fixture_path.read_text(encoding="utf-8")

    payload = {
        "source": source,
        "language": "javascript",
        "filename": "sqli_template_literal.js",
        "options": {"ml": False, "fixes": True},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    findings = [f for f in data["findings"] if f["rule_id"] == "APS-JS-INJ-003"]
    assert len(findings) == 1
    f = findings[0]
    assert f["severity"] == "critical"  # Taint confirmed boosted
    assert len(f["taint_path"]) >= 3


def test_analyze_javascript_safe_text_content_e2e(client: TestClient) -> None:
    """Verify safe textContent JavaScript code reports 0 findings and clean score."""
    fixture_path = JS_FIXTURES / "safe" / "safe_dom_text_content.js"
    source = fixture_path.read_text(encoding="utf-8")

    payload = {
        "source": source,
        "language": "javascript",
        "filename": "safe_dom_text_content.js",
        "options": {"ml": False, "fixes": True},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    active_findings = [f for f in data["findings"] if not f.get("suppressed", False)]
    assert len(active_findings) == 0
    assert data["summary"]["score"] == 100


def test_fix_javascript_e2e(client: TestClient) -> None:
    """Verify applying a verified fix via /api/fix end-to-end."""
    fixture_path = JS_FIXTURES / "vulnerable" / "crypto_md5.js"
    source = fixture_path.read_text(encoding="utf-8")

    # Analyze first to get finding and fix ID
    analyze_resp = client.post(
        "/api/analyze",
        json={
            "source": source,
            "language": "javascript",
            "filename": "crypto_md5.js",
            "options": {"ml": False, "fixes": True},
        },
    )
    assert analyze_resp.status_code == 200
    data = analyze_resp.json()
    finding = next(f for f in data["findings"] if f["rule_id"] == "APS-JS-CRY-002")
    fix = next(fx for fx in finding["fixes"] if fx["verification"]["verified"])

    fix_resp = client.post(
        "/api/fix",
        json={
            "source": source,
            "language": "javascript",
            "fix_id": fix["id"],
            "finding_id": finding["id"],
        },
    )
    assert fix_resp.status_code == 200
    fix_data = fix_resp.json()
    assert fix_data["verification"]["verified"] is True
    assert "sha256" in fix_data["new_source"]
