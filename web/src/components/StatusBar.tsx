import React from 'react';
import { Sparkles, AlertCircle, Cpu, Clock, MapPin } from 'lucide-react';
import { EngineMetadata } from '../api/client';

interface StatusBarProps {
  language: string;
  engine: EngineMetadata | null;
  cursorPosition: { line: number; col: number };
  isAnalyzing: boolean;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  language,
  engine,
  cursorPosition,
  isAnalyzing,
}) => {
  const mlMode = engine?.ml_mode ?? 'on';
  const taintType = engine?.taint ?? 'ast';
  const elapsedMs = engine?.elapsed_ms;

  return (
    <footer style={containerStyle}>
      {/* Left Telemetry Section */}
      <div style={sectionStyle}>
        <div style={itemStyle}>
          <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
            {language ? language.toUpperCase() : 'PYTHON'}
          </span>
        </div>

        {/* ML Mode Pill */}
        <div
          style={{
            ...pillStyle,
            backgroundColor: mlMode === 'on' ? 'rgba(61, 220, 151, 0.15)' : 'rgba(255, 77, 109, 0.18)',
            color: mlMode === 'on' ? 'var(--success)' : 'var(--critical)',
            borderColor: mlMode === 'on' ? 'rgba(61, 220, 151, 0.35)' : 'rgba(255, 77, 109, 0.4)',
          }}
          title={
            mlMode === 'on'
              ? 'Machine learning inference is active with calibrated token windows'
              : 'Machine learning model is offline. Operating strictly on AST rules & taint flow.'
          }
        >
          {mlMode === 'on' ? (
            <>
              <Sparkles size={11} />
              <span>ML on</span>
            </>
          ) : (
            <>
              <AlertCircle size={11} />
              <span>ML off - rules + taint only</span>
            </>
          )}
        </div>

        {/* Taint Engine */}
        <div style={itemStyle}>
          <Cpu size={12} color="var(--muted)" />
          <span style={textMutedStyle}>Taint: {taintType.toUpperCase()} Engine</span>
        </div>
      </div>

      {/* Right Metrics Section */}
      <div style={sectionStyle}>
        {/* Latency */}
        <div style={itemStyle}>
          <Clock size={12} color="var(--muted)" />
          <span style={textMutedStyle}>
            {isAnalyzing ? 'Analyzing...' : elapsedMs !== undefined ? `${elapsedMs.toFixed(1)} ms` : '-- ms'}
          </span>
        </div>

        {/* Cursor Position */}
        <div style={itemStyle}>
          <MapPin size={12} color="var(--muted)" />
          <span style={coordStyle}>
            Ln {cursorPosition.line}, Col {cursorPosition.col}
          </span>
        </div>
      </div>
    </footer>
  );
};

const containerStyle: React.CSSProperties = {
  height: '24px',
  minHeight: '24px',
  maxHeight: '24px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 12px',
  backgroundColor: 'var(--panel-2)',
  borderTop: '1px solid var(--border)',
  fontSize: '11px',
  color: 'var(--muted)',
  userSelect: 'none',
  zIndex: 20,
};

const sectionStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '14px',
};

const itemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
};

const pillStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  padding: '1px 6px',
  borderRadius: 'var(--radius-full)',
  border: '1px solid transparent',
  fontSize: '10px',
  fontWeight: 600,
  letterSpacing: '0.2px',
};

const textMutedStyle: React.CSSProperties = {
  color: 'var(--muted)',
  fontSize: '11px',
};

const coordStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  color: 'var(--text-secondary)',
};
