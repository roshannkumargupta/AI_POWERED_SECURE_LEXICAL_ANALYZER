"""Unit and integration tests for multi-language ML and cross-language evaluation."""

from __future__ import annotations

import json
import shutil
import time

import numpy as np
import pytest

from apsla.languages.cpp_lang.lexer import CppLexer
from apsla.languages.java_lang.lexer import JavaLexer
from apsla.languages.javascript_lang.lexer import JavaScriptLexer
from apsla.languages.python_lang.lexer import PythonLexer
from apsla.ml.features import FEATURE_SCHEMA_HASH
from apsla.ml.infer import ARTIFACTS_DIR, MLInferenceEngine
from apsla.ml.synth.cpp import generate_cpp_dataset
from apsla.ml.synth.java import generate_java_dataset
from apsla.ml.synth.javascript import generate_javascript_dataset
from apsla.ml.synth.python import generate_python_dataset
from apsla.ml.train import (
    prepare_language_arrays,
    split_language_data,
    train_pipeline,
)


def test_multilang_synthetic_generators() -> None:
    """Verifies that all language generators produce valid tokens, labels, and lossless code."""
    for lang, gen, lexer_cls in [
        ("python", generate_python_dataset, PythonLexer),
        ("java", generate_java_dataset, JavaLexer),
        ("javascript", generate_javascript_dataset, JavaScriptLexer),
        ("cpp", generate_cpp_dataset, CppLexer),
    ]:
        snippets = gen(count=20, seed=42)
        assert len(snippets) == 20
        for s in snippets:
            assert s.language == lang
            assert len(s.tokens) > 0
            assert len(s.token_labels) == len(s.tokens)
            # Lossless source code token reconstruction
            reconstructed = "".join(t.text for t in s.tokens)
            assert reconstructed == s.code, f"Lossless reconstruction failed for {lang}"
            assert s.snippet_id.startswith("synth-")
            assert len(s.template_family) > 0


def test_zero_group_leakage_in_splits() -> None:
    """Verifies that 70/15/15 group-aware splitting has exactly zero group overlap."""
    for lang, gen in [
        ("python", generate_python_dataset),
        ("java", generate_java_dataset),
        ("javascript", generate_javascript_dataset),
        ("cpp", generate_cpp_dataset),
    ]:
        snippets = gen(count=30, seed=42)
        prep = prepare_language_arrays(snippets, language=lang)
        splits = split_language_data(prep, seed=42)

        train_groups = splits["train"]["groups"]
        val_groups = splits["val"]["groups"]
        test_groups = splits["test"]["groups"]

        assert len(train_groups) > 0
        assert len(val_groups) > 0
        assert len(test_groups) > 0

        # Zero leakage mathematical guarantee
        assert not (train_groups & val_groups), f"Train-Val group leakage in {lang}"
        assert not (train_groups & test_groups), f"Train-Test group leakage in {lang}"
        assert not (val_groups & test_groups), f"Val-Test group leakage in {lang}"


def test_artifact_loading_and_schema_hash_validation() -> None:
    """Verifies that existing artifacts declare matching feature schema hash."""
    if not ARTIFACTS_DIR.exists():
        return
    for artifact_dir in ARTIFACTS_DIR.iterdir():
        if (
            not artifact_dir.is_dir()
            or artifact_dir.name.startswith("test_")
            or artifact_dir.name.startswith("tmp_")
        ):
            continue
        meta_file = artifact_dir / "meta.json"
        if not meta_file.exists():
            continue
        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
        assert meta.get("feature_schema_hash") == FEATURE_SCHEMA_HASH, (
            f"Schema hash mismatch in artifact {artifact_dir.name}"
        )


def test_fake_artifact_wrong_hash_disables_ml_mode() -> None:
    """Policy Test: A fake artifact with a corrupted schema hash forces ML mode to 'off'."""
    fake_dir = ARTIFACTS_DIR / "tmp_test_corrupted_hash"
    fake_dir.mkdir(parents=True, exist_ok=True)
    try:
        fake_meta = {
            "model_id": "tmp_test_corrupted_hash",
            "model_type": "logistic_regression",
            "feature_schema_hash": "bad_corrupted_hash_99999999999999999999999999999999",
            "feature_dim": 45,
            "thresholds": {"tau_malicious": 0.5},
            "temperature": 1.0,
        }
        with open(fake_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(fake_meta, f)

        engine = MLInferenceEngine(model_id="tmp_test_corrupted_hash")
        assert engine.is_available() is False
        assert engine.get_mode() == "off"

        # Predictions under off mode return all-SAFE default
        dummy_tokens = PythonLexer("x = 1").tokenize()
        probs = engine.predict_token_probabilities(dummy_tokens, language="python")
        assert len(probs) == len(dummy_tokens)
        assert np.all(probs[:, 0] == 1.0)
        assert np.all(probs[:, 1:] == 0.0)
    finally:
        if fake_dir.exists():
            shutil.rmtree(fake_dir)


def test_unsupported_language_disables_ml_mode() -> None:
    """Verifies that an unsupported or unmodeled language safely defaults to ml_mode='off'."""
    engine = MLInferenceEngine(language="unknown_esoteric_lang")
    assert engine.is_available("unknown_esoteric_lang") is False
    assert engine.get_mode("unknown_esoteric_lang") == "off"


@pytest.mark.slow
@pytest.mark.timeout(300)
def test_tiny_e2e_training_run_under_3_minutes() -> None:
    """CI Performance Guarantee: A fast multi-language training run finishes in under 3 minutes."""
    start_time = time.perf_counter()
    summary = train_pipeline(strategy="all", fast_mode=True, seed=42)
    elapsed = time.perf_counter() - start_time

    try:
        assert elapsed < 180.0, f"Training run took {elapsed:.2f}s, exceeding 3-minute limit!"
        assert "s1_separate" in summary
        assert "s2_joint" in summary
        assert "s3_transfer" in summary
    finally:
        for art_id in summary.get("saved_artifacts", []):
            art_dir = ARTIFACTS_DIR / art_id
            if art_dir.exists():
                shutil.rmtree(art_dir, ignore_errors=True)


def test_multilang_inference_prob_shapes() -> None:
    """Verifies token probability prediction across all four languages."""
    engine = MLInferenceEngine()
    if not engine.is_available():
        return

    codes = {
        "python": "import os\nos.system('ls')",
        "java": 'public class T { void f() { Runtime.getRuntime().exec("ls"); } }',
        "javascript": "const { exec } = require('child_process'); exec('ls');",
        "cpp": '#include <stdlib.h>\nvoid f() { system("ls"); }',
    }

    for lang, code in codes.items():
        tokens = (
            PythonLexer(code).tokenize()
            if lang == "python"
            else JavaLexer(code).tokenize()
            if lang == "java"
            else JavaScriptLexer(code).tokenize()
            if lang in ("javascript", "js")
            else CppLexer(code).tokenize()
        )
        probs = engine.predict_token_probabilities(tokens, language=lang)
        assert probs.shape == (len(tokens), 3)
        row_sums = np.sum(probs, axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-3)
