"""Shared helper functions for security rules across languages."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apsla.lexing.token import Token


def shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy in bits per character.

    Args:
        s: Input string to evaluate.

    Returns:
        float: Entropy value in bits/char (0.0 for empty string).
    """
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    length = len(s)
    return -sum((cnt / length) * math.log2(cnt / length) for cnt in freq.values())


def is_inside_comment(pos: int, tokens: list[Token]) -> bool:
    """Check if character index is strictly inside a comment token."""
    for tok in tokens:
        if tok.start <= pos < tok.end:
            return tok.kind == "COMMENT"
    return False


def is_inside_comment_or_string(
    pos: int,
    tokens: list[Token],
    extra_kinds: tuple[str, ...] = (),
) -> bool:
    """Check if character index is strictly inside a comment, string, or specified extra token kinds."""
    target_kinds = ("COMMENT", "STRING", *extra_kinds)
    for tok in tokens:
        if tok.start <= pos < tok.end:
            return tok.kind in target_kinds
    return False


def get_non_trivia_tokens(tokens: list[Token]) -> list[Token]:
    """Filter out whitespace and comment trivia tokens."""
    return [t for t in tokens if t.kind not in ("WHITESPACE", "COMMENT")]
