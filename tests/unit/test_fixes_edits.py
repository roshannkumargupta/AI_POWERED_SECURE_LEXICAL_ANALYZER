"""Unit tests for fixes/edits.py and fixes/imports.py."""

import pytest

from apsla.fixes.edits import OverlappingEditsError, apply_edits, unified_diff
from apsla.fixes.imports import ensure_import_python
from apsla.models import Edit, Range


def test_apply_edits_basic():
    source = "line1\nline2\nline3\n"
    # Edit on line 2: replace "line2" with "new_line2"
    edit1 = Edit(
        range=Range(start_line=2, start_col=1, end_line=2, end_col=6),
        new_text="new_line2",
    )
    result = apply_edits(source, [edit1])
    assert result == "line1\nnew_line2\nline3\n"


def test_apply_edits_multiple_non_overlapping():
    source = "apple banana cherry\n"
    # Replace apple with red, cherry with sweet
    e1 = Edit(
        range=Range(start_line=1, start_col=1, end_line=1, end_col=6),
        new_text="red",
    )
    e2 = Edit(
        range=Range(start_line=1, start_col=14, end_line=1, end_col=20),
        new_text="sweet",
    )
    result = apply_edits(source, [e1, e2])
    assert result == "red banana sweet\n"


def test_apply_edits_overlapping_raises():
    source = "0123456789\n"
    # Edit 1: cols 2..6 ("1234")
    e1 = Edit(
        range=Range(start_line=1, start_col=2, end_line=1, end_col=6),
        new_text="A",
    )
    # Edit 2: cols 4..8 ("3456") - overlaps with e1
    e2 = Edit(
        range=Range(start_line=1, start_col=4, end_line=1, end_col=8),
        new_text="B",
    )
    with pytest.raises(OverlappingEditsError):
        apply_edits(source, [e1, e2])


def test_apply_edits_invalid_range_raises():
    source = "hello world\n"
    # End before start
    e = Edit(
        range=Range(start_line=1, start_col=6, end_line=1, end_col=3),
        new_text="x",
    )
    with pytest.raises(ValueError):
        apply_edits(source, [e])


def test_unified_diff():
    before = "line1\nold line\nline3\n"
    after = "line1\nnew line\nline3\n"
    diff = unified_diff(before, after, filename="test.py")
    assert "-old line" in diff
    assert "+new line" in diff
    assert "--- a/test.py" in diff


def test_ensure_import_python_placement():
    # After docstring and __future__
    source = '"""Module docstring."""\nfrom __future__ import annotations\n\nx = 1\n'
    edits = ensure_import_python(source, "import shlex")
    assert len(edits) == 1
    modified = apply_edits(source, edits)
    assert "from __future__ import annotations\nimport shlex\n" in modified


def test_ensure_import_python_deduplication():
    source = "import os\nimport shlex\n\nx = 1\n"
    # Should not duplicate existing import
    edits = ensure_import_python(source, "import shlex")
    assert edits == []

    # Bare module name deduplication
    edits2 = ensure_import_python(source, "os")
    assert edits2 == []
