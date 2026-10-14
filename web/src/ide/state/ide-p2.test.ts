import { describe, expect, it } from 'vitest';
import { fuzzyMatch, searchCommands } from './commands';
import { clampPanelHeight } from '../lib/panelResize';
import { ideReducer, initialIDEState, selectIsStale } from './store';
import type { AnalysisResultV2 } from '../../api/client';
import { displayEol, dimensionLabel, engineLabel } from '../lib/status';

const doc = {
  id: 'a',
  name: 'main.cpp',
  language: 'cpp',
  source: 'int x;',
  savedSource: 'int x;',
  sourceVersion: 1,
  dirty: false,
  origin: 'new' as const,
};

describe('P2 IDE state and command utilities', () => {
  it('adds, edits, renames, switches language without changing source, and closes documents', () => {
    let state = ideReducer(initialIDEState, { type: 'document/add', document: doc });
    state = ideReducer(state, { type: 'document/edit', id: 'a', source: 'int y;' });
    expect(state.documents[0].dirty).toBe(true);
    expect(selectIsStale(state, 'a')).toBe(true);
    state = ideReducer(state, { type: 'document/rename', id: 'a', name: 'renamed.cpp' });
    state = ideReducer(state, { type: 'document/language', id: 'a', language: 'python' });
    expect(state.documents[0]).toMatchObject({
      name: 'renamed.cpp',
      language: 'python',
      source: 'int y;',
    });
    state = ideReducer(state, { type: 'document/remove', id: 'a' });
    expect(state.documents).toHaveLength(0);
    expect(state.activeDocId).toBeNull();
  });

  it('fuzzy-searches enabled commands and excludes disabled commands', () => {
    expect(fuzzyMatch('tgl thm', 'Toggle Theme')).toBe(true);
    const commands = [
      { id: 'theme', title: 'Toggle Theme', enabled: () => true, run: () => undefined },
      { id: 'disabled', title: 'Toggle Panel', enabled: () => false, run: () => undefined },
    ];
    expect(searchCommands(commands, 'theme').map((item) => item.id)).toEqual(['theme']);
  });

  it('clamps panel height to the editor and panel minimums', () => {
    expect(clampPanelHeight(10, 720)).toBe(120);
    expect(clampPanelHeight(900, 720)).toBe(570);
    expect(clampPanelHeight(200, 720)).toBe(200);
  });

  it('derives status values from the document and backend state', () => {
    expect(displayEol('a\r\nb')).toBe('CRLF');
    expect(displayEol('a\nb')).toBe('LF');
    expect(dimensionLabel(null, 'lexical')).toBe('Not analysed');
    expect(engineLabel(null, true)).toBe('Engine unavailable');
  });

  it('keeps only current analysis results and discards out-of-order versions', () => {
    const current = {
      ...initialIDEState,
      documents: [doc],
      activeDocId: doc.id,
      analysis: {
        [doc.id]: { result: null, forSourceVersion: null, status: 'idle' as const, abort: null },
      },
    };
    const result = { source_version: 1 } as AnalysisResultV2;
    const accepted = ideReducer(current, {
      type: 'analysis/success',
      id: doc.id,
      result,
      version: 1,
    });
    expect(accepted.analysis[doc.id]).toMatchObject({ status: 'ok', forSourceVersion: 1 });
    const edited = ideReducer(accepted, {
      type: 'document/edit',
      id: doc.id,
      source: 'int changed;',
    });
    expect(selectIsStale(edited, doc.id)).toBe(true);
    expect(ideReducer(edited, { type: 'analysis/success', id: doc.id, result, version: 1 })).toBe(
      edited
    );
    expect(ideReducer(current, { type: 'analysis/success', id: doc.id, result, version: 2 })).toBe(
      current
    );
  });

  it('switches the analysis language without rewriting the source and marks prior results stale', () => {
    const state = {
      ...initialIDEState,
      documents: [doc],
      activeDocId: doc.id,
      analysis: {
        [doc.id]: {
          result: { source_version: 1 } as AnalysisResultV2,
          forSourceVersion: 1,
          status: 'ok' as const,
          abort: null,
        },
      },
    };
    const changed = ideReducer(state, {
      type: 'document/language',
      id: doc.id,
      language: 'python',
    });
    expect(changed.documents[0]).toMatchObject({
      source: doc.source,
      sourceVersion: doc.sourceVersion,
      language: 'python',
    });
    expect(changed.analysis[doc.id].status).toBe('stale');
  });

  it('closes maximised panels cleanly, restores them at remembered size, and toggles sidebar state', () => {
    let state = { ...initialIDEState, ui: { ...initialIDEState.ui, panelHeight: 280 } };
    state = ideReducer(state, { type: 'panel/maximise' });
    expect(state.ui).toMatchObject({ panelOpen: true, panelMaximised: true, panelHeight: 280 });
    state = ideReducer(state, { type: 'panel/close' });
    expect(state.ui).toMatchObject({ panelOpen: false, panelMaximised: false, panelHeight: 280 });
    state = ideReducer(state, { type: 'panel/toggle' });
    expect(state.ui).toMatchObject({ panelOpen: true, panelMaximised: false, panelHeight: 280 });
    state = ideReducer(state, { type: 'sidebar/toggle' });
    expect(state.ui.sidebarOpen).toBe(false);
    state = ideReducer(state, { type: 'sidebar/toggle' });
    expect(state.ui.sidebarOpen).toBe(true);
  });

  it('reorders tabs without changing active document or document content', () => {
    const second = { ...doc, id: 'b', name: 'other.cpp', source: 'int y;' };
    const state = { ...initialIDEState, documents: [doc, second], activeDocId: 'a' };
    const moved = ideReducer(state, { type: 'document/move', id: 'b', toIndex: 0 });
    expect(moved.documents.map((item) => item.id)).toEqual(['b', 'a']);
    expect(moved.activeDocId).toBe('a');
    expect(moved.documents[1].source).toBe(doc.source);
  });
});
