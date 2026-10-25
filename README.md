# SecureLex IDE

SecureLex IDE is a local-first editor and static analysis workbench for Python, Java, JavaScript, and C/C++. Its deterministic lexer, parser integrations, rule checks, and patch verifier work without a paid AI service. Results describe the checks that actually ran; static analysis cannot prove a program safe.

## Architecture

- `web/`: React, TypeScript, Vite, Monaco, local fonts and Lucide icons. The workspace UI talks to FastAPI through `web/src/api/client.ts`.
- `src/apsla/server/`: FastAPI routes, request/response schemas, tool runner, resource limits and API compatibility routes.
- `src/apsla/languages/` and `src/apsla/lexing/`: language lexers, parsing, diagnostics and language-specific analysis.
- `src/apsla/rules/`, `src/apsla/taint/`, `src/apsla/security_v2.py`: deterministic security rules, taint tracking and result normalization.
- `src/apsla/agents/` and `src/apsla/llm/`: bounded provider/agent adapters. Model output is untrusted and does not replace deterministic checks.
- `src/apsla/fixes/`: rule or AI patch proposals and independent before/after verification.

For the current implementation status and known gaps, see [docs/STATE.md](docs/STATE.md), [docs/threat_model.md](docs/threat_model.md), and [reports/sl2_final_acceptance.md](reports/sl2_final_acceptance.md).

## Setup

Requires Python 3.12 or newer and Node.js/npm compatible with the lockfile. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
cd web
npm ci
cd ..
```

On macOS/Linux, activate `.venv` and use `python -m pip install -e '.[dev]'`. Optional compiler/analyzer tools are discovered from PATH and reported through `GET /api/capabilities`; install only the tools you intend to use. Supported adapters include g++/gcc/clang/clang++, javac, node, Ruff, Pyflakes, mypy, ESLint, Bandit, Semgrep, cppcheck and clang-tidy. Availability depends on the host and tool configuration. Semgrep uses only the repository-local `rules/semgrep/` rules when that adapter is configured.

### Start the backend and frontend

Use two terminals from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn apsla.server.app:app --app-dir src --host 127.0.0.1 --port 8000
```

```powershell
cd web
npm run dev -- --host 127.0.0.1
```

Open the Vite URL printed by the dev server (normally `http://127.0.0.1:5173`). Keep the API bound to loopback unless you configure an access token and understand the deployment boundary. `python scripts/dev.py` is the existing combined development launcher; its behavior is environment-dependent.

## Providers, consent and environment

Copy `.env.example` to `.env` and adjust values. Never commit real credentials. The lexical analyzer, token table, deterministic checks, and sample catalogue work entirely offline and do not need any LLM provider or paid API.

SecureLex IDE supports a fast hybrid AI architecture configured via `SECURELEX_AI_PROVIDER` (`auto`, `groq`, `ollama`, or `openai-compatible`):
- **Groq (Fast Cloud Layer):** When `GROQ_API_KEY` is present in `.env` or `SECURELEX_AI_PROVIDER=groq`, LLM tasks (explanations, AI fixes, code generation) route to high-speed models (`llama-3.1-8b-instant` for explanations, `llama-3.3-70b-versatile` for code generation/fixes). Because Groq is a remote provider, explicit user consent is required per session via Workbench Settings (`/api/ai/consent`).
- **Ollama (Local Offline Layer):** Local-only loopback provider (`127.0.0.1:11434`). Install Ollama separately and run `ollama pull qwen2.5-coder:3b`.
- **Auto-Routing:** When set to `auto` (default), SecureLex automatically uses Groq if `GROQ_API_KEY` is configured; otherwise it gracefully falls back to local Ollama.

Deterministic lexical analysis, tree-sitter parsing, rule execution, and patch verification **always** run 100% locally on the host, regardless of the active LLM provider.

Keep API keys in the server environment only. Never commit or leak API keys into frontend code, client responses, logs, or git. Check `/api/capabilities` and the title bar status badge (`groq · remote` or `ollama · local`) to inspect active provider status.

## Analysis by language

- **Python:** the Python lexer and standard-library AST parser; optional Ruff/Pyflakes and mypy diagnostics when installed.
- **Java:** the Java lexer and optional tree-sitter parser; `javac` semantic checks when available.
- **JavaScript:** the JavaScript lexer and optional tree-sitter parser; Node syntax checking and ESLint when installed.
- **C/C++:** the C/C++ lexer and optional tree-sitter parser; compiler syntax/semantic checks when g++ or clang++ is available.

Each result is limited to the stages and tools reported in that result. Missing tools are unavailable/incomplete checks, not a clean bill of health. The deterministic security rules and taint engine cover the rule families and source/sink pairs documented in [docs/rules_catalogue.md](docs/rules_catalogue.md) and [docs/limitations.md](docs/limitations.md). Coverage varies by language and syntax; findings require review.

## Fixes and verification

A proposal is a draft. Review its changed lines, assumptions and risks before applying. Applying uses the current source version and creates an undo point. The independent verifier reanalyzes before and after, reports Resolved, Remaining, Introduced and Unverified evidence, and explains which checks were unavailable. “Verified” applies only to the specified checks that ran; it is not a proof of correctness or a substitute for project tests. Undo restores the in-memory pre-patch buffer.

## Agent Safety Lab

Choose a scenario and language in the Safety Lab. Harness mode is deterministic and uses no model. Live mode requires a reachable configured provider; if unavailable, no simulated outcome is substituted. Inspect the observed event timeline, gateway decisions, independent before/after checks and assertions. Runs are not preloaded. See [docs/safety_lab.md](docs/safety_lab.md).

## Rules and token types

See [docs/token_types.md](docs/token_types.md) for token mapping. See [docs/adding_a_rule.md](docs/adding_a_rule.md) for the rule workflow and [docs/rules_catalogue.md](docs/rules_catalogue.md) for available rules. Contributions should add fixtures and tests with the rule, including safe counterparts.

## Tests and reproducibility

Install Python development dependencies and run `python scripts/check_all.py` from the root for the configured repository checks. Individual commands:

```powershell
.\.venv\Scripts\python.exe -m ruff check
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -m security -q
cd web; npm run test; npm run build; npm run e2e
```

The browser E2E command needs a running app and an available browser automation endpoint. A successful unit test or bundle build does not establish browser acceptance. Consult the phase evidence and final acceptance report for the commands that actually completed on this host.

## Limitations

Static analysis has false positives and false negatives, does not model every dependency/runtime/environment, and does not execute user code. External analyzers are optional; their absence reduces coverage. The Run/Test feature is unavailable without a sandbox. AI explanations and suggestions can be wrong; patch proposals must be reviewed and independently checked. Verification reports identify unverified checks and cannot establish all runtime behavior. Capabilities and resource protections have documented host-specific limits in the threat model and phase evidence.
