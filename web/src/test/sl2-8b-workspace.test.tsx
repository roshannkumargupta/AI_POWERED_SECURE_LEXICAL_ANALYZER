import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { SL28bWorkspace, View } from '../components/SL28bWorkspace';

const capabilities = {
  ai: { provider: 'ollama', configured: false, reachable: false, model: 'test-model', processing_location: 'local', consent_required: false, remote_consented: false },
  features: { build_with_ai: false, fix_with_ai: false },
  languages: [{ id: 'python', name: 'Python' }], tools: [],
};
const props = (view: View) => ({ view, onView: vi.fn(), source: 'print(1)\n', language: 'python', filename: 'sample.py', sourceVersion: 1, capabilities, sessionId: 'session-test-id-1234', selectedFinding: null, selectedToken: null, findings: [], onSelectFinding: vi.fn(), onNavigate: vi.fn(), onCandidate: vi.fn(), onSourceChange: vi.fn(), onDataFlow: vi.fn(), theme: 'light' as const, onThemeChange: vi.fn() });

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe('SL2-8b API workspace', () => {
  it('loads lexical and syntax diagnostics from the stage APIs and groups real results', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      return new Response(JSON.stringify(url.endsWith('/lexical')
        ? { diagnostics: [], tools: [], omissions: [] }
        : { analysis_id: 'a1', diagnostics: [{ id: 'd1', category: 'syntax', severity: 'error', message: 'missing delimiter', produced_by: 'parser', certainty: 'definitive', range: { start_line: 1, start_col: 7, end_line: 1, end_col: 8 } }], tools: [], omissions: [], syntax_status: { status: 'issues' } }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    });
    render(<SL28bWorkspace {...props('problems')} />);
    await screen.findByText(/missing delimiter/);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(screen.getByText('syntax')).toBeTruthy();
  });

  it('keeps generation disabled and gives an unavailable explanation when no provider exists', () => {
    render(<SL28bWorkspace {...props('build')} />);
    expect(screen.getByRole('button', { name: 'Generate' })).toBeDisabled();
    expect(screen.getByText(/no candidate is simulated/i)).toBeTruthy();
  });

  it('shows actual API errors instead of a successful placeholder', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ detail: 'remote source consent required' }), { status: 403, headers: { 'Content-Type': 'application/json' } }));
    const p = { ...props('explain'), capabilities: { ...capabilities, ai: { ...capabilities.ai, configured: true, reachable: true } } };
    render(<SL28bWorkspace {...p} />);
    fireEvent.click(screen.getByRole('button', { name: 'Explain selected evidence' }));
    await waitFor(() => expect(screen.getByRole('alert').textContent).toContain('remote source consent required'));
  });

  it('does not change source on proposal and applies only after the explicit Apply action', async () => {
    const onSourceChange = vi.fn();
    const selectedFinding = { id: 'finding-1', title: 'finding', range: { start_line: 1, start_col: 1, end_line: 1, end_col: 2 } };
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith('/fixes/propose')) return new Response(JSON.stringify({ proposal: { id: 'proposal-1', origin: 'rule', diff: '-x\n+y', source_hash: 'hash', source_version: 1, target_finding_id: 'finding-1', edits: [], rationale: 'test rationale' } }), { status: 200 });
      return new Response(JSON.stringify({ applied: true, source: 'print(2)\n', source_version: 2, verification: { outcome: 'Partially verified', resolved: [], remaining: [], introduced: [], unverified: [] } }), { status: 200 });
    });
    render(<SL28bWorkspace {...props('fix')} selectedFinding={selectedFinding} onSourceChange={onSourceChange} />);
    fireEvent.click(screen.getByRole('button', { name: 'Propose rule fix' }));
    await screen.findByText(/test rationale/);
    expect(onSourceChange).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Apply Fix' }));
    await waitFor(() => expect(onSourceChange).toHaveBeenCalledWith('print(2)\n'));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
