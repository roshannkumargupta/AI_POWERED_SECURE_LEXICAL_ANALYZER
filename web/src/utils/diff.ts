/**
 * Generates a clean unified diff string between oldText and newText.
 */
export function generateUnifiedDiff(
  oldText: string,
  newText: string,
  filename: string = 'file'
): string {
  if (oldText === newText) {
    return `--- a/${filename}\n+++ b/${filename}\n (No changes)`;
  }

  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');

  // Find first mismatch from top
  let start = 0;
  while (
    start < oldLines.length &&
    start < newLines.length &&
    oldLines[start] === newLines[start]
  ) {
    start++;
  }

  // Find first mismatch from bottom
  let oldEnd = oldLines.length - 1;
  let newEnd = newLines.length - 1;
  while (oldEnd >= start && newEnd >= start && oldLines[oldEnd] === newLines[newEnd]) {
    oldEnd--;
    newEnd--;
  }

  // Context lines (up to 3 before and after)
  const contextBeforeStart = Math.max(0, start - 3);
  const contextAfterEndOld = Math.min(oldLines.length - 1, oldEnd + 3);
  const contextAfterEndNew = Math.min(newLines.length - 1, newEnd + 3);

  const hunkOldStart = contextBeforeStart + 1;
  const hunkOldCount = contextAfterEndOld - contextBeforeStart + 1;
  const hunkNewStart = contextBeforeStart + 1;
  const hunkNewCount = contextAfterEndNew - contextBeforeStart + 1;

  const diffLines: string[] = [
    `--- a/${filename}`,
    `+++ b/${filename}`,
    `@@ -${hunkOldStart},${hunkOldCount} +${hunkNewStart},${hunkNewCount} @@`,
  ];

  // Context before
  for (let i = contextBeforeStart; i < start; i++) {
    diffLines.push(` ${oldLines[i]}`);
  }

  // Deleted lines
  for (let i = start; i <= oldEnd; i++) {
    diffLines.push(`-${oldLines[i]}`);
  }

  // Added lines
  for (let i = start; i <= newEnd; i++) {
    diffLines.push(`+${newLines[i]}`);
  }

  // Context after
  for (let i = oldEnd + 1; i <= contextAfterEndOld; i++) {
    diffLines.push(` ${oldLines[i]}`);
  }

  return diffLines.join('\n');
}

export interface RangeLike {
  start_line: number;
  start_col: number;
  end_line: number;
  end_col: number;
}

export interface EditLike {
  range: RangeLike;
  new_text: string;
}

export function extractEditText(source: string, edits?: EditLike[]): string {
  if (!edits || edits.length === 0) return '';
  const lines = source.split('\n');
  return edits
    .map((edit) => {
      const startLine = Math.max(0, edit.range.start_line - 1);
      const endLine = Math.max(startLine, edit.range.end_line - 1);
      if (startLine === endLine) {
        return (lines[startLine] || '').slice(
          edit.range.start_col - 1,
          Math.max(edit.range.start_col - 1, edit.range.end_col - 1)
        );
      }
      return [
        lines[startLine]?.slice(edit.range.start_col - 1),
        ...lines.slice(startLine + 1, endLine),
        lines[endLine]?.slice(0, edit.range.end_col - 1),
      ].join('\n');
    })
    .join('\n');
}
