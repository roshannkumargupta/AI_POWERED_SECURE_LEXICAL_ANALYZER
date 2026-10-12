import { describe, expect, it } from 'vitest';
import type { AnalysisResultV2, TokenV2 } from '../../api/client';
import { explainToken } from './explanations';
import { filterAndSortTokens, isAnalysisIncomplete, tokenAtPosition, tokenCounts, tokenCsv, tokenJson, tokenSecurityFindings, tokenTsv, visibleLexeme } from './tokenModel';

const token = (id: string, lexeme: string, category: string, start: number, status: TokenV2['lexical_status'] = 'valid'): TokenV2 => ({
  id, language: 'cpp', lexeme, category, token_type: category === 'Keyword' ? 'KEYWORD' : 'IDENTIFIER',
  start_offset: start, end_offset: start + lexeme.length, start_offset_codepoint: start, end_offset_codepoint: start + lexeme.length,
  start_line: 1, start_column: start + 1, end_line: 1, end_column: start + lexeme.length + 1,
  lexical_status: status, diagnostic_ids: [],
});

const tokens = [token('a', 'int', 'Keyword', 0), token('b', 'name', 'Identifier', 4), token('c', '<img onerror>', 'Identifier', 10, 'invalid'), token('d', '\u202e', 'Operator', 25)];
const result = { analysis_id: 'analysis-1', source_hash: 'a'.repeat(64), source_version: 3, language: 'cpp', lexical_status: { status: 'ok' }, syntax_status: { status: 'ok' }, semantic_status: { status: 'incomplete' }, tokens, lexical_summary: {}, syntax_diagnostics: [], semantic_diagnostics: [], security_findings: [], taint_paths: [], quality: [], tools: [], timing: {}, warnings: [], omissions: [] } as unknown as AnalysisResultV2;

describe('P3 token model', () => {
  it('derives counts directly from token status and categories', () => {
    const counts = tokenCounts(tokens);
    expect(counts).toMatchObject({ total: 4, valid: 3, invalid: 1, unknown: 0 });
    expect(Object.fromEntries(counts.categories)).toEqual({ Keywords: 1, Identifiers: 2, Operators: 1 });
  });

  it('combines category and invalid filters with search and sorts both ways', () => {
    expect(filterAndSortTokens(tokens, 'Identifiers', 'onerror', 'position').map((item) => item.id)).toEqual(['c']);
    expect(filterAndSortTokens(tokens, 'Invalid', '1:11', 'position').map((item) => item.id)).toEqual(['c']);
    expect(filterAndSortTokens(tokens, 'All', 'identifier', 'type').map((item) => item.id)).toEqual(['b', 'c', 'd']);
    expect(filterAndSortTokens([...tokens].reverse(), 'All', '', 'position').map((item) => item.id)).toEqual(['a', 'b', 'c', 'd']);
  });

  it('renders invisible lexemes visibly and keeps HTML as text in exports', () => {
    expect(visibleLexeme('')).toBe('⟨empty⟩');
    expect(visibleLexeme('\u202e')).toBe('<U+202E>');
    const csv = tokenCsv(tokens);
    expect(csv).toContain('"<img onerror>"');
    expect(csv).toContain('<U+202E>');
    expect(tokenTsv(tokens)).toContain('<U+202E>');
    const json = JSON.parse(tokenJson(result));
    expect(json).toMatchObject({ source_hash: result.source_hash, analysis_id: result.analysis_id, language: 'cpp' });
    expect(json.tokens).toHaveLength(tokens.length);
  });

  it('maps editor positions to a row without navigation side effects', () => {
    expect(tokenAtPosition(tokens, 1, 5)?.id).toBe('b');
    expect(tokenAtPosition(tokens, 1, 9)).toBeNull();
  });

  it('only associates actual overlapping security findings and detects incomplete analysis', () => {
    const finding = { id: 'f', range: { start_line: 1, start_col: 5, end_line: 1, end_col: 8 } } as AnalysisResultV2['security_findings'][number];
    expect(tokenSecurityFindings(tokens[1], [finding])).toEqual([finding]);
    expect(tokenSecurityFindings(tokens[0], [finding])).toEqual([]);
    expect(isAnalysisIncomplete(result)).toBe(true);
  });

  it('uses deterministic beginner explanations based on token type and language', () => {
    expect(explainToken('KEYWORD', 'cpp')).toContain('reserved word');
    expect(explainToken('LANGUAGE_SPECIAL', 'java')).toContain('Java language-specific token');
  });
});
