import { useRef } from 'react';
import type { CapabilitiesResponse } from '../../api/client';
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
  useModalBehavior(open, dialog, onClose);
  if (!open) return null;
  const ai = capabilities?.ai;
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
          <h3>AI provider and consent</h3>
          <p>Provider: {ai?.provider ?? 'Unavailable'}</p>
          <p>
            Status:{' '}
            {ai
              ? ai.configured
                ? ai.reachable === false
                  ? 'Configured, unavailable'
                  : 'Configured'
                : 'Not configured'
              : 'Capabilities unavailable'}
          </p>
          <p>
            Model: {ai?.model ?? 'Unavailable'} · {ai?.processing_location ?? 'Unknown'}
          </p>
          {ai?.setup_message && <p role="status">{ai.setup_message}</p>}
          {ai?.provider === 'ollama' && (
            <label className="ide-setting-control">
              Local model
              <select
                aria-label="Select installed local model"
                value={ai.model ?? ''}
                disabled={consentBusy || !ai.installed_models?.length}
                onChange={(event) => onModel(event.target.value)}
              >
                {ai.model && !ai.installed_models?.includes(ai.model) && (
                  <option value={ai.model} disabled>
                    {ai.model} (not installed)
                  </option>
                )}
                {(ai.installed_models ?? []).map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </label>
          )}
          {ai?.provider === 'ollama' && !ai.installed_models?.length && (
            <small>No installed local models were reported by Ollama.</small>
          )}
          {ai?.consent_required && (
            <label>
              <input
                type="checkbox"
                checked={Boolean(ai.remote_consented)}
                disabled={consentBusy}
                onChange={(event) => onConsent(event.target.checked)}
              />{' '}
              Allow remote processing for this session
            </label>
          )}
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
