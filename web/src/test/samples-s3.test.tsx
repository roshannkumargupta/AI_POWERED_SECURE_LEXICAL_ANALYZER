import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Sidebar } from '../components/Sidebar';
import {
  compareSample,
  groupSamples,
  groupSamplesByLanguage,
  searchSamples,
} from '../utils/sampleDemo';
import type { Finding, SampleItem } from '../api/client';

const sample = (extra: Partial<SampleItem> = {}): SampleItem => ({
  id: 'cp-i01',
  title: 'Copy input',
  category: 'vulnerable',
  language: 'cpp',
  filename: 'copy.cpp',
  code: 'strcpy(x,y)',
  description: 'copy topic',
  level: 'intermediate',
  topic: 'Memory Safety',
  expect: { findings: [{ rule_id: 'APS-CP-MEM-001' }] },
  notes: ['plain note'],
  ...extra,
});
const finding = (rule_id: string) => ({ rule_id }) as Finding;

describe('S-3 sample UI helpers', () => {
  it('groups by language-compatible level and supports old API shapes', () => {
    const oldShape = {
      ...sample(),
      level: undefined,
      topic: undefined,
      expect: undefined,
      notes: undefined,
    };
    expect(groupSamples([oldShape]).intermediate).toHaveLength(0);
    expect(groupSamples([oldShape]).basic).toHaveLength(1);
    expect(groupSamples([sample()]).intermediate).toHaveLength(1);
    expect(groupSamplesByLanguage([oldShape, sample({ language: 'python' })]).cpp).toHaveLength(1);
  });
  it('searches title, topic, and rule ID', () => {
    expect(searchSamples([sample()], 'memory')).toHaveLength(1);
    expect(searchSamples([sample()], 'APS-CP-MEM-001')).toHaveLength(1);
    expect(searchSamples([sample()], 'absent')).toHaveLength(0);
  });
  it('compares expected, missing, extra, and edited results', () => {
    const item = sample();
    expect(compareSample(item, [finding('APS-CP-MEM-001')], false)).toBe('Matches expected');
    expect(compareSample(item, [], false)).toContain('missing APS-CP-MEM-001');
    expect(compareSample(item, [finding('OTHER')], false)).toContain('extra OTHER');
    expect(compareSample(item, [], true)).toBe('Edited - comparison paused');
  });
  it('renders API-provided notes as text in the older-shape sidebar', () => {
    const oldShape = sample({
      notes: undefined,
      summary: '<img src=x onerror=alert(1)>',
      level: undefined,
      topic: undefined,
      expect: undefined,
    });
    render(
      <Sidebar
        isCollapsed={false}
        onToggleCollapse={() => {}}
        samples={[oldShape]}
        selectedSampleId={null}
        onSelectSample={() => {}}
        onOpenFile={() => {}}
        onNewFile={() => {}}
        onChooseFile={() => {}}
        language="cpp"
      />
    );
    expect(screen.queryByRole('img')).toBeNull();
  });
});
