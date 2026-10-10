import * as monaco from 'monaco-editor';
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';

export function initMonacoWorkers(): void {
  if (typeof window === 'undefined') return;
  (window as unknown as { MonacoEnvironment: unknown }).MonacoEnvironment = {
    getWorker(_: unknown, label: string) {
      if (label === 'json') return new jsonWorker();
      if (label === 'css' || label === 'scss' || label === 'less') return new cssWorker();
      if (label === 'html' || label === 'handlebars' || label === 'razor') return new htmlWorker();
      if (label === 'typescript' || label === 'javascript') return new tsWorker();
      return new editorWorker();
    },
  };
}

export function getMonacoLanguage(lang: string): string {
  switch (lang.toLowerCase()) {
    case 'python':
    case 'py':
      return 'python';
    case 'javascript':
    case 'js':
      return 'javascript';
    case 'java':
      return 'java';
    case 'cpp':
    case 'c++':
    case 'c':
      return 'cpp';
    default:
      return 'python';
  }
}

export const DEFAULT_MONACO_OPTIONS: monaco.editor.IStandaloneEditorConstructionOptions = {
  readOnly: false,
  domReadOnly: false,
  minimap: { enabled: false },
  lineNumbers: 'on',
  glyphMargin: true,
  bracketPairColorization: { enabled: false },
  renderControlCharacters: true,
  renderLineHighlight: 'none',
  unicodeHighlight: {
    ambiguousCharacters: true,
    invisibleCharacters: true,
    nonBasicASCII: false,
  },
  fontFamily: 'var(--font-code)',
  fontSize: 12,
  lineHeight: 24,
  scrollBeyondLastLine: false,
  automaticLayout: true,
  cursorBlinking: 'smooth',
  cursorSmoothCaretAnimation: 'on',
  smoothScrolling: true,
  tabSize: 4,
  wordWrap: 'off',
};

export function bindEditorCommands(
  editor: monaco.editor.IStandaloneCodeEditor,
  monacoInstance: typeof monaco,
  shortcuts: {
    onAnalyze: () => void;
    onDownload: () => void;
    onNextProblem: () => void;
    onPrevProblem: () => void;
  }
): void {
  editor.addCommand(
    monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.Enter,
    shortcuts.onAnalyze
  );
  editor.addCommand(
    monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.KeyS,
    shortcuts.onDownload
  );
  editor.addCommand(monacoInstance.KeyCode.F8, shortcuts.onNextProblem);
  editor.addCommand(
    monacoInstance.KeyMod.Shift | monacoInstance.KeyCode.F8,
    shortcuts.onPrevProblem
  );
}

import { buildMonacoTheme } from '../theme/monacoTheme';

export function applyMonacoTheme(monacoInstance: typeof monaco, themeName: string): void {
  const styles = getComputedStyle(document.documentElement);
  const themeTokens = Object.fromEntries(
    Array.from(styles)
      .filter((name) => name.startsWith('--'))
      .map((name) => [name, styles.getPropertyValue(name)])
  );
  monacoInstance.editor.defineTheme('securelex-dark', buildMonacoTheme(themeTokens, 'dark'));
  monacoInstance.editor.defineTheme('securelex-light', buildMonacoTheme(themeTokens, 'light'));
  monacoInstance.editor.setTheme(themeName);
}

export const editorPlaceholderStyle: React.CSSProperties = {
  position: 'absolute',
  top: 12,
  left: 76,
  color: 'var(--muted)',
  opacity: 0.6,
  fontFamily: 'var(--font-code)',
  fontSize: 12,
  pointerEvents: 'none',
};

export const editorContainerStyle: React.CSSProperties = {
  height: '100%',
  width: '100%',
  position: 'relative',
};
