# SL2-6 evidence

Date: 2026-10-12

## Implemented

- Added `PatchProposalV2` with source SHA-256/version binding, origin, atomic UTF-16 ranges, diff, rationale, expected outcome, assumptions, risks and UTC creation time.
- Patch validation rejects stale hashes/versions, invalid or clamped coordinates, overlapping/no-op edits, excessive edit count/replacement bytes, and mismatched diffs.
- Added `/api/fixes/propose`, `/api/fixes/verify`, `/api/fixes/apply` and `/api/fixes/undo`. Proposals are drafts; apply requires `approved: true`, reruns verification, records a bounded ten-entry per-session undo stack and increments the version.
- Added `apsla.fixes.independent_verifier`; it runs the legacy deterministic analyzer, the v2 parser, available semantic checks and quality measurements on original and patched strings. It does not inspect the proposal's rationale, expected outcome or any claimed success. User tests are explicitly reported unavailable.
- Routed legacy `/api/fix` and `/api/fix-all` through the independent verifier. Fix-all attempts at most three distinct safe candidates and skips rejected candidates.
- Added the public-server exercise script `scripts/e2e_fix_flow.py` for Python, Java, JavaScript and C++.

## Commands and observed results

Focused static checks:

```text
.venv\Scripts\ruff.exe check src/apsla/fixes/patch_v2.py src/apsla/fixes/independent_verifier.py src/apsla/server/app.py tests/unit/test_sl2_6_patch_flow.py scripts/e2e_fix_flow.py
All checks passed!
```

Focused formatting check was run after formatting the changed files; all five files pass `ruff format --check`.

```text
.venv\Scripts\pytest.exe -v tests/unit/test_sl2_6_patch_flow.py tests/unit/test_fixes_engine_and_verifier.py tests/unit/test_fixes_edits.py --basetemp=reports/.pytest-sl26-focused
collected 15 items
tests/unit/test_sl2_6_patch_flow.py ....
tests/unit/test_fixes_engine_and_verifier.py ....
tests/unit/test_fixes_edits.py .......
15 passed in 4.09s
```

OpenAPI route registration:

```text
PYTHONPATH=src .venv\Scripts\python.exe -c "from apsla.server.app import app; print([p for p in app.openapi()['paths'] if '/fixes/' in p])"
['/api/fixes/propose', '/api/fixes/verify', '/api/fixes/apply', '/api/fixes/undo']
```

The live script was attempted against `http://127.0.0.1:8010/api`. All four language iterations returned the actual local error `WinError 10013` (socket access forbidden by the environment). Therefore no live propose/verify/apply/re-analyze/undo cycle is claimed. `tests/unit/test_server_api.py` was started (19 tests collected) but stalled before printing test results in this Windows environment and was interrupted; the full suite was also started but did not produce results before interruption. Repository-wide `ruff check .` reports existing diagnostics in intentionally malformed example fixtures and `run_tests.py`; the changed-file Ruff command passes.

## Limits / not claimed

- The API and in-memory verifier paths import and register successfully, but live HTTP integration is blocked by the socket sandbox.
- The verifier currently runs the internal deterministic security findings plus available semantic checks. It does not independently invoke each SL2-4 external security adapter, execute user tests, or provide a measured syntax-tree drift/regression fixture result; these remain explicitly unverified rather than successful.
- There is no user-code execution or project-test sandbox. No submitted source is executed.
- The local groq/model state was unavailable in SL2-5 evidence; the AI proposal route was not exercised with a live provider or FakeProvider through HTTP.
