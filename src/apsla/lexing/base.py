"""Abstract base class and state machine primitives for hand-written lexical analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Range


class LexerBase(ABC):
    """Abstract base state machine for hand-written lexical analyzers.

    Features:
      - Cursor tracking with character-by-character advance, peek, and match primitives
      - Synchronized line, column, and UTF-16 offset indexing via OffsetMap
      - Never raises exceptions: unrecognized characters become ERROR tokens
      - Full trivia preservation: whitespace and comments are kept as tokens so
        that "".join(t.text for t in tokens) reconstructs input exactly.
    """

    def __init__(self, source: str, offset_map: OffsetMap | None = None) -> None:
        """Initialize the base lexer state machine.

        Args:
            source: Raw source text to tokenize.
            offset_map: Optional precomputed OffsetMap for coordinates.
        """
        self.source = source
        self.length = len(source)
        self.cursor = 0
        self.offset_map = offset_map if offset_map is not None else OffsetMap(source)

    @property
    def is_eof(self) -> bool:
        """Return True if cursor has reached or passed the end of source."""
        return self.cursor >= self.length

    def peek(self, offset: int = 0) -> str:
        """Inspect character at cursor + offset without moving cursor."""
        pos = self.cursor + offset
        if 0 <= pos < self.length:
            return self.source[pos]
        return ""

    def peek_slice(self, length: int) -> str:
        """Inspect slice of given length starting from cursor without advancing."""
        return self.source[self.cursor : self.cursor + length]

    def advance(self) -> str:
        """Advance cursor by one character and return the consumed character."""
        if self.cursor < self.length:
            ch = self.source[self.cursor]
            self.cursor += 1
            return ch
        return ""

    def advance_by(self, count: int) -> str:
        """Advance cursor by count characters and return the consumed substring."""
        start = self.cursor
        self.cursor = min(self.length, self.cursor + count)
        return self.source[start : self.cursor]

    def match(self, expected: str) -> bool:
        """If source matches expected at current cursor, advance and return True."""
        end = self.cursor + len(expected)
        if end <= self.length and self.source[self.cursor : end] == expected:
            self.cursor = end
            return True
        return False

    def make_token(
        self,
        kind: str,
        start_py: int,
        end_py: int,
        text: str | None = None,
        parts: Sequence[Range] = (),
    ) -> Token:
        """Construct an immutable Token with exact UTF-16 coordinates and line/col bounds.

        Args:
            kind: Token classification (e.g. 'KEYWORD', 'IDENTIFIER', 'STRING').
            start_py: Start index in Python character coordinates.
            end_py: End index in Python character coordinates (exclusive).
            text: Optional override string (defaults to source slice).
            parts: Optional embedded sub-expression ranges (e.g. for f-strings).

        Returns:
            Token: Populated token instance.
        """
        token_text = self.source[start_py:end_py] if text is None else text

        clamped_start = max(0, min(start_py, self.length))
        clamped_end = max(clamped_start, min(end_py, self.length))

        start_u16 = self.offset_map.py_to_utf16(clamped_start)
        end_u16 = self.offset_map.py_to_utf16(clamped_end)
        line, col = self.offset_map.utf16_to_pos(start_u16)
        end_line, end_col = self.offset_map.utf16_to_pos(end_u16)

        return Token(
            kind=kind,
            text=token_text,
            start=start_u16,
            end=end_u16,
            line=line,
            col=col,
            end_line=end_line,
            end_col=end_col,
            parts=tuple(parts),
        )

    @abstractmethod
    def tokenize(self) -> list[Token]:
        """Perform full lexical analysis, returning complete token sequence."""
        ...
