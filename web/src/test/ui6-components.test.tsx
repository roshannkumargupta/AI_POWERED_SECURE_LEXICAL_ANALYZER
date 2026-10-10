import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { FlyoutPanel } from '../components/FlyoutPanel';
import { ExplanationPanel } from '../components/ExplanationPanel';
import { TopBar } from '../components/TopBar';
import type { AnalysisResult, Finding, SampleItem } from '../api/client';

const sample = (id: string, language: string, title = id, level = 'basic'): SampleItem => ({
  id,
  language,
  title,
  filename: `${id}.${language === 'python' ? 'py' : 'js'}`,
  code: 'print(1)',
  description: 'sample',
  category: 'basic',
  level,
});
const noop = vi.fn();
const flyoutProps = {
  files: [],
  activeId: null,
  samples: [
    sample('py-a', 'python', 'Python sample'),
    sample('java-a', 'java', 'Java sample'),
    sample('py-ui5-security', 'python', 'Target Demo - Security'),
    sample('py-ui5-lexical', 'python', 'Target Demo - Lexical Error'),
  ],
  language: 'python',
  onClose: noop,
  onNew: noop,
  onOpen: noop,
  onFolder: noop,
  onSave: noop,
  onSwitch: noop,
  onCloseFile: noop,
  onSample: noop,
};
const unsafeFinding: Finding = {
  id: 'unsafe',
  rule_id: 'APS-PY-CMD-001',
  title: 'Command injection',
  message: 'Unsafe command',
  explanation: 'User input reaches a shell.',
  cwe: 'CWE-78',
  severity: 'critical',
  label: 'MALICIOUS',
  confidence: 0.9,
  range: { start_line: 1, start_col: 1, end_line: 1, end_col: 10 },
  evidence: {},
  taint_path: [],
  fixes: [],
  sources: ['rule'],
  attack: ['T1059'],
};
const analysis: AnalysisResult = {
  language: 'python',
  filename: 'sample.py',
  tokens: [
    {
      token: 'os.system',
      token_type: 'IDENTIFIER',
      range: { start_line: 1, start_col: 1, end_line: 1, end_col: 10 },
      label: 'MALICIOUS',
      score: 0.9,
    },
  ],
  findings: [unsafeFinding],
  summary: {
    critical: 1,
    high: 0,
    medium: 0,
    low: 0,
    info: 0,
    score: 75,
    tokens_total: 1,
    tokens_malicious: 1,
    tokens_suspicious: 0,
  },
  engine: {
    ml_mode: 'off',
    ml_model_id: '',
    taint: 'ast',
    version: '',
    elapsed_ms: 1,
    parser: 'python-ast',
  },
};

describe('UI-6 flyouts and top bar', () => {
  it('shows active-language samples first and exposes other languages on request', () => {
    render(<FlyoutPanel {...flyoutProps} mode="samples" />);
    expect(screen.getByText('Target Demo - Security')).toBeTruthy();
    expect(screen.getByText('Target Demo - Lexical Error')).toBeTruthy();
    expect(screen.queryByText('Java sample')).toBeNull();
    fireEvent.click(screen.getByText('Show all languages'));
    expect(screen.getByText('Java')).toBeTruthy();
    fireEvent.click(screen.getAllByText('Basic')[1]);
    expect(screen.getByText('Java sample')).toBeTruthy();
  });
  it('offers file actions, open files, unsaved state, and close by keyboard or button controls', () => {
    const onSwitch = vi.fn();
    const onCloseFile = vi.fn();
    render(
      <FlyoutPanel
        {...flyoutProps}
        mode="files"
        files={[{ id: 'one', name: 'main.py', language: 'python', dirty: true }]}
        activeId="one"
        onSwitch={onSwitch}
        onCloseFile={onCloseFile}
      />
    );
    expect(screen.getByText('New file')).toBeTruthy();
    expect(screen.getByText('Open folder')).toBeTruthy();
    expect(screen.getByLabelText('Unsaved changes')).toBeTruthy();
    fireEvent.click(screen.getByText('main.py'));
    expect(onSwitch).toHaveBeenCalledWith('one');
    fireEvent.click(screen.getByLabelText('Close main.py'));
    expect(onCloseFile).toHaveBeenCalledWith('one');
  });
  it('shows shortcut and factual engine help without ungrounded ML probabilities', () => {
    render(
      <FlyoutPanel {...flyoutProps} mode="help" engine={{ parser: 'python-ast', ml_mode: 'off' }} />
    );
    expect(screen.getByText('Ctrl+Shift+P')).toBeTruthy();
    expect(screen.getByText('Parser: Python ast; other languages lexer-only')).toBeTruthy();
    expect(screen.getByText(/ML status: off/)).toBeTruthy();
  });
  it('lists open files in the file pill menu and safely renders finding text', () => {
    const onSwitch = vi.fn();
    render(
      <TopBar
        language="auto"
        languages={[]}
        onChangeLanguage={noop}
        isAnalyzing={false}
        onAnalyze={noop}
        onFixAll={noop}
        onDownload={noop}
        onNewFile={noop}
        onOpenFile={noop}
        onCloseFile={noop}
        filename="main.py"
        files={[{ id: 'one', name: 'main.py', dirty: true }]}
        activeFileId="one"
        onSwitchFile={onSwitch}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Open file list' }));
    fireEvent.click(screen.getByRole('menuitem', { name: /main.py/ }));
    expect(onSwitch).toHaveBeenCalledWith('one');
    const { container } = render(
      <ExplanationPanel
        analysis={analysis}
        source="os.system('x')"
        selectedIndex={0}
        selectedFinding={unsafeFinding}
        onApplyFix={noop}
        onFalsePositive={noop}
      />
    );
    expect(screen.getByText('Valid but insecure')).toBeTruthy();
    expect(screen.getByText('CWE-78')).toBeTruthy();
    expect(screen.getByText('ATT&CK T1059')).toBeTruthy();
    expect(container.querySelector('img')).toBeNull();
  });
});
