import React from 'react';
import { X, Keyboard } from 'lucide-react';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ShortcutItem {
  keys: string[];
  description: string;
  category: 'Editor' | 'Analysis' | 'Navigation';
}

const SHORTCUTS: ShortcutItem[] = [
  { keys: ['Ctrl', 'Enter'], description: 'Run security analysis', category: 'Analysis' },
  { keys: ['Ctrl', 'S'], description: 'Save current file', category: 'Editor' },
  { keys: ['Ctrl', 'B'], description: 'Toggle Explorer sidebar', category: 'Navigation' },
  { keys: ['Ctrl', 'N'], description: 'Create new buffer file', category: 'Editor' },
  { keys: ['Ctrl', 'O'], description: 'Open local file', category: 'Editor' },
  { keys: ['Ctrl', 'P'], description: 'Open command palette', category: 'Navigation' },
  { keys: ['F1'], description: 'Open command palette (VS Code style)', category: 'Navigation' },
  { keys: ['Ctrl', 'Shift', 'T'], description: 'Toggle Token Map decorations', category: 'Editor' },
  { keys: ['F8'], description: 'Go to next problem', category: 'Navigation' },
  { keys: ['Shift', 'F8'], description: 'Go to previous problem', category: 'Navigation' },
  { keys: ['?'], description: 'Open keyboard shortcuts cheat-sheet', category: 'Navigation' },
  { keys: ['Escape'], description: 'Close active modal or flyout', category: 'Navigation' },
];

export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({ isOpen, onClose }) => {
  React.useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      data-qa="shortcuts-modal-backdrop"
      style={backdropStyle}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
    >
      <div
        data-qa="shortcuts-modal"
        style={modalStyle}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={headerStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Keyboard size={18} color="var(--accent)" />
            <h2 id="shortcuts-title" style={titleStyle}>
              Keyboard Shortcuts Cheat-sheet
            </h2>
          </div>
          <button
            data-qa="close-shortcuts-btn"
            style={closeBtnStyle}
            onClick={onClose}
            aria-label="Close shortcuts modal"
          >
            <X size={16} />
          </button>
        </div>

        <div style={bodyStyle}>
          <table style={tableStyle}>
            <thead>
              <tr style={thRowStyle}>
                <th style={{ ...thStyle, width: '130px' }}>Category</th>
                <th style={thStyle}>Action</th>
                <th style={{ ...thStyle, width: '180px', textAlign: 'right' }}>Shortcut</th>
              </tr>
            </thead>
            <tbody>
              {SHORTCUTS.map((item, idx) => (
                <tr key={idx} style={trStyle}>
                  <td style={tdCategoryStyle}>
                    <span style={categoryBadgeStyle}>{item.category}</span>
                  </td>
                  <td style={tdStyle}>{item.description}</td>
                  <td style={{ ...tdStyle, textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '4px', justifyContent: 'flex-end' }}>
                      {item.keys.map((k, ki) => (
                        <kbd key={ki} style={kbdStyle}>
                          {k}
                        </kbd>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={footerStyle}>
          <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
            Press <kbd style={kbdStyle}>?</kbd> anytime to open this cheat-sheet.
          </span>
        </div>
      </div>
    </div>
  );
};

const backdropStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'var(--scrim)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 10000,
  backdropFilter: 'blur(3px)',
};

const modalStyle: React.CSSProperties = {
  backgroundColor: 'var(--panel)',
  border: '1px solid var(--border)',
  borderRadius: '8px',
  width: '560px',
  maxWidth: '90vw',
  maxHeight: '85vh',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: 'var(--shadow-modal)',
  overflow: 'hidden',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '12px 16px',
  borderBottom: '1px solid var(--border)',
  backgroundColor: 'var(--panel-2)',
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '14px',
  fontWeight: 600,
  color: 'var(--text-primary)',
};

const closeBtnStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  padding: '4px',
  borderRadius: '4px',
  display: 'flex',
  alignItems: 'center',
};

const bodyStyle: React.CSSProperties = {
  padding: '12px 16px',
  overflowY: 'auto',
  maxHeight: '60vh',
};

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
};

const thRowStyle: React.CSSProperties = {
  borderBottom: '1px solid var(--border)',
};

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '8px',
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
};

const trStyle: React.CSSProperties = {
  borderBottom: '1px solid var(--border)',
};

const tdStyle: React.CSSProperties = {
  padding: '8px',
  fontSize: '12px',
  color: 'var(--text-primary)',
};

const tdCategoryStyle: React.CSSProperties = {
  padding: '8px',
  fontSize: '11px',
};

const categoryBadgeStyle: React.CSSProperties = {
  padding: '2px 6px',
  borderRadius: '4px',
  backgroundColor: 'var(--surface-2)',
  color: 'var(--text-secondary)',
  fontSize: '10px',
  fontWeight: 600,
};

const kbdStyle: React.CSSProperties = {
  padding: '2px 6px',
  fontSize: '10px',
  fontWeight: 600,
  borderRadius: '4px',
  backgroundColor: 'var(--panel-2)',
  color: 'var(--text-primary)',
  border: '1px solid var(--border)',
  fontFamily: 'inherit',
};

const footerStyle: React.CSSProperties = {
  padding: '10px 16px',
  borderTop: '1px solid var(--border)',
  backgroundColor: 'var(--panel-2)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};
