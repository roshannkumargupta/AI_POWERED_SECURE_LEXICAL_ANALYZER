"""Training pipeline for token security classifiers with multi-language strategies and leak-free splitting."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
import torch
from sklearn.metrics import f1_score, precision_score, recall_score

from apsla.ml.calibrate import apply_temperature_scaling, fit_temperature
from apsla.ml.features import (
    FEATURE_COUNT,
    FEATURE_SCHEMA_HASH,
    LANGUAGE_IDS,
    extract_file_features,
)
from apsla.ml.models import UnifiedModelWrapper
from apsla.ml.synth.common import SyntheticSnippet
from apsla.ml.synth.cpp import generate_cpp_dataset
from apsla.ml.synth.java import generate_java_dataset
from apsla.ml.synth.javascript import generate_javascript_dataset
from apsla.ml.synth.python import generate_python_dataset
from apsla.ml.windows import build_token_windows

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("apsla.ml.train")

ARTIFACTS_ROOT = Path(__file__).resolve().parent / "artifacts"
CACHE_DIR = Path(__file__).resolve().parent / "cache"

SUPPORTED_LANGUAGES: tuple[str, ...] = ("python", "java", "javascript", "cpp")
MODEL_ARCHITECTURES: tuple[str, ...] = (
    "logistic_regression",
    "random_forest",
    "hist_gradient_boosting",
    "windowed_bilstm",
)


def synthesize_snippets(
    languages: tuple[str, ...] = SUPPORTED_LANGUAGES,
    num_snippets: int = 3000,
    seed: int = 42,
    fast_mode: bool = False,
) -> dict[str, list[SyntheticSnippet]]:
    """Synthesizes deterministic snippets for requested languages."""
    actual_snippets = min(num_snippets, 150) if fast_mode else num_snippets
    logger.info("Synthesizing %d snippets per language (seed=%d)...", actual_snippets, seed)

    out: dict[str, list[SyntheticSnippet]] = {}
    for lang in languages:
        if lang == "python":
            out["python"] = generate_python_dataset(count=actual_snippets, seed=seed)
        elif lang == "java":
            out["java"] = generate_java_dataset(count=actual_snippets, seed=seed + 1)
        elif lang in ("javascript", "js"):
            out["javascript"] = generate_javascript_dataset(count=actual_snippets, seed=seed + 2)
        elif lang in ("cpp", "c++"):
            out["cpp"] = generate_cpp_dataset(count=actual_snippets, seed=seed + 3)
        else:
            raise ValueError(f"Unsupported language: {lang}")
        logger.info("Language %s: synthesized %d snippets.", lang, len(out[lang]))
    return out


def prepare_language_arrays(
    snippets: list[SyntheticSnippet],
    language: str,
) -> dict[str, Any]:
    """Extracts features and builds context windows for snippets of a single language."""
    all_3d: list[np.ndarray] = []
    all_flat: list[np.ndarray] = []
    all_y: list[np.ndarray] = []
    all_hashes: list[list[str]] = []
    all_groups: list[str] = []
    all_lang_ids: list[int] = []

    target_lang_id = LANGUAGE_IDS.get(language.lower(), 0)

    for snip in snippets:
        feats, _lang_id = extract_file_features(snip.tokens, language=language)
        w3d, wflat, wy, whashes = build_token_windows(snip.tokens, feats, labels=snip.token_labels)
        if wy is None or len(wy) == 0:
            continue

        all_3d.append(w3d)
        all_flat.append(wflat)
        all_y.append(wy)
        all_hashes.append(whashes)

        group_id = f"{snip.language}_{snip.template_family}_{snip.snippet_id}"
        all_groups.append(group_id)
        all_lang_ids.append(target_lang_id)

    return {
        "3d": all_3d,
        "flat": all_flat,
        "y": all_y,
        "hashes": all_hashes,
        "groups": all_groups,
        "lang_id": target_lang_id,
    }


def split_language_data(
    data: dict[str, Any],
    seed: int = 42,
) -> dict[str, dict[str, Any]]:
    """Performs leak-free group split (70% train, 15% val, 15% test) by group ID."""
    all_groups = data["groups"]
    n_snippets = len(all_groups)
    group_indices = list(range(n_snippets))
    random.Random(seed).shuffle(group_indices)

    n_train = int(0.70 * n_snippets)
    n_val = int(0.15 * n_snippets)

    train_idx = set(group_indices[:n_train])
    val_idx = set(group_indices[n_train : n_train + n_val])
    test_idx = set(group_indices[n_train + n_val :])

    # Zero group overlap verification
    train_groups = {all_groups[i] for i in train_idx}
    val_groups = {all_groups[i] for i in val_idx}
    test_groups = {all_groups[i] for i in test_idx}

    assert not (train_groups & val_groups), "Leakage detected: train & val groups overlap!"
    assert not (train_groups & test_groups), "Leakage detected: train & test groups overlap!"
    assert not (val_groups & test_groups), "Leakage detected: val & test groups overlap!"

    def _assemble(indices: set[int]) -> dict[str, Any]:
        if not indices:
            return {
                "3d": np.empty((0, 9, FEATURE_COUNT), dtype=np.float32),
                "flat": np.empty((0, 9 * FEATURE_COUNT), dtype=np.float32),
                "y": np.empty((0,), dtype=np.int64),
                "lang_ids": np.empty((0,), dtype=np.int64),
                "hashes": [],
                "groups": set(),
            }
        split_3d = [data["3d"][i] for i in indices]
        split_flat = [data["flat"][i] for i in indices]
        split_y = [data["y"][i] for i in indices]
        hashes: list[str] = []
        for i in indices:
            hashes.extend(data["hashes"][i])

        y_arr = np.concatenate(split_y)
        lang_ids_arr = np.full((len(y_arr),), fill_value=data["lang_id"], dtype=np.int64)
        return {
            "3d": np.vstack(split_3d),
            "flat": np.vstack(split_flat),
            "y": y_arr,
            "lang_ids": lang_ids_arr,
            "hashes": hashes,
            "groups": {all_groups[i] for i in indices},
        }

    train_split = _assemble(train_idx)
    val_split = _assemble(val_idx)
    test_split = _assemble(test_idx)

    # De-duplicate: remove train windows that occur in val or test
    val_test_hashes = set(val_split["hashes"]) | set(test_split["hashes"])
    keep_mask = [h not in val_test_hashes for h in train_split["hashes"]]
    train_split["3d"] = train_split["3d"][keep_mask]
    train_split["flat"] = train_split["flat"][keep_mask]
    train_split["y"] = train_split["y"][keep_mask]
    train_split["lang_ids"] = train_split["lang_ids"][keep_mask]

    return {
        "train": train_split,
        "val": val_split,
        "test": test_split,
    }


def evaluate_model_on_val(
    model: UnifiedModelWrapper,
    val_split: dict[str, Any],
) -> dict[str, float]:
    """Computes validation metrics using validation set ONLY."""
    probs = model.predict_proba(
        val_split["3d"],
        val_split["flat"],
        lang_ids=val_split["lang_ids"],
    )
    preds = np.argmax(probs, axis=1)
    y_val = val_split["y"]

    macro_f1 = float(f1_score(y_val, preds, average="macro", zero_division=0))
    macro_prec = float(precision_score(y_val, preds, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_val, preds, average="macro", zero_division=0))

    return {
        "macro_f1": round(macro_f1, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
    }


def tune_calibration_and_threshold(
    model: UnifiedModelWrapper,
    val_split: dict[str, Any],
) -> tuple[float, float, float]:
    """Tunes temperature scaling T and malicious threshold tau on validation split ONLY."""
    raw_probs = model.predict_proba(
        val_split["3d"],
        val_split["flat"],
        lang_ids=val_split["lang_ids"],
    )
    y_val = val_split["y"]
    T = fit_temperature(raw_probs, y_val)
    cal_probs = apply_temperature_scaling(raw_probs, temperature=T)

    best_tau = 0.5
    best_mal_f1 = -1.0
    for tau_candidate in [0.5, 0.6, 0.7, 0.8]:
        preds = np.argmax(cal_probs, axis=1)
        preds[cal_probs[:, 2] >= tau_candidate] = 2
        f1_mal = f1_score(y_val == 2, preds == 2, zero_division=0)
        if f1_mal > best_mal_f1:
            best_mal_f1 = f1_mal
            best_tau = tau_candidate

    return round(T, 4), round(best_tau, 2), round(float(best_mal_f1), 4)


def run_strategy_separate(
    splits: dict[str, dict[str, dict[str, Any]]],
    epochs: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Strategy S1: Trains separate individual models per language."""
    logger.info("=== Running Strategy S1: Separate Models Per Language ===")
    results: dict[str, Any] = {}

    for lang in splits:
        lang_train = splits[lang]["train"]
        lang_val = splits[lang]["val"]

        best_model: UnifiedModelWrapper | None = None
        best_model_name = ""
        best_val_f1 = -1.0
        lang_models_metrics: dict[str, Any] = {}

        for m_type in MODEL_ARCHITECTURES:
            logger.info("S1 [%s] Training candidate %s...", lang, m_type)
            wrapper = UnifiedModelWrapper(model_type=m_type, seed=seed)
            wrapper.fit(
                lang_train["3d"],
                lang_train["flat"],
                lang_train["y"],
                lang_ids=lang_train["lang_ids"],
                epochs=epochs,
            )
            metrics = evaluate_model_on_val(wrapper, lang_val)
            lang_models_metrics[m_type] = metrics
            logger.info("S1 [%s] %s -> Val Macro-F1: %.4f", lang, m_type, metrics["macro_f1"])

            if metrics["macro_f1"] > best_val_f1:
                best_val_f1 = metrics["macro_f1"]
                best_model_name = m_type
                best_model = wrapper

        assert best_model is not None
        T, tau, mal_f1 = tune_calibration_and_threshold(best_model, lang_val)

        results[lang] = {
            "best_architecture": best_model_name,
            "best_val_macro_f1": best_val_f1,
            "temperature": T,
            "tau_malicious": tau,
            "val_malicious_f1": mal_f1,
            "candidate_metrics": lang_models_metrics,
            "model_instance": best_model,
        }

    return results


def run_strategy_joint(
    splits: dict[str, dict[str, dict[str, Any]]],
    epochs: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Strategy S2: Trains joint models across all 4 languages with language embeddings/one-hot."""
    logger.info("=== Running Strategy S2: Joint Multi-Language Model ===")

    # Combine training and validation data across all 4 languages
    train_3d = np.vstack([splits[lang]["train"]["3d"] for lang in SUPPORTED_LANGUAGES])
    train_flat = np.vstack([splits[lang]["train"]["flat"] for lang in SUPPORTED_LANGUAGES])
    train_y = np.concatenate([splits[lang]["train"]["y"] for lang in SUPPORTED_LANGUAGES])
    train_lang_ids = np.concatenate(
        [splits[lang]["train"]["lang_ids"] for lang in SUPPORTED_LANGUAGES]
    )

    val_3d = np.vstack([splits[lang]["val"]["3d"] for lang in SUPPORTED_LANGUAGES])
    val_flat = np.vstack([splits[lang]["val"]["flat"] for lang in SUPPORTED_LANGUAGES])
    val_y = np.concatenate([splits[lang]["val"]["y"] for lang in SUPPORTED_LANGUAGES])
    val_lang_ids = np.concatenate([splits[lang]["val"]["lang_ids"] for lang in SUPPORTED_LANGUAGES])

    joint_val_split = {
        "3d": val_3d,
        "flat": val_flat,
        "y": val_y,
        "lang_ids": val_lang_ids,
    }

    best_model: UnifiedModelWrapper | None = None
    best_model_name = ""
    best_val_f1 = -1.0
    candidate_metrics: dict[str, Any] = {}
    per_language_val_metrics: dict[str, dict[str, float]] = {}

    for m_type in MODEL_ARCHITECTURES:
        logger.info("S2 [Joint] Training candidate %s with language features...", m_type)
        wrapper = UnifiedModelWrapper(model_type=m_type, seed=seed)
        wrapper.fit(
            train_3d,
            train_flat,
            train_y,
            lang_ids=train_lang_ids,
            use_lang_features=True,
            epochs=epochs,
        )
        metrics = evaluate_model_on_val(wrapper, joint_val_split)
        candidate_metrics[m_type] = metrics
        logger.info("S2 [Joint] %s -> Overall Val Macro-F1: %.4f", m_type, metrics["macro_f1"])

        if metrics["macro_f1"] > best_val_f1:
            best_val_f1 = metrics["macro_f1"]
            best_model_name = m_type
            best_model = wrapper

    assert best_model is not None
    T, tau, mal_f1 = tune_calibration_and_threshold(best_model, joint_val_split)

    # Evaluate winning joint model on each individual language validation split
    for lang in SUPPORTED_LANGUAGES:
        per_language_val_metrics[lang] = evaluate_model_on_val(best_model, splits[lang]["val"])

    return {
        "best_architecture": best_model_name,
        "best_val_macro_f1": best_val_f1,
        "temperature": T,
        "tau_malicious": tau,
        "val_malicious_f1": mal_f1,
        "candidate_metrics": candidate_metrics,
        "per_language_val_metrics": per_language_val_metrics,
        "model_instance": best_model,
    }


def run_strategy_transfer(
    splits: dict[str, dict[str, dict[str, Any]]],
    epochs: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Strategy S3: Transfer learning from Python base model fine-tuned on 20% of target languages."""
    logger.info("=== Running Strategy S3: Transfer Learning (BiLSTM) ===")

    # Train base WindowedBiLSTM on Python train split
    py_train = splits["python"]["train"]
    py_val = splits["python"]["val"]

    logger.info("S3: Training base WindowedBiLSTM model on Python training data...")
    base_bilstm = UnifiedModelWrapper(model_type="windowed_bilstm", seed=seed)
    base_bilstm.fit(
        py_train["3d"],
        py_train["flat"],
        py_train["y"],
        lang_ids=py_train["lang_ids"],
        epochs=epochs,
    )
    base_py_metrics = evaluate_model_on_val(base_bilstm, py_val)
    logger.info("S3: Base Python model validation Macro-F1: %.4f", base_py_metrics["macro_f1"])

    transfer_results: dict[str, Any] = {
        "base_model": "windowed_bilstm",
        "python_base_val_macro_f1": base_py_metrics["macro_f1"],
        "target_languages": {},
        "tree_models_note": (
            "Tree models (RandomForest, HistGradientBoosting) do not support parameter transfer learning "
            "on a 20% slice without full retraining; warm_start merely appends new trees without adapting old splits."
        ),
    }

    # For each other language: fine-tune on 20% of training data
    for target_lang in ("java", "javascript", "cpp"):
        target_train = splits[target_lang]["train"]
        target_val = splits[target_lang]["val"]

        # Take 20% of target language training slice
        n_samples = len(target_train["y"])
        n_slice = max(1, int(0.20 * n_samples))
        slice_3d = target_train["3d"][:n_slice]
        slice_y = target_train["y"][:n_slice]
        slice_lang_ids = target_train["lang_ids"][:n_slice]

        finetuned = base_bilstm.clone()
        finetuned.finetune_neural(
            slice_3d,
            slice_y,
            lang_ids=slice_lang_ids,
            epochs=max(2, epochs - 1),
            lr=5e-4,
        )

        val_metrics = evaluate_model_on_val(finetuned, target_val)
        T, tau, mal_f1 = tune_calibration_and_threshold(finetuned, target_val)

        logger.info(
            "S3 Transfer -> %s (fine-tuned on 20%%): Val Macro-F1: %.4f",
            target_lang,
            val_metrics["macro_f1"],
        )
        transfer_results["target_languages"][target_lang] = {
            "val_macro_f1": val_metrics["macro_f1"],
            "temperature": T,
            "tau_malicious": tau,
            "val_malicious_f1": mal_f1,
            "model_instance": finetuned,
        }

    return transfer_results


def save_artifact(
    model: UnifiedModelWrapper,
    model_id: str,
    meta_extra: dict[str, Any],
) -> Path:
    """Saves model weights and meta.json to ARTIFACTS_ROOT / model_id."""
    target_dir = ARTIFACTS_ROOT / model_id
    target_dir.mkdir(parents=True, exist_ok=True)
    model_file = model.save(target_dir)

    meta: dict[str, Any] = {
        "model_id": model_id,
        "model_type": model.model_type,
        "feature_schema_hash": FEATURE_SCHEMA_HASH,
        "feature_dim": FEATURE_COUNT,
        "use_lang_features": model.use_lang_features,
        "library_versions": {
            "torch": torch.__version__,
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
        },
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "model_file_size_bytes": os.path.getsize(model_file),
        **meta_extra,
    }

    with open(target_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info("Saved artifact %s to %s", model_id, target_dir)
    return target_dir


def train_pipeline(
    strategy: str = "auto",
    language: str = "python",
    num_snippets: int = 3000,
    epochs: int = 5,
    seed: int = 42,
    model_id: str | None = None,
    fast_mode: bool = False,
) -> TrainingSummary:
    """End-to-end training pipeline comparing S1 (separate), S2 (joint), and S3 (transfer)."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if strategy in ("auto", None):
        strategy = "all" if language == "all" else "separate"

    if strategy in ("all", "joint", "transfer"):
        active_languages = SUPPORTED_LANGUAGES
    else:
        active_languages = (language,)

    if fast_mode:
        num_snippets = min(num_snippets, 150)
        epochs = 1

    # 1. Synthesize multi-language snippets
    snippets_by_lang = synthesize_snippets(
        languages=active_languages,
        num_snippets=num_snippets,
        seed=seed,
        fast_mode=fast_mode,
    )

    # Compute overall dataset hash
    hasher = hashlib.sha256()
    for snips in snippets_by_lang.values():
        for s in snips:
            hasher.update(s.snippet_id.encode("utf-8"))
            hasher.update(s.code.encode("utf-8"))
    dataset_hash = hasher.hexdigest()

    # 2. Extract features, windows, and perform group splits per language
    splits: dict[str, dict[str, dict[str, Any]]] = {}
    for lang in active_languages:
        prep = prepare_language_arrays(snippets_by_lang[lang], language=lang)
        splits[lang] = split_language_data(prep, seed=seed)
        logger.info(
            "Split [%s]: Train=%d, Val=%d, Test=%d tokens",
            lang,
            len(splits[lang]["train"]["y"]),
            len(splits[lang]["val"]["y"]),
            len(splits[lang]["test"]["y"]),
        )

    # Cache held-out test splits for evaluate.py (strictly touched once per final report)
    if set(active_languages) == set(SUPPORTED_LANGUAGES):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        test_3d_all = np.vstack([splits[lang]["test"]["3d"] for lang in SUPPORTED_LANGUAGES])
        test_flat_all = np.vstack([splits[lang]["test"]["flat"] for lang in SUPPORTED_LANGUAGES])
        test_y_all = np.concatenate([splits[lang]["test"]["y"] for lang in SUPPORTED_LANGUAGES])
        test_lang_all = np.concatenate(
            [splits[lang]["test"]["lang_ids"] for lang in SUPPORTED_LANGUAGES]
        )

        np.savez_compressed(
            CACHE_DIR / "multilang_test_split.npz",
            X_test_3d=test_3d_all,
            X_test_flat=test_flat_all,
            y_test=test_y_all,
            lang_ids_test=test_lang_all,
            dataset_hash=dataset_hash,
        )
        # Also save backward-compatible test_split.npz
        np.savez_compressed(
            CACHE_DIR / "test_split.npz",
            X_test_3d=test_3d_all,
            X_test_flat=test_flat_all,
            y_test=test_y_all,
            lang_ids_test=test_lang_all,
            dataset_hash=dataset_hash,
        )

    s1_results: dict[str, Any] = {}
    s2_results: dict[str, Any] = {}
    s3_results: dict[str, Any] = {}

    if strategy in ("separate", "all"):
        s1_results = run_strategy_separate(splits, epochs=epochs, seed=seed)
    if strategy in ("joint", "all"):
        s2_results = run_strategy_joint(splits, epochs=epochs, seed=seed)
    if strategy in ("transfer", "all"):
        s3_results = run_strategy_transfer(splits, epochs=epochs, seed=seed)

    # 3. Model Selection based on VALIDATION macro-F1
    logger.info("=== Selecting Winning Artifacts Based on Validation Macro-F1 ===")
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")

    # Evaluate S2 Joint vs S1 Separate
    saved_artifacts: list[str] = []

    # If S2 was run, save the joint artifact as the primary multi-language engine
    if s2_results:
        joint_model: UnifiedModelWrapper = s2_results["model_instance"]
        joint_id = model_id or f"joint_{joint_model.model_type}_{timestamp}"
        save_artifact(
            joint_model,
            joint_id,
            meta_extra={
                "strategy": "joint",
                "supported_languages": list(SUPPORTED_LANGUAGES),
                "language": "all",
                "thresholds": {"tau_malicious": s2_results["tau_malicious"]},
                "temperature": s2_results["temperature"],
                "validation_macro_f1": s2_results["best_val_macro_f1"],
                "candidate_metrics": s2_results["candidate_metrics"],
                "per_language_val_metrics": s2_results["per_language_val_metrics"],
                "dataset_hash": dataset_hash,
                "seed": seed,
            },
        )
        saved_artifacts.append(joint_id)

    # If S1 was run, also save separate per-language artifacts
    if s1_results:
        for lang, res in s1_results.items():
            lang_model: UnifiedModelWrapper = res["model_instance"]
            lang_art_id = (
                model_id
                if (model_id and len(s1_results) == 1)
                else f"separate_{lang}_{lang_model.model_type}_{timestamp}"
            )
            save_artifact(
                lang_model,
                lang_art_id,
                meta_extra={
                    "strategy": "separate",
                    "supported_languages": [lang],
                    "language": lang,
                    "thresholds": {"tau_malicious": res["tau_malicious"]},
                    "temperature": res["temperature"],
                    "validation_macro_f1": res["best_val_macro_f1"],
                    "candidate_metrics": res["candidate_metrics"],
                    "dataset_hash": dataset_hash,
                    "seed": seed,
                },
            )
            saved_artifacts.append(lang_art_id)

    summary: dict[str, Any] = {
        "strategy": strategy,
        "dataset_hash": dataset_hash,
        "saved_artifacts": saved_artifacts,
        "s1_separate": {
            k: {
                "best_architecture": v["best_architecture"],
                "best_val_macro_f1": v["best_val_macro_f1"],
                "candidate_metrics": v["candidate_metrics"],
            }
            for k, v in s1_results.items()
        }
        if s1_results
        else {},
        "s2_joint": {
            "best_architecture": s2_results.get("best_architecture"),
            "best_val_macro_f1": s2_results.get("best_val_macro_f1"),
            "candidate_metrics": s2_results.get("candidate_metrics"),
            "per_language_val_metrics": s2_results.get("per_language_val_metrics"),
        }
        if s2_results
        else {},
        "s3_transfer": {
            "base_model": s3_results.get("base_model"),
            "python_base_val_macro_f1": s3_results.get("python_base_val_macro_f1"),
            "target_languages": {
                k: {"val_macro_f1": v["val_macro_f1"]}
                for k, v in s3_results.get("target_languages", {}).items()
            },
            "tree_models_note": s3_results.get("tree_models_note"),
        }
        if s3_results
        else {},
    }

    # Populate backward-compatible keys for Phase 4 tests
    best_name = "random_forest"
    if s2_results:
        best_name = s2_results.get("best_architecture", "random_forest")
    elif s1_results:
        target_res = s1_results.get(language) or next(iter(s1_results.values()))
        best_name = target_res.get("best_architecture", "random_forest")

    target_art_id = saved_artifacts[0] if saved_artifacts else ""
    meta_dict: dict[str, Any] = {}
    if target_art_id and (ARTIFACTS_ROOT / target_art_id / "meta.json").exists():
        with open(ARTIFACTS_ROOT / target_art_id / "meta.json", encoding="utf-8") as f:
            meta_dict = json.load(f)

    summary["best_model_name"] = best_name
    summary["meta"] = meta_dict

    # Save summary report
    with open(CACHE_DIR / "strategy_comparison_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Training pipeline completed successfully.")
    return TrainingSummary(summary)


class TrainingSummary(dict):
    """Summary dictionary supporting backward-compatible 2-tuple unpacking (model_name, meta)."""

    def __iter__(self):
        best_name = self.get("best_model_name") or "random_forest"
        meta = self.get("meta") or dict(self)
        return iter([best_name, meta])


def main() -> None:
    """CLI entrypoint for training pipeline."""
    parser = argparse.ArgumentParser(
        prog="python -m apsla.ml.train",
        description="Train, tune, and compare token security classifiers across multiple languages.",
    )
    parser.add_argument(
        "--strategy",
        choices=["all", "separate", "joint", "transfer"],
        default="all",
        help="Training strategy to execute: separate (S1), joint (S2), transfer (S3), or all (compare all three)",
    )
    parser.add_argument(
        "--lang",
        default="python",
        help="Target language when training a specific single language (default: python)",
    )
    parser.add_argument(
        "--snippets",
        type=int,
        default=3000,
        help="Number of synthetic snippets per language (default: 3000)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Training epochs for neural models (default: 5)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed (default: 42)",
    )
    parser.add_argument(
        "--model-id",
        default=None,
        help="Custom identifier for saved model artifact",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast training mode for quick testing/CI runs (< 3 minutes)",
    )

    args = parser.parse_args()
    train_pipeline(
        strategy=args.strategy,
        language=args.lang,
        num_snippets=args.snippets,
        epochs=args.epochs,
        seed=args.seed,
        model_id=args.model_id,
        fast_mode=args.fast,
    )


if __name__ == "__main__":
    main()
