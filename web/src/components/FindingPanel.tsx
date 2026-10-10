import React from 'react';
import {
  AlertOctagon,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  ShieldCheck,
  Flag,
  Wand2,
  GitBranch,
  Sparkles,
  EyeOff,
} from 'lucide-react';
import { Finding, Fix, AnalysisSummary, EngineMetadata, MLInsightsResponse, TaintPathStep, SampleItem } from '../api/client';
import { TaintPath } from './TaintPath';
import { MlInsights } from './MlInsights';
import { TokensPanel } from './TokensPanel';
import { ProblemsPanel } from './ProblemsPanel';
import type { AnalysisResult } from '../api/client';
import { compareSample, DEMO_PATH } from '../utils/sampleDemo';
import { AgentTraceTab } from './AgentTraceTab';

type Tab = 'problems' | 'finding' | 'tokens' | 'taint' | 'summary' | 'ml' | 'trace';

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
  analysis: AnalysisResult | null; selectedTokenIndex: number | null; tokenMap: 'off'|'security'|'full'; onTokenMap: (mode: 'off'|'security'|'full') => void; tokenCategory: string; onTokenCategory: (category: string) => void; onSelectToken: (index: number) => void; onLoadTokenML: (index: number) => void; onSelectFindingById: (id: string) => void;
  showAllTokens?: boolean; tokenMainFilter?: 'All'|'Security'|'Lexical'|'Syntax'; tokenGroups?: string[];
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
  sample = null, sampleEdited = false, onDemoStep,
  analysis, selectedTokenIndex, tokenMap, onTokenMap, tokenCategory, onTokenCategory, onSelectToken, onLoadTokenML, onSelectFindingById, showAllTokens = false, tokenMainFilter = 'All', tokenGroups = [],
  agentMode = 'off', agentModel = 'qwen2.5-coder:3b', ollamaUrl = 'http://127.0.0.1:11434',
}) => {
  const [explanationMode, setExplanationMode] = React.useState<'simple' | 'detailed'>('detailed');

  const getSeverityBadge = (finding: Finding) => {
    switch (finding.severity) {
      case 'critical':
        return (
          <span style={{ ...sevBadgeStyle, color: 'var(--critical)', backgroundColor: 'var(--critical-subtle)' }}>
            <AlertOctagon size={13} />
            CRITICAL
          </span>
        );
      case 'high':
        return (
          <span style={{ ...sevBadgeStyle, color: 'var(--high)', backgroundColor: 'var(--high-subtle)' }}>
            <ShieldAlert size={13} />
            HIGH
          </span>
        );
      case 'medium':
        return (
          <span style={{ ...sevBadgeStyle, color: 'var(--medium)', backgroundColor: 'var(--medium-subtle)' }}>
            <AlertTriangle size={13} />
            MEDIUM
          </span>
        );
      case 'low':
        return (
          <span style={{ ...sevBadgeStyle, color: 'var(--low)', backgroundColor: 'var(--low-subtle)' }}>
            <Info size={13} />
            LOW
          </span>
        );
      case 'info':
      default:
        return (
          <span style={{ ...sevBadgeStyle, color: 'var(--info)', backgroundColor: 'var(--info-subtle)' }}>
            <CheckCircle2 size={13} />
            INFO
          </span>
        );
    }
  };

  return (
    <div data-qa="right-pane" style={containerStyle}>
      {/* Tabs Header */}
      <div data-qa="tabs" role="tablist" aria-label="Analysis views" style={tabHeaderStyle}>
        <button role="tab" aria-selected={activeTab === 'problems'} style={{ ...tabButtonStyle, borderBottom: activeTab === 'problems' ? '2px solid var(--text-accent)' : '2px solid transparent', color: activeTab === 'problems' ? 'var(--text-accent)' : 'var(--text-muted)' }} onClick={() => onChangeTab('problems')}>Problems</button>
        <button role="tab" aria-selected={activeTab === 'finding'} style={{ ...tabButtonStyle, borderBottom: activeTab === 'finding' ? '2px solid var(--text-accent)' : '2px solid transparent', color: activeTab === 'finding' ? 'var(--text-accent)' : 'var(--text-muted)' }} onClick={() => onChangeTab('finding')}>Finding</button>
        <button role="tab" aria-selected={activeTab === 'tokens'} style={{ ...tabButtonStyle, borderBottom: activeTab === 'tokens' ? '2px solid var(--text-accent)' : '2px solid transparent', color: activeTab === 'tokens' ? 'var(--text-accent)' : 'var(--text-muted)' }} onClick={() => onChangeTab('tokens')}>Tokens</button>
        <button role="tab" aria-selected={activeTab === 'taint'} style={{ ...tabButtonStyle, borderBottom: activeTab === 'taint' ? '2px solid var(--text-accent)' : '2px solid transparent', color: activeTab === 'taint' ? 'var(--text-accent)' : 'var(--text-muted)' }} onClick={() => onChangeTab('taint')}>Taint path</button>
        <button role="tab" aria-selected={activeTab === 'ml'} style={{ ...tabButtonStyle, borderBottom: activeTab === 'ml' ? '2px solid var(--text-accent)' : '2px solid transparent', color: activeTab === 'ml' ? 'var(--text-accent)' : 'var(--text-muted)' }} onClick={() => onChangeTab('ml')}>ML insights</button>
        <button
          style={{
            ...tabButtonStyle,
            borderBottom: activeTab === 'summary' ? '2px solid var(--text-accent)' : '2px solid transparent',
            color: activeTab === 'summary' ? 'var(--text-accent)' : 'var(--text-muted)',
          }}
          role="tab" aria-selected={activeTab === 'summary'} onClick={() => onChangeTab('summary')}
        >
          Summary
        </button>
        <button
          style={{
            ...tabButtonStyle,
            borderBottom: activeTab === 'trace' ? '2px solid var(--text-accent)' : '2px solid transparent',
            color: activeTab === 'trace' ? 'var(--text-accent)' : 'var(--text-muted)',
          }}
          role="tab" aria-selected={activeTab === 'trace'} onClick={() => onChangeTab('trace')}
        >
          Agent trace
        </button>
      </div>

      {/* Tab Content */}
      <div style={tabContentStyle}>
        {activeTab === 'problems' && (
          <div style={{ height: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
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
          {sample?.demo_order && <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, padding: '6px 12px 0' }}><button disabled={DEMO_PATH.indexOf(sample.id) <= 0} onClick={() => onDemoStep?.(-1)}>Previous</button><button disabled={DEMO_PATH.indexOf(sample.id) >= DEMO_PATH.length - 1} onClick={() => onDemoStep?.(1)}>Next</button></div>}
          {sample && <details style={{ margin: '8px 12px', color: 'var(--muted)', fontSize: 11 }}>
            <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)' }}>Demo notes</summary>
            <div style={{ display: 'grid', gap: 6, padding: '8px 0' }}>
              <div>{sample.summary || sample.description}</div>
              <ul style={{ margin: 0, paddingLeft: 18 }}>{(sample.notes || []).slice(0, 4).map((note, i) => <li key={i}>{note}</li>)}</ul>
              <div>Expected: {(sample.expect?.findings || []).length} findings - {(sample.expect?.findings || []).map((item) => item.rule_id).join(', ') || 'none'}</div>
              {analysis && <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: sampleEdited ? 'var(--amber)' : compareSample(sample, findings, false) === 'Matches expected' ? 'var(--success)' : 'var(--amber)' }}>{!sampleEdited && compareSample(sample, findings, false) === 'Matches expected' && <CheckCircle2 size={12} />}{sampleEdited ? 'Edited - comparison paused' : compareSample(sample, findings, false)}</div>}
              {sample.senior && <div>Senior project: {sample.senior.flagged === null ? sample.senior.detail : sample.senior.flagged ? `flagged ${sample.senior.detail}` : 'not flagged'} <small>senior tool run without its ML model{sample.senior.note ? ` · ${sample.senior.note}` : ''}</small></div>}
            </div>
          </details>}
          {selectedFinding ? (
            <div style={findingContainerStyle}>
              {/* Finding Title & Badges */}
              <div style={findingHeaderStyle}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  {getSeverityBadge(selectedFinding)}
                  <code style={ruleCodeStyle}>{selectedFinding.rule_id}</code>
                </div>
                <h3 style={titleStyle}>{selectedFinding.title}</h3>
                <span style={locationSubStyle}>{selectedFinding.cwe} · {selectedFinding.message}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <span style={sectionTitleStyle}>WHY IT WAS FLAGGED</span>
                {(['rule', 'taint', 'ml', 'unicode'] as const).map((source) => {
                  const active = selectedFinding.sources?.some((value) => value.toLowerCase().includes(source)) || (source === 'taint' && Boolean(selectedFinding.taint_path?.length));
                  return <span key={source} style={{ color: active ? 'var(--text-secondary)' : 'var(--muted-dark)', fontSize: 11 }}>{active ? '✓' : '○'} {source[0].toUpperCase() + source.slice(1)}</span>;
                })}
              </div>
              <details style={{ color: 'var(--muted)', fontSize: 11 }}>
                <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)' }}>Details</summary>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, padding: '8px 0' }}>
                  <span>Rule: {selectedFinding.rule_id}</span><span>Confidence: {Math.round(selectedFinding.confidence * 100)}%</span>
                  <span>Range: {selectedFinding.range.start_line}:{selectedFinding.range.start_col}</span><span>Detectors: {selectedFinding.sources?.join(', ') || '—'}</span>
                </div>
              </details>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px' }}>
                <span style={sectionTitleStyle}>EXPLANATION</span>
                <div style={{ display: 'inline-flex', borderRadius: '4px', border: '1px solid var(--border)', overflow: 'hidden' }}>
                  <button
                    data-qa="simple-explanation-toggle"
                    type="button"
                    style={{
                      padding: '2px 8px',
                      fontSize: '11px',
                      fontWeight: explanationMode === 'simple' ? 600 : 400,
                      backgroundColor: explanationMode === 'simple' ? 'var(--accent)' : 'var(--panel-2)',
                      color: explanationMode === 'simple' ? 'var(--text-on-accent)' : 'var(--text-secondary)',
                      border: 'none',
                      cursor: 'pointer',
                    }}
                    onClick={() => setExplanationMode('simple')}
                  >
                    Simple
                  </button>
                  <button
                    data-qa="detailed-explanation-toggle"
                    type="button"
                    style={{
                      padding: '2px 8px',
                      fontSize: '11px',
                      fontWeight: explanationMode === 'detailed' ? 600 : 400,
                      backgroundColor: explanationMode === 'detailed' ? 'var(--accent)' : 'var(--panel-2)',
                      color: explanationMode === 'detailed' ? 'var(--text-on-accent)' : 'var(--text-secondary)',
                      border: 'none',
                      cursor: 'pointer',
                    }}
                    onClick={() => setExplanationMode('detailed')}
                  >
                    Detailed
                  </button>
                </div>
              </div>
              <div style={{ ...explanationTextStyle, whiteSpace: 'pre-wrap' }}>
                {explanationMode === 'simple'
                  ? selectedFinding.simple_explanation || selectedFinding.explanation?.split('\n\n')[0] || selectedFinding.message
                  : selectedFinding.detailed_explanation || selectedFinding.explanation || selectedFinding.message}
              </div>

              {/* Data Flow Section (if taint path exists) */}
              {selectedFinding.taint_path && selectedFinding.taint_path.length > 0 && (
                <div style={sectionBoxStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={sectionTitleStyle}>Taint Flow Analysis</span>
                    <button
                      style={{
                        ...flowToggleBtnStyle,
                        backgroundColor: isDataFlowActive ? 'var(--accent)' : 'var(--panel-2)',
                        color: isDataFlowActive ? 'var(--text-on-accent)' : 'var(--text-secondary)',
                      }}
                      onClick={() => onToggleDataFlow(selectedFinding.id)}
                    >
                      <GitBranch size={13} />
                      {isDataFlowActive ? 'Hide Flow' : 'Show Flow in Editor'}
                    </button>
                  </div>
                  <TaintPath steps={selectedFinding.taint_path} onJumpToStep={onJumpToStep} />
                </div>
              )}

              {/* Automated Fixes Section */}
              <div style={sectionBoxStyle}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={sectionTitleStyle}>
                    {selectedFinding.fixes && selectedFinding.fixes.length > 0 ? 'Suggested Fixes' : 'Rule Advice'}
                  </span>
                  <button
                    data-qa="ask-ai-fix-btn"
                    disabled={!llmConfigured || isAskingAI}
                    title={
                      llmConfigured
                        ? `Ask AI (${llmProvider}) for alternative fix`
                        : 'No AI provider configured in .env (set ANTHROPIC_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY)'
                    }
                    style={{
                      ...reviewFixBtnStyle,
                      opacity: llmConfigured ? 1 : 0.55,
                      cursor: llmConfigured ? 'pointer' : 'not-allowed',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                    onClick={() => onAskAIFix?.(selectedFinding)}
                  >
                    <Sparkles size={12} />
                    {isAskingAI ? 'Asking AI...' : 'Ask AI for another fix'}
                  </button>
                </div>

                {selectedFinding.fixes && selectedFinding.fixes.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                    {selectedFinding.fixes.map((fix) => {
                      const isVerified = Boolean(fix.verification?.verified);
                      const isSafe = fix.confidence === 'safe';
                      const hasEdits = Boolean(fix.edits && fix.edits.length > 0);
                      const isLLM = fix.kind === 'llm';

                      return (
                        <div key={fix.id} style={fixCardStyle}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span style={fixTitleStyle}>{fix.title}</span>
                                {isLLM && (
                                  <span
                                    style={{
                                      padding: '1px 5px',
                                      borderRadius: '3px',
                                      fontSize: '10px',
                                      fontWeight: 600,
                                      backgroundColor: 'var(--accent-subtle)',
                                      color: 'var(--accent)',
                                    }}
                                  >
                                    AI
                                  </span>
                                )}
                                {isVerified && isSafe ? (
                                  <span style={verifiedBadgeStyle}>
                                    <ShieldCheck size={11} />
                                    Verified after re-analysis
                                  </span>
                                ) : isLLM && !isVerified ? (
                                  <span style={unverifiedBadgeStyle}>Advice only (Unverified AI suggestion)</span>
                                ) : (
                                  <span style={unverifiedBadgeStyle}>Review needed</span>
                                )}
                              </div>
                              <p style={fixDescStyle}>{fix.description}</p>
                            </div>
                          </div>

                          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px', gap: '6px' }}>
                            {hasEdits && (
                              <button
                                style={reviewFixBtnStyle}
                                onClick={() => onOpenDiff(fix, selectedFinding)}
                                title="Preview unified diff"
                              >
                                Review Diff
                              </button>
                            )}

                            {((isSafe && isVerified) || (fix.confidence === 'review' && hasEdits) || (isLLM && isVerified && hasEdits)) && (
                              <button
                                style={applyFixBtnStyle}
                                onClick={() => onApplyFix(fix, selectedFinding)}
                                title={isSafe && isVerified ? 'Apply verified fix' : 'Apply fix'}
                              >
                                <Wand2 size={12} />
                                {isVerified ? 'Apply Verified Fix' : 'Apply Fix'}
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ marginTop: '6px', fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    <p style={{ margin: '0 0 6px', fontStyle: 'italic' }}>No automatic rule fix for this issue.</p>
                  </div>
                )}
              </div>

              <details style={{ marginTop: 'auto' }}>
                <summary style={{ cursor: 'pointer', color: 'var(--muted)', fontSize: 11 }}>More actions</summary>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                  <button
                    data-qa="suppress-finding-btn"
                    style={feedbackBtnStyle}
                    onClick={() => onSuppressFinding?.(selectedFinding)}
                    title="Insert inline suppression comment in code"
                  >
                    <EyeOff size={13} /> Suppress this finding
                  </button>
                  <button style={feedbackBtnStyle} onClick={() => onMarkFalsePositive(selectedFinding)}>
                    <Flag size={13} /> Mark as False Positive
                  </button>
                </div>
              </details>
            </div>
          ) : (
            <div style={noFindingStyle}>
              <CheckCircle2 size={32} color="var(--muted)" />
              <p style={{ marginTop: '12px', color: 'var(--muted)', fontSize: '13px' }}>
                Select a problem from the bottom panel or click a code squiggle to view vulnerability analysis.
              </p>
            </div>
          )}
          </>
        )}

        {activeTab === 'tokens' && <TokensPanel result={analysis} language={language} selectedIndex={selectedTokenIndex} selectedFindingId={selectedFinding?.id || null} mlMode={mlMode} ml={mlInsights} loadingML={isLoadingInsights} onSelectToken={onSelectToken} onSelectFinding={onSelectFindingById} onLoadML={onLoadTokenML} tokenMap={tokenMap} onTokenMap={onTokenMap} category={tokenCategory} onCategoryChange={onTokenCategory} showAll={showAllTokens} mainFilter={tokenMainFilter} groups={tokenGroups} />}

        {activeTab === 'taint' && (selectedFinding?.taint_path?.length ? <TaintPath steps={selectedFinding.taint_path} engine={engine?.taint} isEditorActive={isDataFlowActive} onToggleEditor={() => onToggleDataFlow(selectedFinding.id)} onJumpToStep={onJumpToStep} /> : <div style={{ color:'var(--text-muted)', padding:12 }}>No data-flow path for this token.</div>)}

        {activeTab === 'summary' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {!summary ? <div className="ui5-empty">Open or paste code to analyse it.</div> : <>
              <div className="ui6-summary-grid">
                {[['Score',summary.score],['Critical',summary.critical],['High',summary.high],['Lexical',summary.lexical_errors ?? 0]].map(([label,value])=><div className="ui6-summary-tile" key={label}><span>{label}</span><strong>{value}</strong></div>)}
              </div>
              {(summary.medium>0||summary.low>0)&&<div className="ui6-summary-grid secondary">{summary.medium>0&&<div className="ui6-summary-tile"><span>Medium</span><strong>{summary.medium}</strong></div>}{summary.low>0&&<div className="ui6-summary-tile"><span>Low</span><strong>{summary.low}</strong></div>}</div>}
              <p className="ui6-summary-note">Lexical errors are listed separately and do not change the score.</p>
              <div className="ui6-summary-meta">{summary.tokens_total} tokens analysed · {engine?.elapsed_ms.toFixed(0) ?? '—'} ms · {language} · {engine?.parser || 'lexer-only'}</div>
            </>}
          </div>
        )}

        {activeTab === 'ml' && (
          <MlInsights
            insights={mlInsights}
            isLoading={isLoadingInsights}
            mlMode={mlMode}
            modelId={engine?.ml_model_id}
            selectedToken={analysis?.tokens?.[selectedTokenIndex ?? -1]?.token ?? analysis?.tokens?.[selectedTokenIndex ?? -1]?.text ?? undefined}
            lexicalError={Boolean(analysis && selectedTokenIndex !== null && analysis.findings.some((finding) => finding.kind === 'lexical' && (() => { const token=analysis.tokens[selectedTokenIndex]; return Boolean(token?.range && token.range.start_line <= finding.range.end_line && token.range.end_line >= finding.range.start_line && (token.range.start_line !== finding.range.end_line || token.range.start_col < finding.range.end_col) && (finding.range.start_line !== token.range.end_line || finding.range.start_col < token.range.end_col)); })()))}
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

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: 'var(--panel)',
  overflow: 'hidden',
};

const tabHeaderStyle: React.CSSProperties = {
  display: 'flex',
  height: '35px',
  minHeight: '35px',
  borderBottom: '1px solid var(--border)',
  backgroundColor: 'var(--panel-2)',
  padding: '0 8px',
};

const tabButtonStyle: React.CSSProperties = {
  flex: 1,
  fontSize: '12px',
  fontWeight: 600,
  padding: '7px 9px',
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const tabContentStyle: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  padding: '16px',
};

const findingContainerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '14px',
  minHeight: '100%',
};

const findingHeaderStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '4px',
};

const sevBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '11px',
  fontWeight: 700,
  padding: '2px 8px',
  borderRadius: 'var(--radius-sm)',
};

const ruleCodeStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '11px',
  color: 'var(--accent)',
  backgroundColor: 'var(--panel-2)',
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
};

const titleStyle: React.CSSProperties = {
  fontSize: '15px',
  fontWeight: 700,
  color: 'var(--text)',
  marginTop: '4px',
  lineHeight: 1.3,
};

const locationSubStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  fontFamily: 'var(--font-code)',
};

const sectionBoxStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '6px',
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
};

const explanationTextStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text-secondary)',
  lineHeight: 1.5,
};

const flowToggleBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
  fontSize: '11px',
  fontWeight: 600,
  padding: '4px 10px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
  cursor: 'pointer',
};

const fixCardStyle: React.CSSProperties = {
  padding: '10px 12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
};

const fixTitleStyle: React.CSSProperties = {
  fontSize: '13px',
  fontWeight: 600,
  color: 'var(--text)',
};

const verifiedBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '3px',
  fontSize: '10px',
  fontWeight: 600,
  color: 'var(--success)',
  backgroundColor: 'var(--success-wash)',
  padding: '1px 6px',
  borderRadius: 'var(--radius-full)',
};

const unverifiedBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '3px',
  fontSize: '10px',
  fontWeight: 600,
  color: 'var(--medium)',
  backgroundColor: 'var(--warning-wash)',
  padding: '1px 6px',
  borderRadius: 'var(--radius-full)',
};

const fixDescStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  marginTop: '4px',
  lineHeight: 1.4,
};

const applyFixBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
  fontSize: '11px',
  fontWeight: 600,
  padding: '5px 12px',
  backgroundColor: 'var(--accent)',
  color: 'var(--text-on-accent)',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
};

const reviewFixBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
  fontSize: '11px',
  fontWeight: 600,
  padding: '5px 12px',
  backgroundColor: 'var(--panel-3)',
  color: 'var(--text)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
};

const feedbackBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '6px',
  width: '100%',
  padding: '8px 12px',
  backgroundColor: 'transparent',
  border: '1px dashed var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--muted)',
  fontSize: '11px',
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
};

const noFindingStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%',
  padding: '32px 16px',
  textAlign: 'center',
};
