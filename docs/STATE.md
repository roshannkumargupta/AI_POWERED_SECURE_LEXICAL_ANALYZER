# Project State & Progress Tracking

**Current Phase:** SL2-10 — Acceptance and handoff (**partial; acceptance gates remain**)  
**Phase Tag:** none  
**Date:** October 12, 2026

The CLEAN-2 section below is the historical baseline recorded before SL2 work. For current v2 status and evidence, use the SL2 phase log at the end of this file and the reports linked there.
## Phase CLEAN-2 Progress (October 10, 2026)
- **Part A (Python Quality & Strict Typing):** Configured strict Ruff (`ruff.toml`) and Mypy (`mypy.ini`, 117 source files fully typed with zero errors). Established domain exceptions hierarchy in `src/apsla/exceptions.py`. Decomposed diagnostic engine by language (`src/apsla/diagnostics/`) and extracted `numeric_lexical.py`. Extracted shared security rule helpers across plugins in `src/apsla/rules/helpers.py`. Added comprehensive docstrings to fix engine and registry classes.
- **Part B (Frontend Architecture & TypeScript Quality):** Configured `strict: true` in `tsconfig.json`, ESLint Flat Config (`eslint.config.js`), and Prettier. Built shared accessible UI primitives (`Badge`, `Button`, `Chip`, `Segmented`, `Switch`, `Select`) in `web/src/components/primitives/`. Extracted pure domain models in `web/src/model/` (`problemsSelection.ts`, `paletteCommands.ts`, `doc.ts`) and custom hooks (`useKeyboardShortcuts.ts`, `useDocuments.ts`, `useAnalysis.ts`, `useFixActions.ts`). Decomposed all monolithic components over 300 lines (`ProblemsPanel`, `FindingPanel`, `Sidebar`, `TopBar`, `App`, `DiffView`, `MlInsights`, `FlyoutPanel`, `AgentTraceTab`, `EditorPane`). Added API contract test (`api-contract.test.ts`) validating against golden OpenAPI schema.
- **Part C (Test Layer & Coverage):** Built `scripts/check_rule_fixtures.py` validating expect schemas and verifying 100% catalog rule fixture coverage (64 tested rules >= 58 catalog rules). Executed 3x flakiness audit across Python (789 tests) and Web (148 tests) with 0 intermittent failures. Python test coverage certified at 87% overall.
- **Part D (Docs, CI Gates & Config):** Authored `docs/README.md` master documentation index and `scripts/check_links.py` (57 doc files, 0 broken links). Built unified CI gate runner `scripts/check_all.py` executing all 11 verification gates. Configured complete `.env.example` with Phase 15 settings and `.pre-commit-config.yaml`.
- **Part E (Hand-off & Verification):** Produced `reports/cleanup/final_report.md`, `reports/cleanup/metrics_after_clean2.json`, and `docs/explained/cleanup.md`. All 11 verification gates passed (0 golden diffs, 0 linter violations, 0 compiler errors, 789 Python tests, 148 Vitest tests, production bundle verified).

## Phase CLEAN-1 Progress (October 10, 2026)
- **Safety Net (Tag clean-0):** Baseline measurements recorded in `reports/cleanup/baseline.md`. Authored `scripts/golden.py` (`--record`, `--check`) recording normalized JSON characterisations of all fixtures, samples, lexical error cases, OpenAPI schemas, CLI `--help` strings, and language registries to `tests/golden/*.json`. Captured UI screenshots at 1536x1022 and 1280x720 in `reports/cleanup/screens_before/`. Computed initial metrics snapshot `reports/cleanup/metrics_before.json`.
- **Repository Inventory & Hygiene:** Generated full repository tree purpose map in `docs/cleanup/inventory.md`. Completed comprehensive `.gitignore` covering Python, Node, Vite, test caches, OS files, and bulky reports while preserving `.md` and `.json` reports. Cleaned ephemeral test artifact outputs in `tests/unit/test_phase10_ml.py`.
- **Registers & Evidence:** Created `docs/cleanup/dead_code_candidates.md`, `docs/cleanup/needs_decision.md`, `docs/cleanup/deleted_files.md`, and `docs/cleanup/skipped.md`. Produced final metrics snapshot `reports/cleanup/metrics_after_clean1.json` and evidence report `reports/cleanup/clean1_evidence.md`.


## Phase 15 Progress (October 10, 2026)
- **Part A (Parser Gap & StructTree):** Hand-written recursive descent parsers with panic-mode error recovery implemented for Java, JavaScript, and C++ (`src/apsla/languages/*/parser.py`), returning typed `StructTree` nodes (`FileNode`, `ClassNode`, `FunctionNode`, `BlockNode`, `StatementNode`, `AssignmentNode`, `CallNode`, `ReturnNode`, `ImportNode`, `ErrorNode`) with UTF-16 coordinates. Replaced bracket-counting in `syntax_check()` with 'no ERROR nodes'. Connected exact call-argument ranges to taint-lite analysis. All 73 parser unit tests and 171 fixture tests pass without regression.
- **Part B (Tool Registry):** Created `src/apsla/agents/tools.py` registering exactly 14 tools (`unicode_scan`, `relex_with_recovery`, `lex_stats`, `detect_language_candidates`, `parse_structure`, `run_rules`, `run_taint`, `ml_score`, `list_fix_candidates`, `apply_fix_to_copy`, `verify_fix`, `rescan_copy`, `build_explanation`, `finish`). Verified with `tests/security/test_agent_tools_allowlist.py` that none of the tools import `subprocess`, `os.system`, `socket`, or `requests`.
- **Part C (Local Model Provider):** Built `src/apsla/llm/local_ollama.py` with strict loopback validation (`127.0.0.1`, `localhost`, `::1`), raising fatal errors on non-loopback hosts. 20s timeout, single retry on invalid JSON, zero network downloads, `GET /api/agent/status` endpoint.
- **Part D (The Agents & Orchestrator):** Implemented 7 compiler-stage agents (`LexerAgent`, `ParserAgent`, `SemanticAgent`, `TriageAgent`, `FixAgent`, `VerifierAgent`, `ExplainAgent`) plus `AgentOrchestrator` under `src/apsla/agents/`. Built `RulesPlanner` (deterministic baseline) and `LLMPlanner` (local model). Verified all 4 invariants: (a) findings superset-or-equal, (b) mode 'off' byte-identical to Phase 14, (c) rules planner deterministic, (d) garbage LLM fallback.
- **Part E (Prompt-Injection Defense):** Hardened `src/apsla/agents/guard.py` restricting prompts to structured facts and 5-line bounded snippets (200 chars/line max, BiDi/control chars escaped to `<U+XXXX>`) wrapped in untrusted data markers. Strict schema and action validation; reason string length-capped at 160 characters. Verified via `tests/security/test_agent_injection.py`.
- **Part F (API, Trace, UI):** Added agent mode support to `POST /api/analyze` and new `POST /api/agent/analyze`. Built 3-state TopBar toggle (Off / Rules / Local AI), StatusBar pill, and vertical timeline tab `AgentTraceTab.tsx` with Bot/Cpu/Workflow icons, AI/Rule decided badges, accepted/rejected states, execution timing, and plain-text XSS-safe rendering. All 133 Vitest tests pass; bundle builds cleanly.
- **Part G (Evaluation & Docs):** Built `scripts/agent_eval.py` (`--help`), evaluated across all 241 fixtures in `off` and `rules` modes (real numbers only: 100% recall maintained, 87 verified fixes), created `docs/agentic_map.md`, `docs/threat_model.md`, `docs/limitations.md`, `reports/phase_15_evidence.md`, and `docs/explained/phase15.md` with 5 viva Q&As.

## Phase 12 Progress (October 10, 2026)
- **Feedback Loop & Active Learning:** Implemented append-only feedback storage in `src/apsla/feedback/store.py` recording `{timestamp, language, rule_id, fingerprint, snippet (max 400 chars), verdict, note}` to git-ignored `data/feedback/false_positives.jsonl`. Added `scripts/retrain_with_feedback.py` (`--help`), extracting hard-negative SAFE-labelled training windows exclusively into TRAIN partitions (never val/test). Added automated safety gate that evaluates held-out validation and external benchmarks (`evaluate_external_benchmarks`), refusing to overwrite model artifacts if external metrics regress. Full evidence recorded in `reports/phase_12_evidence.md`.
- **Multi-Factor Risk Prioritization:** Defined exploitability constants in `src/apsla/config.py` ($1.0$ taint confirmed, $0.7$ dangerous sink without taint path, $0.5$ weak-crypto/config, $0.3$ info). Computed $Priority = Severity \times Confidence \times Exploitability$ in `src/apsla/prioritization.py`. Wired into pipeline and UI Problems panel with descending risk sorting and `⚡ Fix first` badge on top 3 findings.
- **Plain-English Explanations & Rules Catalogue:** Structured explanation templates in `src/apsla/rules/explanations.py` answering *What*, *Why it is dangerous*, *How an attacker uses it*, and *How to fix*. Interpolated concrete variable and line numbers into findings. Added Simple (1-sentence) and Detailed (full structured) toggle in Finding tab. Auto-generated complete catalogue in `docs/rules_catalogue.md`.
- **Inline Suppression Comments:** Added support for `# securelex: ignore <RULE_ID>` (Python) and `// securelex: ignore <RULE_ID>` (Java, JS, C++) on the same or immediately preceding line in `src/apsla/suppression.py`. Added one-click UI action and Monaco QuickFix code action inserting undoable workspace edits.
- **Guarded, Shadow-Verified LLM Assistant:** Implemented abstract provider in `src/apsla/llm/provider.py`, `NullLLMProvider` in `src/apsla/llm/null.py` (default, completely offline), and concrete providers for Anthropic, Gemini, and OpenAI-compatible endpoints using `httpx`. Configured strictly through `.env` with 200-line context window slicing and 15s timeouts. All LLM fixes pass through `verify_fix()` shadow verification; unverified fixes are downgraded to non-executable manual advice. Added disabled UI button with tooltip when unconfigured, and privacy disclosure in `README.md`.
- **Keyboard Shortcuts & Memory State:** Added Keyboard Shortcuts cheat-sheet dialog (press `?` to trigger). Persisted Simple/Detailed explanation mode and panel sizes strictly in memory without `localStorage`.
- **Evidence & Verification:** Captured UI screenshots in `docs/screenshots/phase12/` (`problems_fix_first.png`, `finding_tab_ai_disabled.png`, `suppress_comment_action.png`, `shortcuts_modal.png`). Written comprehensive scientific guide in `docs/explained/phase12.md` with 5 viva Q&As.

## UI-8 Progress (October 9, 2026)
- Added matched dark/light semantic token sets in `web/src/theme/tokens.css` with WCAG AA compliant contrast ratios (>= 4.5:1 text/severity, >= 3:1 controls/focus).
- Added persisted Dark/Light/System theme mode (`localStorage` with in-memory fallback), system preference listener, and pre-paint head script in `web/public/theme-init.js` ensuring zero flash of wrong theme.
- Added toolbar sun/moon toggle button with polite aria-live announcements, Help appearance radio group, and command-palette theme commands (`Theme: Dark`, `Theme: Light`, `Theme: System`, `Toggle theme`).
- Implemented dynamic Monaco theme builder `buildMonacoTheme` in `web/src/theme/monacoTheme.ts` deriving editor colors directly from CSS tokens while preserving editor model, cursor, scroll, and undo history.
- Resolved PART G defects: corrected high/critical DOM XSS grouping to "Dangerous" (G1), eliminated token table sticky header row overlap (G2), restricted insecure token highlighting strictly to anchor lexemes (G3), and aligned status bar pills and Ready telemetry (G4).
- Automated verification: Vitest suite (17 files, 118 tests) and production bundle build passed; ruff check passed; documentation recorded in `reports/ui8_evidence.md`, `docs/explained/ui8.md`, and `docs/user_guide.md`.

## UI-3 Progress (October 2, 2026)
- Audited the full Python and Java analyze samples: token fields are `token`, `token_type`, `range`, `label`, and `score`; no per-token recovered text, script metadata, or probability vector is returned. Documented the audit and representative JavaScript/C++ lexer kinds in `docs/token_security_data.md`.
- Added memoized pure token derivation, a Tokens inspector tab with security/type/search/category filters, bounded virtual rows, exact-range selection, related finding links, unicode evidence/recovery display when supplied, on-demand ML, and visible rendering for control/format characters.
- Added Monaco cursor/token synchronization, category-aware token map decorations, Security/Full modes, palette entries, and Ctrl+Shift+T.
- Added derivation and panel tests including real Python/Java response samples, safe-neutral behavior, XSS-safe text rendering, ML-off, empty state, virtual row count, and a 5,000-token timing check (11.63 ms in the measured run).
- Browser walk-through confirmed Python Flask command injection, Trojan Source, confusable `еxec` (Original `еxec`, Recovered `exec`, U+0435 Cyrillic evidence), Java SQL injection, JavaScript DOM XSS, and C/C++ buffer overflow views.
- Verification: frontend suite and production build status are recorded in `reports/ui3_evidence.md`.

---

## UI-1 Progress (October 2, 2026)
- Audited the live frontend and recorded root causes in `docs/ui_bug_audit.md`; existing baseline captures remain in `docs/screenshots/before_ui1/`.
- Added `web/src/state/workspace.ts`: plain file workspace reducer, editable sample-copy semantics, dirty tracking, stale result version gate, language guesser, and sample filter.
- Added Vitest coverage in `web/src/test/workspace.test.ts` (4 tests).
- Changed startup state to empty with Auto-detect; updated the welcome panel and added an Explorer rail, language filtering/search with four collapsed language groups and Show all, and New/Open file actions.
- Added Ctrl+B, Ctrl+N, Ctrl+O, Ctrl+S, beforeunload warning, and a 512 KB file limit.
- No backend code changed in this UI-1 pass. A direct Uvicorn run on the configured Vite proxy port 8001 worked; fresh endpoint captures now show 4 languages and 17 samples. Vulnerable Python and Java sample analyses returned 2 and 11 findings.
- Verification: `npm.cmd run build` succeeded; `npm.cmd test` passed (20 tests). Final TypeScript typecheck passed. `ruff check .` passed. `ruff format --check .` reported 3 unformatted files under `scratch/`. Full pytest completed with one failure, `tests/unit/test_cpp_syntax.py::test_balanced_preprocessor_conditionals` (outside UI-1). Live browser confirmed empty startup, Auto-detect, Java sample editing and analysis, language grouping/show all, new-buffer typing, and Ctrl+B close/reopen. Ctrl+Z did not visibly undo one sample edit. Quick fixes, Fix all, folder/drag-drop, redo, recovery, and full acceptance remain outstanding. `docs/screenshots/after_ui1/` currently has no evidence captures.

## S-1 Progress (October 2, 2026)
- Added a Pydantic v2 sample schema, cached `importlib.resources` loader, deterministic Python sample builder, and package-data declaration.
- Added 41 manifest entries with 40 shipped samples and one pending engine-gap sample. The manifest meets all 41 quotas; shipped counts are 10 basic, 9 intermediate, 7 advanced, 7 safe, 6 Unicode, and 1 lexer. Pending `py-a01` accounts for the one-sample advanced shortfall (see matrix).
- Kept the previous 17 sample records and all legacy API fields. `/api/samples` adds metadata and `meta=1`; `/api/samples/{id}` serves catalogue and legacy IDs.
- `scripts/verify_samples.py` runs Analyzer with fixes enabled, both ML modes when an artifact is available, checks findings, paths, clean samples and verified fixes, and generates the catalogue guide and evidence matrix.
- `py-a01` is pending because current Python taint analysis does not propagate request-derived values through a helper function parameter into `os.system`; no finding or fix is generated. It is excluded from the samples API and recorded in the matrix.
- Acceptance: `ruff check .` passed; the S-1 test module passed all 3 tests; `python scripts/build_samples.py` and `python scripts/verify_samples.py` completed, with 40 shipped samples passing and one pending. Full `pytest -q` did not pass in this worktree: 17 failures and 20 setup errors were reported, including Windows access denied for temporary paths and named pipes, plus failures in existing JavaScript, C++, Unicode-pipeline, and ML-training tests.
- How to add a sample: (1) add its entry in `scripts/build_samples.py`; (2) set expected rule IDs and source lines from current engine behavior; (3) generate with `python scripts/build_samples.py`; (4) run `python scripts/verify_samples.py` and address failures or mark a real engine gap pending; (5) review `docs/samples_guide.md` and `reports/phase_s1_evidence.md`.
- Sample gaps: `py-a01` (helper-function taint summary unavailable). See `reports/samples_matrix.md` for actual results and fix confidence details.

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
- `data/external/java/`: 42 realistic, hand-written unseen external test snippets with ground truth security labels (Spring servlets, ProcessBuilder, JPA, crypto).
- `data/external/javascript/`: 42 realistic, hand-written unseen external test snippets with ground truth security labels (Express routes, child_process, DOM XSS, prototype pollution).
- `data/external/cpp/`: 42 realistic, hand-written unseen external test snippets with ground truth security labels (POSIX network daemons, strcpy/sprintf buffer manipulations, system wrappers).
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
- `docs/explained/phase8.md`: Educational documentation for Phase 8 (regex vs division disambiguation, recursive template literals, DOM XSS, prototype pollution, 5 viva Q&As).
- `docs/explained/phase9.md`: Educational documentation for Phase 9 (lexer-level C/C++, preprocessor directive tokens, buffer overflows, format string vulnerabilities, 5 viva Q&As).
- `docs/explained/phase10.md`: Educational documentation for Phase 10 (transfer learning, joint vs separate models, why cross-language results drop, 5 viva Q&As).
- `reports/phase_5_evidence.md`: Evidence report for Phase 5 REST API and caching.
- `reports/phase_6_evidence.md`: Evidence report for Phase 6 IDE web app and bundle telemetry.
- `reports/phase_8_evidence.md`: Evidence report for Phase 8 JavaScript plugin and telemetry.
- `reports/phase_9_evidence.md`: Evidence report for Phase 9 C/C++ plugin and telemetry.
- `reports/phase_10_evidence.md`: Evidence report for Phase 10 multi-language ML and honest limitations.
- `reports/metrics_phase10.json`: Complete empirical metrics, confusion matrices, external benchmark scores, cross-language transfer table, and feature group/language-ID ablations.
- `docs/screenshots/`: Visual UI evidence (`empty_state.png`, `taint_path.png`, `trojan_source.png`, `fix_all_remediation.png`, `summary_tab.png`, `dom_xss_taint.png`).
- `src/apsla/ml/synth/`: Template generators for Python (`python.py`), Java (`java.py`), JavaScript (`javascript.py`), and C/C++ (`cpp.py`) with 3,000+ snippets each and per-token ground truth.
- `src/apsla/ml/artifacts/`: Multi-language and joint model artifacts (`joint_windowed_bilstm_*`, `separate_python_*`, `separate_java_*`, `separate_javascript_*`, `separate_cpp_*`) with verified feature schema hashes.
- `tests/unit/test_phase10_ml.py`: 7 tests verifying multi-language synthetic generators, zero leakage group splits, schema hash checks, fake artifact fallback to ML off, and fast CI training under 3 minutes.

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
   - `scripts/dev.py`: Starts Uvicorn on `127.0.0.1:8010` (override with `APSLA_API_PORT`) and prints endpoint banners. It adds `src/` to the import path and avoids the Windows reload child-process failure.
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

### Phase 7 Implemented Java Plugin Components
- Modular Java plugin: `JavaLexer`, `JAVA_TAINT_PROFILE`, 17 deterministic Java security rules, verified fix generators, and import injection.

### Phase 8 Implemented JavaScript Plugin Components (`src/apsla/languages/javascript_lang/`)
1. **Resilient JavaScript Lexer (`lexer.py`):**
   - Hand-written, zero-crash state machine with lossless source reconstruction (`"".join(t.text for t in tokens) == source`).
   - ES2024 keywords and contextual keywords (`async`, `await`, `of`, `get`, `set`, `static`, `let`).
   - Hex, octal, binary, BigInt (`10n`), and numeric separators (`1_000`).
   - Modal template literal state machine (`_MODE_TEMPLATE`, `_MODE_TEMPLATE_EXPR`) supporting arbitrary recursive nesting of `${ ... }`.
   - Context-sensitive lookback disambiguation of `/` for regular expression literals vs. division operators.
   - Private field identifiers (`#field`) and JSX tolerance without error tokens.
2. **JavaScript Taint Profile (`profile.py` & `src/apsla/taint/lite.py`):**
   - Sources: Express (`req.query`, `req.params`, `req.body`, `req.headers`, `req.cookies`), browser navigation (`location.search`, `location.hash`, `location.href`, `document.URL`, `document.referrer`, `document.cookie`, `window.name`), `URLSearchParams`, `process.argv`, `process.env`.
   - Sinks: `eval`, `new Function`, `setTimeout`/`setInterval` strings, `child_process.exec`, `innerHTML`, `outerHTML`, `document.write`, `dangerouslySetInnerHTML`, `location = tainted`, SQL queries, `fs.readFile`, `axios`/`fetch` SSRF, `Math.random`, `createHash("md5"/"sha1")`, hard-coded secrets, `jwt.verify` algorithm none, `Object.assign` prototype pollution, dynamic `RegExp` ReDoS.
   - Sanitizers: `DOMPurify.sanitize`, `encodeURIComponent`, `escape-html`, `textContent`, `parseInt`, `path.basename`.
3. **Deterministic JavaScript Security Rules (`rules.py`):**
   - 16 rules: `APS-JS-INJ-001` through `005`, `APS-JS-XSS-001` through `002`, `APS-JS-NET-001` through `003`, `APS-JS-IO-001`, `APS-JS-CRY-001` through `002`, `APS-JS-SEC-001` through `002`, and `APS-JS-OBF-001`.
4. **Verified Remediation & Imports (`fixes.py` & `src/apsla/fixes/imports.py`):**
   - Verified automated fixes for innerHTML, dangerouslySetInnerHTML, eval, exec, SQL injection, Math.random, weak hash, hard-coded secret, and TLS verification.
   - `ensure_import_javascript`: Automatically detects CommonJS (`require`) vs. ESM (`import`), inserting after shebangs and `"use strict"` directives without duplicate imports.
5. **Fixtures & Visual Evidence:**
   - 61 test fixtures (28 vulnerable, 25 safe, 8 adversarial) in `tests/fixtures/javascript/`.
   - Verified DOM XSS taint data-flow UI screenshot in `docs/screenshots/dom_xss_taint.png`.

### Phase 9 Implemented C/C++ Plugin Components (`src/apsla/languages/cpp_lang/`)
1. **Resilient C/C++ Lexer (`lexer.py`):**
   - Hand-written, zero-crash state machine that elegantly parses C/C++ without a full preprocessor evaluation.
   - Treats preprocessor directives (`#include`, `#define`) as single tokens, properly interpreting backslash line continuations and protecting `<` and `>` characters within header names.
   - Lossless support for C/C++20 keywords, numbers (binary, hex, digit separators `1'000`, floats), and all C++ operators (`<=>`, `->*`).
   - Parses C++11 raw string literals (`R"delim(...)delim"`) properly capturing internal whitespace and escapes.
   - Avoids template parsing, treating `<` and `>` as separate tokens, keeping lexing decoupled from deep semantic analysis.
2. **C/C++ Taint Profile (`profile.py` & `src/apsla/taint/lite.py`):**
   - Sources: `argv`, `getenv`, `recv`, `fread`, `read`, `scanf`, `fscanf`, `sscanf`, `gets`.
   - Sinks: `strcpy`, `strcat`, `sprintf`, `vsprintf`, `printf`, `syslog`, `system`, `popen`, `malloc`, `fopen`.
   - Sanitizers: Safe wrapper functions or size verifications.
3. **Deterministic C/C++ Security Rules (`rules.py`):**
   - 12 rules targeting critical memory safety and injection flaws: `APS-CP-MEM-001` through `007`, `APS-CP-INJ-001`, `APS-CP-IO-001`, `APS-CP-IO-002`, `APS-CP-SEC-001`, `APS-CP-CRY-001`.
4. **Verified Remediation & Imports (`fixes.py` & `src/apsla/fixes/imports.py`):**
   - Automated verified patches for `strcpy` $\to$ `snprintf`, `sprintf` $\to$ `snprintf`, `tmpnam` $\to$ `mkstemp`, `gets` $\to$ `fgets`.
   - `ensure_import_cpp`: Language-variant aware header injection (distinguishing `<cstdio>` for C++ from `<stdio.h>` for C).
5. **Fixtures & Visual Evidence:**
   - 54 test fixtures (23 vulnerable, 22 safe, 9 adversarial) in `tests/fixtures/cpp/`.

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
curl.exe -s http://127.0.0.1:8010/api/health

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
# UI-2 progress (2026-10-02)

- Added SecureLex UI design rules and UI-2 progressive-disclosure/viva notes.
- Reduced the top bar to a 44 px strip, exposed current filename and language, and made Fix all depend on safe verified fixes.
- Set Monaco minimap and bracket pair colourization off by default; editor surface uses the distinct `#0D121C` token.
- Added best-effort source symbol breadcrumbs and CWE-based finding categories. Problems supports severity/location/confidence sorting and category grouping.
- Added utility and component coverage for breadcrumbs, CWE mapping, Problems controls, Finding states, command palette, and Fix all button states.
- Browser walked Python, Java, JavaScript, and C/C++ samples through finding, taint flow, diff, apply, and undo. Verified Java fix-all availability is correctly disabled because the sample exposes no safe verified fix candidates.
- The browser screenshot API displayed before/after review images but offers no workspace file-save method in this environment. `before_ui2/` and `after_ui2/` exist but do not contain screenshots; durable capture remains open.
- The browser Fix All action could not be exercised on sample data because the available remediations are marked review-needed; the empty and enabled states are covered in component tests.
- Final UI test/build check: `npm run test` passed 79 tests in 9 files; `npm run build` passed with a Vite large-bundle advisory for Monaco.

# S-2 Java and JavaScript sample catalogue (2026-10-02)

- Added 35 Java and 34 JavaScript metadata-backed samples using the S-1 manifest/schema/loader and shared verification harness. Existing 41 Python rows remain present.
- Java sources use package/import/class/method structure; JavaScript samples cover Node.js and browser patterns. Added safe, Unicode, and lexer showcase examples, plus two six-flaw advanced demo sources; Java remains pending because the analyzer misses its reflected-XSS issue, while JavaScript verifies all six rules.
- `scripts/build_samples.py` now builds Python, Java, and JavaScript sources and preserves pending locations/reasons. `scripts/sample_catalogue_s2.py` stores the S-2 source catalogue.
- Live analyzer verification: 104 shipped samples passed (40 Python, 32 Java, 32 JavaScript); 6 remain pending (the S-1 Python gap and five S-2 analyzer gaps). Java and JavaScript manifest quotas are met, with shipped shortfalls listed in `reports/phase_s2_evidence.md`.
- Pending S-2 sources are stored under `src/apsla/samples/pending/`. Reasons document the missing Java reflected-XSS detection, five-of-six Java advanced result, Java Unicode rule-ID mismatch, constant-string JavaScript timer coverage, and missing taint propagation through a JavaScript helper.
- `JOBLIB_MULTIPROCESSING=0` is needed for ML-on verification in this Windows environment: sklearn's parallel prediction otherwise raises `WinError 5` while creating a multiprocessing pipe. The analyzer and model code were not changed.
- `ruff check .` passes. The S-2 catalogue end-to-end tests pass (3 tests). API metadata probes returned 200 for Java and JavaScript, grouped by language with 36 rows per response (32 shipped catalogue samples plus 4 legacy records).
- Full `pytest -q` was not clean: 1 pre-existing failure in `tests/unit/test_cpp_syntax.py::test_balanced_preprocessor_conditionals` and 20 setup errors from Windows `WinError 5` while pytest scans/cleans its temp directory. A workspace-local `--basetemp` retry still showed the C++ failure and Windows permission errors. S-2 catalogue e2e passed independently.

# S-3 C/C++ samples, comparison and demo path (2026-10-02)

- Added 34 metadata-backed C/C++ samples, bringing the manifest to 144 records; 30 C/C++ entries pass the live verifier and four are pending with measured analyzer gaps.
- Added a senior comparison script and optional senior API metadata, sample grouping/search helpers, Demo notes, a 13-step demo path, and sample catalogue learning notes.
- Project A comparison disables its absent ML model. Project B runs its regex hotspot stage; JavaScript/C++ rows identify that the Java scanner is not designed for those languages.
- The senior comparison completed for all 144 manifest samples, including pending examples; generated counts appear in `reports/samples_senior_vs_ours.md`.
- Final verification: 134 shipped samples pass the analyzer matrix; 10 remain pending with reasons. `ruff check .` passes. The S-3 Vitest file passes (4/4), and the full web suite reported 91/92 because the existing 5,000-token performance check exceeded its 50 ms threshold under load; an earlier full run passed 92/92. `npm run build` succeeds with Vite's existing Monaco chunk-size advisory.
- Full `pytest -q` did not complete in this environment (quiet run stalled without output; prior S-2 run recorded one C++ conditional test failure and Windows temporary-directory permission errors). The browser walkthrough/screenshots remain unavailable because local port 8000 connections are rejected; see `docs/screenshots/samples/README.md`.

# Runtime repair and final verification (2026-10-03)

- Fixed the Vite `/api` proxy to use the same configurable backend port as `scripts/dev.py` (`APSLA_API_PORT`, default `8010` on this host). The development runner now adds `src/` to Python's import path and disables the Windows reload subprocess that failed to start reliably.
- The API-backed catalogue now loads 151 samples across four languages (including the four retained legacy Python examples) instead of falling back to only four bundled Python samples.
- Fixed C++ syntax validation to avoid treating balanced `#if`/`#ifdef`/`#ifndef` source as a tree-sitter parse error; compiler validation still runs when available. Updated the C++ API test to expect the expanded catalogue.
- Updated the catalogue integration assertions from the old 110-entry phase total to the current 144-entry manifest.
- Verification: `npm.cmd test` passes (92 tests); `npm.cmd run build` succeeds; full `.venv` Python suite passes when run outside the Windows sandbox with `--basetemp=reports/.pytest-tmp`; the catalogue end-to-end suite passes (3 tests); FastAPI API tests pass (18 tests); browser analysis returns a critical CWE-78 finding and ML detection with the ML model active.
- Live endpoints: Vite `http://127.0.0.1:5173/`; API `http://127.0.0.1:8010/api`. `GET /api/health` reports `ok` and ML `on`.

# UI-5 inspection shell and additive diagnostics (2026-10-03)

- Replaced the permanent sidebar and bottom Problems drawer with a 34 px icon strip/flyout, resizable editor and analysis panes, explanation area, severity filter frame, and compact status bar. Removed the editor breadcrumb row and minimap option; set the Monaco theme to `securelex-dark` with minimal syntax coloring and 13 px / 24 px code metrics.
- Added the four right-pane views: Tokens, Taint path, ML insights, and Summary. Token table rows now use `web/src/model/adapt.ts`, merge dotted/namespace call names, preserve raw token identifiers, distinguish primary finding ranges from taint sources, and render invisible controls as `<U+XXXX>` text.
- Added backward-compatible `Finding.kind`, lexical/syntax summary counts, sparse `Finding.attack` tags, fusion confidence breakdowns, and parser metadata. Lexical and syntax diagnostics do not affect the security health score. Added detection for unterminated strings that the Python lexer currently emits as `STRING`, without altering its recovery behavior.
- Added UI-5 security and malformed-string Python demos through `scripts/build_samples.py`; the catalogue now has 146 rows (43 Python). Saved analyzer response payloads for Python, Java, JavaScript, and C in `docs/api_samples/`.
- Added implementation map, viva explanation, and evidence report. The malformed Python demo produces lexical and syntax findings but loses the earlier taint path because `ast.parse` fails; the closing-quote fix is sent through the verifier, which refuses it as an automatic review fix when the corrected source exposes command injection.
- Verification: `npm run test` passed (105 tests); `npm run build` passed with the existing Monaco chunk-size warning; sample builder passed; full `.venv` pytest passed outside the Windows sandbox; ten focused UI-5 backend tests passed; `ruff check .` passed. Visual comparison and screenshot acceptance are blocked by missing `docs/ui_reference/` files, unavailable browser-control runtime, and missing Playwright package. The already-running local API still served its pre-UI-5 schema; the current endpoint schema passed the in-process API round-trip test.

# UI-6 file workspace and token review (2026-10-03)

- Added separate Files, Samples, and Help flyouts; editable sample documents; multi-file tabs and switch/close controls; folder import limited to 200 supported files; unsaved markers; and the keyboard help/reference panel. Flyouts open beside the icon strip so the strip remains clickable while a panel is open.
- Added a real, virtualized token table with stable columns, problem-first defaults, show-all, single-choice All/Security/Lexical/Syntax filtering, multi-choice Dangerous/Suspicious/Malicious filtering, lexical details, literal API text, and synchronized editor selection. Filters live in the bottom bar and update the Tokens view.
- Added a detailed explanation panel, ML probability/feature output when supplied, parser/engine labels, and verified fix application through `/api/fix` and `/api/fix-all`. Security/lexical sample walkthrough confirmed findings, taint steps, ML probabilities, fix-all application, and Monaco undo.
- Added UI-6 component and token-table coverage, the viva guide, user-guide section, demo-script walkthrough, and browser screenshots in `docs/screenshots/after_ui6/`.
- Verification: `npm.cmd test` passed (109 tests); `npm.cmd run build` passed with the existing Monaco chunk-size advisory; `ruff check .` passed. The plain system `pytest -q` invocation could not import `apsla`; a `.venv` invocation with `PYTHONPATH=src` and workspace `--basetemp` was started but stalled without output in this Windows sandbox. The named UI reference mockup and target image are absent from `docs/ui_reference/`, so no measured visual comparison or `compare.png` is claimed. See `reports/ui6_evidence.md` for browser checks and exact limits.

# UI-7 contrast, scrolling, and scale pass (2026-10-03)

- Added a dark native-control scheme, inherited control foregrounds, explicit select/option/placeholder/disabled/focus colors, dark thin scrollbars, and safer contrast for primary action labels. Replaced hard-coded pure-black overlay/shadow colors outside Monaco's intentional transparent-theme exception.
- Fixed flex sizing for the editor body when multi-file tabs are present. Before, `.ui5-editor > :first-child` made the new tab strip the flexible item; browser measurement showed its height collapsing. The editor body now owns remaining height and file tabs stay at their fixed height.
- Set panel wrappers to `min-width:0; min-height:0`, kept scroll ownership in inner regions, and constrained the narrow stacked panel wrapper to the sub-768 px breakpoint. Added overscroll containment to scroll areas.
- Added a reference-frame scale from the 768×480 design and a Help → Interface size Compact/Reference/Large preference, persisted in a guarded localStorage call. Root-frame transform scales existing fixed-unit component styles; the app has not yet migrated every dimension to rem. Monaco remains 12 px base with automatic layout. Added scale and contrast/black-color guard tests.
- Installed browser diagnostics and prompt-derived metric reader; added data-qa hooks to the top bar, controls, strip, code pane, file tabs, legend, analysis pane/tabs, token table, explanation, filter row, and status. Diagnostic background calculation now composites translucent colors and excludes intentional 1 px hidden controls.
- Saved updated empty, Security (four views), Samples flyout, lexical demo, and 300-line diagnostics/screenshots at 1280×720, 1366×768, 1536×864, 1536×1022, and 1920×1080 under `reports/ui7/after/` and `docs/screenshots/ui7/`. Diagnostics for these captured states have zero color/control/clipping/page-scroll findings after the final scale correction.
- Verification: `npm.cmd test` passed (113 tests); `npm.cmd run build` succeeded (existing Monaco bundle-size advisory); `ruff check .` passed; `PYTHONPATH=src .venv/Scripts/python -m pytest -q --basetemp=reports/.pytest-ui7` passed; `python scripts/verify_samples.py` exited 0 (136 shipped/passed, 10 pending, 0 failures; system Python emitted model-version/ML-off warnings).
- Remaining UI-7 acceptance work is explicit: no target image or `ref_metrics.json` exists (only `docs/ui_reference/README.md`), so target pixel-diff and accurate expected-metrics comparison cannot be claimed; Apply-fix diff and complete D1–D16 manual E2E matrix were not verified; Playwright is unavailable. See `reports/ui7_evidence.md`, `reports/ui7/matrix_after.md`, and `docs/ui7_root_causes.md` for exact evidence and limitations.

# UI-9 editor stability, manual analysis, review fixes, and full E2E verification (2026-10-09)

- Resolved all four user-reported defects (D1, D2, D3, D4) at their true root causes:
  - **D1 (Cannot Edit Sample)**: Removed `onMouseDown` token selection interceptor and forced `editor.setSelection` effect in `EditorPane.tsx`. Monaco operates as an uncontrolled editable model with 0 cursor jump anomalies.
  - **D2 (Apply Fix Missing / Unclickable)**: Fixed conditional rendering in `ExplanationPanel.tsx` and `FindingPanel.tsx` to enable `[Apply fix]` for review-level fixes (where the diff is the review) and rendered clear "No automatic fix" advice blocks with `[Copy advice]` buttons for rules without automated edits.
  - **D3 (Automatic Analysis & Cursor Jumps)**: Removed 600ms automatic debounced analysis effect from `App.tsx`. Analysis is manual-only via Analyze button or `Ctrl+Enter`. Implemented 5-state document lifecycle (`not analysed`, `analysing`, `analysed`, `stale`, `error`). In stale state, results are marked out of date and Apply fix is disabled until re-analyzed.
  - **D4 (End-to-End System Audit)**: Hardened file decoding in `fileLoader.ts` (512 KB limit, binary NUL refusal, UTF-8 BOM stripping, invalid UTF-8 replacement chars with warning, CRLF preservation), isolated editor navigation commands in `navigation.ts`, added Review Fixes modal (`ReviewFixesModal.tsx`), and verified truthful ML status.
- Added test harness `window.__slTest` in `testHarness.ts` with cursor logging (`onDidChangeCursorPosition`), request logging (`requestLog`), and state getters. Proved `window.__slTest` is completely absent from production bundle (`dist/`).
- Conducted full fix coverage audit across all 136 catalogue entries (`reports/ui9/fix_coverage.md`).
- Generated 17 edge-case fixtures via `scripts/e2e_data.py` in `web/e2e/fixtures/`.
- Automated CDP feature matrix runner (`scripts/cdp_matrix_runner.mjs`) ran live against Chromium on port 9222:
  - Tested 13 samples across Python, Java, JavaScript, C++: 100% PASS, 0 cursor anomalies, 0 unexpected analyze requests.
  - Captured all 14 required screenshots at 1536x1022 across Dark and Light themes into `docs/screenshots/ui9/`.
  - Diagnostics verified PASS across all 5 viewports (1280x720, 1366x768, 1536x864, 1536x1022, 1920x1080) in both themes with 0 contrast errors.
  - Reference metrics verified PASS within 1.2% (tolerance <= 6%).
- Full verification:
  - `npm.cmd test`: All 18 test files (130 tests) passed cleanly.
  - `npm.cmd run build`: Production bundle built cleanly; `window.__slTest` strictly absent.
  - `.\.venv\Scripts\ruff.exe check .`: All checks passed cleanly (0 errors).
  - `.\.venv\Scripts\pytest.exe -q`: 100% of all tests passed cleanly (470+ tests).
  - `npm.cmd run qa:full`: Complete E2E pipeline passed.


## SL2-0 through SL2-10 v2 status (2026-10-12)

This log preserves the pre-SL2 history above. Detailed evidence is in the linked per-phase reports and explained notes.

| Phase | Status | Evidence |
|---|---|---|
| SL2-0 Audit, decisions and plan | Complete | `docs/sl2_environment.md`, `docs/sl2_inventory.md`, `docs/sl2_gap_analysis.md`, `docs/sl2_prototype_audit.md`, `docs/sl2_decisions.md`, `docs/sl2_rules.md`, `docs/sl2_plan.md` |
| SL2-1 Models, adapters, tool runner and API v2 | Partial | `reports/sl2_1_evidence.md`; schema/API docs exist; see actual test outcomes there |
| SL2-2 Lexer/token contract | Partial | `reports/sl2_2_evidence.md`, `docs/lexer_conformance.md`, `docs/token_types.md`; conformance scope and tests remain bounded by the recorded results |
| SL2-3 Parsing and syntax/semantic diagnostics | Partial | `reports/sl2_3_evidence.md`; optional compiler/tool availability limits semantic checks |
| SL2-4 Security adapters, rules and quality | Partial | `reports/sl2_4_evidence.md`, `docs/rules_catalogue.md`; optional external tools are host-dependent |
| SL2-5 Providers and agent gateway | Partial | `reports/sl2_5_evidence.md`; no live model acceptance on this host |
| SL2-6 Fix proposal and independent verification | Partial | `reports/sl2_6_evidence.md`; browser flow and optional verification checks depend on host capabilities |
| SL2-7 Safety Lab and exports | Partial | `reports/sl2_7_evidence.md`; deterministic harness results are distinct from live-model runs |
| SL2-8b API-wired product workspace | Partial | `reports/sl2_8b_evidence.md`; component tests/build passed historically, browser golden path/screenshots are blocked |
| SL2-9 Application hardening | Partial | `reports/sl2_9_evidence.md`; memory isolation, chunked request cap and browser session isolation remain gaps |
| SL2-10 Acceptance and handoff | Partial | `reports/sl2_final_acceptance.md`, `reports/sl2_10_evidence.md`; mypy/full pytest/browser/fresh-clone and full-suite three-run requirements remain incomplete |

SL2-10 repeat runs: Vitest passed 153 tests across 24 files on three consecutive runs; `pytest -m security` passed 15 tests on three consecutive runs. The full Python suite did not yield a result, mypy reports 36 errors, and browser E2E is denied on localhost port 9222.

The shared checkout is on branch `sl2-0` and contains uncommitted changes from multiple phases. Phase tags were not created. Do not interpret an earlier phase summary as current machine verification; consult each evidence report for its commands and date.


