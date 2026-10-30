import React, { useState } from 'react';

export interface SecurityFindingItem {
  id: string;
  title: string;
  description: string;
  severity: string;
  confidence?: number | null;
  certainty?: string;
  file?: string;
  line?: number;
  col?: number;
  range?: {
    start_line: number;
    start_col: number;
    end_line: number;
    end_col: number;
  } | null;
  ruleId?: string;
  detectorsFired?: string[];
  toolProvenance?: string[];
  evidence?: string[] | Record<string, any>;
  remediation?: string | null;
  cwe?: string;
  taintPathId?: string | null;
}

interface SecurityPanelProps {
  findings: SecurityFindingItem[];
  onApplyRemediation: () => void;
  onJumpToCode?: (line: number, col: number, endLine?: number, endCol?: number) => void;
  onFocusLine?: (line: number) => void;
  onExplainFinding?: (f: SecurityFindingItem) => void;
  onFixWithAiFinding?: (f: SecurityFindingItem) => void;
  isAnalyzing?: boolean;
}

function getSeverityBadge(severity: string) {
  const sev = (severity || 'medium').toLowerCase();
  if (sev === 'critical') {
    return 'bg-status-error/20 text-status-error border-status-error/40';
  }
  if (sev === 'high') {
    return 'bg-status-error/15 text-status-error border-status-error/30';
  }
  if (sev === 'medium' || sev === 'warning') {
    return 'bg-status-warning/15 text-status-warning border-status-warning/40';
  }
  return 'bg-primary/15 text-primary border-primary/30';
}

export const SecurityPanel: React.FC<SecurityPanelProps> = ({
  findings,
  onApplyRemediation,
  onJumpToCode,
  onFocusLine,
  onExplainFinding,
  onFixWithAiFinding,
  isAnalyzing = false,
}) => {
  const [expandedEvidence, setExpandedEvidence] = useState<Record<string, boolean>>({});

  const toggleEvidence = (id: string) => {
    setExpandedEvidence((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div
      className="panel-view flex-1 flex flex-col min-w-0 border-r border-border-primary overflow-hidden p-3 space-y-2.5"
      id="view-security-tab"
    >
      {/* Header Bar */}
      <div className="flex justify-between items-center shrink-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-status-warning flex items-center gap-1.5 text-[12px]">
            <span className="material-symbols-outlined text-[17px]">shield</span> Security Audit Results
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-surface-container border border-border-subtle text-text-muted">
            {findings.length} finding{findings.length === 1 ? '' : 's'}
          </span>
          {isAnalyzing && (
            <span className="flex items-center gap-1 text-[10px] text-primary animate-pulse font-medium">
              <span className="material-symbols-outlined text-[12px] animate-spin">sync</span>
              Auditing...
            </span>
          )}
        </div>
        {findings.length > 0 && (
          <button
            type="button"
            className="px-2.5 py-1 rounded-md bg-status-error/20 hover:bg-status-error/30 text-status-error text-[11px] font-semibold border border-status-error/30 transition-all active:scale-[0.98]"
            onClick={onApplyRemediation}
            title="Apply automated fix patch to eliminate detected vulnerabilities"
          >
            Apply Remediation
          </button>
        )}
      </div>

      {/* Findings List */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
        {findings.length === 0 ? (
          <div className="bg-surface-elevated p-4 rounded-lg border border-status-success/30 space-y-1.5 shadow-xs text-status-success flex items-center gap-2.5">
            <span className="material-symbols-outlined text-[22px]">check_circle</span>
            <div>
              <div className="text-[12px] font-semibold">Clean Security Profile</div>
              <div className="text-[11px] text-text-muted font-normal">
                No active CVE vulnerabilities, Trojan Source Unicode anomalies, or taint sinks detected.
              </div>
            </div>
          </div>
        ) : (
          findings.map((f) => {
            const isEvidenceOpen = !!expandedEvidence[f.id];
            const evidenceItems = Array.isArray(f.evidence)
              ? f.evidence
              : f.evidence && typeof f.evidence === 'object'
              ? Object.entries(f.evidence).map(([k, v]) => `${k}: ${v}`)
              : [];

            return (
              <div
                key={f.id}
                className="bg-surface-elevated p-3 rounded-lg border border-border-subtle space-y-2 shadow-xs transition-colors hover:border-status-warning/40"
              >
                {/* Title and Badges */}
                <div className="flex justify-between items-start gap-2">
                  <div className="flex items-start gap-2 min-w-0">
                    <span className="material-symbols-outlined text-status-error text-[18px] shrink-0 mt-0.5">
                      gpp_maybe
                    </span>
                    <div className="min-w-0">
                      <div className="text-[12px] font-semibold text-text-primary truncate">
                        {f.title}
                      </div>
                      <div className="text-[10px] text-text-muted font-mono flex items-center gap-2 mt-0.5">
                        {f.file && <span>{f.file}</span>}
                        {f.line !== undefined && (
                          <span>
                            Ln {f.line}, Col {f.col}
                            {f.range && ` (to Ln ${f.range.end_line}, Col ${f.range.end_col})`}
                          </span>
                        )}
                        {f.cwe && (
                          <span className="px-1 py-0.2 rounded bg-surface-deepest border border-border-subtle text-text-secondary">
                            {f.cwe}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {f.certainty && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-surface-deepest text-text-muted font-mono uppercase">
                        {f.certainty}
                      </span>
                    )}
                    {f.confidence !== undefined && f.confidence !== null && (
                      <span className="text-[10px] font-mono text-primary font-bold">
                        {Math.round(f.confidence * 100)}% conf
                      </span>
                    )}
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${getSeverityBadge(
                        f.severity
                      )}`}
                    >
                      {f.severity}
                    </span>
                  </div>
                </div>

                {/* Description */}
                <p className="text-[11px] text-text-secondary leading-relaxed pl-6">
                  {f.description}
                </p>

                {/* Detection Rule / Agent Provenance */}
                <div className="pl-6 flex items-center gap-3 text-[10px] text-text-muted font-mono">
                  {f.ruleId && (
                    <span>
                      Rule: <strong className="text-text-secondary">{f.ruleId}</strong>
                    </span>
                  )}
                  {f.toolProvenance && f.toolProvenance.length > 0 && (
                    <span>
                      Tools: <strong className="text-text-secondary">{f.toolProvenance.join(', ')}</strong>
                    </span>
                  )}
                  {f.taintPathId && (
                    <span className="text-status-warning">
                      Taint flow confirmed
                    </span>
                  )}
                </div>

                {/* Remediation Guidance */}
                {f.remediation && (
                  <div className="ml-6 p-2 rounded bg-status-success/10 border border-status-success/20 text-[11px] text-status-success">
                    <div className="font-semibold text-[10px] uppercase tracking-wider flex items-center gap-1 mb-0.5">
                      <span className="material-symbols-outlined text-[13px]">lightbulb</span>
                      Remediation Guidance
                    </div>
                    <div className="font-mono text-[10px] text-text-primary">{f.remediation}</div>
                  </div>
                )}

                {/* Collapsible Evidence Section */}
                {evidenceItems.length > 0 && (
                  <div className="ml-6 border-t border-border-subtle pt-1.5">
                    <button
                      type="button"
                      className="flex items-center gap-1 text-[10px] text-text-muted hover:text-text-primary font-mono transition-colors"
                      onClick={() => toggleEvidence(f.id)}
                    >
                      <span className="material-symbols-outlined text-[12px]">
                        {isEvidenceOpen ? 'expand_less' : 'expand_more'}
                      </span>
                      <span>{isEvidenceOpen ? 'Hide Evidence' : `View Evidence (${evidenceItems.length} items)`}</span>
                    </button>
                    {isEvidenceOpen && (
                      <div className="mt-1 space-y-1 bg-surface-deepest p-2 rounded border border-border-subtle font-mono text-[10px] text-text-secondary overflow-x-auto">
                        {evidenceItems.map((ev, idx) => (
                          <div key={idx} className="truncate">
                            • {ev}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Navigation and Action Footer */}
                <div className="ml-6 pt-1 flex items-center justify-between flex-wrap gap-2">
                  <button
                    type="button"
                    className="flex items-center gap-1 text-[10px] text-primary hover:underline font-medium"
                    onClick={() => {
                      if (f.line !== undefined && f.col !== undefined) {
                        onJumpToCode?.(
                          f.line,
                          f.col,
                          f.range?.end_line,
                          f.range?.end_col
                        );
                      } else if (f.line) {
                        onFocusLine?.(f.line);
                      }
                    }}
                  >
                    <span className="material-symbols-outlined text-[13px]">my_location</span>
                    <span>Jump to Source Coordinate</span>
                  </button>

                  <div className="flex items-center gap-1.5">
                    {onExplainFinding && (
                      <button
                        type="button"
                        className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container hover:bg-surface-hover text-text-primary text-[10px] font-medium transition-colors border border-border-subtle"
                        onClick={() => onExplainFinding(f)}
                        title="Ask AI to explain this security finding"
                      >
                        <span className="material-symbols-outlined text-[13px] text-accent-ai">auto_awesome</span>
                        <span>Ask AI</span>
                      </button>
                    )}
                    {onFixWithAiFinding && (
                      <button
                        type="button"
                        className="flex items-center gap-1 px-2.5 py-0.5 rounded bg-status-success/20 hover:bg-status-success/30 text-status-success border border-status-success/40 text-[10px] font-semibold transition-colors shadow-xs"
                        onClick={() => onFixWithAiFinding(f)}
                        title="Synthesize AI fix for this security finding"
                      >
                        <span className="material-symbols-outlined text-[13px]">auto_fix_high</span>
                        <span>Fix with AI</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
