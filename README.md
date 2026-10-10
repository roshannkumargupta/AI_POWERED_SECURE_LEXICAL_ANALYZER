# SecureLex IDE (`apsla`)

SecureLex IDE is an intelligent, multi-language secure lexical analyzer and IDE-style static/hybrid code analysis platform supporting Python, Java, JavaScript, and C++.

## Features

- **Hybrid Detection**: Seamless fusion of deterministic rule checking, real taint data-flow analysis, and ML confidence scoring.
- **Unicode Defense**: Detection and mitigation of Trojan Source (bidi overrides), zero-width characters, homoglyphs, and confusables.
- **Fix & Verify Engine**: Generates syntax-aware remediation patches and re-analyzes transformed code to verify that vulnerabilities disappear without introducing regressions.
- **Offline & Cross-Platform**: Self-contained architecture without runtime CDN requirements, compatible with Windows, macOS, and Linux.

## Quickstart

```bash
# Set up environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .

# CLI analysis
apsla analyze <path-to-source-file>
```

## Documentation

Comprehensive project documentation is indexed in **[docs/README.md](docs/README.md)**:
- **[System Architecture](docs/architecture.md)** & **[Threat Model](docs/threat_model.md)**
- **[Security Rules Catalogue](docs/rules_catalogue.md)** (58 rules across 4 languages)
- **[REST API Contract](docs/api.md)**
- **[End-User Guide](docs/user_guide.md)** & **[Samples Guide](docs/samples_guide.md)**
- **[UI QA Protocol](docs/ui_qa_protocol.md)** & **[Checklist](docs/ui_qa_checklist.md)**
- **[Phase Retrospectives](docs/explained/)** & **[Master State](docs/STATE.md)**

## How to run the UI QA

Start the API and Vite app with `python scripts/dev.py` (the frontend is at `http://127.0.0.1:5173/`). Append `?ui7qa=1` to print read-only diagnostics at startup; press **Ctrl+Shift+Alt+F9** after changing the sample, tab, or viewport. See [docs/ui_qa_protocol.md](docs/ui_qa_protocol.md) for the viewport/state checklist and the `npm.cmd test`, build, ruff, pytest, and sample-verification commands. Browser E2E is manual in this checkout because Playwright is not installed.

## Agentic Layer & Local LLM Setup (Phase 15)

SecureLex IDE features an agentic compiler orchestration layer that navigates through lexical, syntax, semantic, triage, fix, verify, and explain stages. The deterministic compiler tools remain the sole source of truth; agents only choose which tool to call next and explain why.

### Agent Modes (`APSLA_AGENT_MODE`)
Configure the mode via your `.env` file or environment variables:
- `APSLA_AGENT_MODE=off` (Default): Traditional deterministic pipeline (Phase 14 baseline).
- `APSLA_AGENT_MODE=rules`: Agentic loop guided by deterministic `RulesPlanner`. Zero LLM overhead, 100% reproducible.
- `APSLA_AGENT_MODE=local`: Agentic loop guided by local Ollama model (`qwen2.5-coder:3b`).

### Setting Up Local AI (Ollama)
SecureLex IDE uses a local model exclusively. No external API keys, no cloud calls, and **zero outbound network calls** (`outbound network calls: 0`). The provider strictly enforces loopback connections (`127.0.0.1`, `localhost`, `::1`).

1. **Install Ollama**: Download from [ollama.com](https://ollama.com)
2. **Pull the model**:
   ```bash
   ollama pull qwen2.5-coder:3b
   ```
3. **Start Ollama service**:
   ```bash
   ollama serve
   ```
4. **Configure `.env`**:
   ```ini
   APSLA_AGENT_MODE=local
   APSLA_LOCAL_URL=http://127.0.0.1:11434
   APSLA_LOCAL_MODEL=qwen2.5-coder:3b
   APSLA_AGENT_MAX_STEPS=12
   APSLA_AGENT_MAX_LLM_CALLS=8
   APSLA_AGENT_TIMEOUT_S=60
   ```
5. **Evaluate or run**:
   ```bash
   python scripts/agent_eval.py --modes off rules local
   ```

## Privacy & Security

SecureLex IDE operates 100% locally and offline. No telemetry, code, or tokens are transmitted outside your local machine. In Phase 15, all LLM planning calls are restricted to loopback interfaces, prompt injection attacks in scanned code are sanitized and isolated between untrusted delimiters, and automated fixes must pass deterministic AST verification before being marked verified.
