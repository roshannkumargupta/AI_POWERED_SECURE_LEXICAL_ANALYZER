import React from 'react';
import { ShieldCheck, Play, Wand2, Download, Loader2, ChevronDown, Sun, Moon } from 'lucide-react';
import { LanguageInfo } from '../api/client';
import type { ResolvedTheme } from '../theme/theme';

type OpenFile = { id: string; name: string; dirty: boolean };

interface TopBarProps {
  language: string;
  detectedLanguage?: string;
  languages: LanguageInfo[];
  onChangeLanguage: (lang: string) => void;
  isAnalyzing: boolean;
  onAnalyze: () => void;
  onFixAll: () => void;
  onDownload: () => void;
  onNewFile: () => void;
  onOpenFile: () => void;
  onCloseFile: () => void;
  filename?: string;
  safeFixCount?: number;
  reviewFixCount?: number;
  fileState?: 'not analysed' | 'analysing' | 'analysed' | 'stale' | 'error';
  onOpenReviewFixes?: () => void;
  backendAvailable?: boolean;
  files?: OpenFile[];
  activeFileId?: string | null;
  onSwitchFile?: (id: string) => void;
  onCloseFileById?: (id: string) => void;
  themeResolved?: ResolvedTheme;
  onThemeToggle?: () => void;
  agentMode?: 'off' | 'rules' | 'local';
  onChangeAgentMode?: (mode: 'off' | 'rules' | 'local') => void;
  ollamaReachable?: boolean;
  ollamaModel?: string;
}

export const TopBar: React.FC<TopBarProps> = ({
  language,
  detectedLanguage,
  languages,
  onChangeLanguage,
  isAnalyzing,
  onAnalyze,
  onFixAll,
  onDownload,
  onNewFile,
  onOpenFile,
  onCloseFile,
  filename = '',
  safeFixCount = 0,
  reviewFixCount = 0,
  fileState = 'not analysed',
  onOpenReviewFixes,
  backendAvailable = false,
  files = [],
  activeFileId = null,
  onSwitchFile,
  onCloseFileById,
  themeResolved = 'dark',
  onThemeToggle = () => {},
  agentMode = 'off',
  onChangeAgentMode,
  ollamaReachable = false,
  ollamaModel = 'qwen2.5-coder:3b',
}) => {
  const [isFileMenuOpen, setIsFileMenuOpen] = React.useState(false);
  const [isFileListOpen, setIsFileListOpen] = React.useState(false);
  const [isMoreOpen, setIsMoreOpen] = React.useState(false);
  const [themeAnnouncement, setThemeAnnouncement] = React.useState('');
  const nextThemeLabel = themeResolved === 'dark' ? 'light' : 'dark';

  return (
    <header data-qa="topbar" style={containerStyle}>
      {/* Brand Identity */}
      <div style={brandGroupStyle}>
        <div style={logoIconStyle}>
          <ShieldCheck size={18} color="var(--text-primary)" strokeWidth={1.5} />
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
          <span style={brandTitleStyle}>SecureLex</span>
        </div>
      </div>

      {/* Middle Controls */}
      <div style={middleControlsStyle}>
        <div style={{ position: 'relative' }}>
          <button
            style={secondaryButtonStyle}
            onClick={() => setIsFileMenuOpen((open) => !open)}
            aria-label="File menu"
          >
            File
          </button>
          {isFileMenuOpen && (
            <div style={dropdownMenuStyle}>
              <button
                style={dropdownItemStyle}
                onClick={() => {
                  onNewFile();
                  setIsFileMenuOpen(false);
                }}
              >
                New File <small>Ctrl+N</small>
              </button>
              <button
                style={dropdownItemStyle}
                onClick={() => {
                  onOpenFile();
                  setIsFileMenuOpen(false);
                }}
              >
                Open File... <small>Ctrl+O</small>
              </button>
              <button
                style={dropdownItemStyle}
                onClick={() => {
                  onCloseFile();
                  setIsFileMenuOpen(false);
                }}
              >
                Close File <small>Ctrl+W</small>
              </button>
            </div>
          )}
        </div>
        <div style={{ position: 'relative' }}>
          <button
            aria-label="Open file list"
            aria-expanded={isFileListOpen}
            onClick={() => setIsFileListOpen((open) => !open)}
            title={filename || 'No file open'}
            style={{
              color: 'var(--text-primary)',
              fontSize: 12,
              maxWidth: 220,
              height: 26,
              display: 'inline-flex',
              alignItems: 'center',
              padding: '0 9px',
              border: '1px solid var(--border)',
              borderRadius: 8,
              background: 'var(--surface-2)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {filename || 'No file'} <ChevronDown size={12} />
          </button>
          {isFileListOpen && (
            <div style={dropdownMenuStyle} role="menu" aria-label="Open files">
              {files.map((file) => (
                <div key={file.id} style={{ display: 'flex', alignItems: 'center' }}>
                  <button
                    role="menuitem"
                    aria-current={file.id === activeFileId ? 'true' : undefined}
                    style={{ ...dropdownItemStyle, flex: 1 }}
                    onClick={() => {
                      onSwitchFile?.(file.id);
                      setIsFileListOpen(false);
                    }}
                  >
                    {file.name}
                    {file.dirty ? ' •' : ''}
                  </button>
                  <button
                    aria-label={`Close ${file.name}`}
                    onClick={() => onCloseFileById?.(file.id)}
                  >
                    ×
                  </button>
                </div>
              ))}
              <button
                role="menuitem"
                style={dropdownItemStyle}
                onClick={() => {
                  onNewFile();
                  setIsFileListOpen(false);
                }}
              >
                New
              </button>
              <button
                role="menuitem"
                style={dropdownItemStyle}
                onClick={() => {
                  onOpenFile();
                  setIsFileListOpen(false);
                }}
              >
                Open
              </button>
            </div>
          )}
        </div>
        {/* Language Selector */}
        <div style={selectorWrapperStyle}>
          <label htmlFor="lang-select" style={visuallyHiddenStyle}>
            Language
          </label>
          <select
            data-qa="select-language"
            id="lang-select"
            value={language}
            onChange={(e) => onChangeLanguage(e.target.value)}
            style={selectStyle}
            aria-label="Select target programming language"
          >
            <option value="auto">
              {detectedLanguage ? `Auto - ${detectedLanguage}` : 'Auto-detect'}
            </option>
            {languages.map((l) => (
              <option key={l.id} value={l.id}>
                {l.display_name}
              </option>
            ))}
          </select>
          <ChevronDown size={12} color="var(--muted)" style={selectArrowStyle} />
        </div>

        {/* Agent Mode Toggle */}
        <div
          data-qa="agent-toggle-group"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            backgroundColor: 'var(--surface-2)',
            borderRadius: 6,
            padding: '2px',
            border: '1px solid var(--border)',
            gap: 2,
          }}
          role="group"
          aria-label="Agent Mode Toggle"
        >
          <span
            style={{ fontSize: 11, color: 'var(--text-muted)', padding: '0 4px', fontWeight: 600 }}
          >
            Agent:
          </span>
          <button
            data-qa="agent-toggle-off"
            type="button"
            onClick={() => onChangeAgentMode?.('off')}
            style={{
              fontSize: 11,
              padding: '2px 7px',
              borderRadius: 4,
              border: 'none',
              cursor: 'pointer',
              backgroundColor: agentMode === 'off' ? 'var(--panel-2)' : 'transparent',
              color: agentMode === 'off' ? 'var(--text-primary)' : 'var(--text-muted)',
              fontWeight: agentMode === 'off' ? 600 : 400,
            }}
          >
            Off
          </button>
          <button
            data-qa="agent-toggle-rules"
            type="button"
            onClick={() => onChangeAgentMode?.('rules')}
            style={{
              fontSize: 11,
              padding: '2px 7px',
              borderRadius: 4,
              border: 'none',
              cursor: 'pointer',
              backgroundColor: agentMode === 'rules' ? 'var(--panel-2)' : 'transparent',
              color: agentMode === 'rules' ? 'var(--text-accent)' : 'var(--text-muted)',
              fontWeight: agentMode === 'rules' ? 600 : 400,
            }}
          >
            Rules
          </button>
          <button
            data-qa="agent-toggle-local"
            type="button"
            disabled={!ollamaReachable}
            title={ollamaReachable ? `Local AI (${ollamaModel})` : 'Ollama not running'}
            onClick={() => {
              if (ollamaReachable) onChangeAgentMode?.('local');
            }}
            style={{
              fontSize: 11,
              padding: '2px 7px',
              borderRadius: 4,
              border: 'none',
              cursor: ollamaReachable ? 'pointer' : 'not-allowed',
              opacity: ollamaReachable ? 1 : 0.5,
              backgroundColor: agentMode === 'local' ? 'var(--panel-2)' : 'transparent',
              color: agentMode === 'local' ? 'var(--text-success)' : 'var(--text-muted)',
              fontWeight: agentMode === 'local' ? 600 : 400,
            }}
          >
            Local AI
          </button>
        </div>
      </div>

      {/* Right Action Buttons */}
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
    </header>
  );
};

const containerStyle: React.CSSProperties = {
  height: '49px',
  minHeight: '49px',
  maxHeight: '49px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 16px',
  backgroundColor: 'var(--panel)',
  borderBottom: '1px solid var(--border)',
  zIndex: 30,
};

const brandGroupStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
};

const logoIconStyle: React.CSSProperties = {
  width: '28px',
  height: '28px',
  borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--accent)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  boxShadow: 'none',
};

const brandTitleStyle: React.CSSProperties = {
  fontSize: '14px',
  fontWeight: 500,
  letterSpacing: '-0.3px',
  color: 'var(--text)',
};

const middleControlsStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
};

const selectorWrapperStyle: React.CSSProperties = {
  position: 'relative',
  display: 'flex',
  alignItems: 'center',
};

const visuallyHiddenStyle: React.CSSProperties = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  border: 0,
};

const selectStyle: React.CSSProperties = {
  appearance: 'none',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  width: 110,
  height: 26,
  padding: '3px 24px 3px 8px',
  fontSize: '12px',
  fontWeight: 500,
  cursor: 'pointer',
  outline: 'none',
};

const selectArrowStyle: React.CSSProperties = {
  position: 'absolute',
  right: '8px',
  pointerEvents: 'none',
};

const secondaryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '5px 12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text-secondary)',
  fontSize: '12px',
  fontWeight: 500,
  cursor: 'pointer',
};

const dropdownMenuStyle: React.CSSProperties = {
  position: 'absolute',
  top: 'calc(100% + 6px)',
  left: 0,
  width: '280px',
  maxHeight: '360px',
  overflowY: 'auto',
  backgroundColor: 'var(--panel)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  boxShadow: 'var(--shadow-popover)',
  display: 'flex',
  flexDirection: 'column',
  padding: '6px',
  zIndex: 100,
};

const dropdownItemStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'flex-start',
  padding: '6px 8px',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
  textAlign: 'left',
  transition: 'background-color var(--transition-fast)',
};

const rightActionsStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
};

const primaryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '6px 14px',
  backgroundColor: 'var(--accent)',
  color: 'var(--surface-1)',
  borderRadius: 'var(--radius)',
  fontSize: '12px',
  fontWeight: 600,
  cursor: 'pointer',
  boxShadow: '0 2px 6px var(--accent-wash)',
};

const fixAllButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '6px 14px',
  backgroundColor: 'var(--success-wash)',
  border: '1px solid var(--text-success)',
  color: 'var(--success)',
  borderRadius: 'var(--radius)',
  fontSize: '12px',
  fontWeight: 600,
  cursor: 'pointer',
};

const iconButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '6px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  cursor: 'pointer',
};

const kbdStyle: React.CSSProperties = {
  fontSize: '10px',
  opacity: 0.8,
  backgroundColor: 'var(--surface-3)',
  padding: '1px 4px',
  borderRadius: '2px',
  marginLeft: '2px',
};
