import React, { useEffect, useRef } from 'react';
import Editor, { loader, OnMount } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';

import { buildMonacoTheme } from '../theme/monacoTheme';
import { useTheme } from '../theme/theme';
import { updateMonacoMarkers } from '../monaco/markers';
import { createHoverProvider, setHoverActionHandlers } from '../monaco/hover';
import { createCodeActionProvider, setCodeActionHandlers } from '../monaco/codeActions';
import { DecorationManager } from '../monaco/decorations';
import { AnalysisResult, Finding, Fix } from '../api/client';
import type { TokenInfo } from '../api/client';
import { setEditorPosition, setEditorSelection, revealEditorRange } from '../editor/navigation';
import { harness } from '../testHarness';

// Configure Monaco Environment for Vite with locally bundled web workers (NO CDN)
if (typeof window !== 'undefined') {
  (window as any).MonacoEnvironment = {
    getWorker(_: any, label: string) {
      if (label === 'json') return new jsonWorker();
      if (label === 'css' || label === 'scss' || label === 'less') return new cssWorker();
      if (label === 'html' || label === 'handlebars' || label === 'razor') return new htmlWorker();
      if (label === 'typescript' || label === 'javascript') return new tsWorker();
      return new editorWorker();
    },
  };
}

loader.config({ monaco });

export interface NavTarget {
  type: 'token' | 'finding';
  range: { start_line: number; start_col: number; end_line: number; end_col: number };
  timestamp: number;
}

interface EditorPaneProps {
  source: string;
  language: string;
  filename: string;
  modelKey?: string | null;
  findings: Finding[];
  tokens: TokenInfo[];
  analysis: AnalysisResult | null;
  selectedTokenIndex: number | null;
  tokenMap: 'off' | 'security' | 'full';
  tokenCategory: string;
  selectedFindingId: string | null;
  activeDataFlowFindingId: string | null;
  navTarget?: NavTarget | null;
  onChangeSource: (val: string) => void;
  onCursorChange: (pos: { line: number; col: number }) => void;
  onSelectToken: (tokenIndex: number | null) => void;
  onOpenTokens: () => void;
  onSelectFinding: (findingId: string) => void;
  onOpenDiff: (fix: Fix, finding: Finding) => void;
  onAnalyzeShortcut: () => void;
  onDownloadShortcut: () => void;
  onNextProblem: () => void;
  onPrevProblem: () => void;
}

export const EditorPane: React.FC<EditorPaneProps> = ({
  source,
  language,
  filename,
  modelKey,
  findings,
  tokens,
  analysis,
  selectedTokenIndex,
  tokenMap,
  tokenCategory,
  selectedFindingId: _selectedFindingId,
  activeDataFlowFindingId,
  navTarget,
  onChangeSource,
  onCursorChange,
  onSelectToken,
  onOpenTokens: _onOpenTokens,
  onSelectFinding,
  onOpenDiff,
  onAnalyzeShortcut,
  onDownloadShortcut,
  onNextProblem,
  onPrevProblem,
}) => {
  const { resolved } = useTheme();
  const themeName = `securelex-${resolved}`;
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const decorationManagerRef = useRef<DecorationManager | null>(null);
  const findingsRef = useRef<Finding[]>(findings);
  const tokensRef = useRef(tokens);
  const onSelectTokenRef = useRef(onSelectToken);
  const prevModelKeyRef = useRef<string | null>(null);
  const viewStatesRef = useRef<Map<string, monaco.editor.ICodeEditorViewState>>(new Map());

  findingsRef.current = findings;
  tokensRef.current = tokens;
  onSelectTokenRef.current = onSelectToken;

  // Keep React-originated replacements (new/open sample, verified fix) in sync,
  // while leaving ordinary keystrokes to Monaco so its cursor and undo stack survive.
  useEffect(() => {
    const editor = editorRef.current;
    const model = editor?.getModel();
    if (!editor || !model || model.getValue() === source) return;
    const view = editor.saveViewState();
    editor.executeEdits(
      'securelex-external-change',
      [{ range: model.getFullModelRange(), text: source }],
      () => editor.getSelections()
    );
    if (view) editor.restoreViewState(view);
  }, [source]);

  // View state preservation when switching tabs/documents
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const currentKey = modelKey || filename || 'untitled';
    if (prevModelKeyRef.current && prevModelKeyRef.current !== currentKey) {
      const prevViewState = editor.saveViewState();
      if (prevViewState) {
        viewStatesRef.current.set(prevModelKeyRef.current, prevViewState);
      }
      const newViewState = viewStatesRef.current.get(currentKey);
      if (newViewState) {
        editor.restoreViewState(newViewState);
      }
    }
    prevModelKeyRef.current = currentKey;
  }, [modelKey, filename]);

  // Language mapping to Monaco IDs
  const getMonacoLanguage = (lang: string) => {
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
  };

  const handleEditorDidMount: OnMount = (editor, monacoInstance) => {
    editorRef.current = editor;
    harness.setEditor(editor);

    // Define and apply theme
    const styles = getComputedStyle(document.documentElement);
    const themeTokens = Object.fromEntries(
      Array.from(styles)
        .filter((name) => name.startsWith('--'))
        .map((name) => [name, styles.getPropertyValue(name)])
    );
    monacoInstance.editor.defineTheme('securelex-dark', buildMonacoTheme(themeTokens, 'dark'));
    monacoInstance.editor.defineTheme('securelex-light', buildMonacoTheme(themeTokens, 'light'));
    monacoInstance.editor.setTheme(themeName);
    void document.fonts.ready.then(() => monacoInstance.editor.remeasureFonts());

    // Initialize decoration manager
    const decManager = new DecorationManager(editor, monacoInstance);
    decorationManagerRef.current = decManager;

    // Register hover and code action providers for all supported languages
    ['python', 'javascript', 'java', 'cpp'].forEach((lang) => {
      monacoInstance.languages.registerHoverProvider(
        lang,
        createHoverProvider(() => findingsRef.current, monacoInstance)
      );

      monacoInstance.languages.registerCodeActionProvider(
        lang,
        createCodeActionProvider(() => findingsRef.current, monacoInstance)
      );
    });

    // Wire global action handlers for Monaco Hover widgets
    setHoverActionHandlers({
      onQuickFix: (findingId: string) => onSelectFinding(findingId),
      onShowDataFlow: (findingId: string) => onSelectFinding(findingId),
    });

    // Wire action handlers for Code Action Lightbulb Quick Fixes
    setCodeActionHandlers({
      onOpenDiffView: (fix: Fix, finding: Finding) => onOpenDiff(fix, finding),
    });

    // Keybindings inside Monaco
    editor.addCommand(monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.Enter, () => {
      onAnalyzeShortcut();
    });

    editor.addCommand(monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.KeyS, () => {
      onDownloadShortcut();
    });

    editor.addCommand(monacoInstance.KeyCode.F8, () => {
      onNextProblem();
    });

    editor.addCommand(monacoInstance.KeyMod.Shift | monacoInstance.KeyCode.F8, () => {
      onPrevProblem();
    });

    // Cursor tracking with 50ms debounced token table highlight sync
    let cursorTimer: number | undefined;
    let lastCursorToken: number = -1;

    editor.onDidChangeCursorPosition((e) => {
      harness.recordCursorChange(e.position.lineNumber, e.position.column, 'monaco', e.reason);
      onCursorChange({ line: e.position.lineNumber, col: e.position.column });
      window.clearTimeout(cursorTimer);
      cursorTimer = window.setTimeout(() => {
        const index = tokensRef.current.findIndex((t) => {
          const r = t.range;
          return (
            r &&
            (e.position.lineNumber > r.start_line ||
              (e.position.lineNumber === r.start_line && e.position.column >= r.start_col)) &&
            (e.position.lineNumber < r.end_line ||
              (e.position.lineNumber === r.end_line && e.position.column < r.end_col))
          );
        });
        if (index !== lastCursorToken) {
          lastCursorToken = index;
          onSelectTokenRef.current(index >= 0 ? index : null);
        }
      }, 50);
    });

    editor.onDidChangeCursorSelection((e) => {
      harness.recordCursorChange(
        e.selection.startLineNumber,
        e.selection.startColumn,
        'monaco',
        e.reason
      );
    });

    // Initial markers update
    const model = editor.getModel();
    if (model) {
      updateMonacoMarkers(model, findingsRef.current, monacoInstance);
      decManager.updateUnicodeDecorations(findingsRef.current);
    }
  };

  useEffect(() => {
    const styles = getComputedStyle(document.documentElement);
    const themeTokens = Object.fromEntries(
      Array.from(styles)
        .filter((name) => name.startsWith('--'))
        .map((name) => [name, styles.getPropertyValue(name)])
    );
    monaco.editor.defineTheme('securelex-dark', buildMonacoTheme(themeTokens, 'dark'));
    monaco.editor.defineTheme('securelex-light', buildMonacoTheme(themeTokens, 'light'));
    monaco.editor.setTheme(themeName);
  }, [resolved, themeName]);

  // Synchronize markers whenever findings change
  useEffect(() => {
    if (!editorRef.current) return;
    const model = editorRef.current.getModel();
    if (model) {
      updateMonacoMarkers(model, findings, monaco);
      decorationManagerRef.current?.updateUnicodeDecorations(findings);
    }
  }, [findings]);

  // Synchronize taint flow decorations
  useEffect(() => {
    if (!decorationManagerRef.current) return;

    if (!activeDataFlowFindingId) {
      decorationManagerRef.current.updateTaintPath(null);
      return;
    }

    const finding = findings.find((f) => f.id === activeDataFlowFindingId);
    if (finding && finding.taint_path) {
      decorationManagerRef.current.updateTaintPath(finding.taint_path);
    } else {
      decorationManagerRef.current.updateTaintPath(null);
    }
  }, [activeDataFlowFindingId, findings]);

  useEffect(() => {
    decorationManagerRef.current?.updateTokenMap(
      tokenMap,
      analysis,
      selectedTokenIndex,
      tokenCategory
    );
  }, [tokenMap, analysis, selectedTokenIndex, tokenCategory]);

  useEffect(() => {
    decorationManagerRef.current?.updateSecurityDecorations(analysis, selectedTokenIndex);
  }, [analysis, selectedTokenIndex]);

  // Explicit user navigation ONLY (clicking row in token table or finding list, or F8)
  useEffect(() => {
    if (!editorRef.current || !navTarget) return;
    const { range, type } = navTarget;
    revealEditorRange(
      editorRef.current,
      new monaco.Range(range.start_line, range.start_col, range.end_line, range.end_col),
      `user-nav-${type}`
    );
    if (type === 'token') {
      setEditorSelection(
        editorRef.current,
        new monaco.Selection(range.start_line, range.start_col, range.end_line, range.end_col),
        'user-nav-token'
      );
    } else {
      setEditorPosition(editorRef.current, range.start_line, range.start_col, 'user-nav-finding');
    }
  }, [navTarget]);

  return (
    <div style={containerStyle}>
      <Editor
        height="100%"
        width="100%"
        path={`inmemory://securelex/${encodeURIComponent(modelKey || filename || 'untitled')}`}
        language={getMonacoLanguage(language)}
        defaultValue={source}
        theme={themeName}
        onChange={(val) => onChangeSource(val || '')}
        onMount={handleEditorDidMount}
        options={{
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
        }}
      />
      {!source && (
        <div style={placeholderStyle}>
          Type or paste code. The language is detected automatically.
        </div>
      )}
    </div>
  );
};

const placeholderStyle: React.CSSProperties = {
  position: 'absolute',
  top: 12,
  left: 76,
  color: 'var(--muted)',
  opacity: 0.6,
  fontFamily: 'var(--font-code)',
  fontSize: 12,
  pointerEvents: 'none',
};

const containerStyle: React.CSSProperties = {
  height: '100%',
  width: '100%',
  position: 'relative',
};
