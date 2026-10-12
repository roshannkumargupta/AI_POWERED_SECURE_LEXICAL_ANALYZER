import { useState } from 'react';
import { apiClient, type AIGenerateResponse, type CapabilitiesResponse } from '../../api/client';

interface Props { open: boolean; capabilities: CapabilitiesResponse | null; sessionId: string; onClose(): void; onConsent(): Promise<void>; onCandidate(result: AIGenerateResponse): void }
export function BuildAIDrawer({ open, capabilities, sessionId, onClose, onConsent, onCandidate }: Props) {
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('cpp');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [candidate, setCandidate] = useState<AIGenerateResponse | null>(null);
  const [consent, setConsent] = useState(false);
  const ai = capabilities?.ai;
  const supported = (capabilities?.languages ?? []).filter(item => ['python', 'java', 'javascript', 'cpp'].includes(item.id));
  const disabledReason = !ai ? 'AI provider status is unavailable.' : !ai.configured ? (ai.setup_message || 'AI provider unavailable. Configure the provider in the server environment.') : '';
  const generate = async () => {
    if (ai?.consent_required && !ai.remote_consented && !consent) { setConsent(true); return; }
    setBusy(true); setError(null);
    try {
      if (ai?.consent_required && !ai.remote_consented) await onConsent();
      const requirements = [prompt.trim(), 'Treat “zero unsafe memory calls” as a requirement to address; do not claim this property is guaranteed.'].filter(Boolean);
      const result = await apiClient.generateAI({ session_id: sessionId, remote_consent: Boolean(ai?.consent_required), language: language as 'python' | 'java' | 'javascript' | 'cpp', requirements });
      setCandidate(result); onCandidate(result);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Generation failed.'); }
    finally { setBusy(false); }
  };
  if (!open) return null;
  return <>
    <button className="ide-drawer-backdrop" aria-label="Close Build with AI drawer" onClick={onClose} />
    <aside className="ide-build-drawer" aria-label="Build with AI"><header><h2>Build with AI</h2><button type="button" aria-label="Close drawer" onClick={onClose}>×</button></header>
      <p className="ide-ai-provider">{ai ? `${ai.provider} · ${ai.model ?? 'model unavailable'} · ${ai.processing_location}` : 'Provider status unavailable'}</p>
      {disabledReason && <p role="status">{disabledReason}</p>}
      <label>Language<select value={language} onChange={event => setLanguage(event.target.value)}>{supported.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Requirements<textarea value={prompt} onChange={event => setPrompt(event.target.value)} placeholder="Describe the code candidate you need" /></label>
      <button type="button" disabled={Boolean(disabledReason) || busy || !prompt.trim()} title={disabledReason || (!prompt.trim() ? 'Enter a requirement first.' : '')} onClick={() => void generate()}>{busy ? 'Generating…' : 'Generate'}</button>
      {consent && <div role="dialog" aria-modal="true" aria-label="Remote processing consent" className="ide-ai-consent"><h3>Allow remote processing?</h3><p>Your generation requirements will be sent to the configured remote provider.</p><button type="button" onClick={() => { setConsent(false); void generate(); }}>Allow and continue</button><button type="button" onClick={() => setConsent(false)}>Cancel</button></div>}
      {error && <div role="alert"><p>{error}</p><button type="button" onClick={() => void generate()}>Retry</button></div>}
      {candidate && <section><h3>AI candidate · {candidate.language}</h3><p>{candidate.explanation}</p><p>Provider: {candidate.provider} · {candidate.processing_location}. Candidate was not executed.</p><h4>Analysis</h4><p>{candidate.analysis.tokens.length} tokens · {candidate.analysis.security_findings.length} security findings · {candidate.analysis.syntax_diagnostics.length + candidate.analysis.semantic_diagnostics.length} diagnostics</p><ul>{candidate.analysis.security_findings.map(finding => <li key={finding.id}>{finding.severity} · {finding.title} · {(finding.cwe ?? []).join(', ') || 'CWE unavailable'}</li>)}</ul><h4>Assumptions</h4><ul>{candidate.assumptions.map((item, index) => <li key={index}>{item}</li>)}</ul><h4>Requirements</h4><ul>{candidate.requirements_checklist.map((item, index) => <li key={index}>{item.requirement}: {item.status} — {item.evidence}</li>)}</ul><p>{candidate.limitations.join(' ')}</p></section>}
    </aside>
  </>;
}
