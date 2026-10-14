import { useEffect, useRef, useState } from 'react';
import { apiClient, type AIExplainV2Request, type AIExplainV2Response } from '../../api/client';

type ExplainTarget = AIExplainV2Request['target'];
interface Props {
  request: AIExplainV2Request | null;
  runId: number;
  shouldRun: boolean;
  deterministicText: string | null;
  available: Record<ExplainTarget, boolean>;
  disabledReasons: Record<ExplainTarget, string>;
  timeoutSeconds: number;
  consentRequired: boolean;
  consented: boolean;
  onExplain(target: ExplainTarget): void;
  onConsume(runId: number): void;
  onRetry(): void;
  onConsent(): Promise<void>;
}

const buttonTargets: Array<[ExplainTarget, string]> = [
  ['file', 'Explain current file'],
  ['token', 'Explain selected token'],
  ['diagnostic', 'Explain selected problem'],
  ['finding', 'Explain selected finding'],
];

export function AIExplainPanel({
  request,
  runId,
  shouldRun,
  deterministicText,
  available,
  disabledReasons,
  timeoutSeconds,
  consentRequired,
  consented,
  onExplain,
  onConsume,
  onRetry,
  onConsent,
}: Props) {
  const [response, setResponse] = useState<AIExplainV2Response | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [consentPrompt, setConsentPrompt] = useState(false);
  const activeController = useRef<AbortController | null>(null);
  useEffect(() => {
    if (!request || !shouldRun) return;
    onConsume(runId);
    setResponse(null);
    setError(null);
    setCancelled(false);
    setElapsed(0);
    if (consentRequired && !consented) {
      setConsentPrompt(true);
      return;
    }
    const controller = new AbortController();
    activeController.current = controller;
    const started = Date.now();
    let timedOut = false;
    const timer = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutSeconds * 1000);
    setLoading(true);
    const elapsedTimer = window.setInterval(
      () => setElapsed(Math.floor((Date.now() - started) / 1000)),
      250
    );
    const authorizedRequest = consentRequired ? { ...request, remote_consent: consented } : request;
    apiClient
      .explainAI(authorizedRequest, controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setResponse(value);
      })
      .catch((reason) => {
        if (timedOut)
          setError(
            `AI explanation hit its ${timeoutSeconds}-second deadline. Change SECURELEX_AI_TIMEOUT_SECONDS in .env, then retry.`
          );
        else if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Explanation failed.');
      })
      .finally(() => {
        window.clearTimeout(timer);
        window.clearInterval(elapsedTimer);
        if (activeController.current === controller) activeController.current = null;
        setLoading(false);
      });
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(elapsedTimer);
      controller.abort();
    };
    // shouldRun is read for this request id only; runId changes for every explicit request/retry.
    // Omitting it prevents consuming a request from aborting the in-flight call on the next render.
    // Re-read the request gate only when a new run id arrives; consuming it otherwise aborts a live request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [request, runId, consentRequired, consented, timeoutSeconds, onConsume]);

  const allow = async () => {
    try {
      await onConsent();
      setConsentPrompt(false);
      onRetry();
    } catch (reason) {
      setConsentPrompt(false);
      setError(reason instanceof Error ? reason.message : 'Remote consent could not be saved.');
    }
  };
  const cancel = () => {
    activeController.current?.abort();
    activeController.current = null;
    setLoading(false);
    setCancelled(true);
  };
  return (
    <section className="ide-ai-content" aria-label="AI explanation">
      <header>
        <strong>AI Explain</strong>
        {request && (
          <span>
            {request.language} · {request.target}
          </span>
        )}
      </header>
      <nav className="ide-explain-actions" aria-label="Explain actions">
        {buttonTargets.map(([target, label]) => (
          <button
            key={target}
            type="button"
            disabled={!available[target]}
            title={!available[target] ? disabledReasons[target] : label}
            onClick={() => onExplain(target)}
          >
            {label}
          </button>
        ))}
      </nav>
      {!request && (
        <p>
          Select an item, then choose an Explain action above. Opening this tab does not send a
          request.
        </p>
      )}
      {deterministicText && (
        <section className="ide-explain-deterministic">
          <h3>Deterministic explanation</h3>
          <p className="ide-ai-output">{deterministicText}</p>
        </section>
      )}
      {consentPrompt && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Remote processing consent"
          className="ide-ai-consent"
        >
          <h3>Allow remote processing?</h3>
          <p>The selected source and evidence will be sent to the configured remote AI provider.</p>
          <button type="button" onClick={() => void allow()}>
            Allow for this session
          </button>
          <button type="button" onClick={() => setConsentPrompt(false)}>
            Cancel
          </button>
        </div>
      )}
      {loading && (
        <p role="status">
          Generating explanation… {elapsed}s{' '}
          <button type="button" onClick={cancel}>
            Cancel
          </button>
        </p>
      )}
      {cancelled && <p role="status">Explanation cancelled.</p>}
      {error && (
        <div role="alert">
          <p>{error}</p>
          <button type="button" onClick={onRetry}>
            Retry
          </button>
        </div>
      )}
      {response && (
        <section className="ide-ai-model-output">
          <h3>AI explanation</h3>
          <p className="ide-ai-output">{response.explanation}</p>
          <small>
            {response.deterministic_fallback
              ? 'deterministic explanation'
              : response.grounded
                ? 'Grounded in backend evidence'
                : 'Grounding status unavailable'}{' '}
            · {response.provider} · {response.processing_location}
            {response.limitations.map((item) => ` · ${item}`).join('')}
          </small>
          <button
            type="button"
            onClick={() => void navigator.clipboard?.writeText(response.explanation)}
          >
            Copy explanation
          </button>
        </section>
      )}
    </section>
  );
}
