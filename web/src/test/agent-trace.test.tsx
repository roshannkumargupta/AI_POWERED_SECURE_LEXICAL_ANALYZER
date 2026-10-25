import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AgentTraceTab } from '../components/AgentTraceTab';
import type { AgentTraceStep } from '../api/client';

describe('AgentTraceTab Component', () => {
  const sampleTrace: AgentTraceStep[] = [
    {
      step: 1,
      agent: 'LexerAgent',
      stage: 'lexical',
      action: 'unicode_scan',
      args_summary: 'source=...',
      reason: 'Scanning source code for hidden Unicode bidi characters.',
      observation_summary: 'findings_count=0, has_bidi=false',
      decision_source: 'rules',
      ms: 1.4,
      accepted: true,
    },
    {
      step: 2,
      agent: 'ParserAgent',
      stage: 'syntax',
      action: 'parse_structure',
      args_summary: 'language=python',
      reason: 'Building StructTree AST with panic recovery.',
      observation_summary: 'quality_score=1.0, errors=0',
      decision_source: 'llm',
      ms: 12.8,
      accepted: true,
    },
    {
      step: 3,
      agent: 'FixAgent',
      stage: 'fix',
      action: 'apply_fix_to_copy',
      args_summary: 'fix_id=../../etc/passwd',
      reason: 'Attacker attempting path traversal injection',
      observation_summary: 'Execution error: Path traversal forbidden',
      decision_source: 'llm',
      ms: 3.1,
      accepted: false,
      rejection_reason: 'Path traversal or malformed identifier rejected',
    },
  ];

  it('renders stages, decision badges, and metrics safely', () => {
    render(
      <AgentTraceTab
        trace={sampleTrace}
        agentMode="rules"
      />
    );

    // Verify stage headers
    expect(screen.getByText('LEXICAL STAGE')).toBeTruthy();
    expect(screen.getByText('SYNTAX STAGE')).toBeTruthy();
    expect(screen.getByText('FIX STAGE')).toBeTruthy();

    // Verify decision badges
    expect(screen.getByText('Rule decided')).toBeTruthy();
    expect(screen.getAllByText('AI decided').length).toBe(2);

    // Verify status badges
    expect(screen.getAllByText('Accepted').length).toBe(2);
    expect(screen.getByText('Rejected')).toBeTruthy();
    expect(screen.getByText('Path traversal or malformed identifier rejected')).toBeTruthy();

    // Verify security telemetry
    expect(screen.getByText('Outbound network calls:')).toBeTruthy();
    expect(screen.getByText('0')).toBeTruthy();
    expect(screen.getByText('RulesPlanner')).toBeTruthy();
  });

  it('renders malicious reason string strictly as plain text without HTML injection', () => {
    const maliciousTrace: AgentTraceStep[] = [
      {
        step: 1,
        agent: 'SemanticAgent',
        stage: 'semantic',
        action: 'run_rules',
        args_summary: '',
        reason:
          '<img src="x" onerror="window.maliciousHacked=true" /><script>alert("hacked")</script><b>Bold exploit</b>',
        observation_summary: '<svg onload="alert(1)">',
        decision_source: 'llm',
        ms: 5.0,
        accepted: true,
      },
    ];

    const { container } = render(<AgentTraceTab trace={maliciousTrace} agentMode="rules" />);

    // Verify no injected executable DOM nodes
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('svg[onload]')).toBeNull();

    // The text content is displayed safely as plain text
    const reasonElement = container.querySelector('[data-qa="trace-reason"]');
    expect(reasonElement).toBeTruthy();
    expect(reasonElement?.textContent).toContain(
      '<img src="x" onerror="window.maliciousHacked=true" />'
    );
    expect(reasonElement?.innerHTML).not.toContain('<img');
  });

  it('renders informative placeholder when trace is empty', () => {
    render(<AgentTraceTab trace={[]} agentMode="off" />);
    expect(screen.getByText('No Agent Trace Available')).toBeTruthy();
  });
});
