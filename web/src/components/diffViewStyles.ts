import React from 'react';

export const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'var(--scrim-strong)',
  backdropFilter: 'blur(3px)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: '24px',
};

export const modalStyle: React.CSSProperties = {
  width: '100%',
  maxWidth: '720px',
  maxHeight: '85vh',
  backgroundColor: 'var(--panel)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-lg)',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: 'var(--shadow-modal)',
  overflow: 'hidden',
};

export const headerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '14px 18px',
  borderBottom: '1px solid var(--border)',
  background: 'var(--panel-2)',
};

export const titleStyle: React.CSSProperties = {
  fontSize: '14px',
  fontWeight: 600,
  color: 'var(--text)',
};

export const verifiedBadgeStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--success)',
  backgroundColor: 'var(--success-wash)',
  padding: '2px 8px',
  borderRadius: 'var(--radius-full)',
  border: '1px solid var(--border)',
};

export const unverifiedBadgeStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--medium)',
  backgroundColor: 'var(--warning-wash)',
  padding: '2px 8px',
  borderRadius: 'var(--radius-full)',
  border: '1px solid var(--border)',
};

export const closeButtonStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '4px',
  borderRadius: 'var(--radius-sm)',
};

export const bodyStyle: React.CSSProperties = {
  padding: '18px',
  display: 'flex',
  flexDirection: 'column',
  gap: '14px',
  overflowY: 'auto',
  flex: 1,
};

export const summaryRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};

export const fixTitleStyle: React.CSSProperties = {
  fontSize: '14px',
  fontWeight: 600,
  color: 'var(--text)',
};

export const findingRuleStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '11px',
  backgroundColor: 'var(--panel-2)',
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--accent)',
  border: '1px solid var(--border)',
};

export const descStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--muted)',
  lineHeight: 1.5,
  margin: 0,
};

export const diffContainerStyle: React.CSSProperties = {
  backgroundColor: 'var(--panel-3)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  overflow: 'hidden',
  display: 'flex',
  flexDirection: 'column',
};

export const diffHeaderStyle: React.CSSProperties = {
  padding: '6px 10px',
  fontSize: '11px',
  fontWeight: 600,
  backgroundColor: 'var(--panel-2)',
  borderBottom: '1px solid var(--border)',
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.3px',
};

export const diffPreStyle: React.CSSProperties = {
  margin: 0,
  padding: '10px 0',
  fontFamily: 'var(--font-code)',
  fontSize: '12px',
  lineHeight: 1.5,
  overflowX: 'auto',
  maxHeight: '260px',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-all',
};

export const verificationNotesStyle: React.CSSProperties = {
  padding: '8px 12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  fontSize: '11px',
  color: 'var(--text-secondary)',
};

export const footerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  gap: '10px',
  padding: '12px 18px',
  borderTop: '1px solid var(--border)',
  backgroundColor: 'var(--panel-2)',
};

export const cancelButtonStyle: React.CSSProperties = {
  padding: '6px 14px',
  borderRadius: 'var(--radius)',
  border: '1px solid var(--border)',
  backgroundColor: 'transparent',
  color: 'var(--text-secondary)',
  fontSize: '12px',
  fontWeight: 500,
  cursor: 'pointer',
};

export const applyButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '6px 16px',
  borderRadius: 'var(--radius)',
  border: 'none',
  backgroundColor: 'var(--accent)',
  color: 'var(--text-on-accent)',
  fontSize: '12px',
  fontWeight: 600,
  cursor: 'pointer',
};
