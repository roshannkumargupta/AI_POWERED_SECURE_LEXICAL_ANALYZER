import React from 'react';

export interface ChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  active?: boolean;
  onRemove?: () => void;
  children: React.ReactNode;
}

export const Chip: React.FC<ChipProps> = ({
  active = false,
  onRemove,
  children,
  style,
  ...rest
}) => {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.25rem',
        padding: '0.125rem 0.5rem',
        fontSize: '0.75rem',
        borderRadius: 'var(--radius-full)',
        backgroundColor: active ? 'var(--bg-accent)' : 'var(--surface-3)',
        color: active ? 'var(--text-accent)' : 'var(--text-secondary)',
        border: `1px solid ${active ? 'var(--border-accent)' : 'var(--border)'}`,
        cursor: 'default',
        userSelect: 'none',
        ...style,
      }}
      {...rest}
    >
      {children}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          aria-label="Remove"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '0.875rem',
            height: '0.875rem',
            borderRadius: 'var(--radius-full)',
            border: 'none',
            background: 'none',
            color: 'inherit',
            cursor: 'pointer',
            padding: 0,
            fontSize: '0.75rem',
            lineHeight: 1,
          }}
        >
          ×
        </button>
      )}
    </span>
  );
};
