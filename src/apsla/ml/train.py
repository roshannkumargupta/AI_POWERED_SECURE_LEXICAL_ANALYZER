"""Training pipeline for token security classifiers with group-aware splitting and leakage prevention."""

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
from apsla.ml.features import FEATURE_COUNT, FEATURE_SCHEMA_HASH, extract_file_features
from apsla.ml.models import UnifiedModelWrapper
from apsla.ml.synth.python import generate_python_dataset
from apsla.ml.windows import build_token_windows

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("apsla.ml.train")

ARTIFACTS_ROOT = Path(__file__).resolve().parent / "artifacts"


def train_pipeline(
    language: str = "python",
    num_snippets: int = 3000,
    epochs: int = 5,
    seed: int = 42,
    model_id: str | None = None,
    fast_mode: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Executes end-to-end dataset synthesis, group splitting, model training, and selection.

    Args:
        language: Programming language (default: 'python').
        num_snippets: Total synthetic snippets to generate (default: 3000).
        epochs: Epochs for neural training (default: 5).
        seed: Random seed for reproducibility (default: 42).
        model_id: Custom model artifact folder name.
        fast_mode: If True, uses reduced subset for fast CI test runs.

    Returns:
        tuple containing:
            - best_model_type (str): Identifier of the winning architecture.
            - meta (dict): Metadata dictionary saved in meta.json.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if fast_mode:
        num_snippets = min(num_snippets, 200)
        epochs = 1

    logger.info("Step 1: Generating %d synthetic Python snippets (seed=%d)...", num_snippets, seed)
    snippets = generate_python_dataset(count=num_snippets, seed=seed)

    # Compute deterministic dataset hash
    dataset_hasher = hashlib.sha256()
    for s in snippets:
        dataset_hasher.update(s.snippet_id.encode("utf-8"))
        dataset_hasher.update(s.code.encode("utf-8"))
    dataset_hash = dataset_hasher.hexdigest()
    logger.info("Dataset synthesized: %d snippets, hash=%s", len(snippets), dataset_hash[:12])

    # Step 2: Extract features & windows for all snippets
    logger.info("Step 2: Extracting 45-dim features and 9-token sliding windows...")
    all_3d: list[np.ndarray] = []
    all_flat: list[np.ndarray] = []
    all_y: list[np.ndarray] = []
    all_hashes: list[list[str]] = []
    all_groups: list[str] = []
    snippet_indices: list[int] = []

    for s_idx, snip in enumerate(snippets):
        feats, lang_id = extract_file_features(snip.tokens, language=language)
        w3d, wflat, wy, whashes = build_token_windows(snip.tokens, feats, labels=snip.token_labels)
        if len(wy) == 0:
            continue

        all_3d.append(w3d)
        all_flat.append(wflat)
        all_y.append(wy)
        all_hashes.append(whashes)

        group_id = f"{snip.language}_{snip.template_family}_{snip.snippet_id}"
        all_groups.append(group_id)
        snippet_indices.append(s_idx)

    # Step 3: Group-aware train / val / test split by (language, template_family, snippet_id)
    logger.info("Step 3: Performing group-aware split (70%% train, 15%% val, 15%% test)...")
    n_snippets = len(all_groups)
    group_indices = list(range(n_snippets))
    random.Random(seed).shuffle(group_indices)

    n_train_groups = int(0.70 * n_snippets)
    n_val_groups = int(0.15 * n_snippets)

    train_group_set = set(group_indices[:n_train_groups])
    val_group_set = set(group_indices[n_train_groups : n_train_groups + n_val_groups])
    test_group_set = set(group_indices[n_train_groups + n_val_groups :])

    # Assemble arrays for each split
    def _gather_split(
        indices_set: set[int],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
        split_3d = [all_3d[i] for i in indices_set]
        split_flat = [all_flat[i] for i in indices_set]
        split_y = [all_y[i] for i in indices_set]
        split_h: list[str] = []
        for i in indices_set:
            split_h.extend(all_hashes[i])
        return np.vstack(split_3d), np.vstack(split_flat), np.concatenate(split_y), split_h

    X_train_3d, X_train_flat, y_train, train_hashes = _gather_split(train_group_set)
    X_val_3d, X_val_flat, y_val, val_hashes = _gather_split(val_group_set)
    X_test_3d, X_test_flat, y_test, test_hashes = _gather_split(test_group_set)

    logger.info(
        "Initial split: Train=%d tokens, Val=%d tokens, Test=%d tokens",
        len(y_train),
        len(y_val),
        len(y_test),
    )

    # Step 4: De-duplication: remove near-duplicate windows from train appearing in val/test
    val_test_hashes = set(val_hashes) | set(test_hashes)
    keep_mask = [h not in val_test_hashes for h in train_hashes]
    num_removed = len(train_hashes) - sum(keep_mask)
    logger.info(
        "Step 4: De-duplication: removed %d near-duplicate windows from train split.", num_removed
    )

    X_train_3d = X_train_3d[keep_mask]
    X_train_flat = X_train_flat[keep_mask]
    y_train = y_train[keep_mask]

    # Save test split for evaluate.py
    cache_dir = Path(__file__).resolve().parent / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache_dir / "test_split.npz",
        X_test_3d=X_test_3d,
        X_test_flat=X_test_flat,
        y_test=y_test,
        dataset_hash=dataset_hash,
    )

    # Step 5: Train all 4 model architectures
    candidates = [
        "logistic_regression",
        "random_forest",
        "hist_gradient_boosting",
        "windowed_bilstm",
    ]

    best_model: UnifiedModelWrapper | None = None
    best_model_name = ""
    best_val_macro_f1 = -1.0
    model_val_metrics: dict[str, dict[str, float]] = {}

    for m_type in candidates:
        logger.info("Training candidate architecture: %s...", m_type)
        wrapper = UnifiedModelWrapper(model_type=m_type, seed=seed)
        wrapper.fit(
            X_train_3d,
            X_train_flat,
            y_train,
            epochs=epochs,
            val_data=(X_val_3d, X_val_flat, y_val, None),
        )

        val_probs = wrapper.predict_proba(X_val_3d, X_val_flat)
        val_preds = np.argmax(val_probs, axis=1)

        macro_f1 = float(f1_score(y_val, val_preds, average="macro", zero_division=0))
        prec = float(precision_score(y_val, val_preds, average="macro", zero_division=0))
        rec = float(recall_score(y_val, val_preds, average="macro", zero_division=0))

        logger.info(
            "Candidate %s -> Validation Macro-F1: %.4f (Prec: %.4f, Rec: %.4f)",
            m_type,
            macro_f1,
            prec,
            rec,
        )

        model_val_metrics[m_type] = {
            "macro_f1": round(macro_f1, 4),
            "macro_precision": round(prec, 4),
            "macro_recall": round(rec, 4),
        }

        if macro_f1 > best_val_macro_f1:
            best_val_macro_f1 = macro_f1
            best_model_name = m_type
            best_model = wrapper

    logger.info(
        "Step 6: Winning model selected: %s (Macro-F1: %.4f)", best_model_name, best_val_macro_f1
    )
    assert best_model is not None

    # Step 7: Tune temperature T and malicious threshold tau on validation set ONLY
    logger.info("Step 7: Tuning calibration temperature T and threshold tau on validation split...")
    raw_val_probs = best_model.predict_proba(X_val_3d, X_val_flat)
    T = fit_temperature(raw_val_probs, y_val)
    calibrated_val_probs = apply_temperature_scaling(raw_val_probs, temperature=T)

    # Sweep tau for MALICIOUS class (2) to balance recall and precision on validation
    best_tau = 0.5
    best_mal_f1 = -1.0
    for tau_candidate in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        preds = np.argmax(calibrated_val_probs, axis=1)
        preds[calibrated_val_probs[:, 2] >= tau_candidate] = 2
        f1_mal = f1_score(y_val == 2, preds == 2, zero_division=0)
        if f1_mal > best_mal_f1:
            best_mal_f1 = f1_mal
            best_tau = tau_candidate

    logger.info(
        "Calibration complete: T=%.3f, tau_malicious=%.2f (Validation Malicious F1: %.4f)",
        T,
        best_tau,
        best_mal_f1,
    )

    # Step 8: Save artifact to ml/artifacts/<model_id>/
    if not model_id:
        timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        model_id = f"{best_model_name}_{timestamp}"

    artifact_dir = ARTIFACTS_ROOT / model_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_file = best_model.save(artifact_dir)

    meta: dict[str, Any] = {
        "model_id": model_id,
        "model_type": best_model_name,
        "feature_schema_hash": FEATURE_SCHEMA_HASH,
        "feature_dim": FEATURE_COUNT,
        "thresholds": {"tau_malicious": best_tau},
        "temperature": round(T, 4),
        "validation_metrics": model_val_metrics[best_model_name],
        "all_candidate_metrics": model_val_metrics,
        "dataset_hash": dataset_hash,
        "seed": seed,
        "library_versions": {
            "torch": torch.__version__,
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
        },
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "model_file_size_bytes": os.path.getsize(model_file),
    }

    with open(artifact_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info("Artifact saved successfully to %s", artifact_dir)
    return best_model_name, meta


def main() -> None:
    """CLI entrypoint for training pipeline."""
    parser = argparse.ArgumentParser(
        prog="python -m apsla.ml.train",
        description="Train, tune, and calibrate token security classifiers for SecureLex IDE.",
    )
    parser.add_argument(
        "--lang", default="python", help="Target programming language (default: python)"
    )
    parser.add_argument(
        "--snippets", type=int, default=3000, help="Number of synthetic snippets (default: 3000)"
    )
    parser.add_argument(
        "--epochs", type=int, default=5, help="Training epochs for neural models (default: 5)"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Deterministic random seed (default: 42)"
    )
    parser.add_argument(
        "--model-id", default=None, help="Custom identifier for saved model artifact"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Fast training mode for quick testing/CI"
    )

    args = parser.parse_args()
    train_pipeline(
        language=args.lang,
        num_snippets=args.snippets,
        epochs=args.epochs,
        seed=args.seed,
        model_id=args.model_id,
        fast_mode=args.fast,
    )


if __name__ == "__main__":
    main()
