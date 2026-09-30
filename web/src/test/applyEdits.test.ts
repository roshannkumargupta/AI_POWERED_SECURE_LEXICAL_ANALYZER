import { describe, it, expect } from 'vitest';
import { applyEdits, OverlappingEditsError } from '../utils/applyEdits';
import { Edit } from '../api/client';

describe('applyEdits Utility', () => {
  it('returns original string when edits list is empty', () => {
    const source = 'hello world';
    expect(applyEdits(source, [])).toBe(source);
  });

  it('applies a single edit accurately', () => {
    const source = 'name = request.args.get("q")';
    const edit: Edit = {
      range: { start_line: 1, start_col: 1, end_line: 1, end_col: 5 },
      new_text: 'user_input',
    };
    expect(applyEdits(source, [edit])).toBe('user_input = request.args.get("q")');
  });

  it('applies multiple non-overlapping edits in reverse document order (end-to-start)', () => {
    const source = 'alpha = 1\nbeta = 2\ngamma = 3';

    // Two edits on different lines: one at gamma, one at alpha
    const edits: Edit[] = [
      {
        range: { start_line: 1, start_col: 1, end_line: 1, end_col: 6 },
        new_text: 'first',
      },
      {
        range: { start_line: 3, start_col: 1, end_line: 3, end_col: 6 },
        new_text: 'third',
      },
    ];

    const result = applyEdits(source, edits);
    expect(result).toBe('first = 1\nbeta = 2\nthird = 3');
  });

  it('throws OverlappingEditsError when proposed edits intersect', () => {
    const source = 'critical_function_call(arg1, arg2)';
    const edits: Edit[] = [
      {
        range: { start_line: 1, start_col: 1, end_line: 1, end_col: 15 },
        new_text: 'safe_call',
      },
      {
        range: { start_line: 1, start_col: 10, end_line: 1, end_col: 20 },
        new_text: 'bad_overlap',
      },
    ];

    expect(() => applyEdits(source, edits)).toThrow(OverlappingEditsError);
  });
});
