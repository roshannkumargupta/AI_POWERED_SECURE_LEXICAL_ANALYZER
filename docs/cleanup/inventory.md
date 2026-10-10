# Repository Inventory — CLEAN-1

**Generated:** October 10, 2026  
**Scope:** Full repository audit excluding read-only `legacy/` modifications.  

---

## 1. Folder Tree (Depth 3) & Purpose

| Directory | Purpose |
|---|---|
| `.` (root) | Repository root workspace |
| `benchmarks/` | Throughput, latency, and carbon benchmarks placeholder |
| `data/` | Benchmark and training datasets (raw, provenance, external) |
| `data/external/` | Realistic multi-language external evaluation test snippets |
| `data/external/cpp/` | External C/C++ evaluation snippets |
| `data/external/java/` | External Java Spring/JPA evaluation snippets |
| `data/external/javascript/` | External JavaScript Node/Express evaluation snippets |
| `data/external/python/` | External Python Flask/Django evaluation snippets |
| `data/feedback/` | Append-only user false positive feedback records |
| `data/raw/` | Raw token and homoglyph CSV attack corpora |
| `data/sources/` | Unicode consortium lookalike/confusables source datasets |
| `docs/` | Architecture documentation, developer guides, and viva materials |
| `docs/api_samples/` | Saved raw JSON API response payloads across 4 languages |
| `docs/cleanup/` | CLEAN-1 repository hygiene and dead-code documentation |
| `docs/explained/` | Plain-English phase guides and 5 viva questions per phase |
| `docs/grammar/` | Grammar references and syntax specifications |
| `docs/plan/` | Preserved 16-week improvement plan documents |
| `docs/screenshots/` | Visual UI evidence captures across phases |
| `legacy/` | Strictly read-only historical senior prototype projects |
| `legacy/senior-part1/` | Senior Python analyzer prototype (W5_6, ML_model) |
| `legacy/senior-part2/` | Senior Java analyzer codebase (MIT licensed) |
| `reports/` | Automated verification evidence, matrices, and metrics reports |
| `reports/cleanup/` | CLEAN-1 safety baselines, metrics snapshots, and diffs |
| `reports/cleanup/screens_before/` | UI baseline screenshots captured at clean-0 |
| `reports/ui7/` | UI-7 responsive frame screenshots and QA matrix |
| `reports/ui9/` | UI-9 fix coverage and full E2E evaluation matrices |
| `scratch/` | Scratch investigation and helper test generation scripts |
| `scripts/` | Maintenance, build, verification, and evaluation automation scripts |
| `src/` | Production Python source code root |
| `src/apsla/` | AI-Powered Secure Lexical Analyzer (APSLA) core package |
| `src/apsla/agents/` | Phase 15 modular compiler stage agents and orchestrator |
| `src/apsla/diagnostics/` | Addictive lexical and syntax diagnostic engine |
| `src/apsla/feedback/` | Append-only false positive feedback store and loader |
| `src/apsla/fixes/` | Atomic text remediation, import injection, and verification engine |
| `src/apsla/languages/` | Language plugins and runtime checkable protocols |
| `src/apsla/languages/cpp_lang/` | C/C++ resilient lexer, parser, rules, and fixes |
| `src/apsla/languages/java_lang/` | Java resilient lexer, parser, rules, and fixes |
| `src/apsla/languages/javascript_lang/` | JavaScript resilient lexer, parser, rules, and fixes |
| `src/apsla/languages/python_lang/` | Python lexer, AST parser, taint, rules, and fixes |
| `src/apsla/lexing/` | Token definitions and bidirectional UTF-16 offset maps |
| `src/apsla/llm/` | Guarded local Ollama provider and optional LLM interfaces |
| `src/apsla/ml/` | 45-dim feature extractor, synthetic dataset engine, and models |
| `src/apsla/ml/artifacts/` | Trained ML model weights, temperature calibration, and schemas |
| `src/apsla/ml/synth/` | Multi-language synthetic grammar snippet generators |
| `src/apsla/rules/` | Language-agnostic rules, base classes, and explanations |
| `src/apsla/samples/` | Bundled 146-entry 4-language sample snippets and loader |
| `src/apsla/samples/cpp/` | C/C++ sample snippets |
| `src/apsla/samples/java/` | Java sample snippets |
| `src/apsla/samples/javascript/` | JavaScript sample snippets |
| `src/apsla/samples/pending/` | Catalogued samples with documented engine gaps |
| `src/apsla/samples/python/` | Python sample snippets |
| `src/apsla/server/` | FastAPI HTTP REST service, LRU caching, and SPA mounting |
| `src/apsla/taint/` | Data-flow taint analysis engines (AST and taint-lite) |
| `src/apsla/unicode_defense/` | Confusable mappings, bidi detection, and text recovery |
| `tests/` | Hermetic pytest and vitest test suites and fixtures |
| `tests/e2e/` | End-to-end catalogue and server test cases |
| `tests/fixtures/` | Test fixtures across languages and categories |
| `tests/fixtures/cpp/` | C/C++ vulnerable, safe, and parser fixtures |
| `tests/fixtures/java/` | Java vulnerable, safe, and parser fixtures |
| `tests/fixtures/javascript/` | JavaScript vulnerable, safe, and parser fixtures |
| `tests/fixtures/python/` | Python vulnerable, safe, and adversarial fixtures |
| `tests/golden/` | Normalized golden characterisation baseline JSON files |
| `tests/security/` | Security regression tests (agent tools allowlist, prompt injection) |
| `tests/unit/` | Unit test modules for lexers, parsers, rules, ML, fixes, and server |
| `third_party/` | Third-party licences and vendor attribution files |
| `web/` | React 18 + TypeScript + Monaco Editor SPA IDE frontend |
| `web/e2e/` | Frontend edge-case fixtures and Playwright/CDP runners |
| `web/public/` | Static web assets and pre-paint theme initializer script |
| `web/qa/` | Browser diagnostics and reference frame metrics readers |
| `web/src/` | Frontend React components, state, Monaco hooks, and theme system |
| `web/src/api/` | Typed HTTP API client and backend serializers |
| `web/src/components/` | Modular UI components (TopBar, Editor, Problems, Flyouts) |
| `web/src/editor/` | Monaco editor navigation and action controllers |
| `web/src/model/` | Frontend finding and token adaptation data models |
| `web/src/monaco/` | Monaco markers, decorations, code actions, and themes |
| `web/src/samples/` | Bundled fallback sample snippets |
| `web/src/state/` | Global state reducer, actions, and multi-file workspace store |
| `web/src/test/` | Vitest frontend component, guard, and utility unit tests |
| `web/src/theme/` | Semantic CSS variable tokens and dynamic Monaco themes |
| `web/src/tokens/` | Pure token security classification derivation engine |
| `web/src/utils/` | Diff computation, breadcrumbs, and UI scale utilities |

---

## 2. Tracked Artefacts & Stray Cache Files

**Total stray tracked artefacts found:** 0

*None. All build outputs, logs, and environments are properly excluded by git.*

---

## 3. Duplicate Files by SHA-256 Hash

**Duplicate file clusters (outside `legacy/`):** 91

- **SHA-256:** `e3b0c44298fc...` (25 copies):
  - `benchmarks/.gitkeep`
  - `docs/explained/.gitkeep`
  - `docs/screenshots/.gitkeep`
  - `reports/.gitkeep`
  - `scripts/.gitkeep`
  - `src/apsla/ml/artifacts/.gitkeep`
  - `src/apsla/ml/synth/.gitkeep`
  - `src/apsla/unicode_defense/data/.gitkeep`
  - `tests/e2e/.gitkeep`
  - `tests/fixtures/cpp/adversarial/.gitkeep`
  - `tests/fixtures/cpp/safe/.gitkeep`
  - `tests/fixtures/cpp/vulnerable/.gitkeep`
  - `tests/fixtures/java/adversarial/.gitkeep`
  - `tests/fixtures/java/safe/.gitkeep`
  - `tests/fixtures/java/vulnerable/.gitkeep`
  - `tests/fixtures/javascript/adversarial/.gitkeep`
  - `tests/fixtures/javascript/safe/.gitkeep`
  - `tests/fixtures/javascript/vulnerable/.gitkeep`
  - `tests/fixtures/python/adversarial/.gitkeep`
  - `tests/fixtures/python/safe/.gitkeep`
  - `tests/fixtures/python/vulnerable/.gitkeep`
  - `tests/integration/.gitkeep`
  - `tests/unit/.gitkeep`
  - `web/.gitkeep`
  - `web/e2e/fixtures/empty.py`
- **SHA-256:** `a9d541efc716...` (2 copies):
  - `docs/screenshots/ui7/app_1536x1022.jpg`
  - `reports/cleanup/screens_before/app_1536x1022.jpg`
- **SHA-256:** `a98ce8aec94f...` (2 copies):
  - `docs/screenshots/ui7/apply-diff_1280x720.jpg`
  - `reports/cleanup/screens_before/apply-diff_1280x720.jpg`
- **SHA-256:** `494d9d3b6f7b...` (2 copies):
  - `docs/screenshots/ui7/apply-diff_1366x768.jpg`
  - `reports/cleanup/screens_before/apply-diff_1366x768.jpg`
- **SHA-256:** `5355775e4e54...` (2 copies):
  - `docs/screenshots/ui7/apply-diff_1536x1022.jpg`
  - `reports/cleanup/screens_before/apply-diff_1536x1022.jpg`
- **SHA-256:** `47e943a57d16...` (2 copies):
  - `docs/screenshots/ui7/apply-diff_1536x864.jpg`
  - `reports/cleanup/screens_before/apply-diff_1536x864.jpg`
- **SHA-256:** `a40b6cccd6b3...` (2 copies):
  - `docs/screenshots/ui7/apply-diff_1920x1080.jpg`
  - `reports/cleanup/screens_before/apply-diff_1920x1080.jpg`
- **SHA-256:** `117766d61818...` (2 copies):
  - `docs/screenshots/ui7/empty_1280x720.jpg`
  - `reports/cleanup/screens_before/empty_1280x720.jpg`
- **SHA-256:** `f3dc6888a407...` (2 copies):
  - `docs/screenshots/ui7/empty_1366x768.jpg`
  - `reports/cleanup/screens_before/empty_1366x768.jpg`
- **SHA-256:** `c98a1a4d1202...` (2 copies):
  - `docs/screenshots/ui7/empty_1536x1022.jpg`
  - `reports/cleanup/screens_before/empty_1536x1022.jpg`
- **SHA-256:** `cb758be7e76d...` (2 copies):
  - `docs/screenshots/ui7/empty_1536x864.jpg`
  - `reports/cleanup/screens_before/empty_1536x864.jpg`
- **SHA-256:** `7b4dca345cd9...` (2 copies):
  - `docs/screenshots/ui7/empty_1920x1080.jpg`
  - `reports/cleanup/screens_before/empty_1920x1080.jpg`
- **SHA-256:** `9c30835bc185...` (2 copies):
  - `docs/screenshots/ui7/flyout_1280x720.jpg`
  - `reports/cleanup/screens_before/flyout_1280x720.jpg`
- **SHA-256:** `ae93cac4a935...` (2 copies):
  - `docs/screenshots/ui7/flyout_1366x768.jpg`
  - `reports/cleanup/screens_before/flyout_1366x768.jpg`
- **SHA-256:** `63498a92ee4b...` (2 copies):
  - `docs/screenshots/ui7/flyout_1536x1022.jpg`
  - `reports/cleanup/screens_before/flyout_1536x1022.jpg`
- **SHA-256:** `00067d846fd3...` (2 copies):
  - `docs/screenshots/ui7/flyout_1536x864.jpg`
  - `reports/cleanup/screens_before/flyout_1536x864.jpg`
- **SHA-256:** `ab18a9975955...` (2 copies):
  - `docs/screenshots/ui7/flyout_1920x1080.jpg`
  - `reports/cleanup/screens_before/flyout_1920x1080.jpg`
- **SHA-256:** `482723647287...` (2 copies):
  - `docs/screenshots/ui7/language-cpp_1536x1022.jpg`
  - `reports/cleanup/screens_before/language-cpp_1536x1022.jpg`
- **SHA-256:** `9b950d4895df...` (2 copies):
  - `docs/screenshots/ui7/language-java_1536x1022.jpg`
  - `reports/cleanup/screens_before/language-java_1536x1022.jpg`
- **SHA-256:** `c4de62394cf0...` (2 copies):
  - `docs/screenshots/ui7/language-javascript-error_1536x1022.jpg`
  - `reports/cleanup/screens_before/language-javascript-error_1536x1022.jpg`
- **SHA-256:** `f2498b72c120...` (2 copies):
  - `docs/screenshots/ui7/lexical_1280x720.jpg`
  - `reports/cleanup/screens_before/lexical_1280x720.jpg`
- **SHA-256:** `a0815f035002...` (2 copies):
  - `docs/screenshots/ui7/lexical_1366x768.jpg`
  - `reports/cleanup/screens_before/lexical_1366x768.jpg`
- **SHA-256:** `97876847e29f...` (2 copies):
  - `docs/screenshots/ui7/lexical_1536x1022.jpg`
  - `reports/cleanup/screens_before/lexical_1536x1022.jpg`
- **SHA-256:** `461b7f4d1406...` (2 copies):
  - `docs/screenshots/ui7/lexical_1536x864.jpg`
  - `reports/cleanup/screens_before/lexical_1536x864.jpg`
- **SHA-256:** `ea6baa9c7288...` (2 copies):
  - `docs/screenshots/ui7/lexical_1920x1080.jpg`
  - `reports/cleanup/screens_before/lexical_1920x1080.jpg`
- **SHA-256:** `68ee4cdaac28...` (2 copies):
  - `docs/screenshots/ui7/long_1280x720.jpg`
  - `reports/cleanup/screens_before/long_1280x720.jpg`
- **SHA-256:** `ee152fcb6062...` (2 copies):
  - `docs/screenshots/ui7/long_1366x768.jpg`
  - `reports/cleanup/screens_before/long_1366x768.jpg`
- **SHA-256:** `cad295fda0ab...` (2 copies):
  - `docs/screenshots/ui7/long_1536x1022.jpg`
  - `reports/cleanup/screens_before/long_1536x1022.jpg`
- **SHA-256:** `da34208e3b78...` (2 copies):
  - `docs/screenshots/ui7/long_1536x864.jpg`
  - `reports/cleanup/screens_before/long_1536x864.jpg`
- **SHA-256:** `df2d66714749...` (2 copies):
  - `docs/screenshots/ui7/long_1920x1080.jpg`
  - `reports/cleanup/screens_before/long_1920x1080.jpg`
- **SHA-256:** `e2d6813711b6...` (2 copies):
  - `docs/screenshots/ui7/security-ml-insights_1280x720.jpg`
  - `reports/cleanup/screens_before/security-ml-insights_1280x720.jpg`
- **SHA-256:** `1422d5ae15f5...` (2 copies):
  - `docs/screenshots/ui7/security-ml-insights_1366x768.jpg`
  - `reports/cleanup/screens_before/security-ml-insights_1366x768.jpg`
- **SHA-256:** `43e48697dc13...` (2 copies):
  - `docs/screenshots/ui7/security-ml-insights_1536x1022.jpg`
  - `reports/cleanup/screens_before/security-ml-insights_1536x1022.jpg`
- **SHA-256:** `7c5cfea43254...` (2 copies):
  - `docs/screenshots/ui7/security-ml-insights_1536x864.jpg`
  - `reports/cleanup/screens_before/security-ml-insights_1536x864.jpg`
- **SHA-256:** `966408636ccf...` (2 copies):
  - `docs/screenshots/ui7/security-ml-insights_1920x1080.jpg`
  - `reports/cleanup/screens_before/security-ml-insights_1920x1080.jpg`
- **SHA-256:** `e700019bdffe...` (2 copies):
  - `docs/screenshots/ui7/security-summary_1280x720.jpg`
  - `reports/cleanup/screens_before/security-summary_1280x720.jpg`
- **SHA-256:** `5c0749e3e07d...` (2 copies):
  - `docs/screenshots/ui7/security-summary_1366x768.jpg`
  - `reports/cleanup/screens_before/security-summary_1366x768.jpg`
- **SHA-256:** `fbcfa3971c74...` (2 copies):
  - `docs/screenshots/ui7/security-summary_1536x1022.jpg`
  - `reports/cleanup/screens_before/security-summary_1536x1022.jpg`
- **SHA-256:** `17daf6fabc37...` (2 copies):
  - `docs/screenshots/ui7/security-summary_1536x864.jpg`
  - `reports/cleanup/screens_before/security-summary_1536x864.jpg`
- **SHA-256:** `451b3d7ed8f6...` (2 copies):
  - `docs/screenshots/ui7/security-summary_1920x1080.jpg`
  - `reports/cleanup/screens_before/security-summary_1920x1080.jpg`
- **SHA-256:** `213b7b14fb26...` (2 copies):
  - `docs/screenshots/ui7/security-taint-path_1280x720.jpg`
  - `reports/cleanup/screens_before/security-taint-path_1280x720.jpg`
- **SHA-256:** `ffc1f7742a6c...` (2 copies):
  - `docs/screenshots/ui7/security-taint-path_1366x768.jpg`
  - `reports/cleanup/screens_before/security-taint-path_1366x768.jpg`
- **SHA-256:** `e7ee271542cf...` (2 copies):
  - `docs/screenshots/ui7/security-taint-path_1536x1022.jpg`
  - `reports/cleanup/screens_before/security-taint-path_1536x1022.jpg`
- **SHA-256:** `5fa79e924054...` (2 copies):
  - `docs/screenshots/ui7/security-taint-path_1536x864.jpg`
  - `reports/cleanup/screens_before/security-taint-path_1536x864.jpg`
- **SHA-256:** `862a35a2ccab...` (2 copies):
  - `docs/screenshots/ui7/security-taint-path_1920x1080.jpg`
  - `reports/cleanup/screens_before/security-taint-path_1920x1080.jpg`
- **SHA-256:** `01bb2c998a8e...` (2 copies):
  - `docs/screenshots/ui7/security-tokens_1280x720.jpg`
  - `reports/cleanup/screens_before/security-tokens_1280x720.jpg`
- **SHA-256:** `e7d0e41742f7...` (2 copies):
  - `docs/screenshots/ui7/security-tokens_1366x768.jpg`
  - `reports/cleanup/screens_before/security-tokens_1366x768.jpg`
- **SHA-256:** `93dc24caaacf...` (2 copies):
  - `docs/screenshots/ui7/security-tokens_1536x1022.jpg`
  - `reports/cleanup/screens_before/security-tokens_1536x1022.jpg`
- **SHA-256:** `963868e3df7b...` (2 copies):
  - `docs/screenshots/ui7/security-tokens_1536x864.jpg`
  - `reports/cleanup/screens_before/security-tokens_1536x864.jpg`
- **SHA-256:** `77865c76c76f...` (2 copies):
  - `docs/screenshots/ui7/security-tokens_1920x1080.jpg`
  - `reports/cleanup/screens_before/security-tokens_1920x1080.jpg`
- **SHA-256:** `91db785b4a55...` (12 copies):
  - `docs/screenshots/ui9/dark_advice_only.png`
  - `docs/screenshots/ui9/dark_analysed_state.png`
  - `docs/screenshots/ui9/dark_lexical_error.png`
  - `docs/screenshots/ui9/dark_review_fix_apply.png`
  - `docs/screenshots/ui9/dark_review_fixes_panel.png`
  - `docs/screenshots/ui9/dark_sample_loaded_edited.png`
  - `reports/cleanup/screens_before/dark_advice_only.png`
  - `reports/cleanup/screens_before/dark_analysed_state.png`
  - `reports/cleanup/screens_before/dark_lexical_error.png`
  - `reports/cleanup/screens_before/dark_review_fix_apply.png`
  - `reports/cleanup/screens_before/dark_review_fixes_panel.png`
  - `reports/cleanup/screens_before/dark_sample_loaded_edited.png`
- **SHA-256:** `c974bfb8b5b4...` (2 copies):
  - `docs/screenshots/ui9/dark_ml_off.png`
  - `reports/cleanup/screens_before/dark_ml_off.png`
- **SHA-256:** `b600b7843b3e...` (14 copies):
  - `docs/screenshots/ui9/light_advice_only.png`
  - `docs/screenshots/ui9/light_analysed_state.png`
  - `docs/screenshots/ui9/light_lexical_error.png`
  - `docs/screenshots/ui9/light_ml_off.png`
  - `docs/screenshots/ui9/light_review_fix_apply.png`
  - `docs/screenshots/ui9/light_review_fixes_panel.png`
  - `docs/screenshots/ui9/light_sample_loaded_edited.png`
  - `reports/cleanup/screens_before/light_advice_only.png`
  - `reports/cleanup/screens_before/light_analysed_state.png`
  - `reports/cleanup/screens_before/light_lexical_error.png`
  - `reports/cleanup/screens_before/light_ml_off.png`
  - `reports/cleanup/screens_before/light_review_fix_apply.png`
  - `reports/cleanup/screens_before/light_review_fixes_panel.png`
  - `reports/cleanup/screens_before/light_sample_loaded_edited.png`
- **SHA-256:** `aed2c851249e...` (2 copies):
  - `docs/screenshots/ui9/test_shot.png`
  - `reports/cleanup/screens_before/test_shot.png`
- **SHA-256:** `28b7ea934ab5...` (2 copies):
  - `reports/ui7/after/1536x1022-security-selected.json`
  - `reports/ui7/after/1536x1022-security-tokens.json`
- **SHA-256:** `2e426320aadb...` (2 copies):
  - `reports/ui7/before/1536x1022-security-taint.json`
  - `reports/ui7/before/1536x1022-security-tokens.json`
- **SHA-256:** `7c60d4c37cfd...` (2 copies):
  - `reports/ui7/metrics-1536x1022.json`
  - `reports/ui9/ref_metrics_ui9.json`
- **SHA-256:** `ff44ef8181dc...` (12 copies):
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261001_163417/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261002_122201/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261002_131455/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261002_194952/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261002_195407/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261003_054746/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261009_115719/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261009_133747/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261009_144532/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261009_213046/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261009_214100/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261009_214933/model.joblib`
- **SHA-256:** `8dfa7e971583...` (2 copies):
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261002_161420/model.joblib`
  - `src/apsla/ml/artifacts/joint_hist_gradient_boosting_20261002_161713/model.joblib`
- **SHA-256:** `7f222e83c1d4...` (12 copies):
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261001_163417/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261002_122201/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261002_131455/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261002_194952/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261002_195407/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261003_054746/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261009_115719/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261009_133747/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261009_144532/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261009_213046/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261009_214100/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261009_214933/model.joblib`
- **SHA-256:** `3e3c1b2275c5...` (2 copies):
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261002_161420/model.joblib`
  - `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261002_161713/model.joblib`
- **SHA-256:** `a784a1045272...` (12 copies):
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261001_163417/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261002_122201/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261002_131455/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261002_194952/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261002_195407/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261003_054746/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261009_115719/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261009_133747/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261009_144532/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261009_213046/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261009_214100/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261009_214933/model.joblib`
- **SHA-256:** `bc81aa386711...` (2 copies):
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261002_161420/model.joblib`
  - `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261002_161713/model.joblib`
- **SHA-256:** `f1baefa2115c...` (15 copies):
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261001_162207/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261001_163417/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_122201/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_131455/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_161420/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_161713/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_194952/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_195407/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261003_054746/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_115719/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_133747/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_144532/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_213046/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_214100/model.joblib`
  - `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_214933/model.joblib`
- **SHA-256:** `709f197ece19...` (12 copies):
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261001_163417/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261002_122201/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261002_131455/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261002_194952/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261002_195407/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261003_054746/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261009_115719/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261009_133747/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261009_144532/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261009_213046/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261009_214100/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261009_214933/model.joblib`
- **SHA-256:** `fddf53b0201a...` (2 copies):
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261002_161420/model.joblib`
  - `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261002_161713/model.joblib`
- **SHA-256:** `81019800205b...` (4 copies):
  - `src/apsla/samples/cpp/__init__.py`
  - `src/apsla/samples/java/__init__.py`
  - `src/apsla/samples/javascript/__init__.py`
  - `src/apsla/samples/python/__init__.py`
- **SHA-256:** `422c773fa0d5...` (2 copies):
  - `src/apsla/samples/cpp/cp-b08_compare_a_hard-coded_passwor.c`
  - `src/apsla/samples/pending/cp-b08_compare_a_hard-coded_passwor.c`
- **SHA-256:** `94660a821533...` (2 copies):
  - `src/apsla/samples/cpp/cp-i06_open_a_path_from_argv.c`
  - `src/apsla/samples/pending/cp-i06_open_a_path_from_argv.c`
- **SHA-256:** `e784027727f4...` (2 copies):
  - `src/apsla/samples/cpp/cp-i07_copy_using_pointer_sizeof.c`
  - `src/apsla/samples/pending/cp-i07_copy_using_pointer_sizeof.c`
- **SHA-256:** `2f5a41080e17...` (2 copies):
  - `src/apsla/samples/java/jv-i03_reflected_servlet_output.java`
  - `src/apsla/samples/pending/jv-i03_reflected_servlet_output.java`
- **SHA-256:** `43463018aaf2...` (2 copies):
  - `src/apsla/samples/javascript/js-a05_pass_host_through_a_helper.js`
  - `src/apsla/samples/pending/js-a05_pass_host_through_a_helper.js`
- **SHA-256:** `0e4951631c81...` (2 copies):
  - `src/apsla/samples/javascript/js-b03_schedule_a_string.js`
  - `src/apsla/samples/pending/js-b03_schedule_a_string.js`
- **SHA-256:** `f1009075d2ff...` (3 copies):
  - `tests/fixtures/python/adversarial/bidi_comment_spoof.expect.json`
  - `tests/fixtures/python/adversarial/bidi_string_literal.expect.json`
  - `tests/fixtures/python/adversarial/trojan_source_bidi.expect.json`
- **SHA-256:** `5768afbee8df...` (3 copies):
  - `tests/fixtures/python/adversarial/soft_hyphen_split.expect.json`
  - `tests/fixtures/python/adversarial/zero_width_joiner_ident.expect.json`
  - `tests/fixtures/python/adversarial/zero_width_space_ident.expect.json`
- **SHA-256:** `4f53cda18c2b...` (28 copies):
  - `tests/fixtures/python/safe/cmd_constant_os_system.expect.json`
  - `tests/fixtures/python/safe/cmd_sanitized_shlex.expect.json`
  - `tests/fixtures/python/safe/cmd_wrong_variable_safe.expect.json`
  - `tests/fixtures/python/safe/crypto_md5_usedforsecurity_false.expect.json`
  - `tests/fixtures/python/safe/crypto_sha256_safe.expect.json`
  - `tests/fixtures/python/safe/crypto_sha512_safe.expect.json`
  - `tests/fixtures/python/safe/eval_constant_math_safe.expect.json`
  - `tests/fixtures/python/safe/eval_literal_eval_safe.expect.json`
  - `tests/fixtures/python/safe/importlib_constant_module_safe.expect.json`
  - `tests/fixtures/python/safe/path_basename_sanitized_safe.expect.json`
  - `tests/fixtures/python/safe/path_secure_filename_safe.expect.json`
  - `tests/fixtures/python/safe/path_static_open_safe.expect.json`
  - `tests/fixtures/python/safe/pickle_safe_json_loads.expect.json`
  - `tests/fixtures/python/safe/random_non_sensitive_var.expect.json`
  - `tests/fixtures/python/safe/random_secrets_token_safe.expect.json`
  - `tests/fixtures/python/safe/requests_default_verify_safe.expect.json`
  - `tests/fixtures/python/safe/requests_verify_true_safe.expect.json`
  - `tests/fixtures/python/safe/secret_env_variable_safe.expect.json`
  - `tests/fixtures/python/safe/secret_placeholder_safe.expect.json`
  - `tests/fixtures/python/safe/sql_parameterized_executemany.expect.json`
  - `tests/fixtures/python/safe/sql_parameterized_query.expect.json`
  - `tests/fixtures/python/safe/static_import_statement_safe.expect.json`
  - `tests/fixtures/python/safe/subprocess_list_safe.expect.json`
  - `tests/fixtures/python/safe/subprocess_shell_false.expect.json`
  - `tests/fixtures/python/safe/template_render_static_safe.expect.json`
  - `tests/fixtures/python/safe/xss_markup_escape_safe.expect.json`
  - `tests/fixtures/python/safe/yaml_load_with_safeloader.expect.json`
  - `tests/fixtures/python/safe/yaml_safe_load.expect.json`
- **SHA-256:** `851b26fbbbf9...` (3 copies):
  - `tests/fixtures/python/vulnerable/cmd_injection_flask.expect.json`
  - `tests/fixtures/python/vulnerable/cmd_injection_fstring.expect.json`
  - `tests/fixtures/python/vulnerable/cmd_injection_os_popen.expect.json`
- **SHA-256:** `c5c443dab4db...` (2 copies):
  - `tests/fixtures/python/vulnerable/crypto_md5_hash.expect.json`
  - `tests/fixtures/python/vulnerable/crypto_sha1_hash.expect.json`
- **SHA-256:** `7418eb57142d...` (2 copies):
  - `tests/fixtures/python/vulnerable/dynamic_import_call.expect.json`
  - `tests/fixtures/python/vulnerable/dynamic_importlib_module.expect.json`
- **SHA-256:** `acd81c23a653...` (2 copies):
  - `tests/fixtures/python/vulnerable/eval_dynamic_input.expect.json`
  - `tests/fixtures/python/vulnerable/exec_dynamic_script.expect.json`
- **SHA-256:** `941493477794...` (2 copies):
  - `tests/fixtures/python/vulnerable/hardcoded_api_key.expect.json`
  - `tests/fixtures/python/vulnerable/hardcoded_password.expect.json`
- **SHA-256:** `1ec0cf6554c2...` (3 copies):
  - `tests/fixtures/python/vulnerable/marshal_loads_untrusted.expect.json`
  - `tests/fixtures/python/vulnerable/pickle_loads_untrusted.expect.json`
  - `tests/fixtures/python/vulnerable/shelve_open_untrusted.expect.json`
- **SHA-256:** `a0ba832f4969...` (2 copies):
  - `tests/fixtures/python/vulnerable/path_traversal_open.expect.json`
  - `tests/fixtures/python/vulnerable/path_traversal_send_file.expect.json`
- **SHA-256:** `a4cbe0710f8a...` (2 copies):
  - `tests/fixtures/python/vulnerable/requests_post_verify_false.expect.json`
  - `tests/fixtures/python/vulnerable/requests_verify_false.expect.json`
- **SHA-256:** `83bae87ccbca...` (3 copies):
  - `tests/fixtures/python/vulnerable/sql_injection_concat.expect.json`
  - `tests/fixtures/python/vulnerable/sql_injection_fstring.expect.json`
  - `tests/fixtures/python/vulnerable/sql_injection_percent.expect.json`
- **SHA-256:** `b47eb1dc3084...` (2 copies):
  - `tests/fixtures/python/vulnerable/subprocess_popen_shell.expect.json`
  - `tests/fixtures/python/vulnerable/subprocess_shell_true.expect.json`
- **SHA-256:** `047eb7d9303a...` (2 copies):
  - `tests/fixtures/python/vulnerable/template_injection_render.expect.json`
  - `tests/fixtures/python/vulnerable/xss_raw_markup.expect.json`
- **SHA-256:** `e7853364cbc8...` (2 copies):
  - `tests/fixtures/python/vulnerable/weak_random_secret.expect.json`
  - `tests/fixtures/python/vulnerable/weak_random_token.expect.json`
- **SHA-256:** `756f8facbc45...` (2 copies):
  - `tests/fixtures/python/vulnerable/yaml_load_unsafe.expect.json`
  - `tests/fixtures/python/vulnerable/yaml_unsafe_load_call.expect.json`
- **SHA-256:** `582b68a9c6d1...` (2 copies):
  - `tests/golden/fixtures_ml_off.json`
  - `tests/golden/fixtures_ml_on.json`
- **SHA-256:** `455b5a9684ef...` (2 copies):
  - `tests/golden/samples_ml_off.json`
  - `tests/golden/samples_ml_on.json`

---

## 4. Empty Files and Directories

**Empty (0-byte) tracked files:** 31

- `benchmarks/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `docs/explained/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `docs/screenshots/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `legacy/senior-part1/ML_model/__init__.py` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `legacy/senior-part1/W5_6/__init__.py` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `legacy/senior-part1/carbon_analysis/__init__.py` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `legacy/senior-part1/data/processed/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `legacy/senior-part1/frontend/__init__.py` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `legacy/senior-part1/models/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `reports/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `scripts/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `src/apsla/ml/artifacts/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `src/apsla/ml/synth/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `src/apsla/unicode_defense/data/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/e2e/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/cpp/adversarial/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/cpp/safe/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/cpp/vulnerable/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/java/adversarial/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/java/safe/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/java/vulnerable/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/javascript/adversarial/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/javascript/safe/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/javascript/vulnerable/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/python/adversarial/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/python/safe/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/fixtures/python/vulnerable/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/integration/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `tests/unit/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `web/.gitkeep` (intentional package or git anchor if `__init__.py` or `.gitkeep`)
- `web/e2e/fixtures/empty.py` (intentional package or git anchor if `__init__.py` or `.gitkeep`)

**Empty directories:** 64

- `.hypothesis/examples/`
- `.pytest-s1-full/`
- `.pytest-s2-run/`
- `docs/cleanup/`
- `docs/screenshots/after_ui1/`
- `reports/.pytest-cov/test_analyze_api_round_trip_in0/`
- `reports/.pytest-cov/test_analyze_auto_detect_langu0/`
- `reports/.pytest-cov/test_analyze_caching0/`
- `reports/.pytest-cov/test_analyze_flask_fixture0/`
- `reports/.pytest-cov/test_analyze_payload_too_large0/`
- `reports/.pytest-cov/test_analyze_timeout_5040/`
- `reports/.pytest-cov/test_analyze_unknown_language_0/`
- `reports/.pytest-cov/test_clear_feedback_file0/`
- `reports/.pytest-cov/test_cors_headers0/`
- `reports/.pytest-cov/test_fix_all_endpoint0/`
- `reports/.pytest-cov/test_fix_endpoint_errors0/`
- `reports/.pytest-cov/test_fix_endpoint_happy_path_a0/`
- `reports/.pytest-cov/test_health_endpoint_live0/`
- `reports/.pytest-cov/test_health_endpoint_ml_off0/empty_artifacts/`
- `reports/.pytest-cov/test_internal_error_does_not_l0/`
- `reports/.pytest-cov/test_languages_endpoint0/`
- `reports/.pytest-cov/test_missing_model_fallback_is0/`
- `reports/.pytest-cov/test_ml_insights_endpoint0/`
- `reports/.pytest-cov/test_samples_endpoint0/`
- `reports/.pytest-cov/test_save_and_load_feedback0/`
- `reports/.pytest-cov/test_snippet_truncated_to_400_0/`
- `reports/.pytest-cov/test_static_root_fallback0/`
- `reports/.pytest-tmp/test_analyze_auto_detect_langu0/`
- `reports/.pytest-tmp/test_analyze_caching0/`
- `reports/.pytest-tmp/test_analyze_flask_fixture0/`
- `reports/.pytest-tmp/test_analyze_payload_too_large0/`
- `reports/.pytest-tmp/test_analyze_timeout_5040/`
- `reports/.pytest-tmp/test_analyze_unknown_language_0/`
- `reports/.pytest-tmp/test_cors_headers0/`
- `reports/.pytest-tmp/test_fix_all_endpoint0/`
- `reports/.pytest-tmp/test_fix_endpoint_errors0/`
- `reports/.pytest-tmp/test_fix_endpoint_happy_path_a0/`
- `reports/.pytest-tmp/test_health_endpoint_live0/`
- `reports/.pytest-tmp/test_health_endpoint_ml_off0/empty_artifacts/`
- `reports/.pytest-tmp/test_internal_error_does_not_l0/`
- `reports/.pytest-tmp/test_languages_endpoint0/`
- `reports/.pytest-tmp/test_missing_model_fallback_is0/`
- `reports/.pytest-tmp/test_ml_insights_endpoint0/`
- `reports/.pytest-tmp/test_samples_endpoint0/`
- `reports/.pytest-tmp/test_static_root_fallback0/`
- `reports/.pytest-ui7/test_analyze_api_round_trip_in0/`
- `reports/.pytest-ui7/test_analyze_auto_detect_langu0/`
- `reports/.pytest-ui7/test_analyze_caching0/`
- `reports/.pytest-ui7/test_analyze_flask_fixture0/`
- `reports/.pytest-ui7/test_analyze_payload_too_large0/`
- `reports/.pytest-ui7/test_analyze_timeout_5040/`
- `reports/.pytest-ui7/test_analyze_unknown_language_0/`
- `reports/.pytest-ui7/test_cors_headers0/`
- `reports/.pytest-ui7/test_fix_all_endpoint0/`
- `reports/.pytest-ui7/test_fix_endpoint_errors0/`
- `reports/.pytest-ui7/test_fix_endpoint_happy_path_a0/`
- `reports/.pytest-ui7/test_health_endpoint_live0/`
- `reports/.pytest-ui7/test_health_endpoint_ml_off0/empty_artifacts/`
- `reports/.pytest-ui7/test_internal_error_does_not_l0/`
- `reports/.pytest-ui7/test_languages_endpoint0/`
- `reports/.pytest-ui7/test_missing_model_fallback_is0/`
- `reports/.pytest-ui7/test_ml_insights_endpoint0/`
- `reports/.pytest-ui7/test_samples_endpoint0/`
- `reports/.pytest-ui7/test_static_root_fallback0/`

---

## 5. Large Files (> 1 MB)

**Total files > 1 MB:** 16

| Path | Size (MB) | Category | Action |
|---|---|---|---|
| `src/apsla/ml/artifacts/random_forest_20260929_221524/model.joblib` | 1.56 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261001_162207/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261001_163417/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_122201/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_131455/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_161420/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_161713/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_194952/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261002_195407/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261003_054746/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_115719/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_133747/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_144532/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_213046/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_214100/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |
| `src/apsla/ml/artifacts/separate_javascript_random_forest_20261009_214933/model.joblib` | 1.2 MB | Model weights | Preserve (Required runtime artifact) |

---

## 6. Line Endings & Encodings

- **Files with CRLF line endings:** 734
- **Files with Mixed line endings:** 6
- **Non-UTF-8 / Binary files:** 246 (images, model weights, binaries)
- **Executable tracked files (mode 100755):** 0


---

## 7. Secret-Like Strings Audit

**Suspicious string patterns outside test fixtures/samples:** 27

- `data/external/java/ext_15_hardcoded_aws_credentials.java`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `data/external/python/ext_15_hardcoded_aws_key.py`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `docs/rules_catalogue.md`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `docs/rules_catalogue.md`: Generic Hardcoded Secret (`apiKey = "super_secret_key_12345"...`)
- `docs/rules_catalogue.md`: Generic Hardcoded Secret (`apiKey = "AIzaSyD-sample-key"...`)
- `docs/rules_catalogue.md`: Generic Hardcoded Secret (`API_KEY = "AKIAIOSFODNN7EXAMPLE"...`)
- `scratch/gen_js_fixtures.py`: AWS Access Key ID (`AKIA1234567890ABCDEF...`)
- `scratch/gen_js_fixtures.py`: Generic Hardcoded Secret (`API_KEY = "AKIA1234567890ABCDEF12"...`)
- `scratch/gen_js_fixtures.py`: Generic Hardcoded Secret (`apiKey = "YOUR_API_KEY_HERE"...`)
- `scripts/build_external_benchmarks.py`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `scripts/create_external_dataset.py`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `scripts/generate_fixtures.py`: Generic Hardcoded Secret (`api_key = "ak_live_8f3a9e1b2c4d5e6f7a8b9...`)
- `scripts/sample_catalogue_s2.py`: Generic Hardcoded Secret (`password = "demo-credential-value-2026"...`)
- `scripts/sample_catalogue_s2.py`: Generic Hardcoded Secret (`api_key = "A7kQ9mP2xR5vT8wY3zB6"...`)
- `scripts/sample_catalogue_s2.py`: Generic Hardcoded Secret (`password = "demo-credential-value-2026"...`)
- `scripts/sample_catalogue_s2.py`: Generic Hardcoded Secret (`password = "demo-credential-value-2026"...`)
- `scripts/sample_catalogue_s2.py`: Generic Hardcoded Secret (`api_key = "A7kQ9mP2xR5vT8wY3zB6"...`)
- `src/apsla/ml/synth/cpp.py`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `src/apsla/ml/synth/cpp.py`: Generic Hardcoded Secret (`API_KEY = "sk_live_51M000000000000000000...`)
- `src/apsla/ml/synth/java.py`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `src/apsla/ml/synth/javascript.py`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `src/apsla/ml/synth/javascript.py`: GitHub Personal Access Token (`ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890...`)
- `src/apsla/ml/synth/python.py`: Generic Hardcoded Secret (`SECRET_KEY = "shhhhh_this_is_a_very_secr...`)
- `src/apsla/rules/explanations.py`: AWS Access Key ID (`AKIAIOSFODNN7EXAMPLE...`)
- `src/apsla/rules/explanations.py`: Generic Hardcoded Secret (`API_KEY = "AKIAIOSFODNN7EXAMPLE"...`)
- `src/apsla/rules/explanations.py`: Generic Hardcoded Secret (`apiKey = "AIzaSyD-sample-key"...`)
- `src/apsla/rules/explanations.py`: Generic Hardcoded Secret (`apiKey = "super_secret_key_12345"...`)

---

## 8. Large Generated Outputs in `reports/`

| Report File | Size |
|---|---|
| `reports/cleanup/screens_before/security-ml-insights_1920x1080.jpg` | 142.44 KB |
| `reports/cleanup/screens_before/security-taint-path_1920x1080.jpg` | 142.31 KB |
| `reports/cleanup/screens_before/security-tokens_1920x1080.jpg` | 138.77 KB |
| `reports/cleanup/screens_before/security-taint-path_1536x1022.jpg` | 137.53 KB |
| `reports/cleanup/screens_before/security-ml-insights_1536x1022.jpg` | 136.37 KB |
| `reports/cleanup/screens_before/security-summary_1920x1080.jpg` | 134.0 KB |
| `reports/cleanup/screens_before/security-tokens_1536x1022.jpg` | 132.3 KB |
| `reports/cleanup/screens_before/app_1536x1022.jpg` | 131.93 KB |
| `reports/cleanup/screens_before/language-java_1536x1022.jpg` | 129.57 KB |
| `reports/cleanup/screens_before/lexical_1920x1080.jpg` | 129.42 KB |
| `reports/cleanup/screens_before/security-summary_1536x1022.jpg` | 126.27 KB |
| `reports/cleanup/screens_before/security-taint-path_1536x864.jpg` | 123.96 KB |
| `reports/cleanup/screens_before/security-ml-insights_1536x864.jpg` | 123.48 KB |
| `reports/cleanup/screens_before/flyout_1920x1080.jpg` | 119.68 KB |
| `reports/cleanup/screens_before/security-tokens_1536x864.jpg` | 117.95 KB |