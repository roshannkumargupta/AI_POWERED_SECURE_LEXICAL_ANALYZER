import React from 'react';

export interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label?: string;
  id?: string;
  ariaLabel?: string;
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onChange,
  disabled = false,
  label,
  id,
  ariaLabel,
}) => {
  return (
    <label
      htmlFor={id}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.5rem',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        userSelect: 'none',
      }}
    >
      <div
        role="switch"
        aria-checked={checked}
        aria-label={ariaLabel || label}
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(e) => {
          if (disabled) return;
          if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            onChange(!checked);
          }
        }}
        onClick={() => {
          if (!disabled) onChange(!checked);
        }}
        style={{
          width: '2rem',
          height: '1.125rem',
          borderRadius: 'var(--radius-full)',
          backgroundColor: checked ? 'var(--text-accent)' : 'var(--border-control)',
          position: 'relative',
          transition: 'background-color var(--transition-fast)',
          outline: 'none',
        }}
      >
        <div
          style={{
            width: '0.875rem',
            height: '0.875rem',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--surface-2)',
            position: 'absolute',
            top: '0.125rem',
            left: checked ? '1rem' : '0.125rem',
            transition: 'left var(--transition-fast)',
            boxShadow: '0 1px 2px var(--scrim)',
          }}
        />
      </div>
      {label && (
        <span
          style={{
            fontSize: '0.8125rem',
            color: 'var(--text-primary)',
          }}
        >
          {label}
        </span>
      )}
    </label>
  );
};
