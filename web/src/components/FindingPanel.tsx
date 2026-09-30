import React from 'react';
import {
  AlertOctagon,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Flag,
  Wand2,
  GitBranch,
} from 'lucide-react';
import { Finding, Fix, AnalysisSummary, MLInsightsResponse, TaintPathStep } from '../api/client';
import { ScoreRing } from './ScoreRing';
import { TaintPath } from './TaintPath';
import { MlInsights } from './MlInsights';

interface FindingPanelProps {
  activeTab: 'finding' | 'summary' | 'ml';
  onChangeTab: (tab: 'finding' | 'summary' | 'ml') => void;
  selectedFinding: Finding | null;
  summary: AnalysisSummary | null;
  mlInsights: MLInsightsResponse | null;
  isLoadingInsights: boolean;
  mlMode: 'on' | 'off';
  onApplyFix: (fix: Fix, finding: Finding) => void;
  onOpenDiff: (fix: Fix, finding: Finding) => void;
  onJumpToStep: (step: TaintPathStep) => void;
  onToggleDataFlow: (findingId: string) => void;
  isDataFlowActive: boolean;
  onMarkFalsePositive: (finding: Finding) => void;
}

export const FindingPanel: React.FC<FindingPanelProps> = ({
  activeTab,
  onChangeTab,
  selectedFinding,
  summary,
  mlInsights,
  isLoadingInsights,
  mlMode,
  onApplyFix,
  onOpenDiff,
  onJumpToStep,
  onToggleDataFlow,
  isDataFlowActive,
  onMarkFalsePositive,
}) => {
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
    <div style={containerStyle}>
      {/* Tabs Header */}
      <div style={tabHeaderStyle}>
        <button
          style={{
            ...tabButtonStyle,
            borderBottom: activeTab === 'finding' ? '2px solid var(--accent)' : '2px solid transparent',
            color: activeTab === 'finding' ? 'var(--text)' : 'var(--muted)',
          }}
          onClick={() => onChangeTab('finding')}
        >
          Finding
        </button>
        <button
          style={{
            ...tabButtonStyle,
            borderBottom: activeTab === 'summary' ? '2px solid var(--accent)' : '2px solid transparent',
            color: activeTab === 'summary' ? 'var(--text)' : 'var(--muted)',
          }}
          onClick={() => onChangeTab('summary')}
        >
          Summary
        </button>
        <button
          style={{
            ...tabButtonStyle,
            borderBottom: activeTab === 'ml' ? '2px solid var(--accent)' : '2px solid transparent',
            color: activeTab === 'ml' ? 'var(--text)' : 'var(--muted)',
          }}
          onClick={() => onChangeTab('ml')}
        >
          ML Insights
        </button>
      </div>

      {/* Tab Content */}
      <div style={tabContentStyle}>
        {activeTab === 'finding' && (
          selectedFinding ? (
            <div style={findingContainerStyle}>
              {/* Finding Title & Badges */}
              <div style={findingHeaderStyle}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  {getSeverityBadge(selectedFinding)}
                  <code style={ruleCodeStyle}>{selectedFinding.rule_id}</code>
                </div>
                <h3 style={titleStyle}>{selectedFinding.title}</h3>
                <span style={locationSubStyle}>
                  Line {selectedFinding.range.start_line}, Col {selectedFinding.range.start_col}
                </span>
              </div>

              {/* Meta Grid */}
              <div style={metaGridStyle}>
                <div style={metaItemStyle}>
                  <span style={metaLabelStyle}>CWE Taxonomy</span>
                  <a
                    href={`https://cwe.mitre.org/data/definitions/${selectedFinding.cwe.replace('CWE-', '')}.html`}
                    target="_blank"
                    rel="noreferrer"
                    style={cweLinkStyle}
                  >
                    <span>{selectedFinding.cwe}</span>
                    <ExternalLink size={11} />
                  </a>
                </div>

                <div style={metaItemStyle}>
                  <span style={metaLabelStyle}>Calibrated Confidence</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={confValueStyle}>
                      {Math.round(selectedFinding.confidence * 100)}%
                    </span>
                    <div style={confBarTrackStyle}>
                      <div
                        style={{
                          ...confBarFillStyle,
                          width: `${Math.round(selectedFinding.confidence * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div style={{ ...metaItemStyle, gridColumn: 'span 2' }}>
                  <span style={metaLabelStyle}>Active Detectors ("Why?")</span>
                  <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '2px' }}>
                    {selectedFinding.sources?.map((src) => (
                      <span key={src} style={detectorBadgeStyle}>
                        {src}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Explanation */}
              <div style={sectionBoxStyle}>
                <span style={sectionTitleStyle}>Explanation</span>
                <p style={explanationTextStyle}>
                  {selectedFinding.explanation || selectedFinding.message}
                </p>
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
                        color: isDataFlowActive ? '#FFF' : 'var(--text-secondary)',
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
              {selectedFinding.fixes && selectedFinding.fixes.length > 0 && (
                <div style={sectionBoxStyle}>
                  <span style={sectionTitleStyle}>Automated Fix Proposals</span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                    {selectedFinding.fixes.map((fix) => {
                      const isVerified = fix.verification?.verified;
                      const isSafe = fix.confidence === 'safe';

                      return (
                        <div key={fix.id} style={fixCardStyle}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span style={fixTitleStyle}>{fix.title}</span>
                                {isVerified ? (
                                  <span style={verifiedBadgeStyle}>
                                    <ShieldCheck size={11} />
                                    Verified
                                  </span>
                                ) : (
                                  <span style={unverifiedBadgeStyle}>Review</span>
                                )}
                              </div>
                              <p style={fixDescStyle}>{fix.description}</p>
                            </div>
                          </div>

                          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px', gap: '6px' }}>
                            {fix.edits && fix.edits.length > 0 && (
                              <button
                                style={reviewFixBtnStyle}
                                onClick={() => onOpenDiff(fix, selectedFinding)}
                                title="Preview unified diff"
                              >
                                Review Diff
                              </button>
                            )}

                            {isSafe && (
                              <button
                                style={applyFixBtnStyle}
                                onClick={() => onApplyFix(fix, selectedFinding)}
                              >
                                <Wand2 size={12} />
                                Apply Verified Fix
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* False Positive Feedback */}
              <div style={{ marginTop: 'auto', paddingTop: '16px' }}>
                <button
                  style={feedbackBtnStyle}
                  onClick={() => onMarkFalsePositive(selectedFinding)}
                >
                  <Flag size={13} />
                  Mark as False Positive
                </button>
              </div>
            </div>
          ) : (
            <div style={noFindingStyle}>
              <CheckCircle2 size={32} color="var(--muted)" />
              <p style={{ marginTop: '12px', color: 'var(--muted)', fontSize: '13px' }}>
                Select a problem from the bottom panel or click a code squiggle to view vulnerability analysis.
              </p>
            </div>
          )
        )}

        {activeTab === 'summary' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <ScoreRing summary={summary} />
            {summary && (
              <div style={tokenSummaryBoxStyle}>
                <span style={sectionTitleStyle}>Analysis Metadata</span>
                <div style={summaryRowStyle}>
                  <span style={summaryLabelStyle}>Scanned Tokens:</span>
                  <span style={summaryValStyle}>{summary.tokens_total}</span>
                </div>
                <div style={summaryRowStyle}>
                  <span style={summaryLabelStyle}>Malicious Tokens:</span>
                  <span style={{ ...summaryValStyle, color: 'var(--critical)' }}>
                    {summary.tokens_malicious}
                  </span>
                </div>
                <div style={summaryRowStyle}>
                  <span style={summaryLabelStyle}>Suspicious Tokens:</span>
                  <span style={{ ...summaryValStyle, color: 'var(--medium)' }}>
                    {summary.tokens_suspicious}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'ml' && (
          <MlInsights
            insights={mlInsights}
            isLoading={isLoadingInsights}
            mlMode={mlMode}
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
  height: '36px',
  minHeight: '36px',
  borderBottom: '1px solid var(--border)',
  backgroundColor: 'var(--panel-2)',
  padding: '0 8px',
};

const tabButtonStyle: React.CSSProperties = {
  flex: 1,
  fontSize: '12px',
  fontWeight: 600,
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

const metaGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: '8px',
  padding: '10px 12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
};

const metaItemStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '2px',
};

const metaLabelStyle: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--muted)',
  textTransform: 'uppercase',
  fontWeight: 600,
  letterSpacing: '0.3px',
};

const cweLinkStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--accent)',
  textDecoration: 'none',
};

const confValueStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--text)',
};

const confBarTrackStyle: React.CSSProperties = {
  flex: 1,
  height: '5px',
  backgroundColor: 'var(--panel-3)',
  borderRadius: 'var(--radius-full)',
  overflow: 'hidden',
};

const confBarFillStyle: React.CSSProperties = {
  height: '100%',
  backgroundColor: 'var(--accent)',
  borderRadius: 'var(--radius-full)',
};

const detectorBadgeStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 600,
  fontFamily: 'var(--font-code)',
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--panel-3)',
  color: 'var(--text-secondary)',
  border: '1px solid var(--border)',
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
  backgroundColor: 'rgba(61, 220, 151, 0.15)',
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
  backgroundColor: 'rgba(245, 197, 66, 0.15)',
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
  color: '#FFFFFF',
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

const tokenSummaryBoxStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  padding: '12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
};

const summaryRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  fontSize: '12px',
};

const summaryLabelStyle: React.CSSProperties = {
  color: 'var(--muted)',
};

const summaryValStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  color: 'var(--text)',
  fontWeight: 600,
};
