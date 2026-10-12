# SL2-9 Evidence — Application Hardening

Date: 2026-10-12 (Asia/Calcutta)  
Host: Windows 11 environment; Python 3.12.5; repository virtual environment.

## Changes made

- Added `src/apsla/server/security_limits.py`: a 1 MiB request-size constant, output caps of 100,000 tokens and 2,000 findings per file, a 2,000-node AST maximum, separate process-local rate windows (analysis 20/min, AI 8/min, Safety Lab 5/min), safe filename-label normalization, and terminal/control neutralization.
- Added a FastAPI boundary middleware in `src/apsla/server/app.py`: default configured bind is `127.0.0.1`; an explicitly configured non-loopback bind (`SECURELEX_BIND_HOST`) requires `SECURELEX_ACCESS_TOKEN` checked by `hmac.compare_digest`. It rejects unlisted Host/Origin values, rejects oversized declared Content-Length before request model parsing, sets a random 12-hour HttpOnly/SameSite=Strict cookie, applies CSP/security headers and caps concurrent guarded work at four requests. HTTP and internal errors include structured codes and no exception traceback.
- Session identity for consent, proposal/undo ownership, agent-event queries, and Safety Lab run/export access now comes from the server request cookie, not the caller's body session ID. Expired session-owned transient state is removed. This state is process-local and source is not persisted.
- Removed `compile()` use from Python syntax diagnostics in favor of `ast.parse()`; this does not execute submitted code.
- Added the security-marked tests in `tests/security/test_sl2_9_boundary.py`. Existing tool runner uses fixed allowlisted argument arrays, `shell=False`, temporary directories, scrubbed environment, timeouts and output caps. It currently refuses execution when OS-enforced network isolation is unavailable.
- Added `docs/threat_model.md`, including explicit no-execution allowlist and residual risks. Added frontend clipboard/report sanitization, an ESLint restriction on `dangerouslySetInnerHTML` and `.innerHTML` assignments, plus a hostile-string unit test.

## Commands and actual results

Changed Python files:

```text
\.venv\Scripts\python.exe -m ruff check src/apsla/server/app.py src/apsla/server/security_limits.py src/apsla/diagnostics/python_diag.py tests/security/test_sl2_9_boundary.py
All checks passed!
```

Security suite:

```text
\.venv\Scripts\python.exe -m pytest -m security -q
..............                                                           [100%]
15 passed
```

The run completed in approximately 29 seconds. Pytest emitted a Starlette `TestClient` deprecation warning about httpx; no test failed.

Focused provider/patch/verifier regressions:

```text
\.venv\Scripts\python.exe -m pytest tests/unit/test_sl2_5_provider.py tests/unit/test_sl2_6_patch_flow.py tests/unit/test_fixes_engine_and_verifier.py -q
.....................                                                    [100%]
21 passed
```

Repository-wide Ruff:

```text
\.venv\Scripts\python.exe -m ruff check
Found 11 errors.
```

These findings are in intentionally malformed/adversarial Python examples under `examples/` (invalid syntax, bidi controls and unsafe fixture code) and the pre-existing `run_tests.py` import ordering. They were not changed because they are test inputs or outside this phase's required changes. The changed backend/security files pass Ruff.

Full Python suite:

```text
\.venv\Scripts\python.exe -m pytest -q
No output was produced for 120 seconds; the process was interrupted. No full-suite pass is claimed.
```

Frontend:

```text
npm run test -- --run
Test Files 24 passed (24)
Tests 153 passed (153)

npm run lint
0 errors, 36 warnings (mostly existing explicit-any and hook dependency warnings)

npm run build
✓ built in 1m 13s
```

Vite reported the existing main bundle larger than 500 kB. The test includes `<img onerror>`, a `javascript:`-looking string, terminal escapes and a bidi override; the sanitizer removes control/format characters and React still renders text rather than HTML.

## Verification limits / acceptance status

- Cookie-context isolation was tested using two independent opaque identities; request body session IDs do not select the scoped session. An actual second-browser/HTTP confirmation was attempted using separate ASGI clients, but requests stalled without a response in this environment. Browser isolation is therefore **not confirmed end to end**.
- Request rejection is enforced before Pydantic parsing when a valid `Content-Length` exceeds 1 MiB. Chunked requests without a declared length are not capped by this middleware. Source limits are also applied by analysis endpoints, but many older schemas validate after JSON decoding. Token and finding caps reject oversized results after lexing/analysis and therefore do not bound peak analyzer memory. AST tree responses cap node count at 2,000. AST response IDs are session-scoped and cannot be expanded from another cookie context.
- Four concurrent expensive requests are admitted. Analysis still runs in threads and has no process memory cap; Python analysis may continue after a request timeout. Token and findings-per-file maximums are enforced on outputs (100,000 tokens and 2,000 findings), but only after the relevant lexer/analyzer has run. These required resource controls are **incomplete**.
- AI provider requests are limited by the existing 512 KiB prompt cap, 2,048 output-token cap and retry policy, and endpoint rate limits. No provider key is returned to the frontend. Remote consent is session scoped.
- No live optional analyzer was run. The runner's `network_sandbox_available()` returns false on this host, so external tool execution is reported unavailable. This is the safe fail-closed state, not an analyzer pass.
- The optional Run/Test feature is unavailable without an OS-enforced sandbox. Windows currently has subprocess timeout/kill behavior only; process-tree cleanup and memory/job-object isolation are not established.

SL2-9 is recorded as **partial** in `docs/STATE.md`; no claim is made that all Part 13 resource limits or browser acceptance have passed.
