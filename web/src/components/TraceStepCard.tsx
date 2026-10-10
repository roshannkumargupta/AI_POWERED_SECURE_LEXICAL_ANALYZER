import React from 'react';
import { Bot, Cpu, Workflow, CheckCircle2, XCircle } from 'lucide-react';
import type { AgentTraceStep } from '../api/client';
import {
  stepCardStyle,
  stepRowStyle,
  stepActionStyle,
  argsSummaryStyle,
  badgeStyle,
  latencyStyle,
  reasonTextStyle,
  rejectionBoxStyle,
  observationTextStyle,
} from './agentTraceStyles';

interface TraceStepCardProps {
  step: AgentTraceStep;
}

export const TraceStepCard: React.FC<TraceStepCardProps> = ({ step }) => {
  const isAI = step.decision_source === 'llm';
  const isAccepted = step.accepted;

  return (
    <div style={stepCardStyle} data-qa={`trace-step-${step.step}`}>
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
          {step.args_summary ? <span style={argsSummaryStyle}>({step.args_summary})</span> : null}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
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

      <p style={reasonTextStyle} data-qa="trace-reason">
        {step.reason}
      </p>

      {!isAccepted && step.rejection_reason && (
        <div style={rejectionBoxStyle}>
          <strong>Rejection Reason:</strong> {step.rejection_reason}
        </div>
      )}

      {step.observation_summary && (
        <div style={observationTextStyle}>
          <span style={{ color: 'var(--text-muted)', marginRight: 4 }}>Obs:</span>
          <span>{step.observation_summary}</span>
        </div>
      )}
    </div>
  );
};
