import React, {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from 'react';
import type * as Monaco from 'monaco-editor';
import {
  apiClient,
  type CapabilitiesResponse,
  type TokenV2,
  type DiagnosticV2,
  type WorkspaceFileNode,
  type PatchProposal,
  type AIGenerateResponse,
} from '../api/client';
import { useTheme } from '../theme/theme';
import { Header } from './components/Header';
import { ActivityBar, type SidebarPane } from './components/ActivityBar';
import { ExplorerSidebar } from './components/ExplorerSidebar';
import { EditorWorkspace } from './components/EditorWorkspace';
import { AnalysisPanel, type BottomPanelTab } from './components/AnalysisPanel';
import { AssistantPanel, type ChatMessage } from './components/AssistantPanel';
import { StatusBar } from './components/StatusBar';
import { BuildWithAiModal, type SupportedLanguage } from './components/BuildWithAiModal';
import { CommandPaletteModal, type CommandItem } from './components/CommandPaletteModal';
import { ToastBox, type Toast } from './components/ToastBox';
import type { TokenItem } from './components/TokenInspector';
import type { DiagnosticItem } from './components/DiagnosticsPanel';
import type { PipelineStageInfo, StageStatus } from './components/PipelinePanel';
import type { SecurityFindingItem } from './components/SecurityPanel';
import {
  ideReducer,
  initialIDEState,
  selectActiveDocument,
  deriveCanonicalAnalysisStatus,
  type IDEDocument,
} from './state/store';
import {
  validatePatchProposal,
  applyPatchToSource,
  createEnrichedPatchProposal,
  extractProposedPatchFromAiResponse,
  type EnrichedPatchProposal,
} from './patch/patchWorkflow';
import {
  readPreferences,
  writePreferences,
  type UserPreferences,
} from './settings/preferences';
import './reference-theme.css';

export const IDE: React.FC = () => {
  const { resolved: resolvedTheme, toggleTheme, mode: themeMode, setMode: setThemeMode } = useTheme();
  const [state, dispatch] = useReducer(ideReducer, initialIDEState);

  // User Preferences
  const [prefs, setPrefs] = useState<UserPreferences>(() => readPreferences());

  // App UI state
  const [activePane, setActivePane] = useState<SidebarPane>('pane-explorer');
  const [activeBottomTab, setActiveBottomTab] = useState<BottomPanelTab>('view-tokens');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => prefs.sidebarCollapsed);
  const [sidebarWidth, setSidebarWidth] = useState<number>(() => prefs.panelSizes.sidebarWidth || 220);
  const [bottomHeight, setBottomHeight] = useState<number>(() => prefs.panelSizes.bottomHeight || 280);
  const [bottomCollapsed, setBottomCollapsed] = useState<boolean>(() => prefs.bottomCollapsed);
  const [assistantWidth, setAssistantWidth] = useState<number>(() => prefs.panelSizes.assistantWidth || 447);
  const [assistantOpen, setAssistantOpen] = useState<boolean>(() => !prefs.assistantCollapsed);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [engineMode, setEngineMode] = useState<'local' | 'groq'>('local');
  const [fontSize, setFontSize] = useState<number>(() => prefs.fontSize || 13);
  const [wordWrap, setWordWrap] = useState<'on' | 'off'>(() => prefs.wordWrap || 'on');
  const [minimap, setMinimap] = useState<boolean>(() => prefs.minimap ?? true);
  const [tabSize, setTabSize] = useState<number>(() => prefs.tabSize || 4);
  const [highlightUnicode, setHighlightUnicode] = useState<boolean>(() => prefs.highlightUnicode ?? true);
  const [autoAnalyze, setAutoAnalyze] = useState<boolean>(() => prefs.autoAnalyze ?? false);
  const [isMaximized, setIsMaximized] = useState<boolean>(() => prefs.bottomMaximized ?? false);
  const [buildAiModalOpen, setBuildAiModalOpen] = useState(false);
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(null);

  // Workspace File Management
  const [workspaceTree, setWorkspaceTree] = useState<WorkspaceFileNode[]>([]);

  // Analysis Error State (separate from invalid source tokens)
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Cursor position
  const [cursorPos, setCursorPos] = useState({ line: 6, col: 16 });

  // Toasts
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Selected Token
  const [selectedToken, setSelectedToken] = useState<TokenItem | null>(null);

  // AI Chat Messages & Persistence per File
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [conversationsByFile, setConversationsByFile] = useState<Record<string, ChatMessage[]>>({});
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [activeAssistantFinding, setActiveAssistantFinding] = useState<{
    title: string;
    line: number;
    col: number;
    id?: string;
  } | null>(null);
  const sessionIdRef = useRef<string>(`session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);
  const [providerCapabilities, setProviderCapabilities] = useState<{
    provider: string;
    configured: boolean;
    reachable: boolean | null;
    model: string | null;
    consent_required: boolean;
    remote_consented: boolean;
    setup_message?: string | null;
  } | null>(null);
  const [remoteConsented, setRemoteConsented] = useState<boolean>(true);

  // 7-Stage Compiler Agent Pipeline
  const [pipelineStages, setPipelineStages] = useState<PipelineStageInfo[]>([
    {
      id: 'lexer',
      name: 'Lexer',
      agentName: 'LexerAgent',
      status: 'not_run',
      elapsedMs: 0,
      outputSummary: 'Awaiting lexical stream scan and Unicode defense checks.',
      prerequisites: [],
      steps: [],
    },
    {
      id: 'parser',
      name: 'Parser',
      agentName: 'ParserAgent',
      status: 'not_run',
      elapsedMs: 0,
      outputSummary: 'Awaiting structural AST generation with panic-mode recovery.',
      prerequisites: ['lexer'],
      steps: [],
    },
    {
      id: 'semantic',
      name: 'Semantic',
      agentName: 'SemanticAgent',
      status: 'not_run',
      elapsedMs: 0,
      outputSummary: 'Awaiting static security rules and taint propagation.',
      prerequisites: ['parser'],
      steps: [],
    },
    {
      id: 'triage',
      name: 'Triage',
      agentName: 'TriageAgent',
      status: 'not_run',
      elapsedMs: 0,
      outputSummary: 'Awaiting ML vulnerability scoring and finding triage.',
      prerequisites: ['semantic'],
      steps: [],
    },
    {
      id: 'fix',
      name: 'Fix',
      agentName: 'FixAgent',
      status: 'not_run',
      elapsedMs: 0,
      outputSummary: 'Awaiting deterministic remediation patch synthesis.',
      prerequisites: ['triage'],
      steps: [],
    },
    {
      id: 'verifier',
      name: 'Verifier',
      agentName: 'VerifierAgent',
      status: 'not_run',
      elapsedMs: 0,
      outputSummary: 'Awaiting independent verifier patch check.',
      prerequisites: ['fix'],
      steps: [],
    },
    {
      id: 'explain',
      name: 'Explain',
      agentName: 'ExplainAgent',
      status: 'not_run',
      elapsedMs: 0,
      outputSummary: 'Awaiting remediation explanation synthesis.',
      prerequisites: ['verifier'],
      steps: [],
    },
  ]);
  const [selectedStageId, setSelectedStageId] = useState<string | null>('lexer');
  const [isRunningAllAgents, setIsRunningAllAgents] = useState(false);

  // Monaco Editor Ref
  const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);

  const showToast = useCallback(
    (msg: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
      setToasts((prev) => [...prev, { id, msg, type }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3200);
    },
    []
  );

  // Fetch Workspace Tree from safe backend API
  const fetchWorkspaceTree = useCallback(async () => {
    try {
      const res = await apiClient.getWorkspaceTree();
      setWorkspaceTree(res.tree || []);
      return res.tree || [];
    } catch {
      return [];
    }
  }, []);

  // Open a file into editor tabs
  const handleOpenFile = useCallback(
    async (path: string) => {
      const existing = state.documents.find((d) => d.name === path);
      if (existing) {
        dispatch({ type: 'document/activate', id: existing.id });
        return;
      }
      try {
        const fileDetail = await apiClient.getWorkspaceFile(path);
        const id = `doc-${path}`;
        dispatch({
          type: 'document/add',
          document: {
            id,
            name: fileDetail.path,
            language: fileDetail.language,
            source: fileDetail.content,
            sourceVersion: 1,
            dirty: false,
            origin: 'opened',
          },
        });
        dispatch({ type: 'document/activate', id });
      } catch (err: any) {
        showToast(`Failed to open ${path}: ${err?.message || 'Error'}`, 'error');
      }
    },
    [state.documents, showToast]
  );

  // Save active document to backend disk
  const handleSaveFile = useCallback(async () => {
    const doc = selectActiveDocument(state);
    if (!doc) return;
    try {
      await apiClient.saveWorkspaceFile(doc.name, doc.source);
      dispatch({ type: 'document/save', id: doc.id });
      showToast(`Saved ${doc.name}`, 'success');
      void fetchWorkspaceTree();
    } catch (err: any) {
      showToast(`Failed to save ${doc.name}: ${err?.message || 'Error'}`, 'error');
    }
  }, [state, fetchWorkspaceTree, showToast]);

  // Create new file
  const handleCreateFile = useCallback(
    async (path: string) => {
      try {
        await apiClient.createWorkspaceFile(path, '');
        showToast(`Created ${path}`, 'success');
        await fetchWorkspaceTree();
        await handleOpenFile(path);
      } catch (err: any) {
        showToast(`Failed to create ${path}: ${err?.message || 'Error'}`, 'error');
      }
    },
    [fetchWorkspaceTree, handleOpenFile, showToast]
  );

  // Create new folder
  const handleCreateFolder = useCallback(
    async (path: string) => {
      try {
        await apiClient.createWorkspaceFolder(path);
        showToast(`Created folder ${path}`, 'success');
        await fetchWorkspaceTree();
      } catch (err: any) {
        showToast(`Failed to create folder ${path}: ${err?.message || 'Error'}`, 'error');
      }
    },
    [fetchWorkspaceTree, showToast]
  );

  // Per-file canonical analysis status & source version
  const getFileAnalysisInfo = useCallback(
    (path: string) => {
      const doc = state.documents.find(
        (d) => d.name === path || d.name === `src/${path}` || `src/${d.name}` === path
      );
      if (!doc) return null;
      const analysisEntry = state.analysis[doc.id];
      const status = deriveCanonicalAnalysisStatus(doc, analysisEntry);
      return { status, sourceVersion: doc.sourceVersion };
    },
    [state.documents, state.analysis]
  );

  // Rename file
  const handleRenameFile = useCallback(
    async (oldPath: string, newPath: string) => {
      try {
        await apiClient.renameWorkspaceFile(oldPath, newPath);
        showToast(`Renamed ${oldPath} to ${newPath}`, 'success');
        await fetchWorkspaceTree();
        const doc = state.documents.find((d) => d.name === oldPath);
        if (doc) {
          dispatch({ type: 'document/remove', id: doc.id });
          await handleOpenFile(newPath);
        }
      } catch (err: any) {
        showToast(`Failed to rename: ${err?.message || 'Error'}`, 'error');
      }
    },
    [fetchWorkspaceTree, handleOpenFile, state.documents, showToast]
  );

  // Delete file
  const handleDeleteFile = useCallback(
    async (path: string) => {
      try {
        await apiClient.deleteWorkspaceFile(path);
        showToast(`Deleted ${path}`, 'info');
        const doc = state.documents.find((d) => d.name === path);
        if (doc) {
          dispatch({ type: 'document/remove', id: doc.id });
        }
        await fetchWorkspaceTree();
      } catch (err: any) {
        showToast(`Failed to delete: ${err?.message || 'Error'}`, 'error');
      }
    },
    [fetchWorkspaceTree, state.documents, showToast]
  );

  // Initialize Documents from Workspace Tree
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await apiClient.getWorkspaceTree();
        if (!mounted) return;
        const tree = res.tree || [];
        setWorkspaceTree(tree);

        if (state.documents.length === 0 && tree.length > 0) {
          const findFirst = (nodes: WorkspaceFileNode[]): string | null => {
            for (const n of nodes) {
              if (n.type === 'file') return n.path;
              if (n.children) {
                const f = findFirst(n.children);
                if (f) return f;
              }
            }
            return null;
          };

          const targetPath =
            tree.find((n) => n.name === 'src')?.children?.find((c) => c.name === 'main.cpp')?.path ||
            findFirst(tree) ||
            'src/main.cpp';

          try {
            const fileDetail = await apiClient.getWorkspaceFile(targetPath);
            if (mounted) {
              const id = `doc-${targetPath}`;
              dispatch({
                type: 'document/add',
                document: {
                  id,
                  name: fileDetail.path,
                  language: fileDetail.language,
                  source: fileDetail.content,
                  sourceVersion: 1,
                  dirty: false,
                  origin: 'opened',
                },
              });
              dispatch({ type: 'document/activate', id });
            }
          } catch {
            // Ignore
          }
        }
      } catch {
        // Fallback for offline / test mock environments
        if (state.documents.length === 0 && mounted) {
          const fallbackId = 'doc-src/main.cpp';
          dispatch({
            type: 'document/add',
            document: {
              id: fallbackId,
              name: 'src/main.cpp',
              language: 'cpp',
              source: `#include <iostream>\nusing namespace std;\n\nint main() {\n    int n = 5;\n    for (int i = 0; i \uFEFF<= n; i++) {\n        cout << i << " ";\n    }\n    cout << endl;\n    return 0;\n}\n`,
              sourceVersion: 1,
              dirty: false,
              origin: 'opened',
            },
          });
          dispatch({ type: 'document/activate', id: fallbackId });
        }
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  // Fetch capabilities
  useEffect(() => {
    let mounted = true;
    apiClient
      .getCapabilities()
      .then((caps) => {
        if (mounted) {
          setCapabilities(caps);
          if (caps?.ai) {
            setProviderCapabilities(caps.ai);
            setRemoteConsented(caps.ai.remote_consented || !caps.ai.consent_required);
          }
        }
      })
      .catch(() => {
        /* Offline mode continues safely */
      });
    return () => {
      mounted = false;
    };
  }, []);

  const activeDoc = selectActiveDocument(state);

  // Sync conversation when active file changes
  useEffect(() => {
    if (activeDoc) {
      const fileChat = conversationsByFile[activeDoc.id] || [];
      setChatMessages(fileChat);
    }
  }, [activeDoc?.id]);

  // Helper to update chat messages for active file
  const updateFileChatMessages = useCallback(
    (updater: (prev: ChatMessage[]) => ChatMessage[]) => {
      if (!activeDoc) return;
      setChatMessages((prev) => {
        const next = updater(prev);
        setConversationsByFile((convs) => ({
          ...convs,
          [activeDoc.id]: next,
        }));
        return next;
      });
    },
    [activeDoc]
  );
  const currentAnalysis = activeDoc ? state.analysis[activeDoc.id]?.result : null;
  const isAnalyzing = activeDoc ? state.analysis[activeDoc.id]?.status === 'running' : false;
  const isStale = activeDoc ? state.analysis[activeDoc.id]?.status === 'stale' : false;

  // Run Real Lexical Analysis via apiClient (ONLY lexical stage)
  const triggerAnalyze = useCallback(
    async (targetDoc?: IDEDocument) => {
      const doc = targetDoc || activeDoc;
      if (!doc) return;

      const abort = new AbortController();
      dispatch({ type: 'analysis/start', id: doc.id, abort });

      try {
        const result = await apiClient.analyzeV2(
          {
            source: doc.source,
            language: doc.language,
            filename: doc.name,
            api_version: 2,
            source_version: doc.sourceVersion,
            options: {
              include_tokens: true,
              stages: ['lexical'],
              fixes: false,
              ml: false,
              agent: 'off',
            },
          },
          abort.signal
        );

        setAnalysisError(null);

        dispatch({
          type: 'analysis/success',
          id: doc.id,
          result,
          version: doc.sourceVersion,
        });

        const tokenCount = result.tokens?.length ?? 0;
        const invalidCount = (result.tokens || []).filter((t) => t.lexical_status === 'invalid').length;
        const lexDiagCount = (result.syntax_diagnostics || []).length;

        if (invalidCount > 0 || lexDiagCount > 0) {
          const parts: string[] = [`${tokenCount} tokens scanned`];
          if (invalidCount > 0) parts.push(`${invalidCount} invalid`);
          if (lexDiagCount > 0) parts.push(`${lexDiagCount} lexical diagnostic(s)`);
          showToast(`Lexical scan complete: ${parts.join(', ')}.`, 'warning');
        } else if (tokenCount === 0) {
          showToast('Lexical scan complete: 0 tokens (empty or comment-only source).', 'info');
        } else {
          showToast(`Lexical scan complete: ${tokenCount} tokens scanned. All valid!`, 'success');
        }
      } catch (err: any) {
        if (err?.name !== 'AbortError') {
          dispatch({ type: 'analysis/error', id: doc.id });
          const msg = err?.message || 'Backend analysis request failed.';
          setAnalysisError(msg);
          showToast(`Analysis error: ${msg}`, 'error');
        }
      }
    },
    [activeDoc, showToast]
  );

  // Auto-analyze when activeDoc changes if not analyzed yet
  useEffect(() => {
    if (activeDoc && !state.analysis[activeDoc.id]?.result && !isAnalyzing) {
      void triggerAnalyze(activeDoc);
    }
  }, [activeDoc?.id]);

  // Map Tokens for Table and Inspector from actual backend lexer results
  const mappedTokens: TokenItem[] = useMemo(() => {
    if (!currentAnalysis?.tokens || currentAnalysis.tokens.length === 0) {
      return [];
    }

    const diags = [
      ...((currentAnalysis as any).diagnostics || []),
      ...(currentAnalysis.syntax_diagnostics || []),
      ...(currentAnalysis.semantic_diagnostics || []),
    ];
    const diagMap = new Map<string, DiagnosticV2>();
    diags.forEach((d) => diagMap.set(d.id, d));

    return currentAnalysis.tokens.map((tok: TokenV2, idx: number) => {
      const isInvalid = tok.lexical_status === 'invalid';
      const matchedDiag =
        (tok.diagnostic_ids && tok.diagnostic_ids.length > 0
          ? diagMap.get(tok.diagnostic_ids[0])
          : null) ||
        diags.find(
          (d) =>
            d.range &&
            d.range.start_line <= (tok.end_line ?? tok.start_line) &&
            d.range.end_line >= (tok.start_line ?? 1) &&
            d.range.start_col <= (tok.end_column ?? tok.start_column) &&
            d.range.end_col >= (tok.start_column ?? 1)
        );

      const actualDesc = matchedDiag?.message
        ? matchedDiag.message
        : isInvalid
        ? 'Lexical error: unclassified invalid token'
        : tok.category || tok.token_type || 'Standard token';

      const suggestion =
        (matchedDiag as any)?.remediation ||
        (matchedDiag?.related_evidence && matchedDiag.related_evidence.length > 0
          ? matchedDiag.related_evidence.join(', ')
          : undefined);

      return {
        id: idx + 1,
        tokenId: tok.id,
        line: tok.start_line ?? 1,
        col: tok.start_column ?? 1,
        endLine: tok.end_line ?? tok.start_line ?? 1,
        endCol: tok.end_column ?? ((tok.start_column ?? 1) + (tok.lexeme?.length || 1)),
        startOffset: tok.start_offset,
        endOffset: tok.end_offset,
        startOffsetCodepoint: tok.start_offset_codepoint,
        endOffsetCodepoint: tok.end_offset_codepoint,
        lexeme: tok.lexeme || '',
        type: tok.token_type || tok.category || 'Token',
        category: tok.category,
        status: isInvalid ? 'Invalid' : 'Valid',
        desc: actualDesc,
        ruleId: matchedDiag?.produced_by,
        diagnosticId: matchedDiag?.id,
        severity: matchedDiag?.severity,
        evidence: matchedDiag?.related_evidence,
        suggestion,
      };
    });
  }, [currentAnalysis]);

  // Reset selectedToken when active document switches
  useEffect(() => {
    setSelectedToken(null);
  }, [activeDoc?.id]);

  // Synchronously derived selected token that cannot lag behind or hold stale tokens across renders/edits
  const effectiveSelectedToken = useMemo(() => {
    if (mappedTokens.length === 0) return null;
    if (!selectedToken) {
      return mappedTokens.find((t) => t.status === 'Invalid') || mappedTokens[0];
    }
    const match = mappedTokens.find(
      (t) =>
        (t.tokenId && selectedToken.tokenId && t.tokenId === selectedToken.tokenId) ||
        (t.id === selectedToken.id &&
          t.line === selectedToken.line &&
          t.col === selectedToken.col &&
          t.lexeme === selectedToken.lexeme)
    );
    if (match) return match;
    return mappedTokens.find((t) => t.status === 'Invalid') || mappedTokens[0];
  }, [mappedTokens, selectedToken]);

  // Keep selectedToken state clean when active document or token set changes
  useEffect(() => {
    if (mappedTokens.length === 0) {
      setSelectedToken(null);
      return;
    }
    setSelectedToken((prev) => {
      if (!prev) return mappedTokens.find((t) => t.status === 'Invalid') || mappedTokens[0];
      const match = mappedTokens.find(
        (t) =>
          (t.tokenId && prev.tokenId && t.tokenId === prev.tokenId) ||
          (t.id === prev.id && t.line === prev.line && t.col === prev.col && t.lexeme === prev.lexeme)
      );
      return match || mappedTokens.find((t) => t.status === 'Invalid') || mappedTokens[0];
    });
  }, [mappedTokens]);

  // Highlight invalid tokens in Monaco editor with error markers
  useEffect(() => {
    if (!editorRef.current) return;
    const model = editorRef.current.getModel();
    if (!model) return;
    const monacoGlobal = (window as any).monaco;
    if (!monacoGlobal) return;

    const invalidTokens = mappedTokens.filter((t) => t.status === 'Invalid');
    const markers: Monaco.editor.IMarkerData[] = invalidTokens.map((t) => ({
      severity: monacoGlobal.MarkerSeverity.Error,
      message: t.desc || `Invalid token '${t.lexeme}'`,
      startLineNumber: t.line,
      startColumn: t.col,
      endLineNumber: t.endLine || t.line,
      endColumn: t.endCol || (t.col + Math.max(1, t.lexeme.length)),
      source: t.ruleId || 'securelex-lexer',
    }));

    monacoGlobal.editor.setModelMarkers(model, 'securelex-lexical', markers);
  }, [mappedTokens]);

  // Diagnostics mapping (from actual backend stage diagnostics)
  const mappedDiagnostics: DiagnosticItem[] = useMemo(() => {
    const raw = [
      ...(currentAnalysis?.syntax_diagnostics || []),
      ...(currentAnalysis?.semantic_diagnostics || []),
    ];
    return raw.map((d: DiagnosticV2, idx: number) => ({
      id: d.id || `diag-${idx}`,
      code: d.produced_by || `E${String(idx + 100).padStart(4, '0')}`,
      message: d.message,
      severity: (d.severity?.toLowerCase() === 'error' || d.severity?.toLowerCase() === 'high'
        ? 'error'
        : 'warning') as any,
      file: activeDoc?.name || 'source',
      line: d.range?.start_line ?? 1,
      col: d.range?.start_col ?? 1,
      endLine: d.range?.end_line,
      endCol: d.range?.end_col,
    }));
  }, [currentAnalysis, activeDoc]);

  // Security findings mapping
  const mappedSecurityFindings: SecurityFindingItem[] = useMemo(() => {
    const findings = currentAnalysis?.security_findings || [];
    return findings.map((f: any, idx: number) => ({
      id: f.id || `sec-${idx}`,
      title: f.title || f.rule_id || 'Security Finding',
      description: f.description || f.message || '',
      remediation: f.remediation || null,
      cwe: Array.isArray(f.cwe) ? f.cwe.join(', ') : f.cwe,
      severity: f.severity || 'Medium',
      confidence: f.confidence ?? (f.certainty === 'definitive' ? 1.0 : 0.85),
      certainty: f.certainty || 'heuristic',
      file: activeDoc?.name || 'source',
      line: f.range?.start_line ?? f.line,
      col: f.range?.start_col ?? f.col,
      range: f.range || {
        start_line: f.line ?? 1,
        start_col: f.col ?? 1,
        end_line: f.line ?? 1,
        end_col: (f.col ?? 1) + 1,
      },
      ruleId: f.rule_id || f.produced_by,
      detectorsFired: f.detectors_fired || [],
      toolProvenance: f.tool_provenance || [],
      evidence: f.evidence || f.related_evidence || [],
      taintPathId: f.taint_path_id || null,
    }));
  }, [currentAnalysis, activeDoc]);

  // Delta decorations for source navigation highlight
  const navDecorationsRef = useRef<string[]>([]);
  const navTimeoutRef = useRef<any>(null);

  // Jump to Code in Monaco Editor
  const handleJumpToCode = useCallback(
    async (line: number, col: number, endLine?: number, endCol?: number, file?: string) => {
      let switched = false;
      if (file) {
        const matchingDoc = state.documents.find(
          (d) => d.name === file || d.name === `src/${file}` || file === `src/${d.name}`
        );
        if (matchingDoc) {
          if (activeDoc?.id !== matchingDoc.id) {
            dispatch({ type: 'document/activate', id: matchingDoc.id });
            switched = true;
          }
        } else {
          await handleOpenFile(file);
          switched = true;
        }
      }

      setCursorPos({ line, col });

      const applyNavigation = () => {
        if (!editorRef.current) return;
        const editor = editorRef.current;
        const targetEndLine = endLine || line;
        const targetEndCol = endCol || (col + 1);

        editor.revealRangeInCenter({
          startLineNumber: line,
          startColumn: col,
          endLineNumber: targetEndLine,
          endColumn: targetEndCol,
        });
        editor.setSelection({
          startLineNumber: line,
          startColumn: col,
          endLineNumber: targetEndLine,
          endColumn: targetEndCol,
        });

        navDecorationsRef.current = editor.deltaDecorations(navDecorationsRef.current, [
          {
            range: {
              startLineNumber: line,
              startColumn: col,
              endLineNumber: targetEndLine,
              endColumn: targetEndCol,
            },
            options: {
              isWholeLine: false,
              className: 'bg-primary/20 border-b-2 border-primary animate-pulse',
              inlineClassName: 'bg-primary/30 rounded-xs ring-1 ring-primary/70',
            },
          },
        ]);

        if (navTimeoutRef.current) clearTimeout(navTimeoutRef.current);
        navTimeoutRef.current = setTimeout(() => {
          if (editorRef.current) {
            navDecorationsRef.current = editorRef.current.deltaDecorations(
              navDecorationsRef.current,
              []
            );
          }
        }, 2500);

        editor.focus();
      };

      if (switched) {
        setTimeout(applyNavigation, 60);
      } else {
        applyNavigation();
      }

      showToast(`Focused on Line ${line}, Column ${col}${file ? ` in ${file}` : ''}`);
    },
    [state.documents, activeDoc, handleOpenFile, showToast]
  );

  // Toggle Remote AI Provider Consent
  const handleToggleConsent = useCallback(async () => {
    const nextConsent = !remoteConsented;
    try {
      await apiClient.setRemoteConsent(sessionIdRef.current, nextConsent);
      setRemoteConsented(nextConsent);
      showToast(nextConsent ? 'Remote AI processing consent granted.' : 'Remote AI consent revoked.', 'info');
    } catch (err: any) {
      showToast(`Failed to update consent: ${err?.message || 'Error'}`, 'error');
    }
  }, [remoteConsented, showToast]);

  // Start New Conversation thread for active file
  const handleNewConversation = useCallback(() => {
    if (!activeDoc) return;
    setChatMessages([]);
    setConversationsByFile((convs) => ({
      ...convs,
      [activeDoc.id]: [],
    }));
    showToast(`Started new conversation thread for ${activeDoc.name}.`, 'info');
  }, [activeDoc, showToast]);

  // Insert code snippet into Monaco Editor at cursor
  const handleInsertCodeSnippet = useCallback((code: string) => {
    if (!editorRef.current) return;
    const editor = editorRef.current;
    const selection = editor.getSelection();
    if (selection) {
      editor.executeEdits('ai-assistant', [
        {
          range: selection,
          text: code,
          forceMoveMarkers: true,
        },
      ]);
    } else {
      editor.trigger('keyboard', 'type', { text: code });
    }
    editor.focus();
  }, []);

  // Conversational AI Assistant Query
  const handleSendMessage = useCallback(
    async (text: string) => {
      if (!activeDoc) return;
      const userMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'user',
        text,
        timestamp: Date.now(),
      };
      updateFileChatMessages((prev) => [...prev, userMsg]);
      setIsSendingChat(true);

      try {
        const history = chatMessages.slice(-10).map((m) => ({
          role: m.sender,
          content: m.text,
        }));

        let selectedCode: string | undefined = undefined;
        let selectedRange = {
          start_line: cursorPos.line,
          start_col: cursorPos.col,
          end_line: cursorPos.line,
          end_col: cursorPos.col + 1,
        };
        if (editorRef.current) {
          const sel = editorRef.current.getSelection();
          if (sel && !sel.isEmpty()) {
            selectedRange = {
              start_line: sel.startLineNumber,
              start_col: sel.startColumn,
              end_line: sel.endLineNumber,
              end_col: sel.endColumn,
            };
            const model = editorRef.current.getModel();
            if (model) {
              selectedCode = model.getValueInRange(sel);
            }
          }
        }

        const attachedToken =
          effectiveSelectedToken
            ? {
                id: effectiveSelectedToken.id,
                lexeme: effectiveSelectedToken.lexeme,
                type: effectiveSelectedToken.type,
                status: effectiveSelectedToken.status,
                line: effectiveSelectedToken.line,
                col: effectiveSelectedToken.col,
                desc: effectiveSelectedToken.desc,
              }
            : undefined;

        const context = {
          file: activeDoc.name,
          language: activeDoc.language,
          source_version: activeDoc.sourceVersion,
          selected_range: selectedRange,
          selected_code: selectedCode,
          selected_token: attachedToken,
          stage: activeBottomTab,
          finding: activeAssistantFinding
            ? {
                title: activeAssistantFinding.title,
                line: activeAssistantFinding.line,
                col: activeAssistantFinding.col,
                id: activeAssistantFinding.id,
              }
            : undefined,
          findings_count: mappedSecurityFindings.length,
        };

        const res = await apiClient.chatAI({
          session_id: sessionIdRef.current,
          message: text,
          source: activeDoc.source,
          language: activeDoc.language,
          history,
          context,
          remote_consent: remoteConsented,
        });

        const patch = extractProposedPatchFromAiResponse(activeDoc, res.reply, res.code_snippets);

        const assistantMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          sender: 'assistant',
          text: res.reply,
          codeSnippets: res.code_snippets,
          diff: patch?.diff,
          proposal: patch?.proposal,
          targetContext: patch
            ? {
                file: activeDoc.name,
                stage: activeBottomTab,
                findingTitle: activeAssistantFinding?.title || 'AI Proposed Modification',
                line: activeAssistantFinding?.line || cursorPos.line,
                col: activeAssistantFinding?.col || cursorPos.col,
              }
            : undefined,
          timestamp: Date.now(),
        };
        updateFileChatMessages((prev) => [...prev, assistantMsg]);
      } catch (err: any) {
        const errDetail = err?.message || err?.detail || 'AI Assistant query failed.';
        const assistantErrMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          sender: 'assistant',
          text: `⚠️ **AI Provider Notice**: ${errDetail}\n\n*Please ensure Groq API key is configured in \`.env\` and session consent is granted.*`,
          retryPrompt: text,
          timestamp: Date.now(),
        };
        updateFileChatMessages((prev) => [...prev, assistantErrMsg]);
        showToast(errDetail, 'error');
      } finally {
        setIsSendingChat(false);
      }
    },
    [activeDoc, activeAssistantFinding, activeBottomTab, chatMessages, cursorPos, effectiveSelectedToken, mappedSecurityFindings.length, mappedTokens, remoteConsented, showToast, updateFileChatMessages]
  );

  // Explain selected issue using recorded deterministic analysis evidence
  const handleExplainTarget = useCallback(
    async (target: {
      kind: 'token' | 'finding' | 'diagnostic' | 'file';
      id?: string;
      title: string;
      line?: number;
      col?: number;
    }) => {
      if (!activeDoc) return;
      setAssistantOpen(true);
      setActiveAssistantFinding({
        title: target.title,
        line: target.line || cursorPos.line,
        col: target.col || cursorPos.col,
        id: target.id,
      });

      const userPrompt = `Explain issue: ${target.title}`;
      const userMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'user',
        text: userPrompt,
        timestamp: Date.now(),
      };
      updateFileChatMessages((prev) => [...prev, userMsg]);
      setIsSendingChat(true);

      try {
        const resp = await apiClient.explainAI({
          session_id: sessionIdRef.current,
          target: target.kind,
          target_id: target.id || null,
          source: activeDoc.source,
          language: activeDoc.language,
          source_version: activeDoc.sourceVersion,
          remote_consent: remoteConsented,
        });

        const assistantMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          sender: 'assistant',
          text: resp.explanation,
          timestamp: Date.now(),
        };
        updateFileChatMessages((prev) => [...prev, assistantMsg]);
      } catch (err: any) {
        const errDetail = err?.message || err?.detail || 'Failed to explain target.';
        const assistantErrMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          sender: 'assistant',
          text: `⚠️ **Explanation Unavailable**: ${errDetail}`,
          timestamp: Date.now(),
        };
        updateFileChatMessages((prev) => [...prev, assistantErrMsg]);
        showToast(errDetail, 'error');
      } finally {
        setIsSendingChat(false);
      }
    },
    [activeDoc, cursorPos, remoteConsented, showToast, updateFileChatMessages]
  );

  // Fix with AI or ML/Rules: Propose verified fix using Deterministic Rules/ML or Groq AI
  const handleFixWithAi = useCallback(
    async (
      target: { kind: 'finding' | 'token' | 'diagnostic'; id: string; title: string },
      origin: 'rule' | 'ai' = 'ai'
    ) => {
      if (!activeDoc) return;
      setAssistantOpen(true);
      const isModel = origin === 'rule';
      showToast(
        isModel
          ? `Retrieving deterministic Model & Rule fix for ${target.title}...`
          : `Synthesizing verified AI fix for ${target.title}...`,
        'info'
      );

      const userMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'user',
        text: isModel
          ? `Fix with Model & Rules: ${target.title}`
          : `Fix with AI Assistant: ${target.title}`,
        timestamp: Date.now(),
      };
      updateFileChatMessages((prev) => [...prev, userMsg]);
      setIsSendingChat(true);

      try {
        const res = await apiClient.proposeFix({
          source: activeDoc.source,
          source_version: activeDoc.sourceVersion,
          language: activeDoc.language,
          filename: activeDoc.name,
          target: { kind: target.kind, id: target.id },
          origin,
          session_id: sessionIdRef.current,
          remote_consent: remoteConsented,
        });

        const matchingFinding = mappedSecurityFindings.find((f) => f.id === target.id) || {
          id: target.id,
          title: target.title,
        };

        const enrichedProposal = createEnrichedPatchProposal(
          res.proposal,
          activeDoc.source,
          activeDoc.name,
          {
            id: matchingFinding.id,
            title: matchingFinding.title,
            rule_id: (matchingFinding as any).ruleId,
            severity: (matchingFinding as any).severity,
          }
        );

        const introText = isModel
          ? `🤖 **Model & Rule Suggestion**: I have retrieved the deterministic fix proposal for **${target.title}**:\n\n**Rationale**: ${enrichedProposal.rationale}\n${
              enrichedProposal.risks?.length ? `\n**Risks**: ${enrichedProposal.risks.join('; ')}` : ''
            }`
          : `✨ **AI Assistant Suggestion**: I have synthesized an AI fix proposal for **${target.title}**:\n\n**Rationale**: ${enrichedProposal.rationale}\n${
              enrichedProposal.risks?.length ? `\n**Risks**: ${enrichedProposal.risks.join('; ')}` : ''
            }`;

        const assistantMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          sender: 'assistant',
          text: introText,
          diff: {
            file: activeDoc.name,
            unifiedDiff: enrichedProposal.diff,
          },
          proposal: enrichedProposal,
          targetContext: {
            file: activeDoc.name,
            stage: activeBottomTab,
            findingTitle: target.title,
            line: (matchingFinding as any).line,
            col: (matchingFinding as any).col,
          },
          timestamp: Date.now(),
        };
        updateFileChatMessages((prev) => [...prev, assistantMsg]);
      } catch (err: any) {
        const errDetail = err?.message || err?.detail || 'Failed to synthesize fix.';
        const assistantErrMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          sender: 'assistant',
          text: `⚠️ **Fix Synthesis Failed (${isModel ? 'Model/Rule' : 'AI'})**: ${errDetail}`,
          timestamp: Date.now(),
        };
        updateFileChatMessages((prev) => [...prev, assistantErrMsg]);
        showToast(errDetail, 'error');
      } finally {
        setIsSendingChat(false);
      }
    },
    [activeDoc, activeBottomTab, mappedSecurityFindings, remoteConsented, showToast, updateFileChatMessages]
  );

  const handleSwitchProposalOrigin = useCallback(
    (proposal?: any, targetOrigin: 'rule' | 'ai' = 'ai') => {
      if (!proposal) return;
      const targetId = proposal.target_finding_id || proposal.finding?.id;
      const targetTitle = proposal.finding?.title || 'Active Target';
      const kind = proposal.target_kind || 'finding';
      void handleFixWithAi({ kind, id: targetId, title: targetTitle }, targetOrigin);
    },
    [handleFixWithAi]
  );

  // Ask AI to explain and suggest fixes for a specific Compiler Pipeline Stage
  const handleAskAiStage = useCallback(
    async (stage: PipelineStageInfo) => {
      if (!activeDoc) return;
      setAssistantOpen(true);
      setActiveAssistantFinding({
        title: `Stage: ${stage.name} (${stage.status.toUpperCase()})`,
        line: cursorPos.line,
        col: cursorPos.col,
        id: stage.id,
      });

      const promptText = `Explain the ${stage.name} (${stage.agentName}) compiler stage ${stage.status.toUpperCase()} in ${activeDoc.name} (${activeDoc.language}) and propose a concrete code fix.\n\nStage Output Summary:\n${stage.outputSummary || 'Stage concluded.'}${stage.errorReason ? `\nError Details: ${stage.errorReason}` : ''}${stage.skipReason ? `\nSkip Reason: ${stage.skipReason}` : ''}`;

      await handleSendMessage(promptText);
    },
    [activeDoc, cursorPos, handleSendMessage]
  );

  // Accept and apply proposed diff
  const handleAcceptDiff = useCallback(
    async (proposal?: PatchProposal | EnrichedPatchProposal) => {
      if (!activeDoc || !proposal) return;

      // 1. Verify that source version is still current and target text matches original expected text
      const validation = validatePatchProposal(activeDoc.source, activeDoc.sourceVersion, proposal);
      if (!validation.valid) {
        showToast(validation.reason || 'Patch validation failed.', 'error');
        updateFileChatMessages((prev) => [
          ...prev,
          {
            id: `msg-${Date.now()}`,
            sender: 'assistant',
            text: `❌ **Patch Application Rejected**: ${validation.reason}\n\n*The file has changed since this patch was generated. Please request a fresh fix based on current source.*`,
            timestamp: Date.now(),
          },
        ]);
        return;
      }

      // 2. Apply patch to actual editor document
      const applyResult = applyPatchToSource(activeDoc.source, proposal);
      if (!applyResult.success || applyResult.newSource === undefined) {
        showToast(`Failed to apply patch: ${applyResult.error || 'Unknown error'}`, 'error');
        return;
      }

      const newSource = applyResult.newSource;
      const newVersion = activeDoc.sourceVersion + 1;

      // 3. Update the document in state (single authoritative editor document)
      dispatch({
        type: 'document/edit',
        id: activeDoc.id,
        source: newSource,
      });

      // 4. Invalidate pipeline stages (Mark dependent analysis results as outdated)
      // Never display an old Passed result as the status of a newly edited source file
      setPipelineStages((prev) =>
        prev.map((s) => ({
          ...s,
          status: 'not_run',
          elapsedMs: 0,
          outputSummary: `Source was modified by patch (now v${newVersion}). Reanalysis required.`,
          errorReason: undefined,
          steps: [],
        }))
      );

      // 5. Note: User must save through explicit save workflow (Ctrl+S or Save file button)
      showToast(`Patch applied to ${activeDoc.name} in editor (v${newVersion}). Unsaved changes pending.`, 'success');

      // 6. Offer reanalysis in Assistant conversation
      updateFileChatMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now()}`,
          sender: 'assistant',
          text: `✅ **Patch Applied Successfully** to \`${activeDoc.name}\` (now v${newVersion}).\n\n- **Target**: Ln ${proposal.edits[0]?.range.start_line}:${proposal.edits[0]?.range.start_col}\n- **Document State**: Updated in editor buffer (dirty / unsaved changes pending).\n- **Analysis**: Dependent compiler analysis results marked outdated.\n\nWould you like to reanalyze the updated source now?`,
          timestamp: Date.now(),
        },
      ]);
    },
    [activeDoc, dispatch, showToast, updateFileChatMessages]
  );

  // Reject proposed diff: Discard the proposed patch without changing source
  const handleRejectDiff = useCallback(
    (proposal?: PatchProposal | EnrichedPatchProposal) => {
      const enriched = proposal as Partial<EnrichedPatchProposal> | undefined;
      const targetDesc = enriched?.finding?.title || proposal?.origin || 'identified issue';
      showToast('Patch proposal rejected.', 'info');
      updateFileChatMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now()}`,
          sender: 'assistant',
          text: `🚫 **Patch Rejected**: Discarded proposed fix for ${targetDesc} without modifying editor source. Document remains at v${activeDoc?.sourceVersion ?? 1}.`,
          timestamp: Date.now(),
        },
      ]);
    },
    [activeDoc?.sourceVersion, showToast, updateFileChatMessages]
  );

  // Improve proposed diff: Return to the assistant with proposal context
  const handleImproveDiff = useCallback(
    (proposal?: PatchProposal | EnrichedPatchProposal) => {
      const enriched = proposal as Partial<EnrichedPatchProposal> | undefined;
      const findingTitle = enriched?.finding?.title || 'the identified issue';
      const risks = proposal?.risks?.length ? ` Address risks: ${proposal.risks.join(', ')}.` : '';
      const prompt = `Please refine the proposed fix for ${findingTitle}.${risks} Provide a safer, more robust implementation with proper bounds checking.`;
      void handleSendMessage(prompt);
    },
    [handleSendMessage]
  );

  const handleApplyFixDirect = useCallback(() => {
    if (mappedSecurityFindings.length > 0) {
      const f = mappedSecurityFindings[0];
      void handleFixWithAi({
        kind: 'finding',
        id: f.id,
        title: f.title,
      });
    } else {
      showToast('No active security findings to remediate.', 'info');
    }
  }, [handleFixWithAi, mappedSecurityFindings, showToast]);

  // Real Multi-Agent Pipeline Swarm Runner
  const handleRunAllAgents = useCallback(async () => {
    if (!activeDoc) return;
    setIsRunningAllAgents(true);
    showToast('Executing 7-stage compiler agent pipeline...', 'info');

    // Set all stages to queued / running
    setPipelineStages((prev) =>
      prev.map((s, idx) => ({
        ...s,
        status: idx === 0 ? 'running' : 'queued',
      }))
    );

    try {
      const abort = new AbortController();
      const res = await apiClient.analyzeV2(
        {
          source: activeDoc.source,
          language: activeDoc.language,
          filename: activeDoc.name,
          api_version: 2,
          source_version: activeDoc.sourceVersion,
          options: {
            include_tokens: true,
            stages: ['lexical', 'syntax', 'semantic', 'security'],
            agent: 'rules',
          },
        },
        abort.signal
      );

      // Update state store with complete result
      dispatch({
        type: 'analysis/success',
        id: activeDoc.id,
        result: res,
        version: activeDoc.sourceVersion,
      });

      const trace = res.trace || [];
      const hasSecurityIssues = (res.security_findings?.length ?? 0) > 0;
      const hasLexicalIssues =
        (res.tokens?.filter((t) => t.lexical_status === 'invalid').length ?? 0) > 0;
      const hasSyntaxIssues = (res.syntax_diagnostics?.length ?? 0) > 0;
      const hasSemanticIssues =
        (res.semantic_diagnostics?.length ?? 0) > 0 ||
        res.semantic_status?.status === 'issues';

      setPipelineStages((prev) =>
        prev.map((stage) => {
          const stageSteps = trace.filter(
            (t) =>
              t.agent.toLowerCase() === stage.agentName.toLowerCase() ||
              t.stage.toLowerCase() === stage.id.toLowerCase()
          );

          const totalMs = stageSteps.reduce((acc, st) => acc + (st.ms || 0), 0);
          let lastObservation =
            stageSteps.length > 0
              ? stageSteps[stageSteps.length - 1].observation_summary ||
                stageSteps[stageSteps.length - 1].reason
              : '';

          const anyRejection = stageSteps.find((s) => !s.accepted);

          let status: StageStatus = 'passed';
          let skipReason: string | null = null;
          let errorReason: string | null = anyRejection?.rejection_reason || null;

          if (stage.id === 'lexer') {
            status = hasLexicalIssues ? 'warning' : 'passed';
          } else if (stage.id === 'parser') {
            status = hasSyntaxIssues ? 'warning' : 'passed';
          } else if (stage.id === 'semantic') {
            status = hasSemanticIssues ? 'warning' : 'passed';
            if (!hasSemanticIssues) {
              lastObservation =
                res.semantic_status?.reason ||
                'Semantic typing & symbol resolution completed; no issues found.';
            }
          } else if (stage.id === 'triage') {
            if (!hasSecurityIssues && stageSteps.length === 0) {
              status = 'skipped';
              skipReason = 'No candidate findings from earlier stages to triage.';
            } else {
              status = hasSecurityIssues ? 'warning' : 'passed';
            }
          } else if (stage.id === 'fix') {
            if (!hasSecurityIssues && stageSteps.length === 0) {
              status = 'skipped';
              skipReason = 'No findings require remediation patches.';
            } else {
              status = 'passed';
            }
          } else if (stage.id === 'verifier') {
            if (!hasSecurityIssues && stageSteps.length === 0) {
              status = 'skipped';
              skipReason = 'No fix candidates to verify.';
            } else {
              status = 'passed';
            }
          } else if (stage.id === 'explain') {
            if (!hasSecurityIssues && stageSteps.length === 0) {
              status = 'skipped';
              skipReason = 'No findings to explain.';
            } else {
              status = 'passed';
            }
          }

          if (anyRejection) {
            status = 'failed';
          }

          return {
            ...stage,
            status,
            elapsedMs: totalMs,
            outputSummary:
              lastObservation ||
              (status === 'skipped'
                ? skipReason || 'Skipped'
                : `Executed ${stageSteps.length} step(s)`),
            skipReason,
            errorReason,
            steps: stageSteps.map((st) => ({
              action: st.action,
              reason: st.reason || '',
              observation: st.observation_summary || '',
              ms: st.ms || 0,
              accepted: st.accepted ?? true,
              rejectionReason: st.rejection_reason || undefined,
            })),
          };
        })
      );

      setActiveBottomTab('view-pipeline-tab');
      showToast(
        `Agent pipeline completed in ${res.agent_meta?.elapsed_ms?.toFixed(1) || '0'}ms!`,
        hasSecurityIssues ? 'warning' : 'success'
      );
    } catch (err: any) {
      showToast(`Agent pipeline failed: ${err?.message || 'Error'}`, 'error');
      setPipelineStages((prev) =>
        prev.map((s) =>
          s.status === 'running' || s.status === 'queued'
            ? { ...s, status: 'failed', errorReason: err?.message || 'Execution error' }
            : s
        )
      );
    } finally {
      setIsRunningAllAgents(false);
    }
  }, [activeDoc, showToast]);

  // Sub-routine runner (executes real backend stages)
  const handleSubRoutine = useCallback(
    async (routine: string) => {
      if (!activeDoc) return;
      setBottomCollapsed(false);
      showToast(`Executing ${routine}...`, 'info');

      if (routine === 'Syntax Verification') {
        try {
          const abort = new AbortController();
          const res = await apiClient.analyzeStageV2(
            'syntax',
            {
              source: activeDoc.source,
              language: activeDoc.language,
              filename: activeDoc.name,
              api_version: 2,
              source_version: activeDoc.sourceVersion,
              options: { include_tokens: true, stages: ['syntax'] },
            },
            abort.signal
          );
          setPipelineStages((prev) =>
            prev.map((s) =>
              s.id === 'parser'
                ? {
                    ...s,
                    status: (res.diagnostics?.length ?? 0) > 0 ? 'warning' : 'passed',
                    outputSummary: `Structural AST parsed with ${res.diagnostics?.length ?? 0} syntax diagnostic(s).`,
                  }
                : s
            )
          );
          setActiveBottomTab('view-diagnostics');
          showToast(
            `Syntax verification complete: ${res.diagnostics?.length ?? 0} errors found.`,
            res.diagnostics?.length ? 'warning' : 'success'
          );
        } catch (err: any) {
          showToast(`Syntax verification failed: ${err?.message || 'Error'}`, 'error');
        }
      } else if (routine === 'Semantic Typing Check') {
        try {
          const abort = new AbortController();
          const res = await apiClient.analyzeV2(
            {
              source: activeDoc.source,
              language: activeDoc.language,
              filename: activeDoc.name,
              api_version: 2,
              source_version: activeDoc.sourceVersion,
              options: { include_tokens: true, stages: ['lexical', 'syntax', 'security'] },
            },
            abort.signal
          );
          setPipelineStages((prev) =>
            prev.map((s) =>
              s.id === 'semantic'
                ? {
                    ...s,
                    status: (res.semantic_diagnostics?.length ?? 0) > 0 ? 'warning' : 'passed',
                    outputSummary: `Semantic typing check complete (${res.semantic_diagnostics?.length ?? 0} diagnostics).`,
                  }
                : s
            )
          );
          setActiveBottomTab('view-diagnostics');
          showToast('Semantic typing check completed.', 'success');
        } catch (err: any) {
          showToast(`Semantic check failed: ${err?.message || 'Error'}`, 'error');
        }
      } else if (routine === 'Taint Analysis') {
        try {
          const abort = new AbortController();
          const res = await apiClient.analyzeV2(
            {
              source: activeDoc.source,
              language: activeDoc.language,
              filename: activeDoc.name,
              api_version: 2,
              source_version: activeDoc.sourceVersion,
              options: { include_tokens: true, stages: ['security'] },
            },
            abort.signal
          );
          const paths = res.taint_paths || [];
          setPipelineStages((prev) =>
            prev.map((s) =>
              s.id === 'semantic'
                ? {
                    ...s,
                    status: paths.length > 0 ? 'warning' : 'passed',
                    outputSummary: `Taint analysis completed: ${paths.length} data-flow propagation paths.`,
                  }
                : s
            )
          );
          setActiveBottomTab('view-pipeline-tab');
          showToast(
            `Taint analysis complete: ${paths.length} data-flow path(s) mapped.`,
            paths.length > 0 ? 'warning' : 'success'
          );
        } catch (err: any) {
          showToast(`Taint analysis failed: ${err?.message || 'Error'}`, 'error');
        }
      } else if (routine === 'Full Security Audit') {
        setActiveBottomTab('view-security-tab');
        void handleRunAllAgents();
      }
    },
    [activeDoc, handleRunAllAgents, showToast]
  );

  // Rerun Stage with prerequisites check and downstream dependency invalidation
  const handleRerunStage = useCallback(
    async (stageId: string) => {
      const STAGE_ORDER = ['lexer', 'parser', 'semantic', 'triage', 'fix', 'verifier', 'explain'];
      const stageIdx = STAGE_ORDER.indexOf(stageId);
      if (stageIdx > 0) {
        const prereqId = STAGE_ORDER[stageIdx - 1];
        const prereqStage = pipelineStages.find((s) => s.id === prereqId);
        if (
          !prereqStage ||
          (prereqStage.status !== 'passed' && prereqStage.status !== 'warning')
        ) {
          showToast(
            `Cannot rerun ${stageId}: Prerequisite stage '${prereqId}' has not passed yet.`,
            'warning'
          );
          return;
        }
      }

      // Invalidate downstream stages
      setPipelineStages((prev) =>
        prev.map((s, idx) => {
          if (idx > stageIdx) {
            return {
              ...s,
              status: 'not_run',
              elapsedMs: 0,
              outputSummary: `Prerequisite stage '${stageId}' was rerun; stage invalidated.`,
              steps: [],
            };
          }
          if (s.id === stageId) {
            return { ...s, status: 'running' };
          }
          return s;
        })
      );

      if (stageId === 'lexer') {
        await triggerAnalyze(activeDoc || undefined);
        setPipelineStages((prev) =>
          prev.map((s) => (s.id === 'lexer' ? { ...s, status: 'passed' } : s))
        );
      } else if (stageId === 'parser') {
        await handleSubRoutine('Syntax Verification');
      } else if (stageId === 'semantic') {
        await handleSubRoutine('Semantic Typing Check');
      } else {
        await handleRunAllAgents();
      }
    },
    [activeDoc, handleRunAllAgents, handleSubRoutine, pipelineStages, showToast, triggerAnalyze]
  );

  // Build with AI execution
  const handleExecuteBuildAi = useCallback(
    async (lang: SupportedLanguage, requirement: string): Promise<AIGenerateResponse | null> => {
      try {
        const res = await apiClient.generateAI({
          session_id: sessionIdRef.current,
          language: lang,
          requirements: [requirement],
          remote_consent: remoteConsented,
        });
        return res;
      } catch (err: any) {
        showToast(`Build with AI failed: ${err?.message || 'Error'}`, 'error');
        return null;
      }
    },
    [remoteConsented, showToast]
  );

  const handleCreateFileFromCandidate = useCallback(
    async (fileName: string, content: string) => {
      const newPath = fileName.startsWith('src/') ? fileName : `src/${fileName}`;
      await apiClient.createWorkspaceFile(newPath, content);
      await fetchWorkspaceTree();
      await handleOpenFile(newPath);
    },
    [fetchWorkspaceTree, handleOpenFile]
  );

  const handleRefineCandidateInAssistant = useCallback(
    (candidateCode: string, requirement: string) => {
      setAssistantOpen(true);
      void handleSendMessage(
        `I generated candidate code for requirement "${requirement}":\n\n\`\`\`${activeDoc?.language || 'cpp'}\n${candidateCode}\n\`\`\`\n\nPlease review this code, optimize its performance, and eliminate any remaining security vulnerabilities.`
      );
    },
    [activeDoc?.language, handleSendMessage]
  );

  // Export CSV
  const handleExportCSV = useCallback(() => {
    if (mappedTokens.length === 0) {
      showToast('No analyzed tokens available to export. Run lexical analysis first.', 'warning');
      return;
    }
    const csvHeader =
      'Index,Line,Column,EndLine,EndColumn,StartOffset,EndOffset,Lexeme,Type,Category,Status,Description,RuleId\n';
    const csvRows = mappedTokens
      .map(
        (t) =>
          `${t.id},${t.line},${t.col},${t.endLine || t.line},${t.endCol || t.col},${t.startOffset ?? ''},${t.endOffset ?? ''},"${(t.lexeme || '').replace(/"/g, '""')}","${t.type}","${t.category || ''}","${t.status}","${(t.desc || '').replace(/"/g, '""')}","${t.ruleId || ''}"`
      )
      .join('\n');
    const blob = new Blob([csvHeader + csvRows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `tokens_${activeDoc?.name?.replace(/[\/\\]/g, '_') || 'source'}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    showToast(`Exported ${mappedTokens.length} tokens to CSV`, 'success');
  }, [mappedTokens, activeDoc, showToast]);

  // Export JSON
  const handleExportJSON = useCallback(() => {
    if (!currentAnalysis) {
      showToast('No active analysis results to export. Run lexical analysis first.', 'warning');
      return;
    }
    const payload = {
      analysis_id: currentAnalysis.analysis_id,
      source_hash: currentAnalysis.source_hash,
      source_version: activeDoc?.sourceVersion ?? currentAnalysis.source_version,
      document: activeDoc?.name,
      language: activeDoc?.language,
      tokens: mappedTokens,
      diagnostics: mappedDiagnostics,
      securityFindings: mappedSecurityFindings,
      lexical_summary: currentAnalysis.lexical_summary,
      lexical_status: currentAnalysis.lexical_status,
      exported_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json;charset=utf-8;',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analysis_${activeDoc?.name?.replace(/[\/\\]/g, '_') || 'source'}.json`;
    link.click();
    URL.revokeObjectURL(url);
    showToast('Tokens and analysis exported as JSON successfully', 'success');
  }, [currentAnalysis, mappedTokens, mappedDiagnostics, mappedSecurityFindings, activeDoc, showToast]);

  // Preferences state updater and persistence
  const updatePreferences = useCallback((newPrefs: Partial<UserPreferences>) => {
    const updated = writePreferences(newPrefs);
    setPrefs(updated);
    if (newPrefs.fontSize !== undefined) setFontSize(newPrefs.fontSize);
    if (newPrefs.wordWrap !== undefined) setWordWrap(newPrefs.wordWrap);
    if (newPrefs.minimap !== undefined) setMinimap(newPrefs.minimap);
    if (newPrefs.tabSize !== undefined) setTabSize(newPrefs.tabSize);
    if (newPrefs.highlightUnicode !== undefined) setHighlightUnicode(newPrefs.highlightUnicode);
    if (newPrefs.autoAnalyze !== undefined) setAutoAnalyze(newPrefs.autoAnalyze);
    if (newPrefs.sidebarCollapsed !== undefined) setSidebarCollapsed(newPrefs.sidebarCollapsed);
    if (newPrefs.bottomCollapsed !== undefined) setBottomCollapsed(newPrefs.bottomCollapsed);
    if (newPrefs.bottomMaximized !== undefined) setIsMaximized(newPrefs.bottomMaximized);
    if (newPrefs.assistantCollapsed !== undefined) setAssistantOpen(!newPrefs.assistantCollapsed);
    if (newPrefs.panelSizes?.sidebarWidth !== undefined) setSidebarWidth(newPrefs.panelSizes.sidebarWidth);
    if (newPrefs.panelSizes?.bottomHeight !== undefined) setBottomHeight(newPrefs.panelSizes.bottomHeight);
    if (newPrefs.panelSizes?.assistantWidth !== undefined) setAssistantWidth(newPrefs.panelSizes.assistantWidth);
  }, []);

  // Panel Resizing Handlers
  const handleSidebarResizeStart = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    const handleMove = (moveEv: PointerEvent) => {
      const maxSidebar = Math.min(480, Math.max(160, window.innerWidth - (assistantOpen ? assistantWidth + 380 : 380)));
      const newWidth = Math.min(maxSidebar, Math.max(160, moveEv.clientX - 50));
      setSidebarWidth(newWidth);
      editorRef.current?.layout();
    };
    const handleUp = () => {
      window.removeEventListener('pointermove', handleMove);
      window.removeEventListener('pointerup', handleUp);
      setSidebarWidth((w) => {
        writePreferences({ panelSizes: { ...readPreferences().panelSizes, sidebarWidth: w } });
        return w;
      });
      editorRef.current?.layout();
    };
    window.addEventListener('pointermove', handleMove);
    window.addEventListener('pointerup', handleUp);
  }, [assistantOpen, assistantWidth]);

  const handleAssistantResizeStart = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    const handleMove = (moveEv: PointerEvent) => {
      const maxAssistant = Math.min(700, Math.max(280, window.innerWidth - (!sidebarCollapsed ? sidebarWidth + 380 : 380)));
      const newWidth = Math.min(maxAssistant, Math.max(280, window.innerWidth - moveEv.clientX));
      setAssistantWidth(newWidth);
      editorRef.current?.layout();
    };
    const handleUp = () => {
      window.removeEventListener('pointermove', handleMove);
      window.removeEventListener('pointerup', handleUp);
      setAssistantWidth((w) => {
        writePreferences({ panelSizes: { ...readPreferences().panelSizes, assistantWidth: w } });
        return w;
      });
      editorRef.current?.layout();
    };
    window.addEventListener('pointermove', handleMove);
    window.addEventListener('pointerup', handleUp);
  }, [sidebarCollapsed, sidebarWidth]);

  const handleBottomResizeStart = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    const handleMove = (moveEv: PointerEvent) => {
      const maxBottom = Math.min(650, Math.max(140, window.innerHeight - 180));
      const newHeight = Math.min(maxBottom, Math.max(140, window.innerHeight - moveEv.clientY - 28));
      setBottomHeight(newHeight);
      editorRef.current?.layout();
    };
    const handleUp = () => {
      window.removeEventListener('pointermove', handleMove);
      window.removeEventListener('pointerup', handleUp);
      setBottomHeight((h) => {
        writePreferences({ panelSizes: { ...readPreferences().panelSizes, bottomHeight: h } });
        return h;
      });
      editorRef.current?.layout();
    };
    window.addEventListener('pointermove', handleMove);
    window.addEventListener('pointerup', handleUp);
  }, []);

  // Relayout Monaco on window resize
  useEffect(() => {
    const handleWinResize = () => {
      editorRef.current?.layout();
    };
    window.addEventListener('resize', handleWinResize);
    return () => window.removeEventListener('resize', handleWinResize);
  }, []);

  // Guard against closing tab/browser with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      const hasUnsaved = state.documents.some((d) => d.dirty);
      if (hasUnsaved) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [state.documents]);

  // Export SARIF Security Report
  const handleExportSARIF = useCallback(() => {
    const sarifReport = {
      $schema: 'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json',
      version: '2.1.0',
      runs: [
        {
          tool: {
            driver: {
              name: 'SecureLex Core Analyzer',
              version: '2.0.4',
              informationUri: 'https://github.com/securelex/securelex-ide',
              rules: mappedSecurityFindings.map((f) => ({
                id: f.ruleId || f.id,
                name: f.title,
                shortDescription: { text: f.title },
                fullDescription: { text: f.description },
                defaultConfiguration: {
                  level:
                    f.severity?.toLowerCase() === 'critical' || f.severity?.toLowerCase() === 'high'
                      ? 'error'
                      : 'warning',
                },
              })),
            },
          },
          results: mappedSecurityFindings.map((f) => ({
            ruleId: f.ruleId || f.id,
            level:
              f.severity?.toLowerCase() === 'critical' || f.severity?.toLowerCase() === 'high'
                ? 'error'
                : 'warning',
            message: { text: f.description || f.title },
            locations: [
              {
                physicalLocation: {
                  artifactLocation: { uri: f.file || activeDoc?.name || 'source' },
                  region: {
                    startLine: f.line || 1,
                    startColumn: f.col || 1,
                    endLine: f.range?.end_line || f.line || 1,
                    endColumn: f.range?.end_col || (f.col || 1) + 1,
                  },
                },
              },
            ],
          })),
        },
      ],
    };

    const blob = new Blob([JSON.stringify(sarifReport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sarif_${activeDoc?.name.replace(/[/\\?%*:|"<>]/g, '_') || 'report'}.sarif`;
    link.click();
    URL.revokeObjectURL(url);
    showToast('SARIF security report exported successfully', 'success');
  }, [activeDoc?.name, mappedSecurityFindings, showToast]);

  // Export Markdown Report
  const handleExportMarkdown = useCallback(async () => {
    if (!activeDoc) {
      showToast('No active document available to export.', 'warning');
      return;
    }
    try {
      showToast('Generating Markdown analysis report...', 'info');
      const blob = await apiClient.exportReport({
        kind: 'analysis',
        format: 'markdown',
        source: activeDoc.source,
        language: activeDoc.language,
        filename: activeDoc.name,
        source_version: activeDoc.sourceVersion,
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `securelex-report_${activeDoc.name.replace(/[/\\?%*:|"<>]/g, '_')}.md`;
      link.click();
      URL.revokeObjectURL(url);
      showToast('Exported Markdown analysis report successfully', 'success');
    } catch (err: any) {
      showToast(err?.message || 'Failed to export Markdown report', 'error');
    }
  }, [activeDoc, showToast]);

  // Export HTML Report
  const handleExportHTML = useCallback(async () => {
    if (!activeDoc) {
      showToast('No active document available to export.', 'warning');
      return;
    }
    try {
      showToast('Generating HTML analysis report...', 'info');
      const blob = await apiClient.exportReport({
        kind: 'analysis',
        format: 'html',
        source: activeDoc.source,
        language: activeDoc.language,
        filename: activeDoc.name,
        source_version: activeDoc.sourceVersion,
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `securelex-report_${activeDoc.name.replace(/[/\\?%*:|"<>]/g, '_')}.html`;
      link.click();
      URL.revokeObjectURL(url);
      showToast('Exported HTML analysis report successfully', 'success');
    } catch (err: any) {
      showToast(err?.message || 'Failed to export HTML report', 'error');
    }
  }, [activeDoc, showToast]);

  // Keyboard Shortcuts Hook
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const mod = isMac ? e.metaKey : e.ctrlKey;

      // Ctrl+S: Save File
      if (mod && e.key.toLowerCase() === 's' && !e.shiftKey) {
        e.preventDefault();
        void handleSaveFile();
        return;
      }

      // Ctrl+Enter or F5: Analyze
      if ((mod && e.key === 'Enter') || e.key === 'F5') {
        e.preventDefault();
        void triggerAnalyze();
        return;
      }

      // Ctrl+Shift+P or F1: Command Palette
      if ((mod && e.shiftKey && e.key.toLowerCase() === 'p') || e.key === 'F1') {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
        return;
      }

      // Ctrl+Shift+F: Search & Replace
      if (mod && e.shiftKey && e.key.toLowerCase() === 'f') {
        e.preventDefault();
        setActivePane('pane-search');
        setSidebarCollapsed(false);
        return;
      }

      // Ctrl+B: Toggle Explorer sidebar
      if (mod && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        setSidebarCollapsed((prev) => {
          const next = !prev;
          writePreferences({ sidebarCollapsed: next });
          setTimeout(() => editorRef.current?.layout(), 50);
          return next;
        });
        return;
      }

      // Ctrl+J: Toggle Assistant
      if (mod && e.key.toLowerCase() === 'j') {
        e.preventDefault();
        setAssistantOpen((prev) => {
          const next = !prev;
          writePreferences({ assistantCollapsed: !next });
          setTimeout(() => editorRef.current?.layout(), 50);
          return next;
        });
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSaveFile, triggerAnalyze]);

  // Command Palette Items
  const commandList: CommandItem[] = useMemo(
    () => [
      {
        id: 'cmd-analyze',
        title: 'Run Lexical Analysis (Active File)',
        category: 'Compiler',
        shortcut: 'Ctrl+Enter / F5',
        icon: 'play_arrow',
        action: () => void triggerAnalyze(),
      },
      {
        id: 'cmd-run-agents',
        title: 'Run All 7 Compiler Agents Pipeline Swarm',
        category: 'Swarm',
        shortcut: 'Alt+R',
        icon: 'hub',
        action: () => void handleRunAllAgents(),
      },
      {
        id: 'cmd-save-file',
        title: 'Save Active File to Workspace',
        category: 'File',
        shortcut: 'Ctrl+S',
        icon: 'save',
        action: () => void handleSaveFile(),
      },
      {
        id: 'cmd-search-replace',
        title: 'Search & Replace in Project Workspace',
        category: 'Search',
        shortcut: 'Ctrl+Shift+F',
        icon: 'search',
        action: () => {
          setActivePane('pane-search');
          setSidebarCollapsed(false);
        },
      },
      {
        id: 'cmd-git-status',
        title: 'Open Source Control (Git)',
        category: 'Git',
        shortcut: 'Ctrl+Shift+G',
        icon: 'source_environment',
        action: () => {
          setActivePane('pane-git');
          setSidebarCollapsed(false);
        },
      },
      {
        id: 'cmd-toggle-sidebar',
        title: 'Toggle Primary Sidebar Visibility',
        category: 'View',
        shortcut: 'Ctrl+B',
        icon: 'view_sidebar',
        action: () => {
          setSidebarCollapsed((prev) => {
            const next = !prev;
            updatePreferences({ sidebarCollapsed: next });
            setTimeout(() => editorRef.current?.layout(), 50);
            return next;
          });
        },
      },
      {
        id: 'cmd-toggle-assistant',
        title: 'Toggle AI Assistant Panel Visibility',
        category: 'View',
        shortcut: 'Ctrl+J',
        icon: 'smart_toy',
        action: () => {
          setAssistantOpen((prev) => {
            const next = !prev;
            updatePreferences({ assistantCollapsed: !next });
            setTimeout(() => editorRef.current?.layout(), 50);
            return next;
          });
        },
      },
      {
        id: 'cmd-toggle-maximize-bottom',
        title: 'Toggle Maximize Analysis Results Panel',
        category: 'View',
        shortcut: 'Ctrl+M',
        icon: 'expand',
        action: () => setIsMaximized((prev) => !prev),
      },
      {
        id: 'cmd-toggle-word-wrap',
        title: 'Toggle Editor Word Wrap',
        category: 'Editor',
        shortcut: 'Alt+Z',
        icon: 'wrap_text',
        action: () => {
          const nw = wordWrap === 'on' ? 'off' : 'on';
          updatePreferences({ wordWrap: nw });
          showToast(`Word wrap: ${nw.toUpperCase()}`);
        },
      },
      {
        id: 'cmd-toggle-theme',
        title: `Switch Theme (Currently ${resolvedTheme})`,
        category: 'Preferences',
        icon: 'contrast',
        action: () => toggleTheme(),
      },
      {
        id: 'cmd-export-csv',
        title: 'Export Tokens to CSV File',
        category: 'Export',
        icon: 'file_download',
        action: handleExportCSV,
      },
      {
        id: 'cmd-export-json',
        title: 'Export Full Analysis to JSON File',
        category: 'Export',
        icon: 'data_object',
        action: handleExportJSON,
      },
      {
        id: 'cmd-export-sarif',
        title: 'Export SARIF Security Report (v2.1.0)',
        category: 'Export',
        icon: 'security',
        action: handleExportSARIF,
      },
      {
        id: 'cmd-export-markdown',
        title: 'Export Full Report to Markdown File',
        category: 'Export',
        icon: 'description',
        action: handleExportMarkdown,
      },
      {
        id: 'cmd-export-html',
        title: 'Export Full Interactive HTML Report',
        category: 'Export',
        icon: 'html',
        action: handleExportHTML,
      },
      {
        id: 'cmd-build-with-ai',
        title: 'Build with AI Generator...',
        category: 'AI',
        icon: 'auto_awesome',
        action: () => setBuildAiModalOpen(true),
      },
      {
        id: 'cmd-open-settings',
        title: 'Open SecureLex IDE Settings',
        category: 'Preferences',
        icon: 'settings',
        action: () => {
          setActivePane('pane-settings');
          setSidebarCollapsed(false);
        },
      },
    ],
    [
      triggerAnalyze,
      handleRunAllAgents,
      handleSaveFile,
      updatePreferences,
      wordWrap,
      resolvedTheme,
      toggleTheme,
      handleExportCSV,
      handleExportJSON,
      handleExportSARIF,
      handleExportMarkdown,
      handleExportHTML,
      showToast,
    ]
  );

  // Toggle Engine (Local vs Groq Cloud)
  const handleToggleEngine = useCallback(() => {
    if (engineMode === 'local') {
      setEngineMode('groq');
      showToast('Switched to Groq Cloud LLM engine (Llama 3.3 70B)');
    } else {
      setEngineMode('local');
      showToast('Switched to Local Deterministic Engine');
    }
  }, [engineMode, showToast]);

  return (
    <div
      role="region"
      aria-label="Workbench"
      className="bg-surface font-sans text-text-primary text-[12px] antialiased h-screen w-screen overflow-hidden flex flex-col select-none transition-colors duration-150"
      style={{ fontSize: `${fontSize}px` }}
    >
      {/* ================= TOP HEADER (48px) ================= */}
      <Header
        version={capabilities?.version || '2.4.2'}
        engineMode={engineMode}
        onToggleEngine={handleToggleEngine}
        securityAlertCount={mappedSecurityFindings.length}
        onOpenSecurity={() => {
          setActivePane('pane-security');
          setSidebarCollapsed(false);
          setActiveBottomTab('view-security-tab');
          setBottomCollapsed(false);
        }}
        resolvedTheme={resolvedTheme}
        onToggleTheme={() => {
          toggleTheme();
          showToast(resolvedTheme === 'dark' ? 'Refined Titanium Light Theme enabled' : 'Dark Theme enabled');
        }}
        assistantOpen={assistantOpen}
        onToggleAssistant={() => {
          setAssistantOpen(!assistantOpen);
          updatePreferences({ assistantCollapsed: assistantOpen });
          setTimeout(() => editorRef.current?.layout(), 50);
        }}
        onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        onShowToast={showToast}
      />

      {/* ================= MAIN MIDDLE CONTAINER ================= */}
      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        {/* 1. LEFT ACTIVITY RAIL (50px) */}
        <ActivityBar
          activePane={activePane}
          onSelectPane={(pane) => {
            if (activePane === pane && !sidebarCollapsed) {
              setSidebarCollapsed(true);
              updatePreferences({ sidebarCollapsed: true });
            } else {
              setActivePane(pane);
              setSidebarCollapsed(false);
              updatePreferences({ sidebarCollapsed: false });
              if (pane === 'pane-security') {
                setActiveBottomTab('view-security-tab');
                setBottomCollapsed(false);
              } else if (pane === 'pane-pipeline') {
                setActiveBottomTab('view-pipeline-tab');
                setBottomCollapsed(false);
              }
            }
            setTimeout(() => editorRef.current?.layout(), 50);
          }}
          securityCount={mappedSecurityFindings.length}
          onToggleAssistant={() => {
            setAssistantOpen(!assistantOpen);
            updatePreferences({ assistantCollapsed: assistantOpen });
            setTimeout(() => editorRef.current?.layout(), 50);
          }}
          assistantOpen={assistantOpen}
        />

        {/* 2. SECONDARY SIDEBAR (Collapsible & Resizable) */}
        {!sidebarCollapsed && (
          <ExplorerSidebar
            activePane={activePane}
            width={sidebarWidth}
            onResizeStart={handleSidebarResizeStart}
            tree={workspaceTree}
            documents={state.documents}
            activeDocId={activeDoc?.id ?? null}
            onSelectDoc={(id) => dispatch({ type: 'document/activate', id })}
            onOpenFile={handleOpenFile}
            onCreateFile={handleCreateFile}
            onCreateFolder={handleCreateFolder}
            onRenameFile={handleRenameFile}
            onDeleteFile={handleDeleteFile}
            onRefreshTree={fetchWorkspaceTree}
            getFileAnalysisInfo={getFileAnalysisInfo}
            onSearchFocusLine={(line, col, _len, file) =>
              handleJumpToCode(line, col || 1, undefined, undefined, file)
            }
            onApplyFix={handleApplyFixDirect}
            onRunSwarm={handleRunAllAgents}
            fontSize={fontSize}
            onChangeFontSize={(size) => {
              updatePreferences({ fontSize: size });
              showToast(`Editor font size set to ${size}px`);
            }}
            themeMode={themeMode}
            onSelectThemeMode={(mode) => {
              setThemeMode(mode);
              updatePreferences({ theme: mode });
            }}
            wordWrap={wordWrap}
            onToggleWordWrap={() => {
              const nw = wordWrap === 'on' ? 'off' : 'on';
              updatePreferences({ wordWrap: nw });
              showToast(`Word wrap: ${nw.toUpperCase()}`);
            }}
            minimap={minimap}
            onToggleMinimap={() => {
              updatePreferences({ minimap: !minimap });
              showToast(`Minimap: ${!minimap ? 'ON' : 'OFF'}`);
            }}
            tabSize={tabSize}
            onChangeTabSize={(size) => {
              updatePreferences({ tabSize: size });
              showToast(`Tab size: ${size} spaces`);
            }}
            highlightUnicode={highlightUnicode}
            onToggleHighlightUnicode={(enabled) => {
              updatePreferences({ highlightUnicode: enabled });
              showToast(`Highlight Unicode Traps: ${enabled ? 'ON' : 'OFF'}`);
            }}
            autoAnalyze={autoAnalyze}
            onToggleAutoAnalyze={(enabled) => {
              updatePreferences({ autoAnalyze: enabled });
              showToast('Auto-run preference saved');
            }}
            onResetPanelLayout={() => {
              updatePreferences({
                panelSizes: { sidebarWidth: 220, bottomHeight: 280, assistantWidth: 447 },
                sidebarCollapsed: false,
                bottomCollapsed: false,
                assistantCollapsed: false,
              });
              showToast('Panel layouts reset to default.');
              setTimeout(() => editorRef.current?.layout(), 50);
            }}
            onExportSARIF={handleExportSARIF}
            securityCount={mappedSecurityFindings.length}
            onShowToast={showToast}
          />
        )}

        {/* 3. CENTER WORKSPACE (Editor + Analysis Panel) */}
        <EditorWorkspace
          documents={state.documents}
          activeDoc={activeDoc}
          onSelectDoc={(id) => dispatch({ type: 'document/activate', id })}
          onCloseDoc={(id) => {
            if (state.documents.length <= 1) {
              showToast('Cannot close the only open file.', 'warning');
              return;
            }
            const targetDoc = state.documents.find((d) => d.id === id);
            if (targetDoc?.dirty) {
              const confirmClose = window.confirm(
                `File "${targetDoc.name}" has unsaved modifications.\n\nDo you want to discard unsaved changes and close this file?`
              );
              if (!confirmClose) return;
            }
            dispatch({ type: 'document/remove', id });
          }}
          onSourceChange={(source) => {
            if (activeDoc) {
              dispatch({ type: 'document/edit', id: activeDoc.id, source });
              // Invalidate pipeline stages: never display old Passed result for newly edited source
              setPipelineStages((prev) =>
                prev.map((s) =>
                  s.status !== 'not_run'
                    ? {
                        ...s,
                        status: 'not_run',
                        elapsedMs: 0,
                        outputSummary: 'Source was modified. Reanalysis required.',
                        errorReason: undefined,
                      }
                    : s
                )
              );
            }
          }}
          onSave={handleSaveFile}
          currentLanguage={activeDoc?.language || 'cpp'}
          onSelectLanguage={(lang) => {
            if (activeDoc) {
              dispatch({ type: 'document/language', id: activeDoc.id, language: lang });
              showToast(`Language switched to ${lang}`);
            }
          }}
          isAnalyzing={isAnalyzing}
          onAnalyze={() => {
            setBottomCollapsed(false);
            setActiveBottomTab('view-tokens');
            void triggerAnalyze();
          }}
          onSubRoutine={handleSubRoutine}
          onRunAllAgents={() => {
            setBottomCollapsed(false);
            setActiveBottomTab('view-pipeline-tab');
            void handleRunAllAgents();
          }}
          onOpenBuildWithAi={() => setBuildAiModalOpen(true)}
          onFocusFixInAssistant={() => {
            setAssistantOpen(true);
            showToast('Assistant focused with fix recommendations.');
          }}
          cursorLine={cursorPos.line}
          cursorCol={cursorPos.col}
          onCursorChange={(line, col) => setCursorPos({ line, col })}
          isMaximized={isMaximized}
          resolvedTheme={resolvedTheme}
          fontSize={fontSize}
          wordWrap={wordWrap}
          onToggleWordWrap={() => {
            const nw = wordWrap === 'on' ? 'off' : 'on';
            updatePreferences({ wordWrap: nw });
            showToast(`Word wrap: ${nw.toUpperCase()}`);
          }}
          minimap={minimap}
          tabSize={tabSize}
          bottomHeight={bottomHeight}
          bottomCollapsed={bottomCollapsed}
          onBottomResizeStart={handleBottomResizeStart}
          onShowToast={showToast}
          editorRef={editorRef}
        >
          {/* Bottom Results Panel */}
          <AnalysisPanel
            activeTab={activeBottomTab}
            onSelectTab={setActiveBottomTab}
            tokens={mappedTokens}
            selectedToken={effectiveSelectedToken}
            onSelectToken={setSelectedToken}
            onExplainToken={(t) => {
              const lexemeLabel = t.lexeme && t.lexeme.trim() ? `: '${t.lexeme}'` : '';
              void handleExplainTarget({
                kind: 'token',
                id: String(t.id),
                title: `Token #${t.id} (${t.type}${lexemeLabel})`,
                line: t.line,
                col: t.col,
              });
            }}
            activeSource={activeDoc?.source}
            activeLanguage={activeDoc?.language}
            onFixWithModelToken={(t) => {
              const lexemeLabel = t.lexeme && t.lexeme.trim() ? `: '${t.lexeme}'` : '';
              void handleFixWithAi(
                {
                  kind: 'token',
                  id: String(t.id),
                  title: `Token #${t.id} (${t.type}${lexemeLabel})`,
                },
                'rule'
              );
            }}
            onFixWithAiToken={(t) => {
              const lexemeLabel = t.lexeme && t.lexeme.trim() ? `: '${t.lexeme}'` : '';
              void handleFixWithAi(
                {
                  kind: 'token',
                  id: String(t.id),
                  title: `Token #${t.id} (${t.type}${lexemeLabel})`,
                },
                'ai'
              );
            }}
            onJumpToCode={handleJumpToCode}
            diagnostics={mappedDiagnostics}
            securityFindings={mappedSecurityFindings}
            pipelineStages={pipelineStages}
            selectedStageId={selectedStageId}
            onSelectStage={setSelectedStageId}
            onRerunStage={handleRerunStage}
            isRunningAllAgents={isRunningAllAgents}
            onAskAiStage={handleAskAiStage}
            onExplainDiagnostic={(d) => {
              void handleExplainTarget({
                kind: 'diagnostic',
                id: d.id,
                title: `Diagnostic [${d.code}]: ${d.message}`,
                line: d.line,
                col: d.col,
              });
            }}
            onFixWithModelDiagnostic={(d) => {
              void handleFixWithAi(
                {
                  kind: 'diagnostic',
                  id: d.id,
                  title: `Diagnostic [${d.code}]: ${d.message}`,
                },
                'rule'
              );
            }}
            onFixWithAiDiagnostic={(d) => {
              void handleFixWithAi(
                {
                  kind: 'diagnostic',
                  id: d.id,
                  title: `Diagnostic [${d.code}]: ${d.message}`,
                },
                'ai'
              );
            }}
            onExplainFinding={(f) => {
              void handleExplainTarget({
                kind: 'finding',
                id: f.id,
                title: `Security Finding: ${f.title}`,
                line: f.line,
                col: f.col,
              });
            }}
            onFixWithModelFinding={(f) => {
              void handleFixWithAi(
                {
                  kind: 'finding',
                  id: f.id,
                  title: f.title,
                },
                'rule'
              );
            }}
            onFixWithAiFinding={(f) => {
              void handleFixWithAi(
                {
                  kind: 'finding',
                  id: f.id,
                  title: f.title,
                },
                'ai'
              );
            }}
            onApplyRemediation={() => {
              if (mappedSecurityFindings.length > 0) {
                const f = mappedSecurityFindings[0];
                void handleFixWithAi(
                  {
                    kind: 'finding',
                    id: f.id,
                    title: f.title,
                  },
                  'rule'
                );
              } else {
                showToast('No active security findings to remediate.', 'info');
              }
            }}
            onRunAllAgents={handleRunAllAgents}
            onExportCSV={handleExportCSV}
            onExportJSON={handleExportJSON}
            onExportMarkdown={handleExportMarkdown}
            onExportHTML={handleExportHTML}
            isMaximized={isMaximized}
            onToggleMaximize={() => {
              const nextMax = !isMaximized;
              setIsMaximized(nextMax);
              updatePreferences({ bottomMaximized: nextMax });
              setTimeout(() => editorRef.current?.layout(), 50);
            }}
            onAskFollowUp={(p) => {
              setAssistantOpen(true);
              void handleSendMessage(p);
            }}
            isAnalyzing={isAnalyzing}
            isStale={isStale}
            hasAnalyzed={Boolean(currentAnalysis)}
            onReanalyze={() => void triggerAnalyze()}
            errorMessage={analysisError}
            languageStandard={
              activeDoc?.language.toLowerCase() === 'cpp'
                ? 'ISO/IEC 14882:2020 C++'
                : activeDoc?.language.toLowerCase() === 'python'
                ? 'PEP 538 Python 3'
                : activeDoc?.language.toLowerCase() === 'java'
                ? 'Java SE 17'
                : 'ECMAScript 2024'
            }
          />
        </EditorWorkspace>

        {/* Floating Expand Assistant Button (when collapsed) */}
        {!assistantOpen && (
          <button
            type="button"
            className="absolute bottom-4 right-4 z-40 flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-accent-ai to-primary text-white font-medium text-[12px] rounded-lg shadow-2xl border border-white/20 hover:scale-105 active:scale-95 transition-all"
            id="btnExpandAssistantFloating"
            onClick={() => {
              setAssistantOpen(true);
              updatePreferences({ assistantCollapsed: false });
              setTimeout(() => editorRef.current?.layout(), 50);
            }}
            title="Expand AI Assistant"
          >
            <span className="material-symbols-outlined text-[17px]">smart_toy</span>
            <span>Open Assistant</span>
          </button>
        )}

        {/* 4. RIGHT PERSISTENT ASSISTANT (Collapsible & Resizable) */}
        <AssistantPanel
          isOpen={assistantOpen}
          onClose={() => {
            setAssistantOpen(false);
            updatePreferences({ assistantCollapsed: true });
            setTimeout(() => editorRef.current?.layout(), 50);
          }}
          width={assistantWidth}
          onResizeStart={handleAssistantResizeStart}
          activeFileName={activeDoc?.name || 'main.cpp'}
          sourceVersion={activeDoc?.sourceVersion || 1}
          language={activeDoc?.language || 'cpp'}
          cursorLine={cursorPos.line}
          cursorCol={cursorPos.col}
          providerName={
            providerCapabilities?.model
              ? `Groq Cloud (${providerCapabilities.model})`
              : 'Groq Cloud (openai/gpt-oss-120b)'
          }
          providerConfigured={providerCapabilities?.configured ?? true}
          remoteConsented={remoteConsented}
          onToggleConsent={handleToggleConsent}
          contextStage={
            activeBottomTab === 'view-tokens'
              ? 'Lexical Scanner'
              : activeBottomTab === 'view-diagnostics'
              ? 'AST Syntax Diagnostics'
              : activeBottomTab === 'view-security-tab'
              ? 'Security Analysis'
              : activeBottomTab === 'view-pipeline-tab'
              ? 'Agent Pipeline'
              : 'AI Explain'
          }
          contextFinding={activeAssistantFinding}
          messages={chatMessages}
          onSendMessage={handleSendMessage}
          onNewConversation={handleNewConversation}
          onClearChat={() => {
            setChatMessages([]);
            if (activeDoc) {
              setConversationsByFile((prev) => ({ ...prev, [activeDoc.id]: [] }));
            }
            showToast('Assistant chat cleared');
          }}
          onAcceptDiff={handleAcceptDiff}
          onRejectDiff={handleRejectDiff}
          onImproveDiff={handleImproveDiff}
          onSwitchProposalOrigin={handleSwitchProposalOrigin}
          onReanalyze={async () => {
            await triggerAnalyze();
            await handleRunAllAgents();
          }}
          onInsertCodeSnippet={handleInsertCodeSnippet}
          onShowToast={showToast}
          isSending={isSendingChat}
        />
      </div>

      {/* ================= BOTTOM STATUS BAR (28px) ================= */}
      <StatusBar
        fileName={activeDoc?.name.replace(/^src\//, '') || 'main.cpp'}
        language={activeDoc?.language.toUpperCase() || 'C++'}
        cursorLine={cursorPos.line}
        cursorCol={cursorPos.col}
        securityCount={mappedSecurityFindings.length}
        diagnosticCount={mappedDiagnostics.length}
        invalidTokenCount={mappedTokens.filter((t) => t.status === 'Invalid').length}
        engineStatus={isAnalyzing ? 'Analyzing' : 'Ready'}
        isStale={isStale}
        lexicalStatus={pipelineStages[0]?.status ?? 'not_run'}
        syntaxStatus={pipelineStages[1]?.status ?? 'not_run'}
        semanticStatus={pipelineStages[2]?.status ?? 'not_run'}
        onShowToast={showToast}
        onOpenSecurity={() => {
          setActivePane('pane-security');
          setSidebarCollapsed(false);
          setActiveBottomTab('view-security-tab');
          setBottomCollapsed(false);
        }}
        onOpenDiagnostics={() => {
          setActiveBottomTab('view-diagnostics');
          setBottomCollapsed(false);
        }}
        onOpenTokens={() => {
          setActiveBottomTab('view-tokens');
          setBottomCollapsed(false);
        }}
        onReanalyze={() => void triggerAnalyze()}
      />

      {/* ================= MODAL: COMMAND PALETTE ================= */}
      <CommandPaletteModal
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        commands={commandList}
      />

      {/* ================= MODAL: BUILD WITH AI ================= */}
      <BuildWithAiModal
        isOpen={buildAiModalOpen}
        onClose={() => setBuildAiModalOpen(false)}
        activeLanguage={activeDoc?.language || 'cpp'}
        onGenerate={handleExecuteBuildAi}
        onInsertIntoEditor={handleInsertCodeSnippet}
        onCreateFile={handleCreateFileFromCandidate}
        onRefineInAssistant={handleRefineCandidateInAssistant}
        onShowToast={showToast}
      />

      {/* ================= TOAST SYSTEM ================= */}
      <ToastBox
        toasts={toasts}
        onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))}
      />
    </div>
  );
};

export default IDE;
