import React from 'react';

export type BadgeVariant =
  | 'critical'
  | 'high'
  | 'medium'
  | 'low'
  | 'info'
  | 'success'
  | 'warning'
  | 'danger'
  | 'neutral'
  | 'verified'
  | 'unverified';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  children: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, React.CSSProperties> = {
  critical: {
    color: 'var(--sev-critical)',
    backgroundColor: 'var(--danger-wash)',
    borderColor: 'var(--error-border)',
  },
  high: {
    color: 'var(--sev-high)',
    backgroundColor: 'var(--warning-wash)',
    borderColor: 'var(--amber)',
  },
  medium: {
    color: 'var(--sev-medium)',
    backgroundColor: 'var(--warning-wash)',
    borderColor: 'var(--amber)',
  },
  low: {
    color: 'var(--sev-low)',
    backgroundColor: 'var(--accent-wash)',
    borderColor: 'var(--border-accent)',
  },
  info: {
    color: 'var(--sev-info)',
    backgroundColor: 'var(--surface-3)',
    borderColor: 'var(--border)',
  },
  success: {
    color: 'var(--text-success)',
    backgroundColor: 'var(--bg-success)',
    borderColor: 'var(--text-success)',
  },
  warning: {
    color: 'var(--text-warning)',
    backgroundColor: 'var(--bg-warning)',
    borderColor: 'var(--text-warning)',
  },
  danger: {
    color: 'var(--text-danger)',
    backgroundColor: 'var(--bg-danger)',
    borderColor: 'var(--text-danger)',
  },
  neutral: {
    color: 'var(--text-neutral)',
    backgroundColor: 'var(--bg-neutral)',
    borderColor: 'var(--border)',
  },
  verified: {
    color: 'var(--text-success)',
    backgroundColor: 'var(--bg-success)',
    borderColor: 'var(--text-success)',
  },
  unverified: {
    color: 'var(--text-warning)',
    backgroundColor: 'var(--bg-warning)',
    borderColor: 'var(--text-warning)',
  },
};

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  size = 'sm',
  children,
  style,
  className,
  ...rest
}) => {
  const chosenStyle = variantStyles[variant] || variantStyles.neutral;
  const padding = size === 'sm' ? '0.125rem 0.375rem' : '0.25rem 0.5rem';
  const fontSize = size === 'sm' ? '0.75rem' : '0.8125rem';

  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.25rem',
        padding,
        fontSize,
        fontWeight: 600,
        lineHeight: 1.2,
        borderRadius: 'var(--radius-sm)',
        border: '1px solid',
        textTransform: 'uppercase',
        letterSpacing: '0.02em',
        userSelect: 'none',
        whiteSpace: 'nowrap',
        ...chosenStyle,
        ...style,
      }}
      {...rest}
    >
      {children}
    </span>
  );
};
