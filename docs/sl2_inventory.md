# SL2-0 Repository Inventory

Inventory is based on the checked-in source tree and direct source inspection on 2026-10-12. Legacy, `data/`, and `ml/artifacts/` were not edited.

## Backend modules

| Module | Responsibility |
|---|---|
| `src/apsla/pipeline.py` | Orchestrates lexer, Unicode recovery, rules, taint, ML fusion, diagnostics, fixes and analysis result. |
| `models.py`, `config.py`, `cwe.py`, `scoring.py`, `fusion.py`, `prioritization.py`, `suppression.py` | Pydantic domain model, configuration, CWE mapping, summaries/score, hybrid fusion, risk priority and ignore directives. |
| `lexing/` | Shared token protocol, token model, offset map and common lexical helpers. |
| `languages/` | Language plugin registry, profiles, hand-written parsers/StructTree, lexers, rules, fixes and syntax validation. |
| `rules/` | Generic rule base, registry, reusable helpers, Unicode checks and explanation text/catalogue. |
| `taint/` and `languages/python_lang/taint.py` | Shared lite taint engine/path model and Python AST flow-sensitive taint analysis. Java/JS/C++ plugins expose taint-lite/profile behavior through plugin code. |
| `unicode_defense/` | Confusable data, scanner, script detection, recovery. |
| `diagnostics/` | Lexical and language-specific syntax diagnostics. |
| `fixes/` | Fix candidate registry, text edits, import insertion, orchestration and shadow verifier. |
| `ml/` | Feature extraction, training/evaluation/calibration/inference/explainability, token windows and synthetic-data modules. Model files are stored under `src/apsla/ml/artifacts/`; contents were not opened or modified for this audit. |
| `agents/` | Seven compiler-stage agents, orchestration, planner variants, structured schemas, trace and prompt guard. |
| `agents/tools.py` | In-memory allowlisted tool registry (source comment says 14 registered capabilities). |
| `llm/` | Provider abstraction, null provider, local groq, OpenAI-compatible, groq and groq implementations. |
| `feedback/` | Local append-only feedback persistence. |
| `samples/` | Manifest, schema, loader, per-language samples, pending samples and senior comparison data. |
| `server/` | FastAPI app, API schemas, samples endpoint support and analysis LRU cache. |
| `cli.py`, `exceptions.py` | Typer CLI and domain exceptions. |

## HTTP API

Routes are registered under `/api` in `src/apsla/server/app.py`. Responses below name the Pydantic response model or direct JSON structure. `AnalysisResult` is `{language, filename, findings[], tokens[], summary, engine, trace[], agent_meta}`.

| Method/path | Request | Response |
|---|---|---|
| `GET /api/health` | none | `HealthResponse {status, version, ml_mode, ml_model_id}` |
| `GET /api/languages` | none | `LanguageInfo[] {id, display_name, extensions[], monaco_id}` |
| `POST /api/analyze` | `AnalyzeRequest {source, language?, filename?, options?}`; options `{fixes, ml, include_tokens, include_suppressed, agent}` | `AnalysisResult` |
| `GET /api/agent/status` | none | `{mode, groq_reachable, model, model_present, fallback_active, message}` |
| `POST /api/agent/analyze` | `AnalyzeRequest` | `AnalysisResult` |
| `POST /api/fix` | `{source, language, finding_id, fix_id, filename}` | `{new_source, diff, verification, new_result?}` |
| `POST /api/fix-all` | `{source, language, filename, allow_review}` | `{new_source, applied[], skipped[{fix_id,reason}], diff, score_before, score_after}` |
| `POST /api/feedback` | `{finding_fingerprint?, fingerprint?, rule_id, language, verdict, snippet, note, filename, line?}` | `{saved}` |
| `GET /api/samples` | query `language?`, `meta?` | `SampleItem[]`; metadata mode omits code. |
| `GET /api/samples/{sample_id}` | path ID | `SampleItem {id,title,category,language,filename,code,description,...optional catalogue metadata}` |
| `POST /api/ml/insights` | `{source, language, token_index}` | `{ml_mode, token_index?, token_text?, predicted_label?, probabilities?, feature_group_drops?}` |
| `GET /api/llm/status` | none | `{configured, provider}` |
| `POST /api/llm/fix` | `{source, finding_id, rule_id, language, start_line?, start_col?}` | `{fixes[], notes}`; fixes are verified/advice-only domain fixes. |
| `POST /api/llm/explain` | `{finding_id, rule_id, message?}` | `{explanation, error?}` |
| `GET /` and catch-all frontend routes | none | JSON health-ish root if no built frontend; otherwise static `FileResponse`; excluded from OpenAPI. |

Core schema types in `src/apsla/models.py`: `Range` (1-based UTF-16, end-exclusive), `TokenInfo`, `Token`, `Edit`, `VerificationResult`, `Fix`, `TaintPathStep`, `Finding`, `AnalysisSummary`, `EngineMetadata`, `AnalysisResult`. Server schemas add the request/response types listed above. Exact OpenAPI serialization is in `tests/golden/openapi_schema.json`.

## Languages, rules, parsers and taint

Runtime plugin introspection: `PYTHONPATH=src .\.venv\Scripts\python.exe -c "from apsla.languages.registry import get,list_plugins; get('python'); print([(p.id,len(p.rules())) for p in list_plugins()])"` returned `python 14`, `java 15`, `javascript 16`, `cpp 13` (**58 total plugin rule objects**, including language-local rules; this is not a claim about all generic or Unicode behavior).

| Language | Lexer | Parser/structure | Taint |
|---|---|---|---|
| Python | `languages/python_lang/lexer.py` | Python AST parser in plugin; native `ast.parse` | AST flow-sensitive in `python_lang/taint.py` |
| Java | `languages/java_lang/lexer.py` | Hand-written recursive descent `parser.py`; optional tree-sitter-java validation | Shared lite/profile-driven flow |
| JavaScript | `languages/javascript_lang/lexer.py` | Hand-written recursive descent `parser.py`; optional tree-sitter-javascript validation | Shared lite/profile-driven flow |
| C/C++ | `languages/cpp_lang/lexer.py` | Hand-written recursive descent `parser.py`; optional tree-sitter-cpp validation | Shared lite/profile-driven flow |

Python package discovery found tree-sitter core and cpp/java/javascript/python grammar packages. Grammar load/parse for every language was not verified successfully in this run; package availability is recorded separately from confirmed runtime behavior.

## Agents and planner

Agents: `LexerAgent`, `ParserAgent`, `SemanticAgent`, `TriageAgent`, `FixAgent`, `VerifierAgent`, `ExplainAgent`, coordinated by `AgentOrchestrator`. Planning has deterministic `RulesPlanner` and `LLMPlanner`. `guard.py` bounds and marks untrusted snippets; `schemas.py` validates structured decisions; `trace.py` records agent, stage, action, reasons, observation, decision source, timing and acceptance. Tool registry is in-memory and designed not to provide arbitrary file/process/network capabilities. groq is currently unreachable; live local-model behavior is therefore unavailable in this probe.

## ML artifacts and fixes

`src/apsla/ml/artifacts/` contains dated `joint_*`, `separate_*`, `random_forest_*`, gradient-boosted and BiLSTM artifact directories, with `.joblib` or `.pt` model files and `meta.json` metadata. Artifact bytes/metadata were deliberately not inspected in this audit. Runtime probe `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -c "from apsla.ml.infer import MLInferenceEngine; e=MLInferenceEngine(); print('mode='+e.get_mode()); print('model_id='+str(e.get_model_id()))"` returned `mode=on`, `model_id=separate_python_hist_gradient_boosting_20261009_214933`. This reports the default Python inference engine only; it does not certify every language artifact. Fix generation lives in language plugin `fixes.py`, `fixes/registry.py`, `fixes/engine.py`, with edit application and reanalysis in `fixes/verifier.py`; LLM suggestions go through the same verifier.

## Samples

Sample source and catalogue are in `src/apsla/samples/` with four language subfolders, `manifest.json`, `schema.py`, `loader.py`, and `pending/` for known analyzer gaps. `tests/fixtures/` contains expected finding fixtures; `web/e2e/fixtures/` contains UI edge cases. Manifest is the source of catalogue counts; no hand-entered count is used as runtime truth.

## Frontend

Vite/React/TypeScript app is in `web/`. `web/src/components/` includes editor, top bar, sidebar/flyouts, Problems, Tokens, taint path, explanations, diff/review modal, command palette, status and agent trace views. `web/src/state/workspace.ts` and `store.ts` hold workspace reducer/store; model helpers live in `web/src/model/`; API client is `web/src/api/client.ts`; hooks are under `web/src/hooks/`. Theme tokens and Monaco theme are under `web/src/theme/`. UI diagnostics/QA live in `web/qa/`, `web/e2e/`, and scripts `scripts/cdp_matrix_runner.mjs` / QA scripts.

## Test suites and observed status

Test sources include Python `tests/unit`, `tests/integration`, `tests/security`, fixtures/golden tests, and frontend Vitest files under `web/src/test` plus browser/CDP checks. A fresh `ruff check .` found one I001 error in pre-existing untracked `run_tests.py`; it was left untouched. A fresh full Pytest quiet run emitted no summary and stopped responding; interrupted with **no reliable test count**. Correctly scoped frontend Vitest command `npm.cmd test --prefix web -- --reporter=dot` passed 22 files and 148 tests. A direct runner invocation from repository root was mis-scoped and failed path/environment checks; it is not the project test result. Historical claims in `docs/STATE.md` are not substituted for these fresh results.
