import React from 'react';
import { AnalysisSummary, EngineMetadata } from '../api/client';

interface FindingSummaryViewProps {
  summary: AnalysisSummary | null;
  engine?: EngineMetadata | null;
  language?: string;
}

export const FindingSummaryView: React.FC<FindingSummaryViewProps> = ({
  summary,
  engine = null,
  language = 'auto',
}) => {
  if (!summary) {
    return <div className="ui5-empty">Open or paste code to analyse it.</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div className="ui6-summary-grid">
        {[
          ['Score', summary.score],
          ['Critical', summary.critical],
          ['High', summary.high],
          ['Lexical', summary.lexical_errors ?? 0],
        ].map(([label, value]) => (
          <div className="ui6-summary-tile" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {(summary.medium > 0 || summary.low > 0) && (
        <div className="ui6-summary-grid secondary">
          {summary.medium > 0 && (
            <div className="ui6-summary-tile">
              <span>Medium</span>
              <strong>{summary.medium}</strong>
            </div>
          )}
          {summary.low > 0 && (
            <div className="ui6-summary-tile">
              <span>Low</span>
              <strong>{summary.low}</strong>
            </div>
          )}
        </div>
      )}
      <p className="ui6-summary-note">
        Lexical errors are listed separately and do not change the score.
      </p>
      <div className="ui6-summary-meta">
        {summary.tokens_total} tokens analysed · {engine?.elapsed_ms.toFixed(0) ?? '—'} ms ·{' '}
        {language} · {engine?.parser || 'lexer-only'}
      </div>
    </div>
  );
};
