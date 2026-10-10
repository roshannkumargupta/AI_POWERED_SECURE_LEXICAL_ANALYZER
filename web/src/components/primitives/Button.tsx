import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    backgroundColor: 'var(--text-accent)',
    color: 'var(--text-on-accent)',
    border: '1px solid var(--text-accent)',
  },
  secondary: {
    backgroundColor: 'var(--surface-2)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border)',
  },
  danger: {
    backgroundColor: 'var(--bg-danger)',
    color: 'var(--text-danger)',
    border: '1px solid var(--text-danger)',
  },
  ghost: {
    backgroundColor: 'transparent',
    color: 'var(--text-secondary)',
    border: '1px solid transparent',
  },
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: {
    padding: '0.25rem 0.5rem',
    fontSize: '0.75rem',
  },
  md: {
    padding: '0.375rem 0.75rem',
    fontSize: '0.8125rem',
  },
  lg: {
    padding: '0.5rem 1rem',
    fontSize: '0.875rem',
  },
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'secondary', size = 'md', icon, children, style, disabled, ...rest }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.375rem',
          borderRadius: 'var(--radius)',
          fontWeight: 500,
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          transition: 'all var(--transition-fast)',
          ...sizeStyles[size],
          ...variantStyles[variant],
          ...style,
        }}
        {...rest}
      >
        {icon && <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
