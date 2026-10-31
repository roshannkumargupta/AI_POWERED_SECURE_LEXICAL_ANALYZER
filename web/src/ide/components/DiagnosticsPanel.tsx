import React from 'react';

export interface DiagnosticItem {
  id: string;
  code: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  file: string;
  line: number;
  col: number;
  endLine?: number;
  endCol?: number;
  cwe?: string;
  policy?: string;
}

interface DiagnosticsPanelProps {
  diagnostics: DiagnosticItem[];
  onSelectDiagnostic: (d: DiagnosticItem) => void;
  onExplain?: (d: DiagnosticItem) => void;
  onFixWithModel?: (d: DiagnosticItem) => void;
  onFixWithAi?: (d: DiagnosticItem) => void;
  isStale?: boolean;
  onReanalyze?: () => void;
  isAnalyzing?: boolean;
  hasAnalyzed?: boolean;
  errorMessage?: string | null;
}

export const DiagnosticsPanel: React.FC<DiagnosticsPanelProps> = ({
  diagnostics,
  onSelectDiagnostic,
  onExplain,
  onFixWithModel,
  onFixWithAi,
  isStale = false,
  onReanalyze,
  isAnalyzing = false,
  hasAnalyzed = true,
  errorMessage = null,
}) => {
  const errorCount = diagnostics.filter((d) => d.severity === 'error').length;
  const warningCount = diagnostics.filter((d) => d.severity === 'warning').length;

  return (
    <div
      className="panel-view flex-1 flex flex-col min-w-0 border-r border-border-primary overflow-hidden p-3 space-y-2.5"
      id="view-diagnostics"
    >
      <div className="flex justify-between items-center pb-2 border-b border-border-subtle">
        <span className="font-semibold text-text-primary">Compiler &amp; Lexer Diagnostics</span>
        <div className="flex items-center gap-2">
          {isStale && (
            <span
              className="flex items-center gap-1 text-[10px] text-status-warning bg-status-warning/10 px-1.5 py-0.5 rounded border border-status-warning/30"
              title="Editor content changed since last analysis"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-status-warning animate-pulse" />
              <span>Stale</span>
            </span>
          )}
          <span
            className={`text-[11px] font-bold font-mono ${
              errorCount > 0 ? 'text-status-error' : 'text-status-success'
            }`}
          >
            {errorCount} Error{errorCount === 1 ? '' : 's'}, {warningCount} Warning{warningCount === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {isStale && onReanalyze && (
        <div className="flex items-center justify-between px-3 py-1.5 rounded bg-status-warning/10 border border-status-warning/30 text-status-warning text-[11px] shrink-0">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-status-warning animate-pulse" />
            <span>Editor content modified. Diagnostics may be outdated.</span>
          </span>
          <button
            type="button"
            onClick={onReanalyze}
            className="px-2 py-0.5 rounded bg-status-warning text-surface-deepest font-semibold text-[10px] hover:bg-status-warning/90 transition-colors"
          >
            Reanalyze
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-2">
        {isAnalyzing ? (
          <div className="p-4 rounded-lg bg-surface-elevated border border-primary/30 flex gap-3 items-center text-primary">
            <span className="material-symbols-outlined text-[20px] animate-spin">sync</span>
            <div className="text-[12px] font-medium">Checking source code for syntax and compiler diagnostics...</div>
          </div>
        ) : errorMessage ? (
          <div className="p-4 rounded-lg bg-status-error/10 border border-status-error/40 flex gap-3 items-start text-status-error">
            <span className="material-symbols-outlined text-[20px] shrink-0 mt-0.5">error</span>
            <div>
              <div className="text-[12px] font-semibold">Compiler Diagnostic Check Failed</div>
              <div className="text-[11px] text-text-secondary mt-0.5 font-mono">{errorMessage}</div>
            </div>
          </div>
        ) : !hasAnalyzed ? (
          <div className="p-4 rounded-lg bg-surface-elevated border border-border-subtle flex gap-3 items-center text-text-muted">
            <span className="material-symbols-outlined text-[20px] text-text-muted/60">info</span>
            <div className="text-[12px]">Source code not analyzed yet. Press <strong>Analyze</strong> (⌘↵) to run checks.</div>
          </div>
        ) : diagnostics.length === 0 ? (
          <div className="p-3 rounded-lg bg-surface-elevated border border-status-success/30 flex gap-2.5 items-center text-status-success">
            <span className="material-symbols-outlined text-[20px]">check_circle</span>
            <span className="text-[12px] font-medium">No compiler or lexer diagnostics reported.</span>
          </div>
        ) : (
          diagnostics.map((d) => (
            <div
              key={d.id}
              className="p-3 rounded-lg bg-status-error/10 border border-status-error/40 flex gap-2.5 items-start cursor-pointer hover:bg-status-error/15 transition-colors"
              onClick={() => onSelectDiagnostic(d)}
            >
              <span className="material-symbols-outlined text-status-error text-[20px] mt-0.5">cancel</span>
              <div>
                <div className="font-semibold text-status-error text-[12px]">
                  Error [{d.code}]: {d.message}
                </div>
                <div className="text-[11px] text-text-secondary mt-0.5">
                  {d.file}:{d.line}:{d.col}
                </div>
                {(d.policy || d.cwe) && (
                  <div className="text-[10px] font-mono text-text-muted mt-1.5">
                    {[d.policy, d.cwe].filter(Boolean).join(' • ')}
                  </div>
                )}
                <div className="flex items-center gap-2 mt-2 pt-1 border-t border-status-error/20">
                  {onExplain && (
                    <button
                      type="button"
                      className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container hover:bg-surface-hover text-text-primary text-[10px] font-medium transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        onExplain(d);
                      }}
                      title="Ask AI to explain this diagnostic"
                    >
                      <span className="material-symbols-outlined text-[13px] text-accent-ai">auto_awesome</span>
                      <span>Ask AI</span>
                    </button>
                  )}
                  {onFixWithModel && (
                    <button
                      type="button"
                      className="flex items-center gap-1 px-2 py-0.5 rounded bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 text-[10px] font-semibold transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        onFixWithModel(d);
                      }}
                      title="Propose deterministic Model & compiler rule fix"
                    >
                      <span className="material-symbols-outlined text-[13px]">memory</span>
                      <span>Model Fix</span>
                    </button>
                  )}
                  {onFixWithAi && (
                    <button
                      type="button"
                      className="flex items-center gap-1 px-2 py-0.5 rounded bg-status-success/20 hover:bg-status-success/30 text-status-success border border-status-success/40 text-[10px] font-semibold transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        onFixWithAi(d);
                      }}
                      title="Synthesize AI fix for this diagnostic"
                    >
                      <span className="material-symbols-outlined text-[13px]">auto_fix_high</span>
                      <span>Fix with AI</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

