import type { PatchProposal } from '../../api/client';

export type FixStage =
  | 'idle'
  | 'proposing'
  | 'review'
  | 'applying'
  | 'verifying'
  | 'report'
  | 'stale'
  | 'malformed'
  | 'verification-failed'
  | 'missing-tools'
  | 'error';
export interface FixMachine {
  stage: FixStage;
  proposal: PatchProposal | null;
  report: Record<string, unknown> | null;
  error: string | null;
  appliedSourceVersion: number | null;
}
export const initialFixMachine: FixMachine = {
  stage: 'idle',
  proposal: null,
  report: null,
  error: null,
  appliedSourceVersion: null,
};
export type FixAction =
  | { type: 'propose' }
  | { type: 'proposal'; proposal: PatchProposal }
  | { type: 'apply' }
  | { type: 'verifying' }
  | { type: 'report'; report: Record<string, unknown>; sourceVersion: number | null }
  | {
      type: 'failure';
      stage: 'stale' | 'malformed' | 'verification-failed' | 'missing-tools' | 'error';
      message: string;
    }
  | { type: 'reset' };
export function fixReducer(state: FixMachine, action: FixAction): FixMachine {
  switch (action.type) {
    case 'propose':
      return { ...initialFixMachine, stage: 'proposing' };
    case 'proposal':
      return { ...state, stage: 'review', proposal: action.proposal, error: null };
    case 'apply':
      return { ...state, stage: 'applying', error: null };
    case 'verifying':
      return { ...state, stage: 'verifying' };
    case 'report':
      return {
        ...state,
        stage: 'report',
        report: action.report,
        appliedSourceVersion: action.sourceVersion,
        error: null,
      };
    case 'failure':
      return { ...state, stage: action.stage, error: action.message };
    case 'reset':
      return initialFixMachine;
  }
}

export function outcomeLabel(report: Record<string, unknown>): string {
  const raw = report.outcome;
  return raw === 'Verified for specified checks' ||
    raw === 'Partially verified' ||
    raw === 'Verification failed' ||
    raw === 'Inconclusive'
    ? raw
    : 'Inconclusive';
}

export function verificationCounts(report: Record<string, unknown>) {
  const list = (key: string) => (Array.isArray(report[key]) ? (report[key] as unknown[]) : []);
  return {
    resolved: list('resolved'),
    remaining: list('remaining'),
    introduced: list('introduced'),
    unverified: list('unverified'),
  };
}

export function missingVerificationTools(report: Record<string, unknown>): boolean {
  const tools = report.tools;
  return (
    Array.isArray(tools) &&
    tools.some((value: unknown) => {
      if (!value || typeof value !== 'object') return false;
      const tool = value as Record<string, unknown>;
      return (
        tool.available === false ||
        ['unavailable', 'failed', 'timeout'].includes(String(tool.status))
      );
    })
  );
}
