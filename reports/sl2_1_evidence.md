# SL2-1 Evidence — Versioned contracts and bounded tool boundary

**Date:** 2026-10-12  
**Status:** Partial. Models, adapter, discovery, OpenAPI, and non-HTTP tests passed. Live HTTP verification and the full test suite are blocked by this host's local asyncio socket restriction. No completion tag was created.

## Implemented

- Added Pydantic v2 result types and an adapter in `src/apsla/models_v2.py`. It preserves the legacy result, computes SHA-256 over UTF-8 source, echoes `source_version`, emits stable per-analysis token IDs, and exposes UTF-16 plus code-point offsets. Taint paths are marked incomplete because the current engine does not establish whole-path completeness.
- Added API version selection, `/api/capabilities`, and lexical, syntax, security, and quality routes. `/api/analyze` keeps v1 as the default. Security-stage coupling and missing quality/semantic engines are disclosed in omissions/statuses.
- Added Part 7.4 wording in `src/apsla/status_wording.py` and an OpenAPI override for conditional v1/v2 responses. Generated `docs/api_v2.md` from the app's OpenAPI schema.
- Added allowlisted tool discovery and fixed static profiles in `src/apsla/server/tool_runner.py`. Discovery uses `shutil.which`, short version timeouts, and bounded output. The runner uses argument arrays, fixed executable/profile allowlists, random temporary directories, a scrubbed environment, timeouts, output caps, and cleanup. It fails closed for analyzer execution unless an OS-enforced network sandbox is configured; none is configured on this Windows host. Semgrep is also skipped without a bundled offline ruleset.
- Added tests in `tests/unit/test_sl2_v2.py`; no frontend, `legacy/`, `data/`, or `ml/artifacts/` files were changed.

## Test and lint output

Focused SL2-1 tests:

```text
Command: .venv\Scripts\python.exe -m pytest tests/unit/test_sl2_v2.py -o addopts='' -q --basetemp=reports/sl2_1_pytest_basetemp
........................................................................ [ 26%]
........................................................................ [ 52%]
........................................................................ [ 78%]
............................................................             [100%]
276 passed in 7.87s
```

Focused Ruff:

```text
Command: .venv\Scripts\ruff.exe check src/apsla/models_v2.py src/apsla/status_wording.py src/apsla/server/tool_runner.py src/apsla/server/schemas.py src/apsla/server/app.py tests/unit/test_sl2_v2.py
All checks passed!
```

Full Ruff:

```text
Command: .venv\Scripts\ruff.exe check .
I001 [*] Import block is un-sorted or un-formatted
 --> run_tests.py:1:1
Found 1 error.
```

`run_tests.py` was already an untracked workspace file at the start of SL2-1; it was left untouched.

Existing model/offset regression tests:

```text
Command: .venv\Scripts\python.exe -m pytest tests/unit/test_models.py tests/unit/test_offset_map.py -o addopts='' -q --basetemp=reports/sl2_1_regression_pytest
10 passed in 4.48s
```

Golden rule/fixture schema check:

```text
Command: .venv\Scripts\python.exe scripts/check_rule_fixtures.py
Catalog rules found: 58
Rules covered in fixtures: 64
[OK] All rules have fixture coverage and all expect.json files match schema.
```

Full pytest was attempted:

```text
Command: .venv\Scripts\python.exe -m pytest -q --basetemp=reports/sl2_1_full_pytest -o faulthandler_timeout=60
Blocked at tests/e2e/test_java_end_to_end.py::test_languages_endpoint_includes_java
Trace: asyncio.windows_events.ProactorEventLoop._make_self_pipe -> socket._fallback_socketpair -> socket.accept
      anyio.from_thread.run_blocking_portal -> starlette.testclient.TestClient.handle_request
The test waited without progressing and the run was interrupted. No full-suite pass is claimed.
```

The same TestClient wait occurred for a direct OpenAPI HTTP request. Synchronous `app.openapi()` generation and schema assertions pass, but live ASGI requests could not be exercised because this sandbox blocks the local socket pair needed by Windows asyncio.

## V2 sample adapter check

This exercised the real internal pipeline and adapter, not the blocked HTTP route:

```text
model_valid: True
source_version: 42
source_hash: 1b476b1c34b0a70e5c0c6b91c99776982dad77b9829e75b06563a3df9cc2f876
token_count_derived: 13
security_findings_derived: 1
timing_measured_ms: {'total_ms': 634.99}
unavailable_or_incomplete_notes: ['Semantic diagnostics are not emitted by the current pipeline.', 'Quality observations are not emitted by the current pipeline.']
```

## Capability snapshot from this machine

`build_capabilities()` used the same discovery function as `GET /api/capabilities`; the HTTP response itself remains unverified here.

```text
package_version: 0.1.0
languages: python, java, javascript, cpp (internal lexer and parser available for each)
g++, gcc: unavailable (executable could not start: OSError)
clang, clang++, clang-tidy, cppcheck, javac: unavailable (not on PATH)
node: ok, v24.11.1
ruff: ok, ruff 0.16.8
pyflakes, mypy, eslint, bandit, semgrep, clang-format, black, prettier, google-java-format: unavailable on PATH
ai: Ollama configured=false, reachable=false, model=qwen2.5-coder:3b, model_present=false, processing_location=local
limits: max_source_bytes=524288, max_tokens=null, analysis timeout=10.0s, concurrency=null
```

The v2 HTTP response and live capability endpoint require a host where the local asyncio transport can run. External analyzer execution remains unavailable until an OS-enforced network sandbox is provided.

## Branch/tag and scope

The current branch is `sl2-0`. Creating `codex/sl2-1` failed because Git could not create the ref directory (`fatal: unable to create directory for .git/refs/heads/codex/sl2-1`); workspace permissions expose `.git` as read-only. No tag was created. No UI changes were made.
