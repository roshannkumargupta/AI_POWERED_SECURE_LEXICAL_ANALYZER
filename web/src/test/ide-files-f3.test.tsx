import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import type { CapabilitiesResponse, SampleItem } from '../api/client';
import { SamplesSidebar } from '../ide/sidebar/SamplesSidebar';
import { NewFileDialog } from '../ide/sidebar/NewFileDialog';
import { ideReducer, initialIDEState } from '../ide/state/store';

const sample = (id: string, language: string, category: string): SampleItem => ({ id, language, category, filename: `${id}.${language === 'python' ? 'py' : language === 'java' ? 'java' : language === 'javascript' ? 'js' : 'cpp'}`, title: id, code: 'code', description: id, expect: { findings: [{ rule_id: `${id}-rule` }] } });
const samples = [sample('valid-py', 'python', 'valid'), sample('lex-py', 'python', 'lexical-errors'), sample('syntax-java', 'java', 'syntax-errors'), sample('sec-js', 'javascript', 'security'), sample('adv-cpp', 'cpp', 'adversarial')];
const caps = { languages: [
  { id: 'python', name: 'Python', extensions: ['.py'] }, { id: 'java', name: 'Java', extensions: ['.java'] },
  { id: 'javascript', name: 'JavaScript', extensions: ['.js'] }, { id: 'cpp', name: 'C / C++', extensions: ['.cpp', '.cc'] },
] } as CapabilitiesResponse;

describe('F3 sample catalog and file creation', () => {
  beforeEach(() => localStorage.clear());
  it('groups API samples by language and category, displays empty groups, and persists expansion', () => {
    render(<SamplesSidebar samples={samples} unavailable={false} onOpen={() => {}} />);
    expect(screen.getByRole('button', { name: /Python/ })).toHaveTextContent('2');
    expect(screen.getByRole('button', { name: /^Java 1$/ })).toHaveTextContent('1');
    expect(screen.getByRole('button', { name: /JavaScript/ })).toHaveTextContent('1');
    expect(screen.getByRole('button', { name: /C \/ C\+\+/ })).toHaveTextContent('1');
    for (const item of samples) expect(screen.getByText(item.filename)).toBeInTheDocument();
    expect(screen.getAllByText('none').length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: /Python/ }));
    expect(localStorage.getItem('securelex.ide.samples-expanded.v1')).toContain('python');
  });
  it('search filters sample filenames across all language sections', () => {
    render(<SamplesSidebar samples={samples} unavailable={false} onOpen={() => {}} />);
    fireEvent.change(screen.getByRole('textbox', { name: /Search samples/ }), { target: { value: 'syntax-java' } });
    expect(screen.getByText('syntax-java.java')).toBeInTheDocument();
    expect(screen.queryByText('valid-py.py')).not.toBeInTheDocument();
  });
  it('creates a file through the dialog and rejects duplicates and path separators', () => {
    const onCreate = vi.fn();
    render(<NewFileDialog open capabilities={caps} samples={samples} existingNames={['already.py']} nextIndex={2} onClose={() => {}} onCreate={onCreate} />);
    const filename = screen.getByRole('textbox', { name: 'File name' });
    expect(filename).toHaveValue('untitled-2.py');
    fireEvent.change(filename, { target: { value: 'already.py' } }); fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(screen.getByRole('alert')).toHaveTextContent('already open');
    fireEvent.change(filename, { target: { value: 'folder/new.py' } }); fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(screen.getByRole('alert')).toHaveTextContent('without folder separators');
    fireEvent.change(filename, { target: { value: 'hello.java' } });
    expect(screen.getByRole('combobox', { name: 'New file language' })).toHaveValue('java');
    fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(onCreate).toHaveBeenCalledWith({ name: 'hello.java', language: 'java', source: '' });
  });
  it('uses real API sample source as the vulnerable starter', () => {
    const onCreate = vi.fn();
    render(<NewFileDialog open capabilities={caps} samples={samples} existingNames={[]} nextIndex={1} onClose={() => {}} onCreate={onCreate} />);
    fireEvent.change(screen.getByRole('combobox', { name: 'New file language' }), { target: { value: 'javascript' } });
    fireEvent.change(screen.getByRole('combobox', { name: 'Starter content' }), { target: { value: 'vulnerable' } });
    fireEvent.change(screen.getByRole('textbox', { name: 'File name' }), { target: { value: 'attack.js' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({ source: 'code', language: 'javascript' }));
  });
  it('renames documents and language switches keep the source byte-for-byte', () => {
    const original = { id: 'doc', name: 'work.py', language: 'python', source: 'print("keep me")\r\n', savedSource: '', sourceVersion: 1, dirty: true, origin: 'new' as const };
    let state = ideReducer(initialIDEState, { type: 'document/add', document: original });
    state = ideReducer(state, { type: 'document/rename', id: 'doc', name: 'work.java' });
    state = ideReducer(state, { type: 'document/language', id: 'doc', language: 'java' });
    expect(state.documents[0]).toMatchObject({ name: 'work.java', language: 'java', source: original.source, dirty: true });
  });
});
