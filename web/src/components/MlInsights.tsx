import React from 'react';
import { AlertCircle, Brain, Sparkles } from 'lucide-react';
import { MLInsightsResponse } from '../api/client';

interface MlInsightsProps {
  insights: MLInsightsResponse | null;
  isLoading: boolean;
  mlMode: 'on' | 'off';
  modelId?: string;
  selectedToken?: string;
  lexicalError?: boolean;
  mlReason?: string;
}

export const MlInsights: React.FC<MlInsightsProps> = ({
  insights,
  isLoading,
  mlMode,
  modelId,
  selectedToken,
  lexicalError,
  mlReason,
}) => {
  if (lexicalError) return <div className="ui5-empty">n/a - lexical errors do not use ML</div>;
  if (mlMode === 'off' || (insights && insights.ml_mode === 'off')) {
    return (
      <div style={noticeContainerStyle}>
        <div style={noticeHeaderStyle}>
          <AlertCircle size={20} color="var(--critical)" />
          <span style={noticeTitleStyle}>ML OFF</span>
        </div>
        <p style={noticeTextStyle}>
          ML off - Rules and Taint remain active. Reason:{' '}
          {mlReason || 'the API did not provide an ML-off reason.'}
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={loadingStyle}>
        <Sparkles size={18} className="animate-spin" color="var(--accent)" />
        <span>Extracting 45-dim features & running occlusion analysis...</span>
      </div>
    );
  }

  if (!insights) {
    return (
      <div style={{ ...emptyStyle, alignItems: 'stretch' }}>
        <div className="ui6-ml-header">
          ML on - model {modelId || 'unknown'} - 9-token window - token:{' '}
          {selectedToken || 'unknown'}
        </div>
        <Brain size={24} color="var(--muted)" />
        <p style={{ marginTop: '8px', color: 'var(--muted)', fontSize: '13px' }}>
          Click any token or select a finding to inspect machine learning confidence probabilities
          and feature-group occlusion impacts.
        </p>
      </div>
    );
  }

  const probs = insights.probabilities || { SAFE: 0, SUSPICIOUS: 0, MALICIOUS: 0 };
  const drops = insights.feature_group_drops || {};

  const safePct = Math.round((probs.SAFE || 0) * 100);
  const suspPct = Math.round((probs.SUSPICIOUS || 0) * 100);
  const malPct = Math.round((probs.MALICIOUS || 0) * 100);

  const predLabel = insights.predicted_label || 'SAFE';
  let predColor = 'var(--success)';
  if (predLabel === 'MALICIOUS') predColor = 'var(--critical)';
  else if (predLabel === 'SUSPICIOUS') predColor = 'var(--medium)';

  return (
    <div style={containerStyle}>
      <div className="ui6-ml-header">
        ML on - model {modelId || 'unknown'} - 9-token window - token:{' '}
        {selectedToken || insights.token_text || 'unknown'}
      </div>
      {/* Token Header */}
      <div style={tokenHeaderCardStyle}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>
              Target Token
            </span>
            <code style={tokenCodeStyle}>{insights.token_text || '<unnamed>'}</code>
          </div>
          <span
            style={{
              ...predBadgeStyle,
              color: predColor,
              borderColor: predColor,
              backgroundColor: `${predColor}15`,
            }}
          >
            {predLabel}
          </span>
        </div>
      </div>

      {/* Class Probabilities */}
      <div style={sectionStyle}>
        <span style={sectionTitleStyle}>Calibrated Class Probabilities</span>

        <div style={probRowStyle}>
          <div style={probLabelRowStyle}>
            <span style={{ color: 'var(--success)', fontWeight: 600 }}>SAFE</span>
            <span style={probValStyle}>{safePct}%</span>
          </div>
          <div style={barTrackStyle}>
            <div
              style={{ ...barFillStyle, width: `${safePct}%`, backgroundColor: 'var(--success)' }}
            />
          </div>
        </div>

        <div style={probRowStyle}>
          <div style={probLabelRowStyle}>
            <span style={{ color: 'var(--medium)', fontWeight: 600 }}>SUSPICIOUS</span>
            <span style={probValStyle}>{suspPct}%</span>
          </div>
          <div style={barTrackStyle}>
            <div
              style={{ ...barFillStyle, width: `${suspPct}%`, backgroundColor: 'var(--medium)' }}
            />
          </div>
        </div>

        <div style={probRowStyle}>
          <div style={probLabelRowStyle}>
            <span style={{ color: 'var(--critical)', fontWeight: 600 }}>MALICIOUS</span>
            <span style={probValStyle}>{malPct}%</span>
          </div>
          <div style={barTrackStyle}>
            <div
              style={{ ...barFillStyle, width: `${malPct}%`, backgroundColor: 'var(--critical)' }}
            />
          </div>
        </div>
      </div>

      {/* Feature Group Occlusion Bars */}
      <div style={sectionStyle}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '8px',
          }}
        >
          <span style={sectionTitleStyle}>Feature Group Occlusion Impact (ΔP)</span>
          <span style={{ fontSize: '10px', color: 'var(--muted)' }}>Higher = stronger signal</span>
        </div>

        {Object.entries(drops).length === 0 ? (
          <span style={{ fontSize: '11px', color: 'var(--muted)', fontStyle: 'italic' }}>
            No significant feature occlusion drop measured.
          </span>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {Object.entries(drops)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 6)
              .map(([groupName, dropVal]) => {
                const dropPct = Math.min(100, Math.round(dropVal * 100));
                return (
                  <div
                    key={groupName}
                    style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}
                  >
                    <div
                      style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}
                    >
                      <span
                        style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-code)' }}
                      >
                        {groupName}
                      </span>
                      <span style={{ color: 'var(--accent)', fontWeight: 600 }}>
                        +{dropVal.toFixed(3)}
                      </span>
                    </div>
                    <div style={barTrackSmallStyle}>
                      <div
                        style={{
                          ...barFillStyle,
                          width: `${Math.max(4, dropPct)}%`,
                          backgroundColor: 'var(--accent)',
                        }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '14px',
};

const noticeContainerStyle: React.CSSProperties = {
  padding: '16px',
  background: 'var(--danger-wash)',
  border: '1px solid var(--error-border)',
  borderRadius: 'var(--radius)',
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
};

const noticeHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
};

const noticeTitleStyle: React.CSSProperties = {
  fontWeight: 700,
  fontSize: '13px',
  color: 'var(--critical)',
};

const noticeTextStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text-secondary)',
  lineHeight: 1.5,
};

const loadingStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  padding: '24px',
  justifyContent: 'center',
  color: 'var(--muted)',
  fontSize: '12px',
};

const emptyStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '32px 16px',
  textAlign: 'center',
};

const tokenHeaderCardStyle: React.CSSProperties = {
  padding: '10px 12px',
  background: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
};

const tokenCodeStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  color: 'var(--text)',
  background: 'var(--bg)',
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
  fontSize: '12px',
};

const predBadgeStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 700,
  padding: '2px 8px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid transparent',
};

const sectionStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
};

const probRowStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '3px',
};

const probLabelRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  fontSize: '11px',
};

const probValStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  color: 'var(--text)',
  fontWeight: 600,
};

const barTrackStyle: React.CSSProperties = {
  height: '6px',
  backgroundColor: 'var(--panel-3)',
  borderRadius: 'var(--radius-full)',
  overflow: 'hidden',
};

const barTrackSmallStyle: React.CSSProperties = {
  height: '4px',
  backgroundColor: 'var(--panel-3)',
  borderRadius: 'var(--radius-full)',
  overflow: 'hidden',
};

const barFillStyle: React.CSSProperties = {
  height: '100%',
  borderRadius: 'var(--radius-full)',
  transition: 'width 0.4s ease-in-out',
};
