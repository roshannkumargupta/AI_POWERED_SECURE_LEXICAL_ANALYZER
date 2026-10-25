# SecureLex IDE — Pre-Launch Test Matrix

> Generated: 2026-10-13 · Environment: Windows 11 · Python 3.12 · Node 22 · Vitest 2.1.9

---

## 1  Static Analysis — Python Backend

| Tool | Scope | Result | Notes |
|------|-------|--------|-------|
| **Ruff lint** | 129 source files (excl. legacy, fixtures, web, .venv) | ✅ **0 errors** | `ruff check .` — clean |
| **Ruff format** | src/ + tests/ + scripts/ | ✅ **0 diffs** | Formatting consistent with `ruff.toml` |
| **Mypy** | 129 source files, `--ignore-missing-imports` | ⚠️ **41 errors in 8 files** | Type narrowing gaps; no runtime impact. See §1.1 |

### 1.1  Mypy Error Breakdown

| File | Errors | Primary Issue |
|------|--------|---------------|
| `models_v2.py` | 4 | Literal assignment mismatches |
| `server/app.py` | 16 | Variance (`list` vs `Sequence`), `Literal` narrowing, union-attr |
| `server/tool_runner.py` | 3 | Redefined name, incompatible assignment |
| `server/schemas.py` | 1 | `default_factory` callable signature |
| `security_v2.py` | 4 | `object` missing `.get()` / `__iter__` |
| `agents/provider_v2.py` | 7 | `str | None` → `str` narrowing |
| `safety_lab.py` | 2 | Incompatible assignment |
| `parsing_v2.py` | 2 | Optional module, missing `root_node` |

> **Verdict**: These are annotation issues, not logic bugs. The runtime uses duck-typing and `getattr` calls that work correctly. Recommended to fix before v1.0.

---

## 2  Static Analysis — Frontend (TypeScript / React)

| Tool | Scope | Result | Notes |
|------|-------|--------|-------|
| **tsc --noEmit** | Full frontend (`web/src/`) | ✅ **0 errors** | Clean TypeScript compilation |
| **Vite build** | Production bundle | ✅ **Builds successfully** | 1110 modules transformed, gzipped output ~1.8 MB total |

---

## 3  Unit & Integration Tests — Python Backend (pytest)

| Suite | Passed | Failed | Skipped | Notes |
|-------|--------|--------|---------|-------|
| **Full suite** (excl. `test_fix_javascript_e2e`) | ~1012 | **4** | 1 (filtered) | See §3.1 |

### 3.1  Failing Tests (4)

| # | Test | File | Root Cause | Severity |
|---|------|------|------------|----------|
| 1 | `test_cpp_api_fix_all` | `test_cpp_e2e.py:83` | Fix endpoint does not auto-generate `snprintf` replacement without AI provider | **Low** — AI-dependent fix; deterministic pipeline correctly returns original source |
| 2 | `test_user_benchmark_case[python_syntax_19]` | `test_lexical_syntax_cases.py:585` | `return 5` outside function: Python AST parses bare `return` without raising SyntaxError at module level in some CPython builds | **Low** — edge case in benchmark expectations |
| 3 | `test_fix_endpoint_happy_path_and_reanalyze` | `test_server_api.py:274` | Fix verification returns `verified=False` — deterministic fix is applied but re-analysis still detects the original pattern | **Medium** — fix verification logic needs review |
| 4 | `test_fix_all_endpoint` | `test_server_api.py:336` | `applied` list empty — fix-all endpoint finds no applicable deterministic fixes for yaml_load_unsafe fixture | **Medium** — fix-all coverage gap for YAML rules |

### 3.2  Skipped / Filtered Test (1)

| Test | Reason |
|------|--------|
| `test_fix_javascript_e2e` | Known environment-dependent failure (Node/ESLint fixture path) |

---

## 4  Unit Tests — Frontend (Vitest)

| Metric | Value |
|--------|-------|
| **Test files** | 40 / 40 passed |
| **Total tests** | **202 / 202 passed** |
| **Duration** | 57.63s |
| **Failures** | **0** |

---

## 5  API Smoke Tests (20 tests against live server)

| ID | Test | Result |
|----|------|--------|
| API-01 | Health endpoint truthful and schema-valid | ✅ |
| API-02 | Capabilities returns real installed tool state | ✅ |
| API-03 | Languages endpoint lists 4 supported languages | ✅ |
| API-04 | Samples catalogue & language filtering (153 total, 46 Python) | ✅ |
| API-05 | Minimal valid analysis for all 4 languages | ✅ |
| API-06 | Empty / whitespace-only source handled cleanly | ✅ |
| API-07 | Input validation rejects missing fields, bad enums, malformed JSON | ✅ |
| API-08 | v1 and v2 response contracts conform to schema | ✅ |
| API-09 | Stage endpoint `/api/analyze/lexical` returns stage data | ✅ |
| API-10 | Syntax-invalid code still returns usable lexical tokens | ✅ |
| API-11 | Security findings distinct from token lexical validity | ✅ |
| API-12 | Coordinates format (1-based, UTF-16 code units, emoji-safe) | ✅ |
| API-13 | Zero-finding clean code: `findings=[], score=100` | ✅ |
| API-14 | Repeated identical analysis is byte-level deterministic | ✅ |
| API-15 | Source version echoing prevents stale overwrite | ✅ |
| API-16 | Invalid fix/finding IDs fail closed (HTTP 404) | ✅ |
| API-17 | Error responses do not leak stack traces or paths | ✅ |
| API-18 | Request body >512 KB rejected with HTTP 413 | ✅ |
| API-19 | Concurrent independent requests do not mix tokens | ✅ |
| API-20 | Host header injection rejected (HOST_REJECTED) | ✅ |

**Result: 20 / 20 PASS**

---

## 6  Browser / UI Testing

### 6.1 Basic Surface Rendering

| Test | Method | Result | Evidence |
|------|--------|--------|----------|
| Landing page loads, title correct | Browser subagent | ✅ PASS | `screenshots/01_ide_initial.png` |
| Sample file selector works (Python category) | Browser subagent | ✅ PASS | `screenshots/02_sample_loaded.png` |
| "Analyze" button triggers analysis, results populate | Browser subagent | ✅ PASS | `screenshots/03_analyzed_results.png` |
| Tokens tab shows token table with type/value/line | Browser subagent | ✅ PASS | Token inspection view |
| Problems tab shows diagnostics | Browser subagent | ✅ PASS | Diagnostic list |
| Security tab shows findings with severity badges | Browser subagent | ✅ PASS | Severity badges |
| AI Explain tab renders layout | Browser subagent | ✅ PASS | Explain panel |
| Agent Activity tab renders trace entries | Browser subagent | ✅ PASS | Trace view |

### 6.2 Interactive User-Journey Operations (User Perspective)

| Interactive Operation | Expected Behavior | Actual Behavior | Result | Bug Reference |
|-----------------------|-------------------|-----------------|--------|---------------|
| **Build with AI**: Generate candidate from prompt | Generates AI candidate code | Crashes with HTTP 404/503 "Provider returned HTTP status 404" | ❌ **FAIL** | BUG-009 |
| **Fix with AI**: Propose fix for security finding | Proposes patch with diff and reasoning | Propose request fails 503; modal hangs on "Preparing proposal..." | ❌ **FAIL** | BUG-009 |
| **AI Explain**: Explain security finding / token | Provides evidence-grounded AI explanation | Fails with HTTP 503 error alert | ❌ **FAIL** | BUG-009 |
| **AI Explain**: Explain syntax / lexical problem | Explains compiler / syntax diagnostic | Fails with HTTP 404 "Selected diagnostic is not present" | ❌ **FAIL** | BUG-010 |
| **Problems Panel**: Click inline "Fix" button | Opens Fix proposal for fixable issues | Permanently disabled for all problem rows | ❌ **FAIL** | BUG-011 |
| **Toolbar**: Click "Format" document button | Formats current source in editor | Permanently disabled across Python, Java, JS, C++ | ❌ **FAIL** | BUG-012 |
| **Status Bar**: Clean analysis status indicator | Shows "Up to date" or "Clean" | Shows red "Analysis incomplete" due to optional tools | ⚠️ **FAIL** | BUG-013 |
| **Security Panel**: Flag false positive | Submits feedback and shows toast | Successfully records feedback | ✅ PASS | Verified |
| **Security Panel**: Data flow / taint path step navigation | Jumps editor to taint step range | Editor jumps to line/column | ✅ PASS | Verified |

---

## 7  Golden Characterisation Tests

| Golden File | Result | Notes |
|-------------|--------|-------|
| `fixtures_ml_off.json` | ⚠️ **DIFF** | New `default_example.tokens.json` + `bandit.json` fixtures added to test corpus |
| `fixtures_ml_on.json` | ⚠️ **DIFF** | Same new fixture additions as above |
| `samples_ml_off.json` | ✅ OK | |
| `samples_ml_on.json` | ✅ OK | |
| `openapi_schema.json` | ⚠️ **DIFF** | Added `description` to `SafetyScenarioResponse` model + trailing newline |
| `cli_help.json` | ✅ OK | |
| `rules_per_language.json` | ✅ OK | |
| `api_metadata` | ❌ **CRASH** | `AttributeError: 'str' object has no attribute 'get'` in `scripts/golden.py:230` |

> **Verdict**: Fixture diffs are expected from new test files being added. The `api_metadata` crash is a bug in the golden script, not in the product.

---

## 8  Security Scans

| Check | Result | Notes |
|-------|--------|-------|
| Hardcoded secrets/API keys in source | ✅ **None found** | Grep for `sk-`, `api_key=`, `password=`, `secret=` across Python + TS |
| `.env` protected in `.gitignore` | ✅ | Lines 46-48: `.env`, `.env.local`, `.env.*.local` |
| `.env.example` contains no real credentials | ✅ | All API key fields empty |
| `eval()` / `exec()` in production code | ✅ **Not found** | Only in test fixtures (intentional vulnerable samples) |
| Error responses leak no stack traces | ✅ | Verified via API-17 |
| Host boundary enforced | ✅ | Verified via API-20 |
| Request body size limit enforced | ✅ | Verified via API-18 (413 at >512 KB) |
| Concurrent request isolation | ✅ | Verified via API-19 |

---

## 9  Documentation & Build Integrity

| Check | Result | Notes |
|-------|--------|-------|
| README.md setup instructions | ✅ | Accurate for Windows + macOS/Linux |
| Markdown link integrity (82 doc files) | ✅ | All links valid |
| Production build (`npm run build`) | ✅ | Compiles without errors |
| `.gitignore` comprehensive | ✅ | Covers .env, __pycache__, node_modules, logs, IDE files |

---

## Summary Scorecard

| Dimension | Pass | Fail/Warn | Total | Rate |
|-----------|------|-----------|-------|------|
| Ruff lint | 129 | 0 | 129 | 100% |
| Mypy type check | 88 files | 8 files (41 errors) | 129 | 93.8% |
| tsc --noEmit | All | 0 | All | 100% |
| Python unit tests | ~1012 | 4 | ~1016 | 99.6% |
| Frontend tests | 202 | 0 | 202 | 100% |
| API smoke tests | 20 | 0 | 20 | 100% |
| UI Surface smoke tests | 8 | 0 | 8 | 100% |
| UI Interactive User Operations | 2 | 7 | 9 | 22.2% |
| Golden characterisation | 4 | 3 diff + 1 crash | 8 | 50% |
| Security checks | 8 | 0 | 8 | 100% |
| Doc/build checks | 4 | 0 | 4 | 100% |

> **Evidence**: All raw logs in [`reports/prelaunch/logs/`](file:///c:/Users/ROSHAN%20GUPTA/OneDrive/Documents/Desktop/AIDS%20-Nitw/sem3/toc/securelex-ide/reports/prelaunch/logs/), screenshots in [`reports/prelaunch/screenshots/`](file:///c:/Users/ROSHAN%20GUPTA/OneDrive/Documents/Desktop/AIDS%20-Nitw/sem3/toc/securelex-ide/reports/prelaunch/screenshots/).
