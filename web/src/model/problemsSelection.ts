import { Finding, Severity } from '../api/client';
import { findingCategory } from '../utils/findingCategory';
import type { ReviewFixItem } from '../components/ReviewFixesModal';

export type ProblemsSortBy = 'priority' | 'severity' | 'location' | 'confidence';

export const SEVERITY_ORDER: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export function getTopPriorityFindingIds(findings: Finding[], count = 3): Set<string> {
  const sortedByPriority = [...findings].sort(
    (a, b) => (b.priority ?? 0) - (a.priority ?? 0) || (b.confidence ?? 0) - (a.confidence ?? 0)
  );
  return new Set(sortedByPriority.slice(0, count).map((f) => f.id));
}

export function filterFindings(findings: Finding[], filter: 'all' | Severity): Finding[] {
  const active = findings.filter((f) => !f.suppressed);
  if (filter === 'all') return active;
  return active.filter((f) => f.severity === filter);
}

export function sortFindings(
  findings: Finding[],
  sortBy: ProblemsSortBy,
  grouped = false
): Finding[] {
  const sorted = [...findings].sort((a, b) => {
    if (sortBy === 'priority') {
      const pDiff = (b.priority ?? 0) - (a.priority ?? 0);
      if (Math.abs(pDiff) > 0.0001) return pDiff;
      return (
        SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] ||
        a.range.start_line - b.range.start_line
      );
    }
    if (sortBy === 'location') {
      return a.range.start_line - b.range.start_line || a.range.start_col - b.range.start_col;
    }
    if (sortBy === 'confidence') {
      return b.confidence - a.confidence;
    }
    return SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
  });

  if (!grouped) return sorted;
  return [...sorted].sort((a, b) => findingCategory(a).localeCompare(findingCategory(b)));
}

export function computeSafeFixCount(findings: Finding[]): number {
  return findings.reduce(
    (count, finding) =>
      count +
      (finding.fixes || []).filter((fix) => fix.confidence === 'safe' && fix.verification?.verified)
        .length,
    0
  );
}

export function extractReviewFixItems(source: string, findings: Finding[]): ReviewFixItem[] {
  const items: ReviewFixItem[] = [];
  const lines = source.split('\n');

  findings.forEach((finding) => {
    (finding.fixes || []).forEach((fix) => {
      if (fix.confidence === 'review' && fix.edits && fix.edits.length > 0) {
        const oldSnippet = fix.edits
          .map((e) => {
            const startLine = Math.max(0, e.range.start_line - 1);
            const endLine = Math.max(startLine, e.range.end_line - 1);
            if (startLine === endLine) {
              return (lines[startLine] || '').slice(
                e.range.start_col - 1,
                Math.max(e.range.start_col - 1, e.range.end_col - 1)
              );
            }
            return [
              lines[startLine]?.slice(e.range.start_col - 1),
              ...lines.slice(startLine + 1, endLine),
              lines[endLine]?.slice(0, e.range.end_col - 1),
            ].join('\n');
          })
          .join('\n');

        items.push({
          finding,
          fix,
          oldSnippet,
          newSnippet: fix.edits.map((e) => e.new_text).join(''),
        });
      }
    });
  });
  return items;
}
