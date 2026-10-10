import React from 'react';
import { Clock } from 'lucide-react';
import { EngineMetadata } from '../api/client';

interface StatusBarProps {
  engine: EngineMetadata | null;
  cursorPosition: { line: number; col: number };
  isAnalyzing: boolean;
  findingCount?: number;
  analysisReady?: boolean;
  lexicalCount?: number;
  syntaxCount?: number;
  parser?: string;
  onRetry?: () => void;
  analysisFailed?: boolean;
  fileState?: 'not analysed' | 'analysing' | 'analysed' | 'stale' | 'error';
  agentMode?: 'off' | 'rules' | 'local';
  agentModel?: string;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  engine,
  cursorPosition,
  isAnalyzing,
  findingCount = 0,
  analysisReady: _analysisReady = false,
  lexicalCount = 0, syntaxCount = 0, parser, onRetry, analysisFailed = false,
  fileState = 'not analysed',
  agentMode = 'off',
  agentModel = 'qwen2.5-coder:3b',
}) => {
  const mlMode = engine?.ml_mode ?? 'on';
  const taintType = engine?.taint ?? 'ast';
  const elapsedMs = engine?.elapsed_ms;

  const statePill = () => {
    if (analysisFailed || fileState === 'error') {
      return <button style={textMutedStyle} onClick={onRetry}>Analysis failed - Retry</button>;
    }
    if (fileState === 'analysing' || isAnalyzing) {
      return <span style={{ ...pillStyle, color: 'var(--text-neutral)', background: 'var(--bg-neutral)' }}>Analysing...</span>;
    }
    if (fileState === 'stale') {
      return <span style={{ ...pillStyle, color: 'var(--text-warning)', background: 'var(--bg-warning)' }}>Edited since last analysis - press Analyze</span>;
    }
    if (fileState === 'analysed') {
      return <span style={{ ...pillStyle, color: 'var(--text-success)', background: 'var(--bg-success)' }}>Analysed {elapsedMs !== undefined ? `${elapsedMs.toFixed(0)} ms` : ''}</span>;
    }
    return <span style={{ ...pillStyle, color: 'var(--muted)', background: 'var(--surface-2)' }}>Not analysed - press Analyze</span>;
  };

  const agentPill = () => {
    let text = 'Agent: off';
    let color = 'var(--text-muted)';
    if (agentMode === 'local') {
      text = `Agent: local AI (${agentModel || 'qwen2.5-coder:3b'})`;
      color = 'var(--text-success)';
    } else if (agentMode === 'rules') {
      text = 'Agent: rules';
      color = 'var(--text-accent)';
    }
    return (
      <span
        data-qa="status-agent-pill"
        style={{ ...pillStyle, color, borderColor: color }}
      >
        {text}
      </span>
    );
  };

  return (
    <footer data-qa="status" style={containerStyle}>
      {/* Left Telemetry Section */}
      <div style={sectionStyle}>
        <span style={pillStyle}>{parser || engine?.parser || 'lexer-only'}</span>
        <span style={pillStyle}>taint {taintType}</span>
        <span style={{...pillStyle,color:mlMode==='on'?'var(--text-success)':'var(--text-danger)',background:mlMode==='on'?'var(--bg-success)':'var(--bg-danger)'}} title={mlMode === 'off' ? 'ML unavailable; rules and taint remain active.' : `Model ${engine?.ml_model_id || 'available'}`}>{mlMode==='on'?'ML on':'ML off'}</span>
        {agentPill()}
        {statePill()}
      </div>

      {/* Right Metrics Section */}
      <div style={sectionStyle}>
        {/* Latency */}
        <div style={itemStyle}>
          <Clock size={12} color="var(--muted)" />
          <span style={textMutedStyle}>{elapsedMs !== undefined ? `${elapsedMs.toFixed(0)} ms` : '-- ms'}</span>
        </div>

        <span style={coordStyle}>Security {findingCount} - Lexical {lexicalCount} - Syntax {syntaxCount} - Ln {cursorPosition.line}, Col {cursorPosition.col}</span>
      </div>
    </footer>
  );
};

const containerStyle: React.CSSProperties = {
  height: '35px',
  minHeight: '35px',
  maxHeight: '35px',
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
  gap: '8px',
};

const itemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
};

const pillStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  padding: '1px 7px',
  borderRadius: 'var(--radius-full)',
  border: '1px solid transparent',
  fontSize: '10px',
  fontWeight: 600,
  letterSpacing: '0.2px',
  lineHeight: '16px',
};

const textMutedStyle: React.CSSProperties = {
  color: 'var(--muted)',
  fontSize: '11px',
};

const coordStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  color: 'var(--text-secondary)',
};
