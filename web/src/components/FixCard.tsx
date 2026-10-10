import React from 'react';
import { ShieldCheck, Wand2 } from 'lucide-react';
import { Finding, Fix } from '../api/client';

interface FixCardProps {
  fix: Fix;
  finding: Finding;
  onOpenDiff: (fix: Fix, finding: Finding) => void;
  onApplyFix: (fix: Fix, finding: Finding) => void;
}

export const FixCard: React.FC<FixCardProps> = ({ fix, finding, onOpenDiff, onApplyFix }) => {
  const isVerified = Boolean(fix.verification?.verified);
  const isSafe = fix.confidence === 'safe';
  const hasEdits = Boolean(fix.edits && fix.edits.length > 0);
  const isLLM = fix.kind === 'llm';

  return (
    <div style={fixCardStyle}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={fixTitleStyle}>{fix.title}</span>
            {isLLM && (
              <span
                style={{
                  padding: '1px 5px',
                  borderRadius: '3px',
                  fontSize: '10px',
                  fontWeight: 600,
                  backgroundColor: 'var(--accent-subtle)',
                  color: 'var(--accent)',
                }}
              >
                AI
              </span>
            )}
            {isVerified && isSafe ? (
              <span style={verifiedBadgeStyle}>
                <ShieldCheck size={11} />
                Verified after re-analysis
              </span>
            ) : isLLM && !isVerified ? (
              <span style={unverifiedBadgeStyle}>Advice only (Unverified AI suggestion)</span>
            ) : (
              <span style={unverifiedBadgeStyle}>Review needed</span>
            )}
          </div>
          <p style={fixDescStyle}>{fix.description}</p>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          marginTop: '8px',
          gap: '6px',
        }}
      >
        {hasEdits && (
          <button
            style={reviewFixBtnStyle}
            onClick={() => onOpenDiff(fix, finding)}
            title="Preview unified diff"
          >
            Review Diff
          </button>
        )}

        {((isSafe && isVerified) ||
          (fix.confidence === 'review' && hasEdits) ||
          (isLLM && isVerified && hasEdits)) && (
          <button
            style={applyFixBtnStyle}
            onClick={() => onApplyFix(fix, finding)}
            title={isSafe && isVerified ? 'Apply verified fix' : 'Apply fix'}
          >
            <Wand2 size={12} />
            {isVerified ? 'Apply Verified Fix' : 'Apply Fix'}
          </button>
        )}
      </div>
    </div>
  );
};

const fixCardStyle: React.CSSProperties = {
  padding: '10px 12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
};

const fixTitleStyle: React.CSSProperties = {
  fontSize: '13px',
  fontWeight: 600,
  color: 'var(--text)',
};

const verifiedBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '3px',
  fontSize: '10px',
  fontWeight: 600,
  color: 'var(--success)',
  backgroundColor: 'var(--success-wash)',
  padding: '1px 6px',
  borderRadius: 'var(--radius-full)',
};

const unverifiedBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '3px',
  fontSize: '10px',
  fontWeight: 600,
  color: 'var(--medium)',
  backgroundColor: 'var(--warning-wash)',
  padding: '1px 6px',
  borderRadius: 'var(--radius-full)',
};

const fixDescStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  marginTop: '4px',
  lineHeight: 1.4,
};

const applyFixBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
  fontSize: '11px',
  fontWeight: 600,
  padding: '5px 12px',
  backgroundColor: 'var(--accent)',
  color: 'var(--text-on-accent)',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
};

const reviewFixBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
  fontSize: '11px',
  fontWeight: 600,
  padding: '5px 12px',
  backgroundColor: 'var(--panel-3)',
  color: 'var(--text)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
};
