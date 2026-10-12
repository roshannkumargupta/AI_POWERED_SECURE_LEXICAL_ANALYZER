import type { SampleItem } from '../../api/client';

export const SAMPLE_GROUPS = [
  { id: 'valid', label: 'valid' },
  { id: 'lexical-errors', label: 'lexical-errors' },
  { id: 'syntax-errors', label: 'syntax-errors' },
  { id: 'security', label: 'security' },
  { id: 'adversarial', label: 'adversarial' },
] as const;
export type SampleGroup = (typeof SAMPLE_GROUPS)[number]['id'];

export function groupSample(sample: SampleItem): SampleGroup {
  const metadata = [sample.kind, sample.category, sample.topic, sample.title].filter(Boolean).join(' ').toLocaleLowerCase().replace(/[_-]+/g, ' ');
  if (metadata.includes('adversarial')) return 'adversarial';
  if (metadata.includes('lexical') || metadata.includes('lexer')) return 'lexical-errors';
  if (metadata.includes('syntax') || metadata.includes('parser')) return 'syntax-errors';
  if (metadata.includes('security') || metadata.includes('vulnerable') || metadata.includes('cwe')) return 'security';
  return 'valid';
}

export function sampleBadge(sample: SampleItem): string | null {
  const expected = sample.expect?.findings?.map((finding) => finding.rule_id).filter(Boolean) ?? [];
  if (expected.length) return expected.slice(0, 2).join(', ');
  if (sample.expect?.min_findings !== undefined) return `${sample.expect.min_findings}+ expected`;
  if (sample.category) return sample.category;
  return null;
}
