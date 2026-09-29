"""Token representation and token kind definitions."""

from __future__ import annotations

from dataclasses import dataclass

from apsla.models import Range, TokenInfo


@dataclass(slots=True, frozen=True)
class Token:
    """Represents a lexical token with exact UTF-16 and coordinate spans."""

    kind: str
    text: str
    start: int  # UTF-16 code unit offset (0-based)
    end: int  # UTF-16 code unit offset (0-based, exclusive)
    line: int  # 1-based start line
    col: int  # 1-based start column in UTF-16 code units
    end_line: int  # 1-based end line
    end_col: int  # 1-based end column in UTF-16 code units (exclusive)
    parts: tuple[Range, ...] = ()  # Ranges of embedded expressions (for f-strings)

    def to_range(self) -> Range:
        """Convert token coordinates into a Pydantic Range model."""
        return Range(
            start_line=self.line,
            start_col=self.col,
            end_line=self.end_line,
            end_col=self.end_col,
        )

    def to_token_info(self, label: str = "SAFE", score: float = 0.0) -> TokenInfo:
        """Convert token to user-facing TokenInfo model."""
        return TokenInfo(
            token=self.text,
            token_type=self.kind,
            range=self.to_range(),
            label=label,
            score=score,
        )
