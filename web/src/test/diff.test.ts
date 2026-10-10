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
    expect(diff).toContain('+line 2 (new)');
    expect(diff).toContain(' line 1');
    expect(diff).toContain(' line 3');
  });
});
