import { describe, expect, it } from 'vitest';
import { formatTokenLexeme, type TokenItem } from '../ide/components/TokenInspector';

describe('Lexical Analysis & Token Inspector Unit Tests', () => {
  const sampleTokens: TokenItem[] = [
    {
      id: 1,
      tokenId: 'tok-1',
      line: 1,
      col: 1,
      endLine: 1,
      endCol: 4,
      startOffset: 0,
      endOffset: 3,
      lexeme: 'int',
      type: 'KEYWORD',
      category: 'Keyword',
      status: 'Valid',
      desc: 'Keyword: int',
    },
    {
      id: 2,
      tokenId: 'tok-2',
      line: 1,
      col: 5,
      endLine: 1,
      endCol: 9,
      startOffset: 4,
      endOffset: 8,
      lexeme: 'main',
      type: 'IDENTIFIER',
      category: 'Identifier',
      status: 'Valid',
      desc: 'Identifier: main',
    },
    {
      id: 3,
      tokenId: 'tok-3',
      line: 2,
      col: 10,
      endLine: 2,
      endCol: 11,
      startOffset: 20,
      endOffset: 21,
      lexeme: '\uFEFF',
      type: 'INVALID_TOKEN',
      category: 'Other',
      status: 'Invalid',
      desc: 'Trojan Source: zero-width character detected',
      ruleId: 'APS-CP-LEX-003',
      severity: 'high',
      suggestion: 'Remove invisible U+FEFF Unicode character',
    },
    {
      id: 4,
      tokenId: 'tok-4',
      line: 3,
      col: 5,
      endLine: 3,
      endCol: 7,
      startOffset: 30,
      endOffset: 32,
      lexeme: '42',
      type: 'NUMBER_LITERAL',
      category: 'Literal',
      status: 'Valid',
      desc: 'Integer Literal: 42',
    },
  ];

  it('formats normal and invisible Unicode lexemes correctly', () => {
    const normal = formatTokenLexeme('count');
    expect(normal.isSpecial).toBe(false);
    expect(normal.display).toBe('count');

    const bom = formatTokenLexeme('\uFEFF');
    expect(bom.isSpecial).toBe(true);
    expect(bom.display).toBe('\\uFEFF');
    expect(bom.detail).toContain('U+FEFF');

    const newline = formatTokenLexeme('\n');
    expect(newline.isSpecial).toBe(true);
    expect(newline.display).toBe('\\n');

    const controlChar = formatTokenLexeme('\u0007'); // Bell
    expect(controlChar.isSpecial).toBe(true);
    expect(controlChar.display).toBe('\\u0007');
  });

  it('filters tokens by status (All, Valid, Invalid)', () => {
    const all = sampleTokens;
    expect(all.length).toBe(4);

    const validOnly = sampleTokens.filter((t) => t.status === 'Valid');
    expect(validOnly.length).toBe(3);
    expect(validOnly.every((t) => t.status === 'Valid')).toBe(true);

    const invalidOnly = sampleTokens.filter((t) => t.status === 'Invalid');
    expect(invalidOnly.length).toBe(1);
    expect(invalidOnly[0].id).toBe(3);
    expect(invalidOnly[0].lexeme).toBe('\uFEFF');
  });

  it('filters tokens by category', () => {
    const keywords = sampleTokens.filter((t) => t.category === 'Keyword');
    expect(keywords.length).toBe(1);
    expect(keywords[0].lexeme).toBe('int');

    const literals = sampleTokens.filter((t) => t.category === 'Literal');
    expect(literals.length).toBe(1);
    expect(literals[0].lexeme).toBe('42');
  });

  it('searches tokens by lexeme or type', () => {
    const searchByLexeme = sampleTokens.filter((t) =>
      t.lexeme.toLowerCase().includes('main')
    );
    expect(searchByLexeme.length).toBe(1);
    expect(searchByLexeme[0].type).toBe('IDENTIFIER');

    const searchByType = sampleTokens.filter((t) =>
      t.type.toLowerCase().includes('literal')
    );
    expect(searchByType.length).toBe(1);
    expect(searchByType[0].lexeme).toBe('42');
  });

  it('sorts tokens correctly by line and column', () => {
    const reversed = [...sampleTokens].reverse();
    const sortedAsc = [...reversed].sort((a, b) =>
      a.line !== b.line ? a.line - b.line : a.col - b.col
    );
    expect(sortedAsc.map((t) => t.id)).toEqual([1, 2, 3, 4]);

    const sortedDesc = [...reversed].sort((a, b) =>
      a.line !== b.line ? b.line - a.line : b.col - a.col
    );
    expect(sortedDesc.map((t) => t.id)).toEqual([4, 3, 2, 1]);
  });

  it('preserves exact token offsets and source ranges', () => {
    const token = sampleTokens[0];
    expect(token.line).toBe(1);
    expect(token.col).toBe(1);
    expect(token.endLine).toBe(1);
    expect(token.endCol).toBe(4);
    expect(token.startOffset).toBe(0);
    expect(token.endOffset).toBe(3);
  });
});

