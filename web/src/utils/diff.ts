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
  while (
    oldEnd >= start &&
    newEnd >= start &&
    oldLines[oldEnd] === newLines[newEnd]
  ) {
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
