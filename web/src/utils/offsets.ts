export interface Range {
  start_line: number;
  start_col: number;
  end_line: number;
  end_col: number;
}

/**
 * Split source into line offsets (start of each line in UTF-16 code units).
 * Handles \r\n, \n, and \r.
 */
export function computeLineStarts(source: string): number[] {
  const lineStarts = [0];
  const len = source.length;
  let i = 0;

  while (i < len) {
    const ch = source.charCodeAt(i);
    if (ch === 13) {
      // \r
      if (i + 1 < len && source.charCodeAt(i + 1) === 10) {
        // \r\n
        lineStarts.push(i + 2);
        i += 2;
      } else {
        lineStarts.push(i + 1);
        i += 1;
      }
    } else if (ch === 10) {
      // \n
      lineStarts.push(i + 1);
      i += 1;
    } else {
      i += 1;
    }
  }

  return lineStarts;
}

/**
 * Converts a 1-based line and 1-based UTF-16 column to a 0-based UTF-16 string index.
 */
export function pointToUtf16Offset(source: string, line: number, col: number): number {
  const lineStarts = computeLineStarts(source);
  if (line <= 1) {
    return Math.max(0, Math.min(source.length, col - 1));
  }
  if (line > lineStarts.length) {
    return source.length;
  }
  const lineStart = lineStarts[line - 1];
  const nextLineStart = line < lineStarts.length ? lineStarts[line] : source.length;
  const lineLength = Math.max(0, nextLineStart - lineStart);
  const offset = lineStart + Math.min(lineLength, Math.max(0, col - 1));
  return Math.max(0, Math.min(source.length, offset));
}

/**
 * Converts a 0-based UTF-16 string index into 1-based line and 1-based UTF-16 column.
 */
export function utf16OffsetToPoint(source: string, offset: number): { line: number; col: number } {
  const clampedOffset = Math.max(0, Math.min(source.length, offset));
  const lineStarts = computeLineStarts(source);

  // Binary search for greatest lineStart <= clampedOffset
  let low = 0;
  let high = lineStarts.length - 1;
  let lineIdx = 0;

  while (low <= high) {
    const mid = (low + high) >> 1;
    if (lineStarts[mid] <= clampedOffset) {
      lineIdx = mid;
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }

  const line = lineIdx + 1;
  const col = clampedOffset - lineStarts[lineIdx] + 1;
  return { line, col };
}

/**
 * Converts a 1-based Range to start and end 0-based string offsets.
 */
export function rangeToOffsets(
  source: string,
  range: Range
): { startOffset: number; endOffset: number } {
  const startOffset = pointToUtf16Offset(source, range.start_line, range.start_col);
  const endOffset = pointToUtf16Offset(source, range.end_line, range.end_col);
  return {
    startOffset: Math.min(startOffset, endOffset),
    endOffset: Math.max(startOffset, endOffset),
  };
}

/**
 * Converts 0-based string offsets to a 1-based Range.
 */
export function offsetsToRange(source: string, startOffset: number, endOffset: number): Range {
  const start = utf16OffsetToPoint(source, startOffset);
  const end = utf16OffsetToPoint(source, endOffset);
  return {
    start_line: start.line,
    start_col: start.col,
    end_line: end.line,
    end_col: end.col,
  };
}
