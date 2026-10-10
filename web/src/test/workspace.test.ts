import { describe, expect, it } from 'vitest';
import { filterSamples, guessLanguage, initialWorkspaceState, workspaceReducer } from '../state/workspace';

describe('workspace reducer', () => {
  it('creates empty files, tracks edits and saved state, and switches tabs', () => {
    let s = workspaceReducer(initialWorkspaceState, { type: 'newFile', id: 'a' });
    expect(s.files.a.content).toBe('');
    s = workspaceReducer(s, { type: 'edit', id: 'a', content: 'x' });
    expect(s.files.a.dirty).toBe(true);
    s = workspaceReducer(s, { type: 'markSaved', id: 'a' });
    expect(s.files.a.dirty).toBe(false);
    s = workspaceReducer(s, { type: 'newFile', id: 'b' });
    expect(workspaceReducer(s, { type: 'switchFile', id: 'a' }).activeId).toBe('a');
  });

  it('copies a sample and focuses a clean copy on repeat', () => {
    const opened = workspaceReducer(initialWorkspaceState, { type: 'openSample', id: 's1', name: 'x.py', content: 'print(1)', language: 'python', sampleId: 'sample' });
    expect(opened.files.s1.origin).toBe('sample');
    expect(workspaceReducer(opened, { type: 'openSample', id: 's2', name: 'x.py', content: 'print(1)', language: 'python', sampleId: 'sample' }).order).toEqual(['s1']);
    const dirty = workspaceReducer(opened, { type: 'edit', id: 's1', content: 'changed' });
    expect(workspaceReducer(dirty, { type: 'openSample', id: 's2', name: 'x.py', content: 'print(1)', language: 'python', sampleId: 'sample' }).files.s2.name).toBe('x (2).py');
  });

  it('opens files, closes tabs, and rejects stale analysis', () => {
    let s = workspaceReducer(initialWorkspaceState, { type: 'openFiles', files: [{ id: 'a', name: 'main.py', content: 'x' }] });
    s = workspaceReducer(s, { type: 'edit', id: 'a', content: 'y' });
    expect(workspaceReducer(s, { type: 'setResult', id: 'a', result: null, version: 0 }).files.a.resultVersion).toBe(-1);
    expect(workspaceReducer(s, { type: 'closeFile', id: 'a' }).activeId).toBeNull();
  });

  it('guesses only from strong signals and filters sample groups', () => {
    expect(guessLanguage('print(x)')).toBeNull();
    expect(guessLanguage('def run(self): pass')).toBe('python');
    expect(guessLanguage('const app = () => {}')).toBe('javascript');
    const samples = [{ language: 'python', title: 'SQL Injection' }, { language: 'java', title: 'Prepared Statement' }];
    expect(filterSamples(samples, 'java')).toEqual([samples[1]]);
    expect(filterSamples(samples, null, 'sql', true)).toEqual([samples[0]]);
  });
});
