import { Range } from '../utils/offsets';

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type Label = 'MALICIOUS' | 'SUSPICIOUS';
export type TaintStepKind = 'source' | 'propagate' | 'sink' | 'sanitizer_missing';

export interface Edit {
  range: Range;
  new_text: string;
}

export interface VerificationResult {
  syntax_ok: boolean;
  finding_gone: boolean;
  new_findings: string[];
  verified: boolean;
  notes: string;
}

export interface Fix {
  id: string;
  finding_id: string;
  title: string;
  description: string;
  confidence: 'safe' | 'review' | 'manual';
  kind: string;
  edits: Edit[];
  verification: VerificationResult;
}

export interface TaintPathStep {
  step: TaintStepKind;
  range: Range;
  text: string;
  note: string;
}

export interface Finding {
  id: string;
  rule_id: string;
  title: string;
  cwe: string;
  severity: Severity;
  label: Label;
  confidence: number;
  range: Range;
  message: string;
  explanation: string;
  evidence: Record<string, any>;
  taint_path: TaintPathStep[];
  fixes: Fix[];
  sources: string[];
  suppressed?: boolean;
  suppression_reason?: string | null;
  kind?: 'security' | 'lexical' | 'syntax';
  attack?: string[] | null;
  priority?: number;
  exploitability?: number;
  simple_explanation?: string | null;
  detailed_explanation?: string | null;
}

export interface AnalysisSummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  score: number;
  tokens_total: number;
  tokens_malicious: number;
  tokens_suspicious: number;
  lexical_errors?: number;
  syntax_errors?: number;
}

export interface EngineMetadata {
  ml_mode: 'on' | 'off';
  ml_model_id: string;
  taint: string;
  version: string;
  elapsed_ms: number;
  parser?: string;
}

export interface AgentTraceStep {
  step: number;
  agent: string;
  stage: string;
  action: string;
  args_summary: string;
  reason: string;
  observation_summary: string;
  decision_source: 'llm' | 'rules';
  ms: number;
  accepted: boolean;
  rejection_reason?: string;
}

export interface AgentStatus {
  mode: 'off' | 'rules';
  model: string;
  model_present: boolean;
  fallback_active: boolean;
  message?: string;
}

export interface AnalysisResult {
  language: string;
  filename: string;
  findings: Finding[];
  tokens: TokenInfo[];
  summary: AnalysisSummary;
  engine: EngineMetadata;
  trace?: AgentTraceStep[];
  agent_meta?: Record<string, any>;
}

export interface TokenInfo {
  token: string;
  token_type: string;
  range: Range;
  label: string;
  score: number;
  // Backward-compatibility aliases are accepted to keep older cached API payloads usable.
  text?: string;
  line?: number;
  col?: number;
  confidence?: number;
  utf16_offset?: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  ml_mode: 'on' | 'off';
  ml_model_id: string;
}

export interface LanguageInfo {
  id: string;
  display_name: string;
  extensions: string[];
  monaco_id: string;
}

export interface SampleItem {
  id: string;
  title: string;
  category: string;
  language: string;
  filename: string;
  code: string;
  description: string;
  kind?: string;
  level?: string | null;
  topic?: string | null;
  summary?: string | null;
  notes?: string[];
  expect?: { findings?: Array<{ rule_id: string; line?: number }>; min_findings?: number };
  demo_order?: number | null;
  senior?: { tool: string; flagged: boolean | null; detail: string; note?: string };
}

export interface AnalyzeOptions {
  fixes?: boolean;
  ml?: boolean;
  include_tokens?: boolean;
  include_suppressed?: boolean;
  agent?: 'off' | 'rules' | 'local';
}

export interface AnalyzeRequest {
  source: string;
  language?: string | null;
  filename?: string | null;
  options?: AnalyzeOptions;
}

export interface FixRequest {
  source: string;
  language?: string;
  finding_id: string;
  fix_id: string;
  filename?: string;
}

export interface FixResponse {
  new_source: string;
  diff: string;
  verification: VerificationResult;
  new_result?: AnalysisResult;
}

export interface FixAllRequest {
  source: string;
  language?: string;
  filename?: string;
  allow_review?: boolean;
  session_id?: string;
  source_version?: number;
  approved?: boolean;
  approved_diff?: string;
}

export interface SkippedFixItem {
  fix_id: string;
  reason: string;
}

export interface FixAllResponse {
  new_source: string;
  applied: string[];
  skipped: SkippedFixItem[];
  diff: string;
  score_before: number;
  score_after: number;
}

export interface FeedbackRequest {
  finding_fingerprint: string;
  rule_id: string;
  language: string;
  verdict?: string;
  snippet?: string;
}

export interface FeedbackResponse {
  saved: boolean;
}

export interface MLInsightsRequest {
  source: string;
  language?: string;
  token_index: number;
}

export interface MLInsightsResponse {
  ml_mode: string;
  token_index?: number;
  token_text?: string | null;
  predicted_label?: string | null;
  probabilities?: Record<string, number>;
  feature_group_drops?: Record<string, number>;
  error?: string | null;
}

export interface AnalysisDimensionV2 {
  status: 'ok' | 'issues' | 'incomplete' | 'unavailable';
  reason?: string | null;
}
export interface TokenV2 {
  id: string;
  language: string;
  lexeme: string;
  token_type: string;
  category: string;
  start_offset: number;
  end_offset: number;
  start_offset_codepoint: number;
  end_offset_codepoint: number;
  start_line: number;
  start_column: number;
  end_line: number;
  end_column: number;
  lexical_status: 'valid' | 'invalid' | 'unknown';
  diagnostic_ids: string[];
}
export interface DiagnosticV2 {
  id: string;
  language: string;
  range: Range;
  category: 'lexical' | 'syntax' | 'semantic' | 'security' | 'quality';
  severity: string;
  message: string;
  related_evidence: string[];
  produced_by: string;
  certainty: 'definitive' | 'heuristic' | 'incomplete';
}
export interface TaintPathV2 {
  id: string;
  steps: Array<{
    range: Range;
    text: string;
    role: 'source' | 'propagation' | 'sanitizer' | 'sink';
    note: string;
  }>;
  complete: boolean;
  limitation: string | null;
}
export interface AnalysisResultV2 {
  analysis_id: string;
  source_hash: string;
  source_version: number;
  language: string;
  lexical_status: AnalysisDimensionV2;
  syntax_status: AnalysisDimensionV2;
  semantic_status: AnalysisDimensionV2;
  tokens: TokenV2[];
  lexical_summary: Record<string, Record<string, number>>;
  syntax_diagnostics: DiagnosticV2[];
  semantic_diagnostics: DiagnosticV2[];
  security_findings: Array<
    Omit<Finding, 'cwe'> & {
      cwe: string[];
      taint_path_id: string | null;
      certainty: 'definitive' | 'heuristic' | 'incomplete';
      remediation: string | null;
      tool_provenance: string[];
      safe_pattern: string | null;
      detectors_fired: string[];
    }
  >;
  taint_paths: TaintPathV2[];
  quality: Array<{
    id: string;
    kind: string;
    range: Range | null;
    value: unknown;
    evidence: string[];
    measured: boolean;
  }>;
  tools: Array<{
    name: string;
    kind: string;
    available: boolean;
    version: string | null;
    executed: boolean;
    duration_ms: number | null;
    status: 'ok' | 'failed' | 'timeout' | 'unavailable' | 'skipped';
    reason: string | null;
  }>;
  timing: Record<string, number>;
  warnings: string[];
  omissions: string[];
  trace?: Array<{
    step_number?: number;
    agent: string;
    stage: string;
    action: string;
    args_summary?: string;
    reason?: string;
    observation_summary?: string;
    decision_source?: string;
    ms?: number;
    accepted?: boolean;
    rejection_reason?: string | null;
  }>;
  agent_meta?: {
    mode?: string;
    total_steps?: number;
    llm_calls?: number;
    elapsed_ms?: number;
    structure_quality?: number;
    verified_fixes?: number;
    [key: string]: unknown;
  };
}
// Supported stages contract: 'lexical' | 'syntax' | 'security' | 'quality'
export type AnalysisStage = 'lexical' | 'syntax' | 'security' | 'quality' | 'semantic';
export interface AnalyzeV2Request {
  source: string;
  language?: string | null;
  filename?: string | null;
  api_version: 2;
  source_version: number;
  include_ast?: boolean;
  options: {
    include_tokens: boolean;
    stages: AnalysisStage[];
    fixes?: boolean;
    ml?: boolean;
    include_suppressed?: boolean;
    agent?: 'off' | 'rules' | 'local';
  };
}
export interface FormatSourceResponse {
  source: string;
  formatter: string;
}
export interface APIErrorBody {
  code: string;
  message: string;
  status: number;
}
export interface ASTNodeResponse {
  root_id: string;
  nodes: Array<{
    id: string;
    type: string;
    field_name: string | null;
    range: Range;
    parent_id: string | null;
    child_ids: string[];
    text_preview: string;
    token_ids: string[];
    finding_ids: string[];
  }>;
  truncated: boolean;
  node_limit: number;
  depth_limit: number;
}
export interface StageAnalysisResponse {
  analysis_id: string;
  source_hash: string;
  source_version: number;
  language: string;
  stage: string;
  lexical_status: AnalysisDimensionV2;
  syntax_status: AnalysisDimensionV2;
  semantic_status: AnalysisDimensionV2;
  tokens?: TokenV2[];
  lexical_summary?: Record<string, Record<string, number>>;
  ast: ASTNodeResponse | null;
  diagnostics: DiagnosticV2[];
  findings: AnalysisResultV2['security_findings'];
  taint_paths: AnalysisResultV2['taint_paths'];
  tools: AnalysisResultV2['tools'];
  warnings: string[];
  omissions: string[];
}
export interface PatchProposalRequest {
  source: string;
  source_version: number;
  language?: string;
  filename?: string;
  target?: { kind: 'finding' | 'diagnostic' | 'token'; id: string };
  target_finding_id?: string;
  session_id?: string;
  remote_consent?: boolean;
  origin?: 'rule' | 'ai';
}
export interface PatchProposal {
  id: string;
  source_hash: string;
  source_version: number;
  target_finding_id: string;
  target_kind?: 'finding' | 'diagnostic' | 'token';
  target_signature?: string | null;
  origin: 'rule' | 'ai';
  edits: Edit[];
  diff: string;
  rationale: string;
  expected_outcome: string;
  assumptions: string[];
  risks: string[];
  created_at: string;
}
export interface VerificationItem {
  id?: string;
  rule_id?: string;
  title?: string;
  message?: string;
  reason?: string;
  check?: string;
  [key: string]: unknown;
}
export interface VerificationToolStatus {
  name: string;
  available: boolean;
  status: string;
  version?: string | null;
  reason?: string | null;
}
export interface FixVerificationReport {
  resolved: VerificationItem[];
  remaining: VerificationItem[];
  introduced: VerificationItem[];
  unverified: VerificationItem[];
  outcome:
    'Verified for specified checks' | 'Partially verified' | 'Verification failed' | 'Inconclusive';
  tools: VerificationToolStatus[];
  quality_delta: Record<string, number>;
  quality_evaluation?: Record<string, unknown>;
}
export interface PatchActionRequest {
  source: string;
  source_version: number;
  language?: string;
  filename?: string;
  session_id?: string;
  proposal: PatchProposal;
  approved?: boolean;
}
export interface UndoRequest {
  session_id?: string;
}
export interface FixAllPreview {
  new_source: string;
  applied: string[];
  skipped: SkippedFixItem[];
  diff: string;
  score_before: number;
  score_after: number;
  source_version?: number;
  applied_to_source?: boolean;
}
export interface SafetyRunRequest {
  scenario_id: string;
  language: string;
  mode: 'HARNESS' | 'LIVE';
  config?: { session_id?: string; remote_consent?: boolean };
}
export interface ReportExportRequest {
  kind: 'analysis' | 'safety_run';
  format: 'json' | 'markdown' | 'html' | 'csv';
  source?: string | null;
  language?: string;
  filename?: string;
  source_version?: number;
  run_id?: string | null;
}
export interface SafetyScenario {
  id: string;
  title: string;
  risk: string;
  description: string;
  languages: string[];
  expected_safe_behavior: string;
}
export interface SafetyRunResult {
  run_id: string;
  scenario_id: string;
  source_hash: string;
  mode_label: string;
  status?: 'running' | 'completed' | 'failed' | 'cancelled';
  configuration: { language: string; mode: 'HARNESS' | 'LIVE'; [key: string]: unknown };
  scenario: SafetyScenario;
  timeline: Array<{
    id: string;
    timestamp: string;
    agent: string;
    action: string;
    tool: string | null;
    decision_source: string;
    outcome: string;
    error?: string | null;
    duration?: number;
  }>;
  agent_behavior: {
    response?: string;
    requested_operations?: unknown[];
    proposed_changes?: unknown[];
    [key: string]: unknown;
  };
  operations: Array<{
    tool: string;
    operation: string;
    allowed: boolean;
    denial?: string | null;
    policy?: string | null;
    [key: string]: unknown;
  }>;
  independent_verification: {
    before?: unknown;
    after?: unknown;
    seeded_findings_preserved?: boolean | null;
    triage_findings_preserved?: boolean | null;
    patch_integrity?: unknown;
    tests?: unknown;
    [key: string]: unknown;
  };
  assertions: Array<{ name: string; passed: boolean; detail: string }>;
  outcome:
    | 'Attack resisted'
    | 'Attack contained'
    | 'Attack succeeded'
    | 'Inconclusive'
    | 'Verification failed'
    | null;
  limitations: string[];
}

export interface AIConsentRequest {
  session_id: string;
  consent: boolean;
}
export interface AIExplainV2Request {
  session_id: string;
  remote_consent?: boolean;
  target: 'token' | 'diagnostic' | 'finding' | 'file' | 'patch';
  source: string;
  language: string;
  target_id?: string | null;
  source_version?: number;
  patch?: string | null;
}
export interface AIGenerateRequest {
  session_id: string;
  remote_consent?: boolean;
  language: 'python' | 'java' | 'javascript' | 'cpp';
  requirements: string[];
}
export interface AgentEvent {
  id: string;
  timestamp: string;
  operation_id: string;
  agent: string;
  action: string;
  tool: string | null;
  argument_summary: string;
  decision_source: string;
  outcome: string;
  duration: number;
  error?: string | null;
  subject_type?: AIExplainV2Request['target'] | null;
  subject_id?: string | null;
  provider?: string | null;
  model?: string | null;
  tokens?: number | null;
}
export interface AIExplainV2Response {
  operation_id: string;
  explanation: string;
  provider: string;
  processing_location: string;
  provenance: Array<Record<string, unknown>>;
  limitations: string[];
  grounded?: boolean;
  deterministic_fallback?: boolean;
}
export interface AIGenerateResponse {
  operation_id: string;
  language: string;
  code: string;
  explanation: string;
  assumptions: string[];
  requirements_checklist: Array<{
    requirement: string;
    status: 'met' | 'unmet' | 'unverified';
    evidence: string;
  }>;
  analysis: AnalysisResultV2;
  executed: boolean;
  provider: string;
  processing_location: string;
  limitations: string[];
}

export interface AIChatContext {
  file?: string;
  language?: string;
  source_version?: number;
  selected_range?: { start_line: number; start_col: number; end_line?: number; end_col?: number };
  selected_code?: string;
  selected_token?: Record<string, unknown>;
  stage?: string;
  diagnostic?: Record<string, unknown>;
  finding?: Record<string, unknown>;
  findings_count?: number;
}

export interface AIChatRequest {
  session_id: string;
  remote_consent?: boolean;
  message: string;
  source?: string;
  language?: string;
  history?: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>;
  context?: AIChatContext;
}

export interface AIChatResponse {
  operation_id: string;
  reply: string;
  code_snippets: string[];
  provider: string;
  model: string;
}


const API_BASE = '/api';

export class ApiError extends Error {
  code: string;
  status: number;
  detail?: string;
  constructor(message: string, status = 0, detail?: string, code = 'request_error') {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  responseKind: 'json' | 'blob' = 'json'
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { credentials: 'include', ...options, headers });
    if (!res.ok) {
      let detail = res.statusText;
      let code = 'http_error';
      try {
        const errorJson = await res.json();
        const body =
          errorJson.detail && typeof errorJson.detail === 'object' ? errorJson.detail : errorJson;
        detail = body.message || body.detail || detail;
        code = body.code || code;
      } catch {
        // use fallback
      }
      throw new ApiError(
        detail || `Request failed with status ${res.status}`,
        res.status,
        detail,
        code
      );
    }
    return (responseKind === 'blob' ? await res.blob() : await res.json()) as T;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw err;
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err.message || 'Network error or backend unreachable',
      0,
      undefined,
      'network_error'
    );
  }
}

export interface AITestConnectionResponse {
  ok: boolean;
  provider: string;
  latency_ms: number;
  model: string | null;
  available_models: string[];
  error: string | null;
}

export interface AICapabilities {
  ai: {
    provider: string;
    configured: boolean;
    reachable: boolean | null;
    model: string | null;
    processing_location: string;
    consent_required: boolean;
    remote_consented: boolean;
    model_present?: boolean;
    configured_model_present?: boolean | null;
    installed_models?: string[];
    setup_message?: string | null;
  };
  features: { build_with_ai: boolean; fix_with_ai: boolean; fix_ai?: boolean; fix_rule?: boolean };
  languages?: Array<{ id: string; name: string; extensions?: string[]; monaco_id?: string }>;
  tools?: Array<{
    name: string;
    available: boolean;
    status: string;
    version?: string | null;
    reason?: string | null;
  }>;
}
export interface CapabilitiesResponse extends AICapabilities {
  version: string;
  languages: Array<{
    id: string;
    name: string;
    extensions: string[];
    monaco_id: string;
    lexer: Record<string, unknown>;
    parser: Record<string, unknown>;
    semantic_tools: string[];
    security_tools: string[];
    formatter: string | null;
  }>;
  tools: Array<{
    name: string;
    kind: string;
    available: boolean;
    version: string | null;
    executed: boolean;
    duration_ms: number | null;
    status: string;
    reason: string | null;
  }>;
  limits: Record<string, unknown>;
  features: { build_with_ai: boolean; fix_with_ai: boolean; [key: string]: unknown };
}

export const apiClient = {
  analyzeV2: (req: AnalyzeV2Request, signal?: AbortSignal) =>
    request<AnalysisResultV2>('/analyze', { method: 'POST', body: JSON.stringify(req), signal }),
  analyzeStageV2: (stage: 'lexical' | 'syntax', req: AnalyzeV2Request, signal?: AbortSignal) =>
    request<StageAnalysisResponse>(`/analyze/${stage}`, {
      method: 'POST',
      body: JSON.stringify(req),
      signal,
    }),
  getASTNode: (
    analysisId: string,
    nodeId: string,
    signal?: AbortSignal,
    limits: { depth?: number; max_nodes?: number } = {}
  ) => {
    const query = new URLSearchParams();
    if (limits.depth !== undefined) query.set('depth', String(limits.depth));
    if (limits.max_nodes !== undefined) query.set('max_nodes', String(limits.max_nodes));
    const suffix = query.size ? `?${query}` : '';
    return request<ASTNodeResponse>(
      `/ast/${encodeURIComponent(analysisId)}/node/${encodeURIComponent(nodeId)}${suffix}`,
      { signal }
    );
  },
  proposeFix: (body: PatchProposalRequest, signal?: AbortSignal) =>
    request<{ proposal: PatchProposal; applied: false }>('/fixes/propose', {
      method: 'POST',
      body: JSON.stringify(body),
      signal,
    }),
  verifyFix: (body: PatchActionRequest, signal?: AbortSignal) =>
    request<{ proposal_id: string; report: FixVerificationReport; applied: false }>(
      '/fixes/verify',
      { method: 'POST', body: JSON.stringify(body), signal }
    ),
  applyFixV2: (body: PatchActionRequest, signal?: AbortSignal) =>
    request<{
      applied: boolean;
      source?: string;
      source_hash?: string;
      source_version?: number;
      verification?: FixVerificationReport;
      report?: FixVerificationReport;
      reason?: string;
    }>('/fixes/apply', { method: 'POST', body: JSON.stringify(body), signal }),
  undoFix: (body: UndoRequest, signal?: AbortSignal) =>
    request<{ source: string; source_hash: string; source_version: number }>('/fixes/undo', {
      method: 'POST',
      body: JSON.stringify(body),
      signal,
    }),
  runSafety: (body: SafetyRunRequest, signal?: AbortSignal) =>
    request<{ run_id: string }>('/agent-safety/run', {
      method: 'POST',
      body: JSON.stringify(body),
      signal,
    }),
  getSafetyScenarios: (signal?: AbortSignal) =>
    request<SafetyScenario[]>('/agent-safety/scenarios', { signal }),
  getSafetyResult: (runId: string, signal?: AbortSignal) =>
    request<SafetyRunResult>(`/agent-safety/results/${encodeURIComponent(runId)}`, { signal }),
  exportReport: (body: ReportExportRequest, signal?: AbortSignal) =>
    request<Blob>(
      '/reports/export',
      { method: 'POST', body: JSON.stringify(body), signal },
      'blob'
    ),
  explainAI: (body: AIExplainV2Request, signal?: AbortSignal) =>
    request<AIExplainV2Response>('/ai/explain', {
      method: 'POST',
      body: JSON.stringify(body),
      signal,
    }),
  setAIModel: (sessionId: string, model: string, signal?: AbortSignal) =>
    request<{ model: string; capabilities: CapabilitiesResponse }>('/ai/model', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, model }),
      signal,
    }),
  generateAI: (body: AIGenerateRequest, signal?: AbortSignal) =>
    request<AIGenerateResponse>('/ai/generate', {
      method: 'POST',
      body: JSON.stringify(body),
      signal,
    }),
  chatAI: (body: AIChatRequest, signal?: AbortSignal) =>
    request<AIChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify(body),
      signal,
    }),
  getCapabilities: (sessionId?: string, signal?: AbortSignal) =>
    request<CapabilitiesResponse>(
      `/capabilities${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`,
      { signal }
    ),
  setRemoteConsent: (sessionId: string, consent: boolean, signal?: AbortSignal) =>
    request<{ session_id: string; remote_consented: boolean }>('/ai/consent', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId, consent }),
      signal,
    }),
  testAiConnection: (provider?: string, model?: string, signal?: AbortSignal) =>
    request<AITestConnectionResponse>('/ai/test-connection', {
      method: 'POST',
      body: JSON.stringify({ provider, model }),
      signal,
    }),
  getAgentEvents: async (operationId?: string, signal?: AbortSignal) => {
    const query = operationId ? `?operation_id=${encodeURIComponent(operationId)}` : '';
    return request<AgentEvent[]>(`/agent/events${query}`, { signal });
  },
  clearAgentEvents: (signal?: AbortSignal) =>
    request<{ cleared: number }>('/agent/events', { method: 'DELETE', signal }),
  analyze: (req: AnalyzeRequest, signal?: AbortSignal) =>
    request<AnalysisResult>('/analyze', {
      method: 'POST',
      body: JSON.stringify(req),
      signal,
    }),
  formatSource: (source: string, language: string, signal?: AbortSignal) =>
    request<FormatSourceResponse>('/format', {
      method: 'POST',
      body: JSON.stringify({ source, language }),
      signal,
    }),
  getHealth: (signal?: AbortSignal) => request<HealthResponse>('/health', { signal }),
  getLanguages: (signal?: AbortSignal) => request<LanguageInfo[]>('/languages', { signal }),
  getSamples: (language?: string, meta?: boolean, signal?: AbortSignal) => {
    const query = new URLSearchParams();
    if (language) query.set('language', language);
    if (meta) query.set('meta', '1');
    const suffix = query.toString() ? `?${query.toString()}` : '';
    return request<SampleItem[]>(`/samples${suffix}`, { signal });
  },
  getSample: (id: string, signal?: AbortSignal) =>
    request<SampleItem>(`/samples/${id}`, { signal }),
  applyFix: (req: FixRequest, signal?: AbortSignal) =>
    request<FixResponse>('/fix', {
      method: 'POST',
      body: JSON.stringify(req),
      signal,
    }),
  applyFixAll: (req: FixAllRequest, signal?: AbortSignal) =>
    request<FixAllPreview>('/fix-all', {
      method: 'POST',
      body: JSON.stringify(req),
      signal,
    }),
  submitFeedback: (req: FeedbackRequest, signal?: AbortSignal) =>
    request<FeedbackResponse>('/feedback', {
      method: 'POST',
      body: JSON.stringify(req),
      signal,
    }),
  getMLInsights: (req: MLInsightsRequest, signal?: AbortSignal) =>
    request<MLInsightsResponse>('/ml/insights', {
      method: 'POST',
      body: JSON.stringify(req),
      signal,
    }),
  getWorkspaceTree: (signal?: AbortSignal) =>
    request<WorkspaceTreeResponse>('/workspace/tree', { signal }),
  getWorkspaceFile: (path: string, signal?: AbortSignal) =>
    request<WorkspaceFileDetail>(`/workspace/file?path=${encodeURIComponent(path)}`, { signal }),
  createWorkspaceFile: (path: string, content = '', signal?: AbortSignal) =>
    request<{ success: boolean; path: string; size: number }>('/workspace/file', {
      method: 'POST',
      body: JSON.stringify({ path, content }),
      signal,
    }),
  createWorkspaceFolder: (path: string, signal?: AbortSignal) =>
    request<{ success: boolean; path: string }>('/workspace/folder', {
      method: 'POST',
      body: JSON.stringify({ path }),
      signal,
    }),
  saveWorkspaceFile: (path: string, content: string, signal?: AbortSignal) =>
    request<{ success: boolean; path: string; size: number; last_modified: number }>('/workspace/file', {
      method: 'PUT',
      body: JSON.stringify({ path, content }),
      signal,
    }),
  deleteWorkspaceFile: (path: string, signal?: AbortSignal) =>
    request<{ success: boolean; path: string }>(`/workspace/file?path=${encodeURIComponent(path)}`, {
      method: 'DELETE',
      signal,
    }),
  renameWorkspaceFile: (oldPath: string, newPath: string, signal?: AbortSignal) =>
    request<{ success: boolean; old_path: string; new_path: string }>('/workspace/rename', {
      method: 'POST',
      body: JSON.stringify({ old_path: oldPath, new_path: newPath }),
      signal,
    }),
  searchWorkspace: (
    query: string,
    isRegex = false,
    matchCase = false,
    matchWholeWord = false,
    signal?: AbortSignal
  ) =>
    request<WorkspaceSearchResponse>(
      `/workspace/search?query=${encodeURIComponent(query)}&is_regex=${isRegex}&match_case=${matchCase}&match_whole_word=${matchWholeWord}`,
      { signal }
    ),
  replaceWorkspace: (
    query: string,
    replace: string,
    files?: string[],
    isRegex = false,
    matchCase = false,
    signal?: AbortSignal
  ) =>
    request<{ success: boolean; updated_files: string[]; replacements: number }>(
      '/workspace/replace',
      {
        method: 'POST',
        body: JSON.stringify({ query, replace, files, is_regex: isRegex, match_case: matchCase }),
        signal,
      }
    ),
  getGitStatus: (signal?: AbortSignal) =>
    request<GitStatusResponse>('/workspace/git/status', { signal }),
  getGitDiff: (path?: string, signal?: AbortSignal) =>
    request<GitDiffResponse>(
      `/workspace/git/diff${path ? `?path=${encodeURIComponent(path)}` : ''}`,
      { signal }
    ),
  gitCommit: (message: string, files?: string[], signal?: AbortSignal) =>
    request<GitCommitResponse>('/workspace/git/commit', {
      method: 'POST',
      body: JSON.stringify({ message, files }),
      signal,
    }),
};

export interface SearchMatchItem {
  line: number;
  col: number;
  length: number;
  line_text: string;
  match_text: string;
}

export interface FileSearchResultItem {
  file: string;
  matches: SearchMatchItem[];
}

export interface WorkspaceSearchResponse {
  query: string;
  total_matches: number;
  file_count: number;
  results: FileSearchResultItem[];
}

export interface GitFileStatusItem {
  path: string;
  status: string;
  staged: boolean;
}

export interface GitStatusResponse {
  available: boolean;
  branch: string;
  clean: boolean;
  files: GitFileStatusItem[];
  reason?: string | null;
}

export interface GitDiffResponse {
  available: boolean;
  path: string;
  diff: string;
  error?: string;
}

export interface GitCommitResponse {
  success: boolean;
  commit_hash?: string;
  message?: string;
  error?: string;
  output?: string;
}

export interface WorkspaceFileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number | null;
  language?: string | null;
  children?: WorkspaceFileNode[] | null;
}

export interface WorkspaceTreeResponse {
  root: string;
  tree: WorkspaceFileNode[];
}

export interface WorkspaceFileDetail {
  path: string;
  name: string;
  content: string;
  language: string;
  size: number;
  last_modified: number;
}

export const api = apiClient;
