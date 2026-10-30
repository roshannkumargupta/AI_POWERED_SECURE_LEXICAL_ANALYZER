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
    const a = Math.round(aNum * 255)
      .toString(16)
      .padStart(2, '0');
    return `#${r}${g}${b}${a}`;
  }
  return trimmed;
}

export function buildMonacoTheme(
  tokens: Record<string, string>,
  resolved: ResolvedTheme
): editor.IStandaloneThemeData {
  const token = (name: string) => toHex((tokens[name] || '').trim());
  const dark = resolved === 'dark';
  return {
    base: dark ? 'vs-dark' : 'vs',
    inherit: false,
    rules: [
      { token: '', foreground: token('--text-primary').replace(/^#/, '') },
      {
        token: 'comment',
        foreground: token('--text-muted').replace(/^#/, ''),
        fontStyle: 'italic',
      },
    ],
    colors: {
      'editor.background': token('--surface-2'),
      'editor.foreground': token('--text-primary'),
      'editorLineNumber.foreground': token('--text-muted'),
      'editorLineNumber.activeForeground': dark
        ? token('--text-secondary')
        : token('--text-primary'),
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

export function registerSecureLexThemes(monacoInstance: typeof import('monaco-editor')) {
  monacoInstance.editor.defineTheme('securelex-theme-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '58A6FF', fontStyle: 'bold' },
      { token: 'string', foreground: '7EE787' },
      { token: 'identifier', foreground: 'DCE8F6' },
      { token: 'type', foreground: '8FA7C1' },
      { token: 'number', foreground: 'F5A623' },
      { token: 'comment', foreground: '617B98', fontStyle: 'italic' },
    ],
    colors: {
      'editor.background': '#07111D',
      'editor.foreground': '#DCE8F6',
      'editorLineNumber.foreground': '#617B98',
      'editorLineNumber.activeForeground': '#DCE8F6',
      'editor.lineHighlightBackground': '#10294340',
      'editorGutter.background': '#07111D',
      'editorCursor.foreground': '#1677FF',
      'editorWhitespace.foreground': '#173149',
    },
  });

  monacoInstance.editor.defineTheme('securelex-theme-light', {
    base: 'vs',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '0969DA', fontStyle: 'bold' },
      { token: 'string', foreground: '1A7F37' },
      { token: 'identifier', foreground: '0F172A' },
      { token: 'type', foreground: '0E7490', fontStyle: 'bold' },
      { token: 'number', foreground: '9A6700' },
      { token: 'comment', foreground: '475569', fontStyle: 'italic' },
      { token: 'delimiter', foreground: '0F172A' },
      { token: 'operator', foreground: '0F172A' },
    ],
    colors: {
      'editor.background': '#FAFBFC',
      'editor.foreground': '#0F172A',
      'editorLineNumber.foreground': '#475569',
      'editorLineNumber.activeForeground': '#0F172A',
      'editor.lineHighlightBackground': '#E8ECF280',
      'editorGutter.background': '#F1F5F9',
      'editorCursor.foreground': '#0969DA',
      'editorWhitespace.foreground': '#CBD5E1',
      'editorIndentGuide.background': '#E2E8F0',
      'editorIndentGuide.activeBackground': '#CBD5E1',
    },
  });
}

