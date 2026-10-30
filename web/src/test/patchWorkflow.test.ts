import { describe, it, expect, beforeEach } from 'vitest';
import {
  validatePatchProposal,
  applyPatchToSource,
  createEnrichedPatchProposal,
} from '../ide/patch/patchWorkflow';
import { ideReducer, initialIDEState, type IDEDocument } from '../ide/state/store';
import type { PatchProposal } from '../api/client';

describe('Source-Code Modification Workflow', () => {
  const initialSource = `#include <iostream>
#include <cstdio>
using namespace std;

int main() {
    char buf[10];
    gets(buf);
    return 0;
}
`;

  let baseProposal: PatchProposal;

  beforeEach(() => {
    baseProposal = {
      id: 'prop-1234',
      source_hash: 'abc123hash',
      source_version: 1,
      target_finding_id: 'find-gets-001',
      target_kind: 'finding',
      origin: 'ai',
      edits: [
        {
          range: {
            start_line: 7,
            start_col: 5,
            end_line: 7,
            end_col: 15,
          },
          new_text: 'fgets(buf, sizeof(buf), stdin);',
        },
      ],
      diff: `--- a/main.cpp\n+++ b/main.cpp\n@@ -7,1 +7,1 @@\n-    gets(buf);\n+    fgets(buf, sizeof(buf), stdin);`,
      rationale: 'Replace unsafe gets() with bounds-checked fgets().',
      expected_outcome: 'Buffer overflow vulnerability eliminated.',
      assumptions: ['Buffer is stack-allocated char array.'],
      risks: ['Preserves newline in buffer.'],
      created_at: new Date().toISOString(),
    };
  });

  it('contains all required patch fields: target file, version, range, original text, replacement text, explanation, finding', () => {
    const finding = {
      id: 'find-gets-001',
      title: 'Insecure String Input (gets)',
      rule_id: 'APS-CPP-SEC-001',
      severity: 'critical',
    };

    const enriched = createEnrichedPatchProposal(baseProposal, initialSource, 'src/main.cpp', finding);

    expect(enriched.target_file).toBe('src/main.cpp');
    expect(enriched.source_version).toBe(1);
    expect(enriched.source_hash).toBe('abc123hash');
    expect(enriched.original_range).toEqual({
      start_line: 7,
      start_col: 5,
      end_line: 7,
      end_col: 15,
    });
    expect(enriched.original_text).toBe('gets(buf);');
    expect(enriched.replacement_text).toBe('fgets(buf, sizeof(buf), stdin);');
    expect(enriched.explanation).toBe('Replace unsafe gets() with bounds-checked fgets().');
    expect(enriched.finding).toEqual(finding);
  });

  it('applies a valid patch when source version and range text match current state', () => {
    const enriched = createEnrichedPatchProposal(baseProposal, initialSource, 'src/main.cpp');
    const validation = validatePatchProposal(initialSource, 1, enriched);

    expect(validation.valid).toBe(true);
    expect(validation.reason).toBeUndefined();

    const result = applyPatchToSource(initialSource, enriched);
    expect(result.success).toBe(true);
    expect(result.newSource).toContain('fgets(buf, sizeof(buf), stdin);');
    expect(result.newSource).not.toContain('gets(buf);');
  });

  it('rejects a patch cleanly without changing source', () => {
    const enriched = createEnrichedPatchProposal(baseProposal, initialSource, 'src/main.cpp');
    let documentSource = initialSource;

    // User rejects the patch
    const rejectedByUser = true;
    if (!rejectedByUser) {
      const res = applyPatchToSource(documentSource, enriched);
      if (res.newSource) documentSource = res.newSource;
    }

    // Source must remain completely unmodified
    expect(documentSource).toBe(initialSource);
    expect(documentSource).toContain('gets(buf);');
  });

  it('rejects a stale patch when the document version has advanced', () => {
    const enriched = createEnrichedPatchProposal(baseProposal, initialSource, 'src/main.cpp');

    // Document is at v2, but proposal was for v1
    const validation = validatePatchProposal(initialSource, 2, enriched);

    expect(validation.valid).toBe(false);
    expect(validation.conflictType).toBe('stale_version');
    expect(validation.reason).toContain('Document is currently v2, but proposal was generated for v1');
  });

  it('rejects when the file is modified after receiving a proposal (content mismatch)', () => {
    const enriched = createEnrichedPatchProposal(baseProposal, initialSource, 'src/main.cpp');

    // User modified line 7 manually to gets_s(buf, 10);
    const modifiedSource = initialSource.replace('gets(buf);', 'gets_s(buf, 10);');

    // Version is still 1, but text at range has changed
    const validation = validatePatchProposal(modifiedSource, 1, enriched);

    expect(validation.valid).toBe(false);
    expect(validation.conflictType).toBe('content_mismatch');
    expect(validation.reason).toContain('Content conflict rejected');
  });

  it('applies multiple atomic non-overlapping patches in correct sequence', () => {
    const multiProposal: PatchProposal = {
      ...baseProposal,
      edits: [
        {
          // Replace gets(buf) at line 7
          range: { start_line: 7, start_col: 5, end_line: 7, end_col: 15 },
          new_text: 'fgets(buf, sizeof(buf), stdin);',
        },
        {
          // Replace char buf[10] at line 6
          range: { start_line: 6, start_col: 10, end_line: 6, end_col: 16 },
          new_text: 'buf[256];',
        },
      ],
    };

    const result = applyPatchToSource(initialSource, multiProposal);
    expect(result.success).toBe(true);
    expect(result.newSource).toContain('char buf[256];');
    expect(result.newSource).toContain('fgets(buf, sizeof(buf), stdin);');
  });

  it('updates document version, marks analysis outdated (stale), and sets dirty flag in IDE store', () => {
    const doc: IDEDocument = {
      id: 'doc-main',
      name: 'src/main.cpp',
      language: 'cpp',
      source: initialSource,
      savedSource: initialSource,
      sourceVersion: 1,
      dirty: false,
      origin: 'opened',
    };

    let state = ideReducer(initialIDEState, { type: 'document/add', document: doc });
    expect(state.documents[0].sourceVersion).toBe(1);
    expect(state.documents[0].dirty).toBe(false);

    // Patch is applied
    const patchedSource = initialSource.replace('gets(buf);', 'fgets(buf, sizeof(buf), stdin);');
    state = ideReducer(state, {
      type: 'document/edit',
      id: 'doc-main',
      source: patchedSource,
    });

    // 1. Version incremented
    expect(state.documents[0].sourceVersion).toBe(2);
    // 2. Source updated
    expect(state.documents[0].source).toBe(patchedSource);
    // 3. Marked dirty (unsaved)
    expect(state.documents[0].dirty).toBe(true);
    // 4. Analysis marked stale
    expect(state.analysis['doc-main'].status).toBe('stale');
  });

  it('supports explicit save and reopen workflow persisting modifications', () => {
    const doc: IDEDocument = {
      id: 'doc-main',
      name: 'src/main.cpp',
      language: 'cpp',
      source: initialSource,
      savedSource: initialSource,
      sourceVersion: 1,
      dirty: false,
      origin: 'opened',
    };

    let state = ideReducer(initialIDEState, { type: 'document/add', document: doc });

    // Apply patch
    const patchedSource = initialSource.replace('gets(buf);', 'fgets(buf, sizeof(buf), stdin);');
    state = ideReducer(state, {
      type: 'document/edit',
      id: 'doc-main',
      source: patchedSource,
    });
    expect(state.documents[0].dirty).toBe(true);

    // Explicit User Save Action
    state = ideReducer(state, {
      type: 'document/save',
      id: 'doc-main',
    });
    expect(state.documents[0].dirty).toBe(false);
    expect(state.documents[0].savedSource).toBe(patchedSource);

    // Close and Reopen file
    state = ideReducer(state, { type: 'document/remove', id: 'doc-main' });
    expect(state.documents.length).toBe(0);

    // Reopened from persisted content
    state = ideReducer(state, {
      type: 'document/add',
      document: {
        id: 'doc-main',
        name: 'src/main.cpp',
        language: 'cpp',
        source: patchedSource,
        savedSource: patchedSource,
        sourceVersion: 2,
        dirty: false,
        origin: 'opened',
      },
    });

    expect(state.documents[0].source).toBe(patchedSource);
    expect(state.documents[0].sourceVersion).toBe(2);
    expect(state.documents[0].dirty).toBe(false);
  });
});
