import React from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { X } from 'lucide-react';
import { DocItem } from '../model/doc';
import { EditorPane, NavTarget } from './EditorPane';
import { FindingPanel, Tab } from './FindingPanel';
import {
  AnalysisResult,
  Finding,
  Fix,
  MLInsightsResponse,
  SampleItem,
  TaintPathStep,
} from '../api/client';

interface AppPanelsProps {
  openDocs: DocItem[];
  activeDocId: string | null;
  activateDoc: (doc: DocItem) => void;
  closeCurrentFile: (id?: string) => void;
  source: string;
  language: string;
  filename: string;
  findings: Finding[];
  selectedFindingId: string | null;
  activeDataFlowFindingId: string | null;
  navTarget: NavTarget | null;
  onChangeSource: (val: string) => void;
  onCursorChange: (pos: { line: number; col: number }) => void;
  selectedTokenIndex: number | null;
  tokenMap: 'off' | 'security' | 'full';
  tokenCategory: string;
  onSelectToken: (idx: number | null) => void;
  onOpenTokens: () => void;
  onSelectFinding: (id: string) => void;
  onOpenDiff: (fix: Fix, finding: Finding) => void;
  onAnalyzeShortcut: () => void;
  onDownloadShortcut: () => void;
  onNextProblem: () => void;
  onPrevProblem: () => void;
  // FindingPanel props
  activeTab: Tab;
  onChangeTab: (tab: Tab) => void;
  selectedFinding: Finding | null;
  summary: any;
  engine: any;
  analysisLanguage?: string;
  mlInsights: MLInsightsResponse | null;
  isLoadingInsights: boolean;
  mlMode: 'on' | 'off';
  onApplyFix: (fix: Fix, finding: Finding) => void;
  onJumpToStep: (step: TaintPathStep) => void;
  onToggleDataFlow: (id: string) => void;
  onMarkFalsePositive: (finding: Finding) => void;
  onSuppressFinding: (finding: Finding) => void;
  onAskAIFix: (finding: Finding) => void;
  isAskingAI: boolean;
  llmConfigured: boolean;
  llmProvider: string;
  analysis: AnalysisResult | null;
  onTokenMap: (map: 'off' | 'security' | 'full') => void;
  onTokenCategory: (cat: string) => void;
  onSelectTokenFromPanel: (idx: number) => void;
  onLoadTokenML: (idx: number) => void;
  showAllTokens: boolean;
  tokenMainFilter: 'All' | 'Security' | 'Lexical' | 'Syntax';
  tokenGroups: string[];
  activeSample: SampleItem | null;
  onDemoStep: (delta: number) => void;
  agentMode: 'off' | 'rules' | 'local';
  agentModel: string;
  samples: SampleItem[];
}

export const AppPanels: React.FC<AppPanelsProps> = ({
  openDocs,
  activeDocId,
  activateDoc,
  closeCurrentFile,
  source,
  language,
  filename,
  findings,
  selectedFindingId,
  activeDataFlowFindingId,
  navTarget,
  onChangeSource,
  onCursorChange,
  selectedTokenIndex,
  tokenMap,
  tokenCategory,
  onSelectToken,
  onOpenTokens,
  onSelectFinding,
  onOpenDiff,
  onAnalyzeShortcut,
  onDownloadShortcut,
  onNextProblem,
  onPrevProblem,
  activeTab,
  onChangeTab,
  selectedFinding,
  summary,
  engine,
  analysisLanguage,
  mlInsights,
  isLoadingInsights,
  mlMode,
  onApplyFix,
  onJumpToStep,
  onToggleDataFlow,
  onMarkFalsePositive,
  onSuppressFinding,
  onAskAIFix,
  isAskingAI,
  llmConfigured,
  llmProvider,
  analysis,
  onTokenMap,
  onTokenCategory,
  onSelectTokenFromPanel,
  onLoadTokenML,
  showAllTokens,
  tokenMainFilter,
  tokenGroups,
  activeSample,
  onDemoStep,
  agentMode,
  agentModel,
}) => {
  return (
    <PanelGroup direction="horizontal" autoSaveId="ui5-editor-split" className="ui5-panels">
      <Panel defaultSize={39} minSize={34}>
        <div data-qa="code-pane" className="ui5-editor">
          {openDocs.length >= 2 && (
            <div data-qa="strip-files" className="ui6-tabs" role="tablist" aria-label="Open files">
              {openDocs.map((doc) => (
                <div
                  role="presentation"
                  className={`ui6-tab ${doc.id === activeDocId ? 'active' : ''}`}
                  key={doc.id}
                >
                  <button
                    role="tab"
                    aria-selected={doc.id === activeDocId}
                    onClick={() => activateDoc(doc)}
                    title={doc.name}
                  >
                    {doc.name}
                    {doc.dirty && <i aria-label="Unsaved changes" />}
                  </button>
                  <button aria-label={`Close ${doc.name}`} onClick={() => closeCurrentFile(doc.id)}>
                    <X size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}
          <EditorPane
            source={source}
            language={language}
            filename={filename}
            modelKey={activeDocId}
            findings={findings}
            tokens={analysis?.tokens || []}
            analysis={analysis}
            selectedFindingId={selectedFindingId}
            activeDataFlowFindingId={activeDataFlowFindingId}
            navTarget={navTarget}
            onChangeSource={onChangeSource}
            onCursorChange={onCursorChange}
            selectedTokenIndex={selectedTokenIndex}
            tokenMap={tokenMap}
            tokenCategory={tokenCategory}
            onSelectToken={onSelectToken}
            onOpenTokens={onOpenTokens}
            onSelectFinding={onSelectFinding}
            onOpenDiff={onOpenDiff}
            onAnalyzeShortcut={onAnalyzeShortcut}
            onDownloadShortcut={onDownloadShortcut}
            onNextProblem={onNextProblem}
            onPrevProblem={onPrevProblem}
          />
          <div data-qa="legend-row" className="ui5-legend">
            <span className="ui5-badge safe">Safe</span>
            <span className="ui5-badge warning">Valid but insecure</span>
            <span className="ui5-badge danger">Lexical error</span>
          </div>
        </div>
      </Panel>
      <PanelResizeHandle className="ui5-divider" />
      <Panel defaultSize={61} minSize={42}>
        <FindingPanel
          activeTab={activeTab}
          onChangeTab={onChangeTab}
          selectedFinding={selectedFinding}
          summary={summary}
          findings={findings}
          engine={engine}
          language={analysisLanguage || language}
          mlInsights={mlInsights}
          isLoadingInsights={isLoadingInsights}
          mlMode={mlMode}
          onApplyFix={onApplyFix}
          onOpenDiff={onOpenDiff}
          onJumpToStep={onJumpToStep}
          onToggleDataFlow={onToggleDataFlow}
          isDataFlowActive={activeDataFlowFindingId === selectedFindingId}
          onMarkFalsePositive={onMarkFalsePositive}
          onSuppressFinding={onSuppressFinding}
          onAskAIFix={onAskAIFix}
          isAskingAI={isAskingAI}
          llmConfigured={llmConfigured}
          llmProvider={llmProvider}
          analysis={analysis}
          selectedTokenIndex={selectedTokenIndex}
          tokenMap={tokenMap}
          onTokenMap={onTokenMap}
          tokenCategory={tokenCategory}
          onTokenCategory={onTokenCategory}
          onSelectToken={onSelectTokenFromPanel}
          onLoadTokenML={onLoadTokenML}
          onSelectFindingById={onSelectFinding}
          showAllTokens={showAllTokens}
          tokenMainFilter={tokenMainFilter}
          tokenGroups={tokenGroups}
          sample={activeSample}
          sampleEdited={Boolean(activeSample && source !== activeSample.code)}
          onDemoStep={onDemoStep}
          agentMode={agentMode}
          agentModel={agentModel}
        />
      </Panel>
    </PanelGroup>
  );
};
