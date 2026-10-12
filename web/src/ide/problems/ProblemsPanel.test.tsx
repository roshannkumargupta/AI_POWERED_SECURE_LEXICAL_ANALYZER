import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { DiagnosticV2 } from '../../api/client';
import { ProblemsPanel } from './ProblemsPanel';

const diag = (id: string, category: DiagnosticV2['category'], message: string): DiagnosticV2 => ({ id, language: 'cpp', range: { start_line: 2, start_col: 1, end_line: 2, end_col: 4 }, category, severity: 'high', message, related_evidence: [], produced_by: 'test-rule', certainty: 'heuristic' });

describe('ProblemsPanel', () => {
  it('groups counts, filters and searches diagnostics without treating incomplete checks as clean', () => {
    const diagnostics = [diag('a', 'lexical', 'Bad token'), diag('b', 'syntax', 'Missing brace')];
    render(<ProblemsPanel diagnostics={diagnostics} result={{ omissions: ['parser timed out'], tools: [], lexical_status: { status: 'ok' }, syntax_status: { status: 'incomplete' }, semantic_status: { status: 'unavailable' } } as never} onSelect={vi.fn()} />);
    expect(screen.getAllByText(/Analysis incomplete/).length).toBeGreaterThan(0);
    expect(screen.getByRole('option', { name: 'Lexical (1)' })).toBeTruthy();
    fireEvent.change(screen.getByRole('textbox', { name: 'Search problems' }), { target: { value: 'Missing' } });
    expect(screen.getByText('Missing brace')).toBeTruthy();
    expect(screen.queryByText('Bad token')).toBeNull();
  });
  it('only reports no findings after checks ran', () => {
    const { rerender } = render(<ProblemsPanel diagnostics={[]} result={null} onSelect={vi.fn()} />);
    expect(screen.getByText('Run Analyze to see diagnostics.')).toBeTruthy();
    rerender(<ProblemsPanel diagnostics={[]} result={{ omissions: [], tools: [{ executed: true, available: true, status: 'ok', name: 'lexer' }] } as never} onSelect={vi.fn()} />);
    expect(screen.getByText('No findings detected by checks run')).toBeTruthy();
  });
});
