import React from 'react';

export interface DiagnosticItem {
  id: string;
  code: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
  file: string;
  line: number;
  col: number;
  cwe?: string;
  policy?: string;
}

interface DiagnosticsPanelProps {
  diagnostics: DiagnosticItem[];
  onSelectDiagnostic: (d: DiagnosticItem) => void;
  onExplain?: (d: DiagnosticItem) => void;
  onFixWithAi?: (d: DiagnosticItem) => void;
}

export const DiagnosticsPanel: React.FC<DiagnosticsPanelProps> = ({
  diagnostics,
  onSelectDiagnostic,
  onExplain,
  onFixWithAi,
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
        <span
          className={`text-[11px] font-bold font-mono ${
            errorCount > 0 ? 'text-status-error' : 'text-status-success'
          }`}
        >
          {errorCount} Error{errorCount === 1 ? '' : 's'}, {warningCount} Warning{warningCount === 1 ? '' : 's'}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2">
        {diagnostics.length === 0 ? (
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

