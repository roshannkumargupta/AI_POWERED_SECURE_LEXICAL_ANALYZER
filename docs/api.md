# SecureLex IDE (APSLA) - HTTP REST API Reference

---

## 1. Overview & Architecture

The SecureLex IDE backend exposes an HTTP REST API powered by **FastAPI** and **Uvicorn**, serving as the headless bridge between the core `Analyzer` pipeline and the Phase 6 web interface (React / Monaco Editor).

### Key Architectural Characteristics
- **Base Prefix:** All API endpoints are mounted under `/api`.
- **Content Type:** `application/json` exclusively for all requests and responses.
- **Port & Binding:** Default bind on `http://127.0.0.1:8000`.
- **CORS Allowlist:** Strictly restricted to frontend origins `http://localhost:5173` and `http://127.0.0.1:5173`.
- **Payload Limits:** Maximum source payload of **512 KB**; payloads exceeding this limit receive `HTTP 413 Content Too Large`.
- **Execution Timeouts:** Asynchronous timeout enforced at **10.0 seconds** per analysis request; requests exceeding this limit receive `HTTP 504 Gateway Timeout`.
- **Pure Function LRU Caching:** Pure analysis executions are cached via deterministic SHA-256 keys `hash(source::language::filename::options)` with a thread-safe LRU capacity of 128 items.
- **Production Error Shielding:** Internal server errors (500) never leak Python tracebacks to the client. A unique random 8-character `error_id` is returned while the full traceback is recorded in structured logs.

---

## 2. API Endpoints

### 2.1 Health Check
`GET /api/health`

Returns operational status, semantic version, and the active state of the machine learning inference engine.

#### Response `200 OK`
```json
{
  "status": "ok",
  "version": "0.1.0",
  "ml_mode": "on",
  "ml_model_id": "random_forest_20260929_221524"
}
```

When no trained ML model artifact is present in `src/apsla/ml/artifacts/`, the endpoint truthfully reports:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "ml_mode": "off",
  "ml_model_id": "none"
}
```

---

### 2.2 Supported Languages
`GET /api/languages`

Retrieves registered language plugins from the central `LanguageRegistry`. Newly registered languages (e.g., Java, JavaScript, C++) automatically appear without server modifications.

#### Response `200 OK`
```json
[
  {
    "id": "python",
    "display_name": "Python",
    "extensions": [
      ".py",
      ".pyw"
    ],
    "monaco_id": "python"
  }
]
```

---

### 2.3 Interactive Samples
`GET /api/samples[?language=python]`

Returns pre-bundled realistic code snippets showcasing vulnerabilities, Trojan Source Unicode attacks, and safe coding practices.

#### Query Parameters
| Parameter | Type | Required | Description |
|:---|:---|:---|:---|
| `language` | `string` | Optional | Filter samples by language identifier (e.g. `python`). |

#### Response `200 OK`
```json
[
  {
    "id": "python-vuln-cmd-injection",
    "title": "Command Injection via Web Parameter",
    "category": "vulnerable",
    "language": "python",
    "filename": "vulnerable_ping.py",
    "code": "from flask import Flask, request\nimport os\n\napp = Flask(__name__)\n\n@app.route('/ping')\ndef ping():\n    # Untrusted user parameter flows directly into system shell\n    target = request.args.get('ip')\n    os.system('ping -c 1 ' + target)\n    return 'Ping dispatched'\n",
    "description": "Vulnerable endpoint where an HTTP request parameter enters via request.args.get and reaches the os.system() sink via dynamic string concatenation."
  },
  {
    "id": "python-trojan-source-bidi",
    "title": "Trojan Source Bidi Override (CVE-2021-42574)",
    "category": "adversarial",
    "language": "python",
    "filename": "trojan_auth.py",
    "code": "#!/usr/bin/env python3\n\ndef authenticate(user, access_level):\n    # Trojan Source: Bi-directional unicode characters deceive code review\n    # Visual order masks logic inversion:\n    is_admin = False\n    '''\u202e } \u2066if is_admin:\u2069 \u2066'''\n    return True\n",
    "description": "Adversarial snippet containing bidirectional Unicode override characters (U+202E, U+2066, U+2069) that visually swap logic during peer review."
  }
]
```

---

### 2.4 Code Analysis
`POST /api/analyze`

Executes the unified lexical, Unicode defense, AST rule, taint propagation, and ML fusion analyzer on the provided source.

#### Request Body
```json
{
  "source": "name = request.args.get(\"q\")\nos.system(\"echo \" + name)\n",
  "language": "python",
  "filename": "cmd_injection_flask.py",
  "options": {
    "fixes": true,
    "ml": true,
    "include_tokens": true,
    "include_suppressed": false
  }
}
```
*Note: If `language` is `null` or omitted, the server automatically infers the language from `filename` or lexical content via `registry.detect()`.*

#### Response `200 OK`
```json
{
  "language": "python",
  "filename": "cmd_injection_flask.py",
  "findings": [
    {
      "id": "APS-PY-INJ-002-2-1-cbd81e",
      "rule_id": "APS-PY-INJ-002",
      "title": "Command Injection via Shell Execution Sink",
      "cwe": "CWE-78",
      "severity": "CRITICAL",
      "label": "MALICIOUS",
      "confidence": 0.95,
      "range": {
        "start_line": 2,
        "start_col": 1,
        "end_line": 2,
        "end_col": 26
      },
      "message": "Untrusted input reaches shell execution sink os.system()",
      "explanation": "Dynamic arguments passed into os.system() can allow arbitrary command execution. Replace with subprocess.run(..., shell=False).",
      "evidence": {
        "sink_call": "os.system",
        "has_taint_path": true
      },
      "taint_path": [
        {
          "step": "source",
          "range": { "start_line": 1, "start_col": 8, "end_line": 1, "end_col": 30 },
          "text": "request.args.get(\"q\")",
          "note": "HTTP request parameter enters via 'request.args.get'"
        },
        {
          "step": "propagate",
          "range": { "start_line": 1, "start_col": 1, "end_line": 1, "end_col": 5 },
          "text": "name",
          "note": "Taint propagated via assignment to 'name'"
        },
        {
          "step": "propagate",
          "range": { "start_line": 2, "start_col": 11, "end_line": 2, "end_col": 25 },
          "text": "\"echo \" + name",
          "note": "Tainted concatenation / formatting"
        },
        {
          "step": "sink",
          "range": { "start_line": 2, "start_col": 1, "end_line": 2, "end_col": 26 },
          "text": "os.system(\"echo \" + name)",
          "note": "Tainted command reaches shell execution sink 'os.system()'"
        }
      ],
      "fixes": [
        {
          "id": "fix-APS-PY-INJ-002-2-1-cbd81e-1",
          "finding_id": "APS-PY-INJ-002-2-1-cbd81e",
          "title": "Replace os.system with safe subprocess.run",
          "description": "Convert shell command string into an argument list invoked without shell=True.",
          "confidence": "review",
          "kind": "rule",
          "edits": [
            {
              "range": { "start_line": 1, "start_col": 1, "end_line": 1, "end_col": 1 },
              "new_text": "import subprocess\n"
            },
            {
              "range": { "start_line": 2, "start_col": 1, "end_line": 2, "end_col": 26 },
              "new_text": "subprocess.run([\"echo\", name], check=True)"
            }
          ],
          "verification": {
            "syntax_ok": true,
            "finding_gone": true,
            "new_findings": [],
            "verified": true,
            "notes": "Verified: syntax valid, target finding eliminated, zero regressions."
          }
        }
      ],
      "sources": ["rule", "taint"],
      "suppressed": false
    }
  ],
  "tokens": [],
  "summary": {
    "critical": 1,
    "high": 0,
    "medium": 0,
    "low": 0,
    "info": 0,
    "score": 60,
    "tokens_total": 12,
    "tokens_malicious": 1,
    "tokens_suspicious": 1
  },
  "engine": {
    "ml_mode": "on",
    "ml_model_id": "random_forest_20260929_221524",
    "taint": "ast",
    "version": "0.1.0",
    "elapsed_ms": 2.45
  }
}
```

---

### 2.5 Single Fix Application & Verification
`POST /api/fix`

Applies an atomic, verified fix identified by `fix_id` to the source code, generates a unified diff, verifies syntax safety, and returns the re-analyzed document.

#### Request Body
```json
{
  "source": "name = request.args.get(\"q\")\nos.system(\"echo \" + name)\n",
  "language": "python",
  "finding_id": "APS-PY-INJ-002-2-1-cbd81e",
  "fix_id": "fix-APS-PY-INJ-002-2-1-cbd81e-1",
  "filename": "cmd_injection_flask.py"
}
```

#### Response `200 OK`
```json
{
  "new_source": "import subprocess\nname = request.args.get(\"q\")\nsubprocess.run([\"echo\", name], check=True)\n",
  "diff": "--- a/cmd_injection_flask.py\n+++ b/cmd_injection_flask.py\n@@ -1,2 +1,3 @@\n+import subprocess\n name = request.args.get(\"q\")\n-os.system(\"echo \" + name)\n+subprocess.run([\"echo\", name], check=True)\n",
  "verification": {
    "syntax_ok": true,
    "finding_gone": true,
    "new_findings": [],
    "verified": true,
    "notes": "Verified: syntax valid, target finding eliminated, zero regressions."
  },
  "new_result": {
    "language": "python",
    "filename": "cmd_injection_flask.py",
    "findings": [],
    "summary": {
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 0,
      "info": 0,
      "score": 100
    }
  }
}
```

---

### 2.6 Multi-Pass Batch Remediation
`POST /api/fix-all`

Executes multi-pass (up to 3 passes) automated remediation applying non-conflicting, verified fixes and reporting score progression.

#### Request Body
```json
{
  "source": "stream = input()\nyaml.load(stream)\n",
  "language": "python"
}
```

#### Response `200 OK`
```json
{
  "new_source": "stream = input()\nyaml.safe_load(stream)\n",
  "applied": [
    "fix-APS-PY-DES-002-2-1-aae7f2-1"
  ],
  "skipped": [],
  "diff": "--- a/<editor>\n+++ b/<editor>\n@@ -1,2 +1,2 @@\n stream = input()\n-yaml.load(stream)\n+yaml.safe_load(stream)\n",
  "score_before": 69,
  "score_after": 86
}
```

---

### 2.7 False-Positive User Feedback
`POST /api/feedback`

Records user-flagged false positive findings into append-only storage (`data/feedback/false_positives.jsonl`). Future analyses automatically suppress the finding unless `include_suppressed: true` is explicitly requested.

#### Request Body
```json
{
  "finding_fingerprint": "APS-PY-INJ-002-2-1-cbd81e",
  "rule_id": "APS-PY-INJ-002",
  "language": "python",
  "verdict": "false_positive",
  "snippet": "os.system(\"echo \" + name)"
}
```

#### Response `200 OK`
```json
{
  "saved": true
}
```

---

### 2.8 Machine Learning Explainability Insights
`POST /api/ml/insights`

Computes per-feature-group occlusion explanations for a specific token in the source document. Occludes each feature group with neutral median baseline values and computes the differential drop in predicted malicious probability.

#### Request Body
```json
{
  "source": "name = request.args.get(\"q\")\nos.system(\"echo \" + name)\n",
  "language": "python",
  "token_index": 0
}
```

#### Response `200 OK`
```json
{
  "ml_mode": "on",
  "token_index": 0,
  "token_text": "name",
  "predicted_label": "SUSPICIOUS",
  "probabilities": {
    "SAFE": 0.3095,
    "SUSPICIOUS": 0.6198,
    "MALICIOUS": 0.0707
  },
  "feature_group_drops": {
    "unicode": 0.0,
    "entropy": 0.02,
    "statistical": -0.04,
    "recovery": 0.0,
    "payload": 0.0,
    "api_keyword": 0.0,
    "context": 0.0,
    "enclosing_call": 0.0,
    "neighbours": 0.0303,
    "structure": -0.03
  },
  "error": null
}
```

When ML mode is inactive (`ml_mode: "off"`):
```json
{
  "ml_mode": "off",
  "token_index": 0,
  "token_text": null,
  "predicted_label": null,
  "probabilities": {},
  "feature_group_drops": {},
  "error": "ML model artifact not found or corrupted."
}
```

---

### 2.9 Static Fallback Root
`GET /`

When `web/dist` exists (post frontend build), serves the single-page application `index.html` with client-side routing fallback. When unbuilt, returns a JSON diagnostic message.

#### Response `200 OK` (Dev Mode)
```json
{
  "name": "SecureLex IDE API",
  "status": "running",
  "version": "0.1.0",
  "message": "Backend service is operational. Frontend build not found in web/dist. Run Vite development server at http://localhost:5173 or execute 'npm run build' in web/.",
  "docs_url": "/docs",
  "api_prefix": "/api"
}
```

---

## 3. Error Codes & Handling

The API adheres to standard HTTP status codes:

| HTTP Status | Name | Cause | Response Structure |
|:---:|:---|:---|:---|
| **400** | Bad Request | Unsupported language, missing language, or out-of-bounds token index. | `{"detail": "..."}` |
| **404** | Not Found | Requested `finding_id` or `fix_id` does not exist in target source. | `{"detail": "..."}` |
| **413** | Content Too Large | Source code exceeds 512 KB limit. | `{"detail": "Source payload size (...) exceeds the 512 KB limit."}` |
| **422** | Unprocessable Entity | Pydantic JSON schema validation failure. | `{"detail": [...]}` |
| **504** | Gateway Timeout | Analysis pipeline exceeded 10.0 seconds. | `{"detail": "Analysis timed out after 10 seconds"}` |
| **500** | Internal Server Error | Unhandled server exception. Stack traces are masked. | `{"detail": "Internal server error", "error_id": "a1b2c3d4"}` |
