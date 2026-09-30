# Project State & Progress Tracking

**Current Phase:** Phase 6 Complete — IDE Web Application (Vite, React 18, Monaco Editor, SecureLex Night Theme, Offline Bundle)  
**Phase Tag:** `phase-6`  
**Date:** September 30, 2026  
**Status:** Complete / Verified (202 Python pytest tests passing, 14 Vitest unit tests passing, 100% clean ruff linter & formatter, production build validated)  

---

## 1. What Exists

### Repository & Legacy Layout (Read-Only)
- `legacy/senior-part1/`: Original Python analyzer codebase (prototype lexer `W5_6/`, hybrid validator `ML_model/`, carbon tracker `carbon_analysis/`, and React/FastAPI UI `frontend/`).
- `legacy/senior-part2/`: Original Java-oriented analyzer codebase (`AI-Powered-Secure-Lexical-Analyzer`, MIT licensed).
- `legacy/README.md`: Attribution documentation, sanitation records, and 12 verified architectural and security defects.
- `third_party/LICENSE-senior-part2-MIT.txt`: MIT License from senior part 2 (Copyright (c) 2026 Himanshu Sharma).
- `data/raw/`: Raw CSV datasets copied unchanged (`homoglyph_attacks.csv`, `injection_payloads.csv`, `safe_tokens.csv`).
- `data/sources/`: Official Unicode confusable table (`confusables.txt`).
- `data/PROVENANCE.md`: Cryptographic provenance tracking with exact file paths, sizes in bytes, and SHA-256 hashes.
- `data/external/python/`: 42 realistic, hand-written unseen external test snippets with ground truth security labels.
- `data/feedback/`: Append-only user false positive feedback storage (`false_positives.jsonl`).
- `docs/plan/`: Preserved Word documents (`Professor_Report_16_Week_Improvement_Plan (1).docx`, `Self_Study_Guide_16_Weeks.docx`).
- `PROJECT_SPEC.md`: Definitive project specification covering sections A through P.
- `docs/api.md`: Comprehensive HTTP REST API reference with genuine request/response examples.
- `docs/explained/phase0.md`: Educational documentation for Phase 0.
- `docs/explained/phase1.md`: Educational documentation for Phase 1 (lexer, tokens, homoglyphs, bidi overrides, 5 viva Q&As).
- `docs/explained/phase2.md`: Educational documentation for Phase 2 (lexer state machines, AST taint vs token windows, sources/sinks/sanitizers, 5 viva Q&As).
- `docs/explained/phase3.md`: Educational documentation for Phase 3 (shadow verification sandbox, AST-safe import injection, back-to-front edits, 5 viva Q&As).
- `docs/explained/phase4.md`: Educational documentation for Phase 4 (45-dim feature space, leak-free group splitting, calibration, occlusion explainability, 5 viva Q&As).
- `docs/explained/phase5.md`: Educational documentation for Phase 5 (REST, JSON, pure function LRU caching, error shielding, 5 viva Q&As).
- `docs/explained/phase6.md`: Educational documentation for Phase 6 (Monaco Editor integration, UTF-16 coordinates, debouncing, AbortController, 5 viva Q&As).
- `reports/phase_5_evidence.md`: Evidence report for Phase 5 REST API and caching.
- `reports/phase_6_evidence.md`: Evidence report for Phase 6 IDE web app and bundle telemetry.
- `docs/screenshots/`: Visual UI evidence (`empty_state.png`, `taint_path.png`, `trojan_source.png`, `fix_all_remediation.png`, `summary_tab.png`).

### Phase 1 Implemented Shared Core Components (`src/apsla/`)
1. **Pydantic v2 Unified Schema (`src/apsla/models.py`):**
   - Coordinates & Spans: `Range` (1-based, UTF-16 code units, end-exclusive).
   - Tokens: `Token` and `TokenInfo` with line/col, UTF-16 offsets, labels (`SAFE`, `SUSPICIOUS`, `MALICIOUS`), and confidence scores.
   - Findings & Remediation: `Finding`, `Fix`, `Edit`, `VerificationResult` (`Verification`), `TaintPathStep` (`TaintStep`), `AnalysisSummary` (`Summary`), `EngineMetadata` (`Engine`), and `AnalysisResult`.
   - String Enums: `Severity`, `Label`, `TaintStepKind` implemented with Python 3.12 `StrEnum`.
2. **Global Configuration Constants (`src/apsla/config.py`):**
   - Severity weights (Critical 25, High 12, Medium 5, Low 2, Info 0) and caps (4, 6, 8, 10).
   - Scoring base (100), fusion weights (0.7 rule / 0.3 ML), taint confirmation bonus (0.15), ML-only finding cap (10), context window size (9), random seed (42), file size limit (512 KB), and execution timeouts (30s analysis, 10s fix, 10s taint, 5s ML).
3. **CWE Mapping & Taxonomy (`src/apsla/cwe.py`):**
   - Dict mapping vulnerability categories to official CWE IDs (CWE-78, 89, 79, 94, 95, 502, 327, 798, 22, 918, 120, 787, 134, 611, 1007, 116, 506).
   - Mandatory human review disclaimer constant (`HUMAN_REVIEW_DISCLAIMER`).
4. **Token Representation & Coordinate Indexing (`src/apsla/lexing/`):**
   - `token.py`: Immutable dataclass `Token` with UTF-16 code unit offsets, embedded expression `parts`, and conversions to `Range` and `TokenInfo`.
   - `common.py`: Bidirectional `OffsetMap` class converting between Python string slice indices, UTF-16 code units, and 1-based (line, col) coordinates, with full surrogate-pair support for astral plane characters (emojis), CRLF/LF/CR newlines, and tabs.
5. **Multi-Vector Unicode Defense Layer (`src/apsla/unicode_defense/`):**
   - `scripts/build_confusables.py`: Generates `src/apsla/unicode_defense/data/confusables.json` containing 1,868 Unicode look-alike characters mapping to ASCII.
   - `scripts.py`: Unicode script classification and mixed-script detection using the `regex` package and `\p{Script=...}` property escapes.
   - `scanner.py`: Detects Trojan Source bidi controls, zero-width characters, Unicode tag characters, non-ASCII whitespace, confusables, and mixed-script identifiers.
   - `recovery.py`: Synthesizes `recovered_text` with confusables replaced and invisibles stripped, alongside an inverse mapping projecting recovered coordinates back onto original source text.
6. **Generic Unicode Rules (`src/apsla/rules/generic.py`):**
   - Language-agnostic security rules: `APS-ALL-UNI-001` (Trojan Source bidi), `APS-ALL-UNI-002` (zero-width characters), `APS-ALL-UNI-003` (tag characters), `APS-ALL-UNI-004` (confusables), `APS-ALL-UNI-005` (mixed-script identifiers), and `APS-ALL-UNI-006` (obfuscated dangerous built-in/keyword recovery).

### Phase 2 Implemented Components
1. **Hand-Written Python Lexer State Machine (`src/apsla/lexing/base.py` & `src/apsla/languages/python_lang/lexer.py`):**
   - `LexerBase`: Deterministic cursor, peek, advance, UTF-16 and 1-based line/col tracking. Zero crash design; invalid characters emit `ERROR` tokens.
   - `PythonLexer`: Lossless trivia preservation (`"".join(t.text for t in tokens) == source`).
2. **Deterministic Python Security Rule Engine (`src/apsla/rules/base.py` & `src/apsla/languages/python_lang/rules.py`):**
   - 14 deterministic rules detecting injection, unsafe deserialization, weak cryptography, hard-coded credentials, SSRF/networking, path traversal, dynamic imports, obfuscated execution, and cross-site scripting.
3. **AST Data-Flow Taint Analysis Engine (`src/apsla/languages/python_lang/taint.py`):**
   - Flow-sensitive intra-file taint tracker with source tracking, container/format string propagation, sanitizers, and sink detection producing full provenance paths.

### Phase 3 Implemented Components
1. **Atomic Text Edit Application (`src/apsla/fixes/edits.py`):**
   - `apply_edits(source: str, edits: list[Edit]) -> str`: Sorts non-overlapping edits descending by UTF-16 start offset and applies them back-to-front.
   - `OverlappingEditsError`: Raised when two proposed edits intersect.
   - `unified_diff(before: str, after: str, filename: str) -> str`: Produces clean unified diff representation.
2. **AST-Aware Python Import Insertion (`src/apsla/fixes/imports.py`):**
   - `ensure_import_python(source: str, import_stmt: str) -> list[Edit]`: Analyzes AST to insert imports after shebangs, module docstrings, and `from __future__` imports. Merges with existing imports and deduplicates. Returns edits rather than rewriting source.
3. **Fix Registry & Generation Framework (`src/apsla/fixes/registry.py` & `src/apsla/fixes/engine.py`):**
   - `FixContext`: Bundles source, finding, token stream, AST, offset map, and language.
   - `FixGenerator`: Abstract base for rule remediation generators.
   - `FIX_REGISTRY`: Per-rule registry mapping rule IDs to fix generators with deduplicated registration.
   - `generate_fixes(...)`: Generates fixes and attaches stable IDs (`fix-{finding.id}-{idx}`).
4. **Shadow Verification Sandbox (`src/apsla/fixes/verifier.py`):**
   - Sandboxes each proposed fix on an in-memory document copy.
   - Validates parser syntax (`plugin.syntax_check`).
   - Runs shadow re-analysis (`Analyzer.analyze(..., options={"fixes": False, "ml": False})`).
   - Validates `finding_gone` near the original logical line ($\pm 5$ lines).
   - Detects regression (`new_findings` with severity $\ge$ medium not in unpatched code).
   - Time-limited to **2.0 seconds** per fix. Automatic downgrade to `"manual"` and edit purging on verification failure.
5. **Python Fix Generators (`src/apsla/languages/python_lang/fixes.py`):**
   - 16 registered generators for Unicode rules and all Python security rules (`APS-ALL-UNI-001..006`, `APS-PY-INJ-001..004`, `APS-PY-DES-001..002`, `APS-PY-CRY-001..002`, `APS-PY-SEC-001`, `APS-PY-NET-001`, `APS-PY-IO-001`, `APS-PY-XSS-001`).
6. **Multi-Pass Batch Remediation (`engine.fix_all`):**
   - Applies safe + verified fixes iteratively up to 3 passes until convergence.
   - Returns new source, applied IDs, skipped IDs with reasons, diff, and health score before/after.
   - Verified idempotency: `fix_all(fix_all(x)) == fix_all(x)`.

### Phase 4 Implemented Components
1. **Language-Agnostic 45-Dimensional Feature Extractor (`src/apsla/ml/features.py`):**
   - 45 normalized continuous metrics across lexical identities, Unicode flags, Shannon character/n-gram entropy, character ratios, recovery diffs, encoded payloads, dangerous API sinks, syntactic contexts, and local neighborhood densities.
   - Cryptographic schema integrity guarantee: `FEATURE_SCHEMA_HASH: 313113ff1b1c3eaaef410590101e19a00c1721aa822f0c90e1034f7d06cc5b90`.
2. **Context Window Engine (`src/apsla/ml/windows.py`):**
   - Sliding 9-token asymmetric window generator centered at target token with left/right padding.
   - Extracts both $(N, 9, 45)$ 3D sequence arrays and $(N, 405)$ flattened arrays.
3. **Multi-Architecture Model Implementations (`src/apsla/ml/models.py`):**
   - `WindowedBiLSTM`: PyTorch neural sequence model with input projection, layer normalization, 8-dim language embedding, bidirectional LSTM, and center-state MLP classifier.
   - `UnifiedModelWrapper`: Standardized interface spanning `LogisticRegression`, `RandomForestClassifier`, `HistGradientBoostingClassifier`, and `WindowedBiLSTM`.
4. **Synthetic Dataset Generation & Group-Aware Training Pipeline (`src/apsla/ml/synth/` & `src/apsla/ml/train.py`):**
   - Synthetic grammar engine generating diverse Python snippets across 8 template families with ground truth token security labels.
   - Group-aware 70/15/15 partitioning by `(language, template_family, snippet_id)` with zero template leakage.
5. **Probability Calibration & Threshold Tuning (`src/apsla/ml/calibrate.py`):**
   - L-BFGS-B temperature scaling optimization ($T$) on held-out validation cross-entropy.
   - Validation-only grid sweep for optimal malicious decision threshold ($\tau_{\text{malicious}}$).
6. **Feature-Group Occlusion Explainability Engine (`src/apsla/ml/explain.py`):**
   - Evaluates token-level probability drops ($\Delta P$) across 10 functional feature groups.
7. **Runtime Inference Engine with Artifact Caching (`src/apsla/ml/infer.py`):**
   - `MLInferenceEngine`: Zero silent fallbacks (schema hash mismatch or missing weights automatically disables ML to `"off"`).
   - In-memory artifact caching (`_MODEL_CACHE`) eliminating redundant disk loads during rapid analysis calls.
8. **Hybrid Detection Fusion & Ranking Engine (`src/apsla/fusion.py`):**
   - Blended confidence ($0.7 \times \text{rule\_conf} + 0.3 \times ml\_p$), taint confirmation bonus, noisy rule suppression, and false positive feedback suppression integration.

### Phase 5 Implemented Components
1. **Pydantic v2 Server Request/Response Schemas (`src/apsla/server/schemas.py`):**
   - `HealthResponse`: reports service status, version, ML mode, and active model ID.
   - `LanguageInfo`: id, display_name, file extensions, and Monaco language ID.
   - `AnalyzeOptions` & `AnalyzeRequest`: controls fixes, ML, token emission, and suppression inclusion.
   - `FixRequest` & `FixResponse`: single fix application returning new source, unified diff, verification status, and re-analysis.
   - `FixAllRequest` & `FixAllResponse`: multi-pass batch remediation returning applied IDs, skipped reasons, diff, and before/after health score.
   - `FeedbackRequest` & `FeedbackResponse`: false positive feedback recording.
   - `SampleItem`: bundled sample code snippets for IDE initial state.
   - `MLInsightsRequest` & `MLInsightsResponse`: token explainability occlusion metrics.
2. **Interactive Code Samples (`src/apsla/server/samples.py`):**
   - 4 pre-bundled Python samples: `vulnerable_ping.py` (command injection), `trojan_auth.py` (CVE-2021-42574 Trojan Source bidi override), `homoglyph_exec.py` (Cyrillic homoglyph variable shadowing), and `safe_ping.py` (remediated subprocess.run with argument array).
3. **Thread-Safe Pure LRU Cache (`src/apsla/server/cache.py`):**
   - Thread-safe `AnalysisLRUCache` with capacity of 128 items keyed by deterministic SHA-256 digest: `hash(source::language::filename::options)`.
   - O(1) amortized access and automatic cache clearing on feedback submission.
4. **Append-Only False-Positive Feedback Store (`src/apsla/feedback/store.py`):**
   - Thread-safe append-only JSONL storage at `data/feedback/false_positives.jsonl`.
   - Integrated into `fusion.py` suppression loader: suppresses matches by `finding.id`, `finding_fingerprint`, or `(rule_id, line)`.
5. **Deterministic Finding and Fix Identifiers (`src/apsla/rules/base.py` & `src/apsla/rules/generic.py`):**
   - Replaced random UUID generation with deterministic SHA-256 hashes of coordinates and rule ID, ensuring pure reproducible results across identical inputs.
6. **FastAPI Application & REST Routing (`src/apsla/server/app.py`):**
   - Clean `/api` prefixed routes.
   - CORS middleware restricted to `http://localhost:5173` and `http://127.0.0.1:5173`.
   - 512 KB payload size validation returning `HTTP 413 Content Too Large`.
   - 10.0-second async execution timeout returning `HTTP 504 Gateway Timeout`.
   - Global unhandled exception handler logging full tracebacks with an 8-character `error_id` and masking stack traces from HTTP clients.
   - SPA static file serving at `/` with fallback when `web/dist` exists, or informative status JSON in dev mode.
7. **Development Tooling & CLI Integration (`scripts/dev.py` & `src/apsla/cli.py`):**
   - `scripts/dev.py`: Starts Uvicorn on `127.0.0.1:8000` with auto-reload and formatted endpoint banners.
   - `apsla serve [--host 127.0.0.1] [--port 8000] [--reload]`: Starts the API server directly from the CLI.
8. **Comprehensive Integration Test Suite (`tests/unit/test_server_api.py`):**
   - 18 automated tests verifying happy paths, 413 oversized rejection, 400 bad language, 504 timeout, 500 error shielding, CORS headers, fix application, fix-all multi-pass, feedback suppression, and static root fallback.

### Phase 6 Implemented Components
1. **Frontend Architecture & Project Setup (`web/`):**
   - Vite, React 18, TypeScript strict mode with zero external CDN dependencies.
   - SPA compilation to `web/dist/` served directly by the FastAPI backend at `/`.
2. **"SecureLex Night" Design System (`web/src/theme/`):**
   - Pure CSS variables token file (`tokens.css`): `#0B0F17` base, `#111826` panel, `#223049` borders.
   - Custom Monaco Editor dark theme (`monacoTheme.ts`) mapping AST tokens to harmonious syntax highlights.
   - Non-color-redundant severity badges pairing explicit icons (Octagon, Shield, Triangle, Circle) with text labels.
   - Bundled typography via `@fontsource/inter` and `@fontsource/jetbrains-mono`.
3. **Monaco Editor Deep Integration (`web/src/monaco/`):**
   - `markers.ts`: Real-time diagnostic underlines mapping findings to `monaco.editor.IMarkerData` via UTF-16 coordinates.
   - `decorations.ts`: Glyph margin icons and inline highlights for Taint Source (blue), Propagation (amber), Sink (red), and Trojan Source Unicode danger markers.
   - `hover.ts`: Rich hover tooltips providing CWE, severity, plain-English explanations, and confidence metrics.
   - `codeActions.ts`: Quick Fix lightbulb actions (`Ctrl+.`) presenting verified remediations directly in the editor.
4. **Multi-Panel Resizable Workspace (`web/src/components/`):**
   - Dockable layout powered by `react-resizable-panels`:
     - `Sidebar.tsx`: Interactive sample file picker with category badges and custom file switching.
     - `EditorPane.tsx`: Monaco Editor mounting with coordinate tracking (`Ln X, Col Y`).
     - `FindingPanel.tsx`: Detailed vulnerability inspection, CWE reference links, and false-positive reporting.
     - `ProblemsPanel.tsx`: Tabbed bottom drawer hosting Problems list, Taint Flow step tracer, ML Token Insights, and Summary.
     - `TopBar.tsx`: Language selector, Health Score display, Fix-All button, and ML status pill.
     - `StatusBar.tsx`: Editor coordinates, language, encoding, and live analysis elapsed milliseconds.
5. **Interactive Remediation & Explainability:**
   - `DiffView.tsx`: In-memory unified diff preview before applying single or batch patches.
   - `ScoreRing.tsx`: Animated SVG progress ring visualizing Security Health Score ($0 \dots 100$).
   - `TaintPath.tsx`: Step-by-step visual trace navigation with synchronous editor scrolling.
   - `MlInsights.tsx`: Token feature-group occlusion drop inspector for explainable ML.
6. **Live State Management & Concurrency Safety (`web/src/state/`):**
   - Reducer-based global state (`store.ts`) with typed action dispatchers.
   - Trailing-edge 350ms debouncer preventing excessive HTTP traffic during typing.
   - `AbortController` cancellation guaranteeing out-of-order responses never overwrite the active document state.
7. **Production Build & Offline Telemetry (`scripts/build_all.py`):**
   - Validates `npm ci`, runs `npm run build`, and verifies all 177 bundle assets (12.04 MB) including fonts and Monaco web workers.
8. **Frontend Unit Test Suite (`web/src/test/`):**
   - 14 Vitest unit tests verifying offsets, markers, debouncing, edit application, and severity mapping.

---

## 2. How to Run Acceptance Checks

All acceptance checks run within the local environment:

```bash
# 1. Run Python linter and formatter checks (must report 100% clean)
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .

# 2. Run full Python test suite in quiet mode (202 passed)
.\.venv\Scripts\pytest.exe -q

# 3. Run frontend unit test suite (14 passed)
npm.cmd test --prefix web

# 4. Build production frontend bundle and inspect asset sizes
.\.venv\Scripts\python.exe scripts/build_all.py

# 5. Start development server in one terminal
.\.venv\Scripts\python.exe scripts/dev.py

# 6. Probe API health check from another terminal (returns status: ok, version: 0.1.0)
curl.exe -s http://127.0.0.1:8000/api/health

# 7. Run CLI serve command
.\.venv\Scripts\apsla.exe serve --port 8000
```

---

## 3. Public Function Signatures

### `src/apsla/server/schemas.py`
- `class HealthResponse(BaseModel)`: `status: str`, `version: str`, `ml_mode: str`, `ml_model_id: str`
- `class LanguageInfo(BaseModel)`: `id: str`, `display_name: str`, `extensions: list[str]`, `monaco_id: str`
- `class AnalyzeOptions(BaseModel)`: `fixes: bool = True`, `ml: bool = True`, `include_tokens: bool = True`, `include_suppressed: bool = False`
- `class AnalyzeRequest(BaseModel)`: `source: str`, `language: str | None = None`, `filename: str | None = None`, `options: AnalyzeOptions = ...`
- `class FixRequest(BaseModel)`: `source: str`, `language: str = "python"`, `finding_id: str`, `fix_id: str`, `filename: str = "<editor>"`
- `class FixResponse(BaseModel)`: `new_source: str`, `diff: str`, `verification: VerificationResult`, `new_result: AnalysisResult | None = None`
- `class FixAllRequest(BaseModel)`: `source: str`, `language: str = "python"`, `filename: str = "<editor>"`, `allow_review: bool = False`
- `class FixAllResponse(BaseModel)`: `new_source: str`, `applied: list[str]`, `skipped: list[SkippedFixItem]`, `diff: str`, `score_before: int`, `score_after: int`
- `class FeedbackRequest(BaseModel)`: `finding_fingerprint: str`, `rule_id: str`, `language: str`, `verdict: str = "false_positive"`, `snippet: str = ""`
- `class FeedbackResponse(BaseModel)`: `saved: bool = True`
- `class SampleItem(BaseModel)`: `id: str`, `title: str`, `category: str`, `language: str`, `filename: str`, `code: str`, `description: str`
- `class MLInsightsRequest(BaseModel)`: `source: str`, `language: str = "python"`, `token_index: int`
- `class MLInsightsResponse(BaseModel)`: `ml_mode: str`, `token_index: int`, `token_text: str | None`, `predicted_label: str | None`, `probabilities: dict[str, float]`, `feature_group_drops: dict[str, float]`, `error: str | None`

### `src/apsla/server/cache.py`
- `class AnalysisLRUCache`: `__init__(capacity: int = 128)`, `compute_key(source, language, filename, options) -> str`, `get(key: str) -> AnalysisResult | None`, `put(key: str, value: AnalysisResult)`, `clear()`, `size() -> int`
- `ANALYSIS_CACHE: AnalysisLRUCache`

### `src/apsla/feedback/store.py`
- `save_feedback(record: dict[str, Any], filepath: Path | None = None) -> bool`
- `load_all_feedback(filepath: Path | None = None) -> list[dict[str, Any]]`
- `clear_feedback(filepath: Path | None = None) -> None`

### `src/apsla/server/samples.py`
- `get_samples(language: str | None = None) -> list[SampleItem]`

### `src/apsla/server/app.py`
- `app: FastAPI`
- `GET  /api/health -> HealthResponse`
- `GET  /api/languages -> list[LanguageInfo]`
- `GET  /api/samples -> list[SampleItem]`
- `POST /api/analyze -> AnalysisResult`
- `POST /api/fix -> FixResponse`
- `POST /api/fix-all -> FixAllResponse`
- `POST /api/feedback -> FeedbackResponse`
- `POST /api/ml/insights -> MLInsightsResponse`
- `GET  / -> JSONResponse | FileResponse`

### `src/apsla/cli.py`
- `analyze(file: Path, format: str = "text", language: str = "python", ml: bool = True)`
- `fix(file: Path, apply: bool = False, all_safe: bool = False, language: str | None = None)`
- `serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False)`
