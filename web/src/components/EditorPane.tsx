import React, { useEffect, useRef } from 'react';
import Editor, { loader, OnMount } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';

import { SECURELEX_THEME_NAME, securelexNightTheme } from '../theme/monacoTheme';
import { updateMonacoMarkers } from '../monaco/markers';
import { createHoverProvider, setHoverActionHandlers } from '../monaco/hover';
import { createCodeActionProvider, setCodeActionHandlers } from '../monaco/codeActions';
import { DecorationManager } from '../monaco/decorations';
import { Finding, Fix } from '../api/client';

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

interface EditorPaneProps {
  source: string;
  language: string;
  findings: Finding[];
  tokens: Array<{
    text: string;
    line: number;
    col: number;
    label: string;
    confidence: number;
    utf16_offset: number;
  }>;
  selectedFindingId: string | null;
  activeDataFlowFindingId: string | null;
  onChangeSource: (val: string) => void;
  onCursorChange: (pos: { line: number; col: number }) => void;
  onSelectToken: (tokenIndex: number) => void;
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
  findings,
  tokens,
  selectedFindingId,
  activeDataFlowFindingId,
  onChangeSource,
  onCursorChange,
  onSelectToken,
  onSelectFinding,
  onOpenDiff,
  onAnalyzeShortcut,
  onDownloadShortcut,
  onNextProblem,
  onPrevProblem,
}) => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const decorationManagerRef = useRef<DecorationManager | null>(null);
  const findingsRef = useRef<Finding[]>(findings);
  findingsRef.current = findings;

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

    // Define and apply theme
    monacoInstance.editor.defineTheme(SECURELEX_THEME_NAME, securelexNightTheme);
    monacoInstance.editor.setTheme(SECURELEX_THEME_NAME);

    // Initialize decoration manager
    const decManager = new DecorationManager(editor, monacoInstance);
    decorationManagerRef.current = decManager;

    // Register hover and code action providers
    const currentLang = getMonacoLanguage(language);
    monacoInstance.languages.registerHoverProvider(
      currentLang,
      createHoverProvider(() => findingsRef.current, monacoInstance)
    );

    monacoInstance.languages.registerCodeActionProvider(
      currentLang,
      createCodeActionProvider(() => findingsRef.current, monacoInstance)
    );

    // Register action callbacks
    setHoverActionHandlers({
      onQuickFix: (findingId) => {
        onSelectFinding(findingId);
        editor.trigger('hover', 'editor.action.quickFix', {});
      },
      onShowDataFlow: (findingId) => {
        onSelectFinding(findingId);
      },
    });

    setCodeActionHandlers({
      onOpenDiffView: (fix, finding) => onOpenDiff(fix, finding),
      onShowManualAdvice: (_fix, finding) => onSelectFinding(finding.id),
    });

    // Keyboard bindings
    // Ctrl+Enter -> Analyze
    editor.addCommand(monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.Enter, () => {
      onAnalyzeShortcut();
    });

    // Ctrl+S -> Download
    editor.addCommand(monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.KeyS, () => {
      onDownloadShortcut();
    });

    // F8 -> Next Problem
    editor.addCommand(monacoInstance.KeyCode.F8, () => {
      onNextProblem();
    });

    // Shift+F8 -> Previous Problem
    editor.addCommand(monacoInstance.KeyMod.Shift | monacoInstance.KeyCode.F8, () => {
      onPrevProblem();
    });

    // Cursor position listener
    editor.onDidChangeCursorPosition((e) => {
      onCursorChange({ line: e.position.lineNumber, col: e.position.column });
    });

    // Mouse down listener to select token under cursor for ML Insights
    editor.onMouseDown((e) => {
      if (!e.target.position) return;
      const { lineNumber, column } = e.target.position;

      // Find token matching coordinates
      if (tokens && tokens.length > 0) {
        const foundIdx = tokens.findIndex((t) => {
          if (t.line !== lineNumber) return false;
          const endCol = t.col + t.text.length;
          return column >= t.col && column <= endCol;
        });

        if (foundIdx !== -1) {
          onSelectToken(foundIdx);
        }
      }
    });

    // Initial markers update
    const model = editor.getModel();
    if (model) {
      updateMonacoMarkers(model, findingsRef.current, monacoInstance);
      decManager.updateUnicodeDecorations(findingsRef.current);
    }
  };

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

  // Jump to selected finding when selection changes
  useEffect(() => {
    if (!editorRef.current || !selectedFindingId) return;
    const finding = findings.find((f) => f.id === selectedFindingId);
    if (finding) {
      editorRef.current.revealRangeInCenter(
        new monaco.Range(
          finding.range.start_line,
          finding.range.start_col,
          finding.range.end_line,
          finding.range.end_col
        )
      );
      editorRef.current.setPosition({
        lineNumber: finding.range.start_line,
        column: finding.range.start_col,
      });
    }
  }, [selectedFindingId, findings]);

  return (
    <div style={containerStyle}>
      <Editor
        height="100%"
        width="100%"
        language={getMonacoLanguage(language)}
        value={source}
        theme={SECURELEX_THEME_NAME}
        onChange={(val) => onChangeSource(val || '')}
        onMount={handleEditorDidMount}
        options={{
          minimap: { enabled: true },
          lineNumbers: 'on',
          glyphMargin: true,
          bracketPairColorization: { enabled: true },
          renderControlCharacters: true,
          unicodeHighlight: {
            ambiguousCharacters: true,
            invisibleCharacters: true,
            nonBasicASCII: false,
          },
          fontFamily: 'var(--font-code)',
          fontSize: 14,
          lineHeight: 22,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          tabSize: 4,
          wordWrap: 'off',
        }}
      />
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  height: '100%',
  width: '100%',
  position: 'relative',
  overflow: 'hidden',
  backgroundColor: 'var(--bg)',
};
