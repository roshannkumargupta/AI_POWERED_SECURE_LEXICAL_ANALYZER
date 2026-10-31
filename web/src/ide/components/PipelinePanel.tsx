import React from 'react';

export type StageStatus =
  | 'not_run'
  | 'queued'
  | 'running'
  | 'passed'
  | 'failed'
  | 'warning'
  | 'skipped';

export interface StageTraceStep {
  action: string;
  reason: string;
  observation: string;
  ms: number;
  accepted: boolean;
  rejectionReason?: string;
}

export interface PipelineStageInfo {
  id: string; // 'lexer' | 'parser' | 'semantic' | 'triage' | 'fix' | 'verify' | 'explain'
  name: string;
  agentName: string;
  status: StageStatus;
  elapsedMs: number;
  outputSummary: string;
  errorReason?: string | null;
  skipReason?: string | null;
  prerequisites: string[];
  steps: StageTraceStep[];
}

interface PipelinePanelProps {
  stages: PipelineStageInfo[];
  selectedStageId: string | null;
  onSelectStage: (id: string) => void;
  onRerunStage: (id: string) => void;
  onRunAllAgents: () => void;
  isRunningAll: boolean;
  onAskAiStage?: (stage: PipelineStageInfo) => void;
  isStale?: boolean;
}

function getStatusBadge(status: StageStatus) {
  switch (status) {
    case 'passed':
      return {
        icon: 'check_circle',
        color: 'text-status-success',
        bg: 'bg-status-success/15',
        border: 'border-status-success/30',
        label: 'Passed',
      };
    case 'warning':
      return {
        icon: 'warning',
        color: 'text-status-warning',
        bg: 'bg-status-warning/15',
        border: 'border-status-warning/30',
        label: 'Warning',
      };
    case 'failed':
      return {
        icon: 'cancel',
        color: 'text-status-error',
        bg: 'bg-status-error/15',
        border: 'border-status-error/30',
        label: 'Failed',
      };
    case 'running':
      return {
        icon: 'sync',
        color: 'text-primary',
        bg: 'bg-primary/15',
        border: 'border-primary/40',
        label: 'Running',
      };
    case 'queued':
      return {
        icon: 'hourglass_empty',
        color: 'text-text-muted',
        bg: 'bg-surface-container',
        border: 'border-border-subtle',
        label: 'Queued',
      };
    case 'skipped':
      return {
        icon: 'redo',
        color: 'text-text-muted',
        bg: 'bg-surface-deepest',
        border: 'border-border-subtle',
        label: 'Skipped',
      };
    case 'not_run':
    default:
      return {
        icon: 'radio_button_unchecked',
        color: 'text-text-muted',
        bg: 'bg-surface-container',
        border: 'border-border-subtle',
        label: 'Not Run',
      };
  }
}

export const PipelinePanel: React.FC<PipelinePanelProps> = ({
  stages,
  selectedStageId,
  onSelectStage,
  onRerunStage,
  onRunAllAgents,
  isRunningAll,
  onAskAiStage,
  isStale = false,
}) => {
  const selectedStage = stages.find((s) => s.id === selectedStageId) || stages[0];

  const totalTime = stages.reduce((acc, s) => acc + (s.elapsedMs || 0), 0);
  const passedCount = stages.filter((s) => s.status === 'passed' || s.status === 'warning').length;

  return (
    <div
      className="panel-view flex-1 flex flex-col min-w-0 border-r border-border-primary overflow-hidden p-3 space-y-3"
      id="view-pipeline-tab"
    >
      {/* Top Bar with Run Controls */}
      <div className="flex justify-between items-center shrink-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-text-primary text-[12px] flex items-center gap-1.5">
            <span className="material-symbols-outlined text-primary text-[16px]">account_tree</span>
            7-Stage Compiler Agent Pipeline
          </span>
          <span className="text-[10px] text-text-muted font-mono bg-surface-container px-2 py-0.5 rounded border border-border-subtle">
            {passedCount}/{stages.length} Completed ({totalTime.toFixed(1)} ms)
          </span>
          {isStale && (
            <span
              className="flex items-center gap-1 text-[10px] text-status-warning bg-status-warning/10 px-1.5 py-0.5 rounded border border-status-warning/30"
              title="Editor content changed since last analysis"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-status-warning animate-pulse" />
              <span>Stale</span>
            </span>
          )}
        </div>
        <button
          type="button"
          className="flex items-center gap-1.5 px-3 py-1 bg-primary hover:bg-primary-hover text-white rounded-md text-[11px] font-semibold shadow-xs disabled:opacity-50 transition-all active:scale-[0.98]"
          onClick={onRunAllAgents}
          disabled={isRunningAll}
          id="btnRunAllInPanel"
        >
          <span
            className={`material-symbols-outlined text-[14px] ${isRunningAll ? 'animate-spin' : ''}`}
          >
            play_arrow
          </span>
          <span>{isRunningAll ? 'Running Agents...' : 'Run All Agents'}</span>
        </button>
      </div>

      {isStale && (
        <div className="flex items-center justify-between px-3 py-1.5 rounded bg-status-warning/10 border border-status-warning/30 text-status-warning text-[11px] shrink-0">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-status-warning animate-pulse" />
            <span>Editor content modified since last pipeline execution.</span>
          </span>
          <button
            type="button"
            onClick={onRunAllAgents}
            disabled={isRunningAll}
            className="px-2 py-0.5 rounded bg-status-warning text-surface-deepest font-semibold text-[10px] hover:bg-status-warning/90 transition-colors disabled:opacity-50"
          >
            Rerun Pipeline
          </button>
        </div>
      )}

      {/* 7-Stage Horizontal Pipeline Graph */}
      <div className="grid grid-cols-7 gap-2 shrink-0">
        {stages.map((stage, idx) => {
          const badge = getStatusBadge(stage.status);
          const isSelected = stage.id === selectedStage?.id;

          return (
            <div
              key={stage.id}
              onClick={() => onSelectStage(stage.id)}
              className={`p-2 rounded-lg border text-left cursor-pointer transition-all shadow-xs flex flex-col justify-between ${
                isSelected
                  ? 'border-primary bg-surface-elevated ring-1 ring-primary/40'
                  : 'bg-surface-elevated/70 hover:bg-surface-elevated border-border-subtle'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-text-muted font-mono">#{idx + 1}</span>
                  <span
                    className={`material-symbols-outlined text-[15px] ${badge.color} ${
                      stage.status === 'running' ? 'animate-spin' : ''
                    }`}
                  >
                    {badge.icon}
                  </span>
                </div>
                <div className="font-semibold text-[11px] text-text-primary truncate mt-1">
                  {stage.name}
                </div>
                <div className="text-[10px] text-text-muted font-mono truncate">{stage.agentName}</div>
              </div>

              <div className="mt-2 pt-1 border-t border-border-subtle flex items-center justify-between">
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${badge.bg} ${badge.color}`}
                >
                  {badge.label}
                </span>
                <span className="text-[10px] text-text-muted font-mono">
                  {stage.status !== 'not_run' && stage.status !== 'queued'
                    ? `${stage.elapsedMs.toFixed(1)}ms`
                    : '--'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Stage Detail Inspector */}
      {selectedStage && (
        <div className="flex-1 min-h-0 bg-surface-elevated rounded-lg border border-border-primary p-3 flex flex-col overflow-hidden shadow-xs">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border-subtle pb-2 shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-[12px] font-semibold text-text-primary">
                Stage Detail: {selectedStage.name} ({selectedStage.agentName})
              </span>
              <span
                className={`text-[11px] px-2 py-0.5 rounded font-mono font-bold ${
                  getStatusBadge(selectedStage.status).bg
                } ${getStatusBadge(selectedStage.status).color}`}
              >
                {getStatusBadge(selectedStage.status).label}
              </span>
              <span className="text-[11px] text-text-muted font-mono">
                Duration: {selectedStage.elapsedMs.toFixed(2)} ms
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              {onAskAiStage && (
                <button
                  type="button"
                  className="flex items-center gap-1 px-2.5 py-1 rounded bg-primary/15 hover:bg-primary/25 text-primary border border-primary/40 text-[11px] font-semibold transition-colors"
                  onClick={() => onAskAiStage(selectedStage)}
                  title={`Ask AI to explain and suggest fixes for ${selectedStage.name} stage`}
                >
                  <span className="material-symbols-outlined text-[13px]">auto_awesome</span>
                  <span>Ask AI</span>
                </button>
              )}
              <button
                type="button"
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-surface-container hover:bg-surface-hover text-text-primary border border-border-primary text-[10px] font-medium transition-colors"
                onClick={() => onRerunStage(selectedStage.id)}
                disabled={isRunningAll}
                title={`Rerun ${selectedStage.name} stage`}
              >
                <span className="material-symbols-outlined text-[13px]">refresh</span>
                <span>Rerun Stage</span>
              </button>
            </div>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto pt-2 space-y-2.5">
            {/* Warning / Error Callout with Ask AI button */}
            {(selectedStage.status === 'warning' || selectedStage.status === 'failed') && onAskAiStage && (
              <div className="bg-status-warning/10 border border-status-warning/40 p-2.5 rounded-md flex items-center justify-between gap-3 text-[11px]">
                <div className="flex items-start gap-2">
                  <span className="material-symbols-outlined text-status-warning text-[18px] mt-0.5">warning</span>
                  <div>
                    <div className="font-semibold text-text-primary">
                      {selectedStage.name} reported a {selectedStage.status}
                    </div>
                    <div className="text-text-secondary text-[10px] mt-0.5">
                      {selectedStage.errorReason || selectedStage.outputSummary || 'Stage requires attention. AI can explain the root cause and propose a verified fix.'}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  className="flex items-center gap-1.5 px-3 py-1 bg-primary hover:bg-primary-hover text-white rounded text-[11px] font-semibold transition-all shrink-0 shadow-xs"
                  onClick={() => onAskAiStage(selectedStage)}
                  title="Ask AI to explain and suggest fixes"
                >
                  <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
                  <span>Ask AI to Fix</span>
                </button>
              </div>
            )}

            {/* Output Summary */}
            <div>
              <div className="text-[10px] font-semibold uppercase text-text-muted tracking-wider">
                Output Summary
              </div>
              <div className="text-[11px] text-text-primary mt-0.5 font-mono bg-surface-deepest p-2 rounded border border-border-subtle">
                {selectedStage.outputSummary || 'No output recorded yet.'}
              </div>
            </div>

            {/* Skip Reason (if skipped) */}
            {selectedStage.status === 'skipped' && selectedStage.skipReason && (
              <div className="bg-surface-container p-2.5 rounded border border-border-subtle text-[11px] text-text-secondary flex items-start gap-2">
                <span className="material-symbols-outlined text-text-muted text-[16px] mt-0.5">
                  info
                </span>
                <div>
                  <div className="font-semibold text-text-primary">Stage Skipped</div>
                  <div>{selectedStage.skipReason}</div>
                </div>
              </div>
            )}

            {/* Error Reason (if failed) */}
            {selectedStage.status === 'failed' && selectedStage.errorReason && (
              <div className="bg-status-error/15 p-2.5 rounded border border-status-error/30 text-[11px] text-status-error flex items-start gap-2">
                <span className="material-symbols-outlined text-[16px] mt-0.5">error</span>
                <div>
                  <div className="font-semibold">Execution Failure</div>
                  <div>{selectedStage.errorReason}</div>
                </div>
              </div>
            )}

            {/* Prerequisites */}
            <div className="flex items-center gap-2 text-[10px] text-text-muted font-mono">
              <span>Prerequisites:</span>
              {selectedStage.prerequisites.length === 0 ? (
                <span className="text-text-secondary">None (Entry point)</span>
              ) : (
                selectedStage.prerequisites.map((p) => (
                  <span
                    key={p}
                    className="px-1.5 py-0.5 rounded bg-surface-deepest border border-border-subtle text-text-secondary"
                  >
                    {p}
                  </span>
                ))
              )}
            </div>

            {/* Recorded Steps Audit Trail */}
            <div>
              <div className="text-[10px] font-semibold uppercase text-text-muted tracking-wider mb-1">
                Recorded Audit Steps ({selectedStage.steps.length})
              </div>
              {selectedStage.steps.length === 0 ? (
                <div className="text-[11px] text-text-muted font-sans py-2">
                  No execution steps recorded for this stage.
                </div>
              ) : (
                <div className="space-y-1.5 font-mono text-[10px]">
                  {selectedStage.steps.map((st, idx) => (
                    <div
                      key={idx}
                      className="bg-surface-deepest p-2 rounded border border-border-subtle space-y-0.5"
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-primary">
                          Step #{idx + 1}: {st.action}
                        </span>
                        <span className="text-text-muted">{st.ms.toFixed(2)} ms</span>
                      </div>
                      <div className="text-text-secondary">
                        <strong className="text-text-muted">Reason:</strong> {st.reason}
                      </div>
                      <div className="text-text-primary">
                        <strong className="text-text-muted">Observation:</strong> {st.observation}
                      </div>
                      {st.rejectionReason && (
                        <div className="text-status-error">
                          <strong className="text-text-muted">Rejection:</strong> {st.rejectionReason}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
