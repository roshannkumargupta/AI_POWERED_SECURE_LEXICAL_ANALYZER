import React from 'react';
import { Check, Copy } from 'lucide-react';
import { Finding, Fix } from '../api/client';

interface ExplanationActionBarProps {
  hasEdit: boolean;
  fix?: Fix;
  finding?: Finding;
  isStale: boolean;
  isVerifiedSafe: boolean;
  copiedAdvice: boolean;
  onApplyFix: (fix: Fix, finding: Finding) => void;
  onCopyAdvice: () => void;
  onFalsePositive: (finding: Finding) => void;
}

export const ExplanationActionBar: React.FC<ExplanationActionBarProps> = ({
  hasEdit,
  fix,
  finding,
  isStale,
  isVerifiedSafe,
  copiedAdvice,
  onApplyFix,
  onCopyAdvice,
  onFalsePositive,
}) => {
  return (
    <footer
      className="ui6-explain-actions"
      style={{
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderTop: '1px solid var(--border)',
        paddingTop: '6px',
        marginTop: '6px',
        gap: '8px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {hasEdit && fix && finding && (
          <button
            className="ui6-apply-fix"
            disabled={isStale}
            title={
              isStale
                ? 'Analyse again first'
                : isVerifiedSafe
                  ? 'Apply verified fix'
                  : 'Apply review fix'
            }
            onClick={() => onApplyFix(fix, finding)}
            style={{
              cursor: isStale ? 'not-allowed' : 'pointer',
              opacity: isStale ? 0.5 : 1,
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            Apply fix
          </button>
        )}

        <button
          type="button"
          className="ui6-switch"
          onClick={onCopyAdvice}
          title="Copy advice text to clipboard"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
            padding: '3px 8px',
            borderRadius: 3,
          }}
        >
          {copiedAdvice ? <Check size={11} color="var(--text-success)" /> : <Copy size={11} />}
          <span>{copiedAdvice ? 'Copied' : 'Copy advice'}</span>
        </button>
      </div>

      {finding && (
        <button
          type="button"
          className="ui6-switch"
          onClick={() => onFalsePositive(finding)}
          title="Report this finding as a false positive"
          style={{ padding: '3px 8px', borderRadius: 3 }}
        >
          Mark as false positive
        </button>
      )}
    </footer>
  );
};
