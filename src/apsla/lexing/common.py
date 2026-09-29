"""Common lexer helpers, character matchers, and position tracking."""

from __future__ import annotations

import bisect

from apsla.models import Range


class OffsetMap:
    """Bidirectional coordinate translator between Python character indices,

    UTF-16 code units (Monaco Editor coordinates), and 1-based (line, col) positions.
    Handles multi-byte characters outside BMP (e.g. emojis taking 2 UTF-16 code units),
    CRLF, LF, and CR line breaks.
    """

    __slots__ = (
        "_text",
        "_py_len",
        "_utf16_len",
        "_py_to_u16",
        "_u16_to_py",
        "_line_starts_py",
        "_line_starts_u16",
    )

    def __init__(self, text: str) -> None:
        """Initialize the offset map over the given text string.

        Args:
            text: Source string to index.
        """
        self._text = text
        self._py_len = len(text)

        py_to_u16 = [0] * (self._py_len + 1)
        u16_to_py: list[int] = []

        line_starts_py: list[int] = [0]
        line_starts_u16: list[int] = [0]

        u16 = 0
        i = 0
        while i < self._py_len:
            ch = text[i]
            py_to_u16[i] = u16
            u16_to_py.append(i)

            is_supp = ord(ch) > 0xFFFF
            step_u16 = 2 if is_supp else 1
            if is_supp:
                u16_to_py.append(i)

            u16 += step_u16

            # Handle newlines: CRLF, LF, CR
            if ch == "\r":
                if i + 1 < self._py_len and text[i + 1] == "\n":
                    # CRLF: Consume '\r', then '\n'
                    i += 1
                    py_to_u16[i] = u16
                    u16_to_py.append(i)
                    u16 += 1
                # Line break after \r or \r\n
                line_starts_py.append(i + 1)
                line_starts_u16.append(u16)
            elif ch == "\n":
                # Line break after standalone \n
                line_starts_py.append(i + 1)
                line_starts_u16.append(u16)

            i += 1

        py_to_u16[self._py_len] = u16
        u16_to_py.append(self._py_len)

        self._utf16_len = u16
        self._py_to_u16 = py_to_u16
        self._u16_to_py = u16_to_py
        self._line_starts_py = line_starts_py
        self._line_starts_u16 = line_starts_u16

    @property
    def text(self) -> str:
        """Return the indexed source text."""
        return self._text

    @property
    def py_len(self) -> int:
        """Return total character length in Python."""
        return self._py_len

    @property
    def utf16_len(self) -> int:
        """Return total length in UTF-16 code units."""
        return self._utf16_len

    @property
    def u16_len(self) -> int:
        """Alias for utf16_len."""
        return self._utf16_len

    @property
    def line_count(self) -> int:
        """Return total line count (1-based)."""
        return len(self._line_starts_py)

    def py_to_utf16(self, py_idx: int) -> int:
        """Convert a Python character index to a UTF-16 code unit offset."""
        if py_idx < 0:
            raise ValueError(f"Negative index {py_idx}")
        if py_idx >= self._py_len:
            return self._utf16_len
        return self._py_to_u16[py_idx]

    def utf16_to_py(self, u16_offset: int) -> int:
        """Convert a UTF-16 code unit offset to a Python character index."""
        if u16_offset < 0:
            raise ValueError(f"Negative offset {u16_offset}")
        if u16_offset >= self._utf16_len:
            return self._py_len
        return self._u16_to_py[u16_offset]

    def py_to_pos(self, py_idx: int) -> tuple[int, int]:
        """Convert a Python character index to 1-based (line, col) in UTF-16 code units."""
        if py_idx < 0:
            raise ValueError(f"Negative index {py_idx}")
        clamped_py = min(py_idx, self._py_len)
        u16_offset = self._py_to_u16[clamped_py]
        return self.utf16_to_pos(u16_offset)

    def utf16_to_pos(self, u16_offset: int) -> tuple[int, int]:
        """Convert a UTF-16 code unit offset to 1-based (line, col) in UTF-16 code units."""
        if u16_offset < 0:
            raise ValueError(f"Negative offset {u16_offset}")
        clamped_u16 = min(u16_offset, self._utf16_len)

        # Binary search for line index
        line_idx = bisect.bisect_right(self._line_starts_u16, clamped_u16) - 1
        line_start_u16 = self._line_starts_u16[line_idx]

        line = line_idx + 1
        col = (clamped_u16 - line_start_u16) + 1
        return line, col

    def pos_to_utf16(self, line: int, col: int) -> int:
        """Convert 1-based (line, col) in UTF-16 code units to UTF-16 offset."""
        if line < 1:
            raise ValueError(f"Line must be >= 1, got {line}")
        if col < 1:
            raise ValueError(f"Col must be >= 1, got {col}")

        line_idx = min(line - 1, len(self._line_starts_u16) - 1)
        line_start = self._line_starts_u16[line_idx]

        # Determine line length in UTF-16
        if line_idx + 1 < len(self._line_starts_u16):
            next_start = self._line_starts_u16[line_idx + 1]
            max_col = next_start - line_start + 1
        else:
            max_col = (self._utf16_len - line_start) + 1

        offset = line_start + min(col - 1, max(0, max_col - 1))
        return min(offset, self._utf16_len)

    def pos_to_py(self, line: int, col: int) -> int:
        """Convert 1-based (line, col) in UTF-16 code units to Python character index."""
        u16 = self.pos_to_utf16(line, col)
        return self.utf16_to_py(u16)

    def span_to_range(self, start_py: int, end_py: int) -> Range:
        """Convert Python start/end slice indices to a Monaco-compatible Range."""
        clamped_start = max(0, min(start_py, self._py_len))
        clamped_end = max(clamped_start, min(end_py, self._py_len))
        s_line, s_col = self.py_to_pos(clamped_start)
        e_line, e_col = self.py_to_pos(clamped_end)
        return Range(
            start_line=s_line,
            start_col=s_col,
            end_line=e_line,
            end_col=e_col,
        )
