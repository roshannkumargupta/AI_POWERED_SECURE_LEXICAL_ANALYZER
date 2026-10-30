import React from 'react';
import { TokenTable } from './TokenTable';
import { TokenInspector, type TokenItem } from './TokenInspector';
import { DiagnosticsPanel, type DiagnosticItem } from './DiagnosticsPanel';
import { PipelinePanel, type PipelineStageInfo } from './PipelinePanel';
import { SecurityPanel, type SecurityFindingItem } from './SecurityPanel';
import { AIExplainView } from './AIExplainView';

export type BottomPanelTab =
  | 'view-tokens'
  | 'view-diagnostics'
  | 'view-pipeline-tab'
  | 'view-security-tab'
  | 'view-ai-explain';

interface AnalysisPanelProps {
  activeTab: BottomPanelTab;
  onSelectTab: (tab: BottomPanelTab) => void;
  tokens: TokenItem[];
  selectedToken: TokenItem | null;
  onSelectToken: (token: TokenItem) => void;
  onExplainToken: (token: TokenItem) => void;
  onFixWithAiToken: (token: TokenItem) => void;
  onJumpToCode: (line: number, col: number, endLine?: number, endCol?: number) => void;
  diagnostics: DiagnosticItem[];
  securityFindings: SecurityFindingItem[];
  pipelineStages: PipelineStageInfo[];
  selectedStageId: string | null;
  onSelectStage: (id: string) => void;
  onRerunStage: (id: string) => void;
  isRunningAllAgents: boolean;
  onApplyRemediation: () => void;
  onRunAllAgents: () => void;
  onAskAiStage?: (stage: PipelineStageInfo) => void;
  onExplainDiagnostic?: (d: DiagnosticItem) => void;
  onFixWithAiDiagnostic?: (d: DiagnosticItem) => void;
  onExplainFinding?: (f: SecurityFindingItem) => void;
  onFixWithAiFinding?: (f: SecurityFindingItem) => void;
  onExportCSV: () => void;
  onExportJSON: () => void;
  isMaximized: boolean;
  onToggleMaximize: () => void;
  onAskFollowUp: (prompt: string) => void;
  isAnalyzing?: boolean;
  isStale?: boolean;
  errorMessage?: string | null;
  languageStandard?: string;
}

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  activeTab,
  onSelectTab,
  tokens,
  selectedToken,
  onSelectToken,
  onExplainToken,
  onFixWithAiToken,
  onJumpToCode,
  diagnostics,
  securityFindings,
  pipelineStages,
  selectedStageId,
  onSelectStage,
  onRerunStage,
  isRunningAllAgents,
  onApplyRemediation,
  onRunAllAgents,
  onAskAiStage,
  onExplainDiagnostic,
  onFixWithAiDiagnostic,
  onExplainFinding,
  onFixWithAiFinding,
  onExportCSV,
  onExportJSON,
  isMaximized,
  onToggleMaximize,
  onAskFollowUp,
  isAnalyzing = false,
  isStale = false,
  errorMessage = null,
  languageStandard,
}) => {
  const getTabButtonClass = (tab: BottomPanelTab) => {
    const isActive = activeTab === tab;
    return `panel-tab flex items-center gap-1.5 px-3 h-full text-[11px] font-semibold transition-colors ${
      isActive
        ? 'bg-surface-selected border-b-2 border-primary text-text-primary'
        : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
    }`;
  };

  const hasCriticalSecurity = securityFindings.length > 0;
  const passedPipelineCount = pipelineStages.filter(
    (s) => s.status === 'passed' || s.status === 'warning'
  ).length;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-surface-deepest transition-colors" id="bottomPanel">
      {/* Tabs Header */}
      <div className="h-8 px-2 bg-surface-deepest border-b border-border-primary flex items-center justify-between shrink-0 transition-colors">
        <div className="flex items-center gap-1 h-full" id="panelTabStrip">
          {/* Tokens Tab */}
          <button
            type="button"
            className={getTabButtonClass('view-tokens')}
            onClick={() => onSelectTab('view-tokens')}
            data-target="view-tokens"
          >
            <span className="material-symbols-outlined text-[14px]">token</span>
            <span>Tokens</span>
            <span
              className="px-1.5 py-0.2 rounded-full text-[9px] bg-primary text-white font-mono"
              id="tokenBadge"
            >
              {tokens.length}
            </span>
          </button>

          {/* Diagnostics Tab */}
          <button
            type="button"
            className={getTabButtonClass('view-diagnostics')}
            onClick={() => onSelectTab('view-diagnostics')}
            data-target="view-diagnostics"
          >
            <span className="material-symbols-outlined text-[14px] text-status-error">error</span>
            <span>Diagnostics</span>
            <span
              className={`px-1.5 py-0.2 rounded-full text-[9px] font-bold font-mono text-white ${
                diagnostics.length > 0 ? 'bg-status-error' : 'bg-status-success'
              }`}
            >
              {diagnostics.length}
            </span>
          </button>

          {/* Pipeline Tab */}
          <button
            type="button"
            className={getTabButtonClass('view-pipeline-tab')}
            onClick={() => onSelectTab('view-pipeline-tab')}
            data-target="view-pipeline-tab"
          >
            <span className="material-symbols-outlined text-[14px]">account_tree</span>
            <span>Pipeline</span>
            <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-surface-container border border-border-subtle font-mono text-text-muted">
              {passedPipelineCount}/{pipelineStages.length}
            </span>
          </button>

          {/* Security Tab */}
          <button
            type="button"
            className={getTabButtonClass('view-security-tab')}
            onClick={() => onSelectTab('view-security-tab')}
            data-target="view-security-tab"
          >
            <span className="material-symbols-outlined text-[14px] text-status-warning">shield</span>
            <span>Security</span>
            {securityFindings.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-status-error text-white font-bold font-mono">
                {securityFindings.length}
              </span>
            )}
          </button>

          {/* AI Explain Tab */}
          <button
            type="button"
            className={getTabButtonClass('view-ai-explain')}
            onClick={() => onSelectTab('view-ai-explain')}
            data-target="view-ai-explain"
          >
            <span className="material-symbols-outlined text-[14px] text-accent-ai">psychology</span>
            <span>AI Explain</span>
          </button>
        </div>

        {/* Export & Controls */}
        <div className="flex items-center gap-1 text-text-muted">
          <button
            type="button"
            className="px-2 py-0.5 hover:text-text-primary hover:bg-surface-hover rounded text-[11px] font-mono flex items-center gap-1 border border-transparent hover:border-border-subtle transition-colors"
            onClick={onExportCSV}
            title="Export Token Stream to CSV"
          >
            <span className="material-symbols-outlined text-[13px]">download</span> CSV
          </button>
          <button
            type="button"
            className="px-2 py-0.5 hover:text-text-primary hover:bg-surface-hover rounded text-[11px] font-mono flex items-center gap-1 border border-transparent hover:border-border-subtle transition-colors"
            onClick={onExportJSON}
            title="Export Analysis &amp; Pipeline to JSON"
          >
            <span className="material-symbols-outlined text-[13px]">code</span> JSON
          </button>
          <div className="h-3 w-[1px] bg-border-primary mx-1" />
          <button
            type="button"
            className="p-1 hover:text-text-primary hover:bg-surface-hover rounded transition-colors"
            onClick={onToggleMaximize}
            title={isMaximized ? 'Restore Panel' : 'Maximize Panel'}
          >
            <span className="material-symbols-outlined text-[14px]" id="maxIcon">
              {isMaximized ? 'keyboard_double_arrow_down' : 'keyboard_double_arrow_up'}
            </span>
          </button>
        </div>
      </div>

      {/* Panel Body: Split View */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Active Left View */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-border-primary overflow-hidden">
          {activeTab === 'view-tokens' && (
            <>
              <TokenTable
                tokens={tokens}
                selectedTokenId={selectedToken?.id ?? null}
                onSelectToken={onSelectToken}
                onJumpToCode={onJumpToCode}
                languageStandard={languageStandard}
                isAnalyzing={isAnalyzing}
                isStale={isStale}
                errorMessage={errorMessage}
              />
              <TokenInspector
                token={selectedToken}
                onExplain={onExplainToken}
                onFixWithAi={onFixWithAiToken}
                onJumpToCode={onJumpToCode}
              />
            </>
          )}

          {activeTab === 'view-diagnostics' && (
            <DiagnosticsPanel
              diagnostics={diagnostics}
              onSelectDiagnostic={(d) => onJumpToCode(d.line, d.col)}
              onExplain={onExplainDiagnostic}
              onFixWithAi={onFixWithAiDiagnostic}
            />
          )}

          {activeTab === 'view-pipeline-tab' && (
            <PipelinePanel
              stages={pipelineStages}
              selectedStageId={selectedStageId}
              onSelectStage={onSelectStage}
              onRerunStage={onRerunStage}
              onRunAllAgents={onRunAllAgents}
              isRunningAll={isRunningAllAgents}
              onAskAiStage={onAskAiStage}
            />
          )}

          {activeTab === 'view-security-tab' && (
            <SecurityPanel
              findings={securityFindings}
              onApplyRemediation={onApplyRemediation}
              onJumpToCode={onJumpToCode}
              onFocusLine={(line) => onJumpToCode(line, 1)}
              onExplainFinding={onExplainFinding}
              onFixWithAiFinding={onFixWithAiFinding}
              isAnalyzing={isAnalyzing}
            />
          )}

          {activeTab === 'view-ai-explain' && (
            <AIExplainView onAskFollowUp={onAskFollowUp} />
          )}
        </div>

        {/* RIGHT SUB-PANEL: Real Compiler Agent Pipeline */}
        <div className="w-64 bg-surface-explorer flex flex-col justify-between shrink-0 overflow-hidden transition-colors">
          <div className="h-8 px-3 bg-surface-deepest border-b border-border-primary flex items-center justify-between shrink-0">
            <span className="font-bold text-[10px] uppercase text-text-secondary tracking-wider">
              Agent Pipeline
            </span>
            <span
              className={`text-[10px] font-bold font-mono ${
                hasCriticalSecurity ? 'text-status-warning' : 'text-status-success'
              }`}
              id="pipelinePassedBadge"
            >
              {passedPipelineCount}/{pipelineStages.length} Passed
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {pipelineStages.map((stage, idx) => {
              const isSelected = stage.id === selectedStageId && activeTab === 'view-pipeline-tab';
              const icon =
                stage.status === 'passed'
                  ? 'check_circle'
                  : stage.status === 'warning'
                  ? 'warning'
                  : stage.status === 'failed'
                  ? 'cancel'
                  : stage.status === 'running'
                  ? 'sync'
                  : stage.status === 'skipped'
                  ? 'redo'
                  : 'radio_button_unchecked';

              const color =
                stage.status === 'passed'
                  ? 'text-status-success'
                  : stage.status === 'warning'
                  ? 'text-status-warning'
                  : stage.status === 'failed'
                  ? 'text-status-error'
                  : stage.status === 'running'
                  ? 'text-primary'
                  : 'text-text-muted';

              return (
                <div
                  key={stage.id}
                  className={`flex items-start gap-2 p-2 rounded-md border shadow-xs cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-surface-elevated border-primary'
                      : 'bg-surface-elevated/80 hover:bg-surface-elevated border-border-subtle'
                  }`}
                  onClick={() => {
                    onSelectStage(stage.id);
                    onSelectTab('view-pipeline-tab');
                  }}
                >
                  <span
                    className={`material-symbols-outlined text-[15px] mt-0.5 shrink-0 ${color} ${
                      stage.status === 'running' ? 'animate-spin' : ''
                    }`}
                  >
                    {icon}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-[11px] text-text-primary truncate">
                        {idx + 1}. {stage.name}
                      </span>
                      <span className="text-[9px] text-text-muted font-mono shrink-0 ml-1">
                        {stage.elapsedMs > 0 ? `${stage.elapsedMs.toFixed(1)}ms` : ''}
                      </span>
                    </div>
                    <div className="text-[9px] text-text-muted truncate mt-0.5">
                      {stage.status === 'skipped'
                        ? stage.skipReason || 'Skipped'
                        : stage.status === 'failed'
                        ? stage.errorReason || 'Failed'
                        : stage.outputSummary || stage.agentName}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-2.5 border-t border-border-primary bg-surface-deepest shrink-0">
            <button
              type="button"
              className="w-full py-1.5 bg-primary hover:bg-primary-hover disabled:opacity-50 text-white rounded-md text-[11px] font-semibold shadow-xs transition-colors flex items-center justify-center gap-1.5"
              onClick={onRunAllAgents}
              disabled={isRunningAllAgents}
            >
              <span
                className={`material-symbols-outlined text-[14px] ${
                  isRunningAllAgents ? 'animate-spin' : ''
                }`}
              >
                {isRunningAllAgents ? 'sync' : 'hub'}
              </span>
              <span>{isRunningAllAgents ? 'Executing Agents...' : 'Run All Agents (7)'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
