import { describe, expect, it } from 'vitest';
import {
  initialIDEState,
  ideReducer,
  selectCounts,
  selectIsStale,
  deriveCanonicalAnalysisStatus,
  deriveTokenCounts,
  deriveDiagnosticsCounts,
  type IDEState,
  type DocumentAnalysis,
} from '../ide/state/store';
import type { AnalysisResultV2, TokenV2, DiagnosticV2 } from '../api/client';

const doc = {
  id: 'a',
  name: 'a.py',
  language: 'python' as const,
  source: 'print(1)',
  sourceVersion: 0,
  dirty: false,
  origin: 'new' as const,
};
const result: AnalysisResultV2 = {
  analysis_id: 'x',
  source_hash: '0'.repeat(64),
  source_version: 0,
  language: 'python',
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

describe('P1 IDE state and canonical consistency', () => {
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

  describe('deriveCanonicalAnalysisStatus', () => {
    it('returns not_analyzed when no document or unanalyzed', () => {
      expect(deriveCanonicalAnalysisStatus(null, null)).toBe('not_analyzed');
      const unanalyzed: DocumentAnalysis = { result: null, forSourceVersion: null, status: 'idle', abort: null };
      expect(deriveCanonicalAnalysisStatus(doc, unanalyzed)).toBe('not_analyzed');
    });

    it('returns running when analysis is running', () => {
      const running: DocumentAnalysis = { result: null, forSourceVersion: null, status: 'running', abort: null };
      expect(deriveCanonicalAnalysisStatus(doc, running)).toBe('running');
    });

    it('returns execution_failed on analysis error', () => {
      const err: DocumentAnalysis = { result: null, forSourceVersion: null, status: 'error', abort: null };
      expect(deriveCanonicalAnalysisStatus(doc, err)).toBe('execution_failed');
    });

    it('returns outdated when document source version diverges from analysis', () => {
      const okAnalysis: DocumentAnalysis = { result, forSourceVersion: 0, status: 'ok', abort: null };
      const editedDoc = { ...doc, sourceVersion: 1 };
      expect(deriveCanonicalAnalysisStatus(editedDoc, okAnalysis)).toBe('outdated');
    });

    it('returns passed when all tokens and diagnostics are clean', () => {
      const cleanTokens: TokenV2[] = [
        {
          id: '1',
          language: 'python',
          lexeme: 'x',
          token_type: 'IDENTIFIER',
          category: 'Identifier',
          start_offset: 0,
          end_offset: 1,
          start_offset_codepoint: 0,
          end_offset_codepoint: 1,
          start_line: 1,
          start_column: 1,
          end_line: 1,
          end_column: 2,
          lexical_status: 'valid',
          diagnostic_ids: [],
        },
      ];
      const cleanAnalysis: DocumentAnalysis = {
        result: { ...result, tokens: cleanTokens },
        forSourceVersion: 0,
        status: 'ok',
        abort: null,
      };
      expect(deriveCanonicalAnalysisStatus(doc, cleanAnalysis)).toBe('passed');
    });

    it('returns failed_source_diagnostics when source contains invalid tokens', () => {
      const invalidTokens: TokenV2[] = [
        {
          id: '1',
          language: 'python',
          lexeme: '\uFEFF',
          token_type: 'INVALID_TOKEN',
          category: 'Invalid',
          start_offset: 0,
          end_offset: 1,
          start_offset_codepoint: 0,
          end_offset_codepoint: 1,
          start_line: 1,
          start_column: 1,
          end_line: 1,
          end_column: 2,
          lexical_status: 'invalid',
          diagnostic_ids: ['d1'],
        },
      ];
      const invalidAnalysis: DocumentAnalysis = {
        result: { ...result, tokens: invalidTokens },
        forSourceVersion: 0,
        status: 'ok',
        abort: null,
      };
      expect(deriveCanonicalAnalysisStatus(doc, invalidAnalysis)).toBe('failed_source_diagnostics');
    });

    it('returns failed_source_diagnostics when compiler errors are present', () => {
      const errorDiag: DiagnosticV2 = {
        id: 'd1',
        language: 'python',
        range: { start_line: 1, start_col: 1, end_line: 1, end_col: 5 },
        category: 'syntax',
        severity: 'error',
        message: 'SyntaxError: unexpected EOF',
        related_evidence: [],
        produced_by: 'parser',
        certainty: 'definitive',
      };
      const errorAnalysis: DocumentAnalysis = {
        result: { ...result, syntax_diagnostics: [errorDiag] },
        forSourceVersion: 0,
        status: 'ok',
        abort: null,
      };
      expect(deriveCanonicalAnalysisStatus(doc, errorAnalysis)).toBe('failed_source_diagnostics');
    });

    it('returns warning when non-fatal warnings are present', () => {
      const warnDiag: DiagnosticV2 = {
        id: 'w1',
        language: 'python',
        range: { start_line: 1, start_col: 1, end_line: 1, end_col: 5 },
        category: 'semantic',
        severity: 'warning',
        message: 'Unused variable',
        related_evidence: [],
        produced_by: 'linter',
        certainty: 'heuristic',
      };
      const warnAnalysis: DocumentAnalysis = {
        result: { ...result, semantic_diagnostics: [warnDiag] },
        forSourceVersion: 0,
        status: 'ok',
        abort: null,
      };
      expect(deriveCanonicalAnalysisStatus(doc, warnAnalysis)).toBe('warning');
    });
  });

  describe('deriveTokenCounts', () => {
    it('accurately counts valid and invalid tokens with sum invariant', () => {
      const sampleTokens: TokenV2[] = [
        {
          id: '1',
          language: 'python',
          lexeme: 'def',
          token_type: 'KEYWORD',
          category: 'Keyword',
          start_offset: 0,
          end_offset: 3,
          start_offset_codepoint: 0,
          end_offset_codepoint: 3,
          start_line: 1,
          start_column: 1,
          end_line: 1,
          end_column: 4,
          lexical_status: 'valid',
          diagnostic_ids: [],
        },
        {
          id: '2',
          language: 'python',
          lexeme: 'foo',
          token_type: 'IDENTIFIER',
          category: 'Identifier',
          start_offset: 4,
          end_offset: 7,
          start_offset_codepoint: 4,
          end_offset_codepoint: 7,
          start_line: 1,
          start_column: 5,
          end_line: 1,
          end_column: 8,
          lexical_status: 'valid',
          diagnostic_ids: [],
        },
        {
          id: '3',
          language: 'python',
          lexeme: '\uFEFF',
          token_type: 'INVALID_TOKEN',
          category: 'Invalid',
          start_offset: 8,
          end_offset: 9,
          start_offset_codepoint: 8,
          end_offset_codepoint: 9,
          start_line: 1,
          start_column: 9,
          end_line: 1,
          end_column: 10,
          lexical_status: 'invalid',
          diagnostic_ids: ['d1'],
        },
      ];
      const counts = deriveTokenCounts(sampleTokens);
      expect(counts.total).toBe(3);
      expect(counts.valid).toBe(2);
      expect(counts.invalid).toBe(1);
      expect(counts.unknown).toBe(0);
      expect(counts.valid + counts.invalid + counts.unknown).toBe(counts.total);
    });

    it('returns zeroes for empty token list', () => {
      const counts = deriveTokenCounts([]);
      expect(counts).toEqual({ total: 0, valid: 0, invalid: 0, unknown: 0 });
    });
  });

  describe('deriveDiagnosticsCounts', () => {
    it('separates errors and warnings and does not confuse them with tokens', () => {
      const syntax: DiagnosticV2[] = [
        { id: '1', language: 'python', range: { start_line: 1, start_col: 1, end_line: 1, end_col: 2 }, category: 'syntax', severity: 'error', message: 'Fatal syntax', related_evidence: [], produced_by: 'p', certainty: 'definitive' },
      ];
      const semantic: DiagnosticV2[] = [
        { id: '2', language: 'python', range: { start_line: 2, start_col: 1, end_line: 2, end_col: 2 }, category: 'semantic', severity: 'warning', message: 'Style warning', related_evidence: [], produced_by: 'l', certainty: 'heuristic' },
      ];
      const counts = deriveDiagnosticsCounts(syntax, semantic);
      expect(counts.total).toBe(2);
      expect(counts.errors).toBe(1);
      expect(counts.warnings).toBe(1);
      expect(counts.info).toBe(0);
    });
  });
});
