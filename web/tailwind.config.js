/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  corePlugins: { preflight: false },
  theme: {
    extend: {
      colors: {
        surface: 'var(--ref-surface)',
        'surface-dim': 'var(--ref-surface-dim)',
        'surface-deepest': 'var(--ref-surface-deepest)',
        'surface-editor': 'var(--ref-surface-editor)',
        'surface-explorer': 'var(--ref-surface-explorer)',
        'surface-elevated': 'var(--ref-surface-elevated)',
        'surface-container': 'var(--ref-surface-container)',
        'surface-hover': 'var(--ref-surface-hover)',
        'surface-selected': 'var(--ref-surface-selected)',
        'border-primary': 'var(--ref-border-primary)',
        'border-subtle': 'var(--ref-border-subtle)',
        'text-primary': 'var(--ref-text-primary)',
        'text-secondary': 'var(--ref-text-secondary)',
        'text-muted': 'var(--ref-text-muted)',
        primary: 'var(--ref-primary)',
        'primary-container': 'var(--ref-primary-container)',
        'status-success': 'var(--ref-status-success)',
        'status-warning': 'var(--ref-status-warning)',
        'status-error': 'var(--ref-status-error)',
        'accent-ai': 'var(--ref-accent-ai)',
        'accent-fix': 'var(--ref-accent-fix)',
        vs: Object.fromEntries(
          ['bg','darker','elevated','header','border','borderSubtle','hover','active','selection','highlight','text','muted','light','blue','blueHover','cyan','purple','yellow','green','red','orange','symbol','keyword'].map((name) => [name, `var(--color-vs-${name})`])
        ),
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Consolas', 'Courier New', 'monospace'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
};
