"""Test that a small training run finishes within 60 seconds and produces valid artifacts."""

from __future__ import annotations

import shutil
import time

import pytest

from apsla.ml.features import FEATURE_SCHEMA_HASH
from apsla.ml.train import ARTIFACTS_ROOT, train_pipeline


@pytest.mark.slow
@pytest.mark.timeout(180)
def test_fast_training_run_under_60_seconds():
    artifact_dir = ARTIFACTS_ROOT / "test_fast_model"
    try:
        start_time = time.perf_counter()

        model_name, meta = train_pipeline(
            language="python",
            num_snippets=200,
            epochs=1,
            seed=42,
            model_id="test_fast_model",
            fast_mode=True,
        )

        elapsed = time.perf_counter() - start_time
        assert elapsed < 60.0, f"Training run took {elapsed:.2f}s, expected < 60s"

        assert model_name in (
            "logistic_regression",
            "random_forest",
            "hist_gradient_boosting",
            "windowed_bilstm",
        )
        assert meta["feature_schema_hash"] == FEATURE_SCHEMA_HASH
        assert meta["model_id"] == "test_fast_model"

        assert artifact_dir.exists()
        assert (artifact_dir / "meta.json").exists()

        # File size must be under 50 MB (52,428,800 bytes)
        assert meta["model_file_size_bytes"] < 50 * 1024 * 1024
    finally:
        if artifact_dir.exists():
            shutil.rmtree(artifact_dir, ignore_errors=True)
