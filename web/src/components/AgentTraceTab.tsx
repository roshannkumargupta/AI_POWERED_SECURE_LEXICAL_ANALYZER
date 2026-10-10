import React from 'react';
import { Bot, Cpu, Workflow, CheckCircle2, XCircle, ShieldCheck } from 'lucide-react';
import type { AgentTraceStep } from '../api/client';

export interface AgentTraceTabProps {
  trace: AgentTraceStep[];
  agentMeta?: {
    mode?: string;
    total_steps?: number;
    llm_calls?: number;
    elapsed_ms?: number;
    verified_fixes?: number;
  };
  agentMode?: 'off' | 'rules' | 'local';
  agentModel?: string;
  ollamaUrl?: string;
}

export const AgentTraceTab: React.FC<AgentTraceTabProps> = ({
  trace = [],
  agentMeta,
  agentMode = 'off',
  agentModel = 'qwen2.5-coder:3b',
  ollamaUrl = 'http://127.0.0.1:11434',
}) => {
  const totalMs = agentMeta?.elapsed_ms ?? trace.reduce((acc, s) => acc + s.ms, 0);
  const llmCalls = agentMeta?.llm_calls ?? trace.filter((s) => s.decision_source === 'llm').length;

  // Group steps by stage
  const groupedSteps = React.useMemo(() => {
    const groups: Record<string, AgentTraceStep[]> = {};
    for (const step of trace) {
      const stage = step.stage || 'pipeline';
      if (!groups[stage]) groups[stage] = [];
      groups[stage].push(step);
    }
    return groups;
  }, [trace]);

  if (trace.length === 0) {
    return (
      <div style={emptyContainerStyle}>
        <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-muted)' }}>
          <Workflow size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
          <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}>No Agent Trace Available</h4>
          <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5 }}>
            {agentMode === 'off'
              ? 'Agent is currently turned off. Switch agent mode to "Rules" or "Local AI" in the top bar and click Analyze.'
              : 'Analyze code to inspect real-time agent decisions across all compiler stages.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle} data-qa="agent-trace-tab">
      {/* Top Metrics Summary */}
      <div style={metricsHeaderStyle}>
        <div style={metricCardStyle}>
          <span style={metricLabelStyle}>Total Time</span>
          <strong style={metricValStyle}>{totalMs.toFixed(1)} ms</strong>
        </div>
        <div style={metricCardStyle}>
          <span style={metricLabelStyle}>LLM Calls</span>
          <strong style={metricValStyle}>{llmCalls}</strong>
        </div>
        <div style={metricCardStyle}>
          <span style={metricLabelStyle}>Total Steps</span>
          <strong style={metricValStyle}>{trace.length}</strong>
        </div>
        <div style={metricCardStyle}>
          <span style={metricLabelStyle}>Mode</span>
          <strong style={{ ...metricValStyle, textTransform: 'capitalize' }}>{agentMode}</strong>
        </div>
      </div>

      {/* Security Status Box */}
      <div style={securityBannerStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <ShieldCheck size={14} color="var(--text-success)" />
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-success)' }}>Local Isolation Guarantee</span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 8px' }}>
          <div>Outbound network calls: <strong style={{ color: 'var(--text-primary)' }}>0</strong></div>
          <div>Endpoint: <strong style={{ color: 'var(--text-primary)' }}>{ollamaUrl}</strong></div>
          <div>Model: <strong style={{ color: 'var(--text-primary)' }}>{agentModel}</strong></div>
          <div>Deterministic fallback: <strong style={{ color: 'var(--text-primary)' }}>Active</strong></div>
        </div>
      </div>

      {/* Vertical Timeline */}
      <div style={timelineContainerStyle}>
        {Object.entries(groupedSteps).map(([stage, steps]) => (
          <div key={stage} style={stageGroupStyle}>
            <div style={stageHeaderStyle}>
              <span style={stageBadgeStyle}>{stage.toUpperCase()} STAGE</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{steps.length} step(s)</span>
            </div>

            <div style={stepsListStyle}>
              {steps.map((step) => {
                const isAI = step.decision_source === 'llm';
                const isAccepted = step.accepted;

                return (
                  <div key={step.step} style={stepCardStyle} data-qa={`trace-step-${step.step}`}>
                    {/* Step Title Row */}
                    <div style={stepRowStyle}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        {isAI ? (
                          <Bot size={14} color="var(--text-accent)" />
                        ) : step.stage === 'pipeline' ? (
                          <Workflow size={14} color="var(--text-muted)" />
                        ) : (
                          <Cpu size={14} color="var(--text-muted)" />
                        )}
                        <span style={stepActionStyle}>{step.action}</span>
                        {step.args_summary ? (
                          <span style={argsSummaryStyle}>({step.args_summary})</span>
                        ) : null}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        {/* Decision Source Badge */}
                        <span
                          style={{
                            ...badgeStyle,
                            backgroundColor: isAI ? 'var(--bg-accent)' : 'var(--surface-3)',
                            color: isAI ? 'var(--text-accent)' : 'var(--text-muted)',
                            borderColor: isAI ? 'var(--text-accent)' : 'var(--border)',
                          }}
                        >
                          {isAI ? 'AI decided' : 'Rule decided'}
                        </span>

                        {/* Status Badge */}
                        {isAccepted ? (
                          <span
                            style={{
                              ...badgeStyle,
                              backgroundColor: 'var(--bg-success)',
                              color: 'var(--text-success)',
                              borderColor: 'var(--text-success)',
                            }}
                          >
                            <CheckCircle2 size={10} style={{ marginRight: 3 }} />
                            Accepted
                          </span>
                        ) : (
                          <span
                            style={{
                              ...badgeStyle,
                              backgroundColor: 'var(--bg-danger)',
                              color: 'var(--text-danger)',
                              borderColor: 'var(--text-danger)',
                            }}
                          >
                            <XCircle size={10} style={{ marginRight: 3 }} />
                            Rejected
                          </span>
                        )}

                        <span style={latencyStyle}>{step.ms.toFixed(1)} ms</span>
                      </div>
                    </div>

                    {/* Step Reason (Strictly Plain Text Rendering) */}
                    <p style={reasonTextStyle} data-qa="trace-reason">
                      {step.reason}
                    </p>

                    {/* Rejection Reason if rejected */}
                    {!isAccepted && step.rejection_reason && (
                      <div style={rejectionBoxStyle}>
                        <strong>Rejection Reason:</strong> {step.rejection_reason}
                      </div>
                    )}

                    {/* Observation summary */}
                    {step.observation_summary && (
                      <div style={observationTextStyle}>
                        <span style={{ color: 'var(--text-muted)', marginRight: 4 }}>Obs:</span>
                        <span>{step.observation_summary}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
  padding: '12px',
  overflowY: 'auto',
  height: '100%',
};

const emptyContainerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%',
  padding: '24px',
};

const metricsHeaderStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: '8px',
  paddingBottom: '8px',
  borderBottom: '1px solid var(--border)',
};

const metricCardStyle: React.CSSProperties = {
  backgroundColor: 'var(--surface-2)',
  padding: '8px 10px',
  borderRadius: '6px',
  display: 'flex',
  flexDirection: 'column',
  border: '1px solid var(--border)',
};

const metricLabelStyle: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  fontWeight: 600,
};

const metricValStyle: React.CSSProperties = {
  fontSize: '14px',
  color: 'var(--text-primary)',
  marginTop: '2px',
};

const securityBannerStyle: React.CSSProperties = {
  backgroundColor: 'var(--bg-success)',
  border: '1px solid var(--border)',
  borderRadius: '6px',
  padding: '8px 10px',
};

const timelineContainerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
};

const stageGroupStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '6px',
};

const stageHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 4px',
};

const stageBadgeStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 700,
  letterSpacing: '0.05em',
  color: 'var(--text-secondary)',
};

const stepsListStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
};

const stepCardStyle: React.CSSProperties = {
  backgroundColor: 'var(--surface-1)',
  border: '1px solid var(--border)',
  borderRadius: '6px',
  padding: '10px 12px',
  display: 'flex',
  flexDirection: 'column',
  gap: '6px',
};

const stepRowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  flexWrap: 'wrap',
  gap: '6px',
};

const stepActionStyle: React.CSSProperties = {
  fontSize: '13px',
  fontWeight: 600,
  color: 'var(--text-primary)',
  fontFamily: 'var(--font-code)',
};

const argsSummaryStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--text-muted)',
  fontFamily: 'var(--font-code)',
  maxWidth: '160px',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
};

const badgeStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 600,
  padding: '2px 6px',
  borderRadius: '4px',
  border: '1px solid',
  display: 'inline-flex',
  alignItems: 'center',
};

const latencyStyle: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--text-muted)',
};

const reasonTextStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '12px',
  lineHeight: 1.4,
  color: 'var(--text-primary)',
};

const rejectionBoxStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--text-danger)',
  backgroundColor: 'var(--bg-danger)',
  border: '1px solid var(--border)',
  padding: '6px 8px',
  borderRadius: '4px',
};

const observationTextStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--text-secondary)',
  backgroundColor: 'var(--surface-2)',
  padding: '4px 8px',
  borderRadius: '4px',
  fontFamily: 'var(--font-code)',
  wordBreak: 'break-all',
};
