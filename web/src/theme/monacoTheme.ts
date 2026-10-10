import type { editor } from 'monaco-editor';
import type { ResolvedTheme } from './theme';

export const SECURELEX_THEME_NAME = 'securelex-dark';

function toHex(val: string): string {
  if (!val) return '#00000000';
  const trimmed = val.trim();
  if (trimmed === 'transparent') return '#00000000';
  if (trimmed.startsWith('#')) return trimmed;
  const match = trimmed.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([0-9.]+))?\)/i);
  if (match) {
    const r = parseInt(match[1], 10).toString(16).padStart(2, '0');
    const g = parseInt(match[2], 10).toString(16).padStart(2, '0');
    const b = parseInt(match[3], 10).toString(16).padStart(2, '0');
    const aNum = match[4] !== undefined ? parseFloat(match[4]) : 1;
    const a = Math.round(aNum * 255).toString(16).padStart(2, '0');
    return `#${r}${g}${b}${a}`;
  }
  return trimmed;
}

export function buildMonacoTheme(tokens: Record<string, string>, resolved: ResolvedTheme): editor.IStandaloneThemeData {
  const token = (name: string) => toHex((tokens[name] || '').trim());
  const dark = resolved === 'dark';
  return {
    base: dark ? 'vs-dark' : 'vs',
    inherit: false,
    rules: [
      { token: '', foreground: token('--text-primary').replace(/^#/, '') },
      { token: 'comment', foreground: token('--text-muted').replace(/^#/, ''), fontStyle: 'italic' },
    ],
    colors: {
      'editor.background': token('--surface-2'),
      'editor.foreground': token('--text-primary'),
      'editorLineNumber.foreground': token('--text-muted'),
      'editorLineNumber.activeForeground': dark ? token('--text-secondary') : token('--text-primary'),
      'editor.lineHighlightBackground': token('--editor-line-highlight'),
      'editor.lineHighlightBorder': '#00000000',
      'editor.selectionBackground': token('--editor-selection'),
      'editor.inactiveSelectionBackground': token('--editor-selection'),
      'editorCursor.foreground': token('--text-primary'),
      'editorIndentGuide.background': token('--editor-indent-guide'),
      'editorGutter.background': token('--surface-2'),
      'editorError.foreground': token('--sev-critical'),
      'editorWarning.foreground': token('--sev-medium'),
      'editorInfo.foreground': token('--sev-low'),
      'editorWidget.background': token('--surface-3'),
      'editorWidget.border': token('--border-strong'),
      'editorHoverWidget.background': token('--surface-3'),
      'editorHoverWidget.border': token('--border-strong'),
      'editorSuggestWidget.background': token('--surface-3'),
      'editorSuggestWidget.border': token('--border-strong'),
      'editorSuggestWidget.selectedBackground': token('--bg-accent'),
      'scrollbarSlider.background': token('--scrollbar-thumb'),
      'scrollbarSlider.hoverBackground': token('--scrollbar-thumb-hover'),
      'scrollbarSlider.activeBackground': token('--border-strong'),
    },
  };
}

