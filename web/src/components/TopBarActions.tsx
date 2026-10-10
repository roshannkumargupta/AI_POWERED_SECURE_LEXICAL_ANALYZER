import React from 'react';
import { Play, Wand2, Download, Loader2, Sun, Moon } from 'lucide-react';
import type { ResolvedTheme } from '../theme/theme';
import {
  rightActionsStyle,
  primaryButtonStyle,
  fixAllButtonStyle,
  iconButtonStyle,
  visuallyHiddenStyle,
  dropdownMenuStyle,
  dropdownItemStyle,
  kbdStyle,
} from './topBarStyles';

interface TopBarActionsProps {
  isAnalyzing: boolean;
  fileState: 'not analysed' | 'analysing' | 'analysed' | 'stale' | 'error';
  onAnalyze: () => void;
  safeFixCount: number;
  reviewFixCount: number;
  onFixAll: () => void;
  onOpenReviewFixes?: () => void;
  themeResolved: ResolvedTheme;
  onThemeToggle: () => void;
  backendAvailable: boolean;
  onDownload: () => void;
}

export const TopBarActions: React.FC<TopBarActionsProps> = ({
  isAnalyzing,
  fileState,
  onAnalyze,
  safeFixCount,
  reviewFixCount,
  onFixAll,
  onOpenReviewFixes,
  themeResolved,
  onThemeToggle,
  backendAvailable,
  onDownload,
}) => {
  const [isMoreOpen, setIsMoreOpen] = React.useState(false);
  const [themeAnnouncement, setThemeAnnouncement] = React.useState('');
  const nextThemeLabel = themeResolved === 'dark' ? 'light' : 'dark';

  return (
    <div style={rightActionsStyle}>
      {/* Analyze Button */}
      <button
        data-qa="btn-analyze"
        style={{
          ...primaryButtonStyle,
          backgroundColor: fileState === 'stale' ? 'var(--surface-2)' : 'var(--panel-2)',
          color: fileState === 'stale' ? 'var(--accent)' : 'var(--text-secondary)',
          border: fileState === 'stale' ? '1px solid var(--accent)' : '1px solid var(--border)',
          boxShadow: 'none',
        }}
        onClick={onAnalyze}
        disabled={isAnalyzing}
        title={
          fileState === 'not analysed'
            ? 'Not analysed - press Analyze (Ctrl+Enter)'
            : fileState === 'analysing'
              ? 'Analysing...'
              : fileState === 'stale'
                ? 'Edited since last analysis - press Analyze (Ctrl+Enter)'
                : 'Analyze Code (Ctrl+Enter)'
        }
        aria-label="Analyze Code"
      >
        {isAnalyzing ? (
          <Loader2 size={14} className="animate-spin" />
        ) : (
          <Play size={14} fill="currentColor" />
        )}
        <span>{isAnalyzing ? 'Analysing...' : 'Analyze'}</span>
        <kbd style={kbdStyle}>Ctrl+↵</kbd>
      </button>

      {/* Fix All / Review Fixes Button */}
      {safeFixCount > 0 ? (
        <button
          data-qa="btn-fixall"
          style={{
            ...fixAllButtonStyle,
            backgroundColor: 'var(--accent)',
            borderColor: 'var(--accent)',
            color: 'var(--surface-1)',
            cursor: 'pointer',
          }}
          onClick={onFixAll}
          disabled={isAnalyzing || fileState === 'stale'}
          title={fileState === 'stale' ? 'Analyse again first' : 'Apply all safe verified fixes'}
          aria-label="Fix All Safe Issues"
        >
          <Wand2 size={14} />
          <span>Fix all ({safeFixCount})</span>
        </button>
      ) : reviewFixCount > 0 ? (
        <button
          data-qa="btn-reviewfixes"
          style={{
            ...fixAllButtonStyle,
            backgroundColor: 'transparent',
            borderColor: 'var(--border)',
            color: 'var(--text-primary)',
            cursor: 'pointer',
          }}
          onClick={onOpenReviewFixes}
          disabled={isAnalyzing || fileState === 'stale'}
          title={fileState === 'stale' ? 'Analyse again first' : 'Open Review fixes panel'}
          aria-label="Review Fixes"
        >
          <Wand2 size={14} />
          <span>Review fixes ({reviewFixCount})</span>
        </button>
      ) : (
        <button
          data-qa="btn-fixall"
          style={{
            ...fixAllButtonStyle,
            backgroundColor: 'transparent',
            borderColor: 'var(--border)',
            color: 'var(--muted)',
            cursor: 'not-allowed',
          }}
          disabled={true}
          title="No verified fixes available"
          aria-label="Fix All Safe Issues"
        >
          <Wand2 size={14} />
          <span>Fix all (0)</span>
        </button>
      )}

      <div style={{ position: 'relative' }}>
        <button
          type="button"
          style={{ ...iconButtonStyle, width: 32, height: 32 }}
          aria-label={`Switch to ${nextThemeLabel} theme`}
          title={`Switch to ${nextThemeLabel} theme`}
          onClick={() => {
            onThemeToggle();
            setThemeAnnouncement(
              `${nextThemeLabel[0].toUpperCase()}${nextThemeLabel.slice(1)} theme`
            );
          }}
        >
          {themeResolved === 'dark' ? (
            <Sun size={16} aria-hidden="true" />
          ) : (
            <Moon size={16} aria-hidden="true" />
          )}
        </button>
        <span aria-live="polite" aria-atomic="true" style={visuallyHiddenStyle}>
          {themeAnnouncement}
        </span>
      </div>
      <div style={{ position: 'relative' }}>
        <button
          style={iconButtonStyle}
          aria-label="More actions"
          title="More actions"
          onClick={() => setIsMoreOpen((open) => !open)}
        >
          ···
        </button>
        {isMoreOpen && (
          <div style={{ ...dropdownMenuStyle, left: 'auto', right: 0, width: 220 }}>
            <button
              style={dropdownItemStyle}
              onClick={() => {
                onDownload();
                setIsMoreOpen(false);
              }}
            >
              <span>
                <Download size={13} /> Download <small>Ctrl+S</small>
              </span>
            </button>
            <button
              style={dropdownItemStyle}
              onClick={() => {
                window.dispatchEvent(new KeyboardEvent('keydown', { key: '?', bubbles: true }));
                setIsMoreOpen(false);
              }}
            >
              Keyboard shortcuts <small>?</small>
            </button>
            <div style={{ padding: '7px 8px', color: 'var(--muted)', fontSize: 11 }}>
              Backend: {backendAvailable ? 'Connected' : 'Offline'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
