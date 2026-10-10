# UI-9 Root Cause Analysis Report

## Executive Summary
This document investigates and diagnoses the root causes of the defects reported in Phase UI-9:
- **D1**: Code from a sample cannot be edited; cursor cannot be moved and nothing can be typed.
- **D2**: Fixes are not suggested for all samples, and when a fix is shown its Apply button cannot be clicked.
- **D3**: Analysis runs automatically; cursor jumps by itself.
- **D4**: Flaws across token selection sync loops, file loading/saving bounds, and model lifecycle.

---

## 1. Defect D1: Sample Code Cannot Be Edited / Cursor Jumps / Cannot Type

### Proven Root Causes
1. **Unwanted Selection Storm on Token Click (`web/src/components/EditorPane.tsx:208-223` & `271-277`)**:
   - In `EditorPane.tsx`, `onMouseDown` intercepted clicks on the editor and called `dispatch({ type: 'SELECT_TOKEN', index })`.
   - In `EditorPane.tsx` line 271, a React `useEffect` listened to `selectedTokenIndex`:
     ```typescript
     useEffect(() => {
       if (editorRef.current && selectedTokenIndex !== null && tokens[selectedTokenIndex]) {
         const tok = tokens[selectedTokenIndex];
         editorRef.current.setSelection(new monaco.Range(tok.line, tok.col, tok.end_line, tok.end_col));
       }
     }, [selectedTokenIndex, tokens]);
     ```
   - When a user clicked anywhere in the sample to place the cursor, `onMouseDown` triggered token selection, which immediately expanded the cursor into a full-token selection range via `editor.setSelection()`.
   - Any attempt to type either replaced the entire token or was confused by selection bounds.

2. **Automatic Jump to Finding 0 on Analysis Arrival (`web/src/state/store.ts:126` & `web/src/components/EditorPane.tsx:280-297`)**:
   - In `store.ts` line 126, when `SET_ANALYSIS` arrived, the reducer automatically defaulted `selectedFindingId`:
     ```typescript
     selectedFindingId: activeFindings[0]?.id ?? null,
     ```
   - In `EditorPane.tsx` line 280, a React `useEffect` listened to `[selectedFindingId, findings]`:
     ```typescript
     useEffect(() => {
       if (!editorRef.current || !selectedFindingId) return;
       const f = findings.find(x => x.id === selectedFindingId);
       if (!f) return;
       editorRef.current.revealRangeInCenter(range);
       editorRef.current.setPosition({ lineNumber: range.startLineNumber, column: range.startColumn });
     }, [selectedFindingId, findings]);
     ```
   - Since analysis was triggered continuously (see D3), this effect continuously called `editor.setPosition()` back to line 1 or the start of the first finding, stealing cursor focus from wherever the user was typing.

3. **Status Check of Likely Suspects**:
   - `readOnly` / `domReadOnly`: **NOT REAL** (Options set `readOnly: false`, `domReadOnly: false`).
   - Controlled prop `value` replacing model: **PARTIALLY REAL** (Vite Monaco component can call `setValue` if `value` is bound directly without tracking model versions).
   - React key remounting Monaco: **NOT REAL** (Monaco container remained mounted).
   - Pointer-events blocking overlay: **PARTIALLY REAL** (Empty editor hint had pointer-events before UI-8, but was fixed; however, token clicks triggered synthetic selections).

---

## 2. Defect D2: Fixes Missing or Apply Button Cannot Be Clicked

### Proven Root Causes
1. **Apply Button Restricted to `confidence === 'safe'` Only (`web/src/components/ExplanationPanel.tsx:35` & `FindingPanel.tsx:229`)**:
   - In `ExplanationPanel.tsx` line 35:
     ```tsx
     {fix.confidence === 'safe' && fix.verification?.verified && (
       <button className="sl-btn sl-btn--primary" onClick={handleApplyFix}>
         Apply Fix
       </button>
     )}
     ```
   - In `FindingPanel.tsx` line 229:
     ```tsx
     {isSafe && isVerified && (
       <button className="sl-btn sl-btn--primary sl-btn--sm" onClick={...}>
         Apply Verified Fix
       </button>
     )}
     ```
   - In the APSLA Phase 10 engine, many verified, effective rule fixes (e.g., Python command injection `APS-PY-INJ-002`, SQL injection `APS-PY-INJ-004`, random generators `APS-PY-CRY-002`, JavaScript XSS/Injection, Java ProcessBuilder, C++ snprintf) have `confidence: "review"` because human review of the diff is expected.
   - Because `confidence === 'safe'` was strictly required to display the Apply button, **all review-level fixes had their Apply button completely hidden or unclickable**, even though a valid, syntax-verified diff was displayed!

2. **No Fallback Advice Block for Non-Edit Rules (`web/src/components/ExplanationPanel.tsx`)**:
   - For findings where no automatic code edit is possible (e.g. pickle deserialization `APS-PY-DES-001`, hardcoded secrets `APS-PY-SEC-001`, C buffer redesign), `fix` was `undefined`.
   - The UI displayed an empty fix area or omitted the fix column entirely without explaining *why* no automatic edit exists or offering actionable advice.
   - The rule's advice text and a "Copy advice" button were missing.

---

## 3. Defect D3: Analysis Runs Automatically & Cursor Jumps

### Proven Root Causes
1. **600ms Debounce Auto-Trigger on Keystrokes (`web/src/App.tsx:158-172`)**:
   - In `App.tsx`:
     ```typescript
     useEffect(() => {
       const timer = setTimeout(() => {
         runAnalysis();
       }, 600);
       return () => clearTimeout(timer);
     }, [state.source, state.activeFileId]);
     ```
   - Every time the user typed a character, opened a sample, or switched files, `runAnalysis()` was fired over the network to `/api/analyze`.
   - The user specification states: **Analysis must run ONLY when the user clicks Analyze (or presses Ctrl+Enter).** Opening a file, loading a sample, switching tabs, changing language, changing theme, or typing must NEVER automatically call `/api/analyze`.

2. **Stale Model Race Conditions & Selection Reset**:
   - When the debounced response arrived ~100-300ms later, it updated `state.findings`, triggering the `selectedFindingId` effect in `EditorPane.tsx` which called `setPosition(...)`, making the cursor jump mid-word while typing.

---

## 4. Defect D4: Additional System Flaws

1. **Selection Sync Loop Between Table and Editor**:
   - Clicking a table row selected the editor; moving the cursor in the editor updated the table row; without decoupling editor selection from table highlight, an infinite re-render / selection loop could occur.
2. **Missing Per-File State Machine**:
   - The UI lacked explicit states: `not analysed`, `analysing`, `analysed`, `stale`, and `error`.
   - When text was modified after an analysis, the findings stayed on old line ranges, leading to invalid edits if "Apply fix" was clicked without re-analysis.
3. **File I/O Boundaries**:
   - Missing UTF-8 BOM stripping on file open.
   - Lack of $>512$ KB file refusal and binary NUL byte refusal.
   - Monaco model leak when closing tabs (models were not disposed).
