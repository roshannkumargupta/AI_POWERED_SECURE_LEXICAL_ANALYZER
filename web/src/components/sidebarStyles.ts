import React from 'react';

export const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  backgroundColor: 'var(--panel)',
  display: 'flex',
  flexDirection: 'column',
  borderRight: '1px solid var(--border)',
};

export const collapsedContainerStyle: React.CSSProperties = {
  width: '32px',
  height: '100%',
  backgroundColor: 'var(--panel)',
  borderRight: '1px solid var(--border)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  paddingTop: '8px',
};

export const expandBtnStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: 'var(--muted)',
  cursor: 'pointer',
  padding: '6px',
  borderRadius: 'var(--radius-sm)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

export const headerStyle: React.CSSProperties = {
  height: '35px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 10px',
  borderBottom: '1px solid var(--border)',
  backgroundColor: 'var(--panel-2)',
};

export const titleStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 700,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
};

export const collapseBtnStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: 'var(--muted)',
  cursor: 'pointer',
  padding: '2px',
  borderRadius: 'var(--radius-sm)',
  display: 'flex',
  alignItems: 'center',
};

export const openFileBoxStyle: React.CSSProperties = {
  padding: '8px 10px',
  borderBottom: '1px solid var(--border)',
};

export const openFileButtonStyle: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '6px',
  padding: '6px 10px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--text)',
  fontSize: '11px',
  fontWeight: 500,
  cursor: 'pointer',
};

export const samplesSectionStyle: React.CSSProperties = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
};

export const sectionHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '8px 10px',
  fontSize: '10px',
  fontWeight: 700,
  color: 'var(--muted)',
  letterSpacing: '0.3px',
};

export const badgeCountStyle: React.CSSProperties = {
  fontSize: '9px',
  backgroundColor: 'var(--panel-3)',
  color: 'var(--muted)',
  padding: '1px 5px',
  borderRadius: '10px',
  fontWeight: 600,
};

export const samplesListStyle: React.CSSProperties = {
  flex: 1,
  overflowY: 'auto',
  display: 'flex',
  flexDirection: 'column',
};

export const groupHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  width: '100%',
  padding: '6px 10px',
  background: 'transparent',
  border: 'none',
  fontSize: '10px',
  fontWeight: 700,
  color: 'var(--muted)',
  cursor: 'pointer',
  textAlign: 'left',
  textTransform: 'uppercase',
  letterSpacing: '0.3px',
};

export const sampleItemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  width: '100%',
  padding: '5px 10px',
  background: 'transparent',
  border: 'none',
  cursor: 'pointer',
  textAlign: 'left',
  transition: 'background-color var(--transition-fast)',
};

export const sampleTitleStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text)',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
};

export const sampleLabelStyle: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--muted)',
  marginTop: '1px',
};
