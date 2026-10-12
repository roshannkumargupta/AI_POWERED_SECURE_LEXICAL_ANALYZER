import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient, type SafetyRunResult, type SafetyScenario } from '../../api/client';
import { SafetyLab } from './SafetyLab';

vi.mock('../../api/client', () => ({ apiClient: { getSafetyScenarios: vi.fn(), runSafety: vi.fn(), getSafetyResult: vi.fn(), exportReport: vi.fn() } }));
const scenario: SafetyScenario = { id:'fixture', title:'Fixture scenario', risk:'medium', description:'A served scenario.', languages:['python'], expected_safe_behavior:'Preserve source.' };
const outcomes: Array<SafetyRunResult['outcome']> = ['Attack resisted','Attack contained','Attack succeeded','Inconclusive','Verification failed',null];
const result = (outcome: SafetyRunResult['outcome']): SafetyRunResult => ({ run_id:'run-1', scenario_id:'fixture', source_hash:'hash', mode_label:'Deterministic harness - no model involved', configuration:{language:'python',mode:'HARNESS'}, scenario, timeline:[], agent_behavior:{}, operations:[], independent_verification:{}, assertions:[], outcome, limitations:[] });

describe('SafetyLab', () => {
  beforeEach(() => { vi.mocked(apiClient.getSafetyScenarios).mockResolvedValue([scenario]); vi.mocked(apiClient.runSafety).mockResolvedValue({run_id:'run-1'}); vi.mocked(apiClient.getSafetyResult).mockResolvedValue(result('Attack resisted')); });
  it('starts with empty run columns and uses the API scenario catalogue', async () => {
    render(<SafetyLab capabilities={null} source="" language="python" filename="x.py" sourceVersion={1} onReturn={vi.fn()}/>);
    expect(await screen.findByText('Fixture scenario')).toBeTruthy();
    expect(screen.getByText(/No run yet/)).toBeTruthy();
    expect(screen.getByText('No verification results yet.')).toBeTruthy();
    expect(screen.getByRole('option', { name: /Live/ })).toHaveProperty('disabled', true);
    fireEvent.click(screen.getByRole('button', { name: 'Export Report ▾' }));
    expect(screen.getByRole('menuitem', { name: 'Analysis report · JSON' })).toBeTruthy();
    expect(screen.getByRole('menuitem', { name: 'Tokens · CSV' })).toBeTruthy();
    expect(screen.getByRole('menuitem', { name: 'Safety report · JSON' })).toHaveProperty('disabled', true);
    fireEvent.click(screen.getByRole('button', {name:'Run scenario'}));
    expect(await screen.findByText('Deterministic harness - no model involved')).toBeTruthy();
  });
  it.each(outcomes)('renders verifier outcome %s as returned', async outcome => {
    vi.mocked(apiClient.getSafetyResult).mockResolvedValue(result(outcome));
    render(<SafetyLab capabilities={null} source="" language="python" filename="x.py" sourceVersion={1} onReturn={vi.fn()}/>);
    await screen.findByText('Fixture scenario');
    fireEvent.click(screen.getByRole('button', {name:'Run scenario'}));
    expect(await screen.findByText(outcome ?? 'Inconclusive', {selector:'.ide-safety-outcome'})).toBeTruthy();
  });
});
