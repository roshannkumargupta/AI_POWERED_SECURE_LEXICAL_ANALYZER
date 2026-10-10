import React from 'react';

export interface SegmentedOption<T extends string = string> {
  value: T;
  label: React.ReactNode;
  icon?: React.ReactNode;
  ariaLabel?: string;
}

export interface SegmentedProps<T extends string = string> {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
  size?: 'sm' | 'md';
  ariaLabel?: string;
}

export function Segmented<T extends string = string>({
  options,
  value,
  onChange,
  size = 'md',
  ariaLabel = 'Segmented options',
}: SegmentedProps<T>) {
  const padding = size === 'sm' ? '0.125rem' : '0.25rem';
  const itemPadding = size === 'sm' ? '0.25rem 0.5rem' : '0.375rem 0.75rem';
  const fontSize = size === 'sm' ? '0.75rem' : '0.8125rem';

  return (
    <div
      role="group"
      aria-label={ariaLabel}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding,
        backgroundColor: 'var(--surface-1)',
        borderRadius: 'var(--radius)',
        border: '1px solid var(--border)',
        gap: '0.125rem',
      }}
    >
      {options.map((option) => {
        const isSelected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={isSelected}
            aria-label={
              option.ariaLabel || (typeof option.label === 'string' ? option.label : undefined)
            }
            onClick={() => onChange(option.value)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              padding: itemPadding,
              fontSize,
              fontWeight: isSelected ? 600 : 400,
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: isSelected ? 'var(--surface-2)' : 'transparent',
              color: isSelected ? 'var(--text-primary)' : 'var(--text-muted)',
              boxShadow: isSelected ? '0 1px 2px var(--border)' : 'none',
              transition: 'all var(--transition-fast)',
            }}
          >
            {option.icon && <span style={{ display: 'inline-flex' }}>{option.icon}</span>}
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
