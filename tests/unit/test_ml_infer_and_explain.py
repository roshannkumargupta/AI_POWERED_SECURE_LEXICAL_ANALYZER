"""Unit tests for ML inference engine and explainability."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from apsla.ml.explain import FEATURE_GROUPS, explain_token_prediction
from apsla.ml.infer import MLInferenceEngine
from apsla.ml.models import UnifiedModelWrapper


def test_missing_model_fallback_is_off(tmp_path: Path, monkeypatch):
    """Zero silent fallback: missing model leads strictly to ml_mode='off'."""
    monkeypatch.setattr("apsla.ml.infer.ARTIFACTS_DIR", tmp_path / "nonexistent")

    engine = MLInferenceEngine()
    assert not engine.is_available()
    assert engine.get_mode() == "off"
    assert engine.get_model_id() == "none"


def test_schema_mismatch_disables_ml(tmp_path: Path, monkeypatch):
    """Zero silent fallback: schema mismatch leads strictly to ml_mode='off'."""
    artifact_dir = tmp_path / "fake_model"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "model_id": "fake_model",
        "model_type": "logistic_regression",
        "feature_schema_hash": "bad_hash_12345",
        "temperature": 1.0,
    }
    with open(artifact_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    monkeypatch.setattr("apsla.ml.infer.ARTIFACTS_DIR", tmp_path)

    engine = MLInferenceEngine(model_id="fake_model")
    assert not engine.is_available()
    assert engine.get_mode() == "off"


def test_feature_group_occlusion_explainability():
    """Validates that explain_token_prediction returns drops for all defined feature groups."""
    wrapper = UnifiedModelWrapper("logistic_regression", seed=42)
    # Fit a tiny dummy model
    X_flat = np.zeros((10, 405), dtype=np.float32)
    X_flat[0, :] = 1.0
    y = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0], dtype=np.int64)
    wrapper.fit(np.zeros((10, 9, 45), dtype=np.float32), X_flat, y)

    w3d = np.ones((1, 9, 45), dtype=np.float32)
    wflat = np.ones((1, 405), dtype=np.float32)

    drops = explain_token_prediction(wrapper, w3d, wflat, target_class=2)
    assert len(drops) == len(FEATURE_GROUPS)
    for g_name in FEATURE_GROUPS:
        assert g_name in drops
        assert isinstance(drops[g_name], float)
