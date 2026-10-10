import React from 'react';
import { Finding } from '../api/client';
import { sectionTitleStyle, explanationTextStyle } from './findingStyles';

interface FindingExplanationProps {
  finding: Finding;
}

export const FindingExplanation: React.FC<FindingExplanationProps> = ({ finding }) => {
  const [explanationMode, setExplanationMode] = React.useState<'simple' | 'detailed'>('detailed');

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={sectionTitleStyle}>WHY IT WAS FLAGGED</span>
        {(['rule', 'taint', 'ml', 'unicode'] as const).map((source) => {
          const active =
            finding.sources?.some((value) => value.toLowerCase().includes(source)) ||
            (source === 'taint' && Boolean(finding.taint_path?.length));
          return (
            <span
              key={source}
              style={{
                color: active ? 'var(--text-secondary)' : 'var(--muted-dark)',
                fontSize: 11,
              }}
            >
              {active ? '✓' : '○'} {source[0].toUpperCase() + source.slice(1)}
            </span>
          );
        })}
      </div>
      <details style={{ color: 'var(--muted)', fontSize: 11 }}>
        <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)' }}>Details</summary>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 6,
            padding: '8px 0',
          }}
        >
          <span>Rule: {finding.rule_id}</span>
          <span>Confidence: {Math.round(finding.confidence * 100)}%</span>
          <span>
            Range: {finding.range.start_line}:{finding.range.start_col}
          </span>
          <span>Detectors: {finding.sources?.join(', ') || '—'}</span>
        </div>
      </details>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: '10px',
        }}
      >
        <span style={sectionTitleStyle}>EXPLANATION</span>
        <div
          style={{
            display: 'inline-flex',
            borderRadius: '4px',
            border: '1px solid var(--border)',
            overflow: 'hidden',
          }}
        >
          <button
            data-qa="simple-explanation-toggle"
            type="button"
            style={{
              padding: '2px 8px',
              fontSize: '11px',
              fontWeight: explanationMode === 'simple' ? 600 : 400,
              backgroundColor: explanationMode === 'simple' ? 'var(--accent)' : 'var(--panel-2)',
              color:
                explanationMode === 'simple' ? 'var(--text-on-accent)' : 'var(--text-secondary)',
              border: 'none',
              cursor: 'pointer',
            }}
            onClick={() => setExplanationMode('simple')}
          >
            Simple
          </button>
          <button
            data-qa="detailed-explanation-toggle"
            type="button"
            style={{
              padding: '2px 8px',
              fontSize: '11px',
              fontWeight: explanationMode === 'detailed' ? 600 : 400,
              backgroundColor: explanationMode === 'detailed' ? 'var(--accent)' : 'var(--panel-2)',
              color:
                explanationMode === 'detailed' ? 'var(--text-on-accent)' : 'var(--text-secondary)',
              border: 'none',
              cursor: 'pointer',
            }}
            onClick={() => setExplanationMode('detailed')}
          >
            Detailed
          </button>
        </div>
      </div>
      <div style={{ ...explanationTextStyle, whiteSpace: 'pre-wrap' }}>
        {explanationMode === 'simple'
          ? finding.simple_explanation || finding.explanation?.split('\n\n')[0] || finding.message
          : finding.detailed_explanation || finding.explanation || finding.message}
      </div>
    </>
  );
};
