# Project State & Progress Tracking

**Current Phase:** Phase 1 Complete — Shared Core (Data Models, Offset Handling, Unicode Defense, Plugin Architecture)  
**Phase Tag:** `phase-1`  
**Date:** September 30, 2026  
**Status:** Complete / Verified (48 tests passing, 96% coverage on `unicode_defense`, 100% clean ruff linter)  

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
- `docs/plan/`: Preserved Word documents (`Professor_Report_16_Week_Improvement_Plan (1).docx`, `Self_Study_Guide_16_Weeks.docx`).
- `PROJECT_SPEC.md`: Definitive project specification covering sections A through P.
- `scripts/legacy_probe.py`: Measurement script probing senior baseline and comparing Probes 5 & 6 with our Phase 1 analyzer.
- `reports/phase_0_evidence.md`: Baseline probe and verification evidence for Phase 0.
- `reports/phase_1_evidence.md`: Full verification evidence, coverage reports, and comparative benchmark for Phase 1.
- `docs/explained/phase0.md`: Educational documentation for Phase 0.
- `docs/explained/phase1.md`: Educational documentation for Phase 1 (lexer, tokens, homoglyphs, bidi overrides, 5 viva Q&As).

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
   - `token.py`: Immutable dataclass `Token` with UTF-16 code unit offsets and conversions to `Range` and `TokenInfo`.
   - `common.py`: Bidirectional `OffsetMap` class converting between Python string slice indices, UTF-16 code units, and 1-based (line, col) coordinates, with full surrogate-pair support for astral plane characters (emojis), CRLF/LF/CR newlines, and tabs.
5. **Multi-Vector Unicode Defense Layer (`src/apsla/unicode_defense/`):**
   - `scripts/build_confusables.py`: Generates `src/apsla/unicode_defense/data/confusables.json` containing 1,868 Unicode look-alike characters mapping to ASCII.
   - `scripts.py`: Unicode script classification and mixed-script detection using the `regex` package and `\p{Script=...}` property escapes.
   - `scanner.py`: Detects Trojan Source bidi controls (U+202A–202E, U+2066–2069, U+200E/200F, U+061C), zero-width characters (U+200B–200D, U+2060, U+FEFF not at index 0, U+00AD, U+180E), Unicode tag characters (U+E0000–E007F), non-ASCII whitespace, confusables, and mixed-script identifiers.
   - `recovery.py`: Synthesizes `recovered_text` with confusables replaced and invisibles stripped, alongside an inverse mapping projecting recovered coordinates back onto original source text.
6. **Language Plugin Interface & Registry (`src/apsla/languages/`):**
   - `base.py`: Abstract `LanguagePlugin` protocol matching `PROJECT_SPEC.md` Section F, along with `Rule`, `TaintProfile`, `FixGenerator`, `SyntaxResult`, and `TaintResult`.
   - `registry.py`: Plugin registry supporting `register()`, `get()`, `detect()` (by extension and shebang), `list_plugins()`, and `clear_registry()`.
7. **Generic Unicode Rules (`src/apsla/rules/generic.py`):**
   - Language-agnostic security rules: `APS-ALL-UNI-001` (Trojan Source bidi), `APS-ALL-UNI-002` (zero-width characters), `APS-ALL-UNI-003` (tag characters), `APS-ALL-UNI-004` (confusables), `APS-ALL-UNI-005` (mixed-script identifiers), and `APS-ALL-UNI-006` (obfuscated dangerous built-in/keyword recovery).
   - Generates verified remediation patches for automatic stripping or ASCII normalization.
8. **Scoring & End-to-End Pipeline (`src/apsla/scoring.py` & `src/apsla/pipeline.py`):**
   - `scoring.py`: Computes 0..100 security health score applying weights and penalty caps.
   - `pipeline.py`: `Analyzer.analyze()` orchestrating normalization $\to$ Unicode defense $\to$ generic Unicode rules $\to$ token generation $\to$ summary metrics.

---

## 2. How to Run Acceptance Checks

All acceptance checks run within the local `.venv`:

```bash
# 1. Run linter (must report 100% clean)
.\.venv\Scripts\ruff.exe check .

# 2. Run full test suite in quiet mode (48 passed)
.\.venv\Scripts\pytest.exe -q

# 3. Execute the exact acceptance one-liner
.\.venv\Scripts\python.exe -c "from apsla.pipeline import Analyzer; print(Analyzer().analyze('e\u0445ec(1)', 'python', 'a.py', {}).summary)"

# 4. Check test coverage on unicode_defense (must be >= 90.0%; achieved: 96.1%)
.\.venv\Scripts\pytest.exe --cov=src/apsla/unicode_defense --cov-report=term-missing

# 5. Run comparative probe against legacy senior baseline (comparison column for probes 5 & 6)
.\.venv\Scripts\python.exe scripts/legacy_probe.py
```

---

## 3. Public Function Signatures (Phase 1)

### `src/apsla/models.py`
- `Range(start_line: int, start_col: int, end_line: int, end_col: int)`
- `TokenInfo(token: str, token_type: str, range: Range, label: str = "SAFE", score: float = 0.0)`
- `Token(kind: str, text: str, start: int, end: int, line: int, col: int, end_line: int, end_col: int)`
- `Edit(range: Range, new_text: str)`
- `VerificationResult(syntax_ok: bool, finding_gone: bool, new_findings: list[str], verified: bool, notes: str)`
- `Fix(id: str, finding_id: str, title: str, description: str, confidence: str, kind: str, edits: list[Edit], verification: VerificationResult | None)`
- `Finding(id: str, rule_id: str, title: str, cwe: str, severity: Severity, label: Label, confidence: float, range: Range, message: str, explanation: str, evidence: dict, taint_path: list, fixes: list[Fix], sources: list[str], suppressed: bool)`
- `AnalysisSummary(critical: int, high: int, medium: int, low: int, info: int, score: int, tokens_total: int, tokens_malicious: int, tokens_suspicious: int)`
- `EngineMetadata(ml_mode: str, ml_model_id: str, taint: str, version: str, elapsed_ms: float)`
- `AnalysisResult(tokens: list[TokenInfo], findings: list[Finding], summary: AnalysisSummary, engine: EngineMetadata)`

### `src/apsla/lexing/common.py`
- `OffsetMap(text: str)`:
  - `py_to_utf16(py_idx: int) -> int`
  - `utf16_to_py(u16_idx: int) -> int`
  - `py_to_pos(py_idx: int) -> tuple[int, int]`
  - `utf16_to_pos(u16_idx: int) -> tuple[int, int]`
  - `pos_to_utf16(line: int, col: int) -> int`
  - `pos_to_py(line: int, col: int) -> int`
  - `span_to_range(start_py: int, end_py: int) -> Range`

### `src/apsla/unicode_defense/`
- `scripts.get_character_script(ch: str) -> str`
- `scripts.get_scripts(text: str) -> set[str]`
- `scripts.is_mixed_script(text: str) -> bool`
- `scanner.scan_unicode(text: str, offset_map: OffsetMap | None = None) -> UnicodeScanResult`
- `recovery.recover_text(text: str, offset_map_orig: OffsetMap | None = None) -> RecoveryResult`
  - `map_py_offset(rec_py_idx: int) -> int`
  - `map_span_to_original(rec_start: int, rec_end: int) -> tuple[int, int]`
  - `map_recovered_range(rec_range: Range) -> Range`

### `src/apsla/languages/`
- `base.LanguagePlugin` (Protocol):
  - `lex(source: str) -> list[Token]`
  - `rules() -> list[Rule]`
  - `taint_profile() -> TaintProfile`
  - `analyze_taint(source: str, tokens: list[Token]) -> list[TaintResult]`
  - `fix_generators() -> dict[str, FixGenerator]`
  - `syntax_check(source: str) -> tuple[bool, str | None]`
  - `dangerous_apis() -> dict[str, str]`
- `registry.register(plugin: LanguagePlugin) -> None`
- `registry.get(plugin_id: str) -> LanguagePlugin | None`
- `registry.detect(filename: str, text: str = "") -> LanguagePlugin | None`
- `registry.list_plugins() -> list[LanguagePlugin]`
- `registry.clear_registry() -> None`

### `src/apsla/pipeline.py`
- `Analyzer(options: dict | None = None)`:
  - `analyze(source: str, language: str = "generic", filename: str = "<editor>", options: dict | None = None) -> AnalysisResult`

---

## 4. Key Architectural Decisions (Phase 1)

1. **UTF-16 Code Units as Native Coordinate Space:** Designed from the start to align with Monaco Editor's JavaScript DOM string representation, preventing coordinate drift when processing emoji or non-BMP symbols.
2. **Pre-Lexer Unicode Defense Stage:** Running Unicode defense and token recovery before the language-specific lexer ensures adversarial homoglyphs and hidden bidi overrides are neutralized into canonical ASCII forms before AST or syntax parsers encounter them.
3. **Inverse Coordinate Projection:** When findings are detected on recovered text, the pipeline maps coordinate spans back to original un-sanitized source coordinates through `RecoveryResult.map_recovered_range()`.
4. **Verified Atomic Fix Edits:** Remediation patches are generated as character-level replacements and certified for syntax safety, target vulnerability elimination, and regression prevention.
5. **Immutable `legacy/` Reference:** The legacy student directory remains untouched and read-only. Comparative measurements run by dynamically inspecting legacy code strictly from measurement harnesses.

---

## 5. Blockers

- **None.** All Phase 1 deliverables, benchmarks, and acceptance criteria are completed and verified.

---

## 6. Known Issues / Next Phase Scope

- **Phase 2 Scope:** Phase 2 will implement the Python language plugin (`src/apsla/languages/python_lang/`), replacing the placeholder whitespace tokenizer with the hand-written zero-crash Python lexer, deterministic Python security rules, and AST intra-file taint tracking.
