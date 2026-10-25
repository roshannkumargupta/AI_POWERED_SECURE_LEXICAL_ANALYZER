# SL2-10 Evidence — Acceptance and Handoff

Date: 2026-10-12. Scope: documentation, acceptance inventory, lint fixture scope and safe unified-check runner. Earlier SL2 phase changes were already present in this shared working tree.

## Changes

- Rewrote the README and updated the user guide/demo script with actual setup, provider/consent, test and limitation guidance.
- Removed the destructive `git checkout -- reports/` behavior from `scripts/check_all.py`; subprocess commands now use argument arrays, `shell=False`, and a 900-second per-gate timeout. Added explicit security and browser E2E gates.
- Excluded intentionally malformed/insecure `examples/` inputs from Ruff source linting and sorted `run_tests.py` imports.
- Added the Part 17 acceptance matrix at `reports/sl2_final_acceptance.md`.

## Commands and actual results

- `\.venv\Scripts\ruff.exe check` — **All checks passed!**
- `\.venv\Scripts\python.exe scripts\check_links.py` — all links verified across 82 documentation files.
- `\.venv\Scripts\mypy.exe` — **failed: 36 errors in 8 files**. No pass claimed.
- `npm.cmd run test` — **24 files passed, 153 tests passed** on each of three consecutive runs (Vitest 2.1.9); no flake observed.
- `.\.venv\Scripts\python.exe -m pytest -m security -q` — **15 passed** on each of three consecutive runs; each emitted the same Starlette/httpx deprecation warning.
- `npm.cmd run build` — **passed**, Vite build completed in 1m 5s. Existing bundle warning: main index chunk is 3,666.07 kB before gzip.
- `npm.cmd run e2e` — **blocked/fails before setup**: `connect EACCES 127.0.0.1:9222`.
- `.\.venv\Scripts\python.exe -m pytest -q` — no output or summary in the observed wait; prior phase documented 120-second stall. Incomplete, not a pass.
- `.\.venv\Scripts\python.exe scripts\golden.py --check` — did not return a result during observation. No pass claimed.
- Three-run full suite and fresh-clone acceptance were not completed. The frontend and security-marked suites were repeated three times; the full Python suite was not.

## Honest status

groq CLI exists but no service is reachable. `javac`, Clang tools, cppcheck, Semgrep, Bandit, Pyflakes and Playwright/browser tooling are unavailable (see `docs/sl2_environment.md`). Java compiler-backed analysis, optional external analyzers, live-model paths and browser screenshot acceptance were therefore not exercised. The compatibility routes `/api/fix` and `/api/fix-all` remain because current tests/clients reference them. Git branch/tag state and uncommitted phase changes prevent a clean clone of this exact state; no tag is claimed.

See `reports/sl2_final_acceptance.md` for all 16 criteria, the honesty sweep commands, and limitations.
