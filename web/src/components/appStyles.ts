import React from 'react';

export const appRootStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  width: '100vw',
  overflow: 'hidden',
  backgroundColor: 'var(--surface-1)',
  color: 'var(--text-primary)',
};

export const backendWarningBannerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '6px 14px',
  backgroundColor: 'var(--danger-wash)',
  borderBottom: '1px solid var(--border)',
  color: 'var(--text-danger)',
  fontSize: '11px',
};

export const codeTagStyle: React.CSSProperties = {
  padding: '1px 5px',
  backgroundColor: 'var(--surface-2)',
  borderRadius: '3px',
  fontFamily: 'var(--font-code)',
};

export const retryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  padding: '3px 8px',
  backgroundColor: 'var(--bg-danger)',
  color: 'var(--text-danger)',
  border: '1px solid var(--border)',
  borderRadius: '4px',
  fontSize: '10px',
  fontWeight: 600,
  cursor: 'pointer',
};
