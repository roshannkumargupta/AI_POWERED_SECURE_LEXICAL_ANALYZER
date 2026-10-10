import React from 'react';

export const containerStyle: React.CSSProperties = {
  height: '49px',
  minHeight: '49px',
  maxHeight: '49px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 16px',
  backgroundColor: 'var(--panel)',
  borderBottom: '1px solid var(--border)',
  zIndex: 30,
};

export const brandGroupStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
};

export const logoIconStyle: React.CSSProperties = {
  width: '28px',
  height: '28px',
  borderRadius: 'var(--radius-sm)',
  backgroundColor: 'var(--accent)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  boxShadow: 'none',
};

export const brandTitleStyle: React.CSSProperties = {
  fontSize: '14px',
  fontWeight: 500,
  letterSpacing: '-0.3px',
  color: 'var(--text)',
};

export const middleControlsStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
};

export const selectorWrapperStyle: React.CSSProperties = {
  position: 'relative',
  display: 'flex',
  alignItems: 'center',
};

export const visuallyHiddenStyle: React.CSSProperties = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  border: 0,
};

export const selectStyle: React.CSSProperties = {
  appearance: 'none',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  width: 110,
  height: 26,
  padding: '3px 24px 3px 8px',
  fontSize: '12px',
  fontWeight: 500,
  cursor: 'pointer',
  outline: 'none',
};

export const selectArrowStyle: React.CSSProperties = {
  position: 'absolute',
  right: '8px',
  pointerEvents: 'none',
};

export const secondaryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '5px 12px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text-secondary)',
  fontSize: '12px',
  fontWeight: 500,
  cursor: 'pointer',
};

export const dropdownMenuStyle: React.CSSProperties = {
  position: 'absolute',
  top: 'calc(100% + 6px)',
  left: 0,
  width: '280px',
  maxHeight: '360px',
  overflowY: 'auto',
  backgroundColor: 'var(--panel)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  boxShadow: 'var(--shadow-popover)',
  display: 'flex',
  flexDirection: 'column',
  padding: '6px',
  zIndex: 100,
};

export const dropdownItemStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'flex-start',
  padding: '6px 8px',
  borderRadius: 'var(--radius-sm)',
  cursor: 'pointer',
  textAlign: 'left',
  transition: 'background-color var(--transition-fast)',
};

export const rightActionsStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
};

export const primaryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '6px 14px',
  backgroundColor: 'var(--accent)',
  color: 'var(--surface-1)',
  borderRadius: 'var(--radius)',
  fontSize: '12px',
  fontWeight: 600,
  cursor: 'pointer',
  boxShadow: '0 2px 6px var(--accent-wash)',
};

export const fixAllButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '6px 14px',
  backgroundColor: 'var(--success-wash)',
  border: '1px solid var(--text-success)',
  color: 'var(--success)',
  borderRadius: 'var(--radius)',
  fontSize: '12px',
  fontWeight: 600,
  cursor: 'pointer',
};

export const iconButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '6px',
  backgroundColor: 'var(--panel-2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  color: 'var(--text)',
  cursor: 'pointer',
};

export const kbdStyle: React.CSSProperties = {
  fontSize: '10px',
  opacity: 0.8,
  backgroundColor: 'var(--surface-3)',
  padding: '1px 4px',
  borderRadius: '2px',
  marginLeft: '2px',
};
