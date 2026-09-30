# Phase 5 Explained: Headless REST API, Deterministic LRU Caching & Web Bridge

---

## 1. Executive Summary & Plain-English Overview

Phase 5 transitions SecureLex IDE (`apsla`) from a command-line and library static analysis engine into a **production-grade, headless HTTP REST microservice**. 

While Phases 1 through 4 engineered the analytical brain—lexical scanning, Unicode defense, AST pattern rules, data-flow taint tracking, verified code remediation, and leak-free machine learning fusion—Phase 5 constructs the communications layer. It exposes this analytical power through a standard, language-agnostic interface that will drive the interactive Monaco Editor frontend in Phase 6.

### Primary Objectives Delivered in Phase 5:
1. **Pydantic v2 Schema Layer (`server/schemas.py`):** Strictly typed, validated request and response models reusing core `apsla.models`.
2. **FastAPI Application & Router (`server/app.py`):** Clean `/api` prefixed REST routing, strict CORS security policies, and 512 KB payload size enforcement.
3. **Pure Function LRU Caching (`server/cache.py`):** Thread-safe 128-slot Least-Recently-Used memory cache keyed by deterministic SHA-256 digest of request inputs.
4. **Execution Safety & Defense in Depth:** Asynchronous 10.0-second analysis timeouts (`HTTP 504`) preventing DoS via ReDoS or complex AST traversals, plus unhandled exception shielding that never leaks server stack traces.
5. **Interactive Remediation & ML Explainability APIs:** Endpoints for applying single verified fixes, running 3-pass batch remediation, streaming token-level occlusion drops, and recording false positive feedback.
6. **Developer Tooling & Deployment:** `scripts/dev.py` hot-reloading dev runner and `apsla serve` CLI command.

---

## 2. Deep-Dive Architecture & Core Theoretical Concepts

### A. REST (Representational State Transfer) in Static Security Analysis
The World Wide Web is built on REST architectural constraints (Roy Fielding, 2000). Applying REST principles to static analysis provides distinct operational guarantees:

1. **Statelessness:** Every request from client to server contains all information necessary to understand and process the analysis (`source`, `language`, `filename`, `options`). The server stores no session state between client requests.
2. **Uniform Interface:** Resources are identified by standard URI paths (`/api/analyze`, `/api/fix`, `/api/health`). HTTP verbs communicate intent (`GET` for idempotent queries, `POST` for computational execution or state submission). Standard status codes (`200`, `400`, `404`, `413`, `422`, `504`, `500`) govern outcome semantics.
3. **Decoupling of Client and Server:** The analysis engine can be hosted on a remote server, executed in a container, or run as a local localhost sidecar. The Monaco Editor frontend remains completely decoupled from Python runtimes, C-extensions, or scikit-learn models.

### B. JSON (JavaScript Object Notation) as the Universal Contract
JSON is the ubiquitous lingua franca of modern web development:
- **Type-Strict Validation:** Through Pydantic v2, all incoming JSON payloads are validated against strict type constraints before business logic runs. Invalid types or missing fields are intercepted by FastAPI and return `422 Unprocessable Entity` with exact field error paths.
- **Bi-Directional Serialization:** Internal domain models (`Finding`, `TaintPathStep`, `Fix`, `Edit`, `Range`) serialize cleanly into JSON without custom ad-hoc string formatting, eliminating impedance mismatch between Python and TypeScript.

### C. Why Pure Functions Are Cacheable
In computer science, a function $f$ is **pure** if and only if:
1. **Determinism:** For the exact same input arguments, it always yields the identical return value:
   $$x_1 = x_2 \implies f(x_1) = f(x_2)$$
2. **Absence of Side Effects:** Evaluating $f(x)$ does not mutate external state (does not modify disk, global variables, network sockets, or databases).

Static analysis of a fixed source document with a fixed set of options is a mathematical pure function:
$$\text{Analyze}(\text{source}, \text{language}, \text{options}) \to \text{AnalysisResult}$$

#### Mathematical Caching Rationale
Because the function is pure, re-executing parsing, Unicode recovery, AST visitor passes, taint graphs, and ML inferences across identical keystrokes is redundant CPU overhead. 

SecureLex IDE constructs a deterministic SHA-256 fingerprint:
$$K = \text{SHA-256}(\text{source} \mathbin{\Vert} \text{language} \mathbin{\Vert} \text{filename} \mathbin{\Vert} \text{JSON}(\text{sorted\_options}))$$

- **Time Complexity:** Cache lookup is $O(1)$ amortized using an `OrderedDict` under a thread lock.
- **Space Complexity:** Bound to a constant upper memory limit ($N = 128$ items), evicting the least-recently-used document when capacity is reached.
- **Cache Invalidation:** The cache is explicitly invalidated when user feedback (`POST /api/feedback`) changes the suppression state, ensuring subsequent analyses immediately reflect new suppression rules.

### D. Production Error Shielding & Asynchronous Timeouts
Exposing static code analysis over HTTP introduces significant denial-of-service (DoS) vulnerabilities:
- **Catastrophic Backtracking (ReDoS):** Complex regex rules can lock CPU cores in exponential backtracking when fed pathological input strings.
- **Deep AST Recursion:** Deeply nested expressions can exhaust thread call stacks.
- **Information Leakage:** Unhandled exceptions that return Python tracebacks reveal internal file paths, framework versions, and dependencies to potential adversaries.

SecureLex IDE defends against these risks through two mechanisms:
1. **Asynchronous Non-Blocking Timeout (`HTTP 504`):**
   ```python
   result = await asyncio.wait_for(
       asyncio.to_thread(analyzer.analyze, req.source, ...),
       timeout=10.0,
   )
   ```
   If processing exceeds 10 seconds, `asyncio.wait_for` raises `TimeoutError` and FastAPI aborts the request with `504 Gateway Timeout`.
2. **Unhandled Exception Masking (`HTTP 500`):**
   A global exception handler catches all unexpected `Exception` instances, generates a random 8-character UUID (`error_id`), writes the full stack trace to the structured logging facility, and returns a sanitized JSON response:
   ```json
   {
     "detail": "Internal server error",
     "error_id": "e90d6fb3"
   }
   ```
   No traceback, internal path, or library version is ever exposed to the HTTP client.

---

## 3. End-to-End Endpoint Specifications

| Method | Endpoint | Description | Key Status Codes |
|:---|:---|:---|:---:|
| `GET` | `/api/health` | Service version, operational status, ML mode, and model ID. | `200` |
| `GET` | `/api/languages` | Dynamically registered languages (`id`, `display_name`, `extensions`, `monaco_id`). | `200` |
| `GET` | `/api/samples` | Curated vulnerable, Trojan Source, and safe samples for IDE demoing. | `200` |
| `POST` | `/api/analyze` | Unified lexical, taint, AST, and ML analysis. Enforces 512 KB limit. | `200`, `400`, `413`, `504` |
| `POST` | `/api/fix` | Applies an atomic fix, verifies syntax safety, returns diff and re-analysis. | `200`, `400`, `404` |
| `POST` | `/api/fix-all` | Multi-pass batch remediation applying all verified non-conflicting fixes. | `200`, `400` |
| `POST` | `/api/feedback` | Saves user false positive reports to JSONL; suppresses in future runs. | `200`, `422` |
| `POST` | `/api/ml/insights` | Feature-group occlusion explanations measuring drop in malicious probability. | `200`, `400` |
| `GET` | `/` | Serves `web/dist` SPA fallback if built; returns status JSON in dev mode. | `200` |

---

## 4. Viva Examination Questions & Answers

### Q1: Why did you choose FastAPI over Flask or Django for SecureLex IDE?
**Answer:**
FastAPI was selected for three principal technical reasons:
1. **Native Asynchronous Concurrency:** FastAPI is built upon ASGI (Starlette) and natively supports `async`/`await`. This enables offloading CPU-bound analysis to worker threads via `asyncio.to_thread` while maintaining a strict 10-second timeout via `asyncio.wait_for` without blocking the main event loop.
2. **Automated Schema Validation via Pydantic v2:** FastAPI automatically deserializes, validates, and serializes request/response models. Incoming malformed JSON or invalid types are rejected at the gateway with detailed HTTP 422 responses before reaching business logic.
3. **Zero-Configuration OpenAPI Documentation:** FastAPI dynamically generates interactive Swagger UI (`/docs`) and ReDoc (`/redoc`) documentation directly from code schemas, streamlining API testing and frontend integration.

### Q2: Why is the analysis payload restricted to 512 KB, and why return HTTP 413 rather than truncating the source code?
**Answer:**
Source code files in production repositories rarely exceed a few thousand lines (~100 to 200 KB). Setting an upper boundary of 512 KB prevents malicious or accidental denial-of-service (DoS) attacks caused by memory exhaustion during AST construction, token vector allocation, or 3D window tensor generation ($N \times 9 \times 45$). 

Silently truncating code would violate the correctness invariant of static analysis: truncated code yields syntax errors, truncated string literals, and severed taint propagation paths, producing inaccurate and misleading findings. Returning `HTTP 413 Content Too Large` communicates a clear contract violation to the client without corrupting analytical integrity.

### Q3: How does your LRU caching mechanism guarantee that cached results remain valid and do not return stale findings?
**Answer:**
The cache key is computed as a SHA-256 cryptographic digest combining the raw source text, target language, filename, and sorted options dictionary:
$$\text{Key} = \text{SHA-256}(\text{source} \mathbin{\Vert} \text{language} \mathbin{\Vert} \text{filename} \mathbin{\Vert} \text{JSON}(\text{sorted\_options}))$$
Any modification to the code text—even adding a single whitespace character—or changing an analysis flag (e.g., toggling ML or suppressions) generates a completely distinct cryptographic hash, preventing stale cache hits. Furthermore, when user false-positive feedback is recorded via `POST /api/feedback`, the server explicitly calls `ANALYSIS_CACHE.clear()`, invalidating all cached entries so that suppression rules take immediate effect.

### Q4: Explain the difference between `POST /api/fix` and `POST /api/fix-all`. When should each be used?
**Answer:**
- `POST /api/fix` is an **interactive, granular remediation endpoint**. It targets a single specific finding and fix ID selected by a developer in the IDE. It verifies the fix, applies atomic character range replacements via `apply_edits()`, computes a unified diff, and returns both the diff and the re-analyzed document.
- `POST /api/fix-all` is an **automated batch remediation engine**. It runs up to 3 iterative passes across the document. In each pass, it identifies non-conflicting, verified fixes (restricted to `confidence="safe"` by default, or including `review` fixes if requested), applies them simultaneously, verifies syntax safety, and repeats until convergence or pass limits. It is designed for "Fix All Safe Issues" IDE shortcuts.

### Q5: What security risks are associated with CORS (Cross-Origin Resource Sharing), and how does your API mitigate them?
**Answer:**
CORS is a browser security mechanism that restricts web applications running at one origin from interacting with resources from a different origin. Because the SecureLex IDE API can execute code remediation and file analysis, leaving CORS open (`allow_origins=["*"]`) would allow malicious external websites visited in the developer's browser to send cross-origin requests to `http://127.0.0.1:8000/api/analyze` or `http://127.0.0.1:8000/api/fix`, potentially reading proprietary source code or executing unwanted modifications.

To prevent Cross-Site Request Forgery (CSRF) and cross-origin data exfiltration, the server restricts CORS headers strictly to authorized local Vite dev server origins: `http://localhost:5173` and `http://127.0.0.1:5173`. Requests originating from unauthorized origins receive no `Access-Control-Allow-Origin` header, causing browser security sandboxes to block cross-origin access.

---

## 5. Architectural Glossary

- **ASGI (Asynchronous Server Gateway Interface):** The modern Python standard interface between asynchronous web servers (e.g., Uvicorn) and Python web applications (e.g., FastAPI).
- **CORS (Cross-Origin Resource Sharing):** HTTP-header based mechanism enabling a server to indicate any origins other than its own from which a browser should permit loading resources.
- **LRU (Least Recently Used) Cache:** A cache eviction algorithm that organizes items in order of use; when the cache reaches capacity, the least recently accessed item is evicted.
- **Idempotency:** A property of HTTP operations where making multiple identical requests has the same effect on server state as making a single request (e.g., `GET`, `HEAD`).
- **Pydantic v2:** A high-performance Python data parsing and validation library written in Rust, utilizing Python type annotations to enforce schema definitions.
- **ReDoS (Regular Expression Denial of Service):** An algorithmic complexity attack wherein a crafted input causes a poorly written regular expression engine to exhibit exponential time backtracking.
- **SPA (Single Page Application):** A web application implementation where all code (HTML, JavaScript, CSS) is retrieved with a single page load, and subsequent navigation updates the DOM dynamically without page reloads.
- **Unified Diff:** A standard text format displaying differences between two files using unified line addition (`+`) and deletion (`-`) blocks accompanied by two-line context headers.
- **Occlusion Analysis:** An explainability technique in machine learning where input features are masked or replaced with baseline values to observe the resulting decrease in prediction confidence.
