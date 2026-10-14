import React, { useEffect, useRef, useCallback, useState } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

import { useApp } from './state/store';
import { api, TaintPathStep } from './api/client';
import { TopBar } from './components/TopBar';
import { NavTarget } from './components/EditorPane';
import { StatusBar } from './components/StatusBar';
import { deriveTokens } from './tokens/derive';
import { DEMO_PATH } from './utils/sampleDemo';
import { computeUiScale } from './utils/uiScale';
import { useTheme } from './theme/theme';
import { ExplanationPanel } from './components/ExplanationPanel';
import { harness } from './testHarness';
import { DocItem } from './model/doc';
import { AppModals } from './components/AppModals';
import { AppPanels } from './components/AppPanels';
import { AppFilterRow } from './components/AppFilterRow';
import { AppActivityStrip } from './components/AppActivityStrip';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useDocuments } from './hooks/useDocuments';
import { useAnalysis } from './hooks/useAnalysis';
import { useFixActions } from './hooks/useFixActions';
import { computeSafeFixCount, extractReviewFixItems } from './model/problemsSelection';
import { buildPaletteCommands } from './model/paletteCommands';
import type { AICapabilities } from './api/client';
import {
  appRootStyle,
  backendWarningBannerStyle,
  codeTagStyle,
  retryButtonStyle,
} from './components/appStyles';
import './ui5.css';
import { SL28bWorkspace, View as SL28bView } from './components/SL28bWorkspace';

export type { DocItem };

export const App: React.FC = () => {
  const { state, dispatch } = useApp();
  const {
    mode: themeMode,
    resolved: themeResolved,
    setMode: setThemeMode,
    toggleTheme,
  } = useTheme();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const directoryInputRef = useRef<HTMLInputElement>(null);
  const dirtyRef = useRef(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [sl28bView, setSl28bView] = useState<SL28bView>('workspace');
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [llmStatus, setLlmStatus] = useState<{ configured: boolean; provider: string }>({
    configured: false,
    provider: 'none',
  });
  const [isAskingAI, setIsAskingAI] = useState(false);
  const [aiCapabilities, setAiCapabilities] = useState<AICapabilities | null>(null);
  const [aiSessionId] = useState(() => {
    try {
      const key = 'securelex-ai-session';
      let value = sessionStorage.getItem(key);
      if (!value) {
        value = crypto.randomUUID();
        sessionStorage.setItem(key, value);
      }
      return value;
    } catch {
      return crypto.randomUUID();
    }
  });
  const [tokenMap, setTokenMap] = useState<'off' | 'security' | 'full'>('off');
  const [tokenCategory, setTokenCategory] = useState('');
  const [tokenMainFilter, setTokenMainFilter] = useState<'All' | 'Security' | 'Lexical' | 'Syntax'>(
    'All'
  );
  const [tokenGroups, setTokenGroups] = useState<string[]>([]);
  const [showAllTokens, setShowAllTokens] = useState(false);
  const [flyout, setFlyout] = useState<'files' | 'samples' | 'help' | null>(null);
  const lastFlyoutRef = useRef<'files' | 'samples' | 'help'>('files');
  const flyoutReturnRef = useRef<HTMLButtonElement | null>(null);
  const flyoutRef = useRef<HTMLDivElement>(null);

  const [navTarget, setNavTarget] = useState<NavTarget | null>(null);
  const [reviewFixesOpen, setReviewFixesOpen] = useState(false);
  const [analyzeWhileTyping, setAnalyzeWhileTyping] = useState<boolean>(() => {
    try {
      return localStorage.getItem('securelex-analyze-while-typing') === 'true';
    } catch {
      return false;
    }
  });

  const {
    openDocs,
    setOpenDocs,
    activeDocId,
    activeDoc,
    activeSample,
    activateDoc,
    handleSelectSample,
    handleOpenFileObject,
    createNewFile,
    closeCurrentFile,
  } = useDocuments({ dispatch, dirtyRef });

  const { runAnalysis, loadTokenInsights } = useAnalysis({
    state,
    dispatch,
    activeDocId,
    setOpenDocs,
    analyzeWhileTyping,
  });

  const {
    handleApplyFix,
    handleFixAll,
    handleOpenDiff,
    handleApplyDiffFix,
    handleMarkFalsePositive,
    handleSuppressFinding,
    handleAskAIFix,
    handleApplySelectedReviewFixes,
  } = useFixActions({
    state,
    dispatch,
    dirtyRef,
    activeDoc,
    activeDocId,
    setOpenDocs,
    runAnalysis,
    llmStatus,
    setIsAskingAI,
    setReviewFixesOpen,
  });

  const handleToggleAnalyzeWhileTyping = (enabled: boolean) => {
    setAnalyzeWhileTyping(enabled);
    try {
      localStorage.setItem('securelex-analyze-while-typing', String(enabled));
    } catch {}
    dispatch({
      type: 'ADD_TOAST',
      payload: {
        message: enabled
          ? 'Analyze while typing enabled'
          : 'Analyze while typing disabled (manual mode)',
        type: 'info',
      },
    });
  };

  // Wire test harness state getter
  useEffect(() => {
    harness.setStateGetter(() => ({
      activeDocId,
      isDirty: Boolean(activeDoc?.dirty),
      status: activeDoc?.status || 'not analysed',
      resultVersion: activeDoc?.resultVersion ?? 0,
      openDocsCount: openDocs.length,
    }));
  }, [activeDocId, activeDoc, openDocs.length]);

  // UI-7: scale workspace against reference design frame
  useEffect(() => {
    const updateScale = () => {
      let userZoom = 1;
      try {
        userZoom = Number(localStorage.getItem('securelex-interface-size') || 1);
      } catch {}
      if (![0.85, 1, 1.15].includes(userZoom)) userZoom = 1;
      const scale = computeUiScale(
        window.innerWidth,
        window.innerHeight,
        userZoom as 0.85 | 1 | 1.15
      );
      document.documentElement.style.setProperty('--ui-scale', String(scale));
      document.documentElement.style.setProperty('--ui-frame-size', `${100 / scale}%`);
    };
    let frame = 0;
    const onResize = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(updateScale);
    };
    updateScale();
    window.addEventListener('resize', onResize);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('resize', onResize);
    };
  }, []);

  // Health and capabilities initialization
  const checkBackendHealth = useCallback(async () => {
    try {
      await api.getHealth();
      dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: true });

      try {
        const langs = await api.getLanguages();
        if (langs && langs.length > 0) {
          dispatch({ type: 'SET_LANGUAGES', payload: langs });
        }
      } catch {}

      try {
        const samples = await api.getSamples();
        if (samples && samples.length > 0) {
          dispatch({ type: 'SET_SAMPLES', payload: samples });
        }
      } catch {}

      try {
        const llm = await api.getLLMStatus();
        if (llm) {
          setLlmStatus(llm);
        }
      } catch {}
      try {
        setAiCapabilities(await api.getCapabilities(aiSessionId));
      } catch {}
    } catch {
      dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: false });
    }
  }, [dispatch, aiSessionId]);

  useEffect(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);

  useEffect(() => {
    const onWorkspaceShortcut = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey) || !event.shiftKey) return;
      const key = event.key.toLowerCase();
      const target: Record<string, SL28bView> = {
        e: 'explain',
        f: 'fix',
        a: 'ast',
        s: 'security',
        l: 'safety',
        b: 'build',
        r: 'export',
      };
      if (target[key]) {
        event.preventDefault();
        setSl28bView(target[key]);
      }
    };
    window.addEventListener('keydown', onWorkspaceShortcut);
    return () => window.removeEventListener('keydown', onWorkspaceShortcut);
  }, []);

  // Query Local Agent status on mount
  useEffect(() => {
    let mounted = true;
    api
      .getAgentStatus()
      .then((status) => {
        if (mounted) {
          dispatch({ type: 'SET_AGENT_STATUS', payload: status });
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [dispatch]);

  // Active findings
  const activeFindings = (state.analysis?.findings || []).filter((f) => !f.suppressed);

  const handleNextProblem = () => {
    if (activeFindings.length === 0) return;
    const currentIdx = activeFindings.findIndex((f) => f.id === state.selectedFindingId);
    const nextIdx = (currentIdx + 1) % activeFindings.length;
    const nextFinding = activeFindings[nextIdx];
    dispatch({ type: 'SELECT_FINDING', payload: nextFinding.id });
    if (nextFinding?.range) {
      setNavTarget({ type: 'finding', range: nextFinding.range, timestamp: Date.now() });
    }
  };

  const handlePrevProblem = () => {
    if (activeFindings.length === 0) return;
    const currentIdx = activeFindings.findIndex((f) => f.id === state.selectedFindingId);
    const prevIdx = (currentIdx - 1 + activeFindings.length) % activeFindings.length;
    const prevFinding = activeFindings[prevIdx];
    dispatch({ type: 'SELECT_FINDING', payload: prevFinding.id });
    if (prevFinding?.range) {
      setNavTarget({ type: 'finding', range: prevFinding.range, timestamp: Date.now() });
    }
  };

  // Download / Save File Action (Ctrl+S)
  const handleDownload = () => {
    let contentToSave = state.source;
    if (activeDoc?.hasCrlf) {
      contentToSave = contentToSave.replace(/\r?\n/g, '\r\n');
    }
    const blob = new Blob([contentToSave], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = state.filename || 'source.py';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    dirtyRef.current = false;
    setOpenDocs((docs) =>
      docs.map((doc) => (doc.id === activeDocId ? { ...doc, dirty: false } : doc))
    );
    dispatch({
      type: 'ADD_TOAST',
      payload: { message: `Downloaded ${state.filename}`, type: 'info' },
    });
  };

  const toggleFlyout = (next: 'files' | 'samples' | 'help', btn?: HTMLButtonElement) => {
    if (btn) flyoutReturnRef.current = btn;
    lastFlyoutRef.current = next;
    setFlyout((current) => (current === next ? null : next));
  };

  const selectedFinding = activeFindings.find((f) => f.id === state.selectedFindingId) || null;
  const selectedToken =
    state.analysis && state.selectedTokenIndex !== null
      ? deriveTokens(state.analysis)[state.selectedTokenIndex] || null
      : null;
  const openCandidate = async (code: string, language: string, explanation: string) => {
    const ext = language === 'cpp' ? 'cpp' : language === 'javascript' ? 'js' : language;
    const name = `AI candidate.${ext}`;
    const outcome = await handleOpenFileObject(new File([code], name, { type: 'text/plain' }));
    if (outcome.error || outcome.unsupported) return;
    dispatch({
      type: 'ADD_TOAST',
      payload: {
        message: 'AI candidate opened as a new editable file; review its analysis before use.',
        type: 'info',
      },
    });
    void explanation;
  };

  const selectFindingAndToken = (id: string) => {
    dispatch({ type: 'SELECT_FINDING', payload: id });
    const finding = activeFindings.find((f) => f.id === id);
    if (finding?.range) {
      setNavTarget({ type: 'finding', range: finding.range, timestamp: Date.now() });
    }
    const index = state.analysis
      ? deriveTokens(state.analysis).findIndex((token) =>
          token.relatedFindings.some((f) => f.id === id)
        )
      : -1;
    dispatch({ type: 'SELECT_TOKEN_INDEX', payload: index >= 0 ? index : null });
  };

  const selectTokenFromPanel = (index: number) => {
    dispatch({ type: 'SELECT_TOKEN_INDEX', payload: index });
    const tok = state.analysis?.tokens[index];
    if (tok?.range) {
      setNavTarget({ type: 'token', range: tok.range, timestamp: Date.now() });
    }
  };

  // Keyboard shortcut listener
  useKeyboardShortcuts({
    onOpenPalette: () => setPaletteOpen(true),
    onNextProblem: handleNextProblem,
    onPrevProblem: handlePrevProblem,
    onAnalyze: () => runAnalysis(state.source, state.language, state.filename),
    onApplyQuickFix: () => {
      if (selectedFinding && selectedFinding.fixes?.length) {
        handleApplyFix(selectedFinding.fixes[0], selectedFinding);
      }
    },
    onSave: handleDownload,
    onNewFile: createNewFile,
    onOpenFile: () => fileInputRef.current?.click(),
    onCloseFile: () => closeCurrentFile(),
    onToggleFlyout: () => setFlyout((current) => (current ? null : lastFlyoutRef.current)),
    onCloseFlyout: () => {
      setFlyout(null);
      flyoutReturnRef.current?.focus();
    },
    isFlyoutOpen: Boolean(flyout),
    onOpenShortcuts: () => setShortcutsOpen(true),
    isDirty: dirtyRef.current || openDocs.some((d) => d.dirty),
  });

  // Outside click to close flyout
  useEffect(() => {
    if (!flyout) return;
    const onPointerDown = (event: MouseEvent) => {
      if (
        !flyoutRef.current?.contains(event.target as Node) &&
        !(event.target as HTMLElement).closest('.ui5-strip')
      ) {
        setFlyout(null);
        flyoutReturnRef.current?.focus();
      }
    };
    document.addEventListener('mousedown', onPointerDown);
    flyoutRef.current?.querySelector<HTMLElement>('button,input,[tabindex="0"]')?.focus();
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [flyout]);

  const safeFixCount = computeSafeFixCount(activeFindings);
  const reviewFixItems = extractReviewFixItems(state.source, activeFindings);

  const handleFilesSelected = async (files: File[]) => {
    let unsupportedCount = 0;
    for (const file of files) {
      const res = await handleOpenFileObject(file);
      if (res.unsupported) unsupportedCount++;
    }
    if (unsupportedCount > 0) {
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Skipped ${unsupportedCount} unsupported file(s).`,
          type: 'info',
        },
      });
    }
  };

  const handleDirectoryFilesSelected = async (files: File[]) => {
    const skipPatterns = /(node_modules|\.git|venv|__pycache__|dist|build)/i;
    const filtered = files
      .filter((f) => {
        const rel = (f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name;
        return !skipPatterns.test(rel);
      })
      .slice(0, 200);

    let unsupportedCount = 0;
    for (const file of filtered) {
      const rel = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
      const res = await handleOpenFileObject(file, rel);
      if (res.unsupported) unsupportedCount++;
    }
    if (unsupportedCount > 0) {
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Skipped ${unsupportedCount} unsupported file(s).`,
          type: 'info',
        },
      });
    }
  };

  const fileAnalysisState = activeDoc?.status || 'not analysed';

  const paletteCommands = buildPaletteCommands({
    setThemeMode,
    toggleTheme,
    createNewFile,
    onOpenFileClick: () => fileInputRef.current?.click(),
    onFolderClick: () => directoryInputRef.current?.click(),
    handleDownload,
    closeCurrentFile: () => closeCurrentFile(),
    runAnalysis: () => runAnalysis(state.source, state.language, state.filename),
    handleFixAll,
    safeFixCount,
    handleNextProblem,
    handlePrevProblem,
    onSetTab: (tab) => dispatch({ type: 'SET_ACTIVE_TAB', payload: tab }),
    setTokenMap,
    onToggleSidebar: () => dispatch({ type: 'TOGGLE_SIDEBAR' }),
    samples: state.samples,
    handleSelectSample,
    languages: state.languages,
    onSetLanguage: (lang) => dispatch({ type: 'SET_LANGUAGE', payload: lang }),
    onOpenShortcuts: () => setShortcutsOpen(true),
    onExplainToken: () => setSl28bView('explain'),
    onProposeFix: () => setSl28bView('fix'),
    onOpenSafetyLab: () => setSl28bView('safety'),
    onExportReport: () => setSl28bView('export'),
    onOpenAst: () => setSl28bView('ast'),
    onShowSecurity: () => setSl28bView('security'),
    onBuildWithAI: () => setSl28bView('build'),
    onUndoFix: () => setSl28bView('fix'),
  });

  return (
    <div style={appRootStyle}>
      {/* Top Bar 49px */}
      <TopBar
        themeResolved={themeResolved}
        onThemeToggle={toggleTheme}
        language={state.language}
        detectedLanguage={
          state.language === 'auto' && state.analysis
            ? state.analysis.language[0].toUpperCase() + state.analysis.language.slice(1)
            : undefined
        }
        languages={state.languages}
        onChangeLanguage={(l) => dispatch({ type: 'SET_LANGUAGE', payload: l })}
        isAnalyzing={state.isAnalyzing}
        onAnalyze={() => runAnalysis(state.source, state.language, state.filename)}
        onFixAll={handleFixAll}
        onDownload={handleDownload}
        onNewFile={createNewFile}
        onOpenFile={() => fileInputRef.current?.click()}
        onCloseFile={closeCurrentFile}
        filename={state.filename}
        files={openDocs}
        activeFileId={activeDocId}
        onSwitchFile={(id) => {
          const doc = openDocs.find((item) => item.id === id);
          if (doc) activateDoc(doc);
        }}
        onCloseFileById={closeCurrentFile}
        safeFixCount={safeFixCount}
        reviewFixCount={reviewFixItems.length}
        fileState={fileAnalysisState}
        onOpenReviewFixes={() => setReviewFixesOpen(true)}
        backendAvailable={state.isBackendAvailable}
        agentMode={state.agentMode}
        onChangeAgentMode={(m) => dispatch({ type: 'SET_AGENT_MODE', payload: m })}
        ollamaReachable={state.agentStatus?.ollama_reachable ?? false}
        ollamaModel={state.agentStatus?.model || 'qwen2.5-coder:3b'}
      />

      {aiCapabilities && (
        <div
          data-qa="ai-processing-location"
          role="status"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '4px 12px',
            fontSize: 11,
            color: 'var(--text-muted)',
            background: 'var(--surface-2)',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <span>
            AI provider: {aiCapabilities.ai.provider} · Processing:{' '}
            {aiCapabilities.ai.processing_location} ·{' '}
            {aiCapabilities.ai.model || 'model not configured'} ·{' '}
            {aiCapabilities.ai.reachable === false ? 'unavailable' : 'status reported by provider'}
          </span>
          {aiCapabilities.ai.consent_required && (
            <label
              style={{ display: 'inline-flex', alignItems: 'center', gap: 5, marginLeft: 'auto' }}
            >
              <input
                type="checkbox"
                aria-label="Consent to send source code to the configured remote AI provider"
                checked={aiCapabilities.ai.remote_consented}
                onChange={async (event) => {
                  const consent = event.currentTarget.checked;
                  await api.setRemoteConsent(aiSessionId, consent);
                  setAiCapabilities(await api.getCapabilities(aiSessionId));
                }}
              />
              Allow source processing by remote provider for this session
            </label>
          )}
        </div>
      )}

      {/* Backend Offline Banner */}
      {!state.isBackendAvailable && (
        <div style={backendWarningBannerStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={15} color="var(--critical)" />
            <span>
              Backend not running - run: <code style={codeTagStyle}>python scripts/dev.py</code>
            </span>
          </div>
          <button style={retryButtonStyle} onClick={checkBackendHealth}>
            <RefreshCw size={12} />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      <main data-qa="main" className="ui5-main">
        <AppActivityStrip
          flyout={flyout}
          onToggleFlyout={toggleFlyout}
          flyoutRef={flyoutRef}
          openDocs={openDocs}
          activeDocId={activeDocId}
          samples={state.samples}
          language={state.language}
          engine={state.analysis?.engine}
          themeMode={themeMode}
          themeResolved={themeResolved}
          onThemeChange={setThemeMode}
          analyzeWhileTyping={analyzeWhileTyping}
          onToggleAnalyzeWhileTyping={handleToggleAnalyzeWhileTyping}
          onCloseFlyout={() => {
            setFlyout(null);
            flyoutReturnRef.current?.focus();
          }}
          onNewFile={createNewFile}
          onOpenFile={() => fileInputRef.current?.click()}
          onFolder={() => directoryInputRef.current?.click()}
          onSave={handleDownload}
          onSwitchDoc={(id) => {
            const doc = openDocs.find((item) => item.id === id);
            if (doc) activateDoc(doc);
          }}
          onCloseDoc={closeCurrentFile}
          onSample={(sample) => {
            handleSelectSample(sample);
            setFlyout(null);
          }}
        />

        <nav
          aria-label="SecureLex analysis workspaces"
          style={{
            display: 'flex',
            gap: 4,
            padding: '4px 8px',
            overflowX: 'auto',
            borderBottom: '1px solid var(--border)',
            background: 'var(--surface-2)',
          }}
        >
          {(
            [
              ['workspace', 'Editor'],
              ['problems', 'Problems'],
              ['security', 'Security'],
              ['ast', 'AST'],
              ['explain', 'AI Explain'],
              ['activity', 'Agent Activity'],
              ['build', 'Build with AI'],
              ['fix', 'Fix with AI'],
              ['safety', 'Safety Lab'],
              ['settings', 'Settings'],
              ['export', 'Export'],
            ] as const
          ).map(([view, label]) => (
            <button
              key={view}
              type="button"
              aria-pressed={sl28bView === view}
              onClick={() => setSl28bView(view)}
              style={{
                padding: '4px 8px',
                border: '1px solid var(--border)',
                borderRadius: 4,
                background: sl28bView === view ? 'var(--surface-3)' : 'var(--surface-1)',
                color: 'var(--text-primary)',
              }}
            >
              {label}
            </button>
          ))}
        </nav>

        {sl28bView !== 'workspace' && (
          <SL28bWorkspace
            view={sl28bView}
            onView={setSl28bView}
            source={state.source}
            language={
              state.language === 'auto' ? state.analysis?.language || 'python' : state.language
            }
            filename={state.filename}
            sourceVersion={activeDoc?.contentVersion ?? 0}
            capabilities={(aiCapabilities || null) as any}
            sessionId={aiSessionId}
            selectedFinding={selectedFinding as any}
            selectedToken={selectedToken as any}
            findings={activeFindings as any}
            onSelectFinding={(finding) => {
              dispatch({ type: 'SELECT_FINDING', payload: finding.id });
            }}
            onDataFlow={(id) => dispatch({ type: 'SET_DATA_FLOW', payload: id })}
            theme={themeMode}
            onThemeChange={setThemeMode}
            onNavigate={(range) =>
              setNavTarget({ type: 'finding', range: range as any, timestamp: Date.now() })
            }
            onCandidate={(code, language, explanation) => {
              void openCandidate(code, language, explanation);
            }}
            onSourceChange={(code) => {
              dirtyRef.current = true;
              dispatch({ type: 'SET_SOURCE', payload: code });
              setOpenDocs((docs) =>
                docs.map((doc) =>
                  doc.id === activeDocId
                    ? {
                        ...doc,
                        content: code,
                        dirty: true,
                        contentVersion: doc.contentVersion + 1,
                        status: 'stale',
                      }
                    : doc
                )
              );
            }}
          />
        )}
        {sl28bView === 'workspace' && (
          <AppPanels
            openDocs={openDocs}
            activeDocId={activeDocId}
            activateDoc={activateDoc}
            closeCurrentFile={closeCurrentFile}
            source={state.source}
            language={state.language}
            filename={state.filename}
            findings={activeFindings}
            selectedFindingId={state.selectedFindingId}
            activeDataFlowFindingId={state.activeDataFlowFindingId}
            navTarget={navTarget}
            onChangeSource={(val) => {
              dirtyRef.current = true;
              dispatch({ type: 'SET_SOURCE', payload: val });
              setOpenDocs((docs) =>
                docs.map((doc) =>
                  doc.id === activeDocId
                    ? {
                        ...doc,
                        content: val,
                        dirty: true,
                        contentVersion: doc.contentVersion + 1,
                        status: doc.analysis ? 'stale' : 'not analysed',
                      }
                    : doc
                )
              );
            }}
            onCursorChange={(pos) => dispatch({ type: 'SET_CURSOR_POSITION', payload: pos })}
            selectedTokenIndex={state.selectedTokenIndex}
            tokenMap={tokenMap}
            tokenCategory={tokenCategory}
            onSelectToken={(idx) => dispatch({ type: 'SELECT_TOKEN_INDEX', payload: idx })}
            onOpenTokens={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'tokens' })}
            onSelectFinding={selectFindingAndToken}
            onOpenDiff={handleOpenDiff}
            onAnalyzeShortcut={() => runAnalysis(state.source, state.language, state.filename)}
            onDownloadShortcut={handleDownload}
            onNextProblem={handleNextProblem}
            onPrevProblem={handlePrevProblem}
            activeTab={state.activeTab}
            onChangeTab={(tab) => dispatch({ type: 'SET_ACTIVE_TAB', payload: tab })}
            selectedFinding={selectedFinding}
            summary={state.analysis?.summary || null}
            engine={state.analysis?.engine || null}
            analysisLanguage={state.analysis?.language}
            mlInsights={state.mlInsights}
            isLoadingInsights={state.isLoadingInsights}
            mlMode={state.analysis?.engine?.ml_mode ?? 'on'}
            onApplyFix={handleApplyFix}
            onJumpToStep={(step: TaintPathStep) => {
              dispatch({
                type: 'SET_CURSOR_POSITION',
                payload: { line: step.range.start_line, col: step.range.start_col },
              });
              setNavTarget({ type: 'finding', range: step.range, timestamp: Date.now() });
            }}
            onToggleDataFlow={(id) => {
              dispatch({
                type: 'SET_DATA_FLOW',
                payload: state.activeDataFlowFindingId === id ? null : id,
              });
            }}
            onMarkFalsePositive={handleMarkFalsePositive}
            onSuppressFinding={handleSuppressFinding}
            onAskAIFix={handleAskAIFix}
            isAskingAI={isAskingAI}
            llmConfigured={llmStatus.configured}
            llmProvider={llmStatus.provider}
            analysis={state.analysis}
            onTokenMap={setTokenMap}
            onTokenCategory={setTokenCategory}
            onSelectTokenFromPanel={selectTokenFromPanel}
            onLoadTokenML={loadTokenInsights}
            showAllTokens={showAllTokens}
            tokenMainFilter={tokenMainFilter}
            tokenGroups={tokenGroups}
            activeSample={activeSample}
            onDemoStep={(delta) => {
              const index = DEMO_PATH.indexOf(activeSample?.id || '');
              const next = state.samples.find((item) => item.id === DEMO_PATH[index + delta]);
              if (next) handleSelectSample(next);
            }}
            agentMode={state.agentMode}
            agentModel={state.agentStatus?.model || 'qwen2.5-coder:3b'}
            samples={state.samples}
          />
        )}
      </main>

      <ExplanationPanel
        analysis={state.analysis}
        source={state.source}
        selectedIndex={state.selectedTokenIndex}
        selectedFinding={selectedFinding}
        onApplyFix={handleApplyFix}
        onFalsePositive={handleMarkFalsePositive}
        isStale={fileAnalysisState === 'stale'}
      />

      <AppFilterRow
        onOpenProblems={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'problems' })}
        analysisExists={Boolean(state.analysis)}
        activeFindings={activeFindings}
        isStale={fileAnalysisState === 'stale'}
        tokenMainFilter={tokenMainFilter}
        onSelectTokenMainFilter={(filter) => {
          setTokenMainFilter(filter);
          dispatch({ type: 'SET_ACTIVE_TAB', payload: 'tokens' });
        }}
        tokenGroups={tokenGroups}
        onToggleTokenGroup={(group) => {
          setTokenGroups((current) =>
            current.includes(group) ? current.filter((item) => item !== group) : [...current, group]
          );
          dispatch({ type: 'SET_ACTIVE_TAB', payload: 'tokens' });
        }}
        showAllTokens={showAllTokens}
        onToggleShowAllTokens={(show) => {
          setShowAllTokens(show);
          dispatch({ type: 'SET_ACTIVE_TAB', payload: 'tokens' });
        }}
      />

      {/* Status Bar 35px */}
      <StatusBar
        engine={state.analysis?.engine || null}
        cursorPosition={state.cursorPosition}
        isAnalyzing={state.isAnalyzing}
        findingCount={
          activeFindings.filter(
            (finding) => !['lexical', 'syntax'].includes(finding.kind || 'security')
          ).length
        }
        analysisReady={Boolean(state.analysis)}
        lexicalCount={activeFindings.filter((finding) => finding.kind === 'lexical').length}
        syntaxCount={activeFindings.filter((finding) => finding.kind === 'syntax').length}
        onRetry={() => runAnalysis(state.source, state.language, state.filename)}
        analysisFailed={!state.isBackendAvailable}
        fileState={fileAnalysisState}
        agentMode={state.agentMode}
        agentModel={state.agentStatus?.model || 'qwen2.5-coder:3b'}
      />

      <AppModals
        paletteOpen={paletteOpen}
        onClosePalette={() => setPaletteOpen(false)}
        commands={paletteCommands}
        shortcutsOpen={shortcutsOpen}
        onCloseShortcuts={() => setShortcutsOpen(false)}
        fileInputRef={fileInputRef}
        directoryInputRef={directoryInputRef}
        onFilesSelected={handleFilesSelected}
        onDirectoryFilesSelected={handleDirectoryFilesSelected}
        diffModal={state.diffModal}
        onApplyDiffFix={handleApplyDiffFix}
        onCloseDiffModal={() => dispatch({ type: 'CLOSE_DIFF_MODAL' })}
        reviewFixesOpen={reviewFixesOpen}
        reviewFixItems={reviewFixItems}
        onCloseReviewFixes={() => setReviewFixesOpen(false)}
        onApplySelectedReviewFixes={handleApplySelectedReviewFixes}
        toasts={state.toasts}
        onDismissToast={(id) => dispatch({ type: 'REMOVE_TOAST', payload: id })}
      />
    </div>
  );
};
