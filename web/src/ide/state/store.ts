import type { AnalysisResultV2, DiagnosticV2, TokenV2, PatchProposal } from '../../api/client';

export type DocumentLanguage = string;

// Canonical 10-State Analysis Status Model
export type CanonicalAnalysisStatus =
  | 'not_analyzed'
  | 'queued'
  | 'running'
  | 'passed'
  | 'failed_source_diagnostics'
  | 'execution_failed'
  | 'warning'
  | 'skipped'
  | 'cancelled'
  | 'outdated';

export type AnalysisStatus = 'idle' | 'running' | 'ok' | 'stale' | 'error';
export type Activity = 'explorer' | 'samples' | 'search' | 'ast' | 'security' | 'safetylab';
export type PanelTab = 'tokens' | 'problems' | 'security' | 'explain' | 'agent';

// ── 1. Workspace and project files ───────────────────────────────────────────
export interface WorkspaceFile {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  language?: string;
  children?: WorkspaceFile[];
}

// ── 2. Editor documents ───────────────────────────────────────────────────────
export interface IDEDocument {
  id: string;
  name: string;
  language: DocumentLanguage;
  source: string;
  savedSource?: string;
  sourceVersion: number;
  dirty: boolean;
  origin: 'new' | 'opened' | 'sample';
  sampleId?: string;
}

// ── 3. Document version and content hash ──────────────────────────────────────
export interface DocumentVersionInfo {
  documentId: string;
  sourceVersion: number;
  sourceHash?: string;
  timestamp: number;
}

// ── 4. Lexical analysis runs ──────────────────────────────────────────────────
export interface AnalysisRunRecord {
  runId: string;
  documentId: string;
  sourceVersion: number;
  sourceHash: string;
  language: string;
  startedAt: number;
  completedAt: number;
  status: CanonicalAnalysisStatus;
  stagesExecuted: string[];
}

// ── 5. Tokens ────────────────────────────────────────────────────────────────
export type TokenModel = TokenV2;

export interface TokenCounts {
  total: number;
  valid: number;
  invalid: number;
  unknown: number;
}

export function deriveTokenCounts(tokens: TokenV2[] | null | undefined): TokenCounts {
  if (!tokens || tokens.length === 0) {
    return { total: 0, valid: 0, invalid: 0, unknown: 0 };
  }
  let valid = 0;
  let invalid = 0;
  let unknown = 0;
  for (const t of tokens) {
    if (t.lexical_status === 'valid') {
      valid++;
    } else if (t.lexical_status === 'invalid') {
      invalid++;
    } else {
      unknown++;
    }
  }
  return {
    total: tokens.length,
    valid,
    invalid,
    unknown,
  };
}

// ── 6. Diagnostics ───────────────────────────────────────────────────────────
export type DiagnosticModel = DiagnosticV2;

export interface DiagnosticsCounts {
  total: number;
  errors: number;
  warnings: number;
  info: number;
}

export function deriveDiagnosticsCounts(
  syntaxDiags: DiagnosticV2[] | null | undefined,
  semanticDiags: DiagnosticV2[] | null | undefined
): DiagnosticsCounts {
  const all = [...(syntaxDiags || []), ...(semanticDiags || [])];
  let errors = 0;
  let warnings = 0;
  let info = 0;
  for (const d of all) {
    const sev = (d.severity || '').toLowerCase();
    if (sev === 'error' || sev === 'critical' || sev === 'fatal') {
      errors++;
    } else if (sev === 'warning' || sev === 'warn') {
      warnings++;
    } else {
      info++;
    }
  }
  return {
    total: all.length,
    errors,
    warnings,
    info,
  };
}

// ── 7. Security findings ─────────────────────────────────────────────────────
export type SecurityFindingV2 = AnalysisResultV2['security_findings'][number];

// ── 8. Pipeline execution ────────────────────────────────────────────────────
export interface PipelineExecutionState {
  status: CanonicalAnalysisStatus;
  totalDurationMs: number;
  passedStages: number;
  totalStages: number;
  stages: StageExecutionResult[];
}

// ── 9. Individual agent stage results ────────────────────────────────────────
export interface StageExecutionResult {
  stageId: string;
  name: string;
  agent: string;
  status: CanonicalAnalysisStatus;
  durationMs: number;
  summary: string;
  error?: string;
}

// ── 10. AI conversations ─────────────────────────────────────────────────────
export interface AIConversationMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: number;
  codeSnippets?: string[];
  proposal?: PatchProposal;
  targetContext?: {
    file: string;
    stage?: string;
    findingTitle?: string;
    line?: number;
    col?: number;
  };
}

// ── 11. Proposed code changes ────────────────────────────────────────────────
export interface ProposedCodeChange {
  proposalId: string;
  targetFindingId?: string;
  sourceVersion: number;
  summary: string;
  diff: string;
  patch: string;
  status: 'pending' | 'accepted' | 'rejected' | 'applied';
}

// ── 12. Verification results ──────────────────────────────────────────────────
export interface VerificationResult {
  verified: boolean;
  syntaxValid: boolean;
  diagnosticsCount: number;
  securityCount: number;
  regressions: string[];
  details: string;
}

export interface DocumentAnalysis {
  result: AnalysisResultV2 | null;
  forSourceVersion: number | null;
  status: AnalysisStatus;
  abort: AbortController | null;
}

export interface IDEState {
  documents: IDEDocument[];
  activeDocId: string | null;
  analysis: Record<string, DocumentAnalysis>;
  ui: {
    activity: Activity;
    sidebarOpen: boolean;
    sidebarWidth: number;
    panelTab: PanelTab;
    panelHeight: number;
    panelMaximised: boolean;
    panelOpen: boolean;
    inspectorOpen: boolean;
    settingsOpen: boolean;
    paletteOpen: boolean;
    interfaceScale: number;
    cursor: { line: number; column: number };
    engineStatus: string;
    safetyRunning: boolean;
  };
}

export const initialIDEState: IDEState = {
  documents: [],
  activeDocId: null,
  analysis: {},
  ui: {
    activity: 'explorer',
    sidebarOpen: true,
    sidebarWidth: 240,
    panelTab: 'tokens',
    panelHeight: 0,
    panelMaximised: false,
    panelOpen: true,
    inspectorOpen: false,
    settingsOpen: false,
    paletteOpen: false,
    interfaceScale: 100,
    cursor: { line: 1, column: 1 },
    engineStatus: 'Loading',
    safetyRunning: false,
  },
};

export type IDEAction =
  | { type: 'document/add'; document: IDEDocument }
  | { type: 'document/edit'; id: string; source: string }
  | { type: 'document/save'; id: string }
  | { type: 'document/rename'; id: string; name: string }
  | { type: 'document/language'; id: string; language: string }
  | { type: 'document/activate'; id: string }
  | { type: 'document/move'; id: string; toIndex: number }
  | { type: 'document/remove'; id: string }
  | { type: 'analysis/start'; id: string; abort: AbortController }
  | { type: 'analysis/success'; id: string; result: AnalysisResultV2; version: number }
  | { type: 'analysis/error'; id: string }
  | { type: 'analysis/cancel'; id: string }
  | { type: 'panel/toggle' }
  | { type: 'panel/close' }
  | { type: 'panel/maximise' }
  | { type: 'sidebar/toggle' }
  | { type: 'ui'; patch: Partial<IDEState['ui']> };

const emptyAnalysis = (): DocumentAnalysis => ({
  result: null,
  forSourceVersion: null,
  status: 'idle',
  abort: null,
});

export function ideReducer(state: IDEState, action: IDEAction): IDEState {
  switch (action.type) {
    case 'document/add':
      return {
        ...state,
        documents: [...state.documents, action.document],
        activeDocId: action.document.id,
        analysis: { ...state.analysis, [action.document.id]: emptyAnalysis() },
      };
    case 'document/edit':
      return {
        ...state,
        documents: state.documents.map((doc) =>
          doc.id === action.id
            ? {
                ...doc,
                source: action.source,
                sourceVersion: doc.sourceVersion + 1,
                dirty: action.source !== (doc.savedSource ?? doc.source),
              }
            : doc
        ),
        analysis: state.analysis[action.id]
          ? {
              ...state.analysis,
              [action.id]: { ...state.analysis[action.id], status: 'stale', abort: null },
            }
          : state.analysis,
      };
    case 'document/save':
      return {
        ...state,
        documents: state.documents.map((doc) =>
          doc.id === action.id
            ? {
                ...doc,
                savedSource: doc.source,
                dirty: false,
              }
            : doc
        ),
      };
    case 'document/rename':
      return {
        ...state,
        documents: state.documents.map((doc) =>
          doc.id === action.id ? { ...doc, name: action.name } : doc
        ),
      };
    case 'document/language':
      return {
        ...state,
        documents: state.documents.map((doc) =>
          doc.id === action.id ? { ...doc, language: action.language } : doc
        ),
        analysis: state.analysis[action.id]
          ? {
              ...state.analysis,
              [action.id]: {
                ...state.analysis[action.id],
                status: state.analysis[action.id].result ? 'stale' : 'idle',
                abort: null,
              },
            }
          : state.analysis,
      };
    case 'document/activate':
      return state.documents.some((doc) => doc.id === action.id)
        ? { ...state, activeDocId: action.id }
        : state;
    case 'document/move': {
      const from = state.documents.findIndex((doc) => doc.id === action.id);
      if (from < 0) return state;
      const documents = [...state.documents];
      const [document] = documents.splice(from, 1);
      documents.splice(Math.max(0, Math.min(action.toIndex, documents.length)), 0, document);
      return { ...state, documents };
    }
    case 'document/remove': {
      const index = state.documents.findIndex((doc) => doc.id === action.id);
      const documents = state.documents.filter((doc) => doc.id !== action.id);
      const { [action.id]: _removed, ...analysis } = state.analysis;
      return {
        ...state,
        documents,
        analysis,
        activeDocId:
          state.activeDocId === action.id
            ? (documents[Math.max(0, index - 1)]?.id ?? documents[0]?.id ?? null)
            : state.activeDocId,
      };
    }
    case 'analysis/start':
      if (!state.documents.some((doc) => doc.id === action.id)) return state;
      return {
        ...state,
        analysis: {
          ...state.analysis,
          [action.id]: {
            ...(state.analysis[action.id] ?? emptyAnalysis()),
            status: 'running',
            abort: action.abort,
          },
        },
      };
    case 'analysis/success': {
      const document = state.documents.find((doc) => doc.id === action.id);
      if (
        !document ||
        document.sourceVersion !== action.version ||
        action.result.source_version !== action.version
      )
        return state;
      return {
        ...state,
        analysis: {
          ...state.analysis,
          [action.id]: {
            result: action.result,
            forSourceVersion: action.version,
            status: 'ok',
            abort: null,
          },
        },
      };
    }
    case 'analysis/error':
      return {
        ...state,
        analysis: {
          ...state.analysis,
          [action.id]: {
            ...(state.analysis[action.id] ?? emptyAnalysis()),
            status: 'error',
            abort: null,
          },
        },
      };
    case 'analysis/cancel': {
      const previous = state.analysis[action.id] ?? emptyAnalysis();
      return {
        ...state,
        analysis: {
          ...state.analysis,
          [action.id]: { ...previous, status: previous.result ? 'stale' : 'idle', abort: null },
        },
      };
    }
    case 'panel/toggle':
      return {
        ...state,
        ui: { ...state.ui, panelOpen: !state.ui.panelOpen, panelMaximised: false },
      };
    case 'panel/close':
      return { ...state, ui: { ...state.ui, panelOpen: false, panelMaximised: false } };
    case 'panel/maximise':
      return {
        ...state,
        ui: { ...state.ui, panelOpen: true, panelMaximised: !state.ui.panelMaximised },
      };
    case 'sidebar/toggle':
      return { ...state, ui: { ...state.ui, sidebarOpen: !state.ui.sidebarOpen } };
    case 'ui':
      return { ...state, ui: { ...state.ui, ...action.patch } };
  }
}

export function selectActiveDocument(state: IDEState): IDEDocument | null {
  return state.documents.find((doc) => doc.id === state.activeDocId) ?? null;
}

export function selectIsStale(state: IDEState, id = state.activeDocId): boolean {
  if (!id) return false;
  const current = state.documents.find((doc) => doc.id === id);
  const analysis = state.analysis[id];
  return (
    analysis?.status === 'stale' ||
    Boolean(current && analysis?.result && analysis.forSourceVersion !== current.sourceVersion)
  );
}

export function selectCounts(state: IDEState) {
  return {
    documents: state.documents.length,
    dirty: state.documents.filter((doc) => doc.dirty).length,
  };
}

export function selectAnalysisCounts(state: IDEState) {
  const analysis = state.activeDocId ? state.analysis[state.activeDocId]?.result : null;
  return {
    tokens: analysis?.tokens.length ?? 0,
    problems:
      (analysis?.syntax_diagnostics.length ?? 0) + (analysis?.semantic_diagnostics.length ?? 0),
    security: analysis?.security_findings.length ?? 0,
    errors: [
      ...(analysis?.syntax_diagnostics ?? []),
      ...(analysis?.semantic_diagnostics ?? []),
    ].filter((item) => ['error', 'critical', 'high'].includes(item.severity.toLowerCase())).length,
  };
}

export interface SavedIDEState {
  documents: IDEDocument[];
  activeDocId: string | null;
  panelHeight: number;
  sidebarWidth: number;
  interfaceScale: number;
}

export function hydrateIDEState(raw: string | null): IDEState {
  if (!raw) return initialIDEState;
  try {
    const saved = JSON.parse(raw) as Partial<SavedIDEState>;
    if (!Array.isArray(saved.documents)) return initialIDEState;
    const documents = saved.documents
      .filter((doc): doc is IDEDocument =>
        Boolean(
          doc &&
          typeof doc.id === 'string' &&
          typeof doc.name === 'string' &&
          typeof doc.source === 'string' &&
          typeof doc.language === 'string'
        )
      )
      .map((doc) => ({
        ...doc,
        savedSource: typeof doc.savedSource === 'string' ? doc.savedSource : doc.source,
        sourceVersion: Number.isFinite(doc.sourceVersion) ? doc.sourceVersion : 1,
        dirty: Boolean(doc.dirty),
        origin: (doc.origin === 'sample' || doc.origin === 'opened'
          ? doc.origin
          : 'new') as IDEDocument['origin'],
      }));
    return {
      ...initialIDEState,
      documents,
      activeDocId: documents.some((doc) => doc.id === saved.activeDocId)
        ? (saved.activeDocId ?? null)
        : (documents[0]?.id ?? null),
      analysis: Object.fromEntries(documents.map((doc) => [doc.id, emptyAnalysis()])),
      ui: {
        ...initialIDEState.ui,
        panelHeight: Number.isFinite(saved.panelHeight) ? Number(saved.panelHeight) : 0,
        sidebarWidth: Number.isFinite(saved.sidebarWidth)
          ? Math.max(180, Math.min(420, Number(saved.sidebarWidth)))
          : 240,
        interfaceScale: clampScale(Number(saved.interfaceScale) || 100),
      },
    };
  } catch {
    return initialIDEState;
  }
}

export function serializeIDEState(state: IDEState): string {
  const saved: SavedIDEState = {
    documents: state.documents.map((doc) => ({ ...doc })),
    activeDocId: state.activeDocId,
    panelHeight: state.ui.panelHeight,
    sidebarWidth: state.ui.sidebarWidth,
    interfaceScale: state.ui.interfaceScale,
  };
  return JSON.stringify(saved);
}

export function clampScale(scale: number): number {
  return Math.max(90, Math.min(125, Math.round(scale / 5) * 5));
}

export function deriveCanonicalAnalysisStatus(
  doc: IDEDocument | null | undefined,
  analysis: DocumentAnalysis | null | undefined
): CanonicalAnalysisStatus {
  if (!doc) return 'not_analyzed';
  if (!analysis || (analysis.status === 'idle' && !analysis.result)) {
    return 'not_analyzed';
  }
  if (analysis.status === 'running') return 'running';
  if (analysis.status === 'error') return 'execution_failed';
  if (analysis.status === 'stale') return 'outdated';
  if (analysis.result) {
    if (analysis.forSourceVersion !== null && analysis.forSourceVersion !== doc.sourceVersion) {
      return 'outdated';
    }
    const tokens = analysis.result.tokens || [];
    const hasInvalidTokens = tokens.some((t) => t.lexical_status === 'invalid');
    const allDiags = [
      ...(analysis.result.syntax_diagnostics || []),
      ...(analysis.result.semantic_diagnostics || []),
    ];
    const hasErrors = allDiags.some(
      (d) => d.severity.toLowerCase() === 'error' || d.severity.toLowerCase() === 'critical'
    );
    const hasCriticalSecurity = (analysis.result.security_findings || []).some(
      (f) => f.severity.toLowerCase() === 'critical' || f.severity.toLowerCase() === 'high'
    );
    if (hasInvalidTokens || hasErrors || hasCriticalSecurity) {
      return 'failed_source_diagnostics';
    }
    const hasWarnings =
      allDiags.some((d) => d.severity.toLowerCase() === 'warning') ||
      (analysis.result.security_findings || []).length > 0;
    if (hasWarnings) {
      return 'warning';
    }
    return 'passed';
  }
  return 'not_analyzed';
}
