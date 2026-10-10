import React from 'react';
import {
  sectionStyle,
  sectionTitleStyle,
  barTrackSmallStyle,
  barFillStyle,
} from './mlInsightsStyles';

interface MlOcclusionBarsProps {
  drops: Record<string, number>;
}

export const MlOcclusionBars: React.FC<MlOcclusionBarsProps> = ({ drops }) => {
  return (
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
  );
};
