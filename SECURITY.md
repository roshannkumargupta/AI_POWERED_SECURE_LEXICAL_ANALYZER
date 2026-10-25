# Security Policy

## Reporting Security Issues

We take the security of SecureLex IDE seriously. If you discover a security vulnerability or believe you have found a potential issue, please report it responsibly:

- **Email**: `security@securelex-ide.org` (or contact the repository maintainers directly).
- **Process**: Please include a detailed description of the vulnerability, steps to reproduce, and a proof of concept if available. We will acknowledge receipt within 48 hours and work with you on remediation before any public disclosure.

Please do not open public GitHub issues for sensitive security vulnerabilities.

---

## Architecture & Security Boundary

### 1. Local-First Processing
All primary analysis engines operate strictly locally on the host system:
- **Lexical Analysis**: In-process scanners run without network dependencies.
- **Syntactic Parsing**: Tree-sitter and AST parsers run within process memory.
- **Rule Engine & Taint Analysis**: Deterministic Python engines run within loopback boundaries.
- **Patch Verification**: Candidate patches are evaluated in an isolated in-memory AST sandbox.

### 2. Network Isolation & AI Consent
- **Default Loopback Binding**: The FastAPI backend binds to loopback (`127.0.0.1`) by default.
- **Explicit User Consent**: External AI requests to Groq (`api.groq.com`) occur **only** when the user explicitly grants consent in the Workbench Settings dialog (`/api/ai/consent`).
- **No Inadvertent Code Exfiltration**: Code is never transmitted to any third-party service without user authorization.
- **Credential Protection**: The `GROQ_API_KEY` is loaded server-side from environment variables (`.env`). It is never returned in API payloads, browser state, or client logs.

### 3. Resource Caps & Denial-of-Service Defense
- **Payload Limits**: The API limits input source payloads to a maximum of 512 KB (`HTTP 413 Payload Too Large`).
- **Analysis Timeout**: Asynchronous analysis execution times out after 10.0 seconds (`HTTP 504 Gateway Timeout`).
- **Execution Sandboxing**: SecureLex IDE performs static analysis and does not execute untrusted user code.

### 4. Trojan Source & Homoglyph Protection
SecureLex IDE actively guards against source code supply-chain deception:
- **Bidi Overrides**: Flags bidirectional control characters (CVE-2021-42574) such as `RLO`, `LRO`, and `PDF` that alter the visual order of tokens.
- **Homoglyphs**: Identifies confusable Unicode characters that mimic ASCII identifiers.
