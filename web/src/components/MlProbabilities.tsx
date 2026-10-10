import React from 'react';
import {
  sectionStyle,
  sectionTitleStyle,
  probRowStyle,
  probLabelRowStyle,
  probValStyle,
  barTrackStyle,
  barFillStyle,
} from './mlInsightsStyles';

interface MlProbabilitiesProps {
  safePct: number;
  suspPct: number;
  malPct: number;
}

export const MlProbabilities: React.FC<MlProbabilitiesProps> = ({ safePct, suspPct, malPct }) => {
  return (
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
  );
};
