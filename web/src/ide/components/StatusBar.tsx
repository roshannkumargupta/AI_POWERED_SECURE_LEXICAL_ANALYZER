import React from 'react';
import type { StageStatus } from './PipelinePanel';

export type StageIndicatorStatus = StageStatus;

interface StatusBarProps {
  fileName: string;
  language: string;
  cursorLine: number;
  cursorCol: number;
  encoding?: string;
  securityCount: number;
  diagnosticCount?: number;
  invalidTokenCount?: number;
  engineStatus?: string;
  isStale?: boolean;
  lexicalStatus?: StageIndicatorStatus;
  syntaxStatus?: StageIndicatorStatus;
  semanticStatus?: StageIndicatorStatus;
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
  onOpenSecurity: () => void;
  onOpenDiagnostics?: () => void;
  onOpenTokens?: () => void;
  onReanalyze?: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  fileName,
  language,
  cursorLine,
  cursorCol,
  encoding = 'UTF-8',
  securityCount,
  diagnosticCount = 0,
  invalidTokenCount = 0,
  engineStatus = 'Ready',
  isStale = false,
  lexicalStatus = 'not_run',
  syntaxStatus = 'not_run',
  semanticStatus = 'not_run',
  onShowToast,
  onOpenSecurity,
  onOpenDiagnostics,
  onOpenTokens,
  onReanalyze,
}) => {
  const renderStageIcon = (status: StageIndicatorStatus, name: string) => {
    switch (status) {
      case 'passed':
        return (
          <span className="material-symbols-outlined text-[13px] text-status-success" title={`${name}: Passed clean`}>
            check_circle
          </span>
        );
      case 'warning':
        return (
          <span className="material-symbols-outlined text-[13px] text-status-warning" title={`${name}: Findings present`}>
            warning
          </span>
        );
      case 'failed':
        return (
          <span className="material-symbols-outlined text-[13px] text-status-error" title={`${name}: Error / Failed`}>
            error
          </span>
        );
      case 'queued':
        return (
          <span className="material-symbols-outlined text-[13px] text-text-muted/80 animate-pulse" title={`${name}: Queued`}>
            schedule
          </span>
        );
      case 'running':
        return (
          <span className="material-symbols-outlined text-[13px] text-primary animate-spin" title={`${name}: Running...`}>
            sync
          </span>
        );
      case 'skipped':
        return (
          <span className="material-symbols-outlined text-[13px] text-text-muted/60" title={`${name}: Skipped`}>
            skip_next
          </span>
        );
      case 'not_run':
      default:
        return (
          <span className="material-symbols-outlined text-[13px] text-text-muted/60" title={`${name}: Not run`}>
            radio_button_unchecked
          </span>
        );
    }
  };

  return (
    <footer
      className="h-[28px] w-full bg-surface-deepest border-t border-border-primary flex items-center justify-between px-3 select-none text-[11px] shrink-0 z-50 transition-colors"
      id="ideStatusBar"
    >
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="flex items-center gap-1 text-primary hover:underline font-mono"
          onClick={() => onShowToast(`Active buffer: ${fileName}`)}
          title={`Active file in editor: ${fileName}`}
        >
          <span className="material-symbols-outlined text-[14px]">terminal</span>
          <span id="statusFile">{fileName}</span>
        </button>
        <span className="font-mono text-text-muted" id="statusLang" title={`Language mode: ${language}`}>
          {language}
        </span>
        <span className="font-mono text-text-secondary" id="statusLineCol" title="Cursor line and column position">
          Ln {cursorLine}, Col {cursorCol}
        </span>
        <span className="font-mono text-text-muted hidden sm:inline" title="File character encoding">
          {encoding}
        </span>

        {isStale && (
          <button
            type="button"
            className="flex items-center gap-1 text-[11px] font-medium text-status-warning bg-status-warning/10 px-2 py-0.5 rounded border border-status-warning/30 hover:bg-status-warning/20 transition-colors cursor-pointer"
            onClick={onReanalyze}
            title="Source changed since last analysis run. Click to reanalyze."
          >
            <span className="w-1.5 h-1.5 rounded-full bg-status-warning animate-pulse" />
            <span>Outdated (Reanalyze)</span>
          </button>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5">
          {/* Lexical Status */}
          <div
            className="flex items-center gap-1 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={onOpenTokens}
            title={`Lexical Analysis: ${lexicalStatus.toUpperCase()}${invalidTokenCount > 0 ? ` (${invalidTokenCount} invalid tokens)` : ''}`}
          >
            {renderStageIcon(lexicalStatus, 'Lexical')}
            <span className="text-text-secondary">
              Lexical{invalidTokenCount > 0 ? ` (${invalidTokenCount})` : ''}
            </span>
          </div>

          {/* Syntax Status */}
          <div
            className="flex items-center gap-1 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={onOpenDiagnostics}
            title={`Syntax Analysis: ${syntaxStatus.toUpperCase()}${diagnosticCount > 0 ? ` (${diagnosticCount} diagnostics)` : ''}`}
          >
            {renderStageIcon(syntaxStatus, 'Syntax')}
            <span className="text-text-secondary">
              Syntax{diagnosticCount > 0 ? ` (${diagnosticCount})` : ''}
            </span>
          </div>

          {/* Semantic Status */}
          <div
            className="flex items-center gap-1 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={onOpenDiagnostics}
            title={`Semantic Analysis: ${semanticStatus.toUpperCase()}`}
          >
            {renderStageIcon(semanticStatus, 'Semantic')}
            <span className="text-text-secondary">Semantic</span>
          </div>

          {/* Security Alert Badge */}
          <div
            className={`flex items-center gap-1 cursor-pointer font-medium hover:opacity-80 transition-opacity ${
              securityCount > 0 ? 'text-status-warning' : 'text-status-success'
            }`}
            id="statusSecurityAlert"
            onClick={onOpenSecurity}
            title={`Security Findings: ${securityCount} active`}
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

        {/* Engine Status */}
        <span
          className="font-mono text-status-success font-medium flex items-center gap-1"
          id="engineStatus"
          title={`Compiler Engine State: ${engineStatus}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
          <span>{engineStatus}</span>
        </span>
      </div>
    </footer>
  );
};


