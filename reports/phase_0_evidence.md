# Phase 0 Acceptance Evidence Report

**Project:** SecureLex IDE (`apsla`)  
**Phase:** 0 — Reorganize, Master Specification, Baseline Measurement, Skeleton  
**Date:** September 30, 2026  
**Host Environment:** Windows (PowerShell, Python 3.12.5)  

---

## Acceptance Command 1: Python Virtual Environment & Import Check

### Command
```powershell
.venv\Scripts\python.exe -c "import apsla; print('ok')"
```

### Exact Terminal Output
```
ok
```

---

## Acceptance Command 2: Ruff Code Quality Check

### Command
```powershell
.venv\Scripts\ruff.exe check .
```

### Exact Terminal Output
```
All checks passed!
```

---

## Acceptance Command 3: Pytest Smoke Test Suite

### Command
```powershell
.venv\Scripts\pytest.exe -q
```

### Exact Terminal Output
```
.                                                                        [100%]
1 passed in 0.05s
```

---

## Acceptance Command 4: Legacy Baseline Probe Execution

### Command
```powershell
.venv\Scripts\python.exe scripts/legacy_probe.py
```

### Exact Terminal Output
```
2026-09-30 01:48:53,695 | INFO     | BaselineLexer | BaselineLexer ready (regex engine)
2026-09-30 01:48:53,695 | INFO     | Pipeline | Pipeline ready -> results
2026-09-30 01:48:53,696 | INFO     | BaselineLexer | 'probe_1.py': 19 tokens in 0.1 ms
2026-09-30 01:48:53,700 | INFO     | HybridValidator | Validating 19 tokens
2026-09-30 01:48:53,701 | INFO     | BaselineLexer | 'probe_2.py': 17 tokens in 0.1 ms
2026-09-30 01:48:53,704 | INFO     | HybridValidator | Validating 17 tokens
2026-09-30 01:48:53,704 | WARNING  | HybridValidator | Token 'input' -> SUSPICIOUS (score=0.650)
2026-09-30 01:48:53,704 | WARNING  | HybridValidator | Token 'u' -> SUSPICIOUS (score=0.650)
2026-09-30 01:48:53,705 | WARNING  | HybridValidator | Token 'system' -> MALICIOUS (score=0.920)
2026-09-30 01:48:53,705 | WARNING  | HybridValidator | Token 'v' -> SUSPICIOUS (score=0.650)
2026-09-30 01:48:53,705 | INFO     | BaselineLexer | 'probe_3.py': 17 tokens in 0.1 ms
2026-09-30 01:48:53,708 | INFO     | HybridValidator | Validating 17 tokens
2026-09-30 01:48:53,708 | INFO     | BaselineLexer | 'probe_4.py': 10 tokens in 0.1 ms
2026-09-30 01:48:53,710 | INFO     | HybridValidator | Validating 10 tokens
2026-09-30 01:48:53,711 | WARNING  | HybridValidator | Token 'subprocess' -> MALICIOUS (score=0.900)
2026-09-30 01:48:53,711 | INFO     | BaselineLexer | 'probe_5.py': 3 tokens in 0.1 ms
2026-09-30 01:48:53,712 | INFO     | HybridValidator | Validating 3 tokens
2026-09-30 01:48:53,713 | INFO     | BaselineLexer | 'probe_6.py': 4 tokens in 0.0 ms
2026-09-30 01:48:53,715 | INFO     | HybridValidator | Validating 4 tokens
2026-09-30 01:48:53,715 | WARNING  | HybridValidator | Token '\u0435\u0445\u0435\u0441' -> SUSPICIOUS (score=0.400)
=========================================================================================================
SECURELEX IDE - PHASE 0 LEGACY BASELINE PROBE REPORT
Target: legacy/senior-part1 | Status: ML: not loadable (bilstm_model_real.pth missing from zip archive)
=========================================================================================================

### SECTION 1: SECURITY PROBE RESULTS (6 SCENARIOS)
---------------------------------------------------------------------------------------------------------
#   | Probe Title                            | Senior Verdict           | Flaw / Assessment               
---------------------------------------------------------------------------------------------------------
1   | Flask request taint to os.system sink  | SAFE (0 flagged)         | FALSE NEGATIVE: Missed (attribute split)
2   | Sequential input() taint propagation to os.system | input: SUSPICIOUS (0.65) | CAUGHT: Caught sink & propagation
3   | Sanitized input via shlex.quote()      | SAFE (0 flagged)         | SAFE (no sanitizer model in senior)
4   | Safe list-form subprocess execution    | subprocess: MALICIOUS (0.90) | FALSE POSITIVE: Naive keyword match
5   | Trojan Source Bidi Override (U+202E)   | SAFE (0 flagged)         | FALSE NEGATIVE: Missed Trojan Source
6   | Cyrillic homoglyph look-alike 'exec'   | ехес: SUSPICIOUS (0.40)  | WEAK: Flagged SUSPICIOUS not MALICIOUS
---------------------------------------------------------------------------------------------------------

### SECTION 2: VERIFIED ARCHITECTURAL & CODE DEFECTS
---------------------------------------------------------------------------------------------------------
[DEFECT-A] ML_model/train_model.py lacks training loop
  Location : legacy/senior-part1/ML_model/train_model.py (Lines 1-7, 457 total lines)
  Evidence : File header claims 'Phase 5 + 6 — Hybrid Validator'. Contains 0 training loops (epoch/optimizer/loss found: False). Matches hybrid_validator.py almost line-for-line.

[DEFECT-B] Model loader silent fallback with random weights
  Location : legacy/senior-part1/ML_model/ai_model.py (Lines 160, 186-212)
  Evidence : AIInferenceEngine.__init__ creates self.model = TokenClassifier() with random weights. load_model() catches exceptions, logs error, but continues with uninitialized random weights silently.

[DEFECT-C] BiLSTM fed sequence length 1
  Location : legacy/senior-part1/ML_model/ai_model.py (Lines 69-70, 225-228)
  Evidence : predict() extracts single-token vector (shape [34]), calls .unsqueeze(0), and TokenClassifier.forward unsqueezes to (batch=1, seq_len=1, dim=34). A Bidirectional LSTM evaluated over length 1 provides zero temporal context.

[DEFECT-D] Low token diversity in 50k dataset
  Location : legacy/senior-part1/data/processed/token_security_dataset_v2.csv (CSV dataset (50,000 rows x 33 columns))
  Evidence : Total dataset rows: 50,000. Unique raw token values: 22,600 (45.2% unique). 54.8% duplicate synthetic tokens.

[DEFECT-E] Identical benchmark scores across Static/Dynamic/Pure_ML
  Location : legacy/senior-part1/carbon_analysis/performance/summary.json (Lines 1-59)
  Evidence : wscore is identical (0.3479) across all 3 modes. Precision, recall, and F1 (SAFE=0.8777, SUSPICIOUS=0.1667, MALICIOUS=0.3077) are 100% copy-pasted across Static, Dynamic, and Pure_ML.

=========================================================================================================
```

---

## Acceptance Command 5: Git Status Verification of Legacy Directory

### Command
```powershell
git status legacy/
```

### Exact Terminal Output
```
On branch master
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	legacy/README.md

nothing added to commit but untracked files present (use "git add" to track)
```

*(Note: The contents of `legacy/senior-part1/` and `legacy/senior-part2/` are completely tracked and unchanged in git. The only untracked item in `legacy/` is `legacy/README.md`, which was generated in Step 3 to record attribution and verified defects.)*

---

## Detailed Comparative Analysis: 6 Security Probes

| Probe # | Security Test Scenario | Input Code | Senior Tool Behavior | True Expected Behavior | SecureLex IDE (`apsla`) Solution |
|---|---|---|---|---|---|
| **1** | Web Taint to Command Injection | `name = request.args.get("q"); os.system("echo " + name)` | **FALSE NEGATIVE** (0 flagged). Attribute split `request.args` prevents taint initialization. | Flag `CRITICAL` Command Injection (`APS-PY-INJ-001`). Show path: `request.args.get -> name -> os.system`. | Full AST data-flow analysis resolving `Attribute` access and method calls. |
| **2** | Input Propagation to Sink | `u = input()`<br>`v = u; os.system(v)` | **CAUGHT** (flags `system` as MALICIOUS 0.92, `input`, `u`, `v` as SUSPICIOUS 0.65). | Flag `CRITICAL` Command Injection. Trace propagation: `u -> v -> os.system(v)`. | Intra-procedural assignment flow tracking with verified safe patch generation. |
| **3** | Sanitized Parameter Handling | `c = shlex.quote(u); os.system("echo " + c)` | **SAFE (accidental)** (no taint model exists for `shlex.quote` or `u`). | **PASS AS SAFE**. `shlex.quote` neutralizes shell metacharacters. | Recognizes recognized sanitizer functions and strips taint from output variables. |
| **4** | Safe List-form Subprocess | `subprocess.run(["ls","-l"])` | **FALSE POSITIVE** (flags `subprocess` as MALICIOUS 0.90 via naive keyword rule). | **PASS AS SAFE**. Direct execution of binary without shell interpolation is safe. | Checks argument types and absence of `shell=True` kwarg in AST call. |
| **5** | Trojan Source Bidi Override | `s = "ADM\u202E\u202DMIN"` | **FALSE NEGATIVE** (0 flagged). String literals bypassed Unicode character inspection. | Flag `HIGH` Trojan Source Injection (`APS-ALL-UNI-001`) with exact character offset. | Pre-lexer Unicode defense scanning raw character codepoints across all tokens. |
| **6** | Cyrillic Look-alike Builtin | `\u0435\u0445\u0435\u0441("echo 1")` | **WEAK** (flags SUSPICIOUS 0.40; misses dangerous execution intent). | Flag `CRITICAL` Obfuscated Dangerous Built-in (`APS-ALL-UNI-002`). | Skeleton confusable mapping recovers canonical ASCII `exec` before rule evaluation. |
