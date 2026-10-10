# UI-3 evidence: token security inspector

## Implementation

- Audited the real Python and Java analyze samples in `docs/api_samples/`; field-level results and missing metadata are recorded in `docs/token_security_data.md`.
- Added a pure memoized derivation layer in `web/src/tokens/derive.ts`; it uses exact API ranges to connect rules, taint paths, Unicode evidence, severity, detectors, categories, and findings to tokens.
- Added the integrated Tokens tab with security-relevant default filtering, type/security/search controls, category chips, bounded virtual rows, token detail/flow blocks, visible control-character markers, on-demand ML evidence, keyboard row controls, and Token Map modes.
- Monaco selection now synchronizes token selection with a 50 ms debounce and ignores the matching programmatic selection event. Security map uses one delta-decoration collection and clears on Off/model change; category filtering highlights matching token ranges in the editor.
- Added palette commands and Ctrl+Shift+T.

## Verification

- `npm.cmd run test -- --run`: 88 tests passed across 11 files. The focused UI-3 suite passed 9 tests.
- `npm.cmd run build`: passed TypeScript and Vite production build. Vite continues to report the existing large Monaco bundle advisory (about 3.57 MB minified).
- The 5,000-token derive test measured **11.63 ms**, **15.89 ms**, **30.24 ms**, **34.97 ms**, and **39.99 ms** across focused/full Vitest runs (budget: <50 ms; all observed runs passed).
- Direct API sample tests cover Python and Java token shapes and the Flask taint source/propagation/sink order. A representative lexer probe confirmed JavaScript kinds `COMMENT`, `IDENTIFIER`, `KEYWORD`, `NUMBER`, `OPERATOR`, `PUNCTUATION`, `WHITESPACE` and C/C++ kinds `IDENTIFIER`, `KEYWORD`, `NUMBER`, `OPERATOR`, `PREPROCESSOR`, `WHITESPACE`; `PREPROCESSOR` is intentionally Other because the requested type vocabulary has no preprocessor category.
- Browser walkthrough covered Python command injection, Trojan Source and confusable `еxec`; Java SQL injection; JavaScript DOM XSS; and C/C++ buffer overflow. The confusable token detail showed Original `еxec`, Recovered `exec`, Cyrillic U+0435, and mixed-script/confusable flags. See `docs/screenshots/after_ui3/README.md` for the screenshot capture limitation.

## Data limitation

`/api/analyze` supplies token spelling, lexer kind, range, fused label, and score. It does not supply per-token recovered text, script metadata, or probability vectors. Unicode details are shown only where finding evidence supplies them; selected-token ML evidence remains an on-demand `/api/ml/insights` call. No backend schema change was needed.
