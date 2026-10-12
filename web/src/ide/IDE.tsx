import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import type * as Monaco from 'monaco-editor';
import { apiClient, type AIExplainV2Request, type AIGenerateResponse, type AnalysisResultV2, type AnalyzeV2Request, type CapabilitiesResponse, type DiagnosticV2, type SampleItem, type StageAnalysisResponse, type TokenV2 } from '../api/client';
import { useTheme } from '../theme/theme';
import { buildMonacoTheme } from '../theme/monacoTheme';
import { initIDEWorkers } from './lib/monacoWorkers';
import { SAMPLE_GROUPS, groupSample, sampleBadge } from './lib/sampleGroups';
import { activeLanguage, displayEol, dimensionLabel, engineLabel, grammarLabel, securityLabel } from './lib/status';
import { clampPanelHeight } from './lib/panelResize';
import { setEditorSelection, revealEditorRange } from '../editor/navigation';
import { TokensPanel } from './tokens/TokensPanel';
import { ProblemsPanel } from './problems/ProblemsPanel';
import { SecurityPanel, type IDEFinding } from './security/SecurityPanel';
import { ASTSidebar } from './ast/ASTSidebar';
import { SearchSidebar } from './sidebar/SearchSidebar';
import { SettingsModal } from './settings/SettingsModal';
import { FixWorkflowModal } from './fix/FixWorkflowModal';
import { readAutoAnalyze, writeAutoAnalyze } from './settings/preferences';
import { AIExplainPanel } from './ai/AIExplainPanel';
import { AgentActivityPanel } from './ai/AgentActivityPanel';
import { SafetyLab } from './safety/SafetyLab';
import { BuildAIDrawer } from './ai/BuildAIDrawer';
import { taintDecorations } from './security/taintDecorations';
import { observeInteractiveElements } from './lib/qaAttributes';
import { tokenAtPosition, isAnalysisIncomplete } from './tokens/tokenModel';
import { keybindingMatches, searchCommands, type Command } from './state/commands';
import { clampScale, hydrateIDEState, ideReducer, selectActiveDocument, selectAnalysisCounts, serializeIDEState, type IDEState } from './state/store';
import './IDE.css';
import './p4.css';

const STORAGE_KEY = 'securelex.ide.drafts.v6';
const starter = `#include <iostream>\n\nint main() {\n    int a = 9;\n    int b = 19;\n    int sum = a + b;\n    std::cout << sum << '\\n';\n    return 0;\n}\n`;
const icon = (name: string, size = 18) => <span aria-hidden="true" className="material-symbols-outlined" style={{ fontSize: size }}>{name}</span>;
const makeId = () => `doc-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
const monacoLanguage = (language: string) => ({ cpp: 'cpp', 'c++': 'cpp', c: 'cpp', python: 'python', py: 'python', java: 'java', javascript: 'javascript', js: 'javascript' }[language.toLowerCase()] ?? 'plaintext');
const applyIdeMonacoTheme = (instance: typeof Monaco, theme: 'dark' | 'light') => {
  const style = getComputedStyle(globalThis.document.documentElement);
  const read = (name: string) => style.getPropertyValue(name).trim();
  const tokens = {
    '--text-primary': read('--color-vs-text'), '--text-secondary': read('--color-vs-light'), '--text-muted': read('--color-vs-muted'),
    '--surface-2': read('--color-vs-bg'), '--surface-3': read('--color-vs-elevated'), '--border-strong': read('--color-vs-borderSubtle'),
    '--editor-line-highlight': read('--color-vs-hover'), '--editor-selection': read('--color-vs-selection'), '--editor-indent-guide': read('--gutter-border'),
    '--sev-critical': read('--color-vs-red'), '--sev-medium': read('--color-vs-yellow'), '--sev-low': read('--color-vs-cyan'),
    '--bg-accent': read('--color-vs-highlight'), '--scrollbar-thumb': read('--scrollbar-thumb'), '--scrollbar-thumb-hover': read('--scrollbar-thumb-hover'),
  };
  instance.editor.defineTheme('securelex-dark', buildMonacoTheme(tokens, 'dark'));
  instance.editor.defineTheme('securelex-light', buildMonacoTheme(tokens, 'light'));
  instance.editor.setTheme(`securelex-${theme}`);
};

export function IDE() {
  const { resolved, setMode, toggleTheme } = useTheme();
  const [state, dispatch] = useReducer(ideReducer, undefined, () => {
    let hydrated: IDEState;
    try { hydrated = hydrateIDEState(localStorage.getItem(STORAGE_KEY)); } catch { hydrated = hydrateIDEState(null); }
    const starterDocs = hydrated.documents.filter(doc => doc.name === 'main.cpp' && doc.source === starter && !doc.dirty && doc.origin === 'new');
    if (starterDocs.length > 1) {
      const keepId = starterDocs.some(doc => doc.id === hydrated.activeDocId) ? hydrated.activeDocId : starterDocs[0].id;
      hydrated = { ...hydrated, documents: hydrated.documents.filter(doc => !starterDocs.some(candidate => candidate.id !== keepId && candidate.id === doc.id)), analysis: Object.fromEntries(hydrated.documents.filter(doc => !starterDocs.some(candidate => candidate.id !== keepId && candidate.id === doc.id)).map(doc => [doc.id, hydrated.analysis[doc.id]])), activeDocId: keepId };
    }
    if (hydrated.documents.length) return hydrated;
    return ideReducer(hydrated, { type: 'document/add', document: { id: makeId(), name: 'main.cpp', language: 'cpp', source: starter, savedSource: starter, sourceVersion: 1, dirty: false, origin: 'new' } });
  });
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(null);
  const [samples, setSamples] = useState<SampleItem[]>([]);
  const [apiUnavailable, setApiUnavailable] = useState(false);
  const [health, setHealth] = useState<Awaited<ReturnType<typeof apiClient.getHealth>> | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const [languagePicker, setLanguagePicker] = useState(false);
  const [renaming, setRenaming] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [groupsOpen, setGroupsOpen] = useState<Record<string, boolean>>({});
  const [editorReady, setEditorReady] = useState(false);
  const [editorHistory, setEditorHistory] = useState({ undo: false, redo: false });
  const [lexerTime, setLexerTime] = useState<number | null>(null);
  const [selectedTokenId, setSelectedTokenId] = useState<string | null>(null);
  const [stageData, setStageData] = useState<Record<string, { lexical: StageAnalysisResponse | null; syntax: StageAnalysisResponse | null }>>({});
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);
  const [dataFlowPathId, setDataFlowPathId] = useState<string | null>(null);
  const [selectedProblemId, setSelectedProblemId] = useState<string | null>(null);
  const [autoAnalyze, setAutoAnalyze] = useState(readAutoAnalyze);
  const [consentBusy, setConsentBusy] = useState(false);
  const [buildDrawerOpen, setBuildDrawerOpen] = useState(false);
  const [explainRequest, setExplainRequest] = useState<AIExplainV2Request | null>(null);
  const [aiOperationId, setAiOperationId] = useState<string | null>(null);
  const [fixFinding, setFixFinding] = useState<AnalysisResultV2['security_findings'][number] | null>(null);
  const [fixDocId, setFixDocId] = useState<string | null>(null);
  const [fixUndoAvailable, setFixUndoAvailable] = useState(false);
  const [fixAllRequested, setFixAllRequested] = useState(false);
  const [pendingFixAnalysis, setPendingFixAnalysis] = useState<{ id: string; version: number } | null>(null);
  const [toast, setToast] = useState<{ message: string; error: boolean } | null>(null);
  const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof Monaco | null>(null);
  const analysisControllers = useRef(new Map<string, AbortController>());
  const tokenSelection = useRef(false);
  const decorations = useRef<string[]>([]);
  const p4Decorations = useRef<string[]>([]);
  const pendingNavigation = useRef<{ docId: string; range: { startLineNumber: number; startColumn: number; endLineNumber: number; endColumn: number } } | null>(null);
  const sessionId = useRef(`ide-${globalThis.crypto?.randomUUID?.() ?? makeId()}`);
  const resultRef = useRef<AnalysisResultV2 | null>(null);
  const shellRef = useRef<HTMLElement>(null);
  const paletteInput = useRef<HTMLInputElement>(null);
  const paletteInvoker = useRef<HTMLElement | null>(null);
  const tabStrip = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const toolbarHistoryAction = useRef<'undo' | 'redo' | null>(null);
  const fixActions = useRef<{ apply(): void; undo(): void; fixAll(): void; canApply(): boolean; canUndo(): boolean } | null>(null);
  const document = selectActiveDocument(state);
  const counts = selectAnalysisCounts(state);
  const analysis = document ? state.analysis[document.id] : null;
  const stageForDoc = document && analysis?.status === 'ok' && analysis.forSourceVersion === document.sourceVersion ? stageData[document.id] : null;
  const result = analysis?.result ?? null;
  const problemDiagnostics = useMemo<DiagnosticV2[]>(() => [...(stageForDoc?.lexical?.diagnostics ?? []), ...(result?.syntax_diagnostics ?? []), ...(result?.semantic_diagnostics ?? [])], [stageForDoc?.lexical, result]);
  const currentFinding = result?.security_findings.find(finding => finding.id === selectedFindingId) ?? null;
  const problemCount = problemDiagnostics.length;
  resultRef.current = result;
  const languageInfo = activeLanguage(document, capabilities);
  const canBuild = Boolean(capabilities?.features.build_with_ai);
  const canFix = Boolean(capabilities?.features.fix_with_ai);
  const languageLabel = languageInfo?.name ?? document?.language ?? 'Language unavailable';
  const analysisLabel = analysis?.status === 'running' ? 'Analysis running'
    : analysis?.status === 'error' ? 'Analysis error'
      : analysis?.status === 'stale' || (result && document && analysis?.forSourceVersion !== document.sourceVersion) ? 'Stale'
        : analysis?.status === 'ok' && isAnalysisIncomplete(result) ? 'Analysis incomplete'
          : analysis?.status === 'ok' ? 'Up to date' : 'Not analysed';

  const reportToast = useCallback((message: string, error = false) => {
    setToast({ message, error });
    window.setTimeout(() => setToast(current => current?.message === message ? null : current), 3600);
  }, []);
  const sha256 = useCallback(async (source: string) => {
    const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(source));
    return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
  }, []);
  const analyzeDocument = useCallback(async () => {
    const target = document;
    if (!target || analysisControllers.current.has(target.id)) return;
    const controller = new AbortController();
    analysisControllers.current.set(target.id, controller);
    dispatch({ type: 'analysis/start', id: target.id, abort: controller });
    try {
      const response = await apiClient.analyzeV2({
        source: target.source, language: target.language, filename: target.name,
        api_version: 2, source_version: target.sourceVersion,
        options: { include_tokens: true, stages: ['lexical', 'syntax', 'security', 'quality'], agent: 'off' },
      }, controller.signal);
      if (controller.signal.aborted || analysisControllers.current.get(target.id) !== controller) return;
      const expectedHash = await sha256(target.source);
      if (response.source_version !== target.sourceVersion || response.source_hash !== expectedHash) {
        dispatch({ type: 'analysis/error', id: target.id });
        reportToast('Analysis response did not match this document version.', true);
        return;
      }
      dispatch({ type: 'analysis/success', id: target.id, result: response, version: target.sourceVersion });
      const stageRequest: AnalyzeV2Request = { source: target.source, language: target.language, filename: target.name, api_version: 2, source_version: target.sourceVersion, include_ast: true, options: { include_tokens: true, stages: ['lexical', 'syntax', 'security', 'quality'], agent: 'off' } };
      const [lexicalStage, syntaxStage] = await Promise.allSettled([
        apiClient.analyzeStageV2('lexical', stageRequest, controller.signal),
        apiClient.analyzeStageV2('syntax', stageRequest, controller.signal),
      ]);
      if (controller.signal.aborted || analysisControllers.current.get(target.id) !== controller) return;
      if (lexicalStage.status === 'rejected' || syntaxStage.status === 'rejected') reportToast('Analysis finished, but some lexical or AST details are unavailable.', true);
      setStageData(previous => ({ ...previous, [target.id]: { lexical: lexicalStage.status === 'fulfilled' ? lexicalStage.value : null, syntax: syntaxStage.status === 'fulfilled' ? syntaxStage.value : null } }));
      setSelectedTokenId(response.tokens[0]?.id ?? null);
      reportToast(isAnalysisIncomplete(response) ? 'Analysis completed with unavailable or incomplete checks.' : 'Analysis completed.');
    } catch (error) {
      if (controller.signal.aborted || (error instanceof Error && error.name === 'AbortError')) return;
      if (analysisControllers.current.get(target.id) !== controller) return;
      dispatch({ type: 'analysis/error', id: target.id });
      reportToast(error instanceof Error ? error.message : 'Analysis failed.', true);
    } finally {
      if (analysisControllers.current.get(target.id) === controller) analysisControllers.current.delete(target.id);
    }
  }, [document, reportToast, sha256]);
  const cancelAnalysis = useCallback((id: string) => {
    const controller = analysisControllers.current.get(id);
    if (!controller) return;
    controller.abort();
    analysisControllers.current.delete(id);
    dispatch({ type: 'analysis/cancel', id });
    reportToast('Analysis cancelled.');
  }, [reportToast]);
  const selectToken = useCallback((token: TokenV2) => {
    setSelectedTokenId(token.id);
    const editor = editorRef.current;
    if (!editor) return;
    const range = { startLineNumber: token.start_line, startColumn: token.start_column, endLineNumber: token.end_line, endColumn: token.end_column };
    tokenSelection.current = true;
    setEditorSelection(editor, range, 'token table selection');
    revealEditorRange(editor, range, 'token table selection');
    requestAnimationFrame(() => { tokenSelection.current = false; });
  }, []);
  const navigateRange = useCallback((range: { start_line: number; start_col: number; end_line: number; end_col: number }) => {
    const editor = editorRef.current;
    if (!editor) return;
    const selection = { startLineNumber: range.start_line, startColumn: range.start_col, endLineNumber: range.end_line, endColumn: range.end_col };
    setEditorSelection(editor, selection, 'P4 result selection');
    revealEditorRange(editor, selection, 'P4 result selection');
  }, []);
  const selectProblem = useCallback((item: DiagnosticV2) => { setSelectedProblemId(item.id); navigateRange(item.range); }, [navigateRange]);
  const selectFinding = useCallback((finding: IDEFinding | null) => {
    setSelectedFindingId(finding?.id ?? null);
    setDataFlowPathId(null);
    if (finding) { dispatch({ type: 'ui', patch: { panelTab: 'security', panelOpen: true } }); navigateRange(finding.range); }
  }, [navigateRange]);
  const navigateDocument = useCallback((target: IDEState['documents'][number], range: { start_line: number; start_col: number; end_line: number; end_col: number }) => {
    const selection = { startLineNumber: range.start_line, startColumn: range.start_col, endLineNumber: range.end_line, endColumn: range.end_col };
    if (target.id === state.activeDocId && editorRef.current) { setEditorSelection(editorRef.current, selection, 'document search result'); revealEditorRange(editorRef.current, selection, 'document search result'); }
    else { pendingNavigation.current = { docId: target.id, range: selection }; dispatch({ type: 'document/activate', id: target.id }); }
  }, [state.activeDocId]);
  const submitFalsePositive = useCallback(async (finding: IDEFinding) => {
    try {
      const snippet = document?.source.split(/\r?\n/)[finding.range.start_line - 1] ?? '';
      await apiClient.submitFeedback({ finding_fingerprint: finding.id, rule_id: finding.rule_id, language: document?.language ?? 'unknown', verdict: 'false_positive', snippet });
      reportToast('False-positive feedback recorded.');
    } catch (error) { reportToast(error instanceof Error ? error.message : 'Feedback could not be saved.', true); }
  }, [document, reportToast]);
  const setConsent = useCallback(async (consent: boolean): Promise<boolean> => {
    setConsentBusy(true);
    try { await apiClient.setRemoteConsent(sessionId.current, consent); const updated = await apiClient.getCapabilities(sessionId.current); setCapabilities(updated); reportToast(consent ? 'Remote processing consent saved for this session.' : 'Remote processing consent withdrawn.'); return true; }
    catch (error) { reportToast(error instanceof Error ? error.message : 'Consent setting could not be saved.', true); return false; }
    finally { setConsentBusy(false); }
  }, [reportToast]);
  const requestExplanation = useCallback((target: AIExplainV2Request['target'], targetId?: string | null) => {
    if (!document) return;
    const request: AIExplainV2Request = { session_id: sessionId.current, target, source: document.source, language: document.language, target_id: targetId ?? null, remote_consent: Boolean(capabilities?.ai.remote_consented) };
    setExplainRequest(request); setAiOperationId(null);
    dispatch({ type: 'ui', patch: { panelTab: 'explain', panelOpen: true } });
  }, [document, capabilities]);
  const acceptConsent = useCallback(async () => { if (!await setConsent(true)) throw new Error('Remote processing consent could not be saved.'); }, [setConsent]);
  const startFix = useCallback((finding: AnalysisResultV2['security_findings'][number]) => {
    if (!document || !canFix) return;
    setFixDocId(document.id); setFixFinding(finding); setFixUndoAvailable(false);
  }, [document, canFix]);
  const closeFix = useCallback(() => { setFixFinding(null); setFixDocId(null); setFixAllRequested(false); fixActions.current = null; }, []);
  const startFixAll = useCallback(() => { const target = currentFinding ?? result?.security_findings[0]; if (target && canFix) { setFixAllRequested(true); startFix(target); } }, [currentFinding, result, canFix, startFix]);
  const updateFixActions = useCallback((actions: NonNullable<typeof fixActions.current>) => { fixActions.current = actions; }, []);
  const onFixSourceApplied = useCallback((source: string, version: number) => {
    const target = state.documents.find(item => item.id === fixDocId);
    if (!target || version !== target.sourceVersion + 1) return;
    dispatch({ type: 'document/edit', id: target.id, source });
    setFixUndoAvailable(true); setPendingFixAnalysis({ id: target.id, version });
  }, [state.documents, fixDocId]);
  const onFixUndo = useCallback((source: string, version: number) => {
    const target = state.documents.find(item => item.id === fixDocId);
    if (!target || version !== target.sourceVersion + 1) return;
    dispatch({ type: 'document/edit', id: target.id, source });
    setFixUndoAvailable(false); setPendingFixAnalysis({ id: target.id, version });
  }, [state.documents, fixDocId]);
  const openGeneratedCandidate = useCallback((candidate: AIGenerateResponse) => {
    const id = makeId();
    const name = `AI candidate.${candidate.language === 'cpp' ? 'cpp' : candidate.language === 'javascript' ? 'js' : candidate.language}`;
    dispatch({ type: 'document/add', document: { id, name, language: candidate.language, source: candidate.code, savedSource: '', sourceVersion: 1, dirty: true, origin: 'new' } });
    dispatch({ type: 'analysis/success', id, result: candidate.analysis, version: 1 });
    setAiOperationId(candidate.operation_id);
    setExplainRequest({ session_id: sessionId.current, target: 'file', source: candidate.code, language: candidate.language, remote_consent: Boolean(capabilities?.ai.remote_consented) });
    dispatch({ type: 'ui', patch: { panelTab: 'explain', panelOpen: true } });
  }, [capabilities]);
  const recordAIOperation = useCallback((operationId: string) => setAiOperationId(operationId), []);
  const moveProblem = useCallback((delta: number) => {
    const ordered = [...problemDiagnostics].sort((a, b) => a.range.start_line - b.range.start_line || a.range.start_col - b.range.start_col);
    if (!ordered.length) return;
    const currentIndex = ordered.findIndex(item => item.id === selectedProblemId);
    const nextIndex = currentIndex < 0 ? (delta > 0 ? 0 : ordered.length - 1) : (currentIndex + delta + ordered.length) % ordered.length;
    selectProblem(ordered[nextIndex]);
    dispatch({ type: 'ui', patch: { panelTab: 'problems', panelOpen: true } });
  }, [problemDiagnostics, selectedProblemId, selectProblem]);

  useEffect(() => {
    let active = true;
    apiClient.getCapabilities().then(value => { if (active) { setCapabilities(value); setApiUnavailable(false); } }).catch(() => { if (active) { setApiUnavailable(true); } });
    apiClient.getHealth().then(value => { if (active) setHealth(value); }).catch(() => { if (active) setHealthError(true); });
    apiClient.getSamples().then(value => { if (active) setSamples(value); }).catch(() => { if (active) setApiUnavailable(true); });
    return () => { active = false; };
  }, []);
  useEffect(() => shellRef.current ? observeInteractiveElements(shellRef.current) : undefined, []);
  useEffect(() => { if (state.documents.length) { try { localStorage.setItem(STORAGE_KEY, serializeIDEState(state)); } catch { /* Drafts remain available in memory. */ } } }, [state]);
  useEffect(() => { writeAutoAnalyze(autoAnalyze); }, [autoAnalyze]);
  useEffect(() => {
    if (!autoAnalyze || !document || analysis?.status === 'running') return;
    const timer = window.setTimeout(() => { void analyzeDocument(); }, 700);
    return () => window.clearTimeout(timer);
  }, [autoAnalyze, document, analyzeDocument, analysis?.status]);
  useEffect(() => {
    if (!pendingFixAnalysis || document?.id !== pendingFixAnalysis.id || document.sourceVersion !== pendingFixAnalysis.version || analysis?.status === 'running') return;
    setPendingFixAnalysis(null);
    void analyzeDocument();
  }, [pendingFixAnalysis, document, analysis?.status, analyzeDocument]);
  useEffect(() => () => { analysisControllers.current.forEach(controller => controller.abort()); }, []);
  useEffect(() => {
    globalThis.document.documentElement.style.fontSize = `${13 * state.ui.interfaceScale / 100}px`;
    return () => { globalThis.document.documentElement.style.fontSize = ''; };
  }, [state.ui.interfaceScale]);
  useEffect(() => { initIDEWorkers(); }, []);
  useEffect(() => { setEditorHistory({ undo: false, redo: false }); }, [document?.id]);
  useEffect(() => { if (editorReady && monacoRef.current) applyIdeMonacoTheme(monacoRef.current, resolved); }, [editorReady, resolved]);
  useEffect(() => { if (state.ui.paletteOpen) { setQuery(''); setSelected(0); requestAnimationFrame(() => paletteInput.current?.focus()); } else paletteInvoker.current?.focus(); }, [state.ui.paletteOpen]);
  useEffect(() => { if (state.activeDocId) { const activeTab = tabStrip.current?.querySelector<HTMLElement>(`[data-doc="${CSS.escape(state.activeDocId)}"]`); activeTab?.scrollIntoView?.({ block: 'nearest', inline: 'nearest' }); } }, [state.activeDocId]);

  const openPalette = useCallback((invoker?: HTMLElement | null) => { paletteInvoker.current = invoker ?? globalThis.document.activeElement as HTMLElement; dispatch({ type: 'ui', patch: { paletteOpen: true } }); }, []);
  const newDocument = useCallback(() => {
    const index = state.documents.length + 1;
    const id = makeId();
    dispatch({ type: 'document/add', document: { id, name: `untitled-${index}.${languageInfo?.extensions?.[0]?.replace(/^\./, '') || 'txt'}`, language: document?.language ?? capabilities?.languages[0]?.id ?? 'cpp', source: '', savedSource: '', sourceVersion: 1, dirty: false, origin: 'new' } });
  }, [state.documents.length, languageInfo, document, capabilities]);
  const closeDocument = useCallback((id: string) => dispatch({ type: 'document/remove', id }), []);
  const focusExplorer = useCallback(() => { dispatch({ type: 'ui', patch: { activity: 'explorer', sidebarOpen: true } }); }, []);
  const openExample = useCallback((sample: SampleItem) => {
    const id = makeId();
    dispatch({ type: 'document/add', document: { id, name: sample.filename, language: sample.language, source: sample.code, savedSource: '', sourceVersion: 1, dirty: true, origin: 'sample', sampleId: sample.id } });
    focusExplorer();
  }, [focusExplorer]);
  const commands = useMemo<Command[]>(() => {
    const items: Command[] = [
      { id: 'analyze', title: 'Analyze Current Document', keybinding: 'F5', enabled: () => Boolean(document), run: () => void analyzeDocument() },
      { id: 'propose-fix', title: 'Fix: Propose Fix for Selected Finding', enabled: () => Boolean(currentFinding && canFix), run: () => currentFinding && startFix(currentFinding) },
      { id: 'apply-fix', title: 'Fix: Apply Reviewed Fix', enabled: () => fixActions.current?.canApply() ?? false, run: () => fixActions.current?.apply() },
      { id: 'undo-fix', title: 'Fix: Undo Last Fix', enabled: () => fixUndoAvailable || (fixActions.current?.canUndo() ?? false), run: () => fixActions.current?.undo() },
      { id: 'fix-all-safe', title: 'Fix: Review All Safe Fixes', enabled: () => Boolean(document && result?.security_findings.length && canFix), run: startFixAll },
      { id: 'explain-token', title: 'AI: Explain Selected Token', enabled: () => Boolean(document && selectedTokenId && result?.tokens.some(token => token.id === selectedTokenId)), run: () => { const token = result?.tokens.find(item => item.id === selectedTokenId); if (token) requestExplanation('token', String(result?.tokens.indexOf(token))); } },
      { id: 'explain-file', title: 'AI: Explain Current File', enabled: () => Boolean(document), run: () => requestExplanation('file') },
      { id: 'build-with-ai', title: 'AI: Build with AI', enabled: () => canBuild, run: () => setBuildDrawerOpen(true) },
      { id: 'open-ai-explain', title: 'View: AI Explain', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { panelTab: 'explain', panelOpen: true } }) },
      { id: 'open-safety-lab', title: 'View: Agent Safety Lab', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { activity: 'safetylab', sidebarOpen: false } }) },
      { id: 'run-safety-scenario', title: 'Safety Lab: Run Selected Scenario', enabled: () => true, run: () => { dispatch({ type: 'ui', patch: { activity: 'safetylab', sidebarOpen: false } }); window.setTimeout(() => window.dispatchEvent(new Event('securelex:safety-run')), 0); } },
      { id: 'export-safety-report', title: 'Safety Lab: Export Report', enabled: () => true, run: () => { dispatch({ type: 'ui', patch: { activity: 'safetylab', sidebarOpen: false } }); window.setTimeout(() => window.dispatchEvent(new Event('securelex:safety-export')), 0); } },
      { id: 'open-agent-activity', title: 'View: Agent Activity', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { panelTab: 'agent', panelOpen: true } }) },
      { id: 'show-tokens', title: 'View: Tokens', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { panelTab: 'tokens', panelOpen: true } }) },
      { id: 'show-problems', title: 'View: Problems', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { panelTab: 'problems', panelOpen: true } }) },
      { id: 'show-security', title: 'View: Security', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { panelTab: 'security', panelOpen: true, activity: 'security', sidebarOpen: true } }) },
      { id: 'open-ast', title: 'Open AST Sidebar', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { activity: 'ast', sidebarOpen: true } }) },
      { id: 'open-search', title: 'Open Search Sidebar', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { activity: 'search', sidebarOpen: true } }) },
      { id: 'open-security', title: 'Open Security Sidebar', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { activity: 'security', sidebarOpen: true } }) },
      { id: 'next-problem', title: 'Go to Next Problem', keybinding: 'F8', enabled: () => problemDiagnostics.length > 0, run: () => moveProblem(1) },
      { id: 'previous-problem', title: 'Go to Previous Problem', keybinding: 'Shift+F8', enabled: () => problemDiagnostics.length > 0, run: () => moveProblem(-1) },
      { id: 'open-settings', title: 'Open Workbench Settings', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { settingsOpen: true } }) },
      { id: 'new-file', title: 'New File', keybinding: 'Ctrl+N', enabled: () => true, run: newDocument },
      { id: 'close-tab', title: 'Close Tab', keybinding: 'Ctrl+W', enabled: () => Boolean(document), run: () => document && closeDocument(document.id) },
      { id: 'toggle-theme', title: 'Toggle Theme', keybinding: 'Alt+T', enabled: () => true, run: toggleTheme },
      { id: 'interface-size', title: 'Interface Size', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { settingsOpen: true } }) },
      { id: 'toggle-panel', title: 'Toggle Panel', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { panelOpen: !state.ui.panelOpen } }) },
      { id: 'focus-explorer', title: 'Focus Explorer', keybinding: 'Ctrl+Shift+E', enabled: () => true, run: focusExplorer },
      { id: 'view-search', title: 'View: Search', keybinding: 'Ctrl+Shift+F', enabled: () => true, run: () => dispatch({ type: 'ui', patch: { activity: 'search', sidebarOpen: true } }) },
      ...(['explorer', 'ast', 'security', 'safetylab'] as const).map(activity => ({ id: `view-${activity}`, title: `View: ${activity === 'safetylab' ? 'Agent Safety Lab' : activity[0].toUpperCase() + activity.slice(1)}`, enabled: () => true, run: () => dispatch({ type: 'ui', patch: { activity, sidebarOpen: activity !== 'safetylab' } }) })),
      ...(capabilities?.languages ?? []).map(lang => ({ id: `language-${lang.id}`, title: `Switch Language: ${lang.name}`, enabled: () => Boolean(document), run: () => document && dispatch({ type: 'document/language', id: document.id, language: lang.id }) })),
      ...samples.map(sample => ({ id: `example-${sample.id}`, title: `Open Example: ${sample.title}`, enabled: () => true, run: () => openExample(sample) })),
    ];
    return items;
  }, [newDocument, document, closeDocument, toggleTheme, state.ui.panelOpen, focusExplorer, capabilities, samples, openExample, analyzeDocument, problemDiagnostics, moveProblem, canBuild, requestExplanation, selectedTokenId, result, currentFinding, canFix, startFix, startFixAll, fixUndoAvailable]);
  const filteredCommands = useMemo(() => searchCommands(commands, query), [commands, query]);
  const runCommand = (command?: Command) => { if (!command || !command.enabled()) return; dispatch({ type: 'ui', patch: { paletteOpen: false } }); command.run(); };
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'p') { event.preventDefault(); openPalette(); return; }
      if (state.ui.paletteOpen) {
        if (event.key === 'Escape') { event.preventDefault(); dispatch({ type: 'ui', patch: { paletteOpen: false } }); }
        else if (event.key === 'ArrowDown') { event.preventDefault(); setSelected(value => Math.min(value + 1, filteredCommands.length - 1)); }
        else if (event.key === 'ArrowUp') { event.preventDefault(); setSelected(value => Math.max(0, value - 1)); }
        else if (event.key === 'Enter') { event.preventDefault(); runCommand(filteredCommands[selected]); }
        else if (event.key === 'Tab') { event.preventDefault(); paletteInput.current?.focus(); }
        return;
      }
      if (event.key === 'F5' || (event.ctrlKey && event.key === 'Enter')) { event.preventDefault(); if (document && analysisControllers.current.has(document.id)) cancelAnalysis(document.id); else void analyzeDocument(); return; }
      const matched = commands.find(command => command.keybinding && keybindingMatches(event, command.keybinding));
      if (matched) { event.preventDefault(); matched.run(); return; }
      if (event.ctrlKey && event.key.toLowerCase() === 'n') { event.preventDefault(); newDocument(); }
      else if (event.ctrlKey && event.key.toLowerCase() === 'w' && document) { event.preventDefault(); closeDocument(document.id); }
      else if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'e') { event.preventDefault(); focusExplorer(); }
      else if (event.ctrlKey && event.key.toLowerCase() === 'f') editorRef.current?.getAction('actions.find')?.run();
    };
    window.addEventListener('keydown', handler); return () => window.removeEventListener('keydown', handler);
  }, [state.ui.paletteOpen, filteredCommands, selected, commands, document, newDocument, closeDocument, focusExplorer, openPalette, analyzeDocument, cancelAnalysis]);
  const onEditorMount = (editor: Monaco.editor.IStandaloneCodeEditor, monacoApi: typeof Monaco) => { editorRef.current = editor; monacoRef.current = monacoApi; applyIdeMonacoTheme(monacoApi, resolved); setEditorReady(true); const pending = pendingNavigation.current; if (pending && pending.docId === document?.id) { pendingNavigation.current = null; setEditorSelection(editor, pending.range, 'document search result'); revealEditorRange(editor, pending.range, 'document search result'); } editor.onDidChangeCursorPosition(e => { dispatch({ type: 'ui', patch: { cursor: { line: e.position.lineNumber, column: e.position.column } } }); if (!tokenSelection.current) setSelectedTokenId(tokenAtPosition(resultRef.current?.tokens ?? [], e.position.lineNumber, e.position.column)?.id ?? null); }); };
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || !result || analysis?.status === 'stale') { if (editor) decorations.current = editor.deltaDecorations(decorations.current, []); return; }
    const next = result.tokens.map(token => {
      const category = token.category.toLocaleLowerCase();
      const kind = token.lexical_status === 'invalid' ? 'invalid'
        : category.includes('keyword') ? 'keyword'
          : category.includes('identifier') ? 'identifier'
            : category.includes('operator') ? 'operator'
              : category.includes('literal') || category.includes('header') ? 'literal'
                : category.includes('preprocessor') ? 'preprocessor'
                  : category.includes('delimiter') ? 'delimiter'
                    : category.includes('comment') ? 'comment' : '';
      if (!kind) return null;
      return { range: { startLineNumber: token.start_line, startColumn: token.start_column, endLineNumber: token.end_line, endColumn: token.end_column }, options: { inlineClassName: `ide-monaco-token-${kind}` } };
    }).filter((decoration): decoration is NonNullable<typeof decoration> => decoration !== null);
    decorations.current = editor.deltaDecorations(decorations.current, next);
  }, [result, analysis?.status, document?.id]);
  useEffect(() => { const timing = result?.tools.find(tool => tool.kind.toLowerCase().includes('lexer') || tool.name.toLowerCase().includes('lexer'))?.duration_ms; setLexerTime(typeof timing === 'number' ? timing : null); }, [result]);
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const next: Monaco.editor.IModelDeltaDecoration[] = [];
    if (currentFinding) next.push({ range: { startLineNumber: currentFinding.range.start_line, startColumn: currentFinding.range.start_col, endLineNumber: currentFinding.range.end_line, endColumn: currentFinding.range.end_col }, options: { inlineClassName: 'ide-p4-finding-highlight', overviewRuler: { color: 'var(--token-invalid)', position: monacoRef.current?.editor.OverviewRulerLane.Right ?? 4 } } });
    const flow = result?.taint_paths.find(path => path.id === dataFlowPathId);
    next.push(...taintDecorations(flow, monacoRef.current?.editor.OverviewRulerLane.Right ?? 4));
    p4Decorations.current = editor.deltaDecorations(p4Decorations.current, next);
  }, [currentFinding, dataFlowPathId, result]);
  const changeActivity = (activity: IDEState['ui']['activity']) => dispatch({ type: 'ui', patch: { activity, sidebarOpen: activity !== 'safetylab' } });
  const startRename = (id: string, name: string) => { setRenaming(id); setRenameValue(name); };
  const finishRename = (id: string) => { const value = renameValue.trim(); if (value) dispatch({ type: 'document/rename', id, name: value }); setRenaming(null); };
  const setLanguage = (language: string) => { if (document && document.language !== language) { const running = analysisControllers.current.get(document.id); running?.abort(); analysisControllers.current.delete(document.id); dispatch({ type: 'document/language', id: document.id, language }); } setLanguagePicker(false); };
  const startResize = (event: React.PointerEvent) => { dragging.current = true; event.currentTarget.setPointerCapture(event.pointerId); };
  const availablePanelSpace = () => window.innerHeight - 38 - 24 - 34 - 30 - 5;
  const moveResize = (event: React.PointerEvent) => { if (!dragging.current) return; const bounds = event.currentTarget.parentElement?.getBoundingClientRect(); if (bounds) dispatch({ type: 'ui', patch: { panelHeight: clampPanelHeight(bounds.bottom - event.clientY, availablePanelSpace()), panelMaximised: false } }); };
  const stopResize = () => { dragging.current = false; };
  const setPanelHeight = (delta: number) => dispatch({ type: 'ui', patch: { panelHeight: clampPanelHeight((state.ui.panelHeight || availablePanelSpace() * .52) + delta, availablePanelSpace()), panelMaximised: false, panelOpen: true } });
  const samplesByGroup = (group: string) => samples.filter(sample => sample.language === document?.language && groupSample(sample) === group);
  const visibleExampleGroups = SAMPLE_GROUPS;
  const activityItems = [
    ['explorer', 'folder_copy', 'Explorer', 'Ctrl+Shift+E'], ['search', 'search', 'Search', 'Ctrl+Shift+F'], ['ast', 'account_tree', 'AST', ''], ['security', 'shield', 'Security', ''], ['safetylab', 'smart_toy', 'Agent Safety Lab', ''],
  ] as const;
  const panels = [['tokens', 'Tokens', counts.tokens], ['problems', 'Problems', problemCount], ['security', 'Security', result?.security_findings.length ?? 0], ['explain', 'AI Explain', 0], ['agent', 'Agent Activity', 0]] as const;
  const resultForPanel = state.ui.panelTab === 'tokens' ? 'Tokens appear after analysis.' : state.ui.panelTab === 'problems' ? 'No analysis results yet.' : state.ui.panelTab === 'security' ? 'No security checks have run.' : state.ui.panelTab === 'explain' ? 'Select an item after analysis to request an explanation.' : 'No agent activity is available.';

  const retryBackend = useCallback(async () => {
    setApiUnavailable(false);
    try {
      const [nextCapabilities, nextSamples, nextHealth] = await Promise.all([apiClient.getCapabilities(), apiClient.getSamples(), apiClient.getHealth()]);
      setCapabilities(nextCapabilities); setSamples(nextSamples); setHealth(nextHealth); setHealthError(false);
    } catch { setApiUnavailable(true); setHealthError(true); }
  }, []);

  return <main ref={shellRef} className="ide-shell" aria-label="SecureLex workbench">
    <header className="ide-titlebar">
      <div className="ide-brand"><svg aria-hidden="true" className="ide-logo" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2 3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-3Zm-1 6h2v6h-2V8Zm0 8h2v2h-2v-2Z"/></svg><span className="ide-brand-name">SecureLex</span><span className="ide-version">{capabilities ? `v${capabilities.version}` : '…'}</span><span className="ide-project"><span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: 15 }}>folder_managed</span><span className="ide-project-name">{document?.name ?? 'Workspace'}</span><span className="ide-language-chip">{languageLabel}</span></span></div>
      <button className="ide-command-button" type="button" onClick={event => openPalette(event.currentTarget)} aria-label="Open Command Palette (Ctrl+Shift+P)"><span className="ide-command-content">{icon('search', 15)}<span>Search commands, symbols, files...</span></span><kbd>Ctrl+Shift+P</kbd></button>
      <div className="ide-title-actions"><span className="ide-ai-provider-badge" title={capabilities?.ai.setup_message || (capabilities?.ai.configured ? `${capabilities.ai.provider} · ${capabilities.ai.model ?? 'model unavailable'} · ${capabilities.ai.processing_location}` : 'AI provider status unavailable')}>{capabilities ? `${capabilities.ai.provider} · ${capabilities.ai.processing_location}` : 'AI unavailable'}</span><div className="ide-theme-switch" role="group" aria-label="IDE theme"><button type="button" aria-pressed={resolved === 'dark'} onClick={() => setMode('dark')}>{icon('dark_mode', 14)}<span>Dark</span></button><button type="button" aria-pressed={resolved === 'light'} onClick={() => setMode('light')}>{icon('light_mode', 14)}<span>Light</span></button></div><span className="ide-title-divider"/><div className="ide-action-group"><button className="ide-feature-button" disabled={!canBuild} title={canBuild ? 'Build with AI' : capabilities?.ai.setup_message || 'AI provider unavailable; check backend setup.'} onClick={() => setBuildDrawerOpen(true)}>{icon('auto_fix_high', 15)}<span>Build with AI</span></button><button className="ide-feature-button fix" disabled={!canFix || !currentFinding} title={!canFix ? 'Fix capability is unavailable.' : !currentFinding ? 'Select a finding first.' : 'Propose an AI fix for the selected finding'} onClick={() => currentFinding && startFix(currentFinding)}>{icon('verified', 15)}<span>Fix with AI</span></button></div></div>
    </header>
    {apiUnavailable && <div className="ide-backend-banner" role="alert"><span>Backend unavailable. Reconnect to load capabilities and samples.</span><button type="button" data-qa="retry-backend" onClick={() => void retryBackend()}>Retry</button></div>}
    <div className="ide-main-row">
      <nav className="ide-activity" aria-label="Activity Bar"><div className="ide-activity-group">{activityItems.map(([id, glyph, label, shortcut]) => <button key={id} type="button" className={`ide-activity-button ${id === 'safetylab' ? 'safety' : ''}`} aria-label={label} aria-pressed={state.ui.activity === id} title={`${label}${shortcut ? ` (${shortcut})` : ''}`} onClick={() => changeActivity(id)}>{icon(glyph, 20)}{id === 'safetylab' && <span className={`ide-pulse-dot ${state.ui.safetyRunning ? 'active' : ''}`} />}</button>)}</div><div className="ide-activity-group"><button type="button" className="ide-activity-button" aria-label="Toggle theme (Alt+T)" title="Toggle theme (Alt+T)" onClick={toggleTheme}>{icon('brightness_medium', 20)}</button><button type="button" className="ide-activity-button" aria-label="Settings" title="Settings" aria-pressed={state.ui.settingsOpen} onClick={() => dispatch({ type: 'ui', patch: { settingsOpen: !state.ui.settingsOpen } })}>{icon('settings', 20)}</button></div></nav>
      {state.ui.sidebarOpen && <aside className="ide-sidebar" aria-label={`${state.ui.activity} sidebar`}><div className="ide-sidebar-header"><span>{state.ui.activity === 'safetylab' ? 'Agent Safety Lab' : state.ui.activity === 'ast' ? 'AST' : state.ui.activity[0].toUpperCase() + state.ui.activity.slice(1)}</span>{state.ui.activity === 'explorer' && <div className="ide-inline-actions"><button className="ide-icon-button" type="button" aria-label="New file" title="New File (Ctrl+N)" onClick={newDocument}>{icon('note_add', 16)}</button><button className="ide-icon-button" type="button" aria-label="Refresh samples" title="Refresh sample catalogue" onClick={() => apiClient.getSamples().then(setSamples).catch(() => setApiUnavailable(true))}>{icon('refresh', 15)}</button></div>}</div>{state.ui.activity === 'explorer' ? <div className="ide-tree-scroll">
        <div className="ide-tree-section-title">{icon('expand_more', 15)} Open Editors <span className="ide-group-count">{state.documents.length}</span></div>
        {state.documents.map(doc => <div key={doc.id} className={`ide-tree-row ${doc.id === document?.id ? 'active' : ''}`} onContextMenu={e => { e.preventDefault(); startRename(doc.id, doc.name); }}><button type="button" className="ide-row-main" onClick={() => dispatch({ type: 'document/activate', id: doc.id })}><span className="ide-file-icon">{icon('code', 15)}</span>{renaming === doc.id ? <input autoFocus className="ide-inline-rename" value={renameValue} onChange={e => setRenameValue(e.target.value)} onBlur={() => finishRename(doc.id)} onKeyDown={e => { if (e.key === 'Enter') finishRename(doc.id); if (e.key === 'Escape') setRenaming(null); }} aria-label={`Rename ${doc.name}`} /> : <span className="filename" onDoubleClick={e => { e.stopPropagation(); startRename(doc.id, doc.name); }}>{doc.name}</span>}{doc.dirty && <span className="ide-unsaved-dot" title="Unsaved changes" aria-label="Unsaved changes"/>}</button><span className="ide-inline-actions"><button type="button" className="ide-icon-button ide-row-close" aria-label={`Close ${doc.name}`} title={`Close ${doc.name}`} onClick={() => closeDocument(doc.id)}>{icon('close', 14)}</button></span></div>)}
        <div className="ide-tree-section-title sample-title">{icon('expand_more', 15)} Samples <span className="ide-group-count">{apiUnavailable ? 'Unavailable' : samples.filter(sample => sample.language === document?.language).length}</span></div>{apiUnavailable && <div className="ide-tree-message">Sample catalogue unavailable.</div>}{!samples.length && !apiUnavailable && <div className="ide-tree-message">Loading samples…</div>}{visibleExampleGroups.map(group => <section key={group.id}><button type="button" className="ide-sample-group" aria-expanded={groupsOpen[group.id] !== false} onClick={() => setGroupsOpen(current => ({ ...current, [group.id]: current[group.id] === false }))}>{icon(groupsOpen[group.id] === false ? 'chevron_right' : 'expand_more', 14)}<span>{group.label}</span><span className="ide-group-count">{samplesByGroup(group.id).length}</span></button>{groupsOpen[group.id] !== false && samplesByGroup(group.id).map(sample => <button type="button" key={sample.id} className="ide-tree-row ide-sample-row" title={sample.description} onClick={() => openExample(sample)}><span className="ide-row-main"><span className="ide-file-icon">{icon('description', 15)}</span><span className="filename">{sample.title}</span></span>{sampleBadge(sample) && <span className="ide-sample-badge">{sampleBadge(sample)}</span>}</button>)}</section>)}</div> : state.ui.activity === 'search' ? <SearchSidebar documents={state.documents} onOpen={navigateDocument}/> : state.ui.activity === 'ast' ? <ASTSidebar analysisId={stageForDoc?.syntax?.analysis_id ?? null} initial={stageForDoc?.syntax?.ast ?? null} capabilities={capabilities} document={document} onSelect={navigateRange}/> : state.ui.activity === 'security' ? <div className="ide-sidebar-scroll"><div className="ide-sidebar-section-label">Rule families · {languageLabel}</div>{(languageInfo?.security_tools ?? []).map(name => <div className="ide-security-tool" key={name}><span className="material-symbols-outlined" aria-hidden="true">shield</span>{name}</div>)}<div className="ide-sidebar-section-label">Tool status</div>{(capabilities?.tools ?? []).map(tool => <div className="ide-security-tool" key={tool.name}><span className={`ide-tool-state ${tool.available ? 'available' : ''}`}/><span>{tool.name}</span><small>{tool.status}</small></div>)}{!capabilities && <p className="ide-tree-message">Capabilities unavailable.</p>}</div> : <div className="ide-tree-scroll"><p className="ide-p4-empty">Safety Lab view is not connected in this phase.</p></div>}</aside>}
      <section className="ide-workspace" id="editorWorkspaceView" aria-label="Workbench">{state.ui.activity === 'safetylab' ? <SafetyLab capabilities={capabilities} source={document?.source ?? ''} language={document?.language ?? capabilities?.languages[0]?.id ?? 'python'} filename={document?.name ?? '<editor>'} sourceVersion={document?.sourceVersion ?? 0} onReturn={() => changeActivity('explorer')} onRunning={safetyRunning => dispatch({ type: 'ui', patch: { safetyRunning } })}/> : <><div className="ide-tabbar" ref={tabStrip} role="tablist" aria-label="Open files">{state.documents.map(doc => <div className={`ide-tab ${doc.id === document?.id ? 'active' : ''}`} key={doc.id} data-doc={doc.id} role="tab" aria-selected={doc.id === document?.id} onMouseDown={e => { if (e.button === 1) { e.preventDefault(); closeDocument(doc.id); } }}><button type="button" className="ide-tab-label" onClick={() => dispatch({ type: 'document/activate', id: doc.id })}><span>{icon('code', 14)}</span><span className="ide-tab-name">{doc.name}</span>{doc.dirty && <span className="ide-unsaved-dot" aria-label="Unsaved changes"/>}{state.analysis[doc.id]?.status === 'stale' && <span className="ide-tab-stale" title="Analysis is stale">Stale</span>}</button><button type="button" className="ide-tab-close" aria-label={`Close ${doc.name}`} onClick={() => closeDocument(doc.id)}>{icon('close', 13)}</button></div>)}</div>
      <div className="ide-toolbar"><div className="ide-toolbar-left"><button type="button" className="ide-small-button primary" disabled={!document} title={analysis?.status === 'running' ? 'Cancel analysis' : 'Analyze this file (F5 or Ctrl+Enter)'} onClick={() => document && analysisControllers.current.has(document.id) ? cancelAnalysis(document.id) : void analyzeDocument()}>{icon('play_arrow', 16)}<span className="ide-label">{analysis?.status === 'running' ? 'Cancel' : 'Analyze'}</span></button><button type="button" className="ide-small-button" disabled={!canFix || !currentFinding} title={!canFix ? 'Fix capability is unavailable.' : !currentFinding ? 'Select a finding first.' : 'Fix with AI'} onClick={() => currentFinding && startFix(currentFinding)}>{icon('auto_fix_high', 15)}<span className="ide-label">Fix with AI</span></button><button type="button" className="ide-small-button" disabled={!languageInfo?.formatter} title={languageInfo?.formatter ? `Format with ${languageInfo.formatter}` : 'No formatter is available for this language'} onClick={() => void editorRef.current?.getAction('editor.action.formatDocument')?.run()}>{icon('format_align_left', 15)}<span className="ide-label">Format</span></button><button type="button" className="ide-small-button" aria-label="Undo" title={editorHistory.undo ? 'Undo (Ctrl+Z)' : 'No editor changes to undo'} disabled={!editorHistory.undo} onClick={() => { toolbarHistoryAction.current = 'undo'; editorRef.current?.trigger('ide', 'undo', null); }}>{icon('undo', 15)}</button><button type="button" className="ide-small-button" aria-label="Redo" title={editorHistory.redo ? 'Redo (Ctrl+Y)' : 'No editor changes to redo'} disabled={!editorHistory.redo} onClick={() => { toolbarHistoryAction.current = 'redo'; editorRef.current?.trigger('ide', 'redo', null); }}>{icon('redo', 15)}</button><button type="button" className="ide-small-button" aria-label="Find" title="Find (Ctrl+F)" onClick={() => void editorRef.current?.getAction('actions.find')?.run()}>{icon('search', 15)}</button></div><div className="ide-toolbar-right"><span className="ide-grammar">{grammarLabel(document, capabilities)}</span><span className="ide-status-divider">·</span><span className="ide-time">Lexer {lexerTime === null ? '—' : `${lexerTime} ms`}</span></div></div>
      <div className="ide-editor-area"><Editor key={document?.id} height="100%" language={monacoLanguage(document?.language ?? 'cpp')} value={document?.source ?? ''} theme={`securelex-${resolved}`} onMount={onEditorMount} onChange={value => { if (document && value !== undefined && value !== document.source) { const historyAction = toolbarHistoryAction.current; toolbarHistoryAction.current = null; setEditorHistory(historyAction === 'undo' ? { undo: false, redo: true } : historyAction === 'redo' ? { undo: true, redo: false } : { undo: true, redo: false }); const running = analysisControllers.current.get(document.id); if (running) { running.abort(); analysisControllers.current.delete(document.id); } dispatch({ type: 'document/edit', id: document.id, source: value }); } }} options={{ readOnly: false, domReadOnly: false, minimap: { enabled: true }, lineNumbers: 'on', glyphMargin: true, bracketPairColorization: { enabled: false }, renderControlCharacters: true, renderLineHighlight: 'line', fontFamily: 'JetBrains Mono, monospace', fontSize: 13, lineHeight: 22, scrollBeyondLastLine: false, automaticLayout: true, cursorBlinking: 'smooth', smoothScrolling: true, tabSize: 4, wordWrap: 'off', padding: { top: 9 } }} /></div>
      {state.ui.panelOpen && <><div className="ide-resizer" role="separator" aria-label="Resize bottom panel" aria-orientation="horizontal" tabIndex={0} onPointerDown={startResize} onPointerMove={moveResize} onPointerUp={stopResize} onPointerCancel={stopResize} onKeyDown={e => { if (e.key === 'ArrowUp') { e.preventDefault(); setPanelHeight(20); } if (e.key === 'ArrowDown') { e.preventDefault(); setPanelHeight(-20); } }} /> <section className={`ide-panel ${state.ui.panelMaximised ? 'maximised' : ''}`} style={{ height: state.ui.panelMaximised ? '100%' : state.ui.panelHeight ? `${state.ui.panelHeight}px` : '48%' }}><div className="ide-panel-tabs"><div className="ide-bottom-tab-list" role="tablist" aria-label="Bottom panel">{panels.map(([id, title, count]) => <button type="button" key={id} role="tab" aria-selected={state.ui.panelTab === id} className="ide-panel-tab" onClick={() => dispatch({ type: 'ui', patch: { panelTab: id } })}>{title}{count > 0 && <span className="ide-panel-badge">{count}</span>}</button>)}</div><div className="ide-bottom-actions"><button className="ide-icon-button" type="button" aria-label={state.ui.panelMaximised ? 'Restore panel' : 'Maximise panel'} title={state.ui.panelMaximised ? 'Restore panel' : 'Maximise panel'} onClick={() => dispatch({ type: 'ui', patch: { panelMaximised: !state.ui.panelMaximised } })}>{icon(state.ui.panelMaximised ? 'keyboard_double_arrow_down' : 'keyboard_double_arrow_up', 16)}</button><button className="ide-icon-button" type="button" aria-label="Close panel" title="Close panel" onClick={() => dispatch({ type: 'ui', patch: { panelOpen: false } })}>{icon('close', 16)}</button></div></div><div className="ide-panel-content">{state.ui.panelTab === 'tokens' ? <TokensPanel result={result} analysisStatus={analysis?.status ?? 'idle'} currentVersion={document?.sourceVersion ?? null} language={document?.language ?? ''} grammarLabel={grammarLabel(document, capabilities)} selectedTokenId={selectedTokenId} inspectorOpen={state.ui.inspectorOpen} onSelect={selectToken} onToggleInspector={() => dispatch({ type: 'ui', patch: { inspectorOpen: !state.ui.inspectorOpen } })} onExport={reportToast} /> : state.ui.panelTab === 'problems' ? <ProblemsPanel diagnostics={problemDiagnostics} result={result} lexicalStatus={stageForDoc?.lexical?.lexical_status} onSelect={selectProblem} onExplain={item => requestExplanation('diagnostic', item.id)} onFix={id => { const finding = result?.security_findings.find(item => item.id === id); if (finding) startFix(finding); }} onFixAll={startFixAll} fixEnabled={canFix}/> : state.ui.panelTab === 'security' ? <SecurityPanel result={result} source={document?.source ?? ''} language={document?.language ?? ''} tokens={result?.tokens ?? []} selectedFindingId={selectedFindingId} dataFlowPathId={dataFlowPathId} onSelect={selectFinding} onToggleFlow={setDataFlowPathId} onJump={navigateRange} onFeedback={submitFalsePositive} onExplain={finding => requestExplanation('finding', finding.id)} onFix={startFix} fixEnabled={canFix}/> : state.ui.panelTab === 'explain' ? <AIExplainPanel request={explainRequest} consentRequired={Boolean(capabilities?.ai.consent_required)} consented={Boolean(capabilities?.ai.remote_consented)} onConsent={acceptConsent} onOperation={recordAIOperation}/> : state.ui.panelTab === 'agent' ? <AgentActivityPanel operationId={aiOperationId}/> : <div className="ide-empty-state">{icon('data_object', 23)}<strong>Nothing to show</strong><span>{resultForPanel}</span></div>}</div></section></>}
      </> }</section>
    </div>
    <footer className="ide-statusbar"><div className="ide-status-left"><span className="ide-status-item" title={engineLabel(health, healthError)}>{icon(health ? 'check_circle' : 'sync', 13)}{engineLabel(health, healthError)}</span><span className="ide-status-divider">|</span><span className="ide-status-item" title={dimensionLabel(result, 'lexical')}>Lex {dimensionLabel(result, 'lexical')}</span><span className="ide-status-item" title={dimensionLabel(result, 'syntax')}>Syntax {dimensionLabel(result, 'syntax')}</span><span className="ide-status-item" title={securityLabel(result)}>Security {securityLabel(result)}</span></div><div className="ide-status-right"><span className="ide-status-item" title={analysisLabel}>{analysisLabel}{result?.tokens.length ? ` · ${result.tokens.length} tokens` : ''}</span><span className="ide-status-item">{counts.errors} errors</span><span className="ide-status-divider">|</span><span className="ide-status-item">Ln {state.ui.cursor.line}, Col {state.ui.cursor.column}</span><span className="ide-status-divider">|</span><div className="ide-language-wrap"><button type="button" className="ide-status-item" aria-label={`Language ${languageLabel}; choose language`} aria-expanded={languagePicker} onClick={() => setLanguagePicker(value => !value)}>{languageLabel} {icon('arrow_drop_down', 13)}</button>{languagePicker && <div role="listbox" className="ide-language-menu">{(capabilities?.languages ?? []).map(lang => <button type="button" role="option" aria-selected={lang.id === document?.language} key={lang.id} onClick={() => setLanguage(lang.id)}>{lang.name}</button>)}</div>}</div><span className="ide-status-item">{document ? displayEol(document.source) : 'LF'}</span><span className="ide-status-item">UTF-8</span></div></footer>
    {state.ui.paletteOpen && <div className="ide-overlay" onMouseDown={e => { if (e.target === e.currentTarget) dispatch({ type: 'ui', patch: { paletteOpen: false } }); }}><div className="ide-palette" role="dialog" aria-modal="true" aria-label="Command Palette"><input ref={paletteInput} className="ide-palette-input" value={query} onChange={e => { setQuery(e.target.value); setSelected(0); }} placeholder="Type a command name" aria-label="Search commands" /><div className="ide-palette-results" role="listbox">{filteredCommands.map((command, index) => <button type="button" role="option" aria-selected={index === selected} key={command.id} className="ide-palette-option" onMouseEnter={() => setSelected(index)} onClick={() => runCommand(command)}><span>{command.title}</span>{command.keybinding && <kbd>{command.keybinding}</kbd>}</button>)}{!filteredCommands.length && <div className="ide-tree-message">No matching commands.</div>}</div></div></div>}
    <SettingsModal open={state.ui.settingsOpen} capabilities={capabilities} scale={state.ui.interfaceScale} theme={resolved} autoAnalyze={autoAnalyze} consentBusy={consentBusy} onScale={value => dispatch({ type: 'ui', patch: { interfaceScale: clampScale(value) } })} onTheme={toggleTheme} onAutoAnalyze={setAutoAnalyze} onConsent={value => void setConsent(value)} onClose={() => dispatch({ type: 'ui', patch: { settingsOpen: false } })}/>
    {fixFinding && fixDocId && state.documents.find(item => item.id === fixDocId) && <FixWorkflowModal finding={fixFinding} documentId={fixDocId} activeDocumentId={state.activeDocId} source={state.documents.find(item => item.id === fixDocId)!.source} sourceVersion={state.documents.find(item => item.id === fixDocId)!.sourceVersion} language={state.documents.find(item => item.id === fixDocId)!.language} filename={state.documents.find(item => item.id === fixDocId)!.name} initialFixAll={fixAllRequested} sessionId={sessionId.current} aiReady={canFix} remoteConsentRequired={Boolean(capabilities?.ai.consent_required)} remoteConsented={Boolean(capabilities?.ai.remote_consented)} onConsent={acceptConsent} onSourceApplied={onFixSourceApplied} onUndoApplied={onFixUndo} onClose={closeFix} onAskAI={() => setBuildDrawerOpen(true)} onActions={updateFixActions}/>}
    <BuildAIDrawer open={buildDrawerOpen} capabilities={capabilities} sessionId={sessionId.current} onClose={() => setBuildDrawerOpen(false)} onConsent={acceptConsent} onCandidate={openGeneratedCandidate}/>
    {toast && <div role="status" className={`ide-toast ${toast.error ? 'error' : ''}`}>{toast.message}</div>}</main>;
}
