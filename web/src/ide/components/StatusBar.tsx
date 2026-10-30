import React from 'react';

interface StatusBarProps {
  fileName: string;
  language: string;
  cursorLine: number;
  cursorCol: number;
  encoding?: string;
  securityCount: number;
  engineStatus?: string;
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
  onOpenSecurity: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  fileName,
  language,
  cursorLine,
  cursorCol,
  encoding = 'UTF-8',
  securityCount,
  engineStatus = 'Ready',
  onShowToast,
  onOpenSecurity,
}) => {
  return (
    <footer
      className="h-[28px] w-full bg-surface-deepest border-t border-border-primary flex items-center justify-between px-3 select-none text-[11px] shrink-0 z-50 transition-colors"
    >
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="flex items-center gap-1 text-primary hover:underline font-mono"
          onClick={() => onShowToast(`Active buffer: ${fileName}`)}
        >
          <span className="material-symbols-outlined text-[14px]">terminal</span>
          <span id="statusFile">{fileName}</span>
        </button>
        <span className="font-mono text-text-muted" id="statusLang">
          {language}
        </span>
        <span className="font-mono text-text-secondary" id="statusLineCol">
          Ln {cursorLine}, Col {cursorCol}
        </span>
        <span className="font-mono text-text-muted">{encoding}</span>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5">
          <div
            className="flex items-center gap-1 text-status-success cursor-pointer"
            onClick={() => onShowToast('Lexical Scanner: Clean')}
          >
            <span className="material-symbols-outlined text-[14px]">check_circle</span>
            <span className="text-text-secondary">Lexical</span>
          </div>
          <div
            className="flex items-center gap-1 text-status-success cursor-pointer"
            onClick={() => onShowToast('Syntax Parser: Clean')}
          >
            <span className="material-symbols-outlined text-[14px]">check_circle</span>
            <span className="text-text-secondary">Syntax</span>
          </div>
          <div
            className="flex items-center gap-1 text-status-success cursor-pointer"
            onClick={() => onShowToast('Semantic Typing: Passed')}
          >
            <span className="material-symbols-outlined text-[14px]">check_circle</span>
            <span className="text-text-secondary">Semantic</span>
          </div>
          <div
            className={`flex items-center gap-1 cursor-pointer font-medium ${
              securityCount > 0 ? 'text-status-warning' : 'text-status-success'
            }`}
            id="statusSecurityAlert"
            onClick={onOpenSecurity}
          >
            <span className="material-symbols-outlined text-[14px]">
              {securityCount > 0 ? 'warning' : 'check_circle'}
            </span>
            <span className="text-text-secondary" id="statusSecurityText">
              Security ({securityCount})
            </span>
          </div>
        </div>
        <div className="h-3 w-[1px] bg-border-primary" />
        <span
          className="font-mono text-status-success font-medium flex items-center gap-1"
          id="engineStatus"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
          <span>{engineStatus}</span>
        </span>
      </div>
    </footer>
  );
};

