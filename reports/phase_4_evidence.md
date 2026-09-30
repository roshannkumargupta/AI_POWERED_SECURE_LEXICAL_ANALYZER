# Phase 4 Evidence Report: Reproducible Token ML Pipeline & Evaluation

**Project:** SecureLex IDE (`apsla`)
**Phase:** Phase 4 — Token-Level Machine Learning, 45-Dim Features, Calibration & External Evaluation
**Date:** September 30, 2026
**Status:** Complete & Fully Evaluated

---

## 1. Executive Summary

Phase 4 implements a leak-free token classification pipeline that predicts token security categories (`SAFE`, `SUSPICIOUS`, `MALICIOUS`) over sliding 9-token context windows.

### Architectural Commitments:
1. **Zero Feature Leakage:** Rule outputs and data-flow taint tracking flags are **never** used as ML input features.
2. **Strict Schema Integrity:** The 45-feature schema is cryptographically hashed (`FEATURE_SCHEMA_HASH: 313113ff1b1c3eaaef410590101e19a00c1721aa822f0c90e1034f7d06cc5b90`). If model weights or hashes diverge, ML mode is set to `"off"`.
3. **Group-Aware Splitting:** Grouped by `(language, template_family, snippet_id)` with zero template leakage between train, val, and test splits.
4. **Near-Duplicate De-duplication:** Normalized token window hashes appearing in validation or test splits were purged from training windows.
5. **No Internet & CPU Execution:** All training, calibration, and inference execute entirely on CPU with fixed seed 42.

---

## 2. Test Split Evaluation (Held-Out Test Set)

- **Test Access Timestamp:** `2026-09-30T07:27:03.796961+00:00` (Logged and touched once)
- **Dataset Hash:** `d4f93d6482681100...`
- **Total Test Tokens:** `1427`
- **Macro-F1:** **`0.6532`**
- **Macro-Precision:** **`0.6174`**
- **Macro-Recall:** **`0.7596`**

### Per-Class Test Performance:
| Class | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| `SAFE` | `0.9486` | `0.7402` | `0.8315` |
| `SUSPICIOUS` | `0.4751` | `0.6562` | `0.5512` |
| `MALICIOUS` | `0.4286` | `0.8824` | `0.5769` |

### Test Confusion Matrix:
```text
                  Pred SAFE    Pred SUSP    Pred MAL
Actual SAFE:       812          115          170         
Actual SUSP:       25           105          30          
Actual MAL:        19           1            150         
```

---

## 3. External Benchmark Evaluation (`data/external/python/`)

Evaluated on **42 realistic, hand-written snippets** representing real-world web handlers, system utilities, and cryptographic routines. These files were created by hand and **never appeared in synthetic training or validation pools**.

| Evaluator | Precision | Recall | F1-Score | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **APSLA Machine Learning Model** | **`0.6667`** | **`0.8333`** | **`0.7407`** | Contextual 9-token sliding window inference |
| **Deterministic Rules Baseline** | **`0.6970`** | **`0.9583`** | **`0.8070`** | Deterministic AST pattern rules |

---

## 4. Comparison with Senior Baseline (`summary.json`)

| Model / Source | Precision | Recall | F1 | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Senior Baseline** (`legacy/senior-part1`) | 0.9412 | 0.9412 | 0.9412 | *Not reproducible*: identical scores across all metrics due to an artificial synthetic artifact. |
| **APSLA Held-Out Test Split** | `0.6174` | `0.7596` | `0.6532` | Honest, leak-free evaluation on held-out test windows. |
| **APSLA External Hand-Written Set** | `0.6667` | `0.8333` | `0.7407` | Unseen hand-written real-world Python snippets. |

---

## 5. Honest Weak Spots & Limitations

In accordance with scientific rigor, we document observed limitations:
1. **Subtle Multi-Step Indirections:** When a dangerous sink is split across multiple wrapper functions or module attributes without immediate lexical indicators (e.g. `getattr(mod, 'exec')`), token-level context windows without interprocedural taint flow may assign lower probability to the call.
2. **Ambiguous Boundary Identifiers:** Tokens like `input` or `open` in benign contexts (e.g. `open_modal()`) occasionally exhibit elevated `SUSPICIOUS` probability if surrounded by string literals or quotes.
3. **Imbalance Between Safe and Malicious Tokens:** Even with balanced class weights, standard codebases consist of >90% `SAFE` tokens, meaning high precision requires careful thresholding ($	au$).
