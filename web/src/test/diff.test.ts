import { describe, it, expect } from 'vitest';
import { generateUnifiedDiff } from '../utils/diff';

describe('generateUnifiedDiff', () => {
  it('returns no changes when strings are identical', () => {
    const text = 'print("hello")\n';
    const diff = generateUnifiedDiff(text, text, 'test.py');
    expect(diff).toContain('(No changes)');
  });

  it('generates unified diff with deletions and additions', () => {
    const before = 'line 1\nline 2 (old)\nline 3';
    const after = 'line 1\nline 2 (new)\nline 3';
    const diff = generateUnifiedDiff(before, after, 'test.txt');

    expect(diff).toContain('--- a/test.txt');
    expect(diff).toContain('+++ b/test.txt');
    expect(diff).toContain('-line 2 (old)');
    expect(diff).toContain(' line 3');
  });

  it('extracts edit text from single line and multi line edits', async () => {
    const { extractEditText } = await import('../utils/diff');
    const source = 'hello world\nfoo bar\nbaz';
    const singleLine = [
      { range: { start_line: 1, start_col: 7, end_line: 1, end_col: 12 }, new_text: 'there' },
    ];
    expect(extractEditText(source, singleLine)).toBe('world');

    const multiLine = [
      { range: { start_line: 1, start_col: 7, end_line: 2, end_col: 4 }, new_text: 'replacement' },
    ];
    expect(extractEditText(source, multiLine)).toBe('world\nfoo');
  });
});
