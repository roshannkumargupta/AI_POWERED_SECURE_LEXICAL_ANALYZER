"""Unit tests for Active Learning Retraining and Safety Gate."""

import json
from pathlib import Path

from scripts.retrain_with_feedback import extract_feedback_windows, retrain_with_feedback


def test_extract_feedback_windows_hard_negatives():
    """Verify snippets from feedback are converted into SAFE (0) labeled windows."""
    fake_records = [
        {
            "rule_id": "APS-PY-INJ-001",
            "language": "python",
            "fingerprint": "fp-1",
            "snippet": "import os\nos.system('echo safe')\n",
            "verdict": "false_positive",
        }
    ]

    windows = extract_feedback_windows(fake_records, target_language="python")
    assert len(windows["y"]) > 0
    # Every token window from the false positive is labeled SAFE (0)
    assert all(label == 0 for label in windows["y"])
    assert windows["3d"].shape[0] == len(windows["y"])
    assert windows["flat"].shape[0] == len(windows["y"])


def test_retrain_refuses_when_metrics_degrade(tmp_path: Path):
    """Verify safety gate refuses to replace artifact if external metric degrades."""
    fake_fb_file = tmp_path / "false_positives.jsonl"
    with open(fake_fb_file, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "rule_id": "APS-PY-INJ-001",
                    "language": "python",
                    "fingerprint": "fp-99",
                    "snippet": "print('hello world')",
                    "verdict": "false_positive",
                }
            )
            + "\n"
        )

    # Calling retrain_with_feedback with simulate_regression=True must trigger the refusal gate (returns False)
    passed = retrain_with_feedback(
        feedback_file=fake_fb_file,
        model_type="logistic_regression",
        language="python",
        fast_mode=True,
        simulate_regression=True,
    )
    assert passed is False, (
        "Retrain script must refuse (return False) when external metrics degrade"
    )
