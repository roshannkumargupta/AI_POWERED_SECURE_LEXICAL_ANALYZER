import { useMemo } from 'react';
import type { PatchProposal } from '../../api/client';
import { applyEdits } from '../../utils/applyEdits';
import { generateUnifiedDiff } from '../../utils/diff';

export interface NumberedDiffLine { text: string; oldLine: number | null; newLine: number | null; kind: 'added' | 'removed' | 'context' | 'meta' | 'hunk' }
export function numberDiffLines(diff: string): NumberedDiffLine[] {
  let oldLine: number | null = null, newLine: number | null = null;
  return diff.split('\n').map(text => {
    const header = text.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (header) { oldLine = Number(header[1]); newLine = Number(header[2]); return { text, oldLine: null, newLine: null, kind: 'hunk' }; }
    if (text.startsWith('---') || text.startsWith('+++')) return { text, oldLine: null, newLine: null, kind: 'meta' };
    if (text.startsWith('-')) { const row = { text, oldLine, newLine: null, kind: 'removed' as const }; if (oldLine !== null) oldLine += 1; return row; }
    if (text.startsWith('+')) { const row = { text, oldLine: null, newLine, kind: 'added' as const }; if (newLine !== null) newLine += 1; return row; }
    const row = { text, oldLine, newLine, kind: 'context' as const };
    if (oldLine !== null) oldLine += 1;
    if (newLine !== null) newLine += 1;
    return row;
  });
}

export function DiffPreview({ source, filename, proposal, diffOverride }: { source: string; filename: string; proposal: PatchProposal; diffOverride?: string }) {
  const diff = useMemo(() => {
    if (diffOverride !== undefined) return diffOverride;
    try { return generateUnifiedDiff(source, applyEdits(source, proposal.edits), filename); }
    catch { return 'Malformed proposal edits'; }
  }, [source, filename, proposal.edits, diffOverride]);
  return <pre className="ide-fix-diff" aria-label="Proposed patch diff">{numberDiffLines(diff).map((row, index) => <span key={index} className={row.kind}><i>{row.oldLine ?? ''}</i><i>{row.newLine ?? ''}</i><code>{row.text}</code></span>)}</pre>;
}
