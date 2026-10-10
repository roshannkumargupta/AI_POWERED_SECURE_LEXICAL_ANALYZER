import React, { useState } from 'react';
import { SampleItem } from '../api/client';
import { DEMO_PATH, LEVELS, searchSamples, levelOf } from '../utils/sampleDemo';
import {
  samplesSectionStyle,
  sectionHeaderStyle,
  badgeCountStyle,
  samplesListStyle,
  groupHeaderStyle,
  sampleItemStyle,
  sampleTitleStyle,
  sampleLabelStyle,
} from './sidebarStyles';

interface SidebarSampleListProps {
  samples: SampleItem[];
  selectedSampleId: string | null;
  onSelectSample: (sample: SampleItem) => void;
  language: string;
}

export const SidebarSampleList: React.FC<SidebarSampleListProps> = ({
  samples,
  selectedSampleId,
  onSelectSample,
  language,
}) => {
  const [query, setQuery] = useState('');
  const [showAll, setShowAll] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const [demoOpen, setDemoOpen] = useState(false);

  const visible = searchSamples(samples, query);

  return (
    <div style={samplesSectionStyle}>
      <div style={sectionHeaderStyle}>
        <span>SAMPLES</span>
        <span style={badgeCountStyle}>
          {samples.filter((s) => showAll || language === 'auto' || s.language === language).length}
        </span>
      </div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search samples"
        aria-label="Search samples"
        style={{
          margin: '4px 10px 8px',
          padding: '6px 8px',
          background: 'var(--bg)',
          color: 'var(--text)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
        }}
      />
      <button
        onClick={() => setShowAll((value) => !value)}
        style={{
          margin: '0 10px 6px',
          color: 'var(--accent)',
          background: 'transparent',
          border: 0,
          textAlign: 'left',
          cursor: 'pointer',
        }}
      >
        {showAll ? 'Show active language' : 'Show all languages'}
      </button>

      <div style={samplesListStyle}>
        <button
          aria-expanded={demoOpen}
          onClick={() => setDemoOpen((open) => !open)}
          style={groupHeaderStyle}
        >
          DEMO PATH <span style={badgeCountStyle}>13</span>
        </button>
        {demoOpen &&
          DEMO_PATH.map((id, index) => {
            const sample = samples.find((item) => item.id === id);
            return sample ? (
              <button
                key={id}
                style={sampleItemStyle}
                onClick={() => onSelectSample(sample)}
                title={sample.summary || sample.description}
              >
                {index + 1}. {sample.title}
              </button>
            ) : null;
          })}
        {(showAll || language === 'auto'
          ? ['python', 'java', 'javascript', 'cpp']
          : [language]
        ).map((group) => {
          const groupSamples = visible.filter((s) => s.language === group);
          const label =
            group === 'cpp'
              ? 'C/C++'
              : group === 'javascript'
                ? 'JavaScript'
                : group[0].toUpperCase() + group.slice(1);
          const expanded = expandedGroups[group] ?? showAll;
          return (
            <React.Fragment key={group}>
              {(language === 'auto' || showAll) && (
                <button
                  aria-expanded={expanded}
                  onKeyDown={(event) => {
                    if (event.key === 'ArrowRight')
                      setExpandedGroups((current) => ({ ...current, [group]: true }));
                    if (event.key === 'ArrowLeft')
                      setExpandedGroups((current) => ({ ...current, [group]: false }));
                  }}
                  onClick={() =>
                    setExpandedGroups((current) => ({ ...current, [group]: !current[group] }))
                  }
                  style={groupHeaderStyle}
                >
                  {label}
                  <span style={badgeCountStyle}>{groupSamples.length}</span>
                </button>
              )}
              {(expanded || (language !== 'auto' && !showAll && group === language)) &&
                LEVELS.map((level) => {
                  const levelSamples = groupSamples.filter((sample) => levelOf(sample) === level);
                  if (!levelSamples.length) return null;
                  const key = `${group}:${level}`;
                  const open = expandedGroups[key] ?? level === 'basic';
                  const levelTitle =
                    level === 'safe'
                      ? 'Safe code'
                      : level === 'unicode'
                        ? 'Unicode'
                        : level === 'lexer'
                          ? 'Lexer showcase'
                          : level[0].toUpperCase() + level.slice(1);
                  return (
                    <React.Fragment key={key}>
                      <button
                        aria-expanded={open}
                        onKeyDown={(event) => {
                          if (event.key === 'ArrowRight')
                            setExpandedGroups((current) => ({ ...current, [key]: true }));
                          if (event.key === 'ArrowLeft')
                            setExpandedGroups((current) => ({ ...current, [key]: false }));
                        }}
                        onClick={() =>
                          setExpandedGroups((current) => ({ ...current, [key]: !open }))
                        }
                        style={groupHeaderStyle}
                      >
                        {levelTitle}
                        <span style={badgeCountStyle}>{levelSamples.length}</span>
                      </button>
                      {open &&
                        levelSamples.map((sample) => {
                          const isSelected = sample.id === selectedSampleId;
                          const chip =
                            level === 'safe'
                              ? 'Safe'
                              : level === 'lexer'
                                ? 'Lexer'
                                : level === 'unicode'
                                  ? 'Unicode'
                                  : 'Vulnerable';

                          return (
                            <button
                              key={sample.id}
                              data-sample-row="true"
                              style={{
                                ...sampleItemStyle,
                                backgroundColor: isSelected ? 'var(--panel-3)' : 'transparent',
                                borderLeft: isSelected
                                  ? '2px solid var(--accent)'
                                  : '2px solid transparent',
                              }}
                              onClick={() => onSelectSample(sample)}
                              onKeyDown={(event) => {
                                if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                                  event.preventDefault();
                                  const rows = Array.from(
                                    document.querySelectorAll<HTMLButtonElement>(
                                      '[data-sample-row="true"]'
                                    )
                                  );
                                  const index = rows.indexOf(event.currentTarget);
                                  rows[index + (event.key === 'ArrowDown' ? 1 : -1)]?.focus();
                                }
                              }}
                              title={sample.description}
                            >
                              <div
                                style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}
                              >
                                <div
                                  style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'flex-start',
                                  }}
                                >
                                  <span style={sampleTitleStyle}>{sample.title}</span>
                                  <span style={sampleLabelStyle}>{chip}</span>
                                </div>
                              </div>
                            </button>
                          );
                        })}
                    </React.Fragment>
                  );
                })}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
