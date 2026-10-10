import { describe, it, expect } from 'vitest';
import {
  filterFindings,
  sortFindings,
  getTopPriorityFindingIds,
  SEVERITY_ORDER,
} from '../model/problemsSelection';
import { Finding } from '../api/client';

const mockFinding = (
  id: string,
  severity: Finding['severity'],
  line: number,
  priority = 0,
  confidence = 0.8
): Finding => ({
  id,
  severity,
  cwe: 'CWE-89',
  rule_id: 'SQLI',
  title: `${id} title`,
  message: 'msg',
  explanation: 'expl',
  label: 'MALICIOUS',
  confidence,
  priority,
  range: { start_line: line, start_col: 1, end_line: line, end_col: 5 },
  evidence: {},
  taint_path: [],
  fixes: [],
  sources: ['rule'],
});

describe('problemsSelection model', () => {
  it('filters out suppressed findings and respects severity filter', () => {
    const list: Finding[] = [
      mockFinding('1', 'critical', 1),
      { ...mockFinding('2', 'high', 2), suppressed: true },
      mockFinding('3', 'high', 3),
    ];
    expect(filterFindings(list, 'all').map((f) => f.id)).toEqual(['1', '3']);
    expect(filterFindings(list, 'high').map((f) => f.id)).toEqual(['3']);
  });

  it('sorts findings by location, confidence, and priority', () => {
    const list: Finding[] = [
      mockFinding('a', 'medium', 10, 1, 0.5),
      mockFinding('b', 'critical', 2, 5, 0.9),
      mockFinding('c', 'high', 5, 2, 0.7),
    ];
    expect(sortFindings(list, 'location').map((f) => f.id)).toEqual(['b', 'c', 'a']);
    expect(sortFindings(list, 'confidence').map((f) => f.id)).toEqual(['b', 'c', 'a']);
    expect(sortFindings(list, 'priority').map((f) => f.id)).toEqual(['b', 'c', 'a']);
  });

  it('computes top priority finding ids correctly', () => {
    const list: Finding[] = [
      mockFinding('a', 'low', 1, 1),
      mockFinding('b', 'critical', 2, 10),
      mockFinding('c', 'high', 3, 5),
      mockFinding('d', 'info', 4, 2),
    ];
    const top = getTopPriorityFindingIds(list, 2);
    expect(top.has('b')).toBe(true);
    expect(top.has('c')).toBe(true);
    expect(top.has('a')).toBe(false);
  });

  it('orders severities logically', () => {
    expect(SEVERITY_ORDER.critical).toBeLessThan(SEVERITY_ORDER.high);
    expect(SEVERITY_ORDER.high).toBeLessThan(SEVERITY_ORDER.medium);
    expect(SEVERITY_ORDER.medium).toBeLessThan(SEVERITY_ORDER.low);
    expect(SEVERITY_ORDER.low).toBeLessThan(SEVERITY_ORDER.info);
  });
});
