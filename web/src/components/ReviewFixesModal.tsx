import React, { useState } from 'react';
import { X, Wand2 } from 'lucide-react';
import type { Finding, Fix } from '../api/client';

export interface ReviewFixItem {
  finding: Finding;
  fix: Fix;
  oldSnippet: string;
  newSnippet: string;
}

interface ReviewFixesModalProps {
  isOpen: boolean;
  fixes: ReviewFixItem[];
  onClose: () => void;
  onApplySelected: (selectedFixes: ReviewFixItem[]) => void;
}

export const ReviewFixesModal: React.FC<ReviewFixesModalProps> = ({
  isOpen,
  fixes,
  onClose,
  onApplySelected,
}) => {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  if (!isOpen) return null;

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selectedIds.size === fixes.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(fixes.map((f) => f.fix.id)));
    }
  };

  const handleApply = () => {
    const chosen = fixes.filter((f) => selectedIds.has(f.fix.id));
    onApplySelected(chosen);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="review-fixes-title"
      style={backdropStyle}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div style={modalStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <div>
            <h2 id="review-fixes-title" style={titleStyle}>
              Review Fixes ({fixes.length})
            </h2>
            <p style={subtitleStyle}>
              Review-level security fixes require developer review before applying.
            </p>
          </div>
          <button style={closeBtnStyle} onClick={onClose} aria-label="Close dialog">
            <X size={16} />
          </button>
        </div>

        {/* Toolbar */}
        <div style={toolbarStyle}>
          <button style={textBtnStyle} onClick={selectAll}>
            {selectedIds.size === fixes.length ? 'Deselect all' : 'Select all'}
          </button>
          <span style={{ fontSize: 11, color: 'var(--muted)' }}>
            {selectedIds.size} of {fixes.length} selected
          </span>
        </div>

        {/* Fixes List */}
        <div style={listStyle}>
          {fixes.map((item) => {
            const isChecked = selectedIds.has(item.fix.id);
            return (
              <div
                key={item.fix.id}
                style={{
                  ...cardStyle,
                  borderColor: isChecked ? 'var(--accent)' : 'var(--border)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <input
                    type="checkbox"
                    id={`chk-${item.fix.id}`}
                    aria-label={`Select fix: ${item.fix.title}`}
                    checked={isChecked}
                    onChange={() => toggleSelect(item.fix.id)}
                    style={{ marginTop: 4, cursor: 'pointer' }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-primary)' }}>
                        {item.fix.title}
                      </span>
                      <span className="ui6-meta-pill">{item.finding.rule_id}</span>
                      <span className="ui6-badge insecure">review</span>
                    </div>
                    <p style={{ margin: '4px 0 8px', fontSize: 11, color: 'var(--text-secondary)' }}>
                      {item.fix.description}
                    </p>

                    {/* Diff Preview */}
                    <div style={diffBoxStyle}>
                      {item.oldSnippet && (
                        <div style={{ color: 'var(--text-danger)' }}>- {item.oldSnippet}</div>
                      )}
                      {item.newSnippet && (
                        <div style={{ color: 'var(--text-success)' }}>+ {item.newSnippet}</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div style={footerStyle}>
          <button style={secondaryBtnStyle} onClick={onClose}>
            Cancel
          </button>
          <button
            style={{
              ...primaryBtnStyle,
              opacity: selectedIds.size === 0 ? 0.5 : 1,
              cursor: selectedIds.size === 0 ? 'not-allowed' : 'pointer',
            }}
            disabled={selectedIds.size === 0}
            onClick={handleApply}
          >
            <Wand2 size={13} />
            <span>Apply Selected ({selectedIds.size})</span>
          </button>
        </div>
      </div>
    </div>
  );
};

const backdropStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  backgroundColor: 'var(--scrim-strong)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: 16,
};

const modalStyle: React.CSSProperties = {
  width: '100%',
  maxWidth: '680px',
  maxHeight: '85vh',
  backgroundColor: 'var(--surface-1)',
  border: '1px solid var(--border)',
  borderRadius: 8,
  boxShadow: 'var(--shadow-modal)',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
};

const headerStyle: React.CSSProperties = {
  padding: '14px 18px',
  borderBottom: '1px solid var(--border)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: 15,
  fontWeight: 600,
  color: 'var(--text-primary)',
};

const subtitleStyle: React.CSSProperties = {
  margin: '4px 0 0',
  fontSize: 11,
  color: 'var(--muted)',
};

const closeBtnStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: 'var(--muted)',
  cursor: 'pointer',
  padding: 4,
};

const toolbarStyle: React.CSSProperties = {
  padding: '8px 18px',
  backgroundColor: 'var(--surface-2)',
  borderBottom: '1px solid var(--border)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};

const textBtnStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: 'var(--accent)',
  fontSize: 11,
  cursor: 'pointer',
  padding: 0,
};

const listStyle: React.CSSProperties = {
  padding: 18,
  overflowY: 'auto',
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
};

const cardStyle: React.CSSProperties = {
  padding: 12,
  backgroundColor: 'var(--surface-2)',
  border: '1px solid var(--border)',
  borderRadius: 6,
  transition: 'border-color 0.15s ease',
};

const diffBoxStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: 11,
  lineHeight: 1.5,
  padding: '6px 10px',
  backgroundColor: 'var(--surface-1)',
  borderRadius: 4,
  border: '1px solid var(--border)',
  whiteSpace: 'pre-wrap',
  overflowWrap: 'anywhere',
};

const footerStyle: React.CSSProperties = {
  padding: '12px 18px',
  borderTop: '1px solid var(--border)',
  display: 'flex',
  justifyContent: 'flex-end',
  gap: 8,
  backgroundColor: 'var(--surface-1)',
};

const secondaryBtnStyle: React.CSSProperties = {
  padding: '6px 12px',
  borderRadius: 4,
  border: '1px solid var(--border)',
  background: 'var(--surface-2)',
  color: 'var(--text-primary)',
  fontSize: 12,
  cursor: 'pointer',
};

const primaryBtnStyle: React.CSSProperties = {
  padding: '6px 14px',
  borderRadius: 4,
  border: '1px solid var(--accent)',
  background: 'var(--accent)',
  color: 'var(--surface-1)',
  fontSize: 12,
  fontWeight: 500,
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
};
