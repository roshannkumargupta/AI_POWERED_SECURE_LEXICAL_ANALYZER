import React, { useMemo, useState } from 'react';
import type { SampleItem } from '../api/client';
import { LEVELS, levelOf, searchSamples, DEMO_PATH } from '../utils/sampleDemo';

interface FlyoutSamplesProps {
  samples: SampleItem[];
  language: string;
  onSample: (sample: SampleItem) => void;
}

const languageName = (language: string) =>
  language === 'cpp'
    ? 'C/C++'
    : language === 'javascript'
      ? 'JavaScript'
      : `${language[0]?.toUpperCase() || ''}${language.slice(1)}`;

export const FlyoutSamples: React.FC<FlyoutSamplesProps> = ({ samples, language, onSample }) => {
  const [query, setQuery] = useState('');
  const [showAll, setShowAll] = useState(false);
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  const filtered = useMemo(() => searchSamples(samples, query), [samples, query]);
  const languages = ['python', 'java', 'javascript', 'cpp'];
  const visibleLanguages = showAll || language === 'auto' ? languages : [language];

  return (
    <>
      <input
        className="ui6-search"
        aria-label="Search samples"
        placeholder="Search samples"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <button className="ui6-show-languages" onClick={() => setShowAll((value) => !value)}>
        {showAll ? 'Show active language' : 'Show all languages'}
      </button>
      <div className="ui6-samples-list">
        {visibleLanguages.map((lang) => {
          const groupRows = filtered.filter((sample) => sample.language === lang);
          const targetDemos =
            lang === 'python'
              ? groupRows.filter((sample) => /Target Demo/i.test(sample.title))
              : [];
          const ordinary = groupRows.filter((sample) => !targetDemos.includes(sample));
          const expanded = openGroups[lang] ?? language !== 'auto';
          return (
            <div key={lang}>
              <button
                className="ui6-group"
                aria-expanded={expanded}
                onClick={() => setOpenGroups((current) => ({ ...current, [lang]: !expanded }))}
              >
                {languageName(lang)}
                <span>{groupRows.length}</span>
              </button>
              {expanded && (
                <>
                  {targetDemos.map((sample) => (
                    <button
                      key={sample.id}
                      className="ui6-sample"
                      onClick={() => onSample(sample)}
                      title={sample.description}
                    >
                      {sample.title}
                    </button>
                  ))}
                  {LEVELS.map((level) => {
                    const levelSamples = ordinary.filter((sample) => levelOf(sample) === level);
                    if (!levelSamples.length) return null;
                    const key = `${lang}:${level}`;
                    const levelOpen = openGroups[key] ?? false;
                    const label =
                      level === 'safe'
                        ? 'Safe code'
                        : level === 'lexer'
                          ? 'Lexer showcase'
                          : level[0].toUpperCase() + level.slice(1);
                    return (
                      <div key={key}>
                        <button
                          className="ui6-group level"
                          aria-expanded={levelOpen}
                          onClick={() =>
                            setOpenGroups((current) => ({ ...current, [key]: !levelOpen }))
                          }
                        >
                          {label}
                          <span>{levelSamples.length}</span>
                        </button>
                        {levelOpen &&
                          levelSamples.map((sample) => (
                            <button
                              key={sample.id}
                              className="ui6-sample"
                              onClick={() => onSample(sample)}
                              title={sample.description}
                            >
                              {sample.title}
                            </button>
                          ))}
                      </div>
                    );
                  })}
                </>
              )}
            </div>
          );
        })}
      </div>
      {samples.find((sample) => sample.notes?.length || sample.demo_order) && (
        <details className="ui6-demo-notes">
          <summary>Demo path and notes</summary>
          <ol>
            {DEMO_PATH.map((id) => samples.find((sample) => sample.id === id))
              .filter((sample): sample is SampleItem => Boolean(sample))
              .map((sample) => (
                <li key={sample.id}>
                  <button onClick={() => onSample(sample)}>{sample.title}</button>
                  {sample.notes?.[0] && <small> — {sample.notes[0]}</small>}
                </li>
              ))}
          </ol>
        </details>
      )}
    </>
  );
};
