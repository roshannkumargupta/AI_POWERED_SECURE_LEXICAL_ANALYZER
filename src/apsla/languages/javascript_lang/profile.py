"""JavaScript taint profile and dangerous API taxonomy for SecureLex IDE.

Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT).
"""

from __future__ import annotations

from typing import Final

from apsla.languages.base import TaintProfile

# ── Untrusted Sources ──────────────────────────────────────────────────────────

JS_SOURCES: Final[frozenset[str]] = frozenset(
    {
        # Express / Web framework request properties
        "req.query",
        "req.params",
        "req.body",
        "req.headers",
        "req.cookies",
        "req.param",
        "req.get",
        "request.query",
        "request.params",
        "request.body",
        "request.headers",
        "request.cookies",
        # Browser navigation and DOM locations
        "location.search",
        "location.hash",
        "location.href",
        "document.URL",
        "document.referrer",
        "document.cookie",
        "window.name",
        "window.location",
        "document.location",
        # URL parameters & user prompts
        "URLSearchParams",
        "prompt(",
        "prompt",
        # Process and environment
        "process.argv",
        "process.env",
        # Web storage
        "localStorage.getItem",
        "sessionStorage.getItem",
        "localStorage",
        "sessionStorage",
        # Cross-window messages
        "event.data",
        # File system reads of user-supplied data
        "fs.readFileSync",
        "fs.readFile",
        "readFileSync",
        "readFile",
    }
)

# ── Sensitive Sinks ────────────────────────────────────────────────────────────

JS_SINKS: Final[frozenset[str]] = frozenset(
    {
        # Code injection (CWE-95)
        "eval(",
        "Function(",
        "new Function(",
        "setTimeout(",
        "setInterval(",
        # Command injection (CWE-78)
        "child_process.exec",
        "child_process.execSync",
        "exec(",
        "execSync(",
        "spawn(",
        "spawnSync(",
        # Cross-Site Scripting (CWE-79)
        ".innerHTML",
        ".outerHTML",
        ".insertAdjacentHTML",
        "document.write(",
        "document.writeln(",
        "dangerouslySetInnerHTML",
        # Open redirect & attribute injection (CWE-601)
        "location.href",
        "location =",
        "window.location =",
        "window.location.href =",
        ".setAttribute(",
        # SQL injection (CWE-89)
        ".query(",
        ".execute(",
        ".raw(",
        "db.query(",
        "connection.query(",
        "pool.query(",
        "client.query(",
        "sequelize.query(",
        "knex.raw(",
        # Path traversal (CWE-22)
        "fs.readFile(",
        "fs.readFileSync(",
        "fs.createReadStream(",
        "res.sendFile(",
        "response.sendFile(",
        # Server-Side Request Forgery / SSRF (CWE-918)
        "axios(",
        "axios.get(",
        "axios.post(",
        "fetch(",
        "http.get(",
        "http.request(",
        "https.get(",
        "https.request(",
        # Insecure randomness (CWE-338)
        "Math.random",
        # Weak hash (CWE-327)
        "createHash(",
        "crypto.createHash(",
        # Prototype pollution (CWE-1321)
        "Object.assign(",
        "_.merge(",
        "lodash.merge(",
        "_.set(",
        "lodash.set(",
        # ReDoS (CWE-1333)
        "new RegExp(",
        "RegExp(",
        # JWT verification (CWE-347)
        "jwt.verify(",
        "jwt.decode(",
        # TLS validation (CWE-295)
        "rejectUnauthorized",
        "NODE_TLS_REJECT_UNAUTHORIZED",
    }
)

# ── Sanitizers ────────────────────────────────────────────────────────────────

JS_SANITIZERS: Final[frozenset[str]] = frozenset(
    {
        # HTML / XSS sanitizers
        "DOMPurify.sanitize",
        "DOMPurify.sanitize(",
        "sanitizeHtml(",
        "escapeHtml(",
        "escape-html",
        "validator.escape(",
        "he.encode(",
        # URL sanitizers
        "encodeURIComponent(",
        "encodeURI(",
        # Safe sink / property
        ".textContent",
        "textContent =",
        # Numeric coercion
        "parseInt(",
        "parseFloat(",
        "Number(",
        # Path sanitizers
        "path.basename(",
        "path.normalize(",
        # Validator library
        "validator.isEmail(",
        "validator.isAlphanumeric(",
        "validator.isNumeric(",
        "validator.toInt(",
        # SQL parameterization
        "preparedStatement",
        "parameterize",
        "?",
        "$1",
    }
)

# ── Dangerous APIs Catalog ────────────────────────────────────────────────────

JS_DANGEROUS_APIS: Final[dict[str, str]] = {
    "eval": "Dynamic code execution via eval() (CWE-95)",
    "Function": "Dynamic function construction via Function() (CWE-95)",
    "setTimeout": "String evaluation via setTimeout() (CWE-95)",
    "setInterval": "String evaluation via setInterval() (CWE-95)",
    "child_process.exec": "OS command execution via child_process.exec (CWE-78)",
    "child_process.execSync": "Synchronous OS command execution (CWE-78)",
    "child_process.spawn": "Process execution with shell:true (CWE-78)",
    "innerHTML": "DOM manipulation via innerHTML (XSS risk, CWE-79)",
    "outerHTML": "DOM manipulation via outerHTML (XSS risk, CWE-79)",
    "insertAdjacentHTML": "DOM insertion via insertAdjacentHTML (XSS risk, CWE-79)",
    "document.write": "DOM manipulation via document.write (XSS risk, CWE-79)",
    "dangerouslySetInnerHTML": "React raw HTML rendering without sanitizer (CWE-79)",
    "location": "Client-side open redirect via location assignment (CWE-601)",
    "db.query": "SQL query execution without parameterization (CWE-89)",
    "fs.readFile": "File access with unvalidated path (CWE-22)",
    "res.sendFile": "File transfer with unvalidated path (CWE-22)",
    "fetch": "Server-side HTTP request with unvalidated URL (CWE-918)",
    "axios": "HTTP client request with unvalidated URL (CWE-918)",
    "Math.random": "Insecure pseudo-random number generator for secrets (CWE-338)",
    "crypto.createHash": "Broken cryptographic hash algorithm MD5/SHA1 (CWE-327)",
    "Object.assign": "Prototype pollution via unvalidated object merge (CWE-1321)",
    "_.merge": "Prototype pollution via recursive merge (CWE-1321)",
    "RegExp": "Regular Expression Denial of Service via dynamic regex (CWE-1333)",
    "jwt.verify": "Insecure JWT verification allowing 'none' algorithm (CWE-347)",
    "rejectUnauthorized": "Disabled TLS certificate validation (CWE-295)",
}

JS_TAINT_PROFILE: Final[TaintProfile] = TaintProfile(
    language="javascript",
    sources=JS_SOURCES,
    sinks=JS_SINKS,
    sanitizers=JS_SANITIZERS,
    dangerous_apis=JS_DANGEROUS_APIS,
)
