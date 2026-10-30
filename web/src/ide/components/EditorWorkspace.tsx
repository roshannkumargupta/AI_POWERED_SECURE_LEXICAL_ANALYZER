import React, { useState, useRef, useEffect, lazy, Suspense } from 'react';
import type * as Monaco from 'monaco-editor';
import { EditorTabs } from './EditorTabs';
import type { IDEDocument } from '../state/store';
import { registerSecureLexThemes } from '../../theme/monacoTheme';

const MonacoEditor = lazy(() => import('../lib/MonacoEditor'));

interface EditorWorkspaceProps {
  documents: IDEDocument[];
  activeDoc: IDEDocument | null;
  onSelectDoc: (id: string) => void;
  onCloseDoc: (id: string) => void;
  onSourceChange: (source: string) => void;
  onSave?: () => void;
  currentLanguage: string;
  onSelectLanguage: (lang: string) => void;
  isAnalyzing: boolean;
  onAnalyze: () => void;
  onSubRoutine: (routine: string) => void;
  onRunAllAgents: () => void;
  onOpenBuildWithAi: () => void;
  onFocusFixInAssistant: () => void;
  cursorLine: number;
  cursorCol: number;
  onCursorChange: (line: number, col: number) => void;
  isMaximized: boolean;
  resolvedTheme: 'dark' | 'light';
  fontSize?: number;
  wordWrap?: 'on' | 'off';
  onToggleWordWrap?: () => void;
  minimap?: boolean;
  tabSize?: number;
  bottomHeight?: number;
  bottomCollapsed?: boolean;
  onBottomResizeStart?: (e: React.PointerEvent) => void;
  onShowToast: (msg: string, type?: 'info' | 'success' | 'warning' | 'error') => void;
  children: React.ReactNode;
  editorRef: React.MutableRefObject<Monaco.editor.IStandaloneCodeEditor | null>;
}

const monacoLangMap: Record<string, string> = {
  'c++': 'cpp',
  cpp: 'cpp',
  c: 'cpp',
  python: 'python',
  py: 'python',
  java: 'java',
  javascript: 'javascript',
  js: 'javascript',
  typescript: 'typescript',
  ts: 'typescript',
  markdown: 'markdown',
  md: 'markdown',
};

export const EditorWorkspace: React.FC<EditorWorkspaceProps> = ({
  documents,
  activeDoc,
  onSelectDoc,
  onCloseDoc,
  onSourceChange,
  onSave,
  currentLanguage,
  onSelectLanguage,
  isAnalyzing,
  onAnalyze,
  onSubRoutine,
  onRunAllAgents,
  onOpenBuildWithAi,
  onFocusFixInAssistant,
  cursorLine,
  cursorCol,
  onCursorChange,
  isMaximized,
  resolvedTheme,
  fontSize = 13,
  wordWrap = 'on',
  onToggleWordWrap,
  minimap = true,
  tabSize = 4,
  bottomHeight = 280,
  bottomCollapsed = false,
  onBottomResizeStart,
  onShowToast,
  children,
  editorRef,
}) => {
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [furtherMenuOpen, setFurtherMenuOpen] = useState(false);

  const langSelectRef = useRef<HTMLDivElement>(null);
  const furtherMenuRef = useRef<HTMLDivElement>(null);
  const viewStatesRef = useRef<Record<string, Monaco.editor.ICodeEditorViewState | null>>({});
  const prevDocIdRef = useRef<string | null>(null);

  // Preserve scroll, cursor, and selection state across tab switches
  useEffect(() => {
    if (!editorRef.current) return;
    if (prevDocIdRef.current && prevDocIdRef.current !== activeDoc?.id) {
      viewStatesRef.current[prevDocIdRef.current] = editorRef.current.saveViewState();
    }
    if (activeDoc?.id) {
      const saved = viewStatesRef.current[activeDoc.id];
      if (saved) {
        editorRef.current.restoreViewState(saved);
      }
      prevDocIdRef.current = activeDoc.id;
    }
  }, [activeDoc?.id, editorRef]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (langSelectRef.current && !langSelectRef.current.contains(e.target as Node)) {
        setLangMenuOpen(false);
      }
      if (furtherMenuRef.current && !furtherMenuRef.current.contains(e.target as Node)) {
        setFurtherMenuOpen(false);
      }
    };
    document.addEventListener('pointerdown', handleClickOutside);
    return () => document.removeEventListener('pointerdown', handleClickOutside);
  }, []);

  const languageDisplayName =
    currentLanguage.toLowerCase() === 'cpp' || currentLanguage.toLowerCase() === 'c++'
      ? 'C++'
      : currentLanguage.toLowerCase() === 'python'
      ? 'Python'
      : currentLanguage.toLowerCase() === 'java'
      ? 'Java'
      : currentLanguage.toLowerCase() === 'javascript' || currentLanguage.toLowerCase() === 'js'
      ? 'JavaScript'
      : currentLanguage;

  const standardSubLabel =
    languageDisplayName === 'C++'
      ? 'C++20'
      : languageDisplayName === 'Python'
      ? 'PEP 538'
      : languageDisplayName === 'Java'
      ? 'Java 17'
      : 'ES2024';

  const folderName = activeDoc?.name.includes('/') ? activeDoc.name.split('/')[0] : 'src';
  const fileName = activeDoc?.name.replace(/^src\//, '') ?? 'main.cpp';

  const handleEditorDidMount = (
    editor: Monaco.editor.IStandaloneCodeEditor,
    monacoInstance: typeof Monaco
  ) => {
    editorRef.current = editor;
    (window as any).monaco = monacoInstance;

    // Define SecureLex custom themes for Monaco matching reference colors
    registerSecureLexThemes(monacoInstance);

    monacoInstance.editor.setTheme(
      resolvedTheme === 'dark' ? 'securelex-theme-dark' : 'securelex-theme-light'
    );

    // Track cursor movements
    editor.onDidChangeCursorPosition((e) => {
      onCursorChange(e.position.lineNumber, e.position.column);
    });

    // Keyboard shortcut for Analyze: Cmd+Enter or Ctrl+Enter
    editor.addCommand(monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.Enter, () => {
      onAnalyze();
    });

    // Keyboard shortcut for Save: Cmd+S or Ctrl+S
    editor.addCommand(monacoInstance.KeyMod.CtrlCmd | monacoInstance.KeyCode.KeyS, () => {
      onSave?.();
    });
  };

  useEffect(() => {
    if (editorRef.current) {
      const monacoGlobal = (window as any).monaco;
      if (monacoGlobal) {
        monacoGlobal.editor.setTheme(
          resolvedTheme === 'dark' ? 'securelex-theme-dark' : 'securelex-theme-light'
        );
      }
    }
  }, [resolvedTheme, editorRef]);

  const currentMonacoLang =
    monacoLangMap[activeDoc?.language.toLowerCase() ?? ''] ||
    monacoLangMap[currentLanguage.toLowerCase() ?? ''] ||
    'cpp';

  return (
    <main className="flex-1 flex flex-col min-w-0 border-r border-border-primary bg-surface-editor overflow-hidden transition-colors">
      {/* ================= TOP ACTION TOOLBAR ================= */}
      <div className="h-10 px-3 bg-surface-deepest border-b border-border-primary flex items-center justify-between shrink-0 gap-2 transition-colors">
        <div className="flex items-center gap-2 min-w-0">
          {/* Language Selector */}
          <div className="relative shrink-0" ref={langSelectRef}>
            <button
              type="button"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-container border border-border-primary text-text-primary hover:bg-surface-hover text-[11px] font-semibold transition-colors shadow-xs"
              id="btnLangSelect"
              onClick={() => setLangMenuOpen(!langMenuOpen)}
            >
              <span className="font-mono text-primary" id="curLangBadge">
                {languageDisplayName}
              </span>
              <span className="text-[10px] text-text-muted font-normal">{standardSubLabel}</span>
              <span className="material-symbols-outlined text-[13px] text-text-muted">expand_more</span>
            </button>
            {langMenuOpen && (
              <div
                className="absolute left-0 top-full mt-1 w-36 bg-surface-elevated border border-border-primary shadow-2xl rounded-md py-1 z-50"
                id="langMenu"
              >
                <button
                  type="button"
                  className="w-full text-left px-2.5 py-1.5 text-[11px] text-text-primary hover:bg-surface-hover flex items-center justify-between"
                  onClick={() => {
                    setLangMenuOpen(false);
                    onSelectLanguage('C++');
                  }}
                >
                  <span>C++ (C++20)</span>
                  {languageDisplayName === 'C++' && (
                    <span className="text-[10px] text-primary font-mono">active</span>
                  )}
                </button>
                <button
                  type="button"
                  className="w-full text-left px-2.5 py-1.5 text-[11px] text-text-secondary hover:bg-surface-hover"
                  onClick={() => {
                    setLangMenuOpen(false);
                    onSelectLanguage('Python');
                  }}
                >
                  Python 3
                </button>
                <button
                  type="button"
                  className="w-full text-left px-2.5 py-1.5 text-[11px] text-text-secondary hover:bg-surface-hover"
                  onClick={() => {
                    setLangMenuOpen(false);
                    onSelectLanguage('Java');
                  }}
                >
                  Java 17
                </button>
                <button
                  type="button"
                  className="w-full text-left px-2.5 py-1.5 text-[11px] text-text-secondary hover:bg-surface-hover"
                  onClick={() => {
                    setLangMenuOpen(false);
                    onSelectLanguage('JavaScript');
                  }}
                >
                  JavaScript
                </button>
              </div>
            )}
          </div>

          <div className="h-4 w-[1px] bg-border-primary shrink-0" />

          {/* Editor Tab Strip */}
          <EditorTabs
            documents={documents}
            activeDocId={activeDoc?.id ?? null}
            onSelectDoc={onSelectDoc}
            onCloseDoc={onCloseDoc}
          />
        </div>

        {/* Sleek Adaptive Action Buttons */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* 1. Analyze */}
          <button
            type="button"
            className="flex items-center gap-1.5 px-3 py-1 bg-primary hover:bg-primary-hover text-white rounded-md text-[11px] font-semibold shadow-sm active:scale-[0.98] transition-all ring-1 ring-primary/30 disabled:opacity-50"
            id="btnAnalyze"
            onClick={onAnalyze}
            disabled={isAnalyzing}
          >
            <span
              className={`material-symbols-outlined text-[15px] ${isAnalyzing ? 'animate-spin' : ''}`}
              id="analyzeIcon"
            >
              {isAnalyzing ? 'sync' : 'play_arrow'}
            </span>
            <span id="analyzeText">{isAnalyzing ? 'Analyzing...' : 'Analyze'}</span>
            <kbd className="hidden xl:inline-block ml-0.5 px-1 py-0.2 bg-white/20 rounded text-[9px] font-mono font-normal">
              ⌘↵
            </kbd>
          </button>

          {/* 2. Save */}
          {onSave && (
            <button
              type="button"
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all shadow-xs border ${
                activeDoc?.dirty
                  ? 'bg-status-warning/15 text-status-warning border-status-warning/40 hover:bg-status-warning/25'
                  : 'bg-surface-container text-text-secondary border-border-primary hover:bg-surface-hover hover:text-text-primary'
              }`}
              id="btnSaveFile"
              onClick={onSave}
              title="Save file (Ctrl+S / ⌘S)"
            >
              <span className="material-symbols-outlined text-[14px]">save</span>
              <span>Save</span>
              {activeDoc?.dirty && (
                <span className="w-1.5 h-1.5 rounded-full bg-status-warning animate-pulse" />
              )}
              <kbd className="hidden xl:inline-block ml-0.5 px-1 py-0.2 bg-white/20 rounded text-[9px] font-mono font-normal">
                ⌘S
              </kbd>
            </button>
          )}

          {/* 2. Further Analysis Dropdown */}
          <div className="relative" ref={furtherMenuRef}>
            <button
              type="button"
              className="flex items-center gap-1 px-2.5 py-1 bg-surface-container hover:bg-surface-hover text-text-secondary hover:text-text-primary border border-border-primary rounded-md text-[11px] font-medium transition-colors shadow-xs"
              id="btnFurtherAnalysis"
              onClick={() => setFurtherMenuOpen(!furtherMenuOpen)}
            >
              <span>Further Analysis</span>
              <span className="material-symbols-outlined text-[13px] text-text-muted">expand_more</span>
            </button>
            {furtherMenuOpen && (
              <div
                className="absolute right-0 top-full mt-1.5 w-48 bg-surface-elevated border border-border-primary rounded-md shadow-2xl z-50 py-1 divide-y divide-border-subtle"
                id="furtherMenu"
              >
                <div className="py-0.5">
                  <button
                    type="button"
                    className="w-full text-left px-3 py-1.5 text-[11px] text-text-secondary hover:bg-surface-hover hover:text-text-primary flex items-center gap-2 transition-colors"
                    onClick={() => {
                      setFurtherMenuOpen(false);
                      onSubRoutine('Syntax Verification');
                    }}
                  >
                    <span className="material-symbols-outlined text-status-success text-[14px]">
                      account_tree
                    </span>
                    Syntax Verification
                  </button>
                  <button
                    type="button"
                    className="w-full text-left px-3 py-1.5 text-[11px] text-text-secondary hover:bg-surface-hover hover:text-text-primary flex items-center gap-2 transition-colors"
                    onClick={() => {
                      setFurtherMenuOpen(false);
                      onSubRoutine('Semantic Typing Check');
                    }}
                  >
                    <span className="material-symbols-outlined text-primary text-[14px]">schema</span>
                    Semantic Typing Check
                  </button>
                  <button
                    type="button"
                    className="w-full text-left px-3 py-1.5 text-[11px] text-text-secondary hover:bg-surface-hover hover:text-text-primary flex items-center gap-2 transition-colors"
                    onClick={() => {
                      setFurtherMenuOpen(false);
                      onSubRoutine('Taint Analysis');
                    }}
                  >
                    <span className="material-symbols-outlined text-status-warning text-[14px]">
                      security
                    </span>
                    Taint Analysis
                  </button>
                </div>
                <div className="py-0.5">
                  <button
                    type="button"
                    className="w-full text-left px-3 py-1.5 text-[11px] text-accent-ai hover:bg-surface-hover flex items-center gap-2 transition-colors font-medium"
                    onClick={() => {
                      setFurtherMenuOpen(false);
                      onSubRoutine('Full Security Audit');
                    }}
                  >
                    <span className="material-symbols-outlined text-accent-ai text-[14px]">
                      verified_user
                    </span>
                    Full Security Audit
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* 3. Run All Agents */}
          <button
            type="button"
            className="flex items-center gap-1.5 px-2.5 py-1 bg-surface-container hover:bg-surface-hover text-text-secondary hover:text-text-primary border border-border-primary rounded-md text-[11px] font-medium transition-colors shadow-xs"
            onClick={onRunAllAgents}
            title="Execute 4 pipeline agents simultaneously"
          >
            <span className="material-symbols-outlined text-[14px] text-primary">hub</span>
            <span className="hidden lg:inline">Run All Agents</span>
            <span className="px-1 py-0.2 bg-primary/20 text-primary font-mono text-[9px] rounded font-bold">
              4
            </span>
          </button>

          {/* 4. Build with AI */}
          <button
            type="button"
            className="flex items-center gap-1.5 px-2.5 py-1 bg-accent-ai/10 hover:bg-accent-ai/20 text-accent-ai border border-accent-ai/35 rounded-md text-[11px] font-semibold transition-all shadow-xs active:scale-[0.98]"
            onClick={onOpenBuildWithAi}
          >
            <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
            <span className="hidden md:inline">Build with AI</span>
          </button>

          {/* 5. Fix with AI */}
          <button
            type="button"
            className="flex items-center gap-1.5 px-2.5 py-1 bg-accent-fix/10 hover:bg-accent-fix/20 text-accent-fix border border-accent-fix/35 rounded-md text-[11px] font-semibold transition-all shadow-xs active:scale-[0.98]"
            onClick={onFocusFixInAssistant}
          >
            <span className="material-symbols-outlined text-[14px]">build</span>
            <span>Fix with AI</span>
          </button>
        </div>
      </div>

      {/* Breadcrumbs */}
      <nav className="h-6 px-3 bg-surface-editor border-b border-border-subtle flex items-center justify-between shrink-0 text-[11px] text-text-muted transition-colors">
        <div className="flex items-center gap-1.5 font-mono">
          <span className="material-symbols-outlined text-[13px] text-primary">data_object</span>
          <span className="text-text-secondary" id="breadcrumbFolder">
            {folderName}
          </span>
          <span className="text-text-muted text-[10px]">/</span>
          <span className="text-text-primary font-semibold" id="breadcrumbFile">
            {fileName}
          </span>
          <span className="text-text-muted text-[10px]">/</span>
          <span className="text-text-secondary" id="breadcrumbFunc">
            {languageDisplayName === 'C++' ? 'stripBOM()' : 'main()'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-text-muted font-mono hidden sm:inline">
            Ln {cursorLine}, Col {cursorCol} • UTF-8 • Tab: 4
          </span>
          {onToggleWordWrap && (
            <button
              type="button"
              className={`p-0.5 rounded transition-colors ${
                wordWrap === 'on' ? 'text-primary bg-primary/10' : 'text-text-muted hover:text-text-primary'
              }`}
              onClick={onToggleWordWrap}
              title={`Word Wrap: ${wordWrap === 'on' ? 'ON' : 'OFF'} (Click to toggle)`}
            >
              <span className="material-symbols-outlined text-[14px]">wrap_text</span>
            </button>
          )}
          <button
            type="button"
            className="p-0.5 hover:text-text-primary rounded transition-colors"
            onClick={() => onShowToast('Editor split view toggled')}
            title="Split Editor"
          >
            <span className="material-symbols-outlined text-[14px]">splitscreen_right</span>
          </button>
        </div>
      </nav>

      {/* Code Editor Workspace (Collapsible when maximized) */}
      {!isMaximized && (
        <div
          className="flex-1 min-h-[120px] bg-surface-editor flex border-b border-border-primary relative font-mono text-[13px] overflow-hidden transition-colors"
          id="editorArea"
        >
          <Suspense
            fallback={
              <div className="flex-1 flex items-center justify-center text-text-muted text-[12px]">
                Loading Monaco editor...
              </div>
            }
          >
            <MonacoEditor
              height="100%"
              language={currentMonacoLang}
              value={activeDoc?.source ?? ''}
              onChange={(value) => onSourceChange(value ?? '')}
              theme={resolvedTheme === 'dark' ? 'securelex-theme-dark' : 'securelex-theme-light'}
              beforeMount={(monacoInstance) => {
                (window as any).monaco = monacoInstance;
                registerSecureLexThemes(monacoInstance);
              }}
              onMount={handleEditorDidMount}
              options={{
                fontSize,
                fontFamily: "'JetBrains Mono', monospace",
                lineNumbers: 'on',
                lineNumbersMinChars: 3,
                minimap: { enabled: minimap, maxColumn: 40 },
                scrollBeyondLastLine: false,
                renderLineHighlight: 'all',
                automaticLayout: true,
                tabSize,
                wordWrap,
              }}
            />
          </Suspense>
        </div>
      )}

      {/* Resize Handle for Bottom Panel */}
      {!isMaximized && !bottomCollapsed && onBottomResizeStart && (
        <div
          className="h-1.5 w-full cursor-row-resize hover:bg-primary/40 active:bg-primary bg-border-primary/50 transition-colors shrink-0 z-30"
          onPointerDown={onBottomResizeStart}
          title="Drag to resize bottom panel"
        />
      )}

      {/* ================= BOTTOM RESULTS PANEL ================= */}
      {isMaximized ? (
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">{children}</div>
      ) : !bottomCollapsed ? (
        <div
          className="flex flex-col min-h-0 overflow-hidden shrink-0 transition-all"
          style={{ height: `${bottomHeight}px` }}
        >
          {children}
        </div>
      ) : null}
    </main>
  );
};
