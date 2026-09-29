# Project State & Progress Tracking

**Current Phase:** Phase 2 Complete — Hand-Written Python Lexer, Security Rule Engine & AST Data-Flow Taint Tracking  
**Phase Tag:** `phase-2`  
**Date:** September 30, 2026  
**Status:** Complete / Verified (140 tests passing, 92% coverage on `lexing + python_lang + rules`, 100% clean ruff linter)  

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
- `docs/explained/phase0.md`: Educational documentation for Phase 0.
- `docs/explained/phase1.md`: Educational documentation for Phase 1 (lexer, tokens, homoglyphs, bidi overrides, 5 viva Q&As).
- `docs/explained/phase2.md`: Educational documentation for Phase 2 (lexer state machines, AST taint vs token windows, sources/sinks/sanitizers, 5 viva Q&As).

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
   - `scanner.py`: Detects Trojan Source bidi controls (U+202A–202E, U+2066–2069, U+200E/200F, U+061C), zero-width characters (U+200B–200D, U+2060, U+FEFF not at index 0, U+00AD, U+180E), Unicode tag characters (U+E0000–E007F), non-ASCII whitespace, confusables, and mixed-script identifiers.
   - `recovery.py`: Synthesizes `recovered_text` with confusables replaced and invisibles stripped, alongside an inverse mapping projecting recovered coordinates back onto original source text.
6. **Generic Unicode Rules (`src/apsla/rules/generic.py`):**
   - Language-agnostic security rules: `APS-ALL-UNI-001` (Trojan Source bidi), `APS-ALL-UNI-002` (zero-width characters), `APS-ALL-UNI-003` (tag characters), `APS-ALL-UNI-004` (confusables), `APS-ALL-UNI-005` (mixed-script identifiers), and `APS-ALL-UNI-006` (obfuscated dangerous built-in/keyword recovery).

### Phase 2 Implemented Components
1. **Hand-Written Python Lexer State Machine (`src/apsla/lexing/base.py` & `src/apsla/languages/python_lang/lexer.py`):**
   - `LexerBase`: Deterministic cursor, peek, advance, UTF-16 and 1-based line/col tracking. Zero crash design; invalid characters emit `ERROR` tokens.
   - `PythonLexer`: Lossless trivia preservation (`"".join(t.text for t in tokens) == source`). Supports keywords, Unicode-aware identifiers, numbers (underscores `1_000`, hex `0x`, octal `0o`, binary `0b`, floats, exponents, complex `j`), strings (prefixes `r`, `b`, `f`, `rb`, `br`, `fr`, `u` case-insensitive, single/double/triple quotes, escapes, line continuations), f-strings (emitted as a single `STRING` token with `parts` tuple holding embedded expression ranges), comments, operators (`:=`, `->`, `**=`, `//=`, `@`, `...`), indentation stack emitting `NEWLINE`, `INDENT`, `DEDENT` tokens with delimiter nesting depth tracking.
   - Cross-check test: Tested against Python standard library `tokenize` module on 35 real Python stdlib files for token boundary equivalence.
   - Property-based fuzz test: Hypothesis test verifying lexer never raises on arbitrary random text and reconstructs the input identically.
2. **Deterministic Python Security Rule Engine (`src/apsla/rules/base.py` & `src/apsla/languages/python_lang/rules.py`):**
   - Base `RuleContext` projecting recovered AST coordinates back to original file coordinates via `RecoveryResult.map_recovered_range()`.
   - 14 deterministic rules:
     - `APS-PY-INJ-001`: `eval` / `exec` on non-constant (CWE-95)
     - `APS-PY-INJ-002`: `os.system` / `os.popen` with built string (CWE-78)
     - `APS-PY-INJ-003`: `subprocess` with `shell=True` and dynamic command (CWE-78); list form without `shell=True` is verified SAFE
     - `APS-PY-INJ-004`: SQL built by concatenation, `%`-format, or f-string passed to `execute()` (CWE-89)
     - `APS-PY-DES-001`: `pickle.load(s)` / `marshal` / `shelve` on untrusted data (CWE-502)
     - `APS-PY-DES-002`: `yaml.load` without `SafeLoader` (CWE-502)
     - `APS-PY-CRY-001`: `hashlib.md5` / `sha1` used for security (CWE-327)
     - `APS-PY-CRY-002`: `random` module for tokens / secrets (CWE-338)
     - `APS-PY-SEC-001`: Hard-coded password / API key / token literal via heuristics and Shannon entropy (CWE-798)
     - `APS-PY-NET-001`: `requests` with `verify=False` (CWE-295)
     - `APS-PY-IO-001`: `open()` / `send_file` with user-controlled path (CWE-22)
     - `APS-PY-INJ-005`: dynamic `__import__` / `importlib.import_module` on non-constant (CWE-94)
     - `APS-PY-OBF-001`: `exec` / `eval` of base64 / zlib / bytes-decoded payload (CWE-506)
     - `APS-PY-XSS-001`: `render_template_string` / `Markup` with dynamic user data (CWE-79)
3. **AST Data-Flow Taint Analysis Engine (`src/apsla/languages/python_lang/taint.py`):**
   - Sources: `input()`, `sys.argv`, `os.environ` / `os.getenv`, `sys.stdin.read`/`readline`, socket `.recv()`, Flask `request.args`/`form`/`values`/`json`/`data`/`cookies`/`headers`, Django `request.GET`/`request.POST`, FastAPI parameters, and file read on user path.
   - Propagation: Assignment, augmented assignment, tuple unpacking, f-strings, `%`-formatting, `str.format`, concatenation, `.join`, slicing, list/dict containers, attribute and subscript access, function arguments and return values (intra-file function summaries).
   - Flow-sensitivity: Variable reassigned to constant becomes clean. Branches: set union of environments. Loops: fixed-point iteration (bounded to 3 rounds).
   - Sanitizers: `shlex.quote` (command), `int`/`float` casts (all), `html.escape`/`markupsafe.escape` (XSS), `os.path.basename`/`secure_filename` (path), parameterized SQL queries.
   - Sinks: Maps to rule IDs and produces full `TaintPathStep` provenance traces.
4. **Pipeline & Registry Integration (`src/apsla/pipeline.py` & `src/apsla/languages/python_lang/__init__.py`):**
   - `PythonPlugin` registered with ID `"python"` and extensions `[".py", ".pyw"]`.
   - Pipeline orchestrates: normalise $\to$ Unicode defense $\to$ hand-written lex $\to$ AST rules on recovered source $\to$ AST taint tracking $\to$ fusion stub (confidence +0.15, severity +1 on confirmed taint; sanitized flows suppressed) $\to$ summary score.
5. **Typer CLI (`src/apsla/cli.py`):**
   - `apsla analyze FILE [--format text|json] [--language python]`
   - Rich table output displaying Line, Severity, Rule ID, Message, and multi-step Taint Path.
   - Exits with code 1 if any high or critical finding is detected.
   - No import-time `sys.stdout` re-wrapping (handles Windows console encoding only within command execution).
6. **Fixtures & Benchmark Suite (`tests/fixtures/python/`):**
   - 70 Python test fixtures (31 vulnerable, 28 safe, 11 adversarial) paired with exact `expect.json` ground truth.
   - Tested by `tests/test_fixtures_runner.py` verifying exact `(rule_id, line)` matches.
   - Incorporates all 6 senior baseline probes as regression fixtures.

---

## 2. How to Run Acceptance Checks

All acceptance checks run within the local `.venv`:

```bash
# 1. Run linter (must report 100% clean)
.\.venv\Scripts\ruff.exe check .

# 2. Run full test suite in quiet mode (140 passed)
.\.venv\Scripts\pytest.exe -q

# 3. Check test coverage on lexing, python_lang, and rules (must be >= 85.0%; achieved: 92.0%)
.\.venv\Scripts\pytest.exe --cov=src/apsla/lexing --cov=src/apsla/languages/python_lang --cov=src/apsla/rules --cov-report=term-missing

# 4. Run CLI analysis on vulnerable Flask command injection fixture (shows 4-step taint path)
.\.venv\Scripts\apsla.exe analyze tests/fixtures/python/vulnerable/cmd_injection_flask.py

# 5. Run comparative probe against legacy senior baseline across all 6 probes
.\.venv\Scripts\python.exe scripts/legacy_probe.py
```

---

## 3. Public Function Signatures (Phase 2)

### `src/apsla/lexing/base.py`
- `LexerBase(source: str)`:
  - `peek(offset: int = 0) -> str`
  - `advance() -> str`
  - `match(expected: str) -> bool`
  - `match_any(chars: Container[str]) -> bool`
  - `create_token(kind: str, text: str, start: int, start_line: int, start_col: int) -> Token`
  - `tokenize() -> list[Token]`

### `src/apsla/languages/python_lang/lexer.py`
- `PythonLexer(source: str)`:
  - `tokenize() -> list[Token]`

### `src/apsla/rules/base.py`
- `RuleContext(raw_source: str, recovered_source: str, tokens: list[Token], ast_tree: ast.AST | None, offset_map: OffsetMap, recovery: RecoveryResult, language: str, filename: str, metadata: dict)`:
  - `node_to_range(node: ast.AST) -> Range`
- `Rule(id: str, title: str, cwe: str, severity: Severity, noisy: bool)`:
  - `match(context: RuleContext) -> list[Finding]`

### `src/apsla/languages/python_lang/taint.py`
- `PythonTaintAnalyzer(context: RuleContext)`:
  - `analyze() -> TaintResult`
- `TaintResult(flows: list[TaintFlow])`
- `TaintFlow(rule_id: str, sink_range: Range, path: list[TaintPathStep], sanitized: bool, message: str)`

### `src/apsla/languages/python_lang/__init__.py`
- `PythonPlugin(LanguagePlugin)`:
  - `lex(source: str) -> list[Token]`
  - `rules() -> list[Rule]`
  - `taint_profile() -> TaintProfile`
  - `analyze_taint(source: str, offset_map: OffsetMap) -> list[TaintResult]`
  - `syntax_check(source: str) -> tuple[bool, str | None]`
  - `dangerous_apis() -> dict[str, str]`

### `src/apsla/cli.py`
- `analyze(file: Path, format: str = "text", language: str | None = None)`
