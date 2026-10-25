"""Local storage engine for user false-positive feedback."""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Final

logger = logging.getLogger("apsla.feedback.store")

FEEDBACK_DIR: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "feedback"
)
FEEDBACK_FILE: Final[Path] = FEEDBACK_DIR / "false_positives.jsonl"


def save_feedback(
    record: dict[str, Any] | None = None,
    filepath: Path | None = None,
    **kwargs: Any,
) -> bool:
    """Append a user feedback record to the append-only JSONL storage.

    Enforces feedback schema:
    {timestamp, language, rule_id, fingerprint, snippet (max 400 chars), verdict, note}

    Args:
        record: Dictionary containing finding feedback information, or pass as kwargs.
        filepath: Optional custom file path (primarily for testing).
        **kwargs: Additional or alternative fields.

    Returns:
        True if successfully saved, False otherwise.
    """
    rec = dict(record) if record is not None else {}
    rec.update(kwargs)
    target_file = filepath or FEEDBACK_FILE
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = rec.get("timestamp") or datetime.datetime.now(datetime.UTC).isoformat()
        language = str(rec.get("language") or "python")
        rule_id = str(rec.get("rule_id") or "")
        fingerprint = str(rec.get("fingerprint") or rec.get("finding_fingerprint") or "")
        raw_snippet = str(rec.get("snippet") or "")
        snippet = raw_snippet[:400]
        verdict = str(rec.get("verdict") or "false_positive")
        note = str(rec.get("note") or "")

        normalized: dict[str, Any] = {
            "timestamp": timestamp,
            "language": language,
            "rule_id": rule_id,
            "fingerprint": fingerprint,
            "snippet": snippet,
            "verdict": verdict,
            "note": note,
        }
        # Retain backward-compatible fields if supplied
        for key in ("finding_fingerprint", "filename", "line"):
            if key in rec and key not in normalized:
                normalized[key] = rec[key]

        with open(target_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(normalized, ensure_ascii=False) + "\n")

        logger.info(
            "Saved feedback for rule %s (fingerprint: %s)",
            rule_id,
            fingerprint,
        )
        return True
    except Exception as exc:
        logger.error("Failed to append feedback record: %s", exc)
        return False


def load_all_feedback(filepath: Path | None = None) -> list[dict[str, Any]]:
    """Load all feedback records from the JSONL storage.

    Args:
        filepath: Optional custom file path.

    Returns:
        List of deserialized feedback record dictionaries.
    """
    target_file = filepath or FEEDBACK_FILE
    if not target_file.exists():
        return []

    records: list[dict[str, Any]] = []
    try:
        with open(target_file, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception as exc:
        logger.error("Failed to load feedback records: %s", exc)
    return records


def clear_feedback(filepath: Path | None = None) -> None:
    """Clear all records from feedback storage (useful for testing)."""
    target_file = filepath or FEEDBACK_FILE
    if target_file.exists():
        try:
            target_file.unlink()
        except Exception as exc:
            logger.warning("Failed to remove feedback file: %s", exc)


clear_feedback_file = clear_feedback
