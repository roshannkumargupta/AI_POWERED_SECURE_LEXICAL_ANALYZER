"""Integration checks for the manifest-backed sample catalogue."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from apsla.samples.loader import load_samples
from apsla.server.samples import get_samples

ROOT = Path(__file__).resolve().parents[2]


def test_catalogue_quota_sources_and_pending_reason() -> None:
    """Keep all phase catalogue quotas and explain every unshipped item."""
    root = ROOT / "src" / "apsla" / "samples"
    rows = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert len(rows) == 146
    assert len({row["id"] for row in rows}) == 146
    counts = {
        language: sum(row["language"] == language for row in rows)
        for language in ("python", "java", "javascript", "cpp")
    }
    assert counts == {"python": 43, "java": 35, "javascript": 34, "cpp": 34}
    pending_count = sum(bool(row.get("pending_reason")) for row in rows)
    assert len(load_samples()) == len(rows) - pending_count
    pending = [row for row in rows if row.get("pending_reason")]
    assert all(row["pending_reason"] for row in pending)
    for row in rows:
        source = (root / row["file"]).read_text(encoding="utf-8")
        assert len(source.splitlines()) <= 120
        for value in row["special_chars"]:
            assert chr(int(value[2:], 16)) in source


def test_catalogue_analysis_and_clean_samples() -> None:
    """Verify every shipped sample against live analyzer behavior and write reports."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from verify_samples import verify, write_docs

    rows, failures = verify()
    write_docs(rows)
    assert failures == 0, [(row["id"], row["problems"]) for row in rows if row["status"] == "FAIL"]
    assert len(rows) == 146


def test_api_samples_keep_legacy_opening_fields_and_add_metadata() -> None:
    """Ensure old UI sample fields remain present while new catalogue metadata is exposed."""
    samples = get_samples("python")
    assert any(item.id == "python-vuln-cmd-injection" for item in samples)
    item = next(item for item in samples if item.id == "py-i01")
    assert item.code and item.filename.endswith(".py") and item.category == "vulnerable"
    assert item.group == "python" and item.kind == "vulnerable"
