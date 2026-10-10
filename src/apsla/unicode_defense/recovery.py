"""Adversarial token recovery and ASCII mapping engine."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Final

from apsla.lexing.common import OffsetMap
from apsla.models import Range
from apsla.unicode_defense.scanner import (
    BIDI_CONTROLS,
    CONFUSABLES_PATH,
    ZERO_WIDTH_CHARS,
)


def _load_confusables() -> dict[str, str]:
    """Load confusables JSON dictionary."""
    if CONFUSABLES_PATH.exists():
        try:
            with open(CONFUSABLES_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


_CONFUSABLES_MAP: Final[dict[str, str]] = _load_confusables()


@dataclass(slots=True)
class RecoveryResult:
    """Outcome of Unicode recovery including inverse coordinate mapping."""

    original_text: str
    recovered_text: str
    changed: bool
    confusables_replaced: int
    invisibles_removed: int
    offset_map_orig: OffsetMap
    offset_map_rec: OffsetMap
    rec_to_orig_py: list[int] = field(default_factory=list)

    @property
    def replacement_count(self) -> int:
        """Total number of Unicode characters replaced or removed."""
        return self.confusables_replaced + self.invisibles_removed

    def map_py_offset(self, rec_py_idx: int) -> int:
        """Map a character index in recovered text back to original character index."""
        if not self.rec_to_orig_py or rec_py_idx <= 0:
            return 0
        if rec_py_idx >= len(self.rec_to_orig_py):
            return self.offset_map_orig.py_len
        return self.rec_to_orig_py[rec_py_idx]

    def map_span_to_original(self, rec_start: int, rec_end: int) -> tuple[int, int]:
        """Convert a [start, end) character slice in recovered text back to original text slice."""
        orig_start = self.map_py_offset(rec_start)
        if rec_end >= len(self.recovered_text):
            orig_end = self.offset_map_orig.py_len
        else:
            orig_end = self.map_py_offset(rec_end)
        # Ensure non-empty span if input was non-empty
        if rec_end > rec_start and orig_end <= orig_start:
            orig_end = min(orig_start + 1, self.offset_map_orig.py_len)
        return orig_start, orig_end

    def map_recovered_range(self, rec_range: Range) -> Range:
        """Project a Range calculated on recovered text back to original text coordinates."""
        # Convert rec_range back to python indices
        start_u16 = self.offset_map_rec.pos_to_utf16(rec_range.start_line, rec_range.start_col)
        end_u16 = self.offset_map_rec.pos_to_utf16(rec_range.end_line, rec_range.end_col)

        start_py = self.offset_map_rec.utf16_to_py(start_u16)
        end_py = self.offset_map_rec.utf16_to_py(end_u16)

        orig_start, orig_end = self.map_span_to_original(start_py, end_py)
        return self.offset_map_orig.span_to_range(orig_start, orig_end)


def recover_text(text: str, offset_map_orig: OffsetMap | None = None) -> RecoveryResult:
    """Produce recovered canonical ASCII text (confusables mapped, invisibles and

    bidi controls removed) alongside an inverse offset map projecting recovered
    coordinates back onto the original text.

    Args:
        text: Source code string to normalize.
        offset_map_orig: Optional precomputed OffsetMap for original text.

    Returns:
        RecoveryResult: Transformed text, change counters, and inverse mapping.
    """
    om_orig = offset_map_orig if offset_map_orig is not None else OffsetMap(text)

    recovered_chars: list[str] = []
    rec_to_orig_py: list[int] = []

    confusables_replaced = 0
    invisibles_removed = 0

    i = 0
    py_len = len(text)
    while i < py_len:
        ch = text[i]
        code = ord(ch)

        # 1. Strip zero-width, invisible, and bidi override controls
        if code in ZERO_WIDTH_CHARS or code in BIDI_CONTROLS or (0xE0000 <= code <= 0xE007F):
            # Special case: keep BOM if strictly at offset 0? In recovered text, strip all invisibles
            invisibles_removed += 1
            i += 1
            continue

        # 2. Map confusable character to canonical ASCII
        if ch in _CONFUSABLES_MAP:
            target = _CONFUSABLES_MAP[ch]
            confusables_replaced += 1
            for target_ch in target:
                recovered_chars.append(target_ch)
                rec_to_orig_py.append(i)
            i += 1
            continue

        # 3. Standard character: retain as-is
        recovered_chars.append(ch)
        rec_to_orig_py.append(i)
        i += 1

    recovered_text = "".join(recovered_chars)
    om_rec = OffsetMap(recovered_text)
    changed = (confusables_replaced > 0) or (invisibles_removed > 0)

    return RecoveryResult(
        original_text=text,
        recovered_text=recovered_text,
        changed=changed,
        confusables_replaced=confusables_replaced,
        invisibles_removed=invisibles_removed,
        offset_map_orig=om_orig,
        offset_map_rec=om_rec,
        rec_to_orig_py=rec_to_orig_py,
    )
