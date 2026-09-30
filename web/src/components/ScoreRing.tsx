import React from 'react';
import {
  AlertOctagon,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { AnalysisSummary } from '../api/client';

interface ScoreRingProps {
  summary: AnalysisSummary | null;
}

export const ScoreRing: React.FC<ScoreRingProps> = ({ summary }) => {
  const score = summary ? summary.score : 100;

  // Determine color and status
  let scoreColor = 'var(--success)';
  let scoreLabel = 'Excellent';
  if (score < 50) {
    scoreColor = 'var(--critical)';
    scoreLabel = 'High Risk';
  } else if (score < 80) {
    scoreColor = 'var(--medium)';
    scoreLabel = 'Needs Attention';
  }

  const radius = 54;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const counts = {
    critical: summary?.critical ?? 0,
    high: summary?.high ?? 0,
    medium: summary?.medium ?? 0,
    low: summary?.low ?? 0,
    info: summary?.info ?? 0,
  };

  return (
    <div style={containerStyle}>
      <div style={ringWrapperStyle}>
        <svg height={radius * 2} width={radius * 2} style={{ transform: 'rotate(-90deg)' }}>
          <circle
            stroke="var(--border)"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          <circle
            stroke={scoreColor}
            fill="transparent"
            strokeWidth={stroke}
            strokeDasharray={`${circumference} ${circumference}`}
            style={{ strokeDashoffset, transition: 'stroke-dashoffset 0.5s ease-in-out' }}
            strokeLinecap="round"
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
        </svg>
        <div style={scoreCenterStyle}>
          <span style={{ ...scoreTextStyle, color: scoreColor }}>{score}</span>
          <span style={scoreSubtextStyle}>/ 100</span>
        </div>
      </div>

      <div style={statusLabelStyle}>
        <span style={{ color: scoreColor, fontWeight: 600 }}>{scoreLabel}</span>
        <span style={{ color: 'var(--muted)', fontSize: '11px' }}>Security Health Score</span>
      </div>

      {/* Severity Breakdown Grid */}
      <div style={breakdownGridStyle}>
        <div style={{ ...badgeStyle, borderColor: 'rgba(255, 77, 109, 0.3)' }}>
          <div style={badgeHeaderStyle}>
            <AlertOctagon size={13} color="var(--critical)" />
            <span style={{ color: 'var(--critical)', fontWeight: 600, fontSize: '11px' }}>CRITICAL</span>
          </div>
          <span style={badgeCountStyle}>{counts.critical}</span>
        </div>

        <div style={{ ...badgeStyle, borderColor: 'rgba(255, 138, 61, 0.3)' }}>
          <div style={badgeHeaderStyle}>
            <ShieldAlert size={13} color="var(--high)" />
            <span style={{ color: 'var(--high)', fontWeight: 600, fontSize: '11px' }}>HIGH</span>
          </div>
          <span style={badgeCountStyle}>{counts.high}</span>
        </div>

        <div style={{ ...badgeStyle, borderColor: 'rgba(245, 197, 66, 0.3)' }}>
          <div style={badgeHeaderStyle}>
            <AlertTriangle size={13} color="var(--medium)" />
            <span style={{ color: 'var(--medium)', fontWeight: 600, fontSize: '11px' }}>MEDIUM</span>
          </div>
          <span style={badgeCountStyle}>{counts.medium}</span>
        </div>

        <div style={{ ...badgeStyle, borderColor: 'rgba(92, 200, 255, 0.3)' }}>
          <div style={badgeHeaderStyle}>
            <Info size={13} color="var(--low)" />
            <span style={{ color: 'var(--low)', fontWeight: 600, fontSize: '11px' }}>LOW</span>
          </div>
          <span style={badgeCountStyle}>{counts.low}</span>
        </div>

        <div style={{ ...badgeStyle, borderColor: 'rgba(143, 161, 187, 0.3)' }}>
          <div style={badgeHeaderStyle}>
            <CheckCircle2 size={13} color="var(--info)" />
            <span style={{ color: 'var(--info)', fontWeight: 600, fontSize: '11px' }}>INFO</span>
          </div>
          <span style={badgeCountStyle}>{counts.info}</span>
        </div>
      </div>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '16px',
  background: 'var(--panel)',
  borderRadius: 'var(--radius)',
  border: '1px solid var(--border)',
  gap: '12px',
};

const ringWrapperStyle: React.CSSProperties = {
  position: 'relative',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const scoreCenterStyle: React.CSSProperties = {
  position: 'absolute',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
};

const scoreTextStyle: React.CSSProperties = {
  fontSize: '26px',
  fontWeight: 700,
  lineHeight: 1,
  fontFamily: 'var(--font-code)',
};

const scoreSubtextStyle: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--muted)',
  marginTop: '2px',
};

const statusLabelStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '2px',
};

const breakdownGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(5, 1fr)',
  gap: '6px',
  width: '100%',
  marginTop: '4px',
};

const badgeStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '6px 2px',
  background: 'var(--panel-2)',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
  gap: '3px',
};

const badgeHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '3px',
};

const badgeCountStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '14px',
  fontWeight: 600,
  color: 'var(--text)',
};
