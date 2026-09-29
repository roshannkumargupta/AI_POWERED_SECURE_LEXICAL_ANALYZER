# Project State & Progress Tracking

**Current Phase:** Phase 0 — Reorganize, Specification, Baseline Measurement, Skeleton  
**Phase Tag:** `phase-0`  
**Date:** September 30, 2026  
**Status:** In Progress / Verifying Acceptance  

---

## 1. What Exists

### Repository & Legacy Layout
- `legacy/senior-part1/`: Original Python analyzer codebase (prototype lexer `W5_6/`, hybrid validator `ML_model/`, carbon tracker `carbon_analysis/`, and React/FastAPI UI `frontend/`).
- `legacy/senior-part2/`: Original Java-oriented analyzer codebase (`AI-Powered-Secure-Lexical-Analyzer`, MIT licensed).
- `legacy/README.md`: Attribution documentation, sanitation records, and 12 verified architectural and security defects.
- `third_party/LICENSE-senior-part2-MIT.txt`: MIT License from senior part 2 (Copyright (c) 2026 Himanshu Sharma).
- `data/raw/`: Raw CSV datasets copied unchanged (`homoglyph_attacks.csv`, `injection_payloads.csv`, `safe_tokens.csv`).
- `data/sources/`: Official Unicode confusable table (`confusables.txt`).
- `data/PROVENANCE.md`: Cryptographic provenance tracking with exact file paths, sizes in bytes, and SHA-256 hashes.
- `docs/plan/`: Preserved Word documents (`Professor_Report_16_Week_Improvement_Plan (1).docx`, `Self_Study_Guide_16_Weeks.docx`).
- `PROJECT_SPEC.md`: Definitive project specification covering sections A through P.
- `scripts/legacy_probe.py`: Reproducible measurement script probing the senior baseline across 6 scenarios and verifying 5 architectural defects.

### Purged Legacy Directories (Sanitation Record)
During reorganization in Step 1, only the following folders were purged from the legacy directories:
1. `secure_lexer_code-Part1/.venv` (virtual environment; 449+ files)
2. `secure_lexer_code-Part1/.git` (uncommitted embedded git metadata; 21 files)
3. `secure_lexer_code-Part1/logs` (12 runtime log files)
4. `secure_lexer_code-Part1/results` (40 runtime output files)
5. `secure_lexer_code-Part1/W5_6/results` (2 output files)
6. `secure_lexer_code-Part1/carbon_analysis/results` (1 output file)
7. All `__pycache__` directories across `senior-part1` (11 directories) and `senior-part2` (5 directories)
8. `carbon_analysis/performance/`: Checked for raw outputs > 5 MB. None exceeded 5 MB (largest was `per_class_metrics.png` at 59.4 KB), so all benchmark charts were retained.
9. `node_modules`: Checked; none existed.

Total purged directories: 67 directories. `legacy/` is now permanently **READ-ONLY**.

### Project Skeleton (`src/apsla/`)
- `pyproject.toml`: Configured for package `apsla`, `src/` layout, console script `apsla = apsla.cli:main`.
- `requirements.txt` & `requirements-dev.txt`: Pinned dependencies for runtime and developer tooling.
- `.gitignore`, `.editorconfig`, `ruff.toml`, `.env.example`, `README.md`.
- `src/apsla/`:
  - `__init__.py`, `models.py`, `config.py`, `pipeline.py`, `fusion.py`, `scoring.py`, `cwe.py`, `cli.py`
  - `unicode_defense/`: `__init__.py`, `confusables.py`, `scripts.py`, `scanner.py`, `recovery.py`, `data/.gitkeep`
  - `lexing/`: `__init__.py`, `token.py`, `base.py`, `common.py`
  - `languages/`: `__init__.py`, `base.py`, `registry.py`
  - `languages/python_lang/`: `__init__.py`, `lexer.py`, `rules.py`, `taint.py`, `fixes.py`
  - `languages/java_lang/`: `__init__.py`, `lexer.py`, `rules.py`, `profile.py`, `fixes.py`
  - `languages/javascript_lang/`: `__init__.py`, `lexer.py`, `rules.py`, `profile.py`, `fixes.py`
  - `languages/cpp_lang/`: `__init__.py`, `lexer.py`, `rules.py`, `profile.py`, `fixes.py`
  - `taint/`: `__init__.py`, `lite.py`, `paths.py`
  - `rules/`: `__init__.py`, `base.py`, `registry.py`, `generic.py`
  - `ml/`: `__init__.py`, `features.py`, `windows.py`, `models.py`, `train.py`, `evaluate.py`, `infer.py`, `explain.py`, `calibrate.py`, `synth/.gitkeep`, `artifacts/.gitkeep`
  - `fixes/`: `__init__.py`, `engine.py`, `verifier.py`, `edits.py`, `imports.py`, `registry.py`
  - `feedback/`: `__init__.py`, `store.py`
  - `llm/`: `__init__.py`, `provider.py`, `null.py`
  - `server/`: `__init__.py`, `app.py`, `schemas.py`, `samples.py`
- `tests/`: `__init__.py`, `test_smoke.py`, unit/integration/e2e/fixtures directories with `.gitkeep`.
- `web/`: Directory created with `.gitkeep` (populated in Phase 6).
- `docs/architecture.md`: Detailed system architecture documentation.

---

## 2. How to Run

### Setup Environment
```bash
# Create Python 3.12 virtual environment
python -m venv .venv

# Activate on Windows PowerShell
.venv\Scripts\Activate.ps1

# Activate on POSIX / bash
source .venv/bin/activate

# Install development dependencies and editable package
pip install -r requirements-dev.txt
pip install -e .
```

### Run Acceptance Checks
```bash
# 1. Verify virtual environment & package import
.venv/Scripts/python -c "import apsla; print('ok')"

# 2. Run code style and linter check
ruff check .

# 3. Run smoke test suite
pytest -q

# 4. Run baseline probe against senior legacy code
python scripts/legacy_probe.py

# 5. Verify Git status of legacy directory
git status legacy/
```

---

## 3. Public Function Signatures (Phase 0 Skeleton)

All skeleton files currently define module docstrings. The following top-level signatures are established for implementation in subsequent phases:

- `apsla.cli.main() -> None`: Main CLI entrypoint.
- `apsla.pipeline.Analyzer.analyze(source: str, language: str, filename: str = "<editor>", options: dict | None = None) -> AnalysisResult`: Unified analysis pipeline.
- `apsla.languages.base.LanguagePlugin`:
  - `lex(source: str) -> list[Token]`
  - `rules() -> list[Rule]`
  - `taint_profile() -> TaintProfile`
  - `analyze_taint(source: str, tokens: list[Token]) -> list[TaintFinding]`
  - `fix_generators() -> dict[str, FixGenerator]`
  - `syntax_check(source: str) -> tuple[bool, str | None]`
- `apsla.fixes.engine.FixEngine.apply_fixes(source: str, fixes: list[Fix]) -> str`: Reverse-order atomic edit application.
- `apsla.fixes.verifier.FixVerifier.verify(original: str, modified: str, language: str, finding_id: str) -> VerificationResult`: Shadow re-analysis verifier.
- `scripts.legacy_probe.main() -> None`: Baseline probe runner.

---

## 4. Key Architectural Decisions

1. **Independent Git Repository:** Initialized git directly in `securelex-ide` root, isolating it from user home directory git paths. Used `git mv` to maintain file history while moving legacy components into `legacy/senior-part1` and `legacy/senior-part2`.
2. **Immutable Legacy Sandbox:** `legacy/` is designated as read-only. Production code in `src/apsla/` is forbidden from importing anything from `legacy/`.
3. **No Silent Fallbacks:** Addressed Senior Defect #2 by requiring that any missing or invalid ML model triggers an explicit `"ml_mode": "off"` response, surfaced to the developer.
4. **Resilient Lexer Invariant:** Hand-written lexers must never raise an unhandled exception. Malformed tokens are tagged `TokenType.ERROR`, ensuring complete input reconstruction without crashes.
5. **UTF-8 Everywhere:** Enforced UTF-8 encoding across all file operations and console streams to prevent platform-dependent encoding bugs on Windows.

---

## 5. Blockers

- **None.** Phase 0 requirements and acceptance checks are completely unblocked.

---

## 6. Known Issues

- **Senior Model Weight File Missing:** `models/bilstm_model_real.pth` was not included in the senior's zip archive. The baseline probe script explicitly handles this and reports `"ML: not loadable"`, consistent with instructions.
