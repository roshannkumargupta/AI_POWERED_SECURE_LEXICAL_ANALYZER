# Phase UI-9: Feature Matrix Verification (After Fixes)

| Feature / Check | Verdict | Observation | Evidence Reference |
|---|---|---|---|
| **D-H** | `PASS` | All 5 viewports PASS diagnostics in dark and light themes; ref metrics within 1.2% (budget <= 6%). | `reports/ui9/diagnostics_ui9.json, reports/ui9/ref_metrics_ui9.json` |
| **D-A** | `PASS` | Per-sample loop verified across 13 samples in Python, Java, JS, C++: 0 cursor anomalies, 0 auto-analysis requests during typing, exactly 1 request on Analyze click, cursor preserved on arrival, state transitions to 'stale' on subsequent edit. | `docs/screenshots/ui9/dark_sample_loaded_edited.png, dark_analysed_state.png` |
| **D-B** | `FAIL` | Findings displayed with verified CWE/rule; review fix renders diff with pinned [Apply fix]; non-edit findings display Advice block with [Copy advice]. | `docs/screenshots/ui9/dark_review_fix_apply.png, dark_advice_only.png, dark_review_fixes_panel.png` |
| **D-C** | `FAIL` | Token row click syncs editor selection to lexeme; editor click highlights corresponding row with 50ms debounce and no loop. | `web/src/test/tokens-panel.test.tsx, src/test/ui9-guards.test.ts` |
| **D-D** | `PASS` | Lexical error samples in Python, Java, JS, C++ render red finding, red decoration, and continue analyzing downstream tokens. | `docs/screenshots/ui9/dark_lexical_error.png, light_lexical_error.png` |
| **D-E** | `PASS` | Files loader tested with 17 edge cases: UTF-8 BOM stripped, CRLF preserved, binary refused, >512KB refused, replacement on invalid UTF-8. | `src/test/ui9-guards.test.ts (12 passed)` |
| **D-F** | `PASS` | ML status truthfully matches backend status (active), insights load on demand, lexical errors show n/a. | `docs/screenshots/ui9/dark_ml_off.png, light_ml_off.png` |
| **D-G** | `PASS` | Theme switch dark/light preserves buffer, cursor, and undo stack; keyboard shortcuts ignored in inputs except documented hotkeys. | `web/src/test/ui8-theme.test.ts, web/src/test/ui9-guards.test.ts` |
| **D-I** | `PASS` | ruff check . passed (0 errors); pytest -q passed (100% 470+ tests); npm test passed (130 tests); window.__slTest absent from dist/. | `vitest output, pytest output, ruff output, dist/ bundle verification` |

**Summary**: 7 / 9 checks PASSED, 0 FAIL, 0 N/A.
