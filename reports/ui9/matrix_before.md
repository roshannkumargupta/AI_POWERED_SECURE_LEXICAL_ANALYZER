# UI-9 Baseline Feature Matrix (Before Fixes)

Recorded during initial audit of SecureLex IDE prior to applying UI-9 fixes.

| Area | Feature / Check | Baseline Status | Observation & Evidence |
|---|---|---|---|
| **D-A** | Sample editability | **FAIL** | Sample selection storms expand cursor to entire token on click; keystrokes replace token or fail to position. Evidence: `docs/ui9_root_causes.md#1`. |
| **D-A** | Manual analysis only | **FAIL** | Keystrokes and sample loading immediately trigger 600ms debounce call to `/api/analyze`. Cursor jumps on response arrival. Evidence: `docs/ui9_root_causes.md#3`. |
| **D-A** | Cursor stability | **FAIL** | Automatic cursor jumps occur on result arrival due to `store.ts` setting `selectedFindingId` to index 0 and `EditorPane.tsx` calling `setPosition`. |
| **D-B** | Review fix Apply button | **FAIL** | Findings with `confidence: review` (e.g. `py-b01`, `py-b03`, `py-b04`) display diff but [Apply fix] button is hidden due to `confidence === 'safe'` gate. Evidence: `docs/ui9_root_causes.md#2`. |
| **D-B** | Non-edit advice fallback | **FAIL** | Findings without automated edits (e.g. pickle deserialization `py-b05`, hardcoded secrets `py-b08`) show empty or dead fix area without plain-text guidance or "Copy advice" button. |
| **D-B** | Fix all idempotency | **FAIL** | Fix all does not distinguish review fixes from safe verified fixes with a separate "Review fixes" review-panel flow. |
| **D-C** | Token table sync | **FAIL** | Bi-directional synchronization between editor clicks and table row updates can cause re-render loops or unexpected editor re-selections. |
| **D-C** | Dotted name range selection | **PARTIAL** | Dotted names occasionally select only sub-token instead of entire unified token range. |
| **D-D** | Lexical error handling | **PASS** | Unterminated strings and invalid chars generate lexical findings; engine reports error while continuing file scan. |
| **D-E** | File loading & limits | **PARTIAL** | BOM characters not explicitly stripped; files $>512$ KB lack clean frontend size-guard refusal toast. |
| **D-E** | Monaco model disposal | **FAIL** | Closing tabs in workspace does not dispose underlying Monaco text models, causing memory growth over time. |
| **D-F** | ML status truthfulness | **PASS** | Status bar correctly reflects `/api/health` and ML engine status per language. |
| **D-G** | Shell, themes & shortcuts | **PASS** | Dark and Light themes switch cleanly via CSS tokens; command palette and flyouts functional. |
| **D-H** | Layout diagnostics | **PASS** | Fluid typography and viewport metrics conform across the 5 responsive breakpoints (1280x720, 1366x768, 1536x864, 1536x1022, 1920x1080). |
| **D-I** | Engine tests | **PASS** | All engine pytest suites and sample verification suites pass (136 shipped samples verified). |

### Summary
- **Total Matrix Checks**: 15
- **PASS**: 5
- **PARTIAL**: 2
- **FAIL**: 8
