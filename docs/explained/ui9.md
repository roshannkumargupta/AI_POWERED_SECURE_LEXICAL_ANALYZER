# Phase UI-9 Deep Explanation: Editor Architecture, Diagnostics, and End-to-End Verification

## 1. Controlled vs. Uncontrolled Editors in Monaco and React

In standard React input programming, the **controlled component** pattern binds input value to React state:
$$\text{state} \xrightarrow{\text{render}} \text{DOM.value} \xrightarrow{\text{onChange}} \text{setState} \xrightarrow{\text{re-render}} \text{DOM.value}$$

While effective for standard HTML `<input>` elements, applying a controlled pattern to a high-performance code editor like **Monaco Editor** is an anti-pattern that leads to severe editor instability:

1. **State Lag and Cursor Reset**: Monaco maintains its own complex, multi-threaded text model (`ITextModel`) backed by a piece tree data structure. Calling `editor.setValue(newValue)` on every React render flushes Monaco's undo stack, invalidates active viewports, and resets the caret back to `(line 1, column 1)`.
2. **IME and Composition Breakage**: During CJK or dead-key input composition, rewriting the editor buffer from external state interrupts the native Input Method Editor (IME) composition session.
3. **The Uncontrolled Model Solution**: In UI-9, Monaco is strictly **uncontrolled**. The `ITextModel` instance is created once per file and attached to the editor via `editor.setModel(model)`. Changes typed by the user update the Monaco model directly. React state is updated out-of-band via debounced listeners (`onDidChangeModelContent`), and React **never** pushes value updates back into Monaco during active editing. Programmatic edits occur solely through `editor.executeEdits(source, edits)` wrapped in undo stops (`pushUndoStop()`), preserving native undo/redo integrity.

---

## 2. Cursor Change Reasons in Monaco and Cursor Storm Prevention

Monaco's `onDidChangeCursorPosition` and `onDidChangeCursorSelection` events expose a critical property: `CursorChangeReason`:
- **`NotSet` (0)**: Internal or unclassified caret move.
- **`ContentFlush` (1)**: The underlying model content was completely replaced (e.g., via `setValue`), violently resetting the cursor.
- **`RecoverFromMarkers` (2)**: Markers, diagnostics, or decorations were recomputed and shifted the caret.
- **`Explicit` (3)**: A programmatic or explicit user navigation action moved the cursor (e.g., clicking a token row or calling `setPosition`).
- **`Paste` (4)**, **`Undo` (5)**, **`Redo` (6)**: Native user editing commands.

### How Cursor Storms Occurred (Defect D1 & D3 Root Cause):
1. **The MouseDown Interceptor Trap**: In `EditorPane.tsx`, an `onMouseDown` handler intercepted clicks, calculated the token under the pointer, and dispatched `SELECT_TOKEN`. An active React effect then immediately called `editor.setSelection(tokenRange)`. The caret was prevented from ever resting inside an identifier: clicking on line 2 expanded the selection to the whole token, and any keystroke wiped out the entire identifier.
2. **The Result Arrival Jump**: When an analysis result arrived from the backend, the workspace reducer selected finding 0 by default. A React `useEffect` listened to `selectedFindingId` and immediately invoked `editor.revealRangeInCenter()` and `editor.setPosition()` back to line 1 of finding 0, snatching caret focus mid-typing.

### The UI-9 Solution:
Programmatic navigation is restricted strictly to **explicit user intent** (clicking a finding row, clicking a problem row, or pressing F8/Shift+F8) routed through a dedicated navigation target pipeline (`navTarget`). Token table row selection updates the table highlight only, without forcing editor selections. When analysis results arrive, the editor's cursor, selection, and scroll position remain completely untouched.

---

## 3. Manual vs. Automatic Analysis and Stale Results

In previous versions, a 600 ms debounce effect triggered `/api/analyze` on every keystroke. This caused severe architectural issues:
1. **Race Conditions**: Rapid keystrokes generated parallel network requests. If request $N$ took 400 ms and request $N+1$ took 150 ms, response $N$ could arrive second and overwrite newer data with stale results.
2. **Shifted Spans**: A finding reported at lines 5–7 became invalid as soon as the developer added lines above it. Applying an automated fix generated for line 5 to an edited document corrupted the code.

### The 5-State Document Lifecycle:
UI-9 transitions each document through a deterministic state machine:
$$\text{not analysed} \xrightarrow{\text{Analyze / Ctrl+Enter}} \text{analysing} \xrightarrow{\text{response}} \text{analysed} \xrightarrow{\text{edit buffer}} \text{stale}$$

```
                [Open / New File]
                       │
                       ▼
               ┌───────────────┐
               │ not analysed  │
               └───────┬───────┘
                       │ User clicks Analyze / Ctrl+Enter
                       ▼
               ┌───────────────┐
         ┌────►│   analysing   │◄────┐
         │     └───────┬───────┘     │ Re-analyze
         │             │ Result      │
         │             ▼             │
         │     ┌───────────────┐     │
         │     │   analysed    │     │
         │     └───────┬───────┘     │
         │             │ Buffer edited
         │             ▼             │
         │     ┌───────────────┐     │
         └─────┤     stale     ├─────┘
               └───────────────┘
```

- **Stale State Protection**: When in the `stale` state ("Edited since last analysis - press Analyze"), existing findings and token highlights are dimmed and tagged "Out of date". Critically, **`[Apply fix]` is disabled** with the tooltip *"Analyse again first"*, guaranteeing that remediation edits are never applied against shifted line offsets.
- **Request Cancellation**: Clicking Analyze while a previous request is in flight cancels the stale promise and increments the document's `resultVersion`, discarding any outdated responses.

---

## 4. Why Fixes are Template-Based and Verified (Not LLM/ML Generated)

A foundational architectural principle of SecureLex IDE is the separation of concerns between **Machine Learning** and **Remediation**:
- **ML Role**: Machine learning (logistic regression, random forest, BiLSTM) operates exclusively on 45-dimensional feature vectors to score token anomaly probabilities and adjust rule confidence scores. ML **never** writes or modifies code.
- **Fix Generator Role**: Remediation is driven by deterministic, rule-based fix templates (e.g. converting `os.system(cmd)` to `subprocess.run(shlex.split(cmd), check=True)`).
- **AST/Syntax Verifier**: Before any fix is presented to the user as "safe", it passes through the remediation verifier:
  1. The edit is applied in memory.
  2. The transformed code is parsed by tree-sitter or the language compiler/AST parser.
  3. The analyzer is re-run on the transformed code to verify that the target vulnerability is eliminated without introducing new security flaws or syntax errors.
- **Review Fixes**: Complex fixes (such as migrating password hashing or replacing dynamic SQL queries) cannot be guaranteed 100% mechanically safe without application context. These are marked as `confidence: "review"`. The diff *is* the review, allowing the developer to inspect and apply the remediation with full confidence.

---

## 5. End-to-End Testing & Test Harness Architecture

To guarantee defect resolution without simulated checks, UI-9 introduces:
1. **Isolated Test Harness (`window.__slTest`)**:
   - Exposes comprehensive diagnostic hooks: `getValue()`, `getPosition()`, `selectedText()`, `isReadOnly()`, `cursorLog`, `requestLog`, and `state()`.
   - **Dead-Code Elimination Proof**: Gated behind `import.meta.env.DEV` and `VITE_E2E=1`. Production builds statically eliminate the harness, verified by automated unit tests that inspect production bundle chunks in `dist/`.
2. **Browser Automation via CDP**:
   - Automated test runners (`cdp_matrix_runner.mjs`, `qa_full.mjs`) connect to Chromium via port 9222 using native Node.js WebSockets.
   - Tests viewport reflows across 5 standardized resolutions (1280x720, 1366x768, 1536x864, 1536x1022, 1920x1080).
   - Validates WCAG AA contrast (zero low-contrast elements), 0 cursor jump anomalies, 0 unexpected network requests, and 100% pass across all 13 samples in Python, Java, JavaScript, and C++.

---

## 6. Viva Examination: Questions & Answers

### Q1: Why did clicking on a code sample in the editor previously prevent the user from typing or moving the cursor?
**Answer**:
The defect stemmed from an aggressive selection synchronization loop in `EditorPane.tsx`. An `onMouseDown` handler intercepted editor clicks, resolved the underlying token from lexical data, and dispatched `SELECT_TOKEN` to the React workspace reducer. A paired `useEffect` responded to this token selection by immediately executing `editor.setSelection(...)` over the entire range of the token. Consequently, the user's caret was never allowed to rest at a single character position inside an identifier; any keystroke either replaced the entire token or was swallowed because focus was repeatedly yanked into selection mode. In UI-9, editor mouse events are handled natively by Monaco, token table row highlights are synchronized one-way without hijacking editor selection, and programmatic selections only occur during explicit user navigation actions.

### Q2: Why is the Monaco Editor configured as an uncontrolled component rather than a controlled React component?
**Answer**:
A controlled component in React synchronizes state unidirectionally on every change via `value={state}` and `onChange={setState}`. In Monaco Editor, this approach is destructive because calling `editor.setValue()` destroys Monaco's internal piece-tree markers, wipes the native undo/redo history, and defaults the cursor back to line 1, column 1. An uncontrolled model maintains a single persistent `ITextModel` instance in Monaco. Edits made by the user mutate the model directly with zero React overhead. React reads the model asynchronously via debounced change notifications (`onDidChangeModelContent`), while external updates (such as loading a file or applying a fix) are executed as discrete, undoable edits via `editor.executeEdits()` with explicit undo stops.

### Q3: What is the significance of the 5-state document lifecycle and why is "Apply fix" disabled in the stale state?
**Answer**:
The 5-state model (`not analysed`, `analysing`, `analysed`, `stale`, `error`) decouples text editing from analysis and enforces synchronization safety. When a document is modified after an analysis run, its buffer state enters `stale`. In this state, existing findings are marked "Out of date" and the `[Apply fix]` button is disabled. This is critical because automated fixes rely on exact line and column ranges computed during the last analysis. If a developer inserts or deletes lines above a vulnerable finding, applying a fix with outdated coordinates would overwrite incorrect lines of code. Requiring a fresh analysis before applying fixes guarantees coordinate validity and prevents code corruption.

### Q4: Why does SecureLex IDE use template-based fix generators with an AST verifier instead of generating fixes with an LLM?
**Answer**:
Machine learning models (especially generative LLMs) are inherently non-deterministic, prone to hallucination, and computationally heavy. In a secure static analysis IDE, remediation must be deterministic, idempotent, and provably sound. SecureLex uses rule-based templates that encode proven security refactorings (such as replacing `yaml.load` with `yaml.safe_load`). Crucially, every proposed fix is executed in memory and passed through the AST verifier and re-analyzer. The verifier ensures the patched code parses without syntax errors and that the target vulnerability is eliminated without introducing new weaknesses. ML is strictly utilized for scoring token security confidence, never for synthesizing code.

### Q5: How does the system guarantee that the test harness (`window.__slTest`) cannot be abused in production environments?
**Answer**:
The test harness is conditionally mounted using Vite's compile-time environment flag: `if (import.meta.env.DEV || import.meta.env.VITE_E2E)`. During production compilation (`npm run build`), Vite and Rollup statically evaluate `import.meta.env.DEV` to `false`. Through dead-code elimination and tree shaking, the entire `window.__slTest` harness and its associated test utilities are completely stripped from the production JavaScript bundle. This guarantee is enforced by an automated guard test (`src/test/ui9-guards.test.ts`) that reads the compiled `dist/` assets and asserts that neither `__slTest` nor its debugging symbols exist in the shipped bundle.
