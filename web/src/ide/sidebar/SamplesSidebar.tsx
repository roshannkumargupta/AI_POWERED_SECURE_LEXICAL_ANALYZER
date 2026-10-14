import { useEffect, useMemo, useState } from 'react';
import type { SampleItem } from '../../api/client';
import { groupSample, SAMPLE_GROUPS } from '../lib/sampleGroups';

const expectedBadge = (sample: SampleItem) => {
  const rules = sample.expect?.findings?.map((item) => item.rule_id).filter(Boolean) ?? [];
  if (rules.length) return rules.slice(0, 2).join(', ');
  return sample.expect?.min_findings === undefined
    ? null
    : `${sample.expect.min_findings}+ expected`;
};

const sections = [
  {
    id: 'python',
    label: 'Python',
    match: (language: string) =>
      language.toLowerCase().includes('python') || language.toLowerCase() === 'py',
  },
  { id: 'java', label: 'Java', match: (language: string) => language.toLowerCase() === 'java' },
  {
    id: 'javascript',
    label: 'JavaScript',
    match: (language: string) => ['javascript', 'js'].includes(language.toLowerCase()),
  },
  {
    id: 'cpp',
    label: 'C / C++',
    match: (language: string) => ['cpp', 'c++', 'c'].includes(language.toLowerCase()),
  },
] as const;
const storageKey = 'securelex.ide.samples-expanded.v1';
type Expanded = Record<string, boolean>;

function readExpanded(): Expanded {
  try {
    const value = localStorage.getItem(storageKey);
    return value ? (JSON.parse(value) as Expanded) : {};
  } catch {
    return {};
  }
}

export function SamplesSidebar({
  samples,
  unavailable,
  onOpen,
}: {
  samples: SampleItem[];
  unavailable: boolean;
  onOpen(sample: SampleItem): void;
}) {
  const [query, setQuery] = useState('');
  const [expanded, setExpanded] = useState<Expanded>(readExpanded);
  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(expanded));
    } catch {
      /* Keep the view usable when storage is unavailable. */
    }
  }, [expanded]);
  const needle = query.trim().toLocaleLowerCase();
  const grouped = useMemo(
    () =>
      sections.map((section) => {
        const files = samples.filter(
          (sample) =>
            section.match(sample.language) &&
            (!needle ||
              `${sample.filename} ${sample.title} ${sample.description} ${sample.language}`
                .toLocaleLowerCase()
                .includes(needle))
        );
        return {
          ...section,
          files,
          groups: SAMPLE_GROUPS.map((group) => ({
            ...group,
            files: files.filter((sample) => groupSample(sample) === group.id),
          })),
        };
      }),
    [samples, needle]
  );
  const toggle = (id: string) => setExpanded((value) => ({ ...value, [id]: value[id] === false }));
  return (
    <div className="ide-tree-scroll ide-samples-view">
      <label className="ide-samples-search">
        <span className="material-symbols-outlined" aria-hidden="true">
          search
        </span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search samples"
          aria-label="Search samples across languages"
        />
      </label>
      {unavailable && (
        <div className="ide-tree-message">Sample catalogue unavailable. Retry from Explorer.</div>
      )}
      {!samples.length && !unavailable && <div className="ide-tree-message">Loading samples…</div>}
      {grouped.map((section) => (
        <section key={section.id} className="ide-sample-language">
          <button
            type="button"
            className="ide-sample-language-heading"
            aria-expanded={expanded[section.id] !== false}
            onClick={() => toggle(section.id)}
          >
            <span className="material-symbols-outlined" aria-hidden="true">
              {expanded[section.id] === false ? 'chevron_right' : 'expand_more'}
            </span>
            <span>{section.label}</span>
            <span className="ide-group-count">{section.files.length}</span>
          </button>
          {expanded[section.id] !== false &&
            section.groups.map((group) => (
              <div key={group.id} className="ide-sample-category">
                <div className="ide-sample-category-heading">
                  {group.label}
                  <span className="ide-group-count">{group.files.length}</span>
                </div>
                {group.files.length ? (
                  group.files.map((sample) => (
                    <button
                      type="button"
                      key={sample.id}
                      className="ide-tree-row ide-sample-row"
                      title={sample.description}
                      onClick={() => onOpen(sample)}
                    >
                      <span className="ide-row-main">
                        <span className="ide-file-icon">
                          <span className="material-symbols-outlined" aria-hidden="true">
                            description
                          </span>
                        </span>
                        <span className="filename">{sample.filename}</span>
                      </span>
                      {expectedBadge(sample) && (
                        <span className="ide-sample-badge" title="Expected findings">
                          {expectedBadge(sample)}
                        </span>
                      )}
                    </button>
                  ))
                ) : (
                  <div className="ide-sample-none">none</div>
                )}
              </div>
            ))}
        </section>
      ))}
    </div>
  );
}
