import React, { useEffect } from 'react';
import { X, Check, AlertTriangle, ShieldCheck } from 'lucide-react';
import { Fix, Finding } from '../api/client';

interface DiffViewProps {
  isOpen: boolean;
  fix: Fix;
  finding: Finding;
  diff: string;
  before?: string;
  after?: string;
  onApply: () => void;
  onCancel: () => void;
}

export const DiffView: React.FC<DiffViewProps> = ({
  isOpen,
  fix,
  finding,
  diff,
  before = '',
  after = '',
  onApply,
  onCancel,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const isVerified = fix.verification?.verified;
  const diffLines = diff ? diff.split('\n') : [];

  return (
    <div style={overlayStyle} onClick={onCancel}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div style={headerStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={titleStyle}>Review Remediation Diff</span>
            {isVerified ? (
              <span style={verifiedBadgeStyle}>
                <ShieldCheck size={12} />
                Verified Fix
              </span>
            ) : (
              <span style={unverifiedBadgeStyle}>
                <AlertTriangle size={12} />
                Review Required
              </span>
            )}
          </div>
          <button style={closeButtonStyle} onClick={onCancel} aria-label="Close diff modal">
            <X size={18} color="var(--muted)" />
          </button>
        </div>

        {/* Content Body */}
        <div style={bodyStyle}>
          <div style={summaryRowStyle}>
            <span style={fixTitleStyle}>{fix.title}</span>
            <span style={findingRuleStyle}>Rule: {finding.rule_id}</span>
          </div>

          {fix.description && <p style={descStyle}>{fix.description}</p>}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, minHeight: 160 }}>
            <div style={diffContainerStyle}>
              <div style={diffHeaderStyle}>Before</div>
              <pre style={diffPreStyle}>{before}</pre>
            </div>
            <div style={diffContainerStyle}>
              <div style={diffHeaderStyle}>After</div>
              <pre style={diffPreStyle}>{after}</pre>
            </div>
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 6,
              fontSize: 11,
              color: 'var(--text-secondary)',
            }}
          >
            <span>{fix.verification?.syntax_ok ? '✓' : '×'} Syntax valid</span>
            <span>{fix.verification?.finding_gone ? '✓' : '×'} Original finding removed</span>
            <span>{fix.verification?.new_findings?.length === 0 ? '✓' : '×'} No new findings</span>
          </div>
          {/* Unified Diff Box */}
          <div style={diffContainerStyle}>
            <div style={diffHeaderStyle}>Unified Diff Representation</div>
            <pre style={diffPreStyle}>
              {diffLines.map((line, idx) => {
                let lineBg = 'transparent';
                let lineFg = 'var(--text)';
                if (line.startsWith('+') && !line.startsWith('+++')) {
                  lineBg = 'var(--diff-add-bg)';
                  lineFg = 'var(--success)';
                } else if (line.startsWith('-') && !line.startsWith('---')) {
                  lineBg = 'var(--diff-del-bg)';
                  lineFg = 'var(--critical)';
                } else if (line.startsWith('@@')) {
                  lineBg = 'var(--diff-context-bg)';
                  lineFg = 'var(--accent)';
                }

                return (
                  <div
                    key={idx}
                    style={{ backgroundColor: lineBg, color: lineFg, padding: '0 8px' }}
                  >
                    {line}
                  </div>
                );
              })}
            </pre>
          </div>

          {/* Verification Notes */}
          {fix.verification?.notes && (
            <div style={verificationNotesStyle}>
              <strong>Verification Sandbox Note:</strong> {fix.verification.notes}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div style={footerStyle}>
          <button style={cancelButtonStyle} onClick={onCancel}>
            Cancel
          </button>
          <button style={applyButtonStyle} onClick={onApply}>
            <Check size={14} />
            Apply Remediation
          </button>
        </div>
      </div>
    </div>
  );
};

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'var(--scrim-strong)',
  backdropFilter: 'blur(3px)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: '24px',
};

const modalStyle: React.CSSProperties = {
  width: '100%',
  maxWidth: '720px',
  maxHeight: '85vh',
  backgroundColor: 'var(--panel)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-lg)',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: 'var(--shadow-modal)',
  overflow: 'hidden',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '14px 18px',
  borderBottom: '1px solid var(--border)',
  background: 'var(--panel-2)',
};

const titleStyle: React.CSSProperties = {
  fontSize: '14px',
  fontWeight: 600,
  color: 'var(--text)',
};

const verifiedBadgeStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--success)',
  backgroundColor: 'var(--success-wash)',
  padding: '2px 8px',
  borderRadius: 'var(--radius-full)',
  border: '1px solid var(--text-success)',
};

const unverifiedBadgeStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--medium)',
  backgroundColor: 'var(--warning-wash)',
  padding: '2px 8px',
  borderRadius: 'var(--radius-full)',
  border: '1px solid var(--text-warning)',
};

const closeButtonStyle: React.CSSProperties = {
  padding: '4px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: 'var(--radius-sm)',
};

const bodyStyle: React.CSSProperties = {
  padding: '16px 18px',
  overflowY: 'auto',
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
};

const summaryRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};

const fixTitleStyle: React.CSSProperties = {
  fontWeight: 600,
  fontSize: '14px',
  color: 'var(--text)',
};

const findingRuleStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '11px',
  color: 'var(--muted)',
  backgroundColor: 'var(--panel-2)',
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
};

const descStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text-secondary)',
  lineHeight: 1.4,
};

const diffContainerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  overflow: 'hidden',
  background: 'var(--bg)',
};

const diffHeaderStyle: React.CSSProperties = {
  padding: '6px 12px',
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--muted)',
  background: 'var(--panel-2)',
  borderBottom: '1px solid var(--border)',
};

const diffPreStyle: React.CSSProperties = {
  padding: '8px 0',
  fontFamily: 'var(--font-code)',
  fontSize: '12px',
  lineHeight: 1.5,
  overflowX: 'auto',
  margin: 0,
};

const verificationNotesStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  padding: '8px 12px',
  background: 'var(--panel-2)',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
};

const footerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  gap: '10px',
  padding: '12px 18px',
  borderTop: '1px solid var(--border)',
  background: 'var(--panel-2)',
};

const cancelButtonStyle: React.CSSProperties = {
  padding: '6px 14px',
  borderRadius: 'var(--radius)',
  border: '1px solid var(--border)',
  color: 'var(--text-secondary)',
  fontWeight: 500,
  fontSize: '12px',
};

const applyButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '6px 16px',
  borderRadius: 'var(--radius)',
  backgroundColor: 'var(--accent)',
  color: 'var(--text-on-accent)',
  fontWeight: 600,
  fontSize: '12px',
};
