# SecureLex IDE (`apsla`) — Complete Project Index & Architecture Guide

> **Note for Claude**: This document was generated specifically to provide complete context
> of all files, folders, architecture, interfaces, and design decisions in this repository.

## 1. Executive Summary
- **Repository Name**: `securelex-ide` (`AI_POWERED_SECURE_LEXICAL_ANALYZER`)
- **Package Name**: `apsla` (AI-Powered Secure Lexical Analyzer)
- **Core Purpose**: High-performance, offline-capable developer IDE and static/hybrid security platform for **Python, JavaScript, Java, and C++**.
- **Key Innovations**:
  1. **Hybrid Detection Fusion**: Unifies AST/token rules + interprocedural taint flow + machine learning confidence + Unicode trojan defense.
  2. **Path-Level Explainability**: Traces `source -> propagate -> sanitizer_missing -> sink` with Monaco coordinates.
  3. **Verified Automated Fixes**: Fixes are applied to an isolated AST copy and re-analyzed; marked `verified` only if the vulnerability is eliminated without introducing new regressions.
  4. **AI Assistance**: Integrated with Groq AI provider with strict prompt injection detection and tool runner harnesses.
  5. **Rich Offline Web IDE**: React 18, TypeScript, Monaco Editor, dark/light themes, AST tree visualizer, Safety Lab, and Fix Workflow modal.

## 2. Directory Structure & Component Map
| Directory / File | Description |
|---|---|
| `src/apsla/` | Python backend package (FastAPI, core lexing, AST, taint analysis, ML, rule verifier, LLM agent) |
| `src/apsla/server/` | FastAPI application (`app.py`), Pydantic schemas (`schemas.py`), tool runners, security rate limits |
| `src/apsla/languages/` | Multi-language lexers, AST parsers, and token normalizers (Python, JS, Java, C++) |
| `src/apsla/security_v2.py` | 58 internal security rule definitions, registry builder, rule evaluation |
| `src/apsla/fixes/` | Fix synthesis (`generators.py`), AST patchers, `independent_verifier.py` (verification harness) |
| `src/apsla/agents/` | Agent planner, Groq provider (`provider_v2.py`), prompt injection classifier, execution budget |
| `src/apsla/ml/` | ML pipeline: token windowing (`windows.py`), feature extraction (`features.py`), inference, training scripts |
| `src/apsla/ml/artifacts/` | Model metadata (`meta.json`) for trained scikit-learn & gradient boosting models |
| `web/` | Modern React 18 + TypeScript + Vite frontend IDE |
| `web/src/ide/` | Complete IDE UI: `IDE.tsx`, `MonacoEditor.tsx`, Panels (Tokens, AST, Problems, Security, Safety Lab) |
| `web/src/ide/fix/` | Fix workflow state machine (`machine.ts`), modal (`FixWorkflowModal.tsx`), diff visualizer (`DiffPreview.tsx`) |
| `web/src/ide/ai/` | AI drawer (`BuildAIDrawer.tsx`), Explain panel (`AIExplainPanel.tsx`), Agent activity panel |
| `web/e2e/` | Playwright end-to-end tests for all workflows (Groq AI, failures, prompt injection, UI audit) |
| `tests/` | Comprehensive backend test suites: `unit/`, `security/`, `e2e/`, `golden/` fixtures |
| `scripts/` | Automation utilities: `check_all.py`, `build_all.py`, `golden.py`, `dev.py`, `package_for_claude.py` |
| `docs/` | Architecture specs, `PROJECT_SPEC.md`, `rules_catalogue.md`, `api_v2.md`, threat models |
| `reports/` | Test logs, phase evidence documents, samples matrix, benchmark findings |
| `examples/` | Test samples for all 4 languages: `valid/`, `lexical-errors/`, `syntax-errors/`, `security/`, `adversarial/` |
| `legacy/` | Historical reference code and baseline datasets (`senior-part1`, `senior-part2`) |

## 3. Core Architecture & Data Flow
```mermaid
graph TD
    UserCode[Source Code Input] --> Monaco[Monaco Editor / Web UI]
    Monaco --> API[/api/analyze]
    API --> Parser[Multi-Language Lexer & Parser]
    Parser --> AST[Unified AST & Token Spans]
    AST --> Rules[Security Rule Engine - 58 Rules]
    AST --> Taint[Interprocedural Taint Flow Engine]
    AST --> Trojan[Unicode & Homoglyph Detector]
    AST --> ML[Token Windowing & ML Anomaly Model]
    Rules & Taint & Trojan & ML --> Fusion[Calibrated Multi-Factor Confidence Score]
    Fusion --> Finding[Finding Object with Source-to-Sink Path]
    Finding --> FixHarness[Independent Fix Verifier]
    FixHarness --> VerifiedFix[Verified Clean Patch]
    VerifiedFix --> UI[Problems Panel & Fix Modal]
```

## 4. Key Endpoints (`src/apsla/server/app.py`)
- `POST /api/analyze`: Main pipeline. Analyzes code for syntax, lexical tokens, AST nodes, security findings, taint paths, and ML anomalies.
- `POST /api/fix/propose`: Proposes automated AST/regex fixes for a finding.
- `POST /api/fix/verify`: Runs candidate patch against the isolated verification harness.
- `POST /api/ai/explain`: Explains a vulnerability or code segment with Groq.
- `POST /api/ai/propose-fix`: AI agent proposes a semantic remediation with diff generation.
- `POST /api/ai/generate`: AI code generation / completion with safety filters.
- `POST /api/safety-lab/run`: Evaluates code against known adversarial attacks and injection vectors.
- `POST /api/feedback`: Submits user feedback (false positive / true positive) for active learning.

## 5. Machine Learning Models Manifest
Total trained model artifacts found: **4**

| Model ID | Language | Type | Dim | Macro F1 | Path |
|---|---|---|---|---|---|
| `separate_cpp_hist_gradient_boosting_20261021_162559` | cpp | hist_gradient_boosting | 45 | 0.7494 | `src/apsla/ml/artifacts/separate_cpp_hist_gradient_boosting_20261021_162559` |
| `separate_java_hist_gradient_boosting_20261021_162559` | java | hist_gradient_boosting | 45 | 0.6488 | `src/apsla/ml/artifacts/separate_java_hist_gradient_boosting_20261021_162559` |
| `separate_javascript_random_forest_20261021_162559` | javascript | random_forest | 45 | 0.5411 | `src/apsla/ml/artifacts/separate_javascript_random_forest_20261021_162559` |
| `separate_python_hist_gradient_boosting_20261021_162559` | python | hist_gradient_boosting | 45 | 0.6085 | `src/apsla/ml/artifacts/separate_python_hist_gradient_boosting_20261021_162559` |

*(See all individual `src/apsla/ml/artifacts/*/meta.json` files for full hyperparameter logs)*

## 6. Development & Quality Gate Commands
- **Backend Dev Server**: `python scripts/dev.py --api-only` (runs FastAPI on port 8000)
- **Frontend Dev Server**: `cd web && npm run dev` (runs Vite on port 5173)
- **Run All Quality Gates**: `python scripts/check_all.py` (lint, typecheck, unit tests, golden tests)
- **Run Unit Tests**: `pytest tests/unit/`
- **Run Security Tests**: `pytest tests/security/`
- **Run Golden Fixture Tests**: `python scripts/golden.py check`
- **Frontend Tests**: `cd web && npm test` (Vitest unit tests)
- **Frontend E2E Tests**: `cd web && npx playwright test`

