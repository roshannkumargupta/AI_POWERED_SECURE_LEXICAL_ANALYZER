import React from 'react';

export interface SelectOption<T extends string = string> {
  value: T;
  label: string;
}

export interface SelectProps<T extends string = string> extends Omit<
  React.SelectHTMLAttributes<HTMLSelectElement>,
  'onChange' | 'value' | 'size'
> {
  options: SelectOption<T>[];
  value: T;
  onChange: (value: T) => void;
  size?: 'sm' | 'md';
}

export function Select<T extends string = string>({
  options,
  value,
  onChange,
  size = 'md',
  disabled,
  style,
  ...rest
}: SelectProps<T>) {
  const padding = size === 'sm' ? '0.25rem 0.5rem' : '0.375rem 0.75rem';
  const fontSize = size === 'sm' ? '0.75rem' : '0.8125rem';

  return (
    <select
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value as T)}
      style={{
        padding,
        fontSize,
        borderRadius: 'var(--radius)',
        backgroundColor: 'var(--surface-1)',
        color: 'var(--text-primary)',
        border: '1px solid var(--border)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        outline: 'none',
        ...style,
      }}
      {...rest}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
