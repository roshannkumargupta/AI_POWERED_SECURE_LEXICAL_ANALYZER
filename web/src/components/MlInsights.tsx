import React from 'react';
import { AlertCircle, Brain, Sparkles } from 'lucide-react';
import { MLInsightsResponse } from '../api/client';
import {
  containerStyle,
  noticeContainerStyle,
  noticeHeaderStyle,
  noticeTitleStyle,
  noticeTextStyle,
  loadingStyle,
  emptyStyle,
  tokenHeaderCardStyle,
  tokenCodeStyle,
  predBadgeStyle,
} from './mlInsightsStyles';
import { MlProbabilities } from './MlProbabilities';
import { MlOcclusionBars } from './MlOcclusionBars';

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

      <MlProbabilities safePct={safePct} suspPct={suspPct} malPct={malPct} />
      <MlOcclusionBars drops={drops} />
    </div>
  );
};
