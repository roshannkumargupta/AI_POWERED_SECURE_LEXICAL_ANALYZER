import { useEffect, useRef, useState } from 'react';
import { apiClient, type AIExplainV2Request, type AIExplainV2Response } from '../../api/client';

interface Props {
  request: AIExplainV2Request | null;
  consentRequired: boolean;
  consented: boolean;
  onConsent(): Promise<void>;
  onOperation(operationId: string): void;
}

export function AIExplainPanel({ request, consentRequired, consented, onConsent, onOperation }: Props) {
  const [response, setResponse] = useState<AIExplainV2Response | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [consentPrompt, setConsentPrompt] = useState(false);
  const [retry, setRetry] = useState(0);
  const activeController = useRef<AbortController | null>(null);
  useEffect(() => {
    setResponse(null); setError(null);
    if (!request) return;
    if (consentRequired && !consented) { setConsentPrompt(true); return; }
    const controller = new AbortController();
    activeController.current = controller;
    setLoading(true);
    const authorizedRequest = consentRequired ? { ...request, remote_consent: consented } : request;
    apiClient.explainAI(authorizedRequest, controller.signal).then(value => { setResponse(value); onOperation(value.operation_id); }).catch(reason => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'Explanation failed.');
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); if (activeController.current === controller) activeController.current = null; });
    return () => controller.abort();
  }, [request, consentRequired, consented, retry, onOperation]);
  const allow = async () => { await onConsent(); setConsentPrompt(false); };
  return <section className="ide-ai-content" aria-label="AI explanation">
    <header><strong>AI Explain</strong>{request && <span>Grounded in current analysis evidence</span>}</header>
    {!request && <p>Select a token, problem, or finding to request an explanation.</p>}
    {consentPrompt && <div role="dialog" aria-modal="true" aria-label="Remote processing consent" className="ide-ai-consent"><h3>Allow remote processing?</h3><p>The selected source and evidence will be sent to the configured remote AI provider.</p><button type="button" onClick={() => void allow()}>Allow for this session</button><button type="button" onClick={() => setConsentPrompt(false)}>Cancel</button></div>}
    {loading && <p role="status">Generating explanation… <button type="button" onClick={() => { activeController.current?.abort(); activeController.current = null; setLoading(false); }}>Cancel</button></p>}
    {error && <div role="alert"><p>{error}</p><button type="button" onClick={() => setRetry(value => value + 1)}>Retry</button></div>}
    {response && <><p className="ide-ai-output">{response.explanation}</p><small>{response.deterministic_fallback ? 'deterministic explanation' : response.grounded ? 'Grounded in backend evidence' : 'Grounding status unavailable'} · {response.provider} · {response.processing_location}{response.limitations.map(item => ` · ${item}`).join('')}</small><button type="button" onClick={() => void navigator.clipboard?.writeText(response.explanation)}>Copy explanation</button></>}
  </section>;
}
