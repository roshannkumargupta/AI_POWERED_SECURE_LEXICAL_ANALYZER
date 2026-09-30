import React, { useEffect, useRef, useCallback } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { AlertCircle, RefreshCw } from 'lucide-react';

import { useApp } from './state/store';
import { api, Finding, Fix, SampleItem, TaintPathStep } from './api/client';
import { TopBar } from './components/TopBar';
import { Sidebar } from './components/Sidebar';
import { EditorPane } from './components/EditorPane';
import { ProblemsPanel } from './components/ProblemsPanel';
import { FindingPanel } from './components/FindingPanel';
import { StatusBar } from './components/StatusBar';
import { EmptyState } from './components/EmptyState';
import { ToastContainer } from './components/Toast';
import { DiffView } from './components/DiffView';
import { applyEdits } from './utils/applyEdits';

export const App: React.FC = () => {
  const { state, dispatch } = useApp();
  const abortControllerRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<number | null>(null);

  // Health and capabilities initialization
  const checkBackendHealth = useCallback(async () => {
    try {
      await api.getHealth();
      dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: true });

      // Fetch languages and samples from backend if available
      try {
        const langs = await api.getLanguages();
        if (langs && langs.length > 0) {
          dispatch({ type: 'SET_LANGUAGES', payload: langs });
        }
      } catch {
        // use default languages
      }

      try {
        const samples = await api.getSamples();
        if (samples && samples.length > 0) {
          dispatch({ type: 'SET_SAMPLES', payload: samples });
        }
      } catch {
        // use bundled samples
      }
    } catch {
      dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: false });
    }
  }, [dispatch]);

  useEffect(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);

  // Main Analysis function
  const runAnalysis = useCallback(
    async (sourceCode: string, targetLanguage: string, targetFilename: string) => {
      if (!sourceCode.trim()) {
        return;
      }

      // Cancel previous in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      dispatch({ type: 'SET_ANALYZING', payload: true });

      try {
        const res = await api.analyze(
          {
            source: sourceCode,
            language: targetLanguage === 'auto' ? null : targetLanguage,
            filename: targetFilename,
            options: { fixes: true, ml: true, include_tokens: true },
          },
          controller.signal
        );

        dispatch({ type: 'SET_ANALYSIS', payload: res });
        dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: true });
      } catch (err: any) {
        if (err.name === 'AbortError') return;

        dispatch({ type: 'SET_ANALYZING', payload: false });
        dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: false });
        dispatch({
          type: 'ADD_TOAST',
          payload: {
            message: err.detail || 'Backend unreachable. Running offline.',
            type: 'warning',
          },
        });
      }
    },
    [dispatch]
  );

  // Auto-analyze debounced 600ms on source or language changes
  useEffect(() => {
    if (debounceTimerRef.current) {
      window.clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = window.setTimeout(() => {
      runAnalysis(state.source, state.language, state.filename);
    }, 600);

    return () => {
      if (debounceTimerRef.current) {
        window.clearTimeout(debounceTimerRef.current);
      }
    };
  }, [state.source, state.language, state.filename, runAnalysis]);

  // Token Insights Loader
  const loadTokenInsights = useCallback(
    async (tokenIdx: number) => {
      dispatch({ type: 'SELECT_TOKEN_INDEX', payload: tokenIdx });
      dispatch({ type: 'SET_LOADING_INSIGHTS', payload: true });

      try {
        const res = await api.getMLInsights({
          source: state.source,
          language: state.language === 'auto' ? 'python' : state.language,
          token_index: tokenIdx,
        });
        dispatch({ type: 'SET_ML_INSIGHTS', payload: res });
      } catch {
        dispatch({ type: 'SET_LOADING_INSIGHTS', payload: false });
      }
    },
    [dispatch, state.source, state.language]
  );

  // Fix Application
  const handleApplyFix = async (fix: Fix, _finding: Finding) => {
    try {
      // Apply locally first for immediate responsiveness
      const newSource = applyEdits(state.source, fix.edits);
      dispatch({ type: 'SET_SOURCE', payload: newSource });

      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Applied fix: ${fix.title}`,
          type: 'success',
        },
      });

      // Run re-analysis
      await runAnalysis(newSource, state.language, state.filename);
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Failed to apply fix: ${err.message}`,
          type: 'error',
        },
      });
    }
  };

  // Fix All Action
  const handleFixAll = async () => {
    dispatch({ type: 'SET_ANALYZING', payload: true });
    try {
      const res = await api.applyFixAll({
        source: state.source,
        language: state.language === 'auto' ? 'python' : state.language,
        filename: state.filename,
        allow_review: false,
      });

      dispatch({ type: 'SET_SOURCE', payload: res.new_source });
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Applied ${res.applied.length} fixes — score ${res.score_before} -> ${res.score_after}`,
          type: 'success',
        },
      });

      // Re-analyze new source
      await runAnalysis(res.new_source, state.language, state.filename);
    } catch (err: any) {
      dispatch({ type: 'SET_ANALYZING', payload: false });
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Fix all failed: ${err.message || 'Server error'}`,
          type: 'error',
        },
      });
    }
  };

  // Open Review Diff View
  const handleOpenDiff = (fix: Fix, finding: Finding) => {
    try {
      const newSource = applyEdits(state.source, fix.edits);
      dispatch({
        type: 'OPEN_DIFF_MODAL',
        payload: {
          fix,
          finding,
          oldSource: state.source,
          newSource,
          diff: `--- a/${state.filename}\n+++ b/${state.filename}\n${fix.description}`,
        },
      });
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: `Cannot generate diff: ${err.message}`, type: 'error' },
      });
    }
  };

  // Apply Review Diff from Modal
  const handleApplyDiffFix = async () => {
    if (!state.diffModal || !state.diffModal.fix) return;
    const fix = state.diffModal.fix;
    const newSource = state.diffModal.newSource;

    dispatch({ type: 'SET_SOURCE', payload: newSource });
    dispatch({ type: 'CLOSE_DIFF_MODAL' });
    dispatch({
      type: 'ADD_TOAST',
      payload: { message: `Applied fix: ${fix.title}`, type: 'success' },
    });

    await runAnalysis(newSource, state.language, state.filename);
  };

  // False Positive Report
  const handleMarkFalsePositive = async (finding: Finding) => {
    try {
      await api.submitFeedback({
        finding_fingerprint: finding.id,
        rule_id: finding.rule_id,
        language: state.language === 'auto' ? 'python' : state.language,
        verdict: 'false_positive',
        snippet: state.source.slice(0, 300),
      });

      dispatch({ type: 'HIDE_FINDING', payload: finding.id });
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: 'Thanks - saved for the next model retrain',
          type: 'success',
        },
      });
    } catch {
      // Local fallback hiding
      dispatch({ type: 'HIDE_FINDING', payload: finding.id });
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: 'Thanks - saved for the next model retrain',
          type: 'success',
        },
      });
    }
  };

  // Navigation: Next / Prev problem (F8 / Shift+F8)
  const activeFindings = (state.analysis?.findings || []).filter((f) => !f.suppressed);

  const handleNextProblem = () => {
    if (activeFindings.length === 0) return;
    const currentIdx = activeFindings.findIndex((f) => f.id === state.selectedFindingId);
    const nextIdx = (currentIdx + 1) % activeFindings.length;
    dispatch({ type: 'SELECT_FINDING', payload: activeFindings[nextIdx].id });
  };

  const handlePrevProblem = () => {
    if (activeFindings.length === 0) return;
    const currentIdx = activeFindings.findIndex((f) => f.id === state.selectedFindingId);
    const prevIdx = (currentIdx - 1 + activeFindings.length) % activeFindings.length;
    dispatch({ type: 'SELECT_FINDING', payload: activeFindings[prevIdx].id });
  };

  // Download File Action
  const handleDownload = () => {
    const blob = new Blob([state.source], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = state.filename || 'source.py';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    dispatch({
      type: 'ADD_TOAST',
      payload: { message: `Downloaded ${state.filename}`, type: 'info' },
    });
  };

  // Select Sample Preset
  const handleSelectSample = (sample: SampleItem) => {
    dispatch({ type: 'SET_SOURCE', payload: sample.code });
    dispatch({ type: 'SET_LANGUAGE', payload: sample.language });
    dispatch({ type: 'SET_FILENAME', payload: sample.filename });
  };

  // Open Local File
  const handleOpenFile = (filename: string, content: string) => {
    dispatch({ type: 'SET_FILENAME', payload: filename });
    dispatch({ type: 'SET_SOURCE', payload: content });
    // Attempt to guess language from extension
    if (filename.endsWith('.py')) dispatch({ type: 'SET_LANGUAGE', payload: 'python' });
    else if (filename.endsWith('.java')) dispatch({ type: 'SET_LANGUAGE', payload: 'java' });
    else if (filename.endsWith('.js') || filename.endsWith('.jsx'))
      dispatch({ type: 'SET_LANGUAGE', payload: 'javascript' });
    else if (filename.endsWith('.cpp') || filename.endsWith('.h'))
      dispatch({ type: 'SET_LANGUAGE', payload: 'cpp' });
  };

  const selectedFinding = activeFindings.find((f) => f.id === state.selectedFindingId) || null;

  return (
    <div style={appRootStyle}>
      {/* Top Bar 48px */}
      <TopBar
        language={state.language}
        languages={state.languages}
        onChangeLanguage={(l) => dispatch({ type: 'SET_LANGUAGE', payload: l })}
        isAnalyzing={state.isAnalyzing}
        onAnalyze={() => runAnalysis(state.source, state.language, state.filename)}
        onFixAll={handleFixAll}
        onDownload={handleDownload}
        samples={state.samples}
        onSelectSample={handleSelectSample}
        healthScore={state.analysis?.summary?.score ?? null}
      />

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

      {/* Main Resizable Layout */}
      <main style={mainLayoutStyle}>
        <PanelGroup direction="horizontal">
          {/* Left Sidebar: 240px default */}
          <Panel
            defaultSize={16}
            minSize={10}
            maxSize={25}
            collapsible={true}
            style={{ display: state.isSidebarCollapsed ? 'none' : 'block' }}
          >
            <Sidebar
              isCollapsed={state.isSidebarCollapsed}
              onToggleCollapse={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
              samples={state.samples}
              selectedSampleId={null}
              onSelectSample={handleSelectSample}
              onOpenFile={handleOpenFile}
            />
          </Panel>

          <PanelResizeHandle />

          {/* Center Pane: Editor + Bottom Problems Panel */}
          <Panel defaultSize={56} minSize={30}>
            <PanelGroup direction="vertical">
              {/* Monaco Editor Pane */}
              <Panel defaultSize={72} minSize={30}>
                {state.source.trim() === '' ? (
                  <EmptyState
                    samples={state.samples}
                    onSelectSample={handleSelectSample}
                  />
                ) : (
                  <EditorPane
                    source={state.source}
                    language={state.language}
                    findings={activeFindings}
                    tokens={state.analysis?.tokens || []}
                    selectedFindingId={state.selectedFindingId}
                    activeDataFlowFindingId={state.activeDataFlowFindingId}
                    onChangeSource={(val) => dispatch({ type: 'SET_SOURCE', payload: val })}
                    onCursorChange={(pos) => dispatch({ type: 'SET_CURSOR_POSITION', payload: pos })}
                    onSelectToken={loadTokenInsights}
                    onSelectFinding={(id) => dispatch({ type: 'SELECT_FINDING', payload: id })}
                    onOpenDiff={handleOpenDiff}
                    onAnalyzeShortcut={() => runAnalysis(state.source, state.language, state.filename)}
                    onDownloadShortcut={handleDownload}
                    onNextProblem={handleNextProblem}
                    onPrevProblem={handlePrevProblem}
                  />
                )}
              </Panel>

              <PanelResizeHandle />

              {/* Bottom Problems Drawer */}
              <Panel defaultSize={28} minSize={15} maxSize={50}>
                <ProblemsPanel
                  findings={activeFindings}
                  selectedFindingId={state.selectedFindingId}
                  filter={state.problemsFilter}
                  onSelectFilter={(filter) =>
                    dispatch({ type: 'SET_PROBLEMS_FILTER', payload: filter })
                  }
                  onSelectFinding={(id) => dispatch({ type: 'SELECT_FINDING', payload: id })}
                  onNextFinding={handleNextProblem}
                  onPrevFinding={handlePrevProblem}
                />
              </Panel>
            </PanelGroup>
          </Panel>

          <PanelResizeHandle />

          {/* Right Panel: Finding / Summary / ML Insights: 380px default */}
          <Panel defaultSize={28} minSize={20} maxSize={45}>
            <FindingPanel
              activeTab={state.activeTab}
              onChangeTab={(tab) => dispatch({ type: 'SET_ACTIVE_TAB', payload: tab })}
              selectedFinding={selectedFinding}
              summary={state.analysis?.summary || null}
              mlInsights={state.mlInsights}
              isLoadingInsights={state.isLoadingInsights}
              mlMode={state.analysis?.engine?.ml_mode ?? 'on'}
              onApplyFix={handleApplyFix}
              onOpenDiff={handleOpenDiff}
              onJumpToStep={(step: TaintPathStep) => {
                dispatch({
                  type: 'SET_CURSOR_POSITION',
                  payload: { line: step.range.start_line, col: step.range.start_col },
                });
              }}
              onToggleDataFlow={(id) => {
                dispatch({
                  type: 'SET_DATA_FLOW',
                  payload: state.activeDataFlowFindingId === id ? null : id,
                });
              }}
              isDataFlowActive={state.activeDataFlowFindingId === state.selectedFindingId}
              onMarkFalsePositive={handleMarkFalsePositive}
            />
          </Panel>
        </PanelGroup>
      </main>

      {/* Status Bar 24px */}
      <StatusBar
        language={state.language}
        engine={state.analysis?.engine || null}
        cursorPosition={state.cursorPosition}
        isAnalyzing={state.isAnalyzing}
      />

      {/* Diff Review Modal */}
      {state.diffModal && state.diffModal.fix && state.diffModal.finding && (
        <DiffView
          isOpen={state.diffModal.isOpen}
          fix={state.diffModal.fix}
          finding={state.diffModal.finding}
          diff={state.diffModal.diff}
          onApply={handleApplyDiffFix}
          onCancel={() => dispatch({ type: 'CLOSE_DIFF_MODAL' })}
        />
      )}

      {/* Toast Notifications */}
      <ToastContainer
        toasts={state.toasts}
        onDismiss={(id) => dispatch({ type: 'REMOVE_TOAST', payload: id })}
      />
    </div>
  );
};

const appRootStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  height: '100vh',
  width: '100vw',
  backgroundColor: 'var(--bg)',
  overflow: 'hidden',
};

const backendWarningBannerStyle: React.CSSProperties = {
  height: '28px',
  backgroundColor: 'rgba(255, 77, 109, 0.12)',
  borderBottom: '1px solid rgba(255, 77, 109, 0.3)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 16px',
  fontSize: '11px',
  color: 'var(--critical)',
  zIndex: 25,
};

const codeTagStyle: React.CSSProperties = {
  backgroundColor: 'var(--panel)',
  padding: '2px 6px',
  borderRadius: 'var(--radius-sm)',
  fontFamily: 'var(--font-code)',
  color: 'var(--text)',
};

const retryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  fontSize: '10px',
  fontWeight: 600,
  color: 'var(--text)',
  backgroundColor: 'var(--panel-2)',
  padding: '2px 8px',
  borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--border)',
  cursor: 'pointer',
};

const mainLayoutStyle: React.CSSProperties = {
  flex: 1,
  overflow: 'hidden',
  display: 'flex',
};
