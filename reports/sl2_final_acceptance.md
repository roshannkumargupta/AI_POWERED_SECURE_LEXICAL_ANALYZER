# SL2-10 Final Acceptance Report

Date: 2026-10-12. This is an evidence report for the current checkout; partial and blocked items are not passes.

## Part 17 criteria

| # | Criterion | Status | Evidence and remaining work |
|---:|---|---|---|
| 1 | VS Code-style identity/layout | Partial | `web/` has the IDE layout and SL2-8b workspace. Browser visual diagnostics and requested SL2-10 screenshots were not run because the CDP endpoint is unavailable. |
| 2 | Token table uses lexer output | Partial | Frontend tests include `tokens-panel.test.tsx`, `tokens-derive.test.ts`, `api-contract.test.ts`; `npm run test` passed 153 tests. Live browser/API golden path is blocked. |
| 3 | Correct four-language configuration | Partial | Language modules and examples exist. C++ compiler `g++` exists; `javac` is absent; no fresh four-language browser run was possible. |
| 4 | Token types, positions, validity and counts | Partial | `tests/unit/test_sl2_2_tokens.py`, `tests/unit/test_sl2_v2.py`, `tests/fixtures/cpp/lexical/default_example.tokens.json`, and UI token tests exist. Full Python suite and browser integration did not complete. |
| 5 | Syntax/security independent of lexical validity | Partial | SL2-2/3 tests include this separation; full suite is not confirmed in this phase. |
| 6 | AST from real parser | Partial | Tree-sitter grammar packages were previously probed as loadable in `docs/sl2_environment.md`; `tests/unit/test_sl2_3_parsing.py` exists. No current live AST browser view was exercised. |
| 7 | Security findings from configured rules/analyzers | Partial | `tests/unit/test_sl2_4_security.py`, rule catalogue and adapter fixtures exist. Optional analyzers are unavailable and external tool execution is fail-closed on this host. |
| 8 | Real provider-backed generation and honest failure | Partial | Provider and no-provider tests exist. groq executable exists but its service is unreachable; no live model run was performed. |
| 9 | Reviewable, validated, reversible fixes | Partial | `tests/unit/test_sl2_6_patch_flow.py` exists; old endpoints remain in use by `tests/e2e/test_java_end_to_end.py`, `tests/e2e/test_javascript_end_to_end.py`, and `tests/unit/test_api_contract.py`, so aliases are retained as debt. Browser apply/undo not exercised. |
| 10 | Independent verifier with deterministic checks | Partial | `src/apsla/fixes/independent_verifier.py` and patch flow tests exist; full suite and live four-language path are not confirmed. |
| 11 | Remaining/new/unverified issues visible | Partial | API/UI verification report has four sections; `SL28bWorkspace.tsx` displays report fields. UI interaction remains unverified in a browser. |
| 12 | Real controlled Safety Lab | Partial | `tests/unit/test_sl2_7_safety_lab.py` and `docs/safety_lab.md` exist; no live model, and the browser run/export path was not exercised. |
| 13 | Every visible control has tested behavior/unavailable state | Partial | Vitest passed 153 tests across 24 files; no exhaustive click audit or narrow-width browser matrix was available. |
| 14 | No misleading results, fake responses, fixed counters or unsupported guarantees | Partial | Replaced overstated README and tour claims; focused `rg` sweep found no executable `alert()` UI flow or percent/fake-success claim in current README/user guide/demo. Security examples/tests intentionally contain inert `alert(...)` strings for XSS tests; CSS contains `100%` dimensions. Historic phase documents and legacy routes still contain claims/compatibility references and need a separate review. |
| 15 | Backend protects against execution, prompt injection, unsafe tools/patches | Partial | `tests/security/test_sl2_9_boundary.py` and prior SL2-9 evidence report 15 passing security tests; fresh run in this phase is pending/stalled. Windows process memory isolation, chunked-body pre-parse caps and browser session isolation remain documented gaps. |
| 16 | Understandable and reproducible README/tests | Partial | README, `.env.example`, user guide and demo script updated. Ruff passed; frontend test/build passed. `mypy` fails with 36 errors, full pytest did not produce a summary in the observed run, fresh-clone run was not feasible, and `check_all.py` could not be executed end-to-end. |

## Commands and observed results

- `.\.venv\Scripts\ruff.exe check` — `All checks passed!` after excluding `examples/` (intentionally invalid/insecure inputs) and sorting `run_tests.py` imports.
- `.\.venv\Scripts\python.exe scripts\check_links.py` — **all links verified across 82 documentation files**.
- `.\.venv\Scripts\mypy.exe` — failed with **36 errors in 8 files**, chiefly SL2 model/provider/tool-runner/parser/server typing issues. No type-check pass is claimed.
- `npm.cmd run test` — passed three consecutive runs: each **24 test files, 153 tests** (Vitest 2.1.9, Node v24.11.1); no frontend flake observed.
- `.\.venv\Scripts\python.exe -m pytest -m security -q` — passed three consecutive runs: each **15 passed**, with the same Starlette/httpx deprecation warning; no security-suite flake observed.
- `npm.cmd run build` — passed: Vite built in 1m 5s; bundle warning: `index` is about 3.67 MB before gzip.
- `.\.venv\Scripts\python.exe -m pytest -q` — started, no summary/output during the observed wait; previous phase also recorded a 120-second stall. This is incomplete, not a pass.
- `.\.venv\Scripts\python.exe scripts\golden.py --check` — started with the Python tool checks; did not return a result during the observed wait. No golden pass is claimed.
- `npm.cmd run e2e` — failed before browser setup: `connect EACCES 127.0.0.1:9222` in `scripts/cdp_matrix_runner.mjs`.
- Browser golden paths and requested screenshots — blocked by the unavailable/denied local browser automation endpoint. No screenshot has been fabricated.
- Full test suite three-run flake check — not completed because full pytest and browser E2E did not complete. Frontend and security-marked suites were each run three times.
- Fresh clone/install/start/check/golden path — not run. Current changes are uncommitted, so a clone of the Git `HEAD` would not contain the working tree being evaluated; network access and local clone write permission are also unverified.

## Tool availability observed/reported

`g++` and `gcc` are present. `clang`, `clang++`, `clang-tidy`, `cppcheck`, `javac`, `semgrep`, `bandit`, `pyflakes` and global `mypy`/`eslint` are absent from PATH; local venv mypy and local frontend ESLint are installed. Java runtime is present but `javac` is not. groq CLI is present but no service is reachable, so installed models could not be enumerated and AI paths were not live-tested. Playwright packages/browser cache were reported absent in `docs/sl2_environment.md`; the CDP browser endpoint was denied.

These absences disable or reduce compiler-backed checks for Java/Clang, optional security/semantic analyzers, live AI, and real-browser acceptance. Deterministic lexical analysis and non-provider features do not require a paid API.

## Honesty sweep

Commands run:

```powershell
rg -n -i '100%|100 percent|always secure|fully secure|completely secure|guaranteed secure|simulated response|mock response|alert\(' README.md docs/user_guide.md docs/demo_script.md web/src src/apsla --glob '!*.map'
rg -n '(@deprecated|legacy_alias|def fix\(|def fix_all\(|/api/fix)' src/apsla/server/app.py web/src
rg -n -i '100%|22 tokens|alert\(' docs/ui_reference_v2/prototype.html
```

The first sweep's remaining matches were CSS `100%` sizing and inert XSS/security sample strings and tests containing `alert(...)`; no `alert()` invocation flow was found in the updated docs or shipped `web/src` UI. A broader docs scan found deliberate fake counters, `alert()` handlers and hard-coded outcomes in `docs/ui_reference_v2/prototype.html`; that file is retained as the audited, non-shipped prototype reference and must not be copied into the app. `docs/STATE.md` and prior phase notes contain historical claims that are dated and superseded by this acceptance report; they were not rewritten as current evidence. The README's former “100% locally/offline,” “100% reproducible,” and zero-outbound guarantees were removed. Deprecated `/api/fix` and `/api/fix-all` aliases remain because API contract and end-to-end clients still use them. They are known debt until clients migrate and compatibility tests permit removal.

## Files changed in SL2-10

- `README.md`, `docs/user_guide.md`, `docs/demo_script.md` — setup, operation, consent, analyzer and limitation guidance.
- `docs/explained/sl2_7.md` — corrected an absolute link and replaced an unverified model-absence claim with the observed unreachable-service state.
- `scripts/check_all.py` — removed destructive `git checkout -- reports/`, switched fixed command arrays to `shell=False`, added a subprocess timeout and security/browser gates.
- `ruff.toml` — excludes deliberately malformed product input examples from source linting.
- `run_tests.py` — sorted imports to satisfy Ruff.
- `pyproject.toml` — no net SL2-10 change retained.
- `docs/STATE.md`, `reports/sl2_final_acceptance.md`, `reports/sl2_10_evidence.md`, `docs/explained/sl2_10.md` — phase and evidence records.

Earlier phase file-by-file changes remain in the shared working tree and phase evidence (`reports/sl2_1_evidence.md` through `reports/sl2_9_evidence.md`). They are not attributed to SL2-10. The current checkout has 107 modified/untracked paths from prior SL2 work; a clean per-phase Git diff cannot be reconstructed because those changes are not committed.

## Remaining limitations

Mypy and full pytest acceptance are not green; browser E2E, both-theme screenshots, four-language golden paths, three-run flake checks, live provider tests, fresh-clone reproduction, and the requested `sl2-10` tag are not established. The current branch is `sl2-0`, with extensive uncommitted files. No claim is made that SL2-10 is complete.
