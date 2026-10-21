import { useEffect, useRef, useState } from 'react';
import { apiClient, type AIGenerateResponse, type CapabilitiesResponse } from '../../api/client';
import { useModalBehavior } from '../lib/modalBehavior';

interface Props {
  open: boolean;
  capabilities: CapabilitiesResponse | null;
  sessionId: string;
  onClose(): void;
  onConsent(): Promise<void>;
  onCandidate(result: AIGenerateResponse): void;
}
export function BuildAIDrawer({
  open,
  capabilities,
  sessionId,
  onClose,
  onConsent,
  onCandidate,
}: Props) {
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('cpp');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [candidate, setCandidate] = useState<AIGenerateResponse | null>(null);
  const [consent, setConsent] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [countdown, setCountdown] = useState(0);
  const activeController = useRef<AbortController | null>(null);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = window.setInterval(() => {
      setCountdown((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [countdown]);
  const drawerRef = useRef<HTMLElement>(null);
  const consentRef = useRef<HTMLElement>(null);
  const close = () => {
    activeController.current?.abort();
    activeController.current = null;
    setBusy(false);
    onClose();
  };
  useModalBehavior(open && !consent, drawerRef, close);
  useModalBehavior(open && consent, consentRef, () => setConsent(false));
  const ai = capabilities?.ai;
  const timeoutSettings = capabilities?.limits.timeouts as Record<string, unknown> | undefined;
  const timeoutSeconds = Math.max(
    1,
    Number(timeoutSettings?.ai_generate_seconds ?? timeoutSettings?.ai_seconds ?? 90) || 90
  );
  const supported = (capabilities?.languages ?? []).filter((item) =>
    ['python', 'java', 'javascript', 'cpp'].includes(item.id)
  );
  const disabledReason = countdown > 0
    ? `Rate limit active. Retrying enabled in ${countdown}s.`
    : !ai
      ? 'AI provider status is unavailable.'
      : !ai.configured
        ? ai.setup_message ||
          'AI provider unavailable. Configure the provider in the server environment.'
        : '';
  const generate = async () => {
    if (ai?.consent_required && !ai.remote_consented && !consent) {
      setConsent(true);
      return;
    }
    setBusy(true);
    setError(null);
    setElapsed(0);
    const controller = new AbortController();
    activeController.current = controller;
    const startedAt = Date.now();
    let timedOut = false;
    const timeout = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutSeconds * 1000);
    const ticker = window.setInterval(
      () => setElapsed(Math.floor((Date.now() - startedAt) / 1000)),
      250
    );
    try {
      if (ai?.consent_required && !ai.remote_consented) await onConsent();
      const requirements = [
        prompt.trim(),
        'Treat “zero unsafe memory calls” as a requirement to address; do not claim this property is guaranteed.',
      ].filter(Boolean);
      const result = await apiClient.generateAI(
        {
          session_id: sessionId,
          remote_consent: Boolean(ai?.consent_required),
          language: language as 'python' | 'java' | 'javascript' | 'cpp',
          requirements,
        },
        controller.signal
      );
      setCandidate(result);
      onCandidate(result);
    } catch (reason) {
      if (timedOut)
        setError(
          `AI generation hit its ${timeoutSeconds}-second deadline. Change SECURELEX_AI_TIMEOUT_SECONDS in .env, then retry.`
        );
      else if (!controller.signal.aborted) {
        const msg = reason instanceof Error ? reason.message : 'Generation failed.';
        setError(msg);
        const match = msg.match(/(?:429|rate\s*limit|retry(?: after| in)?)\D*(\d+)/i);
        const waitSec = match ? parseInt(match[1], 10) : /429|rate\s*limit/i.test(msg) ? 30 : 0;
        if (waitSec > 0) {
          setCountdown(waitSec);
        }
      }
    } finally {
      window.clearTimeout(timeout);
      window.clearInterval(ticker);
      if (activeController.current === controller) activeController.current = null;
      setBusy(false);
    }
  };
  if (!open) return null;
  return (
    <>
      <div
        className="ide-drawer-backdrop"
        aria-hidden="true"
        onMouseDown={(event) => {
          if (event.target === event.currentTarget) close();
        }}
      />
      <aside
        ref={drawerRef}
        className="ide-build-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Build with AI"
        tabIndex={-1}
      >
        <header>
          <h2>Build with AI</h2>
          <button type="button" aria-label="Close drawer" onClick={close}>
            ×
          </button>
        </header>
        <p className="ide-ai-provider">
          {ai
            ? `${ai.provider} · ${ai.model ?? 'model unavailable'} · ${ai.processing_location}`
            : 'Provider status unavailable'}
        </p>
        {disabledReason && <p role="status">{disabledReason}</p>}
        <label>
          Language
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            {supported.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Requirements
          <textarea
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Describe the code candidate you need"
          />
        </label>
        <button
          type="button"
          disabled={Boolean(disabledReason) || busy || !prompt.trim() || countdown > 0}
          title={disabledReason || (!prompt.trim() ? 'Enter a requirement first.' : '')}
          onClick={() => void generate()}
        >
          {busy
            ? `Generating… ${elapsed}s`
            : countdown > 0
              ? `Rate limited (${countdown}s)`
              : 'Generate'}
        </button>
        {busy && (
          <button
            type="button"
            onClick={() => {
              activeController.current?.abort();
              activeController.current = null;
              setBusy(false);
              setError('AI generation cancelled.');
            }}
          >
            Cancel
          </button>
        )}
        {consent && (
          <div
            className="ide-consent-scrim"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) setConsent(false);
            }}
          >
            <section
              ref={consentRef}
              role="dialog"
              aria-modal="true"
              aria-label="Remote processing consent"
              className="ide-ai-consent"
              tabIndex={-1}
            >
              <header>
                <h3>Allow remote processing?</h3>
                <button type="button" aria-label="Close consent" onClick={() => setConsent(false)}>
                  ×
                </button>
              </header>
              <p>Your generation requirements will be sent to the configured remote provider.</p>
              <button
                type="button"
                onClick={() => {
                  setConsent(false);
                  void generate();
                }}
              >
                Allow and continue
              </button>
              <button type="button" onClick={() => setConsent(false)}>
                Cancel
              </button>
            </section>
          </div>
        )}
        {error && (
          <div role="alert">
            <p>{error}</p>
            {countdown > 0 && <small>Retrying enabled in {countdown}s</small>}
            <button
              type="button"
              disabled={busy || countdown > 0}
              onClick={() => void generate()}
            >
              {countdown > 0 ? `Retry (${countdown}s)` : 'Retry'}
            </button>
          </div>
        )}
        {candidate && (
          <section>
            <h3>AI candidate · {candidate.language}</h3>
            <p>{candidate.explanation}</p>
            <p>
              Provider: {candidate.provider} · {candidate.processing_location}. Candidate was not
              executed.
            </p>
            <h4>Analysis</h4>
            <p>
              {candidate.analysis.tokens.length} tokens ·{' '}
              {candidate.analysis.security_findings.length} security findings ·{' '}
              {candidate.analysis.syntax_diagnostics.length +
                candidate.analysis.semantic_diagnostics.length}{' '}
              diagnostics
            </p>
            <ul>
              {candidate.analysis.security_findings.map((finding) => (
                <li key={finding.id}>
                  {finding.severity} · {finding.title} ·{' '}
                  {(finding.cwe ?? []).join(', ') || 'CWE unavailable'}
                </li>
              ))}
            </ul>
            <h4>Assumptions</h4>
            <ul>
              {candidate.assumptions.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
            <h4>Requirements</h4>
            <ul>
              {candidate.requirements_checklist.map((item, index) => (
                <li key={index}>
                  {item.requirement}: {item.status} — {item.evidence}
                </li>
              ))}
            </ul>
            <p>{candidate.limitations.join(' ')}</p>
          </section>
        )}
      </aside>
    </>
  );
}
