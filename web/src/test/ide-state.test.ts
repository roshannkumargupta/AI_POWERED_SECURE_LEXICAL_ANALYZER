import { describe, expect, it } from 'vitest';
import { initialIDEState, ideReducer, selectCounts, selectIsStale, type IDEState } from '../ide/state/store';
import type { AnalysisResultV2 } from '../api/client';

const doc = { id: 'a', name: 'a.py', language: 'python' as const, source: 'print(1)', sourceVersion: 0, dirty: false, origin: 'new' as const };
const result: AnalysisResultV2 = { analysis_id: 'x', source_hash: '0'.repeat(64), source_version: 0, language: 'python', lexical_status: { status: 'ok' }, syntax_status: { status: 'ok' }, semantic_status: { status: 'ok' }, tokens: [], lexical_summary: {}, syntax_diagnostics: [], semantic_diagnostics: [], security_findings: [], taint_paths: [], quality: [], tools: [], timing: {}, warnings: [], omissions: [] };
describe('P1 IDE state', () => {
  it('adds documents, stores analysis and marks edited results stale', () => {
    let state: IDEState = ideReducer(initialIDEState, { type: 'document/add', document: doc });
    state = ideReducer(state, { type: 'analysis/success', id: 'a', result, version: 0 });
    expect(selectIsStale(state)).toBe(false);
    state = ideReducer(state, { type: 'document/edit', id: 'a', source: 'print(2)' });
    expect(selectIsStale(state)).toBe(true);
    expect(selectCounts(state)).toEqual({ documents: 1, dirty: 1 });
  });
  it('ignores late analysis results for a source version that has changed', () => {
    let state = ideReducer(initialIDEState, { type: 'document/add', document: doc });
    state = ideReducer(state, { type: 'document/edit', id: 'a', source: 'new source' });
    state = ideReducer(state, { type: 'analysis/success', id: 'a', result, version: 0 });
    expect(selectIsStale(state)).toBe(true);
  });
});
