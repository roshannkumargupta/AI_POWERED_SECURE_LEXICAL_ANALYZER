import React from 'react';

export const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '14px',
};

export const noticeContainerStyle: React.CSSProperties = {
  padding: '16px',
  background: 'var(--danger-wash)',
  border: '1px solid var(--error-border)',
  borderRadius: 'var(--radius)',
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
};

export const noticeHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
};

export const noticeTitleStyle: React.CSSProperties = {
  fontWeight: 700,
  fontSize: '13px',
  color: 'var(--critical)',
};

export const noticeTextStyle: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text-secondary)',
  lineHeight: 1.5,
};

export const loadingStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  padding: '24px',
  justifyContent: 'center',
  color: 'var(--muted)',
  fontSize: '12px',
};

export const emptyStyle: React.CSSProperties = {
  padding: '24px',
  textAlign: 'center',
  color: 'var(--muted)',
  fontSize: '12px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
};

export const tokenHeaderCardStyle: React.CSSProperties = {
  padding: '10px 14px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
};

export const tokenCodeStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  fontSize: '12px',
  backgroundColor: 'var(--panel-3)',
  padding: '2px 8px',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--accent)',
};

export const predBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '11px',
  fontWeight: 700,
  padding: '2px 8px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid',
  letterSpacing: '0.4px',
};

export const sectionStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  padding: '12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
};

export const sectionTitleStyle: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.4px',
};

export const probRowStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '3px',
};

export const probLabelRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  fontSize: '11px',
};

export const probValStyle: React.CSSProperties = {
  fontFamily: 'var(--font-code)',
  color: 'var(--muted)',
};

export const barTrackStyle: React.CSSProperties = {
  height: '6px',
  backgroundColor: 'var(--panel-3)',
  borderRadius: 'var(--radius-full)',
  overflow: 'hidden',
};

export const barTrackSmallStyle: React.CSSProperties = {
  height: '4px',
  backgroundColor: 'var(--panel-3)',
  borderRadius: 'var(--radius-full)',
  overflow: 'hidden',
};

export const barFillStyle: React.CSSProperties = {
  height: '100%',
  borderRadius: 'var(--radius-full)',
  transition: 'width var(--transition-normal)',
};
