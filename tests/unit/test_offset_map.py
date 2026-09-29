"""Unit and property tests for OffsetMap UTF-16, line/col, and Python index conversions."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from apsla.lexing.common import OffsetMap


def test_ascii_simple_offsets():
    """Verify standard single-line ASCII text offset mappings."""
    text = "hello world"
    om = OffsetMap(text)

    assert om.py_len == 11
    assert om.u16_len == 11
    assert om.line_count == 1

    # Python <-> UTF-16
    for i in range(len(text)):
        assert om.py_to_utf16(i) == i
        assert om.utf16_to_py(i) == i

    # (line, col) -> 1-based
    # 'h' is line 1, col 1
    assert om.pos_to_utf16(1, 1) == 0
    assert om.utf16_to_pos(0) == (1, 1)

    # 'w' is at index 6 -> line 1, col 7
    assert om.pos_to_utf16(1, 7) == 6
    assert om.utf16_to_pos(6) == (1, 7)


def test_emoji_astral_plane_surrogate_pairs():
    """Verify that emoji outside the BMP (surrogate pairs) take 2 UTF-16 code units."""
    # Rocket emoji 🚀 is U+1F680 -> 1 Python char, 2 UTF-16 code units (\uD83D\uDE80)
    # Grinning face 😀 is U+1F600 -> 1 Python char, 2 UTF-16 code units (\uD83D\uDE00)
    text = "a🚀b😀c"
    om = OffsetMap(text)

    # Python chars: 'a' (0), '🚀' (1), 'b' (2), '😀' (3), 'c' (4) -> length 5
    assert len(text) == 5
    assert om.py_len == 5

    # UTF-16 units: 'a' (1), '🚀' (2), 'b' (1), '😀' (2), 'c' (1) -> total 7 code units
    assert om.u16_len == 7

    # Offsets check
    assert om.py_to_utf16(0) == 0  # 'a'
    assert om.py_to_utf16(1) == 1  # '🚀' starts at UTF-16 index 1
    assert om.py_to_utf16(2) == 3  # 'b' starts at UTF-16 index 3 (after 2 units of rocket)
    assert om.py_to_utf16(3) == 4  # '😀' starts at UTF-16 index 4
    assert om.py_to_utf16(4) == 6  # 'c' starts at UTF-16 index 6

    # Reverse check
    assert om.utf16_to_py(0) == 0
    assert om.utf16_to_py(1) == 1
    assert om.utf16_to_py(2) == 1  # Trail surrogate also resolves back to char 1
    assert om.utf16_to_py(3) == 2
    assert om.utf16_to_py(4) == 3
    assert om.utf16_to_py(5) == 3
    assert om.utf16_to_py(6) == 4

    # Monaco coordinates (line, col)
    # 'b' is on line 1, col 4 (1-based UTF-16 offset 3 + 1)
    line, col = om.utf16_to_pos(3)
    assert line == 1
    assert col == 4

    # 'c' is on line 1, col 7 (1-based UTF-16 offset 6 + 1)
    line, col = om.utf16_to_pos(6)
    assert line == 1
    assert col == 7


def test_multiline_crlf_lf_cr():
    """Verify offset handling across CRLF, LF, and mixed newlines."""
    # Line 1: 'abc\r\n' (3 chars + 2 newline chars = 5 python chars, 5 UTF-16 units)
    # Line 2: 'de\n'    (2 chars + 1 newline char = 3 python chars, 3 UTF-16 units)
    # Line 3: 'f'       (1 char = 1 python char, 1 UTF-16 unit)
    text = "abc\r\nde\nf"
    om = OffsetMap(text)

    assert om.line_count == 3

    # Line 1 start
    assert om.pos_to_utf16(1, 1) == 0
    assert om.utf16_to_pos(0) == (1, 1)

    # Line 2 start: after 'abc\r\n' which is 5 code units
    assert om.pos_to_utf16(2, 1) == 5
    assert om.utf16_to_pos(5) == (2, 1)

    # Line 2 'd' is pos (2, 1), 'e' is pos (2, 2)
    assert om.pos_to_utf16(2, 2) == 6
    assert om.utf16_to_pos(6) == (2, 2)

    # Line 3 start: after 'abc\r\nde\n' (5 + 3 = 8 units)
    assert om.pos_to_utf16(3, 1) == 8
    assert om.utf16_to_pos(8) == (3, 1)


def test_tab_characters_and_whitespace():
    """Verify tabs and mixed whitespace columns."""
    text = "\tdef foo():\n\t\tpass\n"
    om = OffsetMap(text)

    assert om.line_count == 3
    # First tab is (1, 1), 'd' is (1, 2)
    assert om.pos_to_utf16(1, 1) == 0
    assert om.pos_to_utf16(1, 2) == 1
    assert om.utf16_to_pos(1) == (1, 2)

    # Second line has two tabs: pos_to_utf16(2, 1) is start of line 2
    l2_start = om.pos_to_utf16(2, 1)
    assert om.utf16_to_pos(l2_start) == (2, 1)
    # 'p' is at col 3 (after two tabs)
    assert om.pos_to_utf16(2, 3) == l2_start + 2


def test_span_to_range_conversion():
    """Verify span_to_range converts Python slices into Pydantic Range models."""
    text = "alpha\nbeta\ngamma"
    om = OffsetMap(text)

    # Slice 'beta' -> python indices [6, 10)
    beta_range = om.span_to_range(6, 10)
    assert beta_range.start_line == 2
    assert beta_range.start_col == 1
    assert beta_range.end_line == 2
    assert beta_range.end_col == 5

    # Out of bounds clamping
    clamped = om.span_to_range(-5, 9999)
    assert clamped.start_line == 1
    assert clamped.start_col == 1
    assert clamped.end_line == 3
    assert clamped.end_col == 6


@settings(max_examples=200, deadline=None)
@given(st.text())
def test_hypothesis_offset_map_round_trip(sample: str):
    """Property test: OffsetMap preserves Python <-> UTF-16 and coordinate round-trips for random text."""
    om = OffsetMap(sample)

    assert om.py_len == len(sample)
    # UTF-16 length must be at least Python length
    assert om.u16_len >= om.py_len

    # Every Python index must map to UTF-16 and back to itself
    for py_idx in range(len(sample)):
        u16_idx = om.py_to_utf16(py_idx)
        recovered_py = om.utf16_to_py(u16_idx)
        assert recovered_py == py_idx

    # UTF-16 offsets must round-trip through (line, col)
    for u16_idx in range(om.u16_len):
        line, col = om.utf16_to_pos(u16_idx)
        recovered_u16 = om.pos_to_utf16(line, col)
        assert recovered_u16 == u16_idx
