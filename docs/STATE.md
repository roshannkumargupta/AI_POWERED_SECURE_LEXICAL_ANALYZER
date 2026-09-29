# Project State & Progress Tracking

**Current Phase:** Phase 3 Complete — Verified Automated Fix Generation, Remediation Engine & CLI Fix Subcommand  
**Phase Tag:** `phase-3`  
**Date:** September 30, 2026  
**Status:** Complete / Verified (167 tests passing, 100% clean ruff linter, full automated shadow verification)  

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
- `scripts/legacy_probe.py`: Measurement script probing senior baseline and comparing all 6 probes with our Phase 2 analyzer.
- `reports/phase_0_evidence.md`: Baseline probe and verification evidence for Phase 0.
- `reports/phase_1_evidence.md`: Full verification evidence, coverage reports, and comparative benchmark for Phase 1.
- `reports/phase_2_evidence.md`: Full verification evidence, coverage reports, and comparative benchmark for Phase 2.
- `reports/phase_3_evidence.md`: Full verification evidence, fix matrix, and CLI demonstration for Phase 3.
- `docs/explained/phase0.md`: Educational documentation for Phase 0.
- `docs/explained/phase1.md`: Educational documentation for Phase 1 (lexer, tokens, homoglyphs, bidi overrides, 5 viva Q&As).
- `docs/explained/phase2.md`: Educational documentation for Phase 2 (lexer state machines, AST taint vs token windows, sources/sinks/sanitizers, 5 viva Q&As).
- `docs/explained/phase3.md`: Educational documentation for Phase 3 (shadow verification sandbox, AST-safe import injection, back-to-front edits, 5 viva Q&As).

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
   - `FIX_REGISTRY`: Per-rule registry mapping rule IDs to fix generators.
   - `generate_fixes(...)`: Generates fixes and attaches stable IDs (`fix-{finding.id}-{idx}`).
4. **Shadow Verification Sandbox (`src/apsla/fixes/verifier.py`):**
   - Sandboxes each proposed fix on an in-memory document copy.
   - Validates parser syntax (`plugin.syntax_check`).
   - Runs shadow re-analysis (`Analyzer.analyze(..., options={"fixes": False})`).
   - Validates `finding_gone` near the original logical line ($\pm 5$ lines).
   - Detects regression (`new_findings` with severity $\ge$ medium not in unpatched code).
   - Time-limited to **2.0 seconds** per fix. Automatic downgrade to `"manual"` and edit purging on verification failure.
5. **Python Fix Generators (`src/apsla/languages/python_lang/fixes.py`):**
   - 16 registered generators for Unicode rules and all Python security rules (`APS-ALL-UNI-001..006`, `APS-PY-INJ-001..004`, `APS-PY-DES-001..002`, `APS-PY-CRY-001..002`, `APS-PY-SEC-001`, `APS-PY-NET-001`, `APS-PY-IO-001`, `APS-PY-XSS-001`).
   - Attribution: Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT) where indicated.
6. **Multi-Pass Batch Remediation (`engine.fix_all`):**
   - Applies safe + verified fixes iteratively up to 3 passes until convergence.
   - Returns new source, applied IDs, skipped IDs with reasons, diff, and health score before/after.
   - Verified idempotency: `fix_all(fix_all(x)) == fix_all(x)`.
7. **Pipeline & CLI Remediation Commands (`src/apsla/pipeline.py` & `src/apsla/cli.py`):**
   - Pipeline Stage 7.5 attaches verified fixes automatically when `options={"fixes": True}`.
   - CLI command: `apsla fix FILE [--apply] [--all-safe]` displaying security health increase panel, remediation summary, unified diff, and backup creation (`FILE.bak`) on `--apply`.

---

## 2. How to Run Acceptance Checks

All acceptance checks run within the local `.venv`:

```bash
# 1. Run linter (must report 100% clean)
.\.venv\Scripts\ruff.exe check .

# 2. Run full test suite in quiet mode (167 passed)
.\.venv\Scripts\pytest.exe -q

# 3. Run fix generator test suite verifying all 16 generators, verification downgrades, and idempotency
.\.venv\Scripts\pytest.exe tests/unit/test_fixes_generators.py -v

# 4. Run CLI fix subcommand demonstrating diff and score increase (75 -> 100)
.\.venv\Scripts\apsla.exe fix tests/fixtures/python/vulnerable/cmd_injection_flask.py
```

---

## 3. Public Function Signatures (Phase 3)

### `src/apsla/fixes/edits.py`
- `apply_edits(source: str, edits: list[Edit]) -> str`
- `unified_diff(before: str, after: str, filename: str = "<file>") -> str`
- `class OverlappingEditsError(ValueError)`

### `src/apsla/fixes/imports.py`
- `ensure_import_python(source: str, import_stmt: str) -> list[Edit]`

### `src/apsla/fixes/registry.py`
- `class FixContext`: `source: str`, `finding: Finding`, `tokens: list[Token]`, `ast_tree: ast.AST | None`, `offset_map: OffsetMap`, `language: str`
- `class FixGenerator(ABC)`: `generate(context: FixContext) -> list[Fix]`
- `class FixRegistry`: `register(rule_id: str, generator: FixGenerator)`, `get(rule_id: str) -> list[FixGenerator]`
- `FIX_REGISTRY: FixRegistry`

### `src/apsla/fixes/verifier.py`
- `verify_fix(source: str, fix: Fix, finding: Finding, language: str = "python", existing_finding_keys: set[tuple[str, int]] | None = None, timeout_seconds: float = 2.0) -> Fix`

### `src/apsla/fixes/engine.py`
- `generate_fixes(source: str, finding: Finding, tokens: list[Token], language: str = "python", verify: bool = True, existing_finding_keys: set[tuple[str, int]] | None = None) -> list[Fix]`
- `fix_all(source: str, language: str = "python", filename: str = "<editor>", allow_review: bool = False) -> tuple[str, list[str], dict[str, str], str, int, int]`

### `src/apsla/cli.py`
- `analyze(file: Path, format: str = "text", language: str | None = None)`
- `fix(file: Path, apply: bool = False, all_safe: bool = False, language: str | None = None)`
