# Skipped Items Register — CLEAN-1

**Audit Date:** October 10, 2026  
**Scope:** Phase CLEAN-1  

---

## Skipped Modifications

| Item / Action | Rationale | Reversion / Guard |
|---|---|---|
| `legacy/` modifications | Strictly read-only per project spec and Phase CLEAN-1 rules | Untouched |
| `data/` and `src/apsla/ml/artifacts/` deletions | Runtime and evaluation assets protected by zero-touch policy | Untouched |
| Wholesale line ending conversion (`CRLF -> LF`) | Repository operates seamlessly across Windows and POSIX; mass re-normalization introduces diff noise without behavioral improvement | Postponed; .editorconfig and .gitattributes configure default LF for new files |
| Upgrades of major dependencies | Strictly forbidden during CLEAN-1 to maintain deterministic public contracts | Untouched |
