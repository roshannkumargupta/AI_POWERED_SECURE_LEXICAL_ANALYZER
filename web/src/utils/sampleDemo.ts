import type { Finding, SampleItem } from '../api/client';

export const DEMO_PATH = [
  'py-i01',
  'py-s02',
  'py-u04',
  'py-u01',
  'py-b06',
  'py-a06',
  'jv-i01',
  'jv-i06',
  'js-b04',
  'js-a01',
  'cp-i01',
  'cp-a06',
  'py-a04',
];
export const LEVELS = ['basic', 'intermediate', 'advanced', 'safe', 'unicode', 'lexer'] as const;
export const levelOf = (sample: SampleItem) =>
  sample.level ||
  sample.kind ||
  (sample.category === 'vulnerable'
    ? 'basic'
    : sample.category === 'adversarial'
      ? 'unicode'
      : sample.category);
export function groupSamplesByLanguage(samples: SampleItem[]) {
  return samples.reduce<Record<string, SampleItem[]>>((groups, sample) => {
    (groups[sample.language] ||= []).push(sample);
    return groups;
  }, {});
}
export function groupSamples(samples: SampleItem[]) {
  return Object.fromEntries(
    LEVELS.map((level) => [level, samples.filter((sample) => levelOf(sample) === level)])
  );
}
export function searchSamples(samples: SampleItem[], query: string) {
  const q = query.trim().toLocaleLowerCase();
  return samples.filter(
    (sample) =>
      !q ||
      [
        sample.title,
        sample.topic,
        sample.summary,
        sample.description,
        ...(sample.expect?.findings || []).map((finding) => finding.rule_id),
      ].some((text) => (text || '').toLocaleLowerCase().includes(q))
  );
}
export function compareSample(sample: SampleItem, findings: Finding[], edited: boolean) {
  if (edited) return 'Edited - comparison paused';
  const expected = sample.expect?.findings || [];
  const want = expected.map((item) => item.rule_id);
  const got = findings.map((item) => item.rule_id);
  const missing: string[] = [];
  const extra: string[] = [];
  for (const id of new Set([...want, ...got])) {
    const expectedCount = want.filter((value) => value === id).length;
    const actualCount = got.filter((value) => value === id).length;
    for (let index = actualCount; index < expectedCount; index++) missing.push(id);
    for (let index = expectedCount; index < actualCount; index++) extra.push(id);
  }
  if (!missing.length && !extra.length) return 'Matches expected';
  return `Differs from expected: missing ${missing.join(', ') || 'none'} / extra ${extra.join(', ') || 'none'}`;
}
