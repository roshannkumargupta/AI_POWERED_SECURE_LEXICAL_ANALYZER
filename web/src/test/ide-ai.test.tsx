import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient, type CapabilitiesResponse } from '../api/client';
import { AIExplainPanel } from '../ide/ai/AIExplainPanel';
import { AgentActivityPanel } from '../ide/ai/AgentActivityPanel';
import { BuildAIDrawer } from '../ide/ai/BuildAIDrawer';
import { SettingsModal } from '../ide/settings/SettingsModal';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client');
  return {
    ...actual,
    apiClient: {
      explainAI: vi.fn(),
      generateAI: vi.fn(),
      getAgentEvents: vi.fn(),
      clearAgentEvents: vi.fn(),
    },
  };
});

const request = {
  session_id: 'test-session-0000001',
  target: 'file' as const,
  source: '<img onerror="x">',
  language: 'python',
};
const caps = {
  version: 'test',
  ai: {
    provider: 'test-only-fake',
    configured: true,
    reachable: true,
    model: 'fixture',
    installed_models: [],
    configured_model_present: true,
    processing_location: 'local',
    consent_required: false,
    remote_consented: false,
    setup_message: null,
  },
  features: { build_with_ai: true, fix_with_ai: false },
  languages: [
    {
      id: 'python',
      name: 'Python',
      extensions: [],
      monaco_id: 'python',
      lexer: {},
      parser: {},
      semantic_tools: [],
      security_tools: [],
      formatter: null,
    },
  ],
  tools: [],
  limits: {},
} as unknown as CapabilitiesResponse;
const callbacks = () => ({
  onExplain: vi.fn(),
  onConsume: vi.fn(),
  onRetry: vi.fn(),
  onConsent: vi.fn().mockResolvedValue(undefined),
  available: { file: true, token: false, diagnostic: false, finding: false, patch: false },
  disabledReasons: {
    file: '',
    token: 'Select an analyzed token first.',
    diagnostic: 'Select a problem row first.',
    finding: 'Select a security finding first.',
    patch: 'Unavailable.',
  },
});
function panel(overrides: Partial<React.ComponentProps<typeof AIExplainPanel>> = {}) {
  return (
    <AIExplainPanel
      request={request}
      runId={0}
      shouldRun={false}
      deterministicText="A file explanation."
      available={callbacks().available}
      disabledReasons={callbacks().disabledReasons}
      timeoutSeconds={90}
      consentRequired={false}
      consented={false}
      onExplain={vi.fn()}
      onConsume={vi.fn()}
      onRetry={vi.fn()}
      onConsent={vi.fn().mockResolvedValue(undefined)}
      {...overrides}
    />
  );
}

describe('F2 AI explain and activity', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('does not request on tab open and offers explicit actions with disabled reasons', () => {
    const handlers = callbacks();
    render(
      panel({
        onExplain: handlers.onExplain,
        available: handlers.available,
        disabledReasons: handlers.disabledReasons,
      })
    );
    expect(screen.getByText('A file explanation.')).toBeInTheDocument();
    expect(screen.getByText('Deterministic explanation')).toBeInTheDocument();
    expect(apiClient.explainAI).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Explain current file' }));
    expect(handlers.onExplain).toHaveBeenCalledWith('file');
    const tokenButton = screen.getByRole('button', { name: 'Explain selected token' });
    expect(tokenButton).toBeDisabled();
    expect(tokenButton).toHaveAttribute('title', 'Select an analyzed token first.');
  });

  it('runs only an explicit explanation, renders returned model text as text, and supports cancel', async () => {
    vi.mocked(apiClient.explainAI).mockResolvedValue({
      operation_id: 'op-1',
      explanation: '<img onerror="x">',
      provider: 'fake',
      processing_location: 'local',
      provenance: [],
      limitations: [],
      grounded: true,
    });
    const { rerender } = render(panel());
    expect(apiClient.explainAI).not.toHaveBeenCalled();
    rerender(panel({ runId: 1, shouldRun: true }));
    await waitFor(() => expect(apiClient.explainAI).toHaveBeenCalledOnce());
    await waitFor(() => expect(screen.getByText('<img onerror="x">').tagName).toBe('P'));
    expect(document.querySelector('img')).toBeNull();
    expect(screen.getByText(/Grounded in backend evidence/)).toBeInTheDocument();
  });

  it('shows the real request error and exposes retry', async () => {
    vi.mocked(apiClient.explainAI).mockRejectedValue(new Error('Ollama returned HTTP 404.'));
    const handlers = callbacks();
    render(panel({ runId: 1, shouldRun: true, onRetry: handlers.onRetry }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Ollama returned HTTP 404.');
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(handlers.onRetry).toHaveBeenCalledOnce();
  });

  it('ends at the configured client deadline with actionable timeout text', async () => {
    vi.useFakeTimers();
    vi.mocked(apiClient.explainAI).mockImplementation(
      (_body, signal) =>
        new Promise((_resolve, reject) =>
          signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
        )
    );
    render(panel({ runId: 1, shouldRun: true, timeoutSeconds: 2 }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });
    expect(screen.getByRole('alert')).toHaveTextContent('2-second deadline');
    expect(screen.getByRole('alert')).toHaveTextContent('SECURELEX_AI_TIMEOUT_SECONDS');
  });

  it('can cancel an in-flight request', async () => {
    vi.mocked(apiClient.explainAI).mockImplementation(
      (_body, signal) =>
        new Promise((_resolve, reject) =>
          signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
        )
    );
    const { rerender } = render(panel());
    rerender(panel({ runId: 1, shouldRun: true }));
    expect(await screen.findByRole('status')).toHaveTextContent('Generating explanation');
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(await screen.findByRole('status')).toHaveTextContent('Explanation cancelled.');
  });

  it('requires consent before a remote explanation is sent', async () => {
    const onConsent = vi.fn().mockResolvedValue(undefined);
    render(
      panel({ runId: 1, shouldRun: true, consentRequired: true, consented: false, onConsent })
    );
    expect(
      await screen.findByRole('dialog', { name: 'Remote processing consent' })
    ).toBeInTheDocument();
    expect(apiClient.explainAI).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Allow for this session' }));
    await waitFor(() => expect(onConsent).toHaveBeenCalledOnce());
  });

  it('shows an installed-model picker when the configured Ollama model is missing', () => {
    const missing = {
      ...caps,
      ai: {
        ...caps.ai,
        provider: 'ollama',
        configured: false,
        model: 'qwen2.5-coder:3b',
        installed_models: ['qwen2.5-coder:1.5b'],
        configured_model_present: false,
        setup_message:
          'Configured Ollama model qwen2.5-coder:3b is missing. Choose an installed model in Settings or run: ollama pull qwen2.5-coder:3b',
      },
    };
    render(
      <SettingsModal
        open
        capabilities={missing}
        scale={100}
        theme="dark"
        autoAnalyze={false}
        consentBusy={false}
        onScale={vi.fn()}
        onTheme={vi.fn()}
        onAutoAnalyze={vi.fn()}
        onConsent={vi.fn()}
        onModel={vi.fn()}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText(missing.ai.setup_message)).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'qwen2.5-coder:3b (not installed)' })).toBeDisabled();
    expect(screen.getByRole('option', { name: 'qwen2.5-coder:1.5b' })).toBeInTheDocument();
  });

  it('shows all session events, filters them, links explained items, and clears them', async () => {
    vi.mocked(apiClient.getAgentEvents).mockResolvedValue([
      {
        id: '1',
        timestamp: '2026-10-12T00:00:00Z',
        operation_id: 'op',
        agent: 'ExplanationAgent',
        action: 'explain',
        tool: 'fixture',
        argument_summary: 'target=token',
        decision_source: 'model',
        outcome: 'accepted',
        duration: 16659,
        subject_type: 'token',
        subject_id: '3',
      },
      {
        id: '2',
        timestamp: '2026-10-11T23:00:00Z',
        operation_id: 'older-op',
        agent: 'BuildAgent',
        action: 'generate',
        tool: 'fixture',
        argument_summary: 'language=python',
        decision_source: 'model',
        outcome: 'denied',
        duration: 12,
      },
    ]);
    vi.mocked(apiClient.clearAgentEvents).mockResolvedValue({ cleared: 1 });
    const onOpenEvent = vi.fn();
    render(<AgentActivityPanel onOpenEvent={onOpenEvent} />);
    expect(await screen.findByText('accepted')).toBeInTheDocument();
    expect(screen.getByText('denied')).toBeInTheDocument();
    expect(screen.getByText(new Date('2026-10-12T00:00:00Z').toLocaleString())).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Open explained token' }));
    expect(onOpenEvent).toHaveBeenCalledWith(expect.objectContaining({ subject_id: '3' }));
    fireEvent.change(screen.getByLabelText('Filter agent events'), {
      target: { value: 'missing' },
    });
    expect(screen.getByText('No events yet')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }));
    await waitFor(() => expect(apiClient.clearAgentEvents).toHaveBeenCalledOnce());
  });

  it('shows exact unavailable provider reason and disables generation', () => {
    const noProvider = {
      ...caps,
      ai: {
        ...caps.ai,
        provider: 'ollama',
        configured: false,
        model: 'qwen2.5-coder:3b',
        setup_message:
          'Ollama is unavailable. Start Ollama, then run: ollama pull qwen2.5-coder:3b',
      },
      features: { ...caps.features, build_with_ai: false },
    };
    render(
      <BuildAIDrawer
        open
        capabilities={noProvider}
        sessionId={request.session_id}
        onClose={vi.fn()}
        onConsent={vi.fn()}
        onCandidate={vi.fn()}
      />
    );
    expect(screen.getByText(noProvider.ai.setup_message)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate' })).toBeDisabled();
  });
});
