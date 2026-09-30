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
}

export interface EngineMetadata {
  ml_mode: 'on' | 'off';
  ml_model_id: string;
  taint: string;
  version: string;
  elapsed_ms: number;
}

export interface AnalysisResult {
  language: string;
  filename: string;
  findings: Finding[];
  tokens: Array<{
    text: string;
    line: number;
    col: number;
    label: string;
    confidence: number;
    utf16_offset: number;
  }>;
  summary: AnalysisSummary;
  engine: EngineMetadata;
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
}

export interface AnalyzeOptions {
  fixes?: boolean;
  ml?: boolean;
  include_tokens?: boolean;
  include_suppressed?: boolean;
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

const API_BASE = '/api';

export class ApiError extends Error {
  status?: number;
  detail?: string;
  constructor(message: string, status?: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const errorJson = await res.json();
        detail = errorJson.detail || detail;
      } catch {
        // use fallback
      }
      throw new ApiError(detail || `Request failed with status ${res.status}`, res.status, detail);
    }
    return (await res.json()) as T;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw err;
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || 'Network error or backend unreachable');
  }
}

export const api = {
  getHealth: (signal?: AbortSignal) => request<HealthResponse>('/health', { signal }),
  getLanguages: (signal?: AbortSignal) => request<LanguageInfo[]>('/languages', { signal }),
  getSamples: (language?: string, signal?: AbortSignal) => {
    const q = language ? `?language=${encodeURIComponent(language)}` : '';
    return request<SampleItem[]>(`/samples${q}`, { signal });
  },
  analyze: (req: AnalyzeRequest, signal?: AbortSignal) =>
    request<AnalysisResult>('/analyze', {
      method: 'POST',
      body: JSON.stringify(req),
      signal,
    }),
  applyFix: (req: FixRequest, signal?: AbortSignal) =>
    request<FixResponse>('/fix', {
      method: 'POST',
      body: JSON.stringify(req),
      signal,
    }),
  applyFixAll: (req: FixAllRequest, signal?: AbortSignal) =>
    request<FixAllResponse>('/fix-all', {
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
};
