"""Unit tests for Phase 12 Feedback Store."""

from pathlib import Path

import pytest

from apsla.feedback.store import clear_feedback_file, load_all_feedback, save_feedback


@pytest.fixture(autouse=True)
def clean_feedback_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Ensure feedback tests use an isolated temporary feedback file."""
    fake_feedback_file = tmp_path / "false_positives.jsonl"
    monkeypatch.setattr("apsla.feedback.store.FEEDBACK_FILE", fake_feedback_file)
    monkeypatch.setattr("apsla.feedback.store.FEEDBACK_DIR", tmp_path)
    yield
    if fake_feedback_file.exists():
        fake_feedback_file.unlink()


def test_save_and_load_feedback():
    """Verify feedback is recorded with exact schema and loaded accurately."""
    res = save_feedback(
        rule_id="APS-PY-INJ-001",
        language="python",
        fingerprint="fp-test-123",
        snippet="os.system('safe command')",
        verdict="false_positive",
        note="Sanitized by custom whitelist validator",
    )
    assert res is True

    items = load_all_feedback()
    assert len(items) == 1
    record = items[0]
    assert record["rule_id"] == "APS-PY-INJ-001"
    assert record["language"] == "python"
    assert record["fingerprint"] == "fp-test-123"
    assert record["verdict"] == "false_positive"
    assert record["note"] == "Sanitized by custom whitelist validator"
    assert "timestamp" in record
    assert record["snippet"] == "os.system('safe command')"


def test_snippet_truncated_to_400_chars():
    """Verify snippets over 400 characters are capped strictly at 400 characters."""
    long_snippet = "x = " + ("A" * 500)
    save_feedback(
        rule_id="APS-JS-INJ-001",
        language="javascript",
        fingerprint="fp-trunc-test",
        snippet=long_snippet,
        verdict="false_positive",
    )

    items = load_all_feedback()
    assert len(items) == 1
    assert len(items[0]["snippet"]) == 400
    assert items[0]["snippet"].startswith("x = AAAAA")


def test_clear_feedback_file():
    """Verify feedback file can be cleared cleanly."""
    save_feedback(rule_id="R1", language="python", fingerprint="F1")
    assert len(load_all_feedback()) == 1
    clear_feedback_file()
    assert len(load_all_feedback()) == 0
