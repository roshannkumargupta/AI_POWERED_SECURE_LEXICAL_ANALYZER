import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AnalysisResultV2, FixVerificationReport, PatchProposal } from '../../api/client';
import { apiClient } from '../../api/client';
import { FixWorkflowModal } from './FixWorkflowModal';

vi.mock('../../api/client', async () => {
  const actual = await vi.importActual<typeof import('../../api/client')>('../../api/client');
  return {
    ...actual,
    apiClient: {
      ...actual.apiClient,
      proposeFix: vi.fn(),
      verifyFix: vi.fn(),
      applyFixV2: vi.fn(),
      undoFix: vi.fn(),
      applyFixAll: vi.fn(),
    },
  };
});

const finding: AnalysisResultV2['security_findings'][number] = {
  id: 'f1',
  rule_id: 'R-1',
  title: 'Unsafe call',
  message: 'Finding detail',
  explanation: 'Evidence',
  severity: 'high',
  label: 'MALICIOUS',
  confidence: 0.9,
  range: { start_line: 1, start_col: 1, end_line: 1, end_col: 4 },
  evidence: {},
  taint_path: [],
  fixes: [],
  sources: ['rule'],
  kind: 'security',
  cwe: ['CWE-78'],
  taint_path_id: null,
  certainty: 'definitive',
  remediation: 'Use safe API',
  tool_provenance: ['rules'],
  safe_pattern: null,
  detectors_fired: [],
};
const proposal: PatchProposal = {
  id: 'p1',
  source_hash: 'a'.repeat(64),
  source_version: 1,
  target_finding_id: 'f1',
  origin: 'rule',
  edits: [{ range: { start_line: 1, start_col: 1, end_line: 1, end_col: 4 }, new_text: 'safe' }],
  diff: '',
  rationale: 'Replace unsafe call',
  expected_outcome: 'Finding resolved',
  assumptions: [],
  risks: [],
  created_at: '',
};
const report: FixVerificationReport = {
  outcome: 'Partially verified',
  resolved: [{ id: 'f1', message: 'Fixed' }],
  remaining: [{ id: 'f2', message: 'Still present' }],
  introduced: [],
  unverified: [{ id: 'u1', message: 'Not checked' }],
  tools: [{ name: 'parser', available: true, status: 'ok' }],
  quality_delta: {},
};
const props = {
  finding,
  documentId: 'doc1',
  activeDocumentId: 'doc1',
  source: 'bad\n',
  sourceVersion: 1,
  language: 'python',
  filename: 'main.py',
  sessionId: 'session',
  aiReady: false,
  remoteConsentRequired: false,
  remoteConsented: false,
  onConsent: vi.fn(async () => undefined),
  onSourceApplied: vi.fn(),
  onUndoApplied: vi.fn(),
  onClose: vi.fn(),
  onAskAI: vi.fn(),
};

describe('fix review modal', () => {
  beforeEach(() => vi.clearAllMocks());
  it('reviews a real diff, explicitly verifies before apply, renders report fixtures, and undoes', async () => {
    vi.mocked(apiClient.proposeFix).mockResolvedValue({ proposal, applied: false });
    vi.mocked(apiClient.verifyFix).mockResolvedValue({ proposal_id: 'p1', report, applied: false });
    vi.mocked(apiClient.applyFixV2).mockResolvedValue({
      applied: true,
      source: 'safe\n',
      source_version: 2,
      verification: report,
    });
    vi.mocked(apiClient.undoFix).mockResolvedValue({
      source: 'bad\n',
      source_hash: 'original',
      source_version: 3,
    });
    render(<FixWorkflowModal {...props} />);
    expect(await screen.findByText('+safe')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }));
    await waitFor(() => expect(apiClient.verifyFix).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(apiClient.applyFixV2).toHaveBeenCalledTimes(1));
    expect(props.onSourceApplied).toHaveBeenCalledWith('safe\n', 2);
    expect(await screen.findByText('Partially verified')).toBeTruthy();
    expect(screen.getByText('Still present')).toBeTruthy();
    expect(screen.getByText('Not checked')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Undo Changes' }));
    await waitFor(() => expect(props.onUndoApplied).toHaveBeenCalledWith('bad\n', 3));
  });

  it('rejects stale proposals and closes on Escape while trapping dialog focus', async () => {
    vi.mocked(apiClient.proposeFix).mockResolvedValue({ proposal, applied: false });
    const { rerender } = render(<FixWorkflowModal {...props} />);
    await screen.findByText('+safe');
    rerender(<FixWorkflowModal {...props} sourceVersion={2} />);
    await waitFor(() => expect(screen.getByText(/Stale source:/)).toBeTruthy());
    expect(screen.getByRole('button', { name: 'Apply' })).toBeDisabled();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(props.onClose).toHaveBeenCalled();
  });

  it('shows verifier failure without applying or offering an undo point', async () => {
    vi.mocked(apiClient.proposeFix).mockResolvedValue({ proposal, applied: false });
    vi.mocked(apiClient.verifyFix).mockResolvedValue({
      proposal_id: 'p1',
      report: {
        ...report,
        outcome: 'Verification failed',
        introduced: [{ id: 'new', message: 'New issue' }],
      },
      applied: false,
    });
    const { container } = render(<FixWorkflowModal {...props} />);
    await screen.findByText('+safe');
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }));
    await waitFor(() =>
      expect(container.querySelector('.ide-fix-outcome')?.textContent).toBe('Verification failed')
    );
    expect(screen.getByText('New issue')).toBeTruthy();
    expect(apiClient.applyFixV2).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: 'Undo Changes' })).toBeNull();
  });

  it('requests a rule proposal before an AI fallback and shows a reviewable result', async () => {
    vi.mocked(apiClient.proposeFix)
      .mockRejectedValueOnce(
        new Error('No automatic fix is available for this target; use Explain.')
      )
      .mockResolvedValueOnce({ proposal: { ...proposal, origin: 'ai' }, applied: false });
    render(<FixWorkflowModal {...props} aiReady />);
    expect(await screen.findByText('+safe')).toBeTruthy();
    expect(apiClient.proposeFix).toHaveBeenCalledTimes(2);
    expect(apiClient.proposeFix).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({ origin: 'rule', target: { kind: 'finding', id: 'f1' } }),
      expect.any(AbortSignal)
    );
    expect(apiClient.proposeFix).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({ origin: 'ai' }),
      expect.any(AbortSignal)
    );
  });

  it('ends no-fix failures visibly and offers Retry and Close controls', async () => {
    vi.mocked(apiClient.proposeFix).mockRejectedValue(
      new Error('No automatic fix is available for this finding; use Explain.')
    );
    render(<FixWorkflowModal {...props} />);
    expect(await screen.findByText(/No automatic fix is available/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Close fix review' })).toBeEnabled();
  });

  it('can always close while a proposal is still pending and aborts its request', async () => {
    let signal: AbortSignal | undefined;
    vi.mocked(apiClient.proposeFix).mockImplementation((_request, requestSignal) => {
      signal = requestSignal;
      return new Promise(() => undefined);
    });
    const { container } = render(<FixWorkflowModal {...props} />);
    await screen.findByText(/Preparing proposal/);
    fireEvent.mouseDown(container.querySelector('.ide-fix-overlay')!);
    expect(props.onClose).toHaveBeenCalled();
    expect(signal?.aborted).toBe(true);
  });

  it('reviews the fix-all list and only applies the unchanged reviewed diff', async () => {
    const preview = {
      new_source: 'safe\n',
      applied: ['fix-one'],
      skipped: [{ fix_id: 'fix-two', reason: 'Verifier inconclusive' }],
      diff: '--- a/main.py\n+++ b/main.py\n@@ -1 +1 @@\n-bad\n+safe',
      score_before: 70,
      score_after: 80,
      source_version: 1,
      applied_to_source: false,
    };
    vi.mocked(apiClient.applyFixAll)
      .mockResolvedValueOnce(preview)
      .mockResolvedValueOnce({ ...preview, applied_to_source: true, source_version: 2 });
    render(<FixWorkflowModal {...props} initialFixAll />);
    expect(await screen.findByText('fix-one')).toBeTruthy();
    expect(screen.getByText('fix-two: Verifier inconclusive')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Apply Fix All Safe' }));
    await waitFor(() => expect(props.onSourceApplied).toHaveBeenCalledWith('safe\n', 2));
    expect(apiClient.applyFixAll).toHaveBeenLastCalledWith(
      expect.objectContaining({ approved: true, approved_diff: preview.diff })
    );
  });
});
