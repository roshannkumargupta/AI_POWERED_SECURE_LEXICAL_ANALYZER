import type { AnalysisResult, Finding } from '../api/client';
import type { Range } from '../utils/offsets';
import { findingCategory } from '../utils/findingCategory';

export type LexicalType =
  | 'Keyword'
  | 'Identifier'
  | 'String'
  | 'Number'
  | 'Operator'
  | 'Delimiter'
  | 'Comment'
  | 'Whitespace'
  | 'Newline'
  | 'Indent'
  | 'Dedent'
  | 'Error'
  | 'Other';
export type TokenRole =
  | 'Source'
  | 'Propagation'
  | 'Sink'
  | 'Sanitizer'
  | 'Dangerous API'
  | 'Unicode'
  | 'Obfuscated/Encoded'
  | 'Neutral';
export interface DerivedToken {
  index: number;
  text: string;
  kind: string;
  range: Range;
  label: string;
  score: number;
  lexicalType: LexicalType;
  role: TokenRole;
  severity: 'Safe' | string;
  detectors: string[];
  relatedFindings: Finding[];
  categories: string[];
  securityRelevant: boolean;
  lexicalError: boolean;
  taintSteps: Finding['taint_path'];
  unicodeEvidence: unknown[];
}

const lexicalKinds: Record<string, LexicalType> = {
  KEYWORD: 'Keyword',
  IDENTIFIER: 'Identifier',
  STRING: 'String',
  NUMBER: 'Number',
  OPERATOR: 'Operator',
  PUNCTUATION: 'Delimiter',
  DELIMITER: 'Delimiter',
  PREPROCESSOR: 'Other',
  COMMENT: 'Comment',
  WHITESPACE: 'Whitespace',
  NEWLINE: 'Newline',
  INDENT: 'Indent',
  DEDENT: 'Dedent',
  ERROR: 'Error',
};
export function lexicalType(kind: string): LexicalType {
  return lexicalKinds[kind.toUpperCase()] || 'Other';
}
export function overlaps(a: Range, b: Range): boolean {
  const to = (r: Range) => [r.start_line, r.start_col, r.end_line, r.end_col] as const;
  const [al, ac, ae, ax] = to(a);
  const [bl, bc, be, bx] = to(b);
  return (al < be || (al === be && ac < bx)) && (bl < ae || (bl === ae && bc < ax));
}

const cache = new WeakMap<object, DerivedToken[]>();
const severityRank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
export function deriveTokens(result: AnalysisResult): DerivedToken[] {
  const cached = cache.get(result);
  if (cached) return cached;
  const tokens = result.tokens || [];
  const findings = (result.findings || []).map((finding) => ({
    finding,
    category: findingCategory(finding),
    steps: finding.taint_path || [],
    severity: finding.severity || 'Safe',
    severityRank: severityRank[finding.severity?.toLowerCase() ?? ''] ?? Number.POSITIVE_INFINITY,
    lexical: finding.kind === 'lexical',
    unicodeRule: finding.rule_id.includes('UNI'),
    obfuscationRule: finding.rule_id.includes('OBF') || /UNI-006/.test(finding.rule_id),
    ruleDetector: finding.sources?.includes('rule') ?? false,
    unicodeEvidence: finding.evidence?.unicode,
    callEvidence: Boolean(finding.evidence?.call),
  }));
  const derived = tokens.map((token, index): DerivedToken => {
    const text = token.token ?? token.text ?? '';
    const range = token.range || {
      start_line: token.line || 1,
      start_col: token.col || 1,
      end_line: token.line || 1,
      end_col: (token.col || 1) + text.length,
    };
    const related: Finding[] = [];
    const steps: Finding['taint_path'] = [];
    const unicode: unknown[] = [];
    let lexicalError = false;
    const detectors = new Set<string>();
    let role: TokenRole = 'Neutral';
    let severity = 'Safe';
    let currentSeverityRank = Number.POSITIVE_INFINITY;
    const relatedCategories: string[] = [];
    const fullFlow: Finding['taint_path'] = [];
    for (const info of findings) {
      const { finding } = info;
      const findingHit = overlaps(range, finding.range);
      if (info.lexical && findingHit) lexicalError = true;
      const matchedSteps = info.steps.filter((step) => overlaps(range, step.range));
      const unicodeHit = Boolean(
        (info.unicodeRule && findingHit) ||
        (info.unicodeEvidence && (findingHit || matchedSteps.length))
      );
      if (!findingHit && !matchedSteps.length && !unicodeHit) continue;
      related.push(finding);
      relatedCategories.push(info.category);
      if (matchedSteps.length) fullFlow.push(...info.steps);
      if (findingHit && info.ruleDetector) detectors.add('Rule');
      if (matchedSteps.length) {
        detectors.add('Taint');
        steps.push(...matchedSteps);
      }
      if (unicodeHit) {
        detectors.add('Unicode');
        unicode.push(info.unicodeEvidence ?? finding.evidence);
      }
      if (info.severityRank < currentSeverityRank) {
        severity = info.severity;
        currentSeverityRank = info.severityRank;
      }
      const step = matchedSteps.find(
        (item) =>
          item.step === 'source' ||
          item.step === 'sink' ||
          item.step === 'propagate' ||
          item.step === 'sanitizer_missing'
      );
      if (step) {
        const mapped: TokenRole =
          step.step === 'source'
            ? 'Source'
            : step.step === 'sink'
              ? 'Sink'
              : step.step === 'sanitizer_missing'
                ? 'Sanitizer'
                : 'Propagation';
        if (role === 'Neutral' || mapped === 'Sink' || mapped === 'Source') role = mapped;
      } else if (info.obfuscationRule) role = 'Obfuscated/Encoded';
      else if (unicodeHit) role = 'Unicode';
      else if (findingHit && info.callEvidence) role = 'Dangerous API';
    }
    if (token.label === 'SUSPICIOUS' || token.label === 'MALICIOUS') detectors.add('ML');
    const categories = [
      ...new Set(relatedCategories.filter((category) => !['APS', 'Other'].includes(category))),
    ];
    const securityRelevant = role !== 'Neutral' || severity !== 'Safe' || detectors.size > 0;
    return {
      index,
      text,
      kind: token.token_type || 'UNKNOWN',
      range,
      label: token.label || 'SAFE',
      score: token.score || token.confidence || 0,
      lexicalType: lexicalType(token.token_type || ''),
      role,
      severity,
      detectors: [...detectors],
      relatedFindings: related,
      categories,
      securityRelevant,
      lexicalError,
      taintSteps: fullFlow.length ? fullFlow : steps,
      unicodeEvidence: unicode,
    };
  });
  cache.set(result, derived);
  return derived;
}

export function visibleTokenText(value: string): string {
  return Array.from(value)
    .map((char) => {
      const cp = char.codePointAt(0)!;
      return /[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/u.test(char)
        ? `<U+${cp.toString(16).toUpperCase().padStart(4, '0')}>`
        : char;
    })
    .join('');
}
