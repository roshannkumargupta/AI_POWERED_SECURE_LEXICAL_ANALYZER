import React, { useEffect } from 'react';
import { X, Check, AlertTriangle, ShieldCheck } from 'lucide-react';
import { Fix, Finding } from '../api/client';
import {
  overlayStyle,
  modalStyle,
  headerStyle,
  titleStyle,
  verifiedBadgeStyle,
  unverifiedBadgeStyle,
  closeButtonStyle,
  bodyStyle,
  summaryRowStyle,
  fixTitleStyle,
  findingRuleStyle,
  descStyle,
  diffContainerStyle,
  diffHeaderStyle,
  diffPreStyle,
  verificationNotesStyle,
  footerStyle,
  cancelButtonStyle,
  applyButtonStyle,
} from './diffViewStyles';

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

          {fix.verification?.notes && (
            <div style={verificationNotesStyle}>
              <strong>Verification Sandbox Note:</strong> {fix.verification.notes}
            </div>
          )}
        </div>

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
