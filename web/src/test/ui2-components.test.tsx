import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ProblemsPanel } from '../components/ProblemsPanel';
import { CommandPalette } from '../components/CommandPalette';
import { FindingPanel } from '../components/FindingPanel';
import { TopBar } from '../components/TopBar';
import { Finding } from '../api/client';

const finding = (id: string, severity: Finding['severity'], line: number, cwe = 'CWE-89'): Finding => ({
  id, severity, cwe, rule_id: 'SQL_INJECTION', title: `${id} finding`, message: 'Unsafe query', explanation: 'User input is joined.',
  label: 'MALICIOUS', confidence: 0.8, range: { start_line: line, start_col: 2, end_line: line, end_col: 8 },
  evidence: {}, taint_path: [], fixes: [], sources: ['rule'],
});

describe('UI-2 Problems panel', () => {
  it('filters, sorts, and groups findings by their CWE category', () => {
    const select = vi.fn();
    const Harness = () => { const [filter, setFilter] = React.useState<'all' | Finding['severity']>('all'); return <ProblemsPanel findings={[finding('medium', 'medium', 1), finding('critical', 'critical', 9, 'CWE-79')]} selectedFindingId={null} filter={filter} onSelectFilter={setFilter} onSelectFinding={select} onNextFinding={() => {}} onPrevFinding={() => {}}/>; };
    render(<Harness/>);
    fireEvent.change(screen.getByLabelText('Sort problems'), { target: { value: 'location' } });
    fireEvent.click(screen.getByLabelText('Filter by critical'));
    expect(screen.getByText('critical finding')).toBeTruthy();
    expect(screen.queryByText('medium finding')).toBeNull();
    fireEvent.click(screen.getByLabelText('Filter by all'));
    fireEvent.click(screen.getByLabelText('Group'));
    expect(screen.getByText(/XSS/)).toBeTruthy();
    fireEvent.click(screen.getByText(/critical finding/));
    expect(select).toHaveBeenCalledWith('critical');
  });
});

describe('UI-2 command palette', () => {
  it('fuzzy filters and runs the selected command on Enter', () => {
    const run = vi.fn(); const close = vi.fn();
    render(<CommandPalette open commands={[{ label: 'Open File', run }, { label: 'Analyze', run: vi.fn() }]} onClose={close}/>);
    const input = screen.getByLabelText('Filter commands');
    fireEvent.change(input, { target: { value: 'opfl' } });
    expect(screen.getByText('Open File')).toBeTruthy();
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(run).toHaveBeenCalledOnce(); expect(close).toHaveBeenCalledOnce();
  });
});

describe('UI-2 Finding panel states', () => {
  const makeFinding = (tainted: boolean, verified: boolean): Finding => ({
    ...finding('sql', 'high', 4),
    taint_path: tainted ? [{ step: 'source', range: { start_line: 2, start_col: 1, end_line: 2, end_col: 7 }, text: 'request.id', note: 'User input' }] : [],
    fixes: [{ id: 'fix', finding_id: 'sql', title: 'Use parameters', description: 'Bind the value.', confidence: 'safe', kind: 'replace', edits: [], verification: { syntax_ok: verified, finding_gone: verified, new_findings: [], verified, notes: '' } }],
  });
  const renderFinding = (tainted: boolean, verified: boolean) => render(<FindingPanel activeTab="finding" onChangeTab={() => {}} selectedFinding={makeFinding(tainted, verified)} summary={null} mlInsights={null} isLoadingInsights={false} mlMode="on" onApplyFix={() => {}} onOpenDiff={() => {}} onJumpToStep={() => {}} onToggleDataFlow={() => {}} isDataFlowActive={false} onMarkFalsePositive={() => {}} analysis={null} selectedTokenIndex={null} tokenMap="off" onTokenMap={() => {}} tokenCategory="" onTokenCategory={() => {}} onSelectToken={() => {}} onLoadTokenML={() => {}} onSelectFindingById={() => {}}/>);

  it('shows taint evidence and only enables apply for verified-safe fixes', () => {
    const { unmount } = renderFinding(true, true);
    expect(screen.getByText('SOURCE')).toBeTruthy();
    expect(screen.getByText('Verified after re-analysis')).toBeTruthy();
    expect(screen.getByText('Apply Verified Fix')).toBeTruthy();
    unmount();
    renderFinding(false, false);
    expect(screen.getByText('Review needed')).toBeTruthy();
    expect(screen.queryByText('SOURCE')).toBeNull();
    expect(screen.queryByText('Apply Verified Fix')).toBeNull();
  });

  it('reports ML-off state without claiming inference ran', () => {
    render(<FindingPanel activeTab="ml" onChangeTab={() => {}} selectedFinding={null} summary={null} mlInsights={null} isLoadingInsights={false} mlMode="off" onApplyFix={() => {}} onOpenDiff={() => {}} onJumpToStep={() => {}} onToggleDataFlow={() => {}} isDataFlowActive={false} onMarkFalsePositive={() => {}} analysis={null} selectedTokenIndex={null} tokenMap="off" onTokenMap={() => {}} tokenCategory="" onTokenCategory={() => {}} onSelectToken={() => {}} onLoadTokenML={() => {}} onSelectFindingById={() => {}}/>);
    expect(screen.getByText(/ML OFF/)).toBeTruthy();
    expect(screen.getByText(/Rules and Taint remain active/)).toBeTruthy();
  });
});

describe('UI-2 Fix all control', () => {
  const renderTop = (safeFixCount: number) => render(<TopBar language="auto" languages={[]} onChangeLanguage={() => {}} isAnalyzing={false} onAnalyze={() => {}} onFixAll={() => {}} onDownload={() => {}} onNewFile={() => {}} onOpenFile={() => {}} onCloseFile={() => {}} safeFixCount={safeFixCount}/>);
  it('is disabled with the specified tooltip when no verified safe fixes exist', () => {
    renderTop(0); const button = screen.getByRole('button', { name: 'Fix All Safe Issues' });
    expect((button as HTMLButtonElement).disabled).toBe(true); expect(button.getAttribute('title')).toBe('No verified fixes available');
  });
  it('is enabled and counted when verified safe fixes exist', () => {
    renderTop(2); const button = screen.getByRole('button', { name: 'Fix All Safe Issues' });
    expect((button as HTMLButtonElement).disabled).toBe(false); expect(button.textContent).toContain('Fix all (2)');
  });
});
