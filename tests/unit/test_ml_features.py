"""Unit tests for the 45-dimensional feature extractor."""

from __future__ import annotations

import hashlib

import numpy as np

from apsla.languages.python_lang.lexer import PythonLexer
from apsla.ml.features import (
    FEATURE_COUNT,
    FEATURE_NAMES,
    FEATURE_SCHEMA_HASH,
    _compute_entropy,
    _levenshtein_distance,
    extract_file_features,
    extract_token_features,
)


def test_feature_count_and_schema_hash():
    assert len(FEATURE_NAMES) == 45
    assert FEATURE_COUNT == 45

    # Schema hash must be SHA-256 of comma-joined feature names
    expected_hash = hashlib.sha256(",".join(FEATURE_NAMES).encode("utf-8")).hexdigest()
    assert expected_hash == FEATURE_SCHEMA_HASH

    # Reordering any feature must change the hash
    reordered_names = list(FEATURE_NAMES)
    reordered_names[0], reordered_names[1] = reordered_names[1], reordered_names[0]
    tampered_hash = hashlib.sha256(",".join(reordered_names).encode("utf-8")).hexdigest()
    assert tampered_hash != FEATURE_SCHEMA_HASH


def test_feature_extraction_shape_and_determinism():
    code = 'import os\ncmd = "ls -la"\nos.system(cmd)\n'
    tokens = PythonLexer(code).tokenize()
    assert len(tokens) > 0

    matrix1, lang1 = extract_file_features(tokens, language="python")
    matrix2, lang2 = extract_file_features(tokens, language="python")

    assert matrix1.shape == (len(tokens), 45)
    assert matrix2.shape == (len(tokens), 45)
    assert lang1 == 0
    assert lang2 == 0

    # Strict numerical determinism
    np.testing.assert_array_equal(matrix1, matrix2)


def test_fuzzy_dangerous_levenshtein():
    # Exact match: levenshtein = 0
    assert _levenshtein_distance("exec", "exec") == 0
    # 1 edit (substitution, insertion, deletion)
    assert _levenshtein_distance("exce", "exec") <= 2  # transposition is 2 edits
    assert _levenshtein_distance("execs", "exec") == 1  # insertion
    assert _levenshtein_distance("exe", "exec") == 1  # deletion
    assert _levenshtein_distance("exac", "exec") == 1  # substitution
    # > 1 edits
    assert _levenshtein_distance("completely_safe_function", "exec") > 1


def test_entropy_computation():
    # Empty string
    assert _compute_entropy("", n=1) == 0.0
    # Single repeating character has zero entropy
    assert _compute_entropy("aaaaaaa", n=1) == 0.0
    # Diverse characters have positive entropy
    assert _compute_entropy("abcdefgh", n=1) > 2.0


def test_features_ignore_rules_and_taint():
    """Validates that extract_token_features takes only tokens, context, and recovery."""
    import inspect

    sig = inspect.signature(extract_token_features)
    param_names = list(sig.parameters.keys())
    assert "finding" not in param_names
    assert "taint" not in param_names
    assert "rule" not in param_names
