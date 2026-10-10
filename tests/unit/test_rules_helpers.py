"""Unit tests for shared rule helper utilities."""

from __future__ import annotations

from apsla.lexing.token import Token
from apsla.rules.helpers import (
    get_non_trivia_tokens,
    is_inside_comment,
    is_inside_comment_or_string,
    shannon_entropy,
)


def test_shannon_entropy_calculation() -> None:
    assert shannon_entropy("") == 0.0
    assert shannon_entropy("aaaaaa") == 0.0
    assert shannon_entropy("0123456789abcdef") > 3.5


def test_is_inside_comment_and_string() -> None:
    tokens = [
        Token(kind="COMMENT", text="// test", start=0, end=7, line=1, col=1, end_line=1, end_col=8),
        Token(kind="WHITESPACE", text=" ", start=7, end=8, line=1, col=8, end_line=1, end_col=9),
        Token(kind="STRING", text='"hello"', start=8, end=15, line=1, col=9, end_line=1, end_col=16),
    ]

    assert is_inside_comment(3, tokens) is True
    assert is_inside_comment(10, tokens) is False
    assert is_inside_comment_or_string(3, tokens) is True
    assert is_inside_comment_or_string(10, tokens) is True
    assert is_inside_comment_or_string(7, tokens) is False


def test_get_non_trivia_tokens() -> None:
    tokens = [
        Token(kind="WHITESPACE", text=" ", start=0, end=1, line=1, col=1, end_line=1, end_col=2),
        Token(kind="IDENTIFIER", text="x", start=1, end=2, line=1, col=2, end_line=1, end_col=3),
        Token(kind="COMMENT", text="// note", start=2, end=9, line=1, col=3, end_line=1, end_col=10),
    ]
    non_trivia = get_non_trivia_tokens(tokens)
    assert len(non_trivia) == 1
    assert non_trivia[0].kind == "IDENTIFIER"
