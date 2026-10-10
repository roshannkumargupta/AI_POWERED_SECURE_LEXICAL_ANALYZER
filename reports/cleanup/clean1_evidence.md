# CLEAN-1 Evidence Report

**Phase:** CLEAN-1 (Repository Hygiene & Golden Characterisation Safety Net)  
**Date:** October 10, 2026  
**Status:** Complete & Fully Verified  
**Branch:** `cleanup/clean-1`  

---

## 1. Metrics Before vs. After CLEAN-1

| Metric | Clean-0 (Before) | Clean-1 (After) | Delta | Notes |
|---|---|---|---|---|
| Tracked Files | 1,584 | 1,664 | +80 files | Added golden tests, screens, inventory, cleanup registers |
| Tracked Size (MB) | 91.30 MB | 98.38 MB | +7.08 MB | Normalized golden test fixtures + baseline screenshots |
| Ruff Violations (Strict) | 0 | 0 | 0 | Clean linter status maintained |
| Pytest Test Count | 789 passed | 789 passed | 0 | 100% test pass rate |
| Pytest Coverage | 84% | 84% | 0 | Coverage maintained |
| Golden Characterisation Tests | 0 | 8 test suites (Pass) | +8 suites | 100% match across 329 fixtures & 162 samples |
| Vitest Test Count (Frontend) | 133 passed | 133 passed | 0 | 19 test files passing |
| Vite Bundle Build | 12.14 MB | 12.14 MB | 0 | Zero external CDN requests |
| TypeScript Compiler Errors | 0 | 0 | 0 | Strict typecheck passing |

---

## 2. Commit List on `cleanup/clean-1`

| Commit Hash | Commit Message | Scope | Verification Status |
|---|---|---|---|
| `d5f5df3` | `clean: add golden characterisation tests` | Golden test harness (`scripts/golden.py`) and normalized baselines | PASS (tagged `clean-0`) |
| `b7b8b06` | `clean: repository inventory and directory purpose map` | Depth-3 folder tree purpose map, duplicate file scans, inventory script | PASS |
| `41586f3` | `clean: complete gitignore for build, test, editor, and bulky report outputs` | Comprehensive exclusion rules for Python, Node, Vite, editors, and reports | PASS |
| `35eff21` | `clean: clean up temporary training artifacts in test_phase10_ml` | Test sandbox isolation preventing temporary artifacts from polluting repo | PASS |

---

## 3. Deleted Files Summary

- **Tracked Production Files Deleted:** 0 (All tracked production files confirmed active with dynamic use risk prevention per rule 2).
- **Temporary Untracked Directories Cleaned:** 5 test-generated artifact folders in `src/apsla/ml/artifacts/` created during ephemeral test training.
- **Skipped Deletions:** Logged in `docs/cleanup/skipped.md` (legacy code, data corpora, ML weights, major dependency bumps).

---

## 4. Verification Check Confirmation

After every single commit, the full five-point acceptance check was run:
1. `ruff check .` -> **0 errors**
2. `pytest -q` -> **789 passed**
3. `python scripts/golden.py --check` -> **ALL GOLDEN TESTS PASSED (0 differences)**
4. `npm run test --prefix web` -> **133 passed (19 files)**
5. `npm run build --prefix web` -> **built successfully with zero external dependencies**

---

## 5. Artifacts and Registers Produced

- `reports/cleanup/baseline.md`: Safety baseline measurements across all tooling.
- `reports/cleanup/screens_before/`: Full UI frame captures across light and dark themes.
- `reports/cleanup/metrics_before.json`: Initial metric snapshot.
- `reports/cleanup/metrics_after_clean1.json`: Final CLEAN-1 metric snapshot.
- `docs/cleanup/inventory.md`: Complete directory inventory and purpose map.
- `docs/cleanup/dead_code_candidates.md`: Candidate audit with dynamic risk justification.
- `docs/cleanup/needs_decision.md`: Architectural decision register.
- `docs/cleanup/deleted_files.md`: Deletion tracking register.
- `docs/cleanup/skipped.md`: Skipped items tracking register.
