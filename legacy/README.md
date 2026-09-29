# Legacy Codebase Attribution & Known Defects

This directory preserves the original university compiler design projects submitted by senior students, preserved strictly as **read-only reference** for comparative analysis and benchmarking.

## 1. Project Attribution

### Senior Project Part 1 (`legacy/senior-part1/`)
- **Origin:** University student compiler design project ("Secure Lexer Code - Part 1").
- **Components:** Python lexer prototype (`W5_6/`), initial ML and hybrid validator (`ML_model/`), carbon emission tracker (`carbon_analysis/`), and FastAPI/React prototype (`frontend/`).
- **License Status:** No license file provided in original archive. Code ideas and findings are reimplemented cleanly from scratch in `src/apsla/`; raw datasets are copied with recorded provenance in `data/PROVENANCE.md`.

### Senior Project Part 2 (`legacy/senior-part2/`)
- **Origin:** University project `AI-Powered-Secure-Lexical-Analyzer` (Java-oriented lexical and security analyzer).
- **Author:** Himanshu Sharma
- **License:** MIT License (Copyright (c) 2026 Himanshu Sharma). Full license text archived at [third_party/LICENSE-senior-part2-MIT.txt](file:///third_party/LICENSE-senior-part2-MIT.txt).
- **Usage Policy:** Select lexical and AST patterns may be adapted with explicit citation: `"Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT)"`.

---

## 2. Directory Sanitation Policy

To keep the repository clean, deterministic, and free of redundant artifacts, the following directories were purged from `legacy/` during Phase 0 reorganization (documented in `docs/STATE.md`):
- Virtual environments: `.venv/`
- Version control metadata: `.git/`
- Bytecode caches: `__pycache__/`
- Package manager artifacts: `node_modules/`
- Ephemeral logs: `logs/`
- Runtime output dumps: `results/`, `W5_6/results/`, `carbon_analysis/results/`

---

## 3. Known Defects & Baseline Measurement (12 Items)

The following architectural, conceptual, and security defects were verified in the senior codebase with exact file and line citations:

| # | Defect Title | Source Location | Verified Evidence & Failure Impact |
|---|---|---|---|
| **1** | Missing Training Loop in `train_model.py` | `legacy/senior-part1/ML_model/train_model.py:L1-7` | Despite its name, `train_model.py` contains 0 training loops, 0 epochs, and 0 optimizer steps. It is an earlier duplicate of `hybrid_validator.py`. |
| **2** | Silent Fallback with Random Neural Weights | `legacy/senior-part1/ML_model/ai_model.py:L160, 186-212` | When `bilstm_model_real.pth` is missing, `load_model()` catches `FileNotFoundError`, logs an error, but leaves `self.model` active with random uninitialized weights without disabling ML mode. |
| **3** | BiLSTM Evaluated Over Sequence Length 1 | `legacy/senior-part1/ML_model/ai_model.py:L69-70, 225-228` | Tokens are processed individually with `.unsqueeze(0)` to shape `(batch=1, seq_len=1, dim=34)`. A bidirectional recurrent network on length 1 provides zero temporal or context value. |
| **4** | High Synthetic Token Redundancy | `legacy/senior-part1/data/processed/token_security_dataset_v2.csv` | In a 50,000-row dataset, only 22,600 unique raw tokens exist (54.8% duplicate rows). Row-based random splits result in severe data leakage. |
| **5** | Fabricated / Identical Performance Metrics | `legacy/senior-part1/carbon_analysis/performance/summary.json:L1-59` | Precision, recall, and F1 (`SAFE=0.8777`, `SUSPICIOUS=0.1667`, `MALICIOUS=0.3077`, `wscore=0.3479`) are 100% identical across `Static`, `Dynamic`, and `Pure_ML`. |
| **6** | False Negative on Flask Request Taint Sources | `legacy/senior-part1/ML_model/hybrid_validator.py:L42-46, 86` | `_SOURCE_FUNCS` checks `"request.args"`, but the lexer splits attributes into separate tokens (`"request"`, `"."`, `"args"`). Taint is never initialized on `request.args.get("q")`. |
| **7** | False Positive on Safe Subprocess Execution | `legacy/senior-part1/ML_model/hybrid_validator.py:L159-163, 208-214` | The keyword rule flags `subprocess` unconditionally as `dangerous built-in` + `shell pattern`, classifying `subprocess.run(["ls","-l"])` as MALICIOUS (0.90). |
| **8** | Missed Trojan Source in String Literals | `legacy/senior-part1/W5_6/lexer.py:L55-59` & `ML_model/hybrid_validator.py:L165-174` | Bidirectional control characters (`U+202E`) inside string tokens are not analyzed for Unicode risk, allowing Trojan Source injections to pass as SAFE. |
| **9** | Insufficient Severity for Cyrillic Homoglyphs | `legacy/senior-part1/ML_model/hybrid_validator.py:L168-170, 218-223` | Obfuscated built-in `ехес` (using Cyrillic `е` and `с`) receives only score 0.40 (SUSPICIOUS) instead of being recovered and flagged as MALICIOUS. |
| **10** | Naive Backward LHS Variable Binding | `legacy/senior-part1/ML_model/hybrid_validator.py:L119-130` | `_find_lhs_var()` searches backward up to 5 tokens for `=`. It fails on tuple unpacking, class attributes, and multi-line statements. |
| **11** | Missing Licensing in Part 1 Codebase | `legacy/senior-part1/` | No license or terms of use were provided with the senior Part 1 code, preventing direct code reuse in an open-source project. |
| **12** | Regex-Only Pattern Matching in Part 2 | `legacy/senior-part2/src/security/static_analyzer.py:L30-85` | Part 2 relies on flat regex pattern matching over source lines without AST or scope awareness, causing false alerts on commented-out code. |

---

## 4. Policy Reminder

From Phase 0 onward, **`legacy/` is strictly READ-ONLY**. Do not modify, import, or build against files in this directory.
