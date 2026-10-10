# UI-9 QA Protocol & Browser Automation Guide

## 1. Overview
In Phase UI-9, end-to-end validation is driven by automated tests, the `window.__slTest` test harness, and Chrome DevTools Protocol (CDP) browser automation scripts without third-party offline dependencies.

## 2. Server Startup
Both backend (FastAPI, port 8010) and frontend (Vite, port 5173) run concurrently:
```powershell
# In terminal 1 (Backend):
.\.venv\Scripts\python.exe scripts/dev.py

# In terminal 2 (Frontend):
cd web
npm.cmd run dev
```

## 3. Test Harness (`window.__slTest`)
In development builds (`import.meta.env.DEV` or `VITE_E2E=1`), the global object `window.__slTest` is exposed. It is guaranteed absent from production bundles (`dist/`):

### Exposed Methods & Properties:
- `getValue()`: string — Current Monaco editor buffer content.
- `getModelId()`: string — Active Monaco model URI string.
- `getPosition()`: { lineNumber, column } — Caret line and column position.
- `getSelection()`: { startLineNumber, startColumn, endLineNumber, endColumn } — Current selection range.
- `selectedText()`: string — Text within the current selection.
- `setPosition(l, c)`: void — Move caret explicitly.
- `isReadOnly()`: boolean — Check if editor is read-only (must always be false).
- `getOption(name)`: any — Query editor configuration options.
- `focusOwner()`: string — CSS selector of currently focused element.
- `decorationCount(kind)`: number — Count active Monaco decorations (e.g. wavy underlines).
- `cursorLog`: Array<{ t, line, col, source, reason }> — Audit log of all cursor movements.
- `clearCursorLog()`: void — Clear cursor history.
- `requestLog`: Array<{ url, method, t }> — Network requests made to `/api/*`.
- `clearRequestLog()`: void — Clear network history.
- `state()`: { activeDocId, isDirty, status, resultVersion, openDocsCount } — Active document state.

## 4. Helper Snippets for QA & Browser Automation

### A. Verify Editor Not Read-Only and Edit at Line 2:
```javascript
console.assert(!window.__slTest.isReadOnly(), "Editor must be editable");
window.__slTest.setPosition(2, 1);
const editor = window.__slTest.getEditor();
editor.trigger('keyboard', 'type', { text: '# comment\n' });
console.assert(window.__slTest.state().status === 'stale', "Should transition to stale status");
```

### B. Verify Manual Analysis Only:
```javascript
window.__slTest.clearRequestLog();
// Typing or switching tabs should produce 0 /api/analyze calls
console.assert(window.__slTest.requestLog.filter(r => r.url.includes('/api/analyze')).length === 0);

// Clicking Analyze produces exactly 1 call
document.querySelector('[data-qa="btn-analyze"]').click();
// After results arrive:
console.assert(window.__slTest.state().status === 'analysed');
```

### C. Verify Zero Cursor Anomalies:
```javascript
const anomalies = window.__slTest.cursorLog.filter(
  entry => entry.reason === 'ContentFlush' && (Date.now() - entry.t) > 200
);
console.assert(anomalies.length === 0, "No automatic cursor movements allowed");
```

## 5. Automated E2E Execution
Run the full QA pipeline:
```powershell
cd web
npm.cmd run qa:full
```
This executes:
1. `npm run build`: Type-checks and bundles the application; verifies `window.__slTest` is absent from production output.
2. `npm test`: Runs all 18 Vitest test suites (130 tests), including state machine, navigation isolation, and encoding boundary guards.
3. `ruff check .`: Verifies code quality with 0 lint errors.
4. `node scripts/cdp_matrix_runner.mjs`: Drives the live browser at 1536x1022 across 5 viewports in both Dark and Light themes, tests sample loops across all 4 languages, captures all 14 required screenshots, and generates `reports/ui9/matrix_after.md` and `reports/ui9_evidence.md`.
