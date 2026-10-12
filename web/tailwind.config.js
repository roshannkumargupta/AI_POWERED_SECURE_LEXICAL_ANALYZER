/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  corePlugins: { preflight: false },
  theme: {
    extend: {
      colors: {
        vs: Object.fromEntries(['bg','darker','elevated','header','border','borderSubtle','hover','active','selection','highlight','text','muted','light','blue','blueHover','cyan','purple','yellow','green','red','orange','symbol','keyword'].map((name) => [name, `var(--color-vs-${name})`])),
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Consolas', 'Courier New', 'monospace'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
};
