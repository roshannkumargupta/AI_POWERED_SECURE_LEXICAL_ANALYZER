# Deleted Files Register — CLEAN-1

**Audit Date:** October 10, 2026  
**Scope:** Phase CLEAN-1  

---

## 1. Tracked Production Files Deleted

| File Path | Reason | Evidence 1 | Evidence 2 | Restore Commit Hash |
|---|---|---|---|---|
| *(None)* | All tracked files verified active | Dependency graph & test suite | Golden characterisation test suite | N/A |

*Note: Per rule 2, no files were deleted without verified dual proof of non-use. All core modules, plugins, and test suites are actively referenced.*

---

## 2. Temporary / Untracked Artifacts Cleaned

| Path | Type | Action | Justification |
|---|---|---|---|
| `src/apsla/ml/artifacts/*_20261010_085239/` | Ephemeral test training outputs | Deleted from working tree | Generated dynamically during `test_tiny_e2e_training_run_under_3_minutes` test run; test now cleans them up in `finally` block |
