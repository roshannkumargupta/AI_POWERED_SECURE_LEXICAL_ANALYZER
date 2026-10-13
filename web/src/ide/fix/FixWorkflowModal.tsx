import { useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { apiClient, type FixAllPreview, type FixVerificationReport, type PatchProposal, type PatchProposalRequest, type AnalysisResultV2 } from '../../api/client';
import { applyEdits } from '../../utils/applyEdits';
import { DiffPreview } from './DiffPreview';
import { fixReducer, initialFixMachine, missingVerificationTools, outcomeLabel, verificationCounts } from './machine';

type Finding = AnalysisResultV2['security_findings'][number];
type FixActions = { apply(): void; undo(): void; fixAll(): void; canApply(): boolean; canUndo(): boolean };
interface Props {
  finding: Finding | null; documentId: string | null; activeDocumentId: string | null; source: string; sourceVersion: number;
  language: string; filename: string; sessionId: string; aiReady: boolean; remoteConsentRequired: boolean; remoteConsented: boolean;
  onConsent(): Promise<void>; onSourceApplied(source: string, version: number): void; onUndoApplied(source: string, version: number): void;
  onClose(): void; onAskAI(): void;
  initialFixAll?: boolean;
  timeoutSeconds?: number;
  targetKind?: 'finding' | 'diagnostic' | 'token';
  onActions?(actions: FixActions): void;
}

function FixActionsRegistration({ onActions, apply, undo, fixAll, canApply, canUndo }: FixActions & { onActions?: Props['onActions'] }) {
  const current = useRef({ apply, undo, fixAll, canApply, canUndo });
  current.current = { apply, undo, fixAll, canApply, canUndo };
  useEffect(() => {
    onActions?.({
      apply: () => current.current.apply(), undo: () => current.current.undo(), fixAll: () => current.current.fixAll(),
      canApply: () => current.current.canApply(), canUndo: () => current.current.canUndo(),
    });
  }, [onActions]);
  return null;
}

function isFixReport(value: unknown): value is FixVerificationReport { return Boolean(value && typeof value === 'object' && ['resolved', 'remaining', 'introduced', 'unverified', 'tools'].every(key => Array.isArray((value as Record<string, unknown>)[key]))); }

export function FixWorkflowModal(props: Props) {
  const { finding } = props;
  const [machine, dispatch] = useReducer(fixReducer, initialFixMachine);
  const phaseRef = useRef(machine.phase);
  phaseRef.current = machine.phase;
  const [consentPrompt, setConsentPrompt] = useState(false);
  const [fixAllMode, setFixAllMode] = useState(false);
  const [fixAllPreview, setFixAllPreview] = useState<FixAllPreview | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [elapsed, setElapsed] = useState(0);
  const [retryNonce, setRetryNonce] = useState(0);
  const proposalStartedAt = useRef(Date.now());
  const proposalTimedOut = useRef(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const requestController = useRef<AbortController | null>(null);
  const proposalKey = useRef<string | null>(null);
  const startFixAllRef = useRef<(() => void) | null>(null);
  const closeRef = useRef(props.onClose);
  closeRef.current = props.onClose;
  const patchedPreview = useMemo(() => {
    if (!machine.proposal) return '';
    try { return applyEdits(props.source, machine.proposal.edits); } catch { return ''; }
  }, [machine.proposal, props.source]);
  const stale = props.documentId !== props.activeDocumentId || Boolean(machine.proposal && (machine.proposal.source_version !== props.sourceVersion));
  const report = machine.report;
  const reportCounts = report ? verificationCounts(report) : null;

  useEffect(() => {
    if (!finding) { proposalKey.current = null; dispatch({ type: 'reset' }); setFixAllMode(false); setFixAllPreview(null); return; }
    const key = `${props.documentId}:${finding.id}:${props.sourceVersion}`;
    if (proposalKey.current?.startsWith(`${props.documentId}:${finding.id}:`)) {
      if (proposalKey.current !== key && phaseRef.current !== 'report') dispatch({ type: 'failure', phase: 'stale', message: 'The source changed while this proposal was open. Start a new fix review.' });
      return;
    }
    proposalKey.current = key;
    if (props.initialFixAll) { requestAnimationFrame(() => startFixAllRef.current?.()); return; }
    let current = true;
    const controller = new AbortController();
    requestController.current = controller;
    const propose = async (origin: 'rule' | 'ai', remoteConsent = false) => {
      dispatch({ type: 'propose' });
      proposalStartedAt.current = Date.now();
      proposalTimedOut.current = false;
      const timeout = window.setTimeout(() => { proposalTimedOut.current = true; controller.abort(); }, (props.timeoutSeconds ?? 90) * 1000);
      try {
        const body: PatchProposalRequest = { source: props.source, source_version: props.sourceVersion, language: props.language, filename: props.filename, target: { kind: props.targetKind ?? 'finding', id: finding.id }, ...(props.targetKind === 'finding' || !props.targetKind ? { target_finding_id: finding.id } : {}), session_id: props.sessionId, remote_consent: remoteConsent, origin };
        const response = await apiClient.proposeFix(body, controller.signal);
        if (!current || controller.signal.aborted) return;
        if (!response.proposal?.edits?.length || response.proposal.source_hash.length !== 64) throw new Error('The server returned a malformed proposal.');
        try { if (applyEdits(props.source, response.proposal.edits) === props.source) throw new Error('The proposal does not change this source.'); }
        catch (error) { throw new Error(error instanceof Error ? error.message : 'The proposal edits are malformed.'); }
        dispatch({ type: 'proposal', proposal: response.proposal });
      } catch (error) {
        if (!current || (controller.signal.aborted && !proposalTimedOut.current)) return;
        const message = proposalTimedOut.current ? `AI fix proposal hit its ${props.timeoutSeconds ?? 90}-second deadline. Change SECURELEX_AI_TIMEOUT_SECONDS in .env, then retry or use the rule proposal.` : error instanceof Error ? error.message : 'Could not create a fix proposal.';
        const phase = /stale|version|hash/i.test(message) ? 'stale' : /malformed|edit|range|overlap/i.test(message) ? 'malformed' : 'error';
        if (origin === 'rule' && props.aiReady && /no automatic fix/i.test(message)) {
          if (props.remoteConsentRequired && !props.remoteConsented) {
            setConsentPrompt(true);
            dispatch({ type: 'failure', phase: 'error', message: 'No deterministic fix is available. AI improvement requires your consent before source is sent.' });
          }
          else void propose('ai', props.remoteConsentRequired && props.remoteConsented);
          return;
        }
        dispatch({ type: 'failure', phase, message });
      } finally { window.clearTimeout(timeout); }
    };
    void propose('rule');
    return () => { current = false; controller.abort(); };
  }, [finding, props.documentId, props.source, props.sourceVersion, props.language, props.filename, props.sessionId, props.aiReady, props.remoteConsentRequired, props.remoteConsented, props.initialFixAll, props.targetKind, props.timeoutSeconds, retryNonce]);

  useEffect(() => {
    if (machine.phase !== 'proposing') return;
    const timer = window.setInterval(() => setElapsed(Math.floor((Date.now() - proposalStartedAt.current) / 1000)), 250);
    return () => window.clearInterval(timer);
  }, [machine.phase]);

  useEffect(() => {
    if (!finding) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    dialogRef.current?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); closeRef.current(); }
      if (event.key !== 'Tab') return;
      const nodes = dialogRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),textarea:not(:disabled),select:not(:disabled),[tabindex="0"]');
      if (!nodes?.length) return;
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    window.addEventListener('keydown', keydown);
    return () => { window.removeEventListener('keydown', keydown); previouslyFocused?.focus(); };
  }, [finding]);

  if (!finding) return null;
  const beginAIProposal = async () => {
    let timer: number | undefined;
    let timedOut = false;
    try {
      await props.onConsent(); setConsentPrompt(false);
      const controller = new AbortController(); requestController.current = controller; dispatch({ type: 'propose' });
      proposalStartedAt.current = Date.now();
      timer = window.setTimeout(() => { timedOut = true; controller.abort(); }, (props.timeoutSeconds ?? 90) * 1000);
      const response = await apiClient.proposeFix({ source: props.source, source_version: props.sourceVersion, language: props.language, filename: props.filename, target: { kind: props.targetKind ?? 'finding', id: finding.id }, ...(props.targetKind === 'finding' || !props.targetKind ? { target_finding_id: finding.id } : {}), session_id: props.sessionId, remote_consent: true, origin: 'ai' }, controller.signal);
      if (controller.signal.aborted) return;
      if (!response.proposal?.edits?.length || response.proposal.source_hash.length !== 64) throw new Error('The server returned a malformed proposal.');
      if (applyEdits(props.source, response.proposal.edits) === props.source) throw new Error('The proposal does not change this source.');
      dispatch({ type: 'proposal', proposal: response.proposal });
    }
    catch (error) { dispatch({ type: 'failure', phase: 'error', message: timedOut ? `AI fix proposal hit its ${props.timeoutSeconds ?? 90}-second deadline. Change SECURELEX_AI_TIMEOUT_SECONDS in .env, then retry or use the rule proposal.` : error instanceof Error ? error.message : 'Remote consent could not be saved.' }); setConsentPrompt(false); }
    finally { if (timer !== undefined) window.clearTimeout(timer); }
  };
  const apply = async () => {
    if (stale || !machine.proposal || !patchedPreview) { dispatch({ type: 'failure', phase: 'stale', message: 'The source changed after this proposal. Create a new proposal.' }); return; }
    dispatch({ type: 'apply' });
    const body = { source: props.source, source_version: props.sourceVersion, language: props.language, filename: props.filename, session_id: props.sessionId, proposal: machine.proposal, approved: true };
    try {
      dispatch({ type: 'verifying' });
      const controller = new AbortController(); requestController.current = controller;
      const verified = await apiClient.verifyFix(body, controller.signal);
      if (controller.signal.aborted) return;
      if (!isFixReport(verified.report)) { dispatch({ type: 'failure', phase: 'malformed', message: 'Verifier returned a malformed report.' }); return; }
      const unavailable = missingVerificationTools(verified.report as unknown as Record<string, unknown>);
      if (unavailable) {
        dispatch({ type: 'report', report: verified.report as unknown as Record<string, unknown>, sourceVersion: null });
        dispatch({ type: 'failure', phase: 'missing-tools', message: 'One or more verification tools were unavailable; source was not changed.' });
        return;
      }
      if (!['Verified for specified checks', 'Partially verified'].includes(verified.report.outcome)) {
        dispatch({ type: 'report', report: verified.report as unknown as Record<string, unknown>, sourceVersion: null });
        dispatch({ type: 'failure', phase: 'verification-failed', message: `Verification outcome: ${verified.report.outcome}. Source was not changed.` });
        return;
      }
      const response = await apiClient.applyFixV2(body, controller.signal);
      if (controller.signal.aborted) return;
      const actualReport = response.verification ?? response.report;
      if (!isFixReport(actualReport)) { dispatch({ type: 'failure', phase: 'malformed', message: response.reason || 'Verifier returned a malformed report.' }); return; }
      if (response.applied && response.source !== undefined && response.source_version !== undefined) props.onSourceApplied(response.source, response.source_version);
      const missingTools = missingVerificationTools(actualReport as unknown as Record<string, unknown>);
      dispatch({ type: 'report', report: actualReport as unknown as Record<string, unknown>, sourceVersion: response.source_version ?? null });
      if (!response.applied && outcomeLabel(actualReport as unknown as Record<string, unknown>) === 'Verification failed') dispatch({ type: 'failure', phase: 'verification-failed', message: response.reason || 'Verification failed; source was not changed.' });
      else if (missingTools) dispatch({ type: 'failure', phase: 'missing-tools', message: 'One or more verification tools were unavailable; review the unverified checks.' });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not apply the proposal.';
      dispatch({ type: 'failure', phase: /stale|version|hash/i.test(message) ? 'stale' : 'error', message });
    }
  };
  const undo = async () => {
    try { const response = await apiClient.undoFix({ session_id: props.sessionId }); props.onUndoApplied(response.source, response.source_version); props.onClose(); }
    catch (error) { dispatch({ type: 'failure', phase: 'error', message: error instanceof Error ? error.message : 'Undo failed.' }); }
  };
  const requestFixAllPreview = async () => {
    setFixAllMode(true); setFixAllPreview(null); dispatch({ type: 'propose' });
    try {
      const preview = await apiClient.applyFixAll({ source: props.source, language: props.language, filename: props.filename, session_id: props.sessionId, source_version: props.sourceVersion });
      setFixAllPreview(preview);
      const proposal: PatchProposal = { id: 'fix-all-preview', source_hash: '', source_version: props.sourceVersion, target_finding_id: finding.id, origin: 'rule', edits: [{ range: { start_line: 1, start_col: 1, end_line: props.source.split('\n').length, end_col: props.source.split('\n').at(-1)!.length + 1 }, new_text: preview.new_source }], diff: preview.diff, rationale: `${preview.applied.length} safe changes proposed; ${preview.skipped.length} skipped.`, expected_outcome: '', assumptions: [], risks: preview.skipped.map(item => `${item.fix_id}: ${item.reason}`), created_at: new Date().toISOString() };
      // Keep the complete fix-all response as an actual review preview. It is applied only by the explicit button below.
      dispatch({ type: 'proposal', proposal });
      setExpanded({ fixAll: true });
    } catch (error) { dispatch({ type: 'failure', phase: 'error', message: error instanceof Error ? error.message : 'Fix all preview failed.' }); }
  };
  startFixAllRef.current = () => { void requestFixAllPreview(); };
  const acceptFixAll = async () => {
    if (!machine.proposal) return;
    try {
      const response = await apiClient.applyFixAll({ source: props.source, language: props.language, filename: props.filename, session_id: props.sessionId, source_version: props.sourceVersion, approved: true, approved_diff: fixAllPreview?.diff });
      if (response.applied_to_source && response.source_version !== undefined) props.onSourceApplied(response.new_source, response.source_version);
      props.onClose();
    } catch (error) { dispatch({ type: 'failure', phase: 'error', message: error instanceof Error ? error.message : 'Could not apply safe fixes.' }); }
  };
  const tiles = reportCounts ? Object.entries(reportCounts) as Array<[string, unknown[]]> : [];
  const phaseText: Record<string, string> = { proposing: `Preparing proposal… ${elapsed}s`, applying: 'Applying approved changes…', verifying: 'Running independent verification…', stale: 'Stale source', malformed: 'Malformed proposal', 'verification-failed': 'Verification failed', 'missing-tools': 'Verification tools unavailable', error: 'Fix workflow error' };
  return <div className="ide-fix-overlay" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget && machine.phase === 'review') props.onClose(); }}>
    <div ref={dialogRef} className="ide-fix-modal" role="dialog" aria-modal="true" aria-labelledby="ide-fix-title" tabIndex={-1}>
      <FixActionsRegistration onActions={props.onActions} apply={() => void apply()} undo={() => void undo()} fixAll={() => void requestFixAllPreview()} canApply={() => machine.phase === 'review' && Boolean(machine.proposal) && !stale} canUndo={() => machine.phase === 'report' && machine.appliedSourceVersion !== null}/>
      <header><div><span className="material-symbols-outlined" aria-hidden="true">auto_fix_high</span><strong id="ide-fix-title">Fix Agent Patch &amp; Independent Verifier Pipeline</strong>{machine.proposal && <span className={`ide-fix-origin ${machine.proposal.origin}`}>{machine.proposal.origin} proposal</span>}</div><button type="button" aria-label="Close fix review" onClick={props.onClose}>×</button></header>
      <main>
        {consentPrompt && <section role="dialog" aria-modal="true" className="ide-ai-consent"><h3>Allow remote processing?</h3><p>The current document source and finding evidence will be sent to the configured remote provider to propose a fix.</p><button type="button" onClick={() => void beginAIProposal()}>Allow and propose</button><button type="button" onClick={() => { setConsentPrompt(false); dispatch({ type: 'propose' }); void apiClient.proposeFix({ source: props.source, source_version: props.sourceVersion, language: props.language, filename: props.filename, target_finding_id: finding.id, session_id: props.sessionId, origin: 'rule' }).then(value => dispatch({ type: 'proposal', proposal: value.proposal })).catch(error => dispatch({ type: 'failure', phase: 'error', message: error instanceof Error ? error.message : 'Rule proposal failed.' })); }}>Use rule proposal</button></section>}
        <section className="ide-fix-summary"><div><strong>{finding.title}</strong><span>{finding.rule_id} · {(finding.cwe ?? []).join(', ') || 'CWE unavailable'} · {finding.severity}</span></div>{machine.error && <p role="alert">{machine.error}</p>}{phaseText[machine.phase] && <p role="status">{phaseText[machine.phase]}</p>}{stale && <p role="alert">Stale source: this proposal belongs to a different document or source version.</p>}</section>
        {machine.proposal && !report && <section className="ide-fix-review"><div className="ide-fix-heading"><strong>{fixAllMode ? `Safe fix-all preview · ${props.filename}` : `Proposed patch · ${props.filename}`}</strong><span>{machine.proposal.origin}</span></div><p><b>Rationale:</b> {machine.proposal.rationale || 'No rationale was supplied.'}</p>{!fixAllMode && <><p><b>Expected outcome:</b> {machine.proposal.expected_outcome || 'No expected outcome was supplied.'}</p><div className="ide-fix-lists"><div><h3>Assumptions</h3>{machine.proposal.assumptions.length ? <ul>{machine.proposal.assumptions.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p>None supplied.</p>}</div><div><h3>Risks</h3>{machine.proposal.risks.length ? <ul>{machine.proposal.risks.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p>None supplied.</p>}</div></div></>}{fixAllMode && fixAllPreview && <div className="ide-fix-lists"><div><h3>Safe changes · {fixAllPreview.applied.length}</h3>{fixAllPreview.applied.length ? <ul>{fixAllPreview.applied.map(id => <li key={id}>{id}</li>)}</ul> : <p>No changes proposed.</p>}</div><div><h3>Skipped · {fixAllPreview.skipped.length}</h3>{fixAllPreview.skipped.length ? <ul>{fixAllPreview.skipped.map(item => <li key={item.fix_id}>{item.fix_id}: {item.reason}</li>)}</ul> : <p>None.</p>}</div></div>}<h3>Compare / Patch</h3><DiffPreview source={props.source} filename={props.filename} proposal={machine.proposal} diffOverride={fixAllMode ? fixAllPreview?.diff : undefined}/></section>}
        {report && <section className="ide-fix-report"><div className={`ide-fix-outcome ${outcomeLabel(report).toLowerCase().replace(/ /g, '-')}`}>{outcomeLabel(report)}</div><div className="ide-fix-tiles">{tiles.map(([key, items]) => <details key={key} open={expanded[key]}><summary><strong>{key[0].toUpperCase() + key.slice(1)}</strong><span>{items.length}</span></summary>{items.length ? <ul>{items.map((item, index) => <li key={index}>{typeof item === 'string' ? item : String((item as Record<string, unknown>).message ?? (item as Record<string, unknown>).rule_id ?? (item as Record<string, unknown>).reason ?? (item as Record<string, unknown>).check ?? JSON.stringify(item))}</li>)}</ul> : <p>No items reported.</p>}</details>)}</div><h3>Verification tools</h3><ul className="ide-fix-tools">{(Array.isArray(report.tools) ? report.tools as Array<Record<string, unknown>> : []).map((tool, index) => <li key={index}><span>{String(tool.name ?? 'Tool')}</span><span>{String(tool.status ?? 'unavailable')}</span>{tool.reason != null && <small>{String(tool.reason)}</small>}</li>)}</ul><h3>Quality measurements</h3><p>Complexity delta (measured metrics only): {report.quality_delta && Object.keys(report.quality_delta as Record<string, unknown>).length ? JSON.stringify(report.quality_delta) : 'No measured complexity delta.'}</p><p>{String((report.quality_evaluation as Record<string, unknown> | undefined)?.maintainability ?? 'No separate maintainability score was measured.')}</p></section>}
      </main>
      <footer>{report && machine.appliedSourceVersion !== null ? <><button type="button" onClick={undo}>Undo Changes</button><button type="button" onClick={() => { props.onClose(); props.onAskAI(); }}>Ask AI to Improve Further</button><span/><button type="button" onClick={props.onClose}>Keep Changes</button></> : report ? <><span/><button type="button" onClick={props.onClose}>Close</button></> : fixAllMode && machine.proposal ? <><button type="button" onClick={props.onClose}>Cancel</button><span/><button type="button" onClick={() => void acceptFixAll()}>Apply Fix All Safe</button></> : <><button type="button" onClick={() => { requestController.current?.abort(); props.onClose(); }}>Cancel</button>{machine.phase === 'review' && props.aiReady && <button type="button" onClick={() => { if (props.remoteConsentRequired && !props.remoteConsented) setConsentPrompt(true); else void beginAIProposal(); }}>Improve with AI</button>}{machine.phase === 'error' && props.aiReady && <button type="button" onClick={() => { if (props.remoteConsentRequired && !props.remoteConsented) setConsentPrompt(true); else void beginAIProposal(); }}>Improve with AI</button>}{machine.phase === 'error' && <button type="button" onClick={() => { requestController.current?.abort(); proposalKey.current = null; setRetryNonce(value => value + 1); }}>Retry</button>}<span/><button type="button" disabled={!machine.proposal || stale || machine.phase !== 'review'} title={stale ? 'Source changed; create a new proposal.' : !machine.proposal ? 'Wait for a valid proposal.' : ''} onClick={() => void apply()}>Apply</button><button type="button" onClick={props.onClose}>Reject</button></>}</footer>
    </div>
  </div>;
}
