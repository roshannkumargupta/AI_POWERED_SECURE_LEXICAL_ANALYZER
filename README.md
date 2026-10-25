# SecureLex IDE

SecureLex IDE is a modern, local-first code security analyzer and developer workbench for **Python, JavaScript, Java, and C/C++**. It combines deterministic multi-language lexing, AST parsing, interprocedural taint flow analysis, Trojan Source Unicode detection, machine-learning anomaly scoring, and independent fix verification into an integrated developer environment.

---

## Key Capabilities

- **Deterministic Multi-Language Security**: 58+ built-in security rules covering OWASP Top 10, CWE vulnerabilities, and language-specific injection vectors.
- **Interprocedural Taint Tracking**: Traces taint flow from sources (`request.args`, `argv`, `cin`, `getParameter`) through propagators to dangerous sinks (`execute`, `eval`, `system`, `strcpy`).
- **Trojan Source & Unicode Defense**: Detects bidirectional override attacks (CVE-2021-42574), homoglyphs, and invisible confusable characters before code compiles.
- **Verified Automated Fixes**: Proposed patches are applied to an isolated sandbox and re-analyzed before presentation. Patches are marked "Verified" only when the target vulnerability is eliminated without regressions.
- **Local-First Architecture**: Core lexical analysis, AST parsing, security rules, and patch verification run completely offline on your host machine with zero outbound network calls.
- **AI-Assisted Explanations & Repair**: Optional Groq-powered AI assistance for explaining findings, generating patches, and building code, requiring explicit user consent.

---

## Requirements

- **Python**: 3.12 or newer
- **Node.js**: 18.x or newer (and `npm`)
- **Git**

---

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd securelex-ide
```

### 2. Set up the Python virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```
*(On macOS/Linux: `source .venv/bin/activate && pip install -e ".[dev]" `)*

### 3. Set up the Web Frontend
```bash
cd web
npm ci
cd ..
```

---

## Configuring AI Assistance (`GROQ_API_KEY`)

SecureLex IDE uses **Groq** for high-speed AI assistance (explaining vulnerabilities, proposing remediation diffs, and AI code generation):
- `llama-3.1-8b-instant`: Fast explanations and code triage.
- `llama-3.3-70b-versatile`: Complex patch synthesis and code generation.

### Setting your API key
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and configure your key:
   ```env
   GROQ_API_KEY=your_actual_groq_api_key_here
   SECURELEX_AI_PROVIDER=groq
   ```
3. If no key is set, the entire IDE continues functioning normally in offline mode. AI buttons will indicate that a key is required.

---

## Running the Application

Start the backend and frontend in two terminals:

### Terminal 1: Backend API
```powershell
.\.venv\Scripts\python.exe -m uvicorn apsla.server.app:app --app-dir src --host 127.0.0.1 --port 8000
```

### Terminal 2: Frontend Dev Server
```powershell
cd web
npm run dev -- --host 127.0.0.1
```

Open your browser to `http://127.0.0.1:5173`.

---

## Building the Frontend

To compile the production frontend bundle:
```bash
cd web
npm run build
```
Build artifacts are placed in `web/dist/`.

---

## Testing

SecureLex IDE includes an extensive automated test suite covering unit tests, security rules, API contracts, and browser end-to-end tests:

### Run Python Tests
```powershell
.\.venv\Scripts\python.exe run_tests.py
```

### Run Frontend Tests
```powershell
cd web
npm test
```

### Run Playwright Browser E2E Tests
```powershell
cd web
npm run e2e
```

### Run Full Linter and Type Checks
```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src/apsla
cd web && npm run typecheck
```

---

## Supported Languages

| Language | Analysis Stages | Key Vulnerability Classes Covered |
|---|---|---|
| **Python** | Scanner, AST parser, taint engine, ML model | Command injection, SQL injection, path traversal, weak crypto, eval/exec |
| **JavaScript** | Scanner, AST parser, taint engine, ML model | DOM XSS, prototype pollution, eval injection, shell command execution |
| **Java** | Scanner, AST structure parser, taint engine, ML model | SQL injection, LDAP injection, path traversal, hardcoded secrets |
| **C / C++** | Scanner, AST structure parser, taint engine, ML model | Buffer overflow (`strcpy`, `sprintf`), format string bugs, use-after-free |

---

## Privacy & Security Notice

> **Important**: Code Privacy & Consent
>
> 1. **100% Offline Core**: All lexical analysis, token inspection, AST parsing, deterministic security rules, taint propagation, and fix verification run strictly locally on your machine.
> 2. **Explicit Consent Required**: The AI features (Build with AI, AI Explain, AI Propose Fix) transmit code snippets to Groq (`api.groq.com`) **only after you grant explicit consent** in Settings (`/api/ai/consent`).
> 3. **No Unsolicited Network Calls**: The backend never initiates outbound network traffic without user action and consent.
> 4. **No Credential Leakage**: Your `GROQ_API_KEY` is loaded strictly by the backend server; it is never transmitted to the browser client or logged.

For more details, see [SECURITY.md](SECURITY.md) and [docs/threat_model.md](docs/threat_model.md).

---

## Limitations

- **Static Analysis Inherent Limits**: Static analysis identifies pattern-based risks and taint flows; it cannot prove that code is completely bug-free or vulnerability-free.
- **No Automatic Code Execution**: SecureLex IDE does not execute untrusted source code in a sandbox.
- **Remediation Review**: Automated fix proposals are recommendations. Developers should review diffs and execute project-level integration tests before merging changes.

---

## Documentation Index

- [System Architecture](docs/architecture.md)
- [Security Threat Model](docs/threat_model.md)
- [Rules Catalogue](docs/rules_catalogue.md)
- [Adding a Custom Rule](docs/adding_a_rule.md)
- [User Guide](docs/user_guide.md)
- [REST API Specification](docs/api.md)
- [Security Policy](SECURITY.md)

---

## License

SecureLex IDE is licensed under the [MIT License](LICENSE).
