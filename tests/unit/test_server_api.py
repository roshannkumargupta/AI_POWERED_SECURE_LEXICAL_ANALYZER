"""Unit and integration tests for FastAPI REST API endpoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apsla import __version__
from apsla.server.app import app
from apsla.server.cache import ANALYSIS_CACHE


@pytest.fixture(autouse=True)
def clean_test_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Ensure clean LRU cache and isolated feedback file for every test."""
    test_feedback_file = tmp_path / "feedback" / "false_positives.jsonl"
    monkeypatch.setattr("apsla.feedback.store.FEEDBACK_FILE", test_feedback_file)
    ANALYSIS_CACHE.clear()
    yield
    ANALYSIS_CACHE.clear()


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_health_endpoint_live(client: TestClient):
    """Verify /api/health returns 200 with truthful status and version."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == __version__
    assert data["ml_mode"] in ("on", "off")
    assert "ml_model_id" in data


def test_health_endpoint_ml_off(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Verify /api/health truthfully reports ml_mode 'off' when no model artifact exists."""
    empty_dir = tmp_path / "empty_artifacts"
    empty_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("apsla.ml.infer.ARTIFACTS_DIR", empty_dir)

    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ml_mode"] == "off"
    assert data["ml_model_id"] == "none"


def test_languages_endpoint(client: TestClient):
    """Verify /api/languages lists registered languages including Python."""
    resp = client.get("/api/languages")
    assert resp.status_code == 200
    langs = resp.json()
    assert isinstance(langs, list)
    python_entry = next((lang_item for lang_item in langs if lang_item["id"] == "python"), None)
    assert python_entry is not None
    assert python_entry["display_name"] == "Python"
    assert ".py" in python_entry["extensions"]
    assert python_entry["monaco_id"] == "python"


def test_samples_endpoint(client: TestClient):
    """Verify /api/samples returns at least 3 samples for Python (vulnerable, Trojan, safe)."""
    resp = client.get("/api/samples")
    assert resp.status_code == 200
    samples = resp.json()
    assert len(samples) >= 3

    categories = {s["category"] for s in samples if s["language"] == "python"}
    assert "vulnerable" in categories
    assert "adversarial" in categories or "trojan" in categories
    assert "safe" in categories

    # Filter by language
    py_resp = client.get("/api/samples?language=python")
    assert py_resp.status_code == 200
    assert len(py_resp.json()) == len(samples)

    empty_resp = client.get("/api/samples?language=nonexistent")
    assert empty_resp.status_code == 200
    assert empty_resp.json() == []


def test_analyze_flask_fixture(client: TestClient):
    """Verify POST /api/analyze on Flask fixture returns finding with taint_path and verified fix."""
    flask_fixture_path = (
        Path(__file__).parents[1] / "fixtures" / "python" / "vulnerable" / "cmd_injection_flask.py"
    )
    source = flask_fixture_path.read_text(encoding="utf-8")

    payload = {
        "source": source,
        "language": "python",
        "filename": "cmd_injection_flask.py",
        "options": {
            "fixes": True,
            "ml": True,
            "include_tokens": True,
            "include_suppressed": False,
        },
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Findings check
    findings = data["findings"]
    assert len(findings) >= 1

    inj_finding = next((f for f in findings if f["rule_id"] == "APS-PY-INJ-002"), None)
    assert inj_finding is not None

    # Taint path check
    assert len(inj_finding["taint_path"]) >= 2
    step_kinds = [s["step"] for s in inj_finding["taint_path"]]
    assert "source" in step_kinds
    assert "sink" in step_kinds

    # Verified fix check
    assert len(inj_finding["fixes"]) >= 1
    fix = inj_finding["fixes"][0]
    assert fix["verification"]["verified"] is True
    assert fix["verification"]["syntax_ok"] is True
    assert fix["verification"]["finding_gone"] is True


def test_analyze_auto_detect_language(client: TestClient):
    """Verify POST /api/analyze auto-detects language when language is null."""
    source = "x = 42\nprint(x)\n"
    payload = {
        "source": source,
        "language": None,
        "filename": "script.py",
        "options": {"fixes": False, "ml": False},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "python"


def test_analyze_payload_too_large_413(client: TestClient):
    """Verify POST /api/analyze rejects payloads over 512 KB with HTTP 413."""
    oversized_source = "x = 1\n" + ("# comment\n" * 60000)
    assert len(oversized_source.encode("utf-8")) > 512 * 1024

    payload = {
        "source": oversized_source,
        "language": "python",
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 413
    assert "512 KB" in resp.json()["detail"]


def test_analyze_unknown_language_400(client: TestClient):
    """Verify POST /api/analyze returns 400 for unsupported language."""
    payload = {
        "source": "func main() {}",
        "language": "golang_unknown",
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 400
    assert "unsupported" in resp.json()["detail"].lower()


def test_analyze_caching(client: TestClient):
    """Verify pure function caching by SHA256 returns identical cached results."""
    source = "name = request.args.get('q')\nos.system('echo ' + name)\n"
    payload = {
        "source": source,
        "language": "python",
        "options": {"fixes": False, "ml": False},
    }

    assert ANALYSIS_CACHE.size() == 0

    # First request: computes and caches
    resp1 = client.post("/api/analyze", json=payload)
    assert resp1.status_code == 200
    assert ANALYSIS_CACHE.size() == 1

    # Second request: served from cache
    resp2 = client.post("/api/analyze", json=payload)
    assert resp2.status_code == 200
    assert ANALYSIS_CACHE.size() == 1
    assert resp1.json() == resp2.json()


def test_analyze_timeout_504(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Verify 10 s analysis timeout produces HTTP 504 Gateway Timeout."""
    from apsla.pipeline import Analyzer

    def mock_analyze(*args, **kwargs):
        raise TimeoutError("Analysis timed out")

    monkeypatch.setattr(Analyzer, "analyze", mock_analyze)

    payload = {
        "source": "x = 1\n",
        "language": "python",
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 504
    assert "timed out" in resp.json()["detail"].lower()


def test_fix_endpoint_happy_path_and_reanalyze(client: TestClient):
    """Verify POST /api/fix applies a verified fix and re-analyzing shows finding gone."""
    flask_fixture_path = (
        Path(__file__).parents[1] / "fixtures" / "python" / "vulnerable" / "cmd_injection_flask.py"
    )
    source = flask_fixture_path.read_text(encoding="utf-8")

    # Step 1: Analyze to get finding and fix IDs
    analyze_resp = client.post(
        "/api/analyze",
        json={"source": source, "language": "python", "options": {"fixes": True, "ml": False}},
    )
    assert analyze_resp.status_code == 200
    findings = analyze_resp.json()["findings"]
    assert len(findings) >= 1
    finding = findings[0]
    assert len(finding["fixes"]) >= 1
    fix = finding["fixes"][0]

    # Step 2: Apply the fix via POST /api/fix
    fix_payload = {
        "source": source,
        "language": "python",
        "finding_id": finding["id"],
        "fix_id": fix["id"],
    }
    fix_resp = client.post("/api/fix", json=fix_payload)
    assert fix_resp.status_code == 200
    fix_data = fix_resp.json()

    assert "new_source" in fix_data
    assert "diff" in fix_data
    assert len(fix_data["diff"]) > 0
    assert fix_data["verification"]["verified"] is True
    assert fix_data["verification"]["finding_gone"] is True

    # Step 3: Verify the finding is eliminated in new_result
    new_findings = fix_data["new_result"]["findings"]
    remaining_inj = [f for f in new_findings if f["rule_id"] == finding["rule_id"]]
    assert len(remaining_inj) == 0

    # Step 4: Re-analyze new_source directly through /api/analyze
    reanalyze_resp = client.post(
        "/api/analyze",
        json={
            "source": fix_data["new_source"],
            "language": "python",
            "options": {"fixes": False, "ml": False},
        },
    )
    assert reanalyze_resp.status_code == 200
    direct_findings = reanalyze_resp.json()["findings"]
    assert not any(f["rule_id"] == finding["rule_id"] for f in direct_findings)


def test_fix_endpoint_errors(client: TestClient):
    """Verify POST /api/fix error conditions (finding not found, fix not found, bad lang)."""
    source = "import os\nos.system('echo hi')\n"

    # Bad language
    resp_bad_lang = client.post(
        "/api/fix",
        json={"source": source, "language": "unknown_lang", "finding_id": "f-1", "fix_id": "fix-1"},
    )
    assert resp_bad_lang.status_code == 400

    # Nonexistent finding
    resp_bad_finding = client.post(
        "/api/fix",
        json={
            "source": source,
            "language": "python",
            "finding_id": "nonexistent-finding-id",
            "fix_id": "fix-1",
        },
    )
    assert resp_bad_finding.status_code == 404
    assert "not found" in resp_bad_finding.json()["detail"].lower()


def test_fix_all_endpoint(client: TestClient):
    """Verify POST /api/fix-all applies multi-pass remediation."""
    yaml_fixture = (
        Path(__file__).parents[1] / "fixtures" / "python" / "vulnerable" / "yaml_load_unsafe.py"
    )
    source = yaml_fixture.read_text(encoding="utf-8")
    payload = {
        "source": source,
        "language": "python",
    }
    resp = client.post("/api/fix-all", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "new_source" in data
    assert "diff" in data
    assert len(data["applied"]) >= 1
    assert data["score_after"] > data["score_before"]


def test_feedback_and_suppression(client: TestClient):
    """Verify POST /api/feedback saves false positive and suppresses in subsequent analyses."""
    source = "name = request.args.get('q')\nos.system('echo ' + name)\n"

    # Step 1: Initial analysis
    analyze_resp = client.post(
        "/api/analyze",
        json={"source": source, "language": "python", "options": {"fixes": False, "ml": False}},
    )
    assert analyze_resp.status_code == 200
    findings = analyze_resp.json()["findings"]
    assert len(findings) >= 1
    finding = findings[0]

    # Step 2: Submit feedback
    fb_payload = {
        "finding_fingerprint": finding["id"],
        "rule_id": finding["rule_id"],
        "language": "python",
        "verdict": "false_positive",
        "snippet": "os.system('echo ' + name)",
    }
    fb_resp = client.post("/api/feedback", json=fb_payload)
    assert fb_resp.status_code == 200
    assert fb_resp.json() == {"saved": True}

    # Step 3: Analyze with include_suppressed=False (default) -> finding should be HIDDEN
    resp_hidden = client.post(
        "/api/analyze",
        json={
            "source": source,
            "language": "python",
            "options": {"include_suppressed": False, "fixes": False, "ml": False},
        },
    )
    assert resp_hidden.status_code == 200
    hidden_findings = resp_hidden.json()["findings"]
    assert not any(f["id"] == finding["id"] for f in hidden_findings)

    # Step 4: Analyze with include_suppressed=True -> finding is RETURNED with suppressed=True
    resp_included = client.post(
        "/api/analyze",
        json={
            "source": source,
            "language": "python",
            "options": {"include_suppressed": True, "fixes": False, "ml": False},
        },
    )
    assert resp_included.status_code == 200
    included_findings = resp_included.json()["findings"]
    suppressed_finding = next((f for f in included_findings if f["id"] == finding["id"]), None)
    assert suppressed_finding is not None
    assert suppressed_finding["suppressed"] is True


def test_ml_insights_endpoint(client: TestClient):
    """Verify POST /api/ml/insights returns token occlusion insights or ml_mode 'off'."""
    source = "import os\nprint(123)\n"
    payload = {
        "source": source,
        "language": "python",
        "token_index": 0,
    }
    resp = client.post("/api/ml/insights", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ml_mode"] in ("on", "off")
    if data["ml_mode"] == "on":
        assert "token_text" in data
        assert "feature_group_drops" in data

    # Out of range token_index -> 400
    bad_payload = {
        "source": source,
        "language": "python",
        "token_index": 9999,
    }
    bad_resp = client.post("/api/ml/insights", json=bad_payload)
    assert bad_resp.status_code == 400


def test_static_root_fallback(client: TestClient):
    """Verify GET / returns fallback message when web/dist does not exist."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "Frontend build not found" in data["message"]


def test_cors_headers(client: TestClient):
    """Verify CORS headers only permit authorized origins."""
    headers_allowed = {"Origin": "http://localhost:5173"}
    resp = client.get("/api/health", headers=headers_allowed)
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"

    headers_forbidden = {"Origin": "http://malicious-website.com"}
    resp_forbidden = client.get("/api/health", headers=headers_forbidden)
    assert resp_forbidden.headers.get("access-control-allow-origin") is None


def test_internal_error_does_not_leak_stacktrace():
    """Verify unexpected server crashes return an error_id and never leak stack traces."""
    safe_client = TestClient(app, raise_server_exceptions=False)
    with patch(
        "apsla.server.app.registry.get", side_effect=RuntimeError("Secret database error line 99")
    ):
        resp = safe_client.get("/api/languages")
        assert resp.status_code == 500
        data = resp.json()
        assert "error_id" in data
        assert "Internal server error" in data["detail"]
        assert "Secret database error" not in resp.text
        assert "Traceback" not in resp.text
