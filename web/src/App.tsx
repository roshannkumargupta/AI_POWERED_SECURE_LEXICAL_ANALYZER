import React, { useEffect, useRef, useCallback, useState } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { AlertCircle, RefreshCw, Files, FlaskConical, CircleHelp, X } from 'lucide-react';
import * as monaco from 'monaco-editor';

import { useApp } from './state/store';
import { api, Finding, Fix, SampleItem, TaintPathStep } from './api/client';
import { TopBar } from './components/TopBar';
import { EditorPane, NavTarget } from './components/EditorPane';
import { FindingPanel } from './components/FindingPanel';
import { StatusBar } from './components/StatusBar';
import { ToastContainer } from './components/Toast';
import { DiffView } from './components/DiffView';
import { ReviewFixesModal, ReviewFixItem } from './components/ReviewFixesModal';
import { applyEdits } from './utils/applyEdits';
import { generateUnifiedDiff } from './utils/diff';
import { CommandPalette, PaletteCommand } from './components/CommandPalette';
import { deriveTokens } from './tokens/derive';
import { DEMO_PATH } from './utils/sampleDemo';
import { computeUiScale } from './utils/uiScale';
import { useTheme } from './theme/theme';
import { FlyoutPanel } from './components/FlyoutPanel';
import { ExplanationPanel } from './components/ExplanationPanel';
import { processFileForOpen } from './utils/fileLoader';
import { harness } from './testHarness';
import { KeyboardShortcutsModal } from './components/KeyboardShortcutsModal';
import './ui5.css';

export interface DocItem {
  id: string;
  name: string;
  content: string;
  language: string;
  dirty: boolean;
  sampleId?: string;
  folderPath?: string;
  hasCrlf?: boolean;
  analysis: any | null;
  resultVersion: number;
  contentVersion: number;
  status: 'not analysed' | 'analysing' | 'analysed' | 'stale' | 'error';
  durationMs?: number;
  errorMessage?: string;
}

export const App: React.FC = () => {
  const { state, dispatch } = useApp();
  const {
    mode: themeMode,
    resolved: themeResolved,
    setMode: setThemeMode,
    toggleTheme,
  } = useTheme();
  const abortControllerRef = useRef<AbortController | null>(null);
  const analysisRequestRef = useRef(0);
  const currentContextRef = useRef({
    source: state.source,
    language: state.language,
    filename: state.filename,
  });
  currentContextRef.current = {
    source: state.source,
    language: state.language,
    filename: state.filename,
  };
  const debounceTimerRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const dirtyRef = useRef(false);
  const untitledIndexRef = useRef(0);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [llmStatus, setLlmStatus] = useState<{ configured: boolean; provider: string }>({
    configured: false,
    provider: 'none',
  });
  const [isAskingAI, setIsAskingAI] = useState(false);
  const [tokenMap, setTokenMap] = useState<'off' | 'security' | 'full'>('off');
  const [tokenCategory, setTokenCategory] = useState('');
  const [tokenMainFilter, setTokenMainFilter] = useState<'All' | 'Security' | 'Lexical' | 'Syntax'>(
    'All'
  );
  const [tokenGroups, setTokenGroups] = useState<string[]>([]);
  const [showAllTokens, setShowAllTokens] = useState(false);
  const [activeSample, setActiveSample] = useState<SampleItem | null>(null);
  const [openDocs, setOpenDocs] = useState<DocItem[]>([]);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const [flyout, setFlyout] = useState<'files' | 'samples' | 'help' | null>(null);
  const lastFlyoutRef = useRef<'files' | 'samples' | 'help'>('files');
  const lastAnalyzedSourceRef = useRef<string | null>(null);
  const directoryInputRef = useRef<HTMLInputElement | null>(null);
  const flyoutReturnRef = useRef<HTMLButtonElement | null>(null);
  const flyoutRef = useRef<HTMLDivElement | null>(null);

  const [navTarget, setNavTarget] = useState<NavTarget | null>(null);
  const [reviewFixesOpen, setReviewFixesOpen] = useState(false);
  const [analyzeWhileTyping, setAnalyzeWhileTyping] = useState<boolean>(() => {
    try {
      return localStorage.getItem('securelex-analyze-while-typing') === 'true';
    } catch {
      return false;
    }
  });

  const activeDoc = openDocs.find((doc) => doc.id === activeDocId) || null;

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
    } catch {
      dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: false });
    }
  }, [dispatch]);

  useEffect(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);

  // Main Analysis function (runs ONLY on Analyze button or Ctrl+Enter)
  const runAnalysis = useCallback(
    async (sourceCode: string, targetLanguage: string, targetFilename: string) => {
      if (!sourceCode.trim()) {
        abortControllerRef.current?.abort();
        dispatch({ type: 'CLEAR_ANALYSIS' });
        return;
      }

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;
      const requestId = ++analysisRequestRef.current;
      const targetDocId = activeDocId;

      dispatch({ type: 'SET_ANALYZING', payload: true });
      setOpenDocs((docs) =>
        docs.map((d) => (d.id === targetDocId ? { ...d, status: 'analysing' } : d))
      );

      try {
        const res = await api.analyze(
          {
            source: sourceCode,
            language: targetLanguage === 'auto' ? null : targetLanguage,
            filename: targetFilename,
            options: { fixes: true, ml: true, include_tokens: true, agent: state.agentMode },
          },
          controller.signal
        );

        if (
          controller.signal.aborted ||
          requestId !== analysisRequestRef.current ||
          currentContextRef.current.source !== sourceCode
        ) {
          if (requestId === analysisRequestRef.current) {
            dispatch({ type: 'SET_ANALYZING', payload: false });
          }
          return;
        }

        dispatch({ type: 'SET_ANALYSIS', payload: res });
        lastAnalyzedSourceRef.current = sourceCode;
        dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: true });
        setOpenDocs((docs) =>
          docs.map((d) =>
            d.id === targetDocId
              ? {
                  ...d,
                  analysis: res,
                  resultVersion: d.contentVersion,
                  status: 'analysed',
                  durationMs: res.engine?.elapsed_ms,
                }
              : d
          )
        );
      } catch (err: any) {
        if (
          err.name === 'AbortError' ||
          controller.signal.aborted ||
          requestId !== analysisRequestRef.current
        ) {
          return;
        }

        dispatch({ type: 'SET_ANALYZING', payload: false });
        dispatch({ type: 'SET_BACKEND_AVAILABLE', payload: false });
        setOpenDocs((docs) =>
          docs.map((d) =>
            d.id === targetDocId
              ? { ...d, status: 'error', errorMessage: err.detail || err.message }
              : d
          )
        );
        dispatch({
          type: 'ADD_TOAST',
          payload: {
            message: err.detail || 'Backend unreachable. Running offline.',
            type: 'warning',
          },
        });
      }
    },
    [dispatch, activeDocId]
  );

  // Auto-analyze debounced ONLY when analyzeWhileTyping is enabled
  useEffect(() => {
    if (!analyzeWhileTyping) return;
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
  }, [state.source, state.language, state.filename, analyzeWhileTyping, runAnalysis]);

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

  // Token Insights Loader
  const loadTokenInsights = useCallback(
    async (tokenIdx: number) => {
      dispatch({ type: 'SELECT_TOKEN_INDEX', payload: tokenIdx });
      dispatch({ type: 'SET_LOADING_INSIGHTS', payload: true });

      try {
        const res = await api.getMLInsights({
          source: state.source,
          language:
            state.language === 'auto' ? state.analysis?.language || 'python' : state.language,
          token_index: tokenIdx,
        });
        dispatch({ type: 'SET_ML_INSIGHTS', payload: res });
      } catch {
        dispatch({ type: 'SET_LOADING_INSIGHTS', payload: false });
      }
    },
    [dispatch, state.source, state.language, state.analysis]
  );

  // Fix Application
  const handleApplyFix = async (fix: Fix, finding: Finding) => {
    if (activeDoc?.status === 'stale') {
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: 'Analyse again first: code was edited since last analysis',
          type: 'warning',
        },
      });
      return;
    }

    try {
      const response = await api.applyFix({
        source: state.source,
        language: state.language === 'auto' ? 'python' : state.language,
        finding_id: finding.id,
        fix_id: fix.id,
        filename: state.filename,
      });
      const newSource = response.new_source;
      dispatch({ type: 'SET_SOURCE', payload: newSource });
      dirtyRef.current = true;
      setOpenDocs((docs) =>
        docs.map((doc) =>
          doc.id === activeDocId
            ? {
                ...doc,
                content: newSource,
                dirty: true,
                contentVersion: doc.contentVersion + 1,
              }
            : doc
        )
      );
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: 'Fix applied — Ctrl+Z to undo', type: 'success' },
      });

      await runAnalysis(newSource, state.language, state.filename);
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: `Failed to apply fix: ${err.message}`, type: 'error' },
      });
    }
  };

  // Fix All Action (Safe Verified fixes only)
  const handleFixAll = async () => {
    if (activeDoc?.status === 'stale') {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: 'Analyse again first before applying Fix all', type: 'warning' },
      });
      return;
    }

    dispatch({ type: 'SET_ANALYZING', payload: true });
    try {
      const res = await api.applyFixAll({
        source: state.source,
        language: state.language === 'auto' ? 'python' : state.language,
        filename: state.filename,
        allow_review: false,
      });

      dispatch({ type: 'SET_SOURCE', payload: res.new_source });
      dirtyRef.current = true;
      setOpenDocs((docs) =>
        docs.map((doc) =>
          doc.id === activeDocId
            ? {
                ...doc,
                content: res.new_source,
                dirty: true,
                contentVersion: doc.contentVersion + 1,
              }
            : doc
        )
      );
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Applied ${res.applied.length} fixes — score ${res.score_before} -> ${res.score_after}`,
          type: 'success',
        },
      });

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

  // Open Review Diff View Modal
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
          diff: generateUnifiedDiff(state.source, newSource, state.filename || 'source'),
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
    dirtyRef.current = true;
    setOpenDocs((docs) =>
      docs.map((doc) =>
        doc.id === activeDocId
          ? { ...doc, content: newSource, dirty: true, contentVersion: doc.contentVersion + 1 }
          : doc
      )
    );
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
        payload: { message: 'Thanks - saved for next model retrain', type: 'success' },
      });
    } catch {
      dispatch({ type: 'HIDE_FINDING', payload: finding.id });
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: 'Thanks - saved for next model retrain', type: 'success' },
      });
    }
  };

  // Suppression Comment Action (adds # or // securelex: ignore <RULE_ID> undoable edit)
  const handleSuppressFinding = async (finding: Finding) => {
    const isPy =
      finding.rule_id.includes('-PY-') ||
      state.language === 'python' ||
      (state.filename && state.filename.endsWith('.py'));
    const commentPrefix = isPy ? '#' : '//';
    const comment = `${commentPrefix} securelex: ignore ${finding.rule_id}`;

    const lines = state.source.split('\n');
    const targetLineIndex = Math.max(0, (finding.range?.start_line || 1) - 1);
    const currentLineText = lines[targetLineIndex] || '';
    const indent = currentLineText.match(/^\s*/)?.[0] || '';
    const newLines = [...lines];
    newLines.splice(targetLineIndex, 0, `${indent}${comment}`);
    const newSource = newLines.join('\n');

    dirtyRef.current = true;
    dispatch({ type: 'SET_SOURCE', payload: newSource });
    setOpenDocs((docs) =>
      docs.map((doc) =>
        doc.id === activeDocId
          ? {
              ...doc,
              content: newSource,
              dirty: true,
              contentVersion: doc.contentVersion + 1,
            }
          : doc
      )
    );
    dispatch({
      type: 'ADD_TOAST',
      payload: { message: `Suppression comment added — Ctrl+Z to undo`, type: 'info' },
    });
    await runAnalysis(newSource, state.language, state.filename);
  };

  // Ask AI for Alternative Fix Action
  const handleAskAIFix = async (finding: Finding) => {
    if (!llmStatus.configured) {
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message:
            'No LLM provider configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY in .env',
          type: 'info',
        },
      });
      return;
    }
    setIsAskingAI(true);
    try {
      const res = await api.requestLLMFix({
        source: state.source,
        finding_id: finding.id,
        rule_id: finding.rule_id,
        language: state.language === 'auto' ? undefined : state.language,
        start_line: finding.range?.start_line,
        start_col: finding.range?.start_col,
      });

      if (res.fixes && res.fixes.length > 0) {
        if (state.analysis) {
          const updatedFindings = state.analysis.findings.map((f) => {
            if (f.id === finding.id) {
              return {
                ...f,
                fixes: [...(f.fixes || []), ...res.fixes],
              };
            }
            return f;
          });
          dispatch({
            type: 'SET_ANALYSIS',
            payload: {
              ...state.analysis,
              findings: updatedFindings,
            },
          });
        }
        dispatch({
          type: 'ADD_TOAST',
          payload: {
            message: `Generated ${res.fixes.length} AI fix candidate(s)`,
            type: 'success',
          },
        });
      } else {
        dispatch({
          type: 'ADD_TOAST',
          payload: { message: res.notes || 'No new fixes suggested by AI', type: 'info' },
        });
      }
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: `AI Fix request failed: ${err.message}`, type: 'error' },
      });
    } finally {
      setIsAskingAI(false);
    }
  };

  // Navigation: Next / Prev problem (F8 / Shift+F8)
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

  // Select Sample Preset (Opens as a new editable file)
  const handleSelectSample = (sample: SampleItem) => {
    setActiveSample(sample);
    const existing = openDocs.find((d) => d.sampleId === sample.id && !d.dirty);
    if (existing) {
      activateDoc(existing);
      return;
    }
    const id = `sample-${sample.id}-${Date.now()}-${untitledIndexRef.current++}`;
    const newDoc: DocItem = {
      id,
      name: sample.filename,
      content: sample.code,
      language: sample.language,
      dirty: false,
      sampleId: sample.id,
      analysis: null,
      resultVersion: -1,
      contentVersion: 0,
      status: 'not analysed',
    };
    setOpenDocs((docs) => [...docs, newDoc]);
    setActiveDocId(id);
    dirtyRef.current = false;
    dispatch({ type: 'SET_SOURCE', payload: sample.code });
    dispatch({ type: 'SET_LANGUAGE', payload: sample.language });
    dispatch({ type: 'SET_FILENAME', payload: sample.filename });
    dispatch({ type: 'CLEAR_ANALYSIS' });
  };

  // Switch Active Document Tab
  const activateDoc = (doc: DocItem) => {
    if (doc.id === activeDocId) return;
    setActiveDocId(doc.id);
    dispatch({ type: 'SET_SOURCE', payload: doc.content });
    dispatch({ type: 'SET_FILENAME', payload: doc.name });
    dispatch({ type: 'SET_LANGUAGE', payload: doc.language });
    if (doc.analysis) {
      dispatch({ type: 'SET_ANALYSIS', payload: doc.analysis });
    } else {
      dispatch({ type: 'CLEAR_ANALYSIS' });
    }
  };

  // Open Local File Object
  const handleOpenFileObject = async (file: File, folderPath?: string) => {
    const outcome = await processFileForOpen(file, folderPath);
    if (outcome.isUnsupported) {
      return { unsupported: true };
    }
    if (outcome.error) {
      dispatch({ type: 'ADD_TOAST', payload: { message: outcome.error, type: 'error' } });
      return { error: true };
    }
    if (outcome.warning) {
      dispatch({ type: 'ADD_TOAST', payload: { message: outcome.warning, type: 'warning' } });
    }
    if (outcome.file) {
      const ext = outcome.file.name.toLowerCase().split('.').pop() || '';
      const language =
        ext === 'py'
          ? 'python'
          : ext === 'java'
            ? 'java'
            : ['js', 'jsx', 'mjs', 'cjs'].includes(ext)
              ? 'javascript'
              : ['c', 'h', 'cc', 'cpp', 'cxx', 'hpp'].includes(ext)
                ? 'cpp'
                : 'auto';
      const id = `file-${Date.now()}-${untitledIndexRef.current++}`;
      const newDoc: DocItem = {
        id,
        name: outcome.file.name,
        content: outcome.file.content,
        language,
        dirty: false,
        folderPath: outcome.file.folderPath,
        hasCrlf: outcome.file.hasCrlf,
        analysis: null,
        resultVersion: -1,
        contentVersion: 0,
        status: 'not analysed',
      };
      setOpenDocs((docs) => [...docs, newDoc]);
      setActiveDocId(id);
      dispatch({ type: 'SET_FILENAME', payload: outcome.file.name });
      dispatch({ type: 'SET_SOURCE', payload: outcome.file.content });
      dispatch({ type: 'SET_LANGUAGE', payload: language });
      dispatch({ type: 'CLEAR_ANALYSIS' });
    }
    return { success: true };
  };

  const createNewFile = () => {
    setActiveSample(null);
    dirtyRef.current = false;
    untitledIndexRef.current += 1;
    const name = `untitled-${untitledIndexRef.current}`;
    const id = `new-${Date.now()}-${untitledIndexRef.current}`;
    const newDoc: DocItem = {
      id,
      name,
      content: '',
      language: 'auto',
      dirty: false,
      analysis: null,
      resultVersion: -1,
      contentVersion: 0,
      status: 'not analysed',
    };
    setOpenDocs((docs) => [...docs, newDoc]);
    setActiveDocId(id);
    dispatch({ type: 'SET_SOURCE', payload: '' });
    dispatch({ type: 'SET_FILENAME', payload: name });
    dispatch({ type: 'SET_LANGUAGE', payload: 'auto' });
    dispatch({ type: 'CLEAR_ANALYSIS' });
  };

  const closeCurrentFile = (targetId?: string) => {
    const idToClose = targetId || activeDocId;
    if (!idToClose) return;
    const docToClose = openDocs.find((d) => d.id === idToClose);
    if (!docToClose) return;

    if (docToClose.dirty) {
      const confirmClose = window.confirm(
        `File "${docToClose.name}" has unsaved changes. Close anyway?`
      );
      if (!confirmClose) return;
    }

    // Clean up Monaco model
    try {
      const uri = monaco.Uri.parse(`inmemory://securelex/${encodeURIComponent(docToClose.id)}`);
      monaco.editor.getModel(uri)?.dispose();
    } catch {}

    const remaining = openDocs.filter((d) => d.id !== idToClose);
    setOpenDocs(remaining);
    if (activeDocId === idToClose) {
      if (remaining.length > 0) {
        const nextDoc = remaining[remaining.length - 1];
        activateDoc(nextDoc);
      } else {
        setActiveDocId(null);
        dispatch({ type: 'SET_SOURCE', payload: '' });
        dispatch({ type: 'SET_FILENAME', payload: '' });
        dispatch({ type: 'SET_LANGUAGE', payload: 'auto' });
        dispatch({ type: 'CLEAR_ANALYSIS' });
      }
    }
  };

  const toggleFlyout = (next: 'files' | 'samples' | 'help') => {
    lastFlyoutRef.current = next;
    setFlyout((current) => (current === next ? null : next));
  };

  // Keyboard shortcut listener
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const cmdOrCtrl = isMac ? event.metaKey : event.ctrlKey;

      if (cmdOrCtrl && event.shiftKey && event.key.toLowerCase() === 'p') {
        event.preventDefault();
        setPaletteOpen(true);
        return;
      }

      if (event.key === 'F8') {
        event.preventDefault();
        if (event.shiftKey) handlePrevProblem();
        else handleNextProblem();
        return;
      }

      if (cmdOrCtrl && event.key === 'Enter') {
        event.preventDefault();
        runAnalysis(state.source, state.language, state.filename);
        return;
      }

      if (cmdOrCtrl && event.key === '.') {
        event.preventDefault();
        if (selectedFinding && selectedFinding.fixes?.length) {
          handleApplyFix(selectedFinding.fixes[0], selectedFinding);
        }
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 's') {
        event.preventDefault();
        handleDownload();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 'n') {
        event.preventDefault();
        createNewFile();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 'o') {
        event.preventDefault();
        fileInputRef.current?.click();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 'w') {
        event.preventDefault();
        closeCurrentFile();
        return;
      }

      if (cmdOrCtrl && event.key.toLowerCase() === 'b') {
        event.preventDefault();
        setFlyout((current) => (current ? null : lastFlyoutRef.current));
        return;
      }

      if (event.key === 'Escape' && flyout) {
        event.preventDefault();
        setFlyout(null);
        flyoutReturnRef.current?.focus();
        return;
      }

      if (
        event.key === '?' &&
        !cmdOrCtrl &&
        !event.altKey &&
        !(
          event.target instanceof HTMLElement &&
          (event.target.isContentEditable || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName))
        )
      ) {
        setShortcutsOpen(true);
        return;
      }
    };

    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (dirtyRef.current || openDocs.some((d) => d.dirty)) {
        event.preventDefault();
        event.returnValue = '';
      }
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('beforeunload', onBeforeUnload);
    };
  }, [dispatch, state.source, state.filename, flyout, openDocs, activeFindings, activeDocId]);

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

  const selectedFinding = activeFindings.find((f) => f.id === state.selectedFindingId) || null;

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

  // Safe and Review fixes calculations
  const safeFixCount = activeFindings.reduce(
    (count, finding) =>
      count +
      (finding.fixes || []).filter((fix) => fix.confidence === 'safe' && fix.verification?.verified)
        .length,
    0
  );

  const reviewFixItems: ReviewFixItem[] = [];
  activeFindings.forEach((finding) => {
    (finding.fixes || []).forEach((fix) => {
      if (fix.confidence === 'review' && fix.edits && fix.edits.length > 0) {
        const oldSnippet = fix.edits
          .map((e) => {
            const lines = state.source.split('\n');
            const startLine = Math.max(0, e.range.start_line - 1);
            const endLine = Math.max(startLine, e.range.end_line - 1);
            if (startLine === endLine) {
              return (lines[startLine] || '').slice(
                e.range.start_col - 1,
                Math.max(e.range.start_col - 1, e.range.end_col - 1)
              );
            }
            return [
              lines[startLine]?.slice(e.range.start_col - 1),
              ...lines.slice(startLine + 1, endLine),
              lines[endLine]?.slice(0, e.range.end_col - 1),
            ].join('\n');
          })
          .join('\n');

        reviewFixItems.push({
          finding,
          fix,
          oldSnippet,
          newSnippet: fix.edits.map((e) => e.new_text).join(''),
        });
      }
    });
  });

  const handleApplySelectedReviewFixes = async (selected: ReviewFixItem[]) => {
    setReviewFixesOpen(false);
    if (selected.length === 0) return;
    try {
      let currentSource = state.source;
      for (const item of selected) {
        currentSource = applyEdits(currentSource, item.fix.edits);
      }
      dispatch({ type: 'SET_SOURCE', payload: currentSource });
      dirtyRef.current = true;
      setOpenDocs((docs) =>
        docs.map((doc) =>
          doc.id === activeDocId
            ? {
                ...doc,
                content: currentSource,
                dirty: true,
                contentVersion: doc.contentVersion + 1,
              }
            : doc
        )
      );
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          message: `Applied ${selected.length} review fixes — Ctrl+Z to undo`,
          type: 'success',
        },
      });
      await runAnalysis(currentSource, state.language, state.filename);
    } catch (err: any) {
      dispatch({
        type: 'ADD_TOAST',
        payload: { message: `Failed to apply review fixes: ${err.message}`, type: 'error' },
      });
    }
  };

  const fileAnalysisState = activeDoc?.status || 'not analysed';

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
        <aside data-qa="strip" className="ui5-strip" aria-label="Panels">
          <button
            aria-label="Files"
            title="Files"
            aria-pressed={flyout === 'files'}
            onClick={(event) => {
              flyoutReturnRef.current = event.currentTarget;
              toggleFlyout('files');
            }}
          >
            <Files size={17} strokeWidth={1.5} />
          </button>
          <button
            aria-label="Samples"
            title="Samples"
            aria-pressed={flyout === 'samples'}
            onClick={(event) => {
              flyoutReturnRef.current = event.currentTarget;
              toggleFlyout('samples');
            }}
          >
            <FlaskConical size={17} strokeWidth={1.5} />
          </button>
          <button
            aria-label="Help"
            title="Help"
            aria-pressed={flyout === 'help'}
            onClick={(event) => {
              flyoutReturnRef.current = event.currentTarget;
              toggleFlyout('help');
            }}
          >
            <CircleHelp size={17} strokeWidth={1.5} />
          </button>
        </aside>

        {flyout && (
          <div ref={flyoutRef}>
            <FlyoutPanel
              mode={flyout}
              files={openDocs}
              activeId={activeDocId}
              samples={state.samples}
              language={state.language}
              engine={state.analysis?.engine}
              themeMode={themeMode}
              themeResolved={themeResolved}
              onThemeChange={setThemeMode}
              analyzeWhileTyping={analyzeWhileTyping}
              onToggleAnalyzeWhileTyping={handleToggleAnalyzeWhileTyping}
              onClose={() => {
                setFlyout(null);
                flyoutReturnRef.current?.focus();
              }}
              onNew={createNewFile}
              onOpen={() => fileInputRef.current?.click()}
              onFolder={() => directoryInputRef.current?.click()}
              onSave={handleDownload}
              onSwitch={(id) => {
                const doc = openDocs.find((item) => item.id === id);
                if (doc) activateDoc(doc);
              }}
              onCloseFile={closeCurrentFile}
              onSample={(sample) => {
                handleSelectSample(sample);
                setFlyout(null);
              }}
            />
          </div>
        )}

        <PanelGroup direction="horizontal" autoSaveId="ui5-editor-split" className="ui5-panels">
          <Panel defaultSize={39} minSize={34}>
            <div data-qa="code-pane" className="ui5-editor">
              {openDocs.length >= 2 && (
                <div
                  data-qa="strip-files"
                  className="ui6-tabs"
                  role="tablist"
                  aria-label="Open files"
                >
                  {openDocs.map((doc) => (
                    <div
                      role="presentation"
                      className={`ui6-tab ${doc.id === activeDocId ? 'active' : ''}`}
                      key={doc.id}
                    >
                      <button
                        role="tab"
                        aria-selected={doc.id === activeDocId}
                        onClick={() => activateDoc(doc)}
                        title={doc.name}
                      >
                        {doc.name}
                        {doc.dirty && <i aria-label="Unsaved changes" />}
                      </button>
                      <button
                        aria-label={`Close ${doc.name}`}
                        onClick={() => closeCurrentFile(doc.id)}
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <EditorPane
                source={state.source}
                language={state.language}
                filename={state.filename}
                modelKey={activeDocId}
                findings={activeFindings}
                tokens={state.analysis?.tokens || []}
                analysis={state.analysis}
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
              />
              <div data-qa="legend-row" className="ui5-legend">
                <span className="ui5-badge safe">Safe</span>
                <span className="ui5-badge warning">Valid but insecure</span>
                <span className="ui5-badge danger">Lexical error</span>
              </div>
            </div>
          </Panel>
          <PanelResizeHandle className="ui5-divider" />
          <Panel defaultSize={61} minSize={42}>
            <FindingPanel
              activeTab={state.activeTab}
              onChangeTab={(tab) => dispatch({ type: 'SET_ACTIVE_TAB', payload: tab })}
              selectedFinding={selectedFinding}
              summary={state.analysis?.summary || null}
              findings={activeFindings}
              engine={state.analysis?.engine || null}
              language={state.analysis?.language || state.language}
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
                setNavTarget({ type: 'finding', range: step.range, timestamp: Date.now() });
              }}
              onToggleDataFlow={(id) => {
                dispatch({
                  type: 'SET_DATA_FLOW',
                  payload: state.activeDataFlowFindingId === id ? null : id,
                });
              }}
              isDataFlowActive={state.activeDataFlowFindingId === state.selectedFindingId}
              onMarkFalsePositive={handleMarkFalsePositive}
              onSuppressFinding={handleSuppressFinding}
              onAskAIFix={handleAskAIFix}
              isAskingAI={isAskingAI}
              llmConfigured={llmStatus.configured}
              llmProvider={llmStatus.provider}
              analysis={state.analysis}
              selectedTokenIndex={state.selectedTokenIndex}
              tokenMap={tokenMap}
              onTokenMap={setTokenMap}
              tokenCategory={tokenCategory}
              onTokenCategory={setTokenCategory}
              onSelectToken={selectTokenFromPanel}
              onLoadTokenML={loadTokenInsights}
              onSelectFindingById={selectFindingAndToken}
              showAllTokens={showAllTokens}
              tokenMainFilter={tokenMainFilter}
              tokenGroups={tokenGroups}
              sample={activeSample}
              sampleEdited={Boolean(activeSample && state.source !== activeSample.code)}
              onDemoStep={(delta) => {
                const index = DEMO_PATH.indexOf(activeSample?.id || '');
                const next = state.samples.find((item) => item.id === DEMO_PATH[index + delta]);
                if (next) handleSelectSample(next);
              }}
              agentMode={state.agentMode}
              agentModel={state.agentStatus?.model || 'qwen2.5-coder:3b'}
            />
          </Panel>
        </PanelGroup>
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

      <nav data-qa="filter-row" className="ui5-filter" aria-label="Finding counts">
        <strong
          style={{ cursor: 'pointer' }}
          onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'problems' })}
          title="View Problems List"
        >
          Problems {state.analysis ? activeFindings.length : 0}
        </strong>
        {fileAnalysisState === 'stale' && (
          <span className="ui6-badge insecure" style={{ marginLeft: 6 }}>
            Out of date
          </span>
        )}
        {(['All', 'Security', 'Lexical', 'Syntax'] as const).map((filter) => (
          <button
            key={filter}
            className="ui6-chip"
            aria-pressed={tokenMainFilter === filter}
            onClick={() => {
              setTokenMainFilter(filter);
              dispatch({ type: 'SET_ACTIVE_TAB', payload: 'tokens' });
            }}
          >
            {filter}
            {filter === 'Security'
              ? ` ${activeFindings.filter((f) => !['lexical', 'syntax'].includes(f.kind || 'security')).length}`
              : filter === 'Lexical'
                ? ` ${activeFindings.filter((f) => f.kind === 'lexical').length}`
                : filter === 'Syntax'
                  ? ` ${activeFindings.filter((f) => f.kind === 'syntax').length}`
                  : ''}
          </button>
        ))}
        {(['dangerous', 'suspicious', 'malicious'] as const).map((group) => (
          <button
            key={group}
            className="ui6-chip"
            aria-pressed={tokenGroups.includes(group)}
            onClick={() => {
              setTokenGroups((current) =>
                current.includes(group)
                  ? current.filter((item) => item !== group)
                  : [...current, group]
              );
              dispatch({ type: 'SET_ACTIVE_TAB', payload: 'tokens' });
            }}
          >
            {group[0].toUpperCase() + group.slice(1)}
          </button>
        ))}
        <label className="ui6-show-all">
          <input
            type="checkbox"
            checked={showAllTokens}
            onChange={(event) => {
              setShowAllTokens(event.target.checked);
              dispatch({ type: 'SET_ACTIVE_TAB', payload: 'tokens' });
            }}
          />
          Show all
        </label>
        <span style={{ marginLeft: 'auto' }}>F8 next</span>
      </nav>

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

      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        commands={
          [
            { label: 'Theme: Dark', run: () => setThemeMode('dark') },
            { label: 'Theme: Light', run: () => setThemeMode('light') },
            { label: 'Theme: System', run: () => setThemeMode('system') },
            { label: 'Toggle theme', run: toggleTheme },
            { label: 'New File', run: createNewFile },
            { label: 'Open File', run: () => fileInputRef.current?.click() },
            { label: 'Open Folder', run: () => directoryInputRef.current?.click() },
            { label: 'Save', run: handleDownload },
            { label: 'Close File', run: closeCurrentFile },
            {
              label: 'Analyze',
              run: () => runAnalysis(state.source, state.language, state.filename),
            },
            {
              label: `Fix All (${safeFixCount})`,
              run: handleFixAll,
            },
            { label: 'Next Problem', run: handleNextProblem },
            { label: 'Previous Problem', run: handlePrevProblem },
            {
              label: 'Show Token Security',
              run: () => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'tokens' }),
            },
            {
              label: 'Toggle Token Map',
              run: () =>
                setTokenMap((mode) =>
                  mode === 'off' ? 'security' : mode === 'security' ? 'full' : 'off'
                ),
            },
            {
              label: 'Show Summary',
              run: () => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'summary' }),
            },
            {
              label: 'Show ML Insights',
              run: () => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'ml' }),
            },
            { label: 'Toggle Sidebar', run: () => dispatch({ type: 'TOGGLE_SIDEBAR' }) },
            ...state.samples.slice(0, 20).map((sample) => ({
              label: `Open Sample: ${sample.title}`,
              run: () => handleSelectSample(sample),
              keywords: sample.language,
            })),
            ...state.languages.map((language) => ({
              label: `Change Language: ${language.display_name}`,
              run: () => dispatch({ type: 'SET_LANGUAGE', payload: language.id }),
            })),
            { label: 'Keyboard Shortcuts', run: () => setShortcutsOpen(true) },
          ] as PaletteCommand[]
        }
      />

      <KeyboardShortcutsModal isOpen={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />

      {/* Hidden File Input for Open File */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".py,.java,.js,.mjs,.cjs,.jsx,.c,.h,.cc,.cpp,.cxx,.hpp"
        style={{ display: 'none' }}
        onChange={async (event) => {
          const files = Array.from(event.target.files || []);
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
          event.currentTarget.value = '';
        }}
      />

      {/* Hidden Directory Input for Open Folder */}
      <input
        ref={directoryInputRef}
        type="file"
        multiple
        style={{ display: 'none' }}
        {...({ webkitdirectory: '', directory: '' } as React.InputHTMLAttributes<HTMLInputElement>)}
        onChange={async (event) => {
          const files = Array.from(event.currentTarget.files || []);
          const skipPatterns = /(node_modules|\.git|venv|__pycache__|dist|build)/i;
          const filtered = files
            .filter((f) => {
              const rel =
                (f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name;
              return !skipPatterns.test(rel);
            })
            .slice(0, 200);

          let unsupportedCount = 0;
          for (const file of filtered) {
            const rel =
              (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
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
          event.currentTarget.value = '';
        }}
      />

      {/* Diff Review Modal */}
      {state.diffModal && state.diffModal.fix && state.diffModal.finding && (
        <DiffView
          isOpen={state.diffModal.isOpen}
          fix={state.diffModal.fix}
          finding={state.diffModal.finding}
          diff={state.diffModal.diff}
          before={state.diffModal.oldSource}
          after={state.diffModal.newSource}
          onApply={handleApplyDiffFix}
          onCancel={() => dispatch({ type: 'CLOSE_DIFF_MODAL' })}
        />
      )}

      {/* Review Fixes Modal */}
      <ReviewFixesModal
        isOpen={reviewFixesOpen}
        fixes={reviewFixItems}
        onClose={() => setReviewFixesOpen(false)}
        onApplySelected={handleApplySelectedReviewFixes}
      />

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
  overflow: 'hidden',
  backgroundColor: 'var(--surface-1)',
  color: 'var(--text-primary)',
};

const backendWarningBannerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '6px 14px',
  backgroundColor: 'var(--danger-wash)',
  borderBottom: '1px solid var(--border)',
  color: 'var(--text-danger)',
  fontSize: '11px',
};

const codeTagStyle: React.CSSProperties = {
  padding: '1px 5px',
  backgroundColor: 'var(--surface-2)',
  borderRadius: '3px',
  fontFamily: 'var(--font-code)',
};

const retryButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  padding: '3px 8px',
  backgroundColor: 'var(--bg-danger)',
  color: 'var(--text-danger)',
  border: '1px solid var(--border)',
  borderRadius: '4px',
  fontSize: '10px',
  fontWeight: 600,
  cursor: 'pointer',
};
