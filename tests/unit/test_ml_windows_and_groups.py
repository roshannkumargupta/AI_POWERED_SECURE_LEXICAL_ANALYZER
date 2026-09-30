"""Unit tests for sliding 9-token windows and group-aware dataset splitting."""

from __future__ import annotations

import random

import numpy as np

from apsla.languages.python_lang.lexer import PythonLexer
from apsla.ml.features import extract_file_features
from apsla.ml.synth.python import generate_python_dataset
from apsla.ml.windows import build_token_windows


def test_window_shape_and_padding():
    code = "x = 10\ny = 20\n"
    tokens = PythonLexer(code).tokenize()
    N = len(tokens)
    assert N > 0

    features, _ = extract_file_features(tokens)
    labels = [0] * N
    labels[0] = 2  # Mark first token MALICIOUS

    win_3d, win_flat, y_out, hashes = build_token_windows(tokens, features, labels=labels)

    assert win_3d.shape == (N, 9, 45)
    assert win_flat.shape == (N, 405)
    assert y_out is not None
    assert len(y_out) == N
    assert len(hashes) == N

    # The label must strictly belong to the center token
    assert y_out[0] == 2
    assert y_out[1] == 0

    # Token 0 is at document start; the 4 left context positions (indices 0..3 in window) must be zero padded
    for left_idx in range(4):
        np.testing.assert_array_equal(win_3d[0, left_idx, :], np.zeros(45, dtype=np.float32))

    # Token N-1 is at document end; the 4 right context positions (indices 5..8 in window) must be zero padded
    for right_idx in range(5, 9):
        np.testing.assert_array_equal(win_3d[N - 1, right_idx, :], np.zeros(45, dtype=np.float32))


def test_group_split_zero_leakage():
    """Validates that splitting by (language, template_family, snippet_id) produces zero group leakage."""
    snippets = generate_python_dataset(count=100, seed=42)
    assert len(snippets) == 100

    groups = [f"{s.language}_{s.template_family}_{s.snippet_id}" for s in snippets]
    unique_groups = list(set(groups))
    assert len(unique_groups) == 100

    indices = list(range(len(groups)))
    random.Random(42).shuffle(indices)

    n_train = int(0.7 * len(indices))
    n_val = int(0.15 * len(indices))

    train_groups = {groups[i] for i in indices[:n_train]}
    val_groups = {groups[i] for i in indices[n_train : n_train + n_val]}
    test_groups = {groups[i] for i in indices[n_train + n_val :]}

    # Zero overlap across all pairwise splits
    assert len(train_groups.intersection(val_groups)) == 0
    assert len(train_groups.intersection(test_groups)) == 0
    assert len(val_groups.intersection(test_groups)) == 0
