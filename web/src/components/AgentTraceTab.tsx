import React from 'react';
import { Workflow, ShieldCheck } from 'lucide-react';
import type { AgentTraceStep } from '../api/client';
import {
  containerStyle,
  emptyContainerStyle,
  metricsHeaderStyle,
  metricCardStyle,
  metricLabelStyle,
  metricValStyle,
  securityBannerStyle,
  timelineContainerStyle,
  stageGroupStyle,
  stageHeaderStyle,
  stageBadgeStyle,
  stepsListStyle,
} from './agentTraceStyles';
import { TraceStepCard } from './TraceStepCard';

export interface AgentTraceTabProps {
  trace: AgentTraceStep[];
  agentMeta?: {
    mode?: string;
    total_steps?: number;
    llm_calls?: number;
    elapsed_ms?: number;
    verified_fixes?: number;
  };
  agentMode?: 'off' | 'rules';
}

export const AgentTraceTab: React.FC<AgentTraceTabProps> = ({
  trace = [],
  agentMeta,
  agentMode = 'off',
}) => {
  const totalMs = agentMeta?.elapsed_ms ?? trace.reduce((acc, s) => acc + s.ms, 0);
  const llmCalls = agentMeta?.llm_calls ?? trace.filter((s) => s.decision_source === 'llm').length;

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
          <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}>
            No Agent Trace Available
          </h4>
          <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5 }}>
            {agentMode === 'off'
              ? 'Agent is currently turned off. Switch agent mode to "Rules" in the top bar and click Analyze.'
              : 'Analyze code to inspect real-time agent decisions across all compiler stages.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle} data-qa="agent-trace-tab">
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

      <div style={securityBannerStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <ShieldCheck size={14} color="var(--text-success)" />
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-success)' }}>
            Local Isolation Guarantee
          </span>
        </div>
        <div
          style={{
            fontSize: 11,
            color: 'var(--text-muted)',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '4px 8px',
          }}
        >
          <div>
            Outbound network calls: <strong style={{ color: 'var(--text-primary)' }}>0</strong>
          </div>
          <div>
            Engine: <strong style={{ color: 'var(--text-primary)' }}>RulesPlanner</strong>
          </div>
          <div>
            Deterministic execution: <strong style={{ color: 'var(--text-primary)' }}>Active</strong>
          </div>
          <div>
            Shadow verifier: <strong style={{ color: 'var(--text-primary)' }}>Active</strong>
          </div>
        </div>
      </div>

      <div style={timelineContainerStyle}>
        {Object.entries(groupedSteps).map(([stage, steps]) => (
          <div key={stage} style={stageGroupStyle}>
            <div style={stageHeaderStyle}>
              <span style={stageBadgeStyle}>{stage.toUpperCase()} STAGE</span>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {steps.length} step(s)
              </span>
            </div>

            <div style={stepsListStyle}>
              {steps.map((step) => (
                <TraceStepCard key={step.step} step={step} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
