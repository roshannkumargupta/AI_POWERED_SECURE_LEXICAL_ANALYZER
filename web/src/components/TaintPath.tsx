import React from 'react';
import { ArrowDown, CornerDownRight } from 'lucide-react';
import { TaintPathStep } from '../api/client';

interface TaintPathProps {
  steps: TaintPathStep[];
  onJumpToStep: (step: TaintPathStep) => void;
}

export const TaintPath: React.FC<TaintPathProps> = ({ steps, onJumpToStep }) => {
  if (!steps || steps.length === 0) {
    return (
      <div style={emptyStyle}>
        <span>No data flow trace recorded for this finding.</span>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <span style={titleStyle}>Source-to-Sink Data Flow Trace</span>
        <span style={stepCountStyle}>{steps.length} steps</span>
      </div>

      <div style={timelineStyle}>
        {steps.map((step, idx) => {
          const isSource = step.step === 'source';
          const isSink = step.step === 'sink';
          const isMissingSanitizer = step.step === 'sanitizer_missing';

          let stepColor = 'var(--medium)';
          let stepLabel = 'PROPAGATE';

          if (isSource) {
            stepColor = 'var(--low)';
            stepLabel = 'SOURCE';
          } else if (isSink) {
            stepColor = 'var(--critical)';
            stepLabel = 'SINK';
          } else if (isMissingSanitizer) {
            stepColor = 'var(--high)';
            stepLabel = 'MISSING SANITIZER';
          }

          return (
            <React.Fragment key={idx}>
              <div
                style={{
                  ...stepCardStyle,
                  borderColor: isSource
                    ? 'rgba(92, 200, 255, 0.4)'
                    : isSink
                    ? 'rgba(255, 77, 109, 0.4)'
                    : 'var(--border)',
                }}
                onClick={() => onJumpToStep(step)}
                title="Click to jump to line in editor"
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') onJumpToStep(step);
                }}
              >
                <div style={stepTopRowStyle}>
                  <div style={stepBadgeGroupStyle}>
                    <span
                      style={{
                        ...numberBadgeStyle,
                        backgroundColor: stepColor,
                      }}
                    >
                      {idx + 1}
                    </span>
                    <span
                      style={{
                        ...labelBadgeStyle,
                        color: stepColor,
                        backgroundColor: `${stepColor}20`,
                      }}
                    >
                      {stepLabel}
                    </span>
                  </div>
                  <span style={locStyle}>
                    Ln {step.range.start_line}, Col {step.range.start_col}
                  </span>
                </div>

                <div style={codeSnippetStyle}>
                  <code>{step.text}</code>
                </div>

                {step.note && <div style={noteStyle}>{step.note}</div>}

                <div style={jumpHintStyle}>
                  <CornerDownRight size={12} color="var(--muted)" />
                  <span>Jump to code</span>
                </div>
              </div>

              {idx < steps.length - 1 && (
                <div style={arrowWrapperStyle}>
                  <ArrowDown size={14} color="var(--muted-dark)" />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '10px',
  marginTop: '8px',
};

const emptyStyle: React.CSSProperties = {
  padding: '16px',
  color: 'var(--muted)',
  fontStyle: 'italic',
  fontSize: '12px',
  textAlign: 'center',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
};

const titleStyle: React.CSSProperties = {
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
};

const stepCountStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  backgroundColor: 'var(--panel-2)',
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
};

const timelineStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'stretch',
};

const stepCardStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '6px',
  padding: '10px 12px',
  background: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
};

const stepTopRowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
};

const stepBadgeGroupStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
};

const numberBadgeStyle: React.CSSProperties = {
  width: '18px',
  height: '18px',
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '10px',
  fontWeight: 700,
  color: '#0B0F17',
};

const labelBadgeStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 700,
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
  letterSpacing: '0.3px',
};

const locStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  fontFamily: 'var(--font-code)',
};

const codeSnippetStyle: React.CSSProperties = {
  padding: '6px 8px',
  background: 'var(--bg)',
  borderRadius: 'var(--radius-sm)',
  fontFamily: 'var(--font-code)',
  fontSize: '12px',
  color: 'var(--text)',
  overflowX: 'auto',
  border: '1px solid var(--border)',
};

const noteStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--text-secondary)',
  lineHeight: 1.4,
};

const jumpHintStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '10px',
  color: 'var(--muted)',
  marginTop: '2px',
};

const arrowWrapperStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '4px 0',
};
