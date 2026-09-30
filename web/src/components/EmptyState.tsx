import React from 'react';
import { Shield, Sparkles, AlertOctagon, Terminal } from 'lucide-react';
import { SampleItem } from '../api/client';

interface EmptyStateProps {
  samples: SampleItem[];
  onSelectSample: (sample: SampleItem) => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ samples, onSelectSample }) => {
  const threeSamples = samples.slice(0, 3);

  return (
    <div style={containerStyle}>
      <div style={iconCircleStyle}>
        <Shield size={36} color="var(--accent)" />
      </div>

      <h2 style={titleStyle}>Welcome to SecureLex IDE</h2>
      <p style={subtitleStyle}>
        Interactive static code security analysis fusing deterministic AST rules, taint flow tracking, and calibrated machine learning with verified automated fixes.
      </p>

      <div style={samplesBoxStyle}>
        <span style={samplesBoxTitleStyle}>Load a security demonstration sample:</span>
        <div style={buttonsGroupStyle}>
          {threeSamples.map((sample) => (
            <button
              key={sample.id}
              style={sampleButtonStyle}
              onClick={() => onSelectSample(sample)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {sample.category === 'vulnerable' ? (
                  <AlertOctagon size={16} color="var(--critical)" />
                ) : sample.category === 'adversarial' ? (
                  <Sparkles size={16} color="var(--high)" />
                ) : (
                  <Terminal size={16} color="var(--accent)" />
                )}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                  <span style={sampleBtnTitleStyle}>{sample.title}</span>
                  <span style={sampleBtnSubStyle}>{sample.filename}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <span style={footerHintStyle}>
        Or simply paste code directly into the Monaco editor or press <kbd style={kbdStyle}>Ctrl+Enter</kbd> to analyze.
      </span>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%',
  width: '100%',
  padding: '32px',
  textAlign: 'center',
  backgroundColor: 'var(--bg)',
};

const iconCircleStyle: React.CSSProperties = {
  width: '72px',
  height: '72px',
  borderRadius: '50%',
  backgroundColor: 'rgba(79, 140, 255, 0.1)',
  border: '1px solid rgba(79, 140, 255, 0.25)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: '16px',
};

const titleStyle: React.CSSProperties = {
  fontSize: '20px',
  fontWeight: 700,
  color: 'var(--text)',
  marginBottom: '8px',
};

const subtitleStyle: React.CSSProperties = {
  fontSize: '13px',
  color: 'var(--muted)',
  maxWidth: '520px',
  lineHeight: 1.5,
  marginBottom: '28px',
};

const samplesBoxStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '12px',
  maxWidth: '480px',
  width: '100%',
  marginBottom: '20px',
};

const samplesBoxTitleStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
};

const buttonsGroupStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  width: '100%',
};

const sampleButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '10px 14px',
  backgroundColor: 'var(--panel)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  transition: 'all var(--transition-fast)',
  cursor: 'pointer',
  textAlign: 'left',
};

const sampleBtnTitleStyle: React.CSSProperties = {
  fontSize: '13px',
  fontWeight: 600,
  color: 'var(--text)',
};

const sampleBtnSubStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  fontFamily: 'var(--font-code)',
};

const footerHintStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--muted-dark)',
};

const kbdStyle: React.CSSProperties = {
  padding: '2px 6px',
  background: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  fontFamily: 'var(--font-code)',
  fontSize: '11px',
  color: 'var(--text)',
};
