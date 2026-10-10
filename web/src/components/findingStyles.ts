import React from 'react';

export const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: 'var(--panel)',
  overflow: 'hidden',
};

export const tabHeaderStyle: React.CSSProperties = {
  display: 'flex',
  height: '35px',
  minHeight: '35px',
  borderBottom: '1px solid var(--border)',
  backgroundColor: 'var(--panel-2)',
  padding: '0 8px',
};

export const tabButtonStyle: React.CSSProperties = {
  flex: 1,
  fontSize: '12px',
  fontWeight: 600,
  padding: '7px 9px',
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

export const tabContentStyle: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  padding: '16px',
};

export const findingContainerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '14px',
  minHeight: '100%',
};

export const findingHeaderStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '4px',
};

export const sevBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '11px',
  fontWeight: 700,
  padding: '2px 8px',
  borderRadius: 'var(--radius-sm)',
};

export const ruleCodeStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '11px',
  color: 'var(--accent)',
  backgroundColor: 'var(--panel-2)',
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
};

export const titleStyle: React.CSSProperties = {
  fontSize: '15px',
  fontWeight: 700,
  color: 'var(--text)',
  marginTop: '4px',
  lineHeight: 1.3,
};

export const locationSubStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--muted)',
  fontFamily: 'var(--font-code)',
};

export const sectionBoxStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '6px',
};

export const sectionTitleStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
};

export const explanationTextStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text-secondary)',
  lineHeight: 1.5,
};

export const flowToggleBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
  fontSize: '11px',
  fontWeight: 600,
  padding: '4px 10px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
  cursor: 'pointer',
};

export const reviewFixBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '5px',
  fontSize: '11px',
  fontWeight: 600,
  padding: '5px 12px',
  backgroundColor: 'var(--panel-3)',
  color: 'var(--text)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
};

export const feedbackBtnStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '6px',
  width: '100%',
  padding: '8px 12px',
  backgroundColor: 'transparent',
  border: '1px dashed var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--muted)',
  fontSize: '11px',
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'all var(--transition-fast)',
};

export const noFindingStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%',
  padding: '32px 16px',
  textAlign: 'center',
};
