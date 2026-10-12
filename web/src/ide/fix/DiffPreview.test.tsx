import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { PatchProposal } from '../../api/client';
import { DiffPreview, numberDiffLines } from './DiffPreview';

describe('proposal diff', () => {
  it('numbers removed and added rows against their respective files', () => {
    expect(numberDiffLines('--- a/a.py\n+++ b/a.py\n@@ -2,1 +2,1 @@\n-old\n+new')).toEqual([
      { text: '--- a/a.py', oldLine: null, newLine: null, kind: 'meta' },
      { text: '+++ b/a.py', oldLine: null, newLine: null, kind: 'meta' },
      { text: '@@ -2,1 +2,1 @@', oldLine: null, newLine: null, kind: 'hunk' },
      { text: '-old', oldLine: 2, newLine: null, kind: 'removed' },
      { text: '+new', oldLine: null, newLine: 2, kind: 'added' },
    ]);
  });
  it('renders actual edited source as text with red/green line classes', () => {
    const proposal: PatchProposal = { id: 'p1', source_hash: 'hash', source_version: 1, target_finding_id: 'f1', origin: 'rule', edits: [{ range: { start_line: 1, start_col: 1, end_line: 1, end_col: 4 }, new_text: 'safe' }], diff: '', rationale: '', expected_outcome: '', assumptions: [], risks: [], created_at: '' };
    const { container } = render(<DiffPreview source={'bad\nkeep'} filename="x.py" proposal={proposal}/>);
    expect(screen.getByText('-bad')).toBeTruthy();
    expect(screen.getByText('+safe')).toBeTruthy();
    expect(container.querySelector('.context code')?.textContent).toBe(' keep');
    expect(container.querySelector('.removed')).toBeTruthy();
    expect(container.querySelector('.added')).toBeTruthy();
  });
});
