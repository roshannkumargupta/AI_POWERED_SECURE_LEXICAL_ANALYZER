import type { AnalysisResultV2, TokenV2 } from '../../api/client';
type SecurityFindingV2 = AnalysisResultV2['security_findings'][number];

export type TokenFilter = 'All' | 'Invalid' | string;
export type TokenSort = 'position' | 'type';

export function categoryGroup(category: string): string {
  const lower = category.toLocaleLowerCase();
  if (lower === 'keyword' || lower === 'keywords') return 'Keywords';
  if (lower === 'identifier' || lower === 'identifiers') return 'Identifiers';
  if (lower === 'operator' || lower === 'operators') return 'Operators';
  if (lower.includes('literal')) return 'Literals';
  if (lower === 'delimiter' || lower === 'delimiters') return 'Delimiters';
  if (lower === 'comment' || lower === 'comments') return 'Comments';
  if (lower.includes('preprocessor')) return 'Preprocessor';
  return category;
}

export function tokenCounts(tokens: TokenV2[]) {
  const categories = new Map<string, number>();
  let valid = 0;
  let invalid = 0;
  let unknown = 0;
  for (const token of tokens) {
    const group = categoryGroup(token.category);
    categories.set(group, (categories.get(group) ?? 0) + 1);
    if (token.lexical_status === 'valid') valid += 1;
    else if (token.lexical_status === 'invalid') invalid += 1;
    else unknown += 1;
  }
  return { total: tokens.length, valid, invalid, unknown, categories };
}

export function filterAndSortTokens(
  tokens: TokenV2[],
  filter: TokenFilter,
  query: string,
  sort: TokenSort
) {
  const needle = query.trim().toLocaleLowerCase();
  const filtered = tokens.filter((token) => {
    if (filter === 'Invalid' && token.lexical_status !== 'invalid') return false;
    if (filter !== 'All' && filter !== 'Invalid' && categoryGroup(token.category) !== filter)
      return false;
    if (!needle) return true;
    const position = `${token.start_line}:${token.start_column}-${token.end_line}:${token.end_column}`;
    return [
      token.lexeme,
      token.token_type,
      token.category,
      position,
      `${token.start_line}:${token.start_column}`,
      `${token.end_line}:${token.end_column}`,
    ].some((value) => value.toLocaleLowerCase().includes(needle));
  });
  return filtered.sort((a, b) =>
    sort === 'type'
      ? a.token_type.localeCompare(b.token_type) || a.start_offset - b.start_offset
      : a.start_offset - b.start_offset
  );
}

const invisible =
  /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]/gu;
export function visibleLexeme(value: string): string {
  if (!value) return '⟨empty⟩';
  return value.replace(
    invisible,
    (character) => `<U+${character.codePointAt(0)!.toString(16).toUpperCase().padStart(4, '0')}>`
  );
}

export function tokenSecurityFindings(token: TokenV2, findings: SecurityFindingV2[]) {
  return findings.filter((finding) => {
    const range = finding.range;
    return (
      (range.start_line < token.end_line ||
        (range.start_line === token.end_line && range.start_col < token.end_column)) &&
      (range.end_line > token.start_line ||
        (range.end_line === token.start_line && range.end_col > token.start_column))
    );
  });
}

export function isAnalysisIncomplete(result: AnalysisResultV2 | null): boolean {
  if (!result) return false;
  return (
    result.omissions.length > 0 ||
    [result.lexical_status, result.syntax_status, result.semantic_status].some(
      (item) => item.status === 'incomplete' || item.status === 'unavailable'
    ) ||
    result.tools.some((tool) => ['failed', 'timeout', 'unavailable'].includes(tool.status))
  );
}

export function tokenCsv(tokens: TokenV2[]): string {
  const quote = (value: string) => `"${value.replace(/"/g, '""')}"`;
  return [
    ['Line:Col', 'Lexeme', 'Token Type', 'Category', 'Lexical Status', 'Semantic / Symbol Info'],
    ...tokens.map((token) => [
      `${token.start_line}:${token.start_column}`,
      visibleLexeme(token.lexeme),
      token.token_type,
      token.category,
      token.lexical_status,
      '—',
    ]),
  ]
    .map((row) => row.map(quote).join(','))
    .join('\r\n');
}

export function tokenTsv(tokens: TokenV2[]): string {
  return tokens
    .map((token) =>
      [
        `${token.start_line}:${token.start_column}`,
        visibleLexeme(token.lexeme),
        token.token_type,
      ].join('\t')
    )
    .join('\n');
}

export function tokenJson(result: AnalysisResultV2, tokens: TokenV2[] = result.tokens): string {
  return JSON.stringify(
    {
      source_hash: result.source_hash,
      analysis_id: result.analysis_id,
      language: result.language,
      tokens,
    },
    null,
    2
  );
}

export function tokenAtPosition(tokens: TokenV2[], line: number, column: number): TokenV2 | null {
  return (
    tokens.find(
      (token) =>
        (line > token.start_line || (line === token.start_line && column >= token.start_column)) &&
        (line < token.end_line || (line === token.end_line && column < token.end_column))
    ) ?? null
  );
}
