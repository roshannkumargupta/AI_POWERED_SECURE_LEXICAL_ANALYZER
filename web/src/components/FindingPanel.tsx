import React from 'react';
import {
  Finding,
  Fix,
  AnalysisSummary,
  EngineMetadata,
  MLInsightsResponse,
  TaintPathStep,
  SampleItem,
  AnalysisResult,
} from '../api/client';
import { TaintPath } from './TaintPath';
import { MlInsights } from './MlInsights';
import { TokensPanel } from './TokensPanel';
import { ProblemsPanel } from './ProblemsPanel';
import { AgentTraceTab } from './AgentTraceTab';
import { FindingDetailView } from './FindingDetailView';
import { FindingSummaryView } from './FindingSummaryView';
import { FindingDemoBar } from './FindingDemoBar';
import { containerStyle, tabHeaderStyle, tabButtonStyle, tabContentStyle } from './findingStyles';

export type Tab = 'problems' | 'finding' | 'tokens' | 'taint' | 'summary' | 'ml' | 'trace';

interface FindingPanelProps {
  activeTab: Tab;
  onChangeTab: (tab: Tab) => void;
  selectedFinding: Finding | null;
  summary: AnalysisSummary | null;
  findings?: Finding[];
  engine?: EngineMetadata | null;
  language?: string;
  mlInsights: MLInsightsResponse | null;
  isLoadingInsights: boolean;
  mlMode: 'on' | 'off';
  agentMode?: 'off' | 'rules' | 'local';
  agentModel?: string;
  ollamaUrl?: string;
  onApplyFix: (fix: Fix, finding: Finding) => void;
  onOpenDiff: (fix: Fix, finding: Finding) => void;
  onJumpToStep: (step: TaintPathStep) => void;
  onToggleDataFlow: (findingId: string) => void;
  isDataFlowActive: boolean;
  onMarkFalsePositive: (finding: Finding) => void;
  onSuppressFinding?: (finding: Finding) => void;
  onAskAIFix?: (finding: Finding) => void;
  isAskingAI?: boolean;
  llmConfigured?: boolean;
  llmProvider?: string;
  sample?: SampleItem | null;
  sampleEdited?: boolean;
  onDemoStep?: (delta: number) => void;
  analysis: AnalysisResult | null;
  selectedTokenIndex: number | null;
  tokenMap: 'off' | 'security' | 'full';
  onTokenMap: (mode: 'off' | 'security' | 'full') => void;
  tokenCategory: string;
  onTokenCategory: (category: string) => void;
  onSelectToken: (index: number) => void;
  onLoadTokenML: (index: number) => void;
  onSelectFindingById: (id: string) => void;
  showAllTokens?: boolean;
  tokenMainFilter?: 'All' | 'Security' | 'Lexical' | 'Syntax';
  tokenGroups?: string[];
}

export const FindingPanel: React.FC<FindingPanelProps> = ({
  activeTab,
  onChangeTab,
  selectedFinding,
  summary,
  findings = [],
  engine = null,
  language = 'auto',
  mlInsights,
  isLoadingInsights,
  mlMode,
  onApplyFix,
  onOpenDiff,
  onJumpToStep,
  onToggleDataFlow,
  isDataFlowActive,
  onMarkFalsePositive,
  onSuppressFinding,
  onAskAIFix,
  isAskingAI = false,
  llmConfigured = false,
  llmProvider = 'none',
  sample = null,
  sampleEdited = false,
  onDemoStep,
  analysis,
  selectedTokenIndex,
  tokenMap,
  onTokenMap,
  tokenCategory,
  onTokenCategory,
  onSelectToken,
  onLoadTokenML,
  onSelectFindingById,
  showAllTokens = false,
  tokenMainFilter = 'All',
  tokenGroups = [],
  agentMode = 'off',
  agentModel = 'qwen2.5-coder:3b',
  ollamaUrl = 'http://127.0.0.1:11434',
}) => {
  return (
    <div data-qa="right-pane" style={containerStyle}>
      {/* Tabs Header */}
      <div data-qa="tabs" role="tablist" aria-label="Analysis views" style={tabHeaderStyle}>
        {(
          [
            ['problems', 'Problems'],
            ['finding', 'Finding'],
            ['tokens', 'Tokens'],
            ['taint', 'Taint path'],
            ['ml', 'ML insights'],
            ['summary', 'Summary'],
            ['trace', 'Agent trace'],
          ] as const
        ).map(([tabKey, label]) => (
          <button
            key={tabKey}
            role="tab"
            aria-selected={activeTab === tabKey}
            style={{
              ...tabButtonStyle,
              borderBottom:
                activeTab === tabKey ? '2px solid var(--text-accent)' : '2px solid transparent',
              color: activeTab === tabKey ? 'var(--text-accent)' : 'var(--text-muted)',
            }}
            onClick={() => onChangeTab(tabKey)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={tabContentStyle}>
        {activeTab === 'problems' && (
          <div
            style={{ height: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column' }}
          >
            <ProblemsPanel
              findings={findings}
              selectedFindingId={selectedFinding?.id || null}
              filter="all"
              onSelectFilter={() => {}}
              onSelectFinding={(id) => {
                onSelectFindingById?.(id);
                onChangeTab('finding');
              }}
              onNextFinding={() => {}}
              onPrevFinding={() => {}}
            />
          </div>
        )}

        {activeTab === 'finding' && (
          <>
            {sample && (
              <FindingDemoBar
                sample={sample}
                sampleEdited={sampleEdited}
                onDemoStep={onDemoStep}
                findings={findings}
                analysis={analysis}
              />
            )}
            <FindingDetailView
              selectedFinding={selectedFinding}
              isDataFlowActive={isDataFlowActive}
              onToggleDataFlow={onToggleDataFlow}
              onJumpToStep={onJumpToStep}
              onApplyFix={onApplyFix}
              onOpenDiff={onOpenDiff}
              onMarkFalsePositive={onMarkFalsePositive}
              onSuppressFinding={onSuppressFinding}
              onAskAIFix={onAskAIFix}
              isAskingAI={isAskingAI}
              llmConfigured={llmConfigured}
              llmProvider={llmProvider}
            />
          </>
        )}

        {activeTab === 'tokens' && (
          <TokensPanel
            result={analysis}
            language={language}
            selectedIndex={selectedTokenIndex}
            selectedFindingId={selectedFinding?.id || null}
            mlMode={mlMode}
            ml={mlInsights}
            loadingML={isLoadingInsights}
            onSelectToken={onSelectToken}
            onSelectFinding={onSelectFindingById}
            onLoadML={onLoadTokenML}
            tokenMap={tokenMap}
            onTokenMap={onTokenMap}
            category={tokenCategory}
            onCategoryChange={onTokenCategory}
            showAll={showAllTokens}
            mainFilter={tokenMainFilter}
            groups={tokenGroups}
          />
        )}

        {activeTab === 'taint' &&
          (selectedFinding?.taint_path?.length ? (
            <TaintPath
              steps={selectedFinding.taint_path}
              engine={engine?.taint}
              isEditorActive={isDataFlowActive}
              onToggleEditor={() => onToggleDataFlow(selectedFinding.id)}
              onJumpToStep={onJumpToStep}
            />
          ) : (
            <div style={{ color: 'var(--text-muted)', padding: 12 }}>
              No data-flow path for this token.
            </div>
          ))}

        {activeTab === 'summary' && (
          <FindingSummaryView summary={summary} engine={engine} language={language} />
        )}

        {activeTab === 'ml' && (
          <MlInsights
            insights={mlInsights}
            isLoading={isLoadingInsights}
            mlMode={mlMode}
            modelId={engine?.ml_model_id}
            selectedToken={
              analysis?.tokens?.[selectedTokenIndex ?? -1]?.token ??
              analysis?.tokens?.[selectedTokenIndex ?? -1]?.text ??
              undefined
            }
            lexicalError={Boolean(
              analysis &&
              selectedTokenIndex !== null &&
              analysis.findings.some(
                (finding) =>
                  finding.kind === 'lexical' &&
                  (() => {
                    const token = analysis.tokens[selectedTokenIndex];
                    return Boolean(
                      token?.range &&
                      token.range.start_line <= finding.range.end_line &&
                      token.range.end_line >= finding.range.start_line &&
                      (token.range.start_line !== finding.range.end_line ||
                        token.range.start_col < finding.range.end_col) &&
                      (finding.range.start_line !== token.range.end_line ||
                        finding.range.start_col < token.range.end_col)
                    );
                  })()
              )
            )}
            mlReason={(engine as (EngineMetadata & { ml_reason?: string }) | null)?.ml_reason}
          />
        )}

        {activeTab === 'trace' && (
          <AgentTraceTab
            trace={analysis?.trace || []}
            agentMeta={analysis?.agent_meta}
            agentMode={agentMode}
            agentModel={agentModel}
            ollamaUrl={ollamaUrl}
          />
        )}
      </div>
    </div>
  );
};
