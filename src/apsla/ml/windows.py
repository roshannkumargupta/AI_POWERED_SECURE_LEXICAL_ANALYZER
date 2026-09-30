"""Sliding 9-token window construction and padding for context-aware ML models."""

from __future__ import annotations

import hashlib
from typing import Final

import numpy as np

from apsla.config import FEATURE_DIM, WINDOW_SIZE
from apsla.lexing.token import Token

DEFAULT_WINDOW_SIZE: Final[int] = WINDOW_SIZE
DEFAULT_FEATURE_DIM: Final[int] = FEATURE_DIM


def compute_window_hash(token_texts: list[str]) -> str:
    """Computes a normalized SHA-256 hash of window token texts for duplicate detection."""
    normalized = " ".join(t.strip().lower() for t in token_texts if t.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_token_windows(
    tokens: list[Token],
    features: np.ndarray,
    labels: list[int] | None = None,
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, list[str]]:
    """Builds sliding token context windows centered on each token.

    For each token i in 0..N-1, a window of size 9 is constructed containing:
    4 left tokens, the center token i, and 4 right tokens.
    Tokens outside document boundaries [0, N-1] are padded with zero vectors.
    The label for the window is assigned strictly from the center token.

    Args:
        tokens: Sequence of Token objects.
        features: (N, FEATURE_DIM) feature matrix where row i matches token i.
        labels: Optional list of integer labels (0=SAFE, 1=SUSPICIOUS, 2=MALICIOUS).
        window_size: Odd integer window size (default: 9).

    Returns:
        tuple containing:
            - windows_3d: (N, window_size, FEATURE_DIM) np.ndarray float32 for sequence models.
            - windows_flat: (N, window_size * FEATURE_DIM) np.ndarray float32 for tabular models.
            - target_labels: (N,) np.ndarray int64 or None if labels not provided.
            - window_hashes: list[str] of normalized hashes for leakage / duplicate prevention.
    """
    n_tokens = len(tokens)
    if n_tokens == 0:
        empty_3d = np.empty((0, window_size, DEFAULT_FEATURE_DIM), dtype=np.float32)
        empty_flat = np.empty((0, window_size * DEFAULT_FEATURE_DIM), dtype=np.float32)
        empty_labels = np.empty((0,), dtype=np.int64) if labels is not None else None
        return empty_3d, empty_flat, empty_labels, []

    half = window_size // 2
    pad_vector = np.zeros(DEFAULT_FEATURE_DIM, dtype=np.float32)

    windows_3d = np.zeros((n_tokens, window_size, DEFAULT_FEATURE_DIM), dtype=np.float32)
    windows_flat = np.zeros((n_tokens, window_size * DEFAULT_FEATURE_DIM), dtype=np.float32)
    hashes: list[str] = []

    for i in range(n_tokens):
        win_texts: list[str] = []
        for offset_idx, k in enumerate(range(i - half, i + half + 1)):
            if 0 <= k < n_tokens:
                vec = features[k]
                win_texts.append(tokens[k].text)
            else:
                vec = pad_vector
                win_texts.append("<PAD>")

            windows_3d[i, offset_idx, :] = vec
            windows_flat[
                i, offset_idx * DEFAULT_FEATURE_DIM : (offset_idx + 1) * DEFAULT_FEATURE_DIM
            ] = vec

        hashes.append(compute_window_hash(win_texts))

    target_labels = np.array(labels, dtype=np.int64) if labels is not None else None
    return windows_3d, windows_flat, target_labels, hashes
