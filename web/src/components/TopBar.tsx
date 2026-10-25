import React from 'react';
import { ShieldCheck, ChevronDown } from 'lucide-react';
import { LanguageInfo } from '../api/client';
import type { ResolvedTheme } from '../theme/theme';
import {
  containerStyle,
  brandGroupStyle,
  logoIconStyle,
  brandTitleStyle,
  middleControlsStyle,
  selectorWrapperStyle,
  visuallyHiddenStyle,
  selectStyle,
  selectArrowStyle,
} from './topBarStyles';
import { TopBarActions } from './TopBarActions';
import { TopBarFileMenu, OpenFile } from './TopBarFileMenu';

export type { OpenFile };

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
  agentMode?: 'off' | 'rules';
  onChangeAgentMode?: (mode: 'off' | 'rules') => void;
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
}) => {
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
        <TopBarFileMenu
          onNewFile={onNewFile}
          onOpenFile={onOpenFile}
          onCloseFile={onCloseFile}
          filename={filename}
          files={files}
          activeFileId={activeFileId}
          onSwitchFile={onSwitchFile}
          onCloseFileById={onCloseFileById}
        />

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
        </div>
      </div>

      {/* Right Action Buttons */}
      <TopBarActions
        isAnalyzing={isAnalyzing}
        fileState={fileState}
        onAnalyze={onAnalyze}
        safeFixCount={safeFixCount}
        reviewFixCount={reviewFixCount}
        onFixAll={onFixAll}
        onOpenReviewFixes={onOpenReviewFixes}
        themeResolved={themeResolved}
        onThemeToggle={onThemeToggle}
        backendAvailable={backendAvailable}
        onDownload={onDownload}
      />
    </header>
  );
};
