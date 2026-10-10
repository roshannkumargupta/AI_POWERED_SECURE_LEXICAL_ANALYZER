import React from 'react';

export const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '12px',
  padding: '12px',
  overflowY: 'auto',
  height: '100%',
};

export const emptyContainerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%',
  padding: '24px',
};

export const metricsHeaderStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: '8px',
  paddingBottom: '8px',
  borderBottom: '1px solid var(--border)',
};

export const metricCardStyle: React.CSSProperties = {
  backgroundColor: 'var(--surface-2)',
  padding: '8px 10px',
  borderRadius: '6px',
  display: 'flex',
  flexDirection: 'column',
  border: '1px solid var(--border)',
};

export const metricLabelStyle: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  fontWeight: 600,
};

export const metricValStyle: React.CSSProperties = {
  fontSize: '14px',
  color: 'var(--text-primary)',
  fontWeight: 700,
  marginTop: '2px',
};

export const securityBannerStyle: React.CSSProperties = {
  backgroundColor: 'var(--surface-2)',
  border: '1px solid var(--border)',
  borderRadius: '6px',
  padding: '10px 12px',
};

export const timelineContainerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
};

export const stageGroupStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
};

export const stageHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  paddingBottom: '4px',
  borderBottom: '1px dashed var(--border)',
};

export const stageBadgeStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 700,
  letterSpacing: '0.04em',
  color: 'var(--text-accent)',
};

export const stepsListStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
};

export const stepCardStyle: React.CSSProperties = {
  backgroundColor: 'var(--surface-2)',
  border: '1px solid var(--border)',
  borderRadius: '6px',
  padding: '10px 12px',
  display: 'flex',
  flexDirection: 'column',
  gap: '6px',
};

export const stepRowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
};

export const stepActionStyle: React.CSSProperties = {
  fontSize: '12px',
  fontWeight: 600,
  color: 'var(--text-primary)',
  fontFamily: 'var(--font-code)',
};

export const argsSummaryStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--text-muted)',
};

export const badgeStyle: React.CSSProperties = {
  fontSize: '10px',
  fontWeight: 600,
  padding: '2px 6px',
  borderRadius: '4px',
  border: '1px solid',
  display: 'inline-flex',
  alignItems: 'center',
};

export const latencyStyle: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--text-muted)',
  fontFamily: 'var(--font-code)',
};

export const reasonTextStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text-secondary)',
  margin: 0,
  lineHeight: 1.4,
};

export const rejectionBoxStyle: React.CSSProperties = {
  backgroundColor: 'var(--bg-danger)',
  color: 'var(--text-danger)',
  border: '1px solid var(--text-danger)',
  borderRadius: '4px',
  padding: '6px 8px',
  fontSize: '11px',
  lineHeight: 1.4,
};

export const observationTextStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--text-primary)',
  backgroundColor: 'var(--surface-3)',
  padding: '4px 8px',
  borderRadius: '4px',
  fontFamily: 'var(--font-code)',
};
