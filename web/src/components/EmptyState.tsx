import React from 'react';
import { Shield } from 'lucide-react';
import { SampleItem } from '../api/client';

interface EmptyStateProps {
  samples: SampleItem[];
  onSelectSample: (sample: SampleItem) => void;
  onNewFile: () => void;
  onOpenFile: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  samples,
  onSelectSample,
  onNewFile,
  onOpenFile,
}) => {
  const exampleLanguages = [
    ['python', 'Python'],
    ['java', 'Java'],
    ['javascript', 'JavaScript'],
    ['cpp', 'C/C++'],
  ];
  const examples = exampleLanguages
    .map(([language, label]) => [
      label,
      samples.find((s) => s.language === language && s.category === 'vulnerable'),
    ])
    .filter((entry) => entry[1]) as Array<[string, SampleItem]>;

  return (
    <div style={containerStyle}>
      <div style={iconCircleStyle}>
        <Shield size={36} color="var(--accent)" />
      </div>

      <h2 style={titleStyle}>SecureLex</h2>
      <p style={subtitleStyle}>Open or paste code to check it for security problems.</p>

      <div style={buttonsGroupStyle}>
        <button style={sampleButtonStyle} onClick={onNewFile}>
          New file
        </button>
        <button style={sampleButtonStyle} onClick={onOpenFile}>
          Open file
        </button>
      </div>

      <div style={samplesBoxStyle}>
        <span style={samplesBoxTitleStyle}>Try an example:</span>
        <div style={exampleLinksStyle}>
          {examples.map(([label, sample]) => (
            <button key={sample.id} style={exampleLinkStyle} onClick={() => onSelectSample(sample)}>
              {label}
            </button>
          ))}
        </div>
      </div>
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
  backgroundColor: 'var(--accent-wash)',
  border: '1px solid var(--border-accent)',
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
  flexDirection: 'row',
  gap: '8px',
  width: '100%',
};

const exampleLinksStyle: React.CSSProperties = { display: 'flex', gap: 12 };
const exampleLinkStyle: React.CSSProperties = {
  color: 'var(--accent)',
  textDecoration: 'underline',
  cursor: 'pointer',
  fontSize: 12,
  background: 'transparent',
  border: 0,
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
