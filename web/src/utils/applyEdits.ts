import { Edit } from '../api/client';
import { rangeToOffsets } from './offsets';

export class OverlappingEditsError extends Error {
  constructor(message: string = 'Edits contain overlapping ranges.') {
    super(message);
    this.name = 'OverlappingEditsError';
  }
}

/**
 * Applies a list of atomic text edits to source text.
 * Edits are sorted in reverse document order (end-to-start)
 * to maintain offset validity across multiple replacements.
 */
export function applyEdits(source: string, edits: Edit[]): string {
  if (!edits || edits.length === 0) {
    return source;
  }

  // Convert edits to offset intervals
  const withOffsets = edits.map((edit, index) => {
    const { startOffset, endOffset } = rangeToOffsets(source, edit.range);
    return {
      edit,
      index,
      startOffset,
      endOffset,
    };
  });

  // Sort ascending by startOffset to detect overlapping
  const sortedAsc = [...withOffsets].sort((a, b) => {
    if (a.startOffset !== b.startOffset) {
      return a.startOffset - b.startOffset;
    }
    return a.endOffset - b.endOffset;
  });

  // Check for overlaps
  for (let i = 0; i < sortedAsc.length - 1; i++) {
    const current = sortedAsc[i];
    const next = sortedAsc[i + 1];
    if (current.endOffset > next.startOffset) {
      throw new OverlappingEditsError(
        `Overlapping edit detected at offset range [${current.startOffset}, ${current.endOffset}) and [${next.startOffset}, ${next.endOffset}).`
      );
    }
  }

  // Sort descending by startOffset (end-to-start)
  const sortedDesc = [...withOffsets].sort((a, b) => {
    if (b.startOffset !== a.startOffset) {
      return b.startOffset - a.startOffset;
    }
    return b.endOffset - a.endOffset;
  });

  let result = source;
  for (const item of sortedDesc) {
    const before = result.slice(0, item.startOffset);
    const after = result.slice(item.endOffset);
    result = before + item.edit.new_text + after;
  }

  return result;
}
