import type { AnalysisResult, Finding } from '../api/client';
import type { Range } from '../utils/offsets';
import { findingCategory } from '../utils/findingCategory';

export type LexicalType = 'Keyword' | 'Identifier' | 'String' | 'Number' | 'Operator' | 'Delimiter' | 'Comment' | 'Whitespace' | 'Newline' | 'Indent' | 'Dedent' | 'Error' | 'Other';
export type TokenRole = 'Source' | 'Propagation' | 'Sink' | 'Sanitizer' | 'Dangerous API' | 'Unicode' | 'Obfuscated/Encoded' | 'Neutral';
export interface DerivedToken {
  index: number; text: string; kind: string; range: Range; label: string; score: number;
  lexicalType: LexicalType; role: TokenRole; severity: 'Safe' | string; detectors: string[];
  relatedFindings: Finding[]; categories: string[]; securityRelevant: boolean;
  lexicalError: boolean;
  taintSteps: Finding['taint_path']; unicodeEvidence: unknown[];
}

const lexicalKinds: Record<string, LexicalType> = {
  KEYWORD: 'Keyword', IDENTIFIER: 'Identifier', STRING: 'String', NUMBER: 'Number',
  OPERATOR: 'Operator', PUNCTUATION: 'Delimiter', DELIMITER: 'Delimiter', PREPROCESSOR: 'Other',
  COMMENT: 'Comment', WHITESPACE: 'Whitespace', NEWLINE: 'Newline', INDENT: 'Indent',
  DEDENT: 'Dedent', ERROR: 'Error',
};
export function lexicalType(kind: string): LexicalType { return lexicalKinds[kind.toUpperCase()] || 'Other'; }
export function overlaps(a: Range, b: Range): boolean {
  const to = (r: Range) => [r.start_line, r.start_col, r.end_line, r.end_col] as const;
  const [al, ac, ae, ax] = to(a); const [bl, bc, be, bx] = to(b);
  return (al < be || (al === be && ac < bx)) && (bl < ae || (bl === ae && bc < ax));
}

const cache = new WeakMap<object, DerivedToken[]>();
export function deriveTokens(result: AnalysisResult): DerivedToken[] {
  const cached = cache.get(result); if (cached) return cached;
  const tokens = result.tokens || [];
  const derived = tokens.map((token, index): DerivedToken => {
    const text = token.token ?? token.text ?? '';
    const range = token.range || { start_line: token.line || 1, start_col: token.col || 1, end_line: token.line || 1, end_col: (token.col || 1) + text.length };
    const related: Finding[] = []; const steps: Finding['taint_path'] = []; const unicode: unknown[] = [];
    const lexicalError = (result.findings || []).some((finding) => finding.kind === 'lexical' && overlaps(range, finding.range));
    const detectors = new Set<string>(); let role: TokenRole = 'Neutral'; let severity = 'Safe';
    for (const finding of result.findings || []) {
      const matchedSteps = (finding.taint_path || []).filter((step) => overlaps(range, step.range));
      const findingHit = overlaps(range, finding.range);
      const evidenceUnicode = finding.evidence?.unicode;
      const unicodeHit = Boolean(finding.rule_id.includes('UNI') && findingHit || evidenceUnicode && (findingHit || matchedSteps.length));
      if (!findingHit && !matchedSteps.length && !unicodeHit) continue;
      related.push(finding);
      if (findingHit && finding.sources?.includes('rule')) detectors.add('Rule');
      if (matchedSteps.length) { detectors.add('Taint'); steps.push(...matchedSteps); }
      if (unicodeHit) { detectors.add('Unicode'); unicode.push(evidenceUnicode ?? finding.evidence); }
      if (finding.severity && ['critical', 'high', 'medium', 'low', 'info'].indexOf(finding.severity) < ['critical', 'high', 'medium', 'low', 'info'].indexOf(severity.toLowerCase()) || severity === 'Safe') severity = finding.severity;
      const step = matchedSteps.find((item) => item.step === 'source' || item.step === 'sink' || item.step === 'propagate' || item.step === 'sanitizer_missing');
      if (step) {
        const mapped: TokenRole = step.step === 'source' ? 'Source' : step.step === 'sink' ? 'Sink' : step.step === 'sanitizer_missing' ? 'Sanitizer' : 'Propagation';
        if (role === 'Neutral' || mapped === 'Sink' || mapped === 'Source') role = mapped;
      } else if (finding.rule_id.includes('OBF') || /UNI-006/.test(finding.rule_id)) role = 'Obfuscated/Encoded';
      else if (unicodeHit) role = 'Unicode';
      else if (findingHit && finding.evidence?.call) role = 'Dangerous API';
    }
    if (token.label === 'SUSPICIOUS' || token.label === 'MALICIOUS') detectors.add('ML');
    const categories = [...new Set(related.map(findingCategory).filter((category) => !['APS', 'Other'].includes(category)))];
    const fullFlow = related.filter((finding) => (finding.taint_path || []).some((step) => overlaps(range, step.range))).flatMap((finding) => finding.taint_path || []);
    const securityRelevant = role !== 'Neutral' || severity !== 'Safe' || detectors.size > 0;
    return { index, text, kind: token.token_type || 'UNKNOWN', range, label: token.label || 'SAFE', score: token.score || token.confidence || 0, lexicalType: lexicalType(token.token_type || ''), role, severity, detectors: [...detectors], relatedFindings: related, categories, securityRelevant, lexicalError, taintSteps: fullFlow.length ? fullFlow : steps, unicodeEvidence: unicode };
  });
  cache.set(result, derived); return derived;
}

export function visibleTokenText(value: string): string {
  return Array.from(value).map((char) => {
    const cp = char.codePointAt(0)!;
    return /[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/u.test(char) ? `<U+${cp.toString(16).toUpperCase().padStart(4, '0')}>` : char;
  }).join('');
}
