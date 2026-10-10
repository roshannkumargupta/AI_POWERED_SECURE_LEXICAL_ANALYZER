import React from 'react';
import { AnalysisSummary } from '../api/client';

export const ScoreRing: React.FC<{ summary: AnalysisSummary | null }> = ({ summary }) => {
  const score = summary?.score ?? 100;
  const color = score >= 80 ? 'var(--muted)' : score >= 50 ? 'var(--medium)' : 'var(--critical)';
  const radius = 28;
  const stroke = 3;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '8px 0',
        borderBottom: '1px solid var(--border)',
      }}
    >
      <div style={{ position: 'relative', width: 56, height: 56, flex: 'none' }}>
        <svg height={56} width={56} style={{ transform: 'rotate(-90deg)' }}>
          <circle
            stroke="var(--border)"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          <circle
            stroke={color}
            fill="transparent"
            strokeWidth={stroke}
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={offset}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
        </svg>
        <span
          style={{
            position: 'absolute',
            inset: 0,
            display: 'grid',
            placeItems: 'center',
            color,
            font: '600 14px var(--font-code)',
          }}
        >
          {score}
        </span>
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600 }}>
          Security {score} <span style={{ fontSize: 11, color: 'var(--muted)' }}>/ 100</span>
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          {summary
            ? `${summary.critical + summary.high} high, ${summary.medium} medium, ${summary.low} low`
            : 'Waiting for analysis'}
        </div>
        {summary && (
          <div style={{ fontSize: 11, color: 'var(--muted)' }}>
            {summary.tokens_total} tokens analyzed · {summary.tokens_malicious} malicious ·{' '}
            {summary.tokens_suspicious} suspicious
          </div>
        )}
      </div>
    </div>
  );
};
