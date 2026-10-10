# UI-5 verification evidence (2026-10-03)

## API-shaped analyzer responses

`docs/api_samples/analyze_python.json`, `analyze_python_lexical.json`, `analyze_java.json`, `analyze_javascript.json`, and `analyze_c.json` were generated from current `Analyzer.analyze()` results and serialized with Pydantic. A permitted health probe reached the already-running API, but its response schema predates UI-5 (`parser` and `Finding.kind` were absent), so it was not used for these payloads. The API round-trip test exercised the current `/api/analyze` route in-process and passed. The browser-control runtime and the required reference assets were unavailable in this turn.

| Sample | Findings | Taint path steps | `ml_mode` | Parser |
|---|---:|---:|---|---|
| Security demo (Python) | 6 | 4 on `APS-PY-INJ-002` | on | python-ast |
| Java demo | 7 | 0 | on | lexer-only |
| JavaScript demo | 6 | 0 | on | lexer-only |
| C demo via C++ plugin | 3 | 0 | on | lexer-only |
| Malformed Python demo | 12: one lexical, one syntax, ten ML-only | 0 | on | python-ast |

The malformed file's earlier request-to-command flow is absent because `ast.parse` rejects the file. Python's lexer returns the unclosed line as a `STRING`, so the additive lexical diagnostic recognizes that unterminated string token without changing lexer recovery. The candidate closing-quote fix goes through the existing verifier; the verifier marks it manual and removes the edit because the corrected source exposes a high-severity command-injection finding.

## Checks run

- `npm run test`: passed, 105 tests in 13 files, including four real analyzer response samples, adapter behavior and contrast thresholds.
- `npm run build`: passed. Vite reported its existing oversized Monaco bundle advisory.
- `scripts/build_samples.py`: passed and generated 146 manifest-backed samples (43 Python, 35 Java, 34 JavaScript, 34 C/C++).
- Full `.venv` `pytest -q --basetemp=reports/.pytest-ui5-final-full`: passed after the final cross-language lexical-fix change. This includes UI-5 backend diagnostics, API round trip, fixtures, and sample catalogue.
- The ten focused UI-5 backend tests passed, including unterminated-string diagnostics and verifier results for all four language plugins.
- `ruff check .`: passed.
- Reference style comparison, screenshots at 1536x1022 and 1280x720, and the no-horizontal-scroll browser check remain unverified. The browser skill's CUA tool was not present; `playwright` is not installed; and `docs/ui_reference/securelex_full_feature_ui_mockup.html` plus `target.png` are missing.

The expected style values remain encoded in `web/src/theme/tokens.css` and the shell dimensions in `web/src/ui5.css`. The 2 px reference tolerance cannot be claimed without rendering the supplied mockup and the app at the requested viewports.
