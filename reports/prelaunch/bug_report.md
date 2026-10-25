# SecureLex IDE — Pre-Launch Bug Report

> Generated: 2026-10-13 · QA Agent Run

---

## Open Bugs

### BUG-001 · Fix verification returns `verified=False` for deterministic cmd_injection fix
- **Severity**: Medium
- **Component**: `src/apsla/server/app.py` — `/api/fix` endpoint
- **Reproduction**: `POST /api/fix` with `cmd_injection_flask.py` fixture → fix is applied, `diff` is non-empty, but `verification.verified` is `False`
- **Expected**: After applying the deterministic fix, re-analysis should confirm the finding is resolved
- **Actual**: Fix is applied (new_source differs), but verification logic still detects the original pattern
- **Test**: `tests/unit/test_server_api.py::test_fix_endpoint_happy_path_and_reanalyze` (line 274)
- **Impact**: Users who apply a deterministic fix see an incorrect "unverified" status in the Fix Review modal
- **Recommendation**: Review the re-analysis pass in the fix endpoint — the finding matcher may be comparing against the original source instead of `new_source`

---

### BUG-002 · Fix-all endpoint finds no applicable fixes for yaml_load_unsafe fixture
- **Severity**: Medium
- **Component**: `src/apsla/server/app.py` — `/api/fix-all` endpoint
- **Reproduction**: `POST /api/fix-all` with `yaml_load_unsafe.py` fixture → `applied: []`, no fixes generated
- **Expected**: At least one deterministic fix should be proposed for `yaml.load()` → `yaml.safe_load()`
- **Actual**: Endpoint returns `new_source` (unchanged) and empty `applied` list
- **Test**: `tests/unit/test_server_api.py::test_fix_all_endpoint` (line 336)
- **Impact**: "Fix All" button in UI has no effect for certain vulnerability patterns
- **Recommendation**: Ensure the YAML unsafe-load rule in `src/apsla/rules/` includes a fix template, and the fix-all pipeline iterates through applicable rule-based fixes

---

### BUG-003 · C++ fix-all does not generate `snprintf` replacement without AI provider
- **Severity**: Low
- **Component**: `src/apsla/server/app.py` — `/api/fix-all` endpoint (C++ path)
- **Reproduction**: `POST /api/fix-all` with `strcpy(dest, src)` C code → `new_source` is unchanged
- **Expected**: Deterministic fix should replace `strcpy` → `snprintf` for buffer overflow rule
- **Actual**: Source returned unmodified
- **Test**: `tests/unit/test_cpp_e2e.py::test_cpp_api_fix_all` (line 83)
- **Impact**: C++ users cannot auto-fix buffer overflow findings without an AI provider configured
- **Recommendation**: Add deterministic `strcpy→snprintf` fix template to the C/C++ rules or mark the test as `@pytest.mark.requires_ai`

---

### BUG-004 · Benchmark case #19: `return 5` at module level not detected as syntax error
- **Severity**: Low
- **Component**: `src/apsla/languages/python_lang/` — syntax detection
- **Reproduction**: Analyze `return 5` as Python with no enclosing function
- **Expected**: At least one lexical/syntax finding for bare `return` outside function
- **Actual**: 0 findings; Python's `ast.parse()` may accept this in some modes
- **Test**: `tests/unit/test_lexical_syntax_cases.py::test_user_benchmark_case[python_syntax_19]` (line 585)
- **Impact**: One benchmark assertion fails; no user-facing behavior change
- **Recommendation**: Either update the benchmark expectation or add a custom lint rule for bare `return` at module level

---

### BUG-005 · Golden script crashes on `api_metadata` collection
- **Severity**: Low
- **Component**: `scripts/golden.py:230`
- **Reproduction**: Run `python scripts/golden.py check` → crashes with `AttributeError: 'str' object has no attribute 'get'`
- **Expected**: `collect_api_metadata()` iterates sample entries as dicts
- **Actual**: Some sample entries are strings, not dicts — `.get("id")` fails
- **Test**: `reports/prelaunch/logs/golden_check.log` (line 129-141)
- **Impact**: CI golden check script cannot complete; does not affect product
- **Recommendation**: Guard with `isinstance(s, dict)` or fix the sample catalogue structure returned by the API

---

### BUG-006 · Mypy reports 41 type errors across 8 files
- **Severity**: Low (no runtime impact)
- **Component**: Multiple files — see [test_matrix.md §1.1](file:///c:/Users/ROSHAN%20GUPTA/OneDrive/Documents/Desktop/AIDS%20-Nitw/sem3/toc/securelex-ide/reports/prelaunch/test_matrix.md)
- **Reproduction**: `mypy src/apsla/ --ignore-missing-imports`
- **Impact**: Type safety is not enforced at compile time; all errors are annotation gaps, not logic bugs
- **Recommendation**: Fix incrementally. Priority files: `server/app.py` (16 errors), `agents/provider_v2.py` (7 errors)

---

### BUG-007 · Golden characterisation diffs for fixtures_ml_off/on.json
- **Severity**: Info
- **Component**: `tests/golden/`
- **Details**: Two new test fixtures (`default_example.tokens.json`, `bandit.json`) were added to the test corpus but not regenerated into the golden files
- **Impact**: CI golden check reports diffs; no product impact
- **Recommendation**: Run `python scripts/golden.py update` to regenerate golden files

---

### BUG-008 · OpenAPI schema golden diff — SafetyScenarioResponse description added
- **Severity**: Info
- **Component**: `tests/golden/openapi_schema.json`
- **Details**: `SafetyScenarioResponse` model now has a `description` field in the OpenAPI schema. This is an improvement, not a regression.
- **Impact**: Golden check reports a diff
- **Recommendation**: Regenerate golden files

---

### BUG-009 · AI features fail with HTTP 503/404 due to model tag mismatch and false positive model detection
- **Severity**: Critical (User POV)
- **Component**: `src/apsla/llm/local_ollama.py` (lines 240-247) & `src/apsla/agents/provider_v2.py` (line 185)
- **Reproduction**:
  1. Have Ollama running with `qwen2.5-coder:1.5b` (or any non-3b tag).
  2. Open IDE at `http://localhost:5173/`. UI shows `ollama · local` and enables "Build with AI", "Fix with AI", and "Explain".
  3. Click "Build with AI" -> enter prompt -> click "Generate" -> Drawer errors with "Generation failed: Provider returned HTTP status 404".
  4. Click "Fix with AI" or inline "Fix" -> Fix modal gets stuck on "Preparing proposal..." because `POST /api/fixes/propose` with `origin='ai'` returns HTTP 503 (`AI proposal unavailable: Provider returned HTTP status 404`).
  5. Click "Explain" on any finding -> AI Explain panel errors with HTTP 503 (`AI explanation unavailable: Provider returned HTTP status 404`).
- **Root Cause**:
  `local_ollama.py` tests `m.split(":")[0] == clean_target` (`"qwen2.5-coder"`), which evaluates to `True` for `qwen2.5-coder:1.5b`. It sets `model_present = True` and tells the frontend AI is ready. However, it never updates `model_name` or configures the provider with the matched tag. The provider still attempts to call `qwen2.5-coder:3b`, which Ollama rejects with HTTP 404 Not Found.
- **Impact**: All AI capabilities advertised in the UI are completely broken out of the box unless the user explicitly happens to have pulled the exact `3b` tag.
- **Recommendation**: Update `local_ollama.py` and `provider_v2.py` to either auto-select the detected matching tag, or correctly report `model_present = False` with the exact pull command if the exact tag is missing.

---

### BUG-010 · Explaining syntax/lexical diagnostics fails with HTTP 404
- **Severity**: High (User POV)
- **Component**: `src/apsla/server/app.py` (lines 1581-1594) — `/api/ai/explain`
- **Reproduction**:
  1. Open a file with syntax/lexical diagnostics (e.g. `Exercise C++ Literals`).
  2. Switch to Problems tab.
  3. Click the "Explain" button next to any diagnostic item.
- **Expected**: An explanation of the diagnostic is generated or provided.
- **Actual**: Request fails with `HTTP 404: Selected diagnostic is not present in current analysis evidence.`
- **Root Cause**:
  The handler executes `result = Analyzer().analyze(...)` and then filters:
  ```python
  found = next((f for f in result.findings if f.id == req.target_id and getattr(f, "kind", None) in {"lexical", "syntax"}), None)
  ```
  However, `result.findings` from `Analyzer().analyze()` only populates security findings (`kind == "security"`). Lexical and syntax diagnostics are not present in `result.findings` under those IDs, making this lookup impossible to satisfy.
- **Impact**: The "Explain" button in the Problems tab is completely broken for all syntax and lexical diagnostics.
- **Recommendation**: Look up the diagnostic in `result.syntax_diagnostics` or `stage_data` rather than `result.findings`.

---

### BUG-011 · Inline "Fix" buttons in Problems tab are permanently disabled
- **Severity**: Medium (User POV)
- **Component**: `web/src/ide/problems/ProblemsPanel.tsx` (line 25)
- **Reproduction**:
  1. Open any sample with problems in the Problems tab.
  2. Observe the "Fix" button next to each problem row.
- **Expected**: If a fix is available, the Fix button is enabled.
- **Actual**: The "Fix" button is disabled on every diagnostic row with tooltip "No fixable finding is associated with this diagnostic."
- **Root Cause**:
  `ProblemsPanel.tsx` tests `const fixable = result?.security_findings?.some(finding => finding.id === item.id) ?? false;`. Diagnostic IDs from syntax/semantic checkers never match security finding fingerprints.
- **Impact**: Users see disabled Fix buttons next to all problems, giving the impression of broken UI controls.
- **Recommendation**: Wire diagnostic IDs to corresponding security findings or rule fixes, or hide the Fix button when a diagnostic is purely syntactic without an available fix.

---

### BUG-012 · "Format" toolbar button is permanently disabled across all 4 languages
- **Severity**: Medium (User POV)
- **Component**: `src/apsla/server/tool_runner.py` & `web/src/ide/IDE.tsx` (line 443)
- **Reproduction**:
  1. Open any file in Python, Java, JavaScript, or C++.
  2. Observe the "Format" button in the editor toolbar.
- **Expected**: User can format their code using standard built-in or virtual environment formatters (e.g. Monaco document formatting or `ruff format` for Python).
- **Actual**: Button is permanently disabled with tooltip "No formatter is available for this language".
- **Root Cause**:
  The backend checks for external binaries (`clang-format`, `black`, `prettier`, `google-java-format`) on system PATH. When not installed globally, `formatter` is returned as `null`. Even though `ruff` is present and capable of formatting Python code (`ruff format`), it is only registered as an analyzer. Furthermore, Monaco's client-side formatting action is guarded by `disabled={!languageInfo?.formatter}`.
- **Impact**: A standard IDE code formatting experience is unavailable to users without manual global tool installations.
- **Recommendation**: Register `ruff` as a formatter for Python, and allow Monaco client-side formatting fallback when external CLI tools are absent.

---

### BUG-013 · False "Analysis Incomplete" status displayed in red for normal successful analysis
- **Severity**: Low / UI Polish
- **Component**: `web/src/ide/tokens/tokenModel.ts` (lines 64-69)
- **Reproduction**:
  1. Analyze any valid C++, Python, or Java code.
  2. Notice the status bar and Tokens tab header display `Analysis incomplete` in red.
- **Expected**: A clean analysis run indicates "Up to date" or "Analysis complete".
- **Actual**: Shows "Analysis incomplete: Analysis completed with unavailable or incomplete checks."
- **Root Cause**:
  `isAnalysisIncomplete` returns true if ANY tool in the tool registry has `status === 'unavailable'`. Because tools like `clang-tidy`, `cppcheck`, `bandit`, and `eslint` are optional external linters that most users do not have installed simultaneously, every normal analysis run is branded "incomplete".
- **Impact**: Users believe the analyzer is broken or failing on their code.
- **Recommendation**: Differentiate between primary engine completion (lexical/syntax/security AST pass) and optional external linter availability.

---

## Summary

| Severity | Count | Ship-Blocking? |
|----------|-------|----------------|
| **Critical** | 1 (BUG-009) | **YES** — Breaks primary marketed feature (AI assistance / Fix / Build / Explain) |
| **High** | 1 (BUG-010) | **YES** — Explaining problems in UI is 100% broken |
| **Medium** | 4 (BUG-001, BUG-002, BUG-011, BUG-012) | Fix pipeline & formatting degradation |
| **Low** | 5 (BUG-003 – BUG-006, BUG-013) | No |
| **Info** | 2 (BUG-007, BUG-008) | No |
| **Total** | **13** | **2 Ship-Blocking bugs found from User POV** |

