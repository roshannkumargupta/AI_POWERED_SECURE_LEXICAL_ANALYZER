import { describe, expect, it } from 'vitest';
import type { PatchProposal } from '../../api/client';
import {
  fixReducer,
  initialFixMachine,
  missingVerificationTools,
  outcomeLabel,
  verificationCounts,
} from './machine';

const proposal: PatchProposal = {
  id: 'p1',
  source_hash: 'a'.repeat(64),
  source_version: 1,
  target_finding_id: 'f1',
  origin: 'rule',
  edits: [],
  diff: '',
  rationale: '',
  expected_outcome: '',
  assumptions: [],
  risks: [],
  created_at: '',
};

describe('fix workflow state machine', () => {
  it('advances proposal, review, verify and report, and exposes explicit failure states', () => {
    let state = fixReducer(initialFixMachine, { type: 'propose' });
    expect(state.phase).toBe('proposing');
    state = fixReducer(state, { type: 'proposal', proposal });
    expect(state.phase).toBe('review');
    state = fixReducer(state, { type: 'apply' });
    expect(fixReducer(state, { type: 'verifying' }).phase).toBe('verifying');
    expect(fixReducer(state, { type: 'failure', phase: 'stale', message: 'stale' }).phase).toBe(
      'stale'
    );
    expect(
      fixReducer(state, { type: 'failure', phase: 'malformed', message: 'bad edits' }).phase
    ).toBe('malformed');
    expect(
      fixReducer(state, { type: 'failure', phase: 'verification-failed', message: 'failed' }).phase
    ).toBe('verification-failed');
    expect(
      fixReducer(state, { type: 'failure', phase: 'missing-tools', message: 'missing' }).phase
    ).toBe('missing-tools');
  });

  it('reports outcome labels, counts, and missing verifier tools from fixture data', () => {
    const fixture = {
      outcome: 'Partially verified',
      resolved: [{ id: 'a' }],
      remaining: [{ id: 'b' }],
      introduced: [],
      unverified: [{ id: 'c' }],
      tools: [{ name: 'compiler', available: false, status: 'unavailable' }],
    };
    expect(outcomeLabel(fixture)).toBe('Partially verified');
    expect(verificationCounts(fixture)).toEqual({
      resolved: [{ id: 'a' }],
      remaining: [{ id: 'b' }],
      introduced: [],
      unverified: [{ id: 'c' }],
    });
    expect(missingVerificationTools(fixture)).toBe(true);
    expect(outcomeLabel({ outcome: 'unknown' })).toBe('Inconclusive');
  });
});
