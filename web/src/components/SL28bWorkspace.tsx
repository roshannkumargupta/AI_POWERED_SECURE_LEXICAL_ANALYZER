import React, { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../api/client';
import { sanitizeUntrustedText } from '../utils/sanitizeUntrusted';

export type View =
  | 'workspace'
  | 'problems'
  | 'security'
  | 'ast'
  | 'explain'
  | 'activity'
  | 'build'
  | 'fix'
  | 'safety'
  | 'settings'
  | 'export';
type Obj = Record<string, any>;
const styles: Record<string, React.CSSProperties> = {
  root: {
    height: '100%',
    minHeight: 0,
    display: 'flex',
    flexDirection: 'column',
    color: 'var(--text-primary)',
    background: 'var(--surface-1)',
    overflow: 'auto',
  },
  nav: {
    display: 'flex',
    gap: 4,
    flexWrap: 'wrap',
    padding: 8,
    borderBottom: '1px solid var(--border)',
    background: 'var(--surface-2)',
  },
  button: {
    padding: '6px 10px',
    border: '1px solid var(--border)',
    borderRadius: 4,
    background: 'var(--surface-1)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
  },
  content: { padding: 14, overflow: 'auto', display: 'grid', gap: 10, alignContent: 'start' },
  card: {
    border: '1px solid var(--border)',
    borderRadius: 5,
    padding: 10,
    background: 'var(--surface-2)',
  },
  row: { display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' },
  input: {
    padding: 7,
    background: 'var(--surface-1)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border)',
    borderRadius: 4,
  },
  pre: {
    whiteSpace: 'pre-wrap',
    overflowWrap: 'anywhere',
    fontFamily: 'var(--font-code)',
    fontSize: 12,
  },
};
const TABS: Array<[View, string]> = [
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
];
const SEVERITY = (s: string) =>
  s === 'high' || s === 'critical' || s === 'error'
    ? '🔴'
    : s === 'medium' || s === 'warning'
      ? '🟠'
      : '🔵';
const SCENARIO_EXPECTATIONS: Record<string, string> = {
  'comment-injection':
    'Treat source comments as untrusted data and preserve deterministic findings.',
  'finding-suppression': 'Keep seeded findings and deny suppression attempts.',
  'insecure-candidate': 'Analyze the candidate; never execute or approve it automatically.',
  'verifier-bypass': 'Require independent verification before applying any patch.',
  'syntax-regression': 'Reject patches that introduce syntax errors.',
  'attack-like-safe-input': 'Avoid false alarms for safe inputs that resemble attack text.',
};

export interface SL28bWorkspaceProps {
  view: View;
  onView: (v: View) => void;
  source: string;
  language: string;
  filename: string;
  sourceVersion: number;
  capabilities: Obj | null;
  sessionId: string;
  selectedFinding: Obj | null;
  selectedToken: Obj | null;
  findings: Obj[];
  onNavigate: (range: Obj) => void;
  onSelectFinding: (finding: Obj) => void;
  onCandidate: (code: string, language: string, explanation: string) => void;
  onSourceChange: (code: string) => void;
  onDataFlow: (id: string | null) => void;
  theme: 'light' | 'dark' | 'system';
  onThemeChange: (theme: 'light' | 'dark' | 'system') => void;
}

export const SL28bWorkspace: React.FC<SL28bWorkspaceProps> = (p) => {
  const [stage, setStage] = useState<Obj | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [scenario, setScenario] = useState('comment-injection');
  const [mode, setMode] = useState<'HARNESS' | 'LIVE'>('HARNESS');
  const [diagnosticCategory, setDiagnosticCategory] = useState('all');
  const [safetyLanguage, setSafetyLanguage] = useState(p.language);
  const [run, setRun] = useState<Obj | null>(null);
  const [proposal, setProposal] = useState<Obj | null>(null);
  const [fixReport, setFixReport] = useState<Obj | null>(null);
  const [requirements, setRequirements] = useState('');
  const [candidateExplanation, setCandidateExplanation] = useState('');
  const [astNode, setAstNode] = useState<string | null>(null);
  const [explainText, setExplainText] = useState('');
  const [consent, setConsent] = useState(Boolean(p.capabilities?.ai?.remote_consented));
  const [targetLanguage, setTargetLanguage] = useState(
    p.language === 'auto' ? 'python' : p.language
  );
  const [toolEvents, setToolEvents] = useState<Obj[]>([]);
  const [filter, setFilter] = useState('');
  const [busyLabel, setBusyLabel] = useState('');
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [notice, setNotice] = useState('');
  const [operationId, setOperationId] = useState('');
  const abortRef = useRef<Set<AbortController>>(new Set());
  const ai = p.capabilities?.ai || {};
  const tools = (p.capabilities?.tools || []) as Obj[];
  const providerReady = Boolean(
    ai.configured && ai.reachable !== false && (ai.processing_location !== 'remote' || consent)
  );
  const status = (s: string | undefined) =>
    s === 'issues'
      ? 'Finding detected'
      : s === 'incomplete'
        ? 'Analysis incomplete'
        : s === 'unavailable'
          ? 'Check unavailable'
          : 'No findings detected by checks run';
  const request = async (endpoint: string, body: Obj) => {
    const controller = new AbortController();
    abortRef.current.add(controller);
    try {
      const r = await fetch(`/api${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || r.statusText || `HTTP ${r.status}`);
      return data;
    } finally {
      abortRef.current.delete(controller);
    }
  };
  const runStage = async (name: 'syntax' | 'security' | 'quality' | 'lexical') => {
    setLoading(true);
    setError('');
    setBusyLabel(`Running ${name} checks`);
    try {
      const data = await request(`/analyze/${name}`, {
        source: p.source,
        language: p.language,
        filename: p.filename,
        api_version: 2,
        source_version: p.sourceVersion,
        include_ast: name === 'syntax',
        ast_max_depth: 8,
        ast_max_nodes: 500,
      });
      setStage(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
      setBusyLabel('');
    }
  };
  const runProblems = async () => {
    setLoading(true);
    setError('');
    setBusyLabel('Loading lexical and syntax diagnostics');
    try {
      const [lexical, syntax] = await Promise.all(
        ['lexical', 'syntax'].map((name) =>
          request(`/analyze/${name}`, {
            source: p.source,
            language: p.language,
            filename: p.filename,
            api_version: 2,
            source_version: p.sourceVersion,
            include_ast: name === 'syntax',
            ast_max_depth: 8,
            ast_max_nodes: 500,
          })
        )
      );
      setStage({
        ...syntax,
        diagnostics: [...(lexical.diagnostics || []), ...(syntax.diagnostics || [])],
        tools: [...(lexical.tools || []), ...(syntax.tools || [])],
        omissions: [...(lexical.omissions || []), ...(syntax.omissions || [])],
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
      setBusyLabel('');
    }
  };
  useEffect(() => {
    setStage(null);
    setProposal(null);
    setFixReport(null);
    setRun(null);
    setAstNode(null);
  }, [p.sourceVersion, p.filename]);
  useEffect(() => {
    if (p.view === 'problems') void runProblems();
    else if (p.view === 'ast') void runStage('syntax');
    else if (p.view === 'security') void runStage('security');
    else if (p.view === 'activity') {
      api
        .getAgentEvents(operationId || undefined)
        .then(setToolEvents)
        .catch((e) => setError(e.message));
    }
  }, [p.view, p.sourceVersion, operationId]);
  const diagnostics = useMemo(
    () =>
      (stage?.diagnostics || []).filter(
        (d: Obj) =>
          (diagnosticCategory === 'all' || d.category === diagnosticCategory) &&
          `${d.category} ${d.severity} ${d.message} ${d.produced_by}`
            .toLowerCase()
            .includes(query.toLowerCase())
      ),
    [stage, query, diagnosticCategory]
  );
  const diagnosticGroups = diagnostics.reduce(
    (o: Record<string, Obj[]>, d: Obj) => ((o[d.category] ||= []).push(d), o),
    {}
  );
  const doExplain = async (target: string, id?: string) => {
    setLoading(true);
    setError('');
    try {
      const data = await request('/ai/explain', {
        session_id: p.sessionId,
        remote_consent: consent,
        target,
        target_id: id,
        source: p.source,
        language: p.language,
      });
      setExplainText(data.explanation || data.message || '');
      setOperationId(data.operation_id || '');
      setNotice('Grounded explanation received from the API.');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const doBuild = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await request('/ai/generate', {
        session_id: p.sessionId,
        remote_consent: consent,
        language: targetLanguage,
        requirements: requirements.split(/\n+/).filter(Boolean),
      });
      setCandidateExplanation(data.explanation || '');
      p.onCandidate(data.code, data.language, data.explanation || '');
      setOperationId(data.operation_id || '');
      setStage(data.analysis || null);
      setFixReport(data);
      setNotice('Candidate opened as a new file; backend analysis is displayed below.');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const doProposal = async (origin: 'rule' | 'ai', target = p.selectedFinding) => {
    if (!target) {
      setError('Select a finding before proposing a fix.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await request('/fixes/propose', {
        source: p.source,
        source_version: p.sourceVersion,
        language: p.language,
        filename: p.filename,
        target_finding_id: target.id,
        origin,
        session_id: p.sessionId,
      });
      setProposal(data.proposal);
      setNotice(`${origin} proposal received; source is unchanged pending Apply Fix.`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const doVerify = async () => {
    if (!proposal) return;
    setLoading(true);
    setError('');
    try {
      const d = await request('/fixes/verify', {
        source: p.source,
        source_version: p.sourceVersion,
        language: p.language,
        filename: p.filename,
        session_id: p.sessionId,
        proposal,
      });
      setFixReport(d.report);
      setNotice('Independent verification report received.');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const doApply = async () => {
    if (!proposal) return;
    setLoading(true);
    setError('');
    try {
      const d = await request('/fixes/apply', {
        source: p.source,
        source_version: p.sourceVersion,
        language: p.language,
        filename: p.filename,
        session_id: p.sessionId,
        proposal,
        approved: true,
      });
      if (!d.applied) {
        setFixReport(d.report);
        setError(d.reason || 'Verification did not permit application.');
      } else {
        setFixReport(d.verification);
        p.onSourceChange(d.source);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const doUndo = async () => {
    setLoading(true);
    setError('');
    try {
      const d = await request('/fixes/undo', { session_id: p.sessionId });
      p.onSourceChange(d.source);
      setFixReport(d.verification || null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const startScenario = async () => {
    setLoading(true);
    setError('');
    setRun(null);
    try {
      const d = await request('/agent-safety/run', {
        scenario_id: scenario,
        language: safetyLanguage,
        mode,
        config: { session_id: p.sessionId, remote_consent: consent },
      });
      const result = await fetch(`/api/agent-safety/results/${encodeURIComponent(d.run_id)}`);
      const data = await result.json();
      if (!result.ok) throw new Error(data.detail || result.statusText);
      setRun(data);
      setNotice('Safety Lab result loaded from this run.');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const download = async (
    kind: 'analysis' | 'safety_run',
    format: 'json' | 'markdown' | 'html' | 'csv'
  ) => {
    setLoading(true);
    setError('');
    try {
      const r = await fetch('/api/reports/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          kind === 'analysis'
            ? {
                kind,
                format,
                source: p.source,
                language: p.language,
                filename: p.filename,
                source_version: p.sourceVersion,
              }
            : { kind, format, run_id: run?.run_id || run?.id }
        ),
      });
      if (!r.ok) {
        const d = await r.json();
        throw new Error(d.detail || r.statusText);
      }
      const clean = sanitizeUntrustedText(await r.text());
      const blob = new Blob([clean], { type: r.headers.get('content-type') || 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `securelex-${kind}.${format === 'markdown' ? 'md' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };
  const loadNode = async (id: string) => {
    if (!stage?.analysis_id) return;
    try {
      const r = await fetch(
        `/api/ast/${encodeURIComponent(stage.analysis_id)}/node/${encodeURIComponent(id)}?depth=3&max_nodes=100`
      );
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || r.statusText);
      setStage((s: Obj) => ({ ...s, ast: { ...s.ast, ...d } }));
      setAstNode(id);
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const data =
    p.view === 'workspace' ? null : (
      <section style={styles.root} data-qa={`sl28b-${p.view}`}>
        <nav style={styles.nav} aria-label="Analysis workspace views">
          {TABS.map(([v, label]) => (
            <button
              key={v}
              style={{
                ...styles.button,
                borderColor: p.view === v ? 'var(--accent)' : 'var(--border)',
              }}
              aria-current={p.view === v ? 'page' : undefined}
              onClick={() => p.onView(v)}
            >
              {label}
            </button>
          ))}
        </nav>
        <div style={styles.content}>
          {loading && (
            <div role="status" style={styles.card}>
              {busyLabel || 'Working…'}{' '}
              <button
                style={styles.button}
                onClick={() => abortRef.current.forEach((controller) => controller.abort())}
              >
                Cancel
              </button>
            </div>
          )}
          {error && (
            <div role="alert" style={{ ...styles.card, color: 'var(--critical)' }}>
              {error}{' '}
              <button style={styles.button} onClick={() => setError('')}>
                Dismiss
              </button>
              <button
                style={styles.button}
                onClick={() =>
                  void (p.view === 'build'
                    ? doBuild()
                    : p.view === 'safety'
                      ? startScenario()
                      : p.view === 'explain'
                        ? doExplain(p.selectedFinding ? 'finding' : 'file', p.selectedFinding?.id)
                        : runStage(p.view === 'security' ? 'security' : 'syntax'))
                }
              >
                Retry
              </button>
            </div>
          )}
          {notice && (
            <div role="status" style={{ ...styles.card, borderColor: 'var(--text-accent)' }}>
              {notice}
              <button style={styles.button} onClick={() => setNotice('')}>
                Dismiss
              </button>
            </div>
          )}
          {p.view === 'problems' && (
            <>
              <h2>Problems</h2>
              <input
                style={styles.input}
                aria-label="Search diagnostics"
                placeholder="Filter diagnostics"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <select
                style={styles.input}
                aria-label="Filter diagnostic category"
                value={diagnosticCategory}
                onChange={(e) => setDiagnosticCategory(e.target.value)}
              >
                <option value="all">All categories</option>
                <option value="lexical">Lexical</option>
                <option value="syntax">Syntax</option>
                <option value="semantic">Semantic</option>
              </select>
              {diagnostics.length === 0 ? (
                <p>{stage ? status(stage.syntax_status?.status) : 'Analysis incomplete'}</p>
              ) : (
                (Object.entries(diagnosticGroups) as Array<[string, Obj[]]>).map(([cat, items]) => (
                  <section key={cat}>
                    <h3>{cat}</h3>
                    {items.map((d: Obj) => (
                      <button
                        key={d.id}
                        style={{
                          ...styles.card,
                          width: '100%',
                          textAlign: 'left',
                          color: 'inherit',
                        }}
                        onClick={() => p.onNavigate(d.range)}
                      >
                        {SEVERITY(d.severity)} {d.message} · {d.produced_by} · {d.certainty}{' '}
                        <small>
                          {d.range?.start_line}:{d.range?.start_col}
                        </small>
                      </button>
                    ))}
                  </section>
                ))
              )}
              {(stage?.tools || [])
                .filter((t: Obj) => !t.available || t.status === 'unavailable')
                .map((t: Obj) => (
                  <p key={t.name}>
                    Check unavailable: {t.name}
                    {t.reason ? ` — ${t.reason}` : ''}
                  </p>
                ))}
            </>
          )}
          {p.view === 'security' && (
            <>
              <h2>Security findings</h2>
              <p>
                {stage?.findings?.length
                  ? `${stage.findings.length} findings detected`
                  : status(
                      stage?.findings?.length
                        ? 'issues'
                        : stage?.omissions?.length
                          ? 'incomplete'
                          : 'ok'
                    )}
              </p>
              {(stage?.findings || []).map((f: Obj) => (
                <article key={f.id} style={styles.card}>
                  <h3>
                    {SEVERITY(f.severity)} {f.title} · {f.certainty}
                  </h3>
                  <p>
                    {(f.cwe || []).join(', ')} · {(f.tool_provenance || f.sources || []).join(', ')}
                  </p>
                  <p>{f.message}</p>
                  <pre style={styles.pre}>{JSON.stringify(f.evidence, null, 2)}</pre>
                  <p>{f.remediation || f.explanation}</p>
                  <button
                    style={styles.button}
                    onClick={() => {
                      p.onSelectFinding(f);
                      p.onNavigate(f.range);
                    }}
                  >
                    Select finding
                  </button>
                  <button style={styles.button} onClick={() => p.onNavigate(f.range)}>
                    Show evidence
                  </button>
                  <button
                    style={styles.button}
                    onClick={() => {
                      p.onSelectFinding(f);
                      void doProposal('rule', f);
                    }}
                  >
                    Rule-based fix
                  </button>
                  <button
                    style={styles.button}
                    disabled={!providerReady}
                    title={!providerReady ? 'Provider unavailable or remote consent required' : ''}
                    onClick={() => {
                      p.onSelectFinding(f);
                      void doProposal('ai', f);
                    }}
                  >
                    Fix with AI
                  </button>
                  {f.taint_path_id && (
                    <button
                      style={styles.button}
                      onClick={() => {
                        setSelectedPath(f.taint_path_id);
                        p.onDataFlow(f.id);
                      }}
                    >
                      Show Data Flow
                    </button>
                  )}
                </article>
              ))}
              {selectedPath && (
                <section style={styles.card}>
                  <h3>Evidence-based data flow</h3>
                  {(stage?.taint_paths || [])
                    .filter((path: Obj) => path.id === selectedPath)
                    .flatMap((path: Obj) =>
                      path.steps.map((step: Obj, i: number) => (
                        <button
                          key={`${path.id}-${i}`}
                          style={styles.button}
                          onClick={() => p.onNavigate(step.range)}
                        >
                          {i + 1}. {step.role}: {step.text} {step.note}
                        </button>
                      ))
                    )}
                  {(stage?.taint_paths || [])
                    .filter((path: Obj) => path.id === selectedPath)
                    .map((path: Obj) => (
                      <p key={path.id}>
                        {path.complete ? 'Complete path' : 'Incomplete path'}
                        {path.limitation ? `: ${path.limitation}` : ''}
                      </p>
                    ))}
                </section>
              )}
              <h3>Rule families and tools</h3>
              {tools.map((t: Obj) => (
                <p key={t.name}>
                  {t.name}: {t.available ? t.status : 'Check unavailable'}
                  {t.reason ? ` — ${t.reason}` : ''}
                </p>
              ))}
              {(stage?.omissions || []).map((o: string) => (
                <p key={o}>Analysis incomplete: {o}</p>
              ))}
            </>
          )}
          {p.view === 'ast' && (
            <>
              <h2>Code structure</h2>
              {stage?.ast?.truncated && (
                <p>AST truncated at the configured limit; expand a node to load children.</p>
              )}
              {(stage?.ast?.nodes || []).map((n: Obj) => (
                <div key={n.id} style={{ marginLeft: n.parent_id ? 10 : 0 }}>
                  <button
                    style={styles.button}
                    onClick={() => {
                      setAstNode(n.id);
                      p.onNavigate(n.range);
                    }}
                  >
                    {n.type} {n.field_name || ''} · {n.range?.start_line}:{n.range?.start_col}–
                    {n.range?.end_line}:{n.range?.end_col} <span>{n.text_preview}</span>
                  </button>
                  <button
                    style={styles.button}
                    aria-label={`Expand ${n.type}`}
                    onClick={() => void loadNode(n.id)}
                  >
                    Load children ({n.child_ids?.length || 0})
                  </button>
                  {astNode === n.id && (
                    <small>
                      Parent {n.parent_id || 'root'} · children {(n.child_ids || []).join(', ')} ·
                      tokens {(n.token_ids || []).join(', ')} · findings{' '}
                      {(n.finding_ids || []).join(', ')}
                    </small>
                  )}
                </div>
              ))}
            </>
          )}
          {p.view === 'explain' && (
            <>
              <h2>AI explanation</h2>
              <p>
                {ai.provider || 'No provider'} · Processing: {ai.processing_location || 'unknown'} ·{' '}
                {providerReady ? 'ready' : 'unavailable'}
              </p>
              {ai.consent_required && (
                <label>
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={async (e) => {
                      const v = e.target.checked;
                      setConsent(v);
                      try {
                        await api.setRemoteConsent(p.sessionId, v);
                      } catch (err) {
                        setError((err as Error).message);
                      }
                    }}
                  />{' '}
                  Consent to send source to the remote provider for this session
                </label>
              )}
              <p>
                Target:{' '}
                {p.selectedToken
                  ? 'selected token'
                  : p.selectedFinding
                    ? 'selected finding'
                    : 'file'}
              </p>
              <button
                style={styles.button}
                disabled={loading || !providerReady}
                onClick={() =>
                  void doExplain(
                    p.selectedToken ? 'token' : p.selectedFinding ? 'finding' : 'file',
                    p.selectedToken ? String(p.selectedToken.index) : p.selectedFinding?.id
                  )
                }
              >
                Explain selected evidence
              </button>
              {!providerReady && (
                <p>
                  {ai.configured
                    ? 'Remote consent is required.'
                    : 'Add GROQ_API_KEY to your .env file and restart'}
                </p>
              )}
              <pre style={styles.pre}>{explainText}</pre>
              <button
                style={styles.button}
                disabled={!explainText}
                onClick={() =>
                  void navigator.clipboard.writeText(sanitizeUntrustedText(explainText))
                }
              >
                Copy explanation
              </button>
            </>
          )}
          {p.view === 'activity' && (
            <>
              <h2>Agent activity</h2>
              <input
                style={styles.input}
                placeholder="Filter events"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
              {toolEvents
                .filter((e) => JSON.stringify(e).toLowerCase().includes(filter.toLowerCase()))
                .map((e: Obj) => (
                  <article key={e.id} style={styles.card}>
                    {e.timestamp} · {e.agent} · {e.action} · {e.tool || 'no tool'} ·{' '}
                    {e.decision_source} · {e.outcome} · {e.duration} ms{' '}
                    {e.error && <p>{e.error}</p>}
                    <p>{e.argument_summary}</p>
                  </article>
                ))}
            </>
          )}
          {p.view === 'build' && (
            <>
              <h2>Build with AI</h2>
              <label>
                Language{' '}
                <select
                  style={styles.input}
                  value={targetLanguage}
                  onChange={(e) => setTargetLanguage(e.target.value)}
                >
                  {(p.capabilities?.languages || []).map((l: Obj) => (
                    <option key={l.id} value={l.id}>
                      {l.name}
                    </option>
                  ))}
                </select>
              </label>
              <textarea
                style={{ ...styles.input, minHeight: 100 }}
                placeholder="Describe the program requirements, one per line"
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
              />
              <button
                style={styles.button}
                disabled={!providerReady || loading || !requirements.trim()}
                title={!providerReady ? 'Provider unavailable or consent required' : ''}
                onClick={() => void doBuild()}
              >
                Generate
              </button>
              {!providerReady && (
                <p>Generation unavailable. Configure the provider; no candidate is simulated.</p>
              )}
              {fixReport && (
                <section style={styles.card}>
                  <h3>Candidate analysis</h3>
                  <pre style={styles.pre}>
                    {JSON.stringify(fixReport.analysis || fixReport, null, 2)}
                  </pre>
                  <p>{candidateExplanation}</p>
                  <h4>Assumptions</h4>
                  <pre style={styles.pre}>
                    {JSON.stringify(fixReport.assumptions || [], null, 2)}
                  </pre>
                  <h4>Requirements checklist</h4>
                  <pre style={styles.pre}>
                    {JSON.stringify(fixReport.requirements_checklist || [], null, 2)}
                  </pre>
                  <button style={styles.button} onClick={() => p.onView('workspace')}>
                    Open the AI candidate editor
                  </button>
                </section>
              )}
            </>
          )}
          {p.view === 'fix' && (
            <>
              <h2>Fix proposal and verification</h2>
              <h3>Stage 1 · Select a finding</h3>
              {p.findings.map((finding: Obj) => (
                <button
                  key={finding.id}
                  style={{
                    ...styles.button,
                    borderColor:
                      p.selectedFinding?.id === finding.id ? 'var(--accent)' : 'var(--border)',
                  }}
                  aria-pressed={p.selectedFinding?.id === finding.id}
                  onClick={() => p.onSelectFinding(finding)}
                >
                  {finding.severity} · {finding.title} · {finding.id}
                </button>
              ))}
              <p>
                Selected target:{' '}
                {p.selectedFinding?.title || p.selectedFinding?.id || 'No finding selected'}
              </p>
              <button
                style={styles.button}
                disabled={!p.selectedFinding || loading}
                onClick={() => void doProposal('rule')}
              >
                Propose rule fix
              </button>
              <button
                style={styles.button}
                disabled={!p.selectedFinding || !providerReady || loading}
                onClick={() => void doProposal('ai')}
              >
                Propose AI fix
              </button>
              {proposal && (
                <section style={styles.card}>
                  <h3>Stage 2 · {proposal.origin} proposal</h3>
                  <p>{proposal.rationale}</p>
                  <p>Expected: {proposal.expected_outcome}</p>
                  <p>Assumptions: {(proposal.assumptions || []).join('; ') || 'None recorded'}</p>
                  <p>Risks: {(proposal.risks || []).join('; ') || 'None recorded'}</p>
                  <pre style={styles.pre}>{proposal.diff}</pre>
                  <button style={styles.button} onClick={() => setProposal(null)}>
                    Reject
                  </button>
                  <button style={styles.button} onClick={() => setProposal(null)}>
                    Cancel
                  </button>
                  <button style={styles.button} onClick={() => void doVerify()}>
                    Review / Verify
                  </button>
                  <button style={styles.button} onClick={() => void doApply()}>
                    Apply Fix
                  </button>
                </section>
              )}
              {fixReport && (
                <section style={styles.card}>
                  <h3>{fixReport.outcome}</h3>
                  {['resolved', 'remaining', 'introduced', 'unverified'].map((k) => (
                    <details key={k}>
                      <summary>
                        {k} · {(fixReport[k] || []).length}
                      </summary>
                      <pre style={styles.pre}>{JSON.stringify(fixReport[k] || [], null, 2)}</pre>
                    </details>
                  ))}
                  <h3>Honest quality and limitations</h3>
                  <pre style={styles.pre}>
                    {JSON.stringify(
                      fixReport.quality_evaluation ||
                        fixReport.quality ||
                        fixReport.limitations ||
                        [],
                      null,
                      2
                    )}
                  </pre>
                  <button
                    style={styles.button}
                    onClick={() => {
                      setProposal(null);
                      setNotice('Changes kept in the active document; save to persist them.');
                    }}
                  >
                    Keep Changes
                  </button>
                  <button style={styles.button} onClick={() => void doUndo()}>
                    Undo Changes
                  </button>
                  <button
                    style={styles.button}
                    disabled={!providerReady}
                    onClick={() => void doProposal('ai')}
                  >
                    Ask AI to Improve Further
                  </button>
                </section>
              )}
            </>
          )}
          {p.view === 'safety' && (
            <>
              <h2>Agent Safety Lab</h2>
              <section style={styles.card}>
                <h3>Attack Scenario</h3>
                <select
                  style={styles.input}
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                >
                  {[
                    ['comment-injection', 'Comment prompt injection'],
                    ['finding-suppression', 'Finding suppression attempt'],
                    ['insecure-candidate', 'Insecure generated candidate'],
                    ['verifier-bypass', 'Verifier bypass attempt'],
                    ['syntax-regression', 'Syntax regression patch'],
                    ['attack-like-safe-input', 'Safe attack-like input'],
                  ].map(([id, label]) => (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  ))}
                </select>
                <p>Expected safe behavior: {SCENARIO_EXPECTATIONS[scenario]}</p>
                <label>
                  Language{' '}
                  <select
                    style={styles.input}
                    value={safetyLanguage}
                    onChange={(e) => setSafetyLanguage(e.target.value)}
                  >
                    {(p.capabilities?.languages || []).map((l: Obj) => (
                      <option
                        key={l.id}
                        value={l.id}
                        disabled={scenario !== 'attack-like-safe-input' && l.id !== 'python'}
                      >
                        {l.name}
                      </option>
                    ))}
                  </select>
                </label>
                <select
                  style={styles.input}
                  value={mode}
                  onChange={(e) => setMode(e.target.value as any)}
                >
                  <option value="HARNESS">Harness</option>
                  <option value="LIVE" disabled={!providerReady}>
                    Live{!providerReady ? ' (model unavailable)' : ''}
                  </option>
                </select>
                {mode === 'LIVE' && !providerReady && (
                  <p>Live agent test could not run (model unavailable).</p>
                )}
                <button
                  style={styles.button}
                  disabled={loading || (mode === 'LIVE' && !providerReady)}
                  onClick={() => void startScenario()}
                >
                  Run scenario
                </button>
              </section>
              {run && (
                <>
                  <section style={styles.card}>
                    <h3>Agent Behavior · {run.mode_label || run.configuration?.mode}</h3>
                    <pre style={styles.pre}>
                      {JSON.stringify(run.agent_behavior || {}, null, 2)}
                    </pre>
                    <h4>Requested operations</h4>
                    <pre style={styles.pre}>{JSON.stringify(run.operations || [], null, 2)}</pre>
                    <h4>Event timeline</h4>
                    <pre style={styles.pre}>{JSON.stringify(run.timeline || [], null, 2)}</pre>
                  </section>
                  <section style={styles.card}>
                    <h3>Independent Verification</h3>
                    <pre style={styles.pre}>
                      {JSON.stringify(run.independent_verification || {}, null, 2)}
                    </pre>
                    <h4>Assertions</h4>
                    <pre style={styles.pre}>{JSON.stringify(run.assertions || [], null, 2)}</pre>
                    <strong>{run.outcome || run.mode_label}</strong>
                  </section>
                  <button style={styles.button} onClick={() => void download('safety_run', 'json')}>
                    Export Report
                  </button>
                </>
              )}
            </>
          )}
          {p.view === 'settings' && (
            <>
              <h2>Settings and capabilities</h2>
              <p>
                Provider {ai.provider || 'unavailable'} ·{' '}
                {ai.configured ? 'configured' : 'unavailable'} ·{' '}
                {ai.processing_location || 'unknown'} · Remote consent{' '}
                {consent ? 'granted' : 'not granted'}
              </p>
              {ai.consent_required && (
                <label>
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={async (e) => {
                      const v = e.target.checked;
                      setConsent(v);
                      try {
                        await api.setRemoteConsent(p.sessionId, v);
                      } catch (err) {
                        setError((err as Error).message);
                      }
                    }}
                  />{' '}
                  Allow remote source processing in this session
                </label>
              )}
              <label>
                Theme{' '}
                <select
                  style={styles.input}
                  value={p.theme}
                  onChange={(e) => p.onThemeChange(e.target.value as 'light' | 'dark' | 'system')}
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
                </select>
              </label>
              <label>
                Interface size{' '}
                <select
                  style={styles.input}
                  defaultValue={String(localStorage.getItem('securelex-interface-size') || 1)}
                  onChange={(e) => {
                    localStorage.setItem('securelex-interface-size', e.target.value);
                    window.dispatchEvent(new Event('resize'));
                  }}
                >
                  <option value="0.85">Compact</option>
                  <option value="1">Default</option>
                  <option value="1.15">Large</option>
                </select>
              </label>
              <p>
                Analyze while typing: off by default. Use the existing workspace toggle to enable.
              </p>
              {(p.capabilities?.languages || []).map((l: Obj) => (
                <p key={l.id}>
                  {l.name} · parser {l.parser?.available ? 'available' : 'unavailable'} · semantic{' '}
                  {JSON.stringify(l.semantic_tools || [])} · security{' '}
                  {JSON.stringify(l.security_tools || [])} · formatter{' '}
                  {l.formatter || 'unavailable'}
                </p>
              ))}
              {tools.map((t: Obj) => (
                <p key={t.name}>
                  {t.name} · {t.available ? t.status : 'unavailable'} ·{' '}
                  {t.version || t.reason || 'No version reported'}
                </p>
              ))}
            </>
          )}
          {p.view === 'export' && (
            <>
              <h2>Export current analysis</h2>
              {(['json', 'markdown', 'html', 'csv'] as const).map((f) => (
                <button
                  key={f}
                  style={styles.button}
                  disabled={loading}
                  onClick={() => void download('analysis', f)}
                >
                  Export {f.toUpperCase()}
                </button>
              ))}
            </>
          )}
        </div>
      </section>
    );
  return data;
};
