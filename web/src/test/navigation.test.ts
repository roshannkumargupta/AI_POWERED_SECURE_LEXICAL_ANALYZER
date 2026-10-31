import { describe, expect, it } from 'vitest';
import {
  initialIDEState,
  ideReducer,
  selectActiveDocument,
  deriveCanonicalAnalysisStatus,
  type IDEState,
  type IDEDocument,
} from '../ide/state/store';
import type { AnalysisResultV2, DiagnosticV2 } from '../api/client';

describe('Workspace and Editor Navigation Refinement', () => {
  const fileCpp: IDEDocument = {
    id: 'doc-src/main.cpp',
    name: 'src/main.cpp',
    language: 'cpp',
    source: '#include <iostream>\nint main() {\n    return 0;\n}\n',
    sourceVersion: 1,
    dirty: false,
    origin: 'opened',
  };

  const filePy: IDEDocument = {
    id: 'doc-sample.py',
    name: 'sample.py',
    language: 'python',
    source: 'def add(a, b):\n    return a + b\n',
    sourceVersion: 1,
    dirty: false,
    origin: 'opened',
  };

  it('preserves document source and dirty status across tab switching', () => {
    let state: IDEState = ideReducer(initialIDEState, {
      type: 'document/add',
      document: fileCpp,
    });
    state = ideReducer(state, {
      type: 'document/add',
      document: filePy,
    });
    expect(state.documents.length).toBe(2);

    // Switch to fileCpp and edit it
    state = ideReducer(state, { type: 'document/activate', id: fileCpp.id });
    expect(selectActiveDocument(state)?.id).toBe(fileCpp.id);

    const editedCpp = '#include <iostream>\nint main() {\n    int x = 42;\n    return 0;\n}\n';
    state = ideReducer(state, { type: 'document/edit', id: fileCpp.id, source: editedCpp });

    const activeAfterEdit = selectActiveDocument(state);
    expect(activeAfterEdit?.dirty).toBe(true);
    expect(activeAfterEdit?.sourceVersion).toBe(2);
    expect(activeAfterEdit?.source).toBe(editedCpp);

    // Switch to filePy
    state = ideReducer(state, { type: 'document/activate', id: filePy.id });
    expect(selectActiveDocument(state)?.id).toBe(filePy.id);
    expect(selectActiveDocument(state)?.dirty).toBe(false);

    // Switch back to fileCpp - unsaved edit is strictly preserved
    state = ideReducer(state, { type: 'document/activate', id: fileCpp.id });
    const restoredCpp = selectActiveDocument(state);
    expect(restoredCpp?.dirty).toBe(true);
    expect(restoredCpp?.sourceVersion).toBe(2);
    expect(restoredCpp?.source).toBe(editedCpp);
  });

  it('marks document clean and keeps sourceVersion upon save', () => {
    let state: IDEState = ideReducer(initialIDEState, {
      type: 'document/add',
      document: fileCpp,
    });
    state = ideReducer(state, { type: 'document/edit', id: fileCpp.id, source: '// updated' });
    expect(selectActiveDocument(state)?.dirty).toBe(true);

    // Save action
    state = ideReducer(state, { type: 'document/save', id: fileCpp.id });
    const savedDoc = selectActiveDocument(state);
    expect(savedDoc?.dirty).toBe(false);
    expect(savedDoc?.source).toBe('// updated');
  });

  it('computes canonical analysis status accurately for each file', () => {
    let state: IDEState = ideReducer(initialIDEState, {
      type: 'document/add',
      document: fileCpp,
    });
    const doc = selectActiveDocument(state)!;

    // Before analysis: not_analyzed
    expect(deriveCanonicalAnalysisStatus(doc, state.analysis[doc.id])).toBe('not_analyzed');

    // After successful analysis matching sourceVersion: passed
    const cleanResult: AnalysisResultV2 = {
      analysis_id: 'test-run-1',
      source_hash: 'abc',
      source_version: 1,
      language: 'cpp',
      lexical_status: { status: 'ok' },
      syntax_status: { status: 'ok' },
      semantic_status: { status: 'ok' },
      tokens: [],
      lexical_summary: {},
      syntax_diagnostics: [],
      semantic_diagnostics: [],
      security_findings: [],
      taint_paths: [],
      quality: [],
      tools: [],
      timing: {},
      warnings: [],
      omissions: [],
    };
    state = ideReducer(state, {
      type: 'analysis/success',
      id: doc.id,
      result: cleanResult,
      version: 1,
    });
    expect(deriveCanonicalAnalysisStatus(doc, state.analysis[doc.id])).toBe('passed');

    // When edited, status becomes outdated (stale)
    state = ideReducer(state, { type: 'document/edit', id: doc.id, source: '// new line' });
    const editedDoc = selectActiveDocument(state)!;
    expect(deriveCanonicalAnalysisStatus(editedDoc, state.analysis[editedDoc.id])).toBe('outdated');
  });

  it('reflects diagnostic errors and warnings in file analysis status', () => {
    let state: IDEState = ideReducer(initialIDEState, {
      type: 'document/add',
      document: fileCpp,
    });
    const doc = selectActiveDocument(state)!;

    const diagError: DiagnosticV2 = {
      id: 'd1',
      severity: 'error',
      message: 'Unexpected token',
      range: { start_line: 2, start_col: 5, end_line: 2, end_col: 10 },
      produced_by: 'SyntaxParser',
      language: 'cpp',
      category: 'syntax',
      certainty: 'definitive',
      related_evidence: [],
    };

    const errorResult: AnalysisResultV2 = {
      analysis_id: 'test-run-2',
      source_hash: 'xyz',
      source_version: 1,
      language: 'cpp',
      lexical_status: { status: 'issues' },
      syntax_status: { status: 'issues' },
      semantic_status: { status: 'ok' },
      tokens: [],
      lexical_summary: {},
      syntax_diagnostics: [diagError],
      semantic_diagnostics: [],
      security_findings: [],
      taint_paths: [],
      quality: [],
      tools: [],
      timing: {},
      warnings: [],
      omissions: [],
    };

    state = ideReducer(state, {
      type: 'analysis/success',
      id: doc.id,
      result: errorResult,
      version: 1,
    });
    expect(deriveCanonicalAnalysisStatus(doc, state.analysis[doc.id])).toBe(
      'failed_source_diagnostics'
    );
  });
});
