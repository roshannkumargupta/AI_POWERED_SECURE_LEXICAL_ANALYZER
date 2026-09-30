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


def save_feedback(record: dict[str, Any], filepath: Path | None = None) -> bool:
    """Append a user feedback record to the append-only JSONL storage.

    Args:
        record: Dictionary containing finding_fingerprint, rule_id, language,
            verdict, snippet, etc.
        filepath: Optional custom file path (primarily for testing).

    Returns:
        True if successfully saved, False otherwise.
    """
    target_file = filepath or FEEDBACK_FILE
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        if "timestamp" not in record:
            record["timestamp"] = datetime.datetime.now(datetime.UTC).isoformat()

        with open(target_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info(
            "Saved feedback for rule %s (fingerprint: %s)",
            record.get("rule_id"),
            record.get("finding_fingerprint"),
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
            for line in f:
                line = line.strip()
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
