import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../api/client';
import { AIExplainPanel } from '../ide/ai/AIExplainPanel';
import { AgentActivityPanel } from '../ide/ai/AgentActivityPanel';
import { BuildAIDrawer } from '../ide/ai/BuildAIDrawer';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client');
  return { ...actual, apiClient: { explainAI: vi.fn(), generateAI: vi.fn(), getAgentEvents: vi.fn() } };
});
const request = { session_id: 'test-session-0000001', target: 'file' as const, source: '<img onerror="x">', language: 'python' };
const caps = { version: 'test', ai: { provider: 'test-only-fake', configured: true, reachable: true, model: 'fixture', processing_location: 'local', consent_required: false, remote_consented: false, setup_message: null }, features: { build_with_ai: true, fix_with_ai: false }, languages: [{ id: 'python', name: 'Python', extensions: [], monaco_id: 'python', lexer: {}, parser: {}, semantic_tools: [], security_tools: [], formatter: null }], tools: [], limits: {} };

describe('P5 AI views', () => {
  beforeEach(() => vi.clearAllMocks());
  it('asks for remote consent before sending explanation and renders model output as text', async () => {
    vi.mocked(apiClient.explainAI).mockResolvedValue({ operation_id: 'op-1', explanation: '<img onerror="x">', provider: 'remote', processing_location: 'remote', provenance: [], limitations: [] });
    const consent = vi.fn().mockResolvedValue(undefined);
    const { rerender } = render(<AIExplainPanel request={request} consentRequired consented={false} onConsent={consent} onOperation={vi.fn()} />);
    expect(screen.getByRole('dialog', { name: 'Remote processing consent' })).toBeInTheDocument();
    expect(apiClient.explainAI).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText('Allow for this session'));
    await waitFor(() => expect(consent).toHaveBeenCalled());
    rerender(<AIExplainPanel request={request} consentRequired consented onConsent={consent} onOperation={vi.fn()} />);
    await waitFor(() => expect(apiClient.explainAI).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText('<img onerror="x">').tagName).toBe('P'));
    expect(document.querySelector('img')).toBeNull();
  });
  it('shows exact unavailable setup reason and keeps generation disabled', () => {
    const noProvider = { ...caps, ai: { ...caps.ai, provider: 'ollama', configured: false, model: 'qwen2.5-coder:3b', setup_message: 'Ollama is unavailable. Start Ollama, then run: ollama pull qwen2.5-coder:3b' }, features: { ...caps.features, build_with_ai: false } };
    render(<BuildAIDrawer open capabilities={noProvider} sessionId={request.session_id} onClose={vi.fn()} onConsent={vi.fn()} onCandidate={vi.fn()} />);
    expect(screen.getByText('Ollama is unavailable. Start Ollama, then run: ollama pull qwen2.5-coder:3b')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate' })).toBeDisabled();
  });
  it('filters real operation events and shows the empty state', async () => {
    vi.mocked(apiClient.getAgentEvents).mockResolvedValue([{ id: '1', timestamp: '2026-10-12T00:00:00Z', operation_id: 'op', agent: 'BuildAgent', action: 'generate', tool: 'fixture', argument_summary: '', decision_source: 'model', outcome: 'denied', duration: 1, error: 'blocked' }]);
    const { rerender } = render(<AgentActivityPanel operationId={null} />);
    expect(screen.getByText('No events yet')).toBeInTheDocument();
    rerender(<AgentActivityPanel operationId="op" />);
    await waitFor(() => expect(screen.getByText('denied')).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText('Filter agent events'), { target: { value: 'missing' } });
    expect(screen.getByText('No events yet')).toBeInTheDocument();
  });
});
