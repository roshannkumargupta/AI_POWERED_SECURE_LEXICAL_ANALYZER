import { describe, expect, it } from 'vitest';
import type { TaintPathV2 } from '../../api/client';
import { taintDecorations } from './taintDecorations';

const path: TaintPathV2 = { id: 'p', complete: false, limitation: 'bounded', steps: [
  { range: { start_line: 1, start_col: 1, end_line: 1, end_col: 3 }, text: 'input', role: 'source', note: '' },
  { range: { start_line: 2, start_col: 2, end_line: 2, end_col: 5 }, text: 'sink', role: 'sink', note: 'unsafe call' },
] };
describe('taint decorations', () => {
  it('numbers the real source and sink spans and handles absent paths', () => {
    const decorations = taintDecorations(path, 4);
    expect(decorations).toHaveLength(2);
    expect(decorations[0].options.inlineClassName).toBe('ide-p4-flow-source');
    expect(decorations[0].options.before?.content).toBe('1 ');
    expect(decorations[1].options.hoverMessage).toEqual({ value: '2. sink: unsafe call' });
    expect(taintDecorations(undefined, 4)).toEqual([]);
  });
});
