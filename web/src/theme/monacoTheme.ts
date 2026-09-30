import type { editor } from 'monaco-editor';

export const SECURELEX_THEME_NAME = 'securelex-night';

export const securelexNightTheme: editor.IStandaloneThemeData = {
  base: 'vs-dark',
  inherit: true,
  rules: [
    { token: '', foreground: 'E6EDF7', background: '0B0F17' },
    { token: 'comment', foreground: '5B6D88', fontStyle: 'italic' },
    { token: 'keyword', foreground: '4F8CFF', fontStyle: 'bold' },
    { token: 'string', foreground: '3DDC97' },
    { token: 'number', foreground: 'F5C542' },
    { token: 'regexp', foreground: 'FF8A3D' },
    { token: 'type', foreground: '5CC8FF' },
    { token: 'class', foreground: '5CC8FF' },
    { token: 'function', foreground: '8FA1BB' },
    { token: 'variable', foreground: 'E6EDF7' },
    { token: 'operator', foreground: '8FA1BB' },
    { token: 'delimiter', foreground: '8FA1BB' },
  ],
  colors: {
    // Canvas & Editor Base
    'editor.background': '#0B0F17',
    'editor.foreground': '#E6EDF7',
    'editorCursor.foreground': '#4F8CFF',
    'editor.lineHighlightBackground': '#131B2A',
    'editor.lineHighlightBorder': '#1A2538',
    'editor.selectionBackground': '#1E3A66',
    'editor.inactiveSelectionBackground': '#162842',
    'editor.selectionHighlightBackground': '#1A3359',
    
    // Gutter and Margins
    'editorLineNumber.foreground': '#5B6D88',
    'editorLineNumber.activeForeground': '#E6EDF7',
    'editorGutter.background': '#0B0F17',
    'editorGutter.modifiedBackground': '#5CC8FF',
    'editorGutter.addedBackground': '#3DDC97',
    'editorGutter.deletedBackground': '#FF4D6D',

    // Squiggle Colors (Severity-Mapped)
    'editorError.foreground': '#FF4D6D',
    'editorWarning.foreground': '#F5C542',
    'editorInfo.foreground': '#5CC8FF',
    'editorHint.foreground': '#8FA1BB',

    // Minimap
    'minimap.background': '#0B0F17',
    'minimap.selectionHighlight': '#1E3A66',
    'minimap.errorHighlight': '#FF4D6D',
    'minimap.warningHighlight': '#F5C542',

    // Widgets & Popups
    'editorWidget.background': '#111826',
    'editorWidget.border': '#223049',
    'editorHoverWidget.background': '#111826',
    'editorHoverWidget.border': '#223049',
    'editorHoverWidget.statusBarBackground': '#161E2E',
    'editorSuggestWidget.background': '#111826',
    'editorSuggestWidget.border': '#223049',
    'editorSuggestWidget.selectedBackground': '#1E3A66',

    // Brackets & Indentation
    'editorIndentGuide.background': '#1A2538',
    'editorIndentGuide.activeBackground': '#2A3C5B',
    'editorBracketMatch.background': '#1E3A66',
    'editorBracketMatch.border': '#4F8CFF',
  },
};
