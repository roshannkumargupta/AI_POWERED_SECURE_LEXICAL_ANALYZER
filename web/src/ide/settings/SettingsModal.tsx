import { useRef, useState } from 'react';
import { api, type AITestConnectionResponse, type CapabilitiesResponse } from '../../api/client';
import { clampScale } from '../state/store';
import { closeOnBackdrop, useModalBehavior } from '../lib/modalBehavior';

interface Props {
  open: boolean;
  capabilities: CapabilitiesResponse | null;
  scale: number;
  theme: 'dark' | 'light';
  autoAnalyze: boolean;
  consentBusy: boolean;
  onScale(value: number): void;
  onTheme(): void;
  onAutoAnalyze(value: boolean): void;
  onConsent(value: boolean): void;
  onModel(value: string): void;
  onClose(): void;
}
export function SettingsModal({
  open,
  capabilities,
  scale,
  theme,
  autoAnalyze,
  consentBusy,
  onScale,
  onTheme,
  onAutoAnalyze,
  onConsent,
  onModel,
  onClose,
}: Props) {
  const dialog = useRef<HTMLDivElement>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<AITestConnectionResponse | null>(null);

  useModalBehavior(open, dialog, onClose);
  if (!open) return null;
  const ai = capabilities?.ai;

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testAiConnection(ai?.provider, ai?.model ?? undefined);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        ok: false,
        provider: ai?.provider ?? 'unknown',
        latency_ms: 0,
        model: null,
        available_models: [],
        error: err.message || 'Connection test failed',
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="ide-p4-modal-scrim" onMouseDown={(event) => closeOnBackdrop(event, onClose)}>
      <div
        ref={dialog}
        className="ide-p4-settings"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ide-settings-title"
        tabIndex={-1}
      >
        <header>
          <h2 id="ide-settings-title">Workbench Settings</h2>
          <button type="button" aria-label="Close settings" onClick={onClose}>
            ×
          </button>
        </header>
        <section>
          <h3>Groq AI provider and consent</h3>
          <p>
            Provider: <strong>{ai?.provider ?? 'groq'}</strong> ·{' '}
            <span>{ai?.processing_location ?? 'remote'}</span>
          </p>
          <p>
            API Key configured:{' '}
            <strong>{ai?.configured ? 'Yes' : 'No'}</strong>
          </p>
          <p>
            Reachable: <strong>{ai?.reachable ? 'Yes' : 'No'}</strong>
          </p>
          <p>
            Active Model: <code>{ai?.model ?? 'None'}</code>
          </p>
          {ai?.setup_message && <p role="status">{ai.setup_message}</p>}
          <label className="ide-setting-control">
            Groq model
            <select
              aria-label="Select Groq model"
              value={ai?.model ?? ''}
              disabled={consentBusy || !ai?.installed_models?.length}
              onChange={(event) => onModel(event.target.value)}
            >
              {ai?.model && !ai?.installed_models?.includes(ai.model) && (
                <option value={ai.model} disabled>
                  {ai.model} (not installed)
                </option>
              )}
              {(ai?.installed_models ?? []).map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </label>
          <div style={{ marginTop: '0.75rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              type="button"
              disabled={testing || !ai?.configured}
              onClick={handleTestConnection}
            >
              {testing ? 'Testing connection...' : 'Test connection'}
            </button>
            {testResult && (
              <span
                style={{
                  fontSize: '0.85rem',
                  color: testResult.ok ? 'var(--text-success)' : 'var(--text-danger)',
                }}
              >
                {testResult.ok
                  ? `✓ Connected (${testResult.latency_ms} ms)`
                  : `✗ ${testResult.error || 'Failed'}`}
              </span>
            )}
          </div>
          {ai?.consent_required && (
            <label>
              <input
                type="checkbox"
                checked={Boolean(ai.remote_consented)}
                disabled={consentBusy}
                onChange={(event) => onConsent(event.target.checked)}
              />{' '}
              Allow remote processing (Groq) for this session
            </label>
          )}
          <small style={{ display: 'block', marginTop: '0.4rem', color: 'var(--text-muted)' }}>
            Deterministic lexing, parsing, and rule fixes remain 100% local. Remote processing is only used for AI explanations and candidates when consented.
          </small>
        </section>
        <section>
          <h3>Interface</h3>
          <label className="ide-setting-control">
            Interface size <span>{scale}%</span>
            <input
              type="range"
              min="90"
              max="125"
              step="5"
              value={scale}
              onChange={(event) => onScale(clampScale(Number(event.target.value)))}
            />
          </label>
          <button type="button" onClick={onTheme}>
            Switch to {theme === 'dark' ? 'light' : 'dark'} theme
          </button>
          <label>
            <input
              type="checkbox"
              checked={autoAnalyze}
              onChange={(event) => onAutoAnalyze(event.target.checked)}
            />{' '}
            Analyze while typing
          </label>
        </section>
        <section>
          <h3>Formatters and tools by language</h3>
          {capabilities ? (
            <div className="ide-settings-tools">
              {capabilities.languages.map((language) => {
                const toolNames = [
                  ...new Set([...language.semantic_tools, ...language.security_tools]),
                ];
                const tools = capabilities.tools.filter((tool) => toolNames.includes(tool.name));
                return (
                  <article key={language.id}>
                    <strong>{language.name}</strong>
                    <p>Formatter: {language.formatter ?? 'Unavailable'}</p>
                    {tools.length ? (
                      tools.map((tool) => (
                        <small key={`${language.id}-${tool.name}`}>
                          {tool.name}: {tool.status}
                          {tool.reason ? ` — ${tool.reason}` : ''}
                        </small>
                      ))
                    ) : (
                      <small>No language-specific analyzer or security tool is listed.</small>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <p>Capabilities unavailable.</p>
          )}
        </section>
      </div>
    </div>
  );
}
