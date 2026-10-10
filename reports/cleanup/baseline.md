# Baseline Verification Report — CLEAN-1

**Date:** October 10, 2026  
**Branch:** `cleanup/clean-1`  
**Base Commit:** `650acbd` (`feat(phase-15): local agentic compiler layer, recursive-descent StructTree parsers, 14-tool execution registry, prompt guard, and timeline trace UI`)  

---

## 1. Python Linter & Formatter (`ruff`)

Command:
```bash
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

Output:
```text
All checks passed!
268 files already formatted
```

Status: **PASS (100% clean)**

---

## 2. Python Test Suite & Coverage (`pytest`)

### Functional Test Suite (without coverage tracing)
Command:
```bash
.\.venv\Scripts\pytest.exe -q --basetemp=reports/.pytest-run
```
Output:
```text
........................................................................ [  9%]
........................................................................ [ 18%]
........................................................................ [ 27%]
........................................................................ [ 37%]
........................................................................ [ 46%]
........................................................................ [ 55%]
........................................................................ [ 64%]
........................................................................ [ 74%]
........................................................................ [ 83%]
........................................................................ [ 92%]
.........................................................                [100%]
789 passed
```
Status: **PASS (100% clean, 0 failures)**

### Coverage Measurement
Command:
```bash
.\.venv\Scripts\pytest.exe -q --cov=src/apsla --cov-report=term --basetemp=reports/.pytest-cov
```
Output Summary:
```text
TOTAL lines: 13,211
Covered lines: 11,100
Line coverage: 84%
Pre-existing advisory: tests/unit/test_unicode_defense.py::test_200kb_file_processes_under_two_seconds
(Coverage tracing profiling overhead adds ~0.2s to execution time, causing the strict 2.0s benchmark test to fail under coverage mode only).
```
Status: **84% line coverage (target >= 80% met)**

---

## 3. Web Frontend Test Suite (`vitest`)

Command:
```bash
npm.cmd test --prefix web
```

Output:
```text
✓ src/test/workspace.test.ts (4 tests)
✓ src/test/applyEdits.test.ts (4 tests)
✓ src/test/offsets.test.ts (4 tests)
✓ src/test/markers.test.ts (2 tests)
✓ src/test/ui7-contrast.test.ts (2 tests)
✓ src/test/ui2-utils.test.ts (53 tests)
✓ src/test/ui8-theme.test.ts (4 tests)
✓ src/test/tokens-derive.test.ts (5 tests)
✓ src/test/ui5-adapt.test.ts (14 tests)
✓ src/test/ui9-guards.test.ts (12 tests)
✓ src/test/samples-s3.test.tsx (4 tests)
✓ src/test/agent-trace.test.tsx (3 tests)
✓ src/test/tokens-panel.test.tsx (4 tests)
✓ src/test/ui6-components.test.tsx (4 tests)
✓ src/test/ui2-components.test.tsx (6 tests)
✓ src/test/ui7-guards.test.ts (2 tests)
✓ src/test/severity.test.ts (2 tests)
✓ src/test/diff.test.ts (2 tests)
✓ src/test/debounce.test.ts (2 tests)

Test Files  19 passed (19)
Tests       133 passed (133)
```
Status: **PASS (100% clean)**

---

## 4. Frontend Production Build (`vite build`)

Command:
```bash
npm.cmd run build --prefix web
```

Output Summary:
```text
✓ built in 57.25s
Production bundle generated under web/dist/:
- dist/index.html (5.24 kB)
- dist/assets/index-*.js (3,630.27 kB | gzip: 949.60 kB)
- Monaco language chunks and font assets bundled offline with zero CDN dependencies
```
Status: **PASS (100% clean)**

---

## 5. Sample Catalogue & Fix Matrix (`verify_samples.py`)

Command:
```bash
.\.venv\Scripts\python.exe scripts/verify_samples.py
```

Output:
```text
146 catalogue entries; 136 shipped; 136 passed; 10 pending; 0 failures
```
Status: **PASS (100% clean)**
