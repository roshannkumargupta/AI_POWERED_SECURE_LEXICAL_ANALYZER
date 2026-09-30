"""Atomic text edit models and range replacement helpers."""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from apsla.lexing.common import OffsetMap
from apsla.models import Edit, Range


class OverlappingEditsError(ValueError):
    """Raised when two or more text edits overlap in source coordinates."""


@dataclass(slots=True)
class _ResolvedEdit:
    start_py: int
    end_py: int
    new_text: str
    original_edit: Edit


def apply_edits(source: str, edits: list[Edit]) -> str:
    """Apply a collection of non-overlapping text edits to source code.

    Edits are sorted and applied from the end of the file to the start, preserving
    offsets of earlier edits. Overlapping edits raise OverlappingEditsError.

    Args:
        source: Original source text.
        edits: List of atomic text edits with UTF-16 Ranges.

    Returns:
        Modified source text with all edits applied.

    Raises:
        OverlappingEditsError: If any two edits have overlapping ranges.
        ValueError: If an edit range is invalid.
    """
    if not edits:
        return source

    offset_map = OffsetMap(source)
    resolved: list[_ResolvedEdit] = []

    for edit in edits:
        r: Range = edit.range
        start_py = offset_map.pos_to_py(r.start_line, r.start_col)
        end_py = offset_map.pos_to_py(r.end_line, r.end_col)
        if start_py > end_py:
            raise ValueError(
                f"Invalid edit range: start offset {start_py} ({r.start_line}:{r.start_col}) "
                f"exceeds end offset {end_py} ({r.end_line}:{r.end_col})"
            )
        resolved.append(
            _ResolvedEdit(
                start_py=start_py,
                end_py=end_py,
                new_text=edit.new_text,
                original_edit=edit,
            )
        )

    # Sort ascending by start offset to check for overlaps
    resolved.sort(key=lambda e: (e.start_py, e.end_py))

    for i in range(len(resolved) - 1):
        cur = resolved[i]
        nxt = resolved[i + 1]
        # Overlap occurs if the next edit starts before the current edit ends
        if nxt.start_py < cur.end_py:
            raise OverlappingEditsError(
                f"Overlapping edits detected between range "
                f"({cur.original_edit.range.start_line}:{cur.original_edit.range.start_col}-"
                f"{cur.original_edit.range.end_line}:{cur.original_edit.range.end_col}) and "
                f"({nxt.original_edit.range.start_line}:{nxt.original_edit.range.start_col}-"
                f"{nxt.original_edit.range.end_line}:{nxt.original_edit.range.end_col})"
            )

    # Sort descending by start offset to apply from back to front
    resolved.sort(key=lambda e: (e.start_py, e.end_py), reverse=True)

    result = source
    for edit_item in resolved:
        result = result[: edit_item.start_py] + edit_item.new_text + result[edit_item.end_py :]

    return result


def unified_diff(before: str, after: str, filename: str = "file") -> str:
    """Generate unified diff string between before and after text.

    Args:
        before: Original source code.
        after: Modified source code.
        filename: Optional filename for diff header.

    Returns:
        Unified diff as formatted string.
    """
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm="",
        )
    )
    return "".join(diff_lines)
