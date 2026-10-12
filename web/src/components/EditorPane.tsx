import React, { useEffect, useRef } from 'react';
import Editor, { loader, OnMount } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

import { useTheme } from '../theme/theme';
import { updateMonacoMarkers } from '../monaco/markers';
import { createHoverProvider, setHoverActionHandlers } from '../monaco/hover';
import { createCodeActionProvider, setCodeActionHandlers } from '../monaco/codeActions';
import { DecorationManager } from '../monaco/decorations';
import { AnalysisResult, Finding, Fix } from '../api/client';
import type { TokenInfo } from '../api/client';
import { setEditorSelection, revealEditorRange } from '../editor/navigation';
import { harness } from '../testHarness';
import {
  initMonacoWorkers,
  getMonacoLanguage,
  DEFAULT_MONACO_OPTIONS,
  bindEditorCommands,
  applyMonacoTheme,
  editorContainerStyle,
  editorPlaceholderStyle,
} from '../monaco/setupMonaco';

// Configure Monaco Environment for Vite with locally bundled web workers (NO CDN)
initMonacoWorkers();
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

  const handleEditorDidMount: OnMount = (editor, monacoInstance) => {
    editorRef.current = editor;
    harness.setEditor(editor);

    applyMonacoTheme(monacoInstance, themeName);
    void document.fonts.ready.then(() => monacoInstance.editor.remeasureFonts());

    const decManager = new DecorationManager(editor, monacoInstance);
    decorationManagerRef.current = decManager;

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

    setHoverActionHandlers({
      onQuickFix: (findingId: string) => onSelectFinding(findingId),
      onShowDataFlow: (findingId: string) => onSelectFinding(findingId),
    });

    setCodeActionHandlers({
      onOpenDiffView: (fix: Fix, finding: Finding) => onOpenDiff(fix, finding),
    });

    bindEditorCommands(editor, monacoInstance, {
      onAnalyze: onAnalyzeShortcut,
      onDownload: onDownloadShortcut,
      onNextProblem,
      onPrevProblem,
    });

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

    const model = editor.getModel();
    if (model) {
      updateMonacoMarkers(model, findingsRef.current, monacoInstance);
      decManager.updateUnicodeDecorations(findingsRef.current);
    }
  };

  useEffect(() => {
    applyMonacoTheme(monaco, themeName);
  }, [resolved, themeName]);

  useEffect(() => {
    if (!editorRef.current) return;
    const model = editorRef.current.getModel();
    if (model) {
      updateMonacoMarkers(model, findings, monaco);
      decorationManagerRef.current?.updateUnicodeDecorations(findings);
    }
  }, [findings]);

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

  useEffect(() => {
    if (!editorRef.current || !navTarget) return;
    const { range, type } = navTarget;
    revealEditorRange(
      editorRef.current,
      new monaco.Range(range.start_line, range.start_col, range.end_line, range.end_col),
      `user-nav-${type}`
    );
    setEditorSelection(
      editorRef.current,
      new monaco.Selection(range.start_line, range.start_col, range.end_line, range.end_col),
      type === 'token' ? 'user-nav-token' : 'user-nav-diagnostic'
    );
  }, [navTarget]);

  return (
    <div style={editorContainerStyle}>
      <Editor
        height="100%"
        width="100%"
        path={`inmemory://securelex/${encodeURIComponent(modelKey || filename || 'untitled')}`}
        language={getMonacoLanguage(language)}
        defaultValue={source}
        theme={themeName}
        onChange={(val) => onChangeSource(val || '')}
        onMount={handleEditorDidMount}
        options={DEFAULT_MONACO_OPTIONS}
      />
      {!source && (
        <div style={editorPlaceholderStyle}>
          Type or paste code. The language is detected automatically.
        </div>
      )}
    </div>
  );
};
