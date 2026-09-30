import { describe, it, expect } from 'vitest';
import {
  computeLineStarts,
  pointToUtf16Offset,
  utf16OffsetToPoint,
  rangeToOffsets,
  offsetsToRange,
} from '../utils/offsets';

describe('Offsets & Coordinate Conversions', () => {
  it('correctly computes line starts with LF newlines', () => {
    const text = 'line 1\nline 2\nline 3';
    const starts = computeLineStarts(text);
    expect(starts).toEqual([0, 7, 14]);
  });

  it('correctly handles CRLF newlines', () => {
    const text = 'line 1\r\nline 2\r\nline 3';
    const starts = computeLineStarts(text);
    expect(starts).toEqual([0, 8, 16]);

    // Check pointToUtf16Offset across CRLF
    expect(pointToUtf16Offset(text, 1, 1)).toBe(0);
    expect(pointToUtf16Offset(text, 2, 1)).toBe(8);
    expect(pointToUtf16Offset(text, 3, 1)).toBe(16);

    // Round-trip back to point
    expect(utf16OffsetToPoint(text, 8)).toEqual({ line: 2, col: 1 });
    expect(utf16OffsetToPoint(text, 16)).toEqual({ line: 3, col: 1 });
  });

  it('correctly tracks astral plane characters (emojis / surrogate pairs)', () => {
    // 🔒 is 2 UTF-16 code units (surrogate pair)
    const text = 'secure: 🔒 safe code';
    // 'secure: ' is 8 chars, 🔒 is 2 code units -> offset 8 and 9
    expect(text.charCodeAt(8)).toBeGreaterThan(0xd7ff); // surrogate
    expect(text.length).toBe(20);

    const pointAfterEmoji = utf16OffsetToPoint(text, 10);
    expect(pointAfterEmoji).toEqual({ line: 1, col: 11 });

    const offsetBack = pointToUtf16Offset(text, 1, 11);
    expect(offsetBack).toBe(10);
  });

  it('converts range to offsets and vice versa', () => {
    const text = 'def ping():\n    target = "127.0.0.1"\n    return target';
    const range = {
      start_line: 2,
      start_col: 5,
      end_line: 2,
      end_col: 11,
    };

    const { startOffset, endOffset } = rangeToOffsets(text, range);
    expect(text.slice(startOffset, endOffset)).toBe('target');

    const recoveredRange = offsetsToRange(text, startOffset, endOffset);
    expect(recoveredRange).toEqual(range);
  });
});
