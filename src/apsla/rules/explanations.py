"""Rule explanation templates, concrete variable/line formatting, and catalogue generation.

Phase 12: Every rule has a structured plain-English template with:
  - what
  - why it is dangerous
  - how an attacker uses it
  - how to fix
  - simple (1-sentence summary)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from apsla.models import Finding


@dataclass(frozen=True, slots=True)
class RuleExplanationTemplate:
    """Structured plain-English explanation template for a security rule."""

    rule_id: str
    language: str
    cwe: str
    severity: str
    title: str
    what: str
    why_dangerous: str
    how_attacker_uses_it: str
    how_to_fix: str
    simple: str
    example: str = ""
    fix_example: str = ""


# Comprehensive template catalog for all SecureLex rules
RULE_TEMPLATES: Final[dict[str, RuleExplanationTemplate]] = {
    # ── Python Rules ──────────────────────────────────────────────────────────
    "APS-PY-INJ-001": RuleExplanationTemplate(
        rule_id="APS-PY-INJ-001",
        language="python",
        cwe="CWE-95",
        severity="critical",
        title="Arbitrary Code Execution via eval/exec",
        what="The code passes dynamic or untrusted input directly to Python's `eval()` or `exec()` runtime evaluators.",
        why_dangerous="Python's `eval()` and `exec()` execute arbitrary Python bytecode in the current process context with full user permissions.",
        how_attacker_uses_it="An attacker injects payload strings like `__import__('os').system('rm -rf /')` to achieve unauthenticated remote code execution.",
        how_to_fix="Replace `eval()` with `ast.literal_eval()` for safe constant parsing, or use structured parsers like `json.loads()`.",
        simple="Passing dynamic strings into eval/exec allows attackers to execute arbitrary code with application privileges.",
        example="result = eval(user_input)",
        fix_example="import ast\nresult = ast.literal_eval(user_input)",
    ),
    "APS-PY-INJ-002": RuleExplanationTemplate(
        rule_id="APS-PY-INJ-002",
        language="python",
        cwe="CWE-78",
        severity="critical",
        title="Command Injection via os.system",
        what="The code invokes the host operating system shell via `os.system()` with concatenated or dynamic command arguments.",
        why_dangerous="The system shell interprets shell metacharacters (;, &, |, `, $) allowing attackers to append secondary malicious commands.",
        how_attacker_uses_it="An attacker submits shell chaining characters (e.g., `payload; cat /etc/passwd`) to escape the intended utility and run host commands.",
        how_to_fix="Use `subprocess.run()` with argument lists and `shell=False`, or sanitize inputs using `shlex.quote()`.",
        simple="os.system executes shell commands without argument escaping, permitting shell injection via command chaining.",
        example="os.system('ping ' + ip)",
        fix_example="import subprocess\nsubprocess.run(['ping', '-c', '1', ip], check=True)",
    ),
    "APS-PY-INJ-003": RuleExplanationTemplate(
        rule_id="APS-PY-INJ-003",
        language="python",
        cwe="CWE-78",
        severity="critical",
        title="Subprocess Shell Injection",
        what="The code executes a subprocess call with `shell=True` using a string containing dynamic or concatenated variables.",
        why_dangerous="Enabling `shell=True` invokes `/bin/sh` or `cmd.exe` to interpret the command string, exposing it to shell metacharacter manipulation.",
        how_attacker_uses_it="An attacker injects pipes or semicolons (`|`, `;`, `&&`) into arguments to hijack command execution flow.",
        how_to_fix="Pass arguments as a list and set `shell=False` (the safe default in subprocess functions).",
        simple="Using subprocess with shell=True exposes commands to shell metacharacter injection.",
        example="subprocess.Popen(f'ls {directory}', shell=True)",
        fix_example="subprocess.Popen(['ls', directory], shell=False)",
    ),
    "APS-PY-INJ-004": RuleExplanationTemplate(
        rule_id="APS-PY-INJ-004",
        language="python",
        cwe="CWE-89",
        severity="high",
        title="SQL Injection via Query Formatting",
        what="The code constructs a SQL query string using string concatenation, `%` formatting, `.format()`, or f-strings.",
        why_dangerous="String-interpolated parameters break out of the SQL syntax context, allowing arbitrary database querying or data modification.",
        how_attacker_uses_it="An attacker inputs quotes (`' OR '1'='1`) to bypass authentication or extract sensitive tables using `UNION SELECT`.",
        how_to_fix="Use parameterized queries with DB-API placeholders (e.g. `cursor.execute(sql, (param,))`).",
        simple="Constructing SQL queries using string formatting permits attackers to manipulate database queries.",
        example="cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        fix_example="cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
    ),
    "APS-PY-DES-001": RuleExplanationTemplate(
        rule_id="APS-PY-DES-001",
        language="python",
        cwe="CWE-502",
        severity="critical",
        title="Untrusted Deserialization via pickle",
        what="The code unpickles untrusted binary data using `pickle.loads()` or `pickle.load()`.",
        why_dangerous="Python's pickle protocol supports arbitrary object instantiation via the `__reduce__` method, triggering code on load.",
        how_attacker_uses_it="An attacker crafts a serialized byte stream with a malicious `__reduce__` tuple that executes OS commands upon unpickling.",
        how_to_fix="Never unpickle untrusted data. Use safe serialization formats such as JSON, Protocol Buffers, or CBOR.",
        simple="Unpickling untrusted data allows attackers to achieve remote code execution via object reduction payloads.",
        example="data = pickle.loads(untrusted_bytes)",
        fix_example="import json\ndata = json.loads(untrusted_json)",
    ),
    "APS-PY-DES-002": RuleExplanationTemplate(
        rule_id="APS-PY-DES-002",
        language="python",
        cwe="CWE-502",
        severity="critical",
        title="Insecure YAML Deserialization",
        what="The code deserializes YAML documents using `yaml.load()` without an explicit safe loader.",
        why_dangerous="Standard `yaml.load()` resolves custom tags like `!!python/object/apply` which execute arbitrary Python callables.",
        how_attacker_uses_it="An attacker submits a YAML payload containing `!!python/object/apply:os.system ['touch /tmp/pwn']` to execute code.",
        how_to_fix="Always use `yaml.safe_load()` or specify `Loader=yaml.SafeLoader`.",
        simple="yaml.load executes arbitrary Python objects unless restricted with yaml.safe_load.",
        example="obj = yaml.load(raw_yaml)",
        fix_example="obj = yaml.safe_load(raw_yaml)",
    ),
    "APS-PY-CRY-001": RuleExplanationTemplate(
        rule_id="APS-PY-CRY-001",
        language="python",
        cwe="CWE-327",
        severity="medium",
        title="Broken Hash Algorithm (MD5/SHA1)",
        what="The code uses MD5 or SHA1 cryptographic hash functions for security or integrity checks.",
        why_dangerous="MD5 and SHA1 suffer from proven practical collision attacks, permitting attackers to generate identical hashes for malicious files.",
        how_attacker_uses_it="An attacker creates a collision payload with a valid hash signature to bypass integrity verification.",
        how_to_fix="Upgrade to modern collision-resistant cryptographic hashes such as SHA-256 (`hashlib.sha256()`) or SHA-3.",
        simple="MD5 and SHA-1 have broken collision resistance and must not be used for cryptographic integrity or signatures.",
        example="h = hashlib.md5(data).hexdigest()",
        fix_example="h = hashlib.sha256(data).hexdigest()",
    ),
    "APS-PY-CRY-002": RuleExplanationTemplate(
        rule_id="APS-PY-CRY-002",
        language="python",
        cwe="CWE-327",
        severity="medium",
        title="Weak Cipher Algorithm (DES/ECB)",
        what="The code initializes encryption using legacy DES or Electronic Codebook (ECB) cipher mode.",
        why_dangerous="DES uses an inadequate 56-bit key susceptible to brute force, while ECB mode preserves plaintext patterns across blocks.",
        how_attacker_uses_it="An attacker reconstructs data patterns or rapidly cracks DES keys using inexpensive cloud computing.",
        how_to_fix="Use AES in GCM authenticated encryption mode (AES-GCM-256) with unique initialization vectors.",
        simple="DES and ECB encryption modes lack security and leak structural patterns in ciphertext.",
        example="cipher = DES.new(key, DES.MODE_ECB)",
        fix_example="cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)",
    ),
    "APS-PY-SEC-001": RuleExplanationTemplate(
        rule_id="APS-PY-SEC-001",
        language="python",
        cwe="CWE-798",
        severity="high",
        title="Hardcoded Credential or Secret",
        what="The source code contains a high-entropy string or API token assigned directly to a credential variable.",
        why_dangerous="Hardcoded secrets in source files are committed to version control and distributed in deployed code repositories.",
        how_attacker_uses_it="An attacker scans public git histories or decompiles packaged binaries to extract API keys and access cloud infrastructure.",
        how_to_fix="Load credentials at runtime from environment variables (`os.environ`) or a secrets manager.",
        simple="Hardcoded secrets risk exposure in version control and source archives.",
        example='API_KEY = "AKIAIOSFODNN7EXAMPLE"',
        fix_example='API_KEY = os.environ["API_KEY"]',
    ),
    "APS-PY-NET-001": RuleExplanationTemplate(
        rule_id="APS-PY-NET-001",
        language="python",
        cwe="CWE-918",
        severity="high",
        title="Server-Side Request Forgery (SSRF)",
        what="The application performs HTTP client requests to a URL derived from user-controlled parameters.",
        why_dangerous="The server can be coerced into issuing requests to internal loopback addresses or cloud metadata endpoints.",
        how_attacker_uses_it="An attacker submits `http://169.254.169.254/latest/meta-data/` to steal IAM roles and cloud instance credentials.",
        how_to_fix="Validate URLs against strict hostname allowlists, block private/loopback IP ranges, and disable HTTP redirects.",
        simple="Unvalidated outgoing HTTP requests allow attackers to reach internal network and cloud metadata endpoints.",
        example="requests.get(target_url)",
        fix_example="if is_allowed_domain(target_url):\n    requests.get(target_url)",
    ),
    "APS-PY-IO-001": RuleExplanationTemplate(
        rule_id="APS-PY-IO-001",
        language="python",
        cwe="CWE-22",
        severity="high",
        title="Path Traversal via File Access",
        what="The code passes a dynamic path into file open operations without canonical path validation.",
        why_dangerous="Directory traversal sequences (`../`) break out of the intended folder, permitting read/write across the entire filesystem.",
        how_attacker_uses_it="An attacker requests `../../../../etc/passwd` to read sensitive configuration and user accounts.",
        how_to_fix="Resolve paths with `Path.resolve()` and verify that the target starts with the intended base directory.",
        simple="Unsanitized file paths allow attackers to escape the storage directory using directory traversal sequences.",
        example="open(base_path + '/' + filename, 'r')",
        fix_example="safe = (base / filename).resolve()\nif base in safe.parents:\n    open(safe, 'r')",
    ),
    "APS-PY-INJ-005": RuleExplanationTemplate(
        rule_id="APS-PY-INJ-005",
        language="python",
        cwe="CWE-94",
        severity="high",
        title="Server-Side Template Injection",
        what="The application evaluates untrusted input directly inside a template engine string.",
        why_dangerous="Template engines provide expressions that can navigate object models to access built-ins and call system commands.",
        how_attacker_uses_it="An attacker inputs `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}` to execute code.",
        how_to_fix="Pass data exclusively as template context variables instead of concatenating input into template strings.",
        simple="Evaluating untrusted strings in template engines allows remote code execution via template escape expressions.",
        example="jinja2.Template('Hello ' + name).render()",
        fix_example="jinja2.Template('Hello {{ name }}').render(name=name)",
    ),
    "APS-PY-OBF-001": RuleExplanationTemplate(
        rule_id="APS-PY-OBF-001",
        language="python",
        cwe="CWE-116",
        severity="high",
        title="Obfuscated Payload Execution",
        what="The code decodes a base64 or hex-encoded payload and immediately evaluates or executes it.",
        why_dangerous="Encoding masks malicious shellcodes or droppers from static signature scanners.",
        how_attacker_uses_it="An attacker disguises malware droppers as benign encoded configuration strings.",
        how_to_fix="Avoid dynamic decoding and execution of encoded strings; use explicit static modules.",
        simple="Decoding and executing obfuscated strings indicates hidden execution patterns or evasion.",
        example="exec(base64.b64decode(payload))",
        fix_example="# Review and write explicit, transparent logic",
    ),
    "APS-PY-XSS-001": RuleExplanationTemplate(
        rule_id="APS-PY-XSS-001",
        language="python",
        cwe="CWE-79",
        severity="high",
        title="Cross-Site Scripting via Dynamic HTML",
        what="The application renders unescaped user input directly into an HTML response.",
        why_dangerous="The browser executes injected `<script>` tags in the origin context of the user.",
        how_attacker_uses_it="An attacker steals session cookies and authorization tokens, or performs actions on the victim's behalf.",
        how_to_fix="Use automatic HTML escaping (e.g. Jinja2 templates) or sanitize with an HTML entity sanitizer.",
        simple="Rendering unsanitized input into HTML responses permits Cross-Site Scripting.",
        example="return render_template_string('<h1>' + user + '</h1>')",
        fix_example="return render_template('profile.html', user=user)",
    ),
    # ── Java Rules ────────────────────────────────────────────────────────────
    "APS-JV-INJ-001": RuleExplanationTemplate(
        rule_id="APS-JV-INJ-001",
        language="java",
        cwe="CWE-78",
        severity="critical",
        title="Command Injection via Runtime.exec",
        what="The application passes a dynamic command string to `Runtime.getRuntime().exec()`.",
        why_dangerous="Dynamic arguments concatenated into command strings are subject to shell interpretation and subshell injection.",
        how_attacker_uses_it="An attacker appends shell metacharacters to run arbitrary host binaries with the servlet container's UID.",
        how_to_fix="Pass commands and arguments as discrete `String[]` array elements without shell invocation.",
        simple="Executing dynamic commands via Runtime.exec allows host command injection.",
        example='Runtime.getRuntime().exec("cmd.exe /c " + input);',
        fix_example='new ProcessBuilder("safe_tool", input).start();',
    ),
    "APS-JV-INJ-002": RuleExplanationTemplate(
        rule_id="APS-JV-INJ-002",
        language="java",
        cwe="CWE-78",
        severity="critical",
        title="Command Injection via ProcessBuilder",
        what="The application initializes a `ProcessBuilder` with command strings containing user-controllable input.",
        why_dangerous="If a shell (`sh -c` or `cmd.exe /c`) is wrapped around dynamic arguments, command injection occurs.",
        how_attacker_uses_it="An attacker injects secondary commands using shell delimiters.",
        how_to_fix="Execute binaries directly using separate argument tokens without wrapping in a shell.",
        simple="Passing unvalidated input to ProcessBuilder shell arguments enables command injection.",
        example='new ProcessBuilder("sh", "-c", "ping " + host).start();',
        fix_example='new ProcessBuilder("ping", host).start();',
    ),
    "APS-JV-INJ-003": RuleExplanationTemplate(
        rule_id="APS-JV-INJ-003",
        language="java",
        cwe="CWE-89",
        severity="high",
        title="SQL Injection via JDBC Statement",
        what="The code concatenates variables directly into a SQL query executed via `Statement.executeQuery()`.",
        why_dangerous="The database engine treats the concatenated values as SQL syntax rather than literal data.",
        how_attacker_uses_it="An attacker injects quotation marks and SQL clauses (`' OR '1'='1`) to dump databases.",
        how_to_fix="Use parameterized `PreparedStatement` with `?` place-holders.",
        simple="Concatenating input into JDBC statements allows SQL query manipulation.",
        example='stmt.executeQuery("SELECT * FROM users WHERE name = \'" + name + "\'");',
        fix_example='PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE name = ?");\nps.setString(1, name);',
    ),
    "APS-JV-INJ-004": RuleExplanationTemplate(
        rule_id="APS-JV-INJ-004",
        language="java",
        cwe="CWE-89",
        severity="high",
        title="HQL / JPQL Injection",
        what="The application builds JPA or Hibernate queries by concatenating user inputs into JPQL/HQL queries.",
        why_dangerous="HQL/JPQL supports query injection, object traversal, and arbitrary data extraction.",
        how_attacker_uses_it="An attacker alters query conditions to bypass authorization checks.",
        how_to_fix='Use named query parameters (e.g., `query.setParameter("name", name)`).',
        simple="Concatenating inputs into JPQL/HQL queries exposes the database to injection.",
        example='em.createQuery("FROM User WHERE name = \'" + name + "\'");',
        fix_example='em.createQuery("FROM User WHERE name = :name").setParameter("name", name);',
    ),
    "APS-JV-DES-001": RuleExplanationTemplate(
        rule_id="APS-JV-DES-001",
        language="java",
        cwe="CWE-502",
        severity="critical",
        title="Untrusted Java Deserialization",
        what="The code deserializes untrusted streams with `ObjectInputStream.readObject()`.",
        why_dangerous="Java deserialization executes gadget chains (e.g. Apache Commons Collections) during deserialization.",
        how_attacker_uses_it="An attacker uses tools like ysoserial to craft gadget payloads that trigger remote code execution upon deserialization.",
        how_to_fix="Use safe data formats like JSON/Protobuf, or enforce an `ObjectInputFilter` whitelist.",
        simple="Untrusted Java object deserialization triggers remote code execution via gadget chains.",
        example="Object obj = new ObjectInputStream(in).readObject();",
        fix_example="// Use JSON/Jackson with safe typing or ObjectInputFilter",
    ),
    "APS-JV-CRY-001": RuleExplanationTemplate(
        rule_id="APS-JV-CRY-001",
        language="java",
        cwe="CWE-327",
        severity="medium",
        title="Weak Hash Algorithm in Java (MD5/SHA-1)",
        what="The code requests an MD5 or SHA-1 instance from `MessageDigest.getInstance()`.",
        why_dangerous="MD5 and SHA-1 lack cryptographic collision resistance.",
        how_attacker_uses_it="An attacker constructs colliding payloads sharing identical hash digests.",
        how_to_fix='Use `MessageDigest.getInstance("SHA-256")` or SHA-512.',
        simple="MD5 and SHA-1 in Java have broken collision resistance.",
        example='MessageDigest md = MessageDigest.getInstance("MD5");',
        fix_example='MessageDigest md = MessageDigest.getInstance("SHA-256");',
    ),
    "APS-JV-CRY-002": RuleExplanationTemplate(
        rule_id="APS-JV-CRY-002",
        language="java",
        cwe="CWE-327",
        severity="medium",
        title="Insecure Cipher / ECB Mode",
        what="The application requests DES or ECB cipher modes from `Cipher.getInstance()`.",
        why_dangerous="DES has a small key space and ECB leaks structural patterns across blocks.",
        how_attacker_uses_it="An attacker extracts patterns and breaks encryption keys.",
        how_to_fix='Use `Cipher.getInstance("AES/GCM/NoPadding")`.',
        simple="DES and ECB encryption modes in Java provide inadequate confidentiality.",
        example='Cipher c = Cipher.getInstance("DES/ECB/PKCS5Padding");',
        fix_example='Cipher c = Cipher.getInstance("AES/GCM/NoPadding");',
    ),
    "APS-JV-CRY-003": RuleExplanationTemplate(
        rule_id="APS-JV-CRY-003",
        language="java",
        cwe="CWE-330",
        severity="low",
        title="Insecure Random Number Generator",
        what="The code uses `java.util.Random` for cryptographic tokens, salts, or passwords.",
        why_dangerous="`java.util.Random` uses a 48-bit linear congruential generator whose internal state can be deduced from a few consecutive values.",
        how_attacker_uses_it="An attacker predicts future tokens or session IDs.",
        how_to_fix="Use `java.security.SecureRandom` for security-sensitive values.",
        simple="java.util.Random is mathematically predictable and unsuitable for security tokens.",
        example="Random r = new Random();",
        fix_example="SecureRandom sr = new SecureRandom();",
    ),
    "APS-JV-SEC-001": RuleExplanationTemplate(
        rule_id="APS-JV-SEC-001",
        language="java",
        cwe="CWE-798",
        severity="high",
        title="Hardcoded Password or Key in Java",
        what="The Java source defines hardcoded password or private key literals.",
        why_dangerous="Secrets in compiled `.class` and `.jar` files are easily extracted with decompilers.",
        how_attacker_uses_it="An attacker decompiles the binary to recover hardcoded keys.",
        how_to_fix="Store secrets in environment variables or cloud key vaults.",
        simple="Hardcoded secrets in Java binaries can be extracted by decompilation.",
        example='String apiKey = "AIzaSyD-sample-key";',
        fix_example='String apiKey = System.getenv("API_KEY");',
    ),
    "APS-JV-XML-001": RuleExplanationTemplate(
        rule_id="APS-JV-XML-001",
        language="java",
        cwe="CWE-611",
        severity="high",
        title="XML External Entity (XXE) Injection",
        what="The application parses XML with a `DocumentBuilderFactory` without disabling external entity resolution.",
        why_dangerous="The XML parser resolves external entity references, allowing reading local files or port scanning.",
        how_attacker_uses_it='An attacker submits `<!ENTITY xxe SYSTEM "file:///etc/passwd">` to read system files.',
        how_to_fix='Set `factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)`.',
        simple="XML parsers with external entities enabled can read local server files via XXE.",
        example="DocumentBuilder db = factory.newDocumentBuilder();",
        fix_example='factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);',
    ),
    "APS-JV-IO-001": RuleExplanationTemplate(
        rule_id="APS-JV-IO-001",
        language="java",
        cwe="CWE-22",
        severity="high",
        title="Path Traversal in Java File Access",
        what="The application constructs a `File` or `Path` from user input without canonical directory verification.",
        why_dangerous="Traversal sequences allow reading or overwriting files outside the target directory.",
        how_attacker_uses_it="An attacker writes `../../conf/server.xml` to tamper with server configuration.",
        how_to_fix="Call `path.normalize().toRealPath()` and verify it starts with the base directory.",
        simple="Unsanitized path strings allow directory traversal outside intended storage.",
        example="new File(baseDir, filename);",
        fix_example="Path p = baseDir.resolve(filename).normalize();\nif (!p.startsWith(baseDir)) throw new SecurityException();",
    ),
    "APS-JV-XSS-001": RuleExplanationTemplate(
        rule_id="APS-JV-XSS-001",
        language="java",
        cwe="CWE-79",
        severity="high",
        title="Reflected XSS in Servlet Response",
        what="The servlet writes user request parameters directly to `PrintWriter.println()` without escaping.",
        why_dangerous="The browser interprets user input as active HTML/JavaScript in the victim's session.",
        how_attacker_uses_it="An attacker crafts links with script payloads to compromise user accounts.",
        how_to_fix="Encode user data using OWASP Java Encoder (`Encode.forHtml(input)`).",
        simple="Writing unencoded input to servlet responses enables Cross-Site Scripting.",
        example='response.getWriter().println("<h1>" + user + "</h1>");',
        fix_example='response.getWriter().println("<h1>" + Encode.forHtml(user) + "</h1>");',
    ),
    "APS-JV-NET-001": RuleExplanationTemplate(
        rule_id="APS-JV-NET-001",
        language="java",
        cwe="CWE-918",
        severity="high",
        title="Java SSRF via URL Connection",
        what="The code opens an `HttpURLConnection` to a URL specified by user input.",
        why_dangerous="The server can be forced to query internal services and cloud metadata endpoints.",
        how_attacker_uses_it="An attacker targets internal administrative panels or metadata APIs.",
        how_to_fix="Validate URLs against an allowlist and reject loopback/RFC1918 private IPs.",
        simple="Unchecked outgoing URL connections allow Server-Side Request Forgery.",
        example="new URL(inputUrl).openConnection();",
        fix_example="if (isAllowed(inputUrl)) { new URL(inputUrl).openConnection(); }",
    ),
    "APS-JV-NET-002": RuleExplanationTemplate(
        rule_id="APS-JV-NET-002",
        language="java",
        cwe="CWE-295",
        severity="critical",
        title="TLS Certificate Validation Disabled",
        what="The code installs a trust manager that ignores SSL/TLS certificate errors (`TrustAllCerts`).",
        why_dangerous="All HTTPS connections become vulnerable to Man-in-the-Middle (MITM) interception.",
        how_attacker_uses_it="An attacker intercepts and decrypts sensitive network communications.",
        how_to_fix="Use the default system trust store or configure a specific trusted certificate authority.",
        simple="Disabling TLS certificate verification permits Man-in-the-Middle eavesdropping.",
        example="sc.init(null, new TrustManager[]{new TrustAllCerts()}, null);",
        fix_example="// Use standard SSLContext with default trusted certificates",
    ),
    "APS-JV-UNI-001": RuleExplanationTemplate(
        rule_id="APS-JV-UNI-001",
        language="java",
        cwe="CWE-1007",
        severity="high",
        title="Confusable or Homoglyph Identifier in Java",
        what="An identifier contains non-ASCII lookalike characters mimicking ASCII keywords or APIs.",
        why_dangerous="Developers mistake the identifier for standard APIs, masking malicious functionality.",
        how_attacker_uses_it="An attacker creates a lookalike function that appears harmless during code review.",
        how_to_fix="Normalize identifiers to ASCII or restrict source files to ASCII identifiers.",
        simple="Unicode homoglyphs conceal dangerous logic by mimicking trusted APIs.",
        example="void \u0435xec() { ... } // Cyrillic \u0435 mimics 'exec'",
        fix_example="void exec() { ... }",
    ),
    # ── JavaScript Rules ──────────────────────────────────────────────────────
    "APS-JS-INJ-001": RuleExplanationTemplate(
        rule_id="APS-JS-INJ-001",
        language="javascript",
        cwe="CWE-95",
        severity="critical",
        title="Arbitrary Code Execution via eval() or Function()",
        what="The code passes dynamic strings to `eval()` or `new Function()` in JavaScript.",
        why_dangerous="Strings are evaluated with access to scope variables and runtime APIs.",
        how_attacker_uses_it="An attacker injects arbitrary JavaScript to compromise frontend sessions or backend Node processes.",
        how_to_fix="Use structured data parsing (`JSON.parse()`) instead of code evaluation.",
        simple="eval() and Function() execute arbitrary JavaScript from untrusted inputs.",
        example="eval('data = ' + userJson);",
        fix_example="const data = JSON.parse(userJson);",
    ),
    "APS-JS-INJ-002": RuleExplanationTemplate(
        rule_id="APS-JS-INJ-002",
        language="javascript",
        cwe="CWE-78",
        severity="critical",
        title="Command Injection via child_process.exec",
        what="The code executes commands using `child_process.exec()` with concatenated strings.",
        why_dangerous="The underlying shell interprets operators like `|`, `;`, and `&`.",
        how_attacker_uses_it="An attacker appends shell commands to execute unauthorized host processes.",
        how_to_fix="Use `child_process.execFile()` or `spawn()` with an array of arguments.",
        simple="child_process.exec invokes a shell that executes chained injected commands.",
        example="exec('git log ' + branch);",
        fix_example="execFile('git', ['log', branch]);",
    ),
    "APS-JS-XSS-001": RuleExplanationTemplate(
        rule_id="APS-JS-XSS-001",
        language="javascript",
        cwe="CWE-79",
        severity="high",
        title="DOM-Based XSS via innerHTML",
        what="User input is assigned directly to `element.innerHTML` or `document.write()`.",
        why_dangerous="The browser parses HTML tags and executes embedded scripts.",
        how_attacker_uses_it="An attacker injects `<img src=x onerror=alert(1)>` to steal session tokens.",
        how_to_fix="Use `element.textContent` or sanitize with DOMPurify.",
        simple="Assigning unescaped user input to innerHTML executes malicious JavaScript in the browser.",
        example="div.innerHTML = location.hash;",
        fix_example="div.textContent = location.hash;",
    ),
    "APS-JS-XSS-002": RuleExplanationTemplate(
        rule_id="APS-JS-XSS-002",
        language="javascript",
        cwe="CWE-79",
        severity="high",
        title="React dangerouslySetInnerHTML Vulnerability",
        what="A React component renders raw markup using `dangerouslySetInnerHTML` with user input.",
        why_dangerous="Bypasses React's built-in XSS protection.",
        how_attacker_uses_it="An attacker injects scripts that execute when other users view the component.",
        how_to_fix="Sanitize with `DOMPurify.sanitize()` before passing to `__html`.",
        simple="dangerouslySetInnerHTML disables React's automatic escaping, enabling XSS.",
        example="<div dangerouslySetInnerHTML={{ __html: postContent }} />",
        fix_example="<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(postContent) }} />",
    ),
    "APS-JS-NET-001": RuleExplanationTemplate(
        rule_id="APS-JS-NET-001",
        language="javascript",
        cwe="CWE-918",
        severity="high",
        title="SSRF via fetch / axios",
        what="Node.js issues HTTP requests to user-provided URLs using `fetch` or `axios`.",
        why_dangerous="Enables requests to internal cloud metadata and private microservices.",
        how_attacker_uses_it="An attacker probes internal network endpoints and accesses cloud credentials.",
        how_to_fix="Validate destination hostnames against an allowlist.",
        simple="Unvalidated fetch/axios calls allow attackers to reach internal network services.",
        example="await axios.get(req.query.url);",
        fix_example="if (isAllowedUrl(req.query.url)) await axios.get(req.query.url);",
    ),
    "APS-JS-INJ-003": RuleExplanationTemplate(
        rule_id="APS-JS-INJ-003",
        language="javascript",
        cwe="CWE-95",
        severity="medium",
        title="String Code Execution in Timer",
        what="The code passes a string rather than a callback function to `setTimeout` or `setInterval`.",
        why_dangerous="Timers evaluate string parameters similarly to `eval()`.",
        how_attacker_uses_it="An attacker manipulates the timer string to run injected code.",
        how_to_fix="Always pass a callback function to timers.",
        simple="Passing strings to setTimeout/setInterval evaluates code dynamically.",
        example="setTimeout('doWork(' + id + ')', 1000);",
        fix_example="setTimeout(() => doWork(id), 1000);",
    ),
    "APS-JS-IO-001": RuleExplanationTemplate(
        rule_id="APS-JS-IO-001",
        language="javascript",
        cwe="CWE-22",
        severity="high",
        title="Path Traversal in Node.js fs",
        what="The application passes user input to `fs.readFile()` or `fs.writeFile()` without resolution checks.",
        why_dangerous="Directory traversal sequences allow accessing files outside the target directory.",
        how_attacker_uses_it="An attacker retrieves configuration files containing keys or sensitive database info.",
        how_to_fix="Resolve paths with `path.resolve()` and verify prefix containment.",
        simple="Unsanitized path strings in fs calls allow directory traversal.",
        example="fs.readFile(baseDir + '/' + req.query.file);",
        fix_example="const safe = path.resolve(baseDir, req.query.file);\nif (safe.startsWith(baseDir)) fs.readFile(safe);",
    ),
    "APS-JS-NET-002": RuleExplanationTemplate(
        rule_id="APS-JS-NET-002",
        language="javascript",
        cwe="CWE-942",
        severity="medium",
        title="Overly Permissive CORS Policy",
        what="The server sets `Access-Control-Allow-Origin: *` while accepting credentials or sensitive endpoints.",
        why_dangerous="Any website can read authenticated responses from the user's browser.",
        how_attacker_uses_it="A malicious site makes cross-origin requests to read user account details.",
        how_to_fix="Specify exact trusted origin domains instead of wildcards.",
        simple="Wildcard CORS headers permit untrusted origins to read sensitive data.",
        example="res.setHeader('Access-Control-Allow-Origin', '*');",
        fix_example="res.setHeader('Access-Control-Allow-Origin', 'https://trusted.app.com');",
    ),
    "APS-JS-CRY-001": RuleExplanationTemplate(
        rule_id="APS-JS-CRY-001",
        language="javascript",
        cwe="CWE-327",
        severity="medium",
        title="Weak Hash Algorithm in Node.js",
        what="The application creates MD5 or SHA-1 hashes via `crypto.createHash()`.",
        why_dangerous="These algorithms have proven collision vulnerabilities.",
        how_attacker_uses_it="An attacker constructs colliding inputs with identical hash values.",
        how_to_fix="Use `crypto.createHash('sha256')`.",
        simple="MD5 and SHA-1 in Node.js provide insufficient collision resistance.",
        example="crypto.createHash('md5').update(data).digest('hex');",
        fix_example="crypto.createHash('sha256').update(data).digest('hex');",
    ),
    "APS-JS-CRY-002": RuleExplanationTemplate(
        rule_id="APS-JS-CRY-002",
        language="javascript",
        cwe="CWE-327",
        severity="medium",
        title="Insecure Cipher Algorithm in Node.js",
        what="The application initializes DES or ECB encryption via `crypto.createCipheriv()`.",
        why_dangerous="Inadequate key lengths and lack of authentication permit cryptanalysis.",
        how_attacker_uses_it="An attacker extracts ciphertext patterns or brute-forces keys.",
        how_to_fix="Use authenticated encryption such as `aes-256-gcm`.",
        simple="DES and ECB ciphers in Node.js fail modern confidentiality requirements.",
        example="crypto.createCipheriv('des-ecb', key, null);",
        fix_example="crypto.createCipheriv('aes-256-gcm', key, iv);",
    ),
    "APS-JS-SEC-001": RuleExplanationTemplate(
        rule_id="APS-JS-SEC-001",
        language="javascript",
        cwe="CWE-798",
        severity="high",
        title="Hardcoded API Key or Secret",
        what="The JavaScript source contains hardcoded secrets or API tokens.",
        why_dangerous="Frontend bundles and server repositories expose these secrets publicly.",
        how_attacker_uses_it="An attacker inspects bundle source maps or source repositories to steal credentials.",
        how_to_fix="Load secrets from environment variables (`process.env`).",
        simple="Hardcoded secrets in JavaScript are exposed in bundles and repository histories.",
        example="const token = 'ghp_secretTokenExample';",
        fix_example="const token = process.env.GITHUB_TOKEN;",
    ),
    "APS-JS-SEC-002": RuleExplanationTemplate(
        rule_id="APS-JS-SEC-002",
        language="javascript",
        cwe="CWE-614",
        severity="low",
        title="Insecure Cookie Flags",
        what="A cookie is set without `httpOnly` or `secure` flags.",
        why_dangerous="Cookies are accessible via client-side script and sent over unencrypted connections.",
        how_attacker_uses_it="An attacker uses XSS to read session cookies, or sniffs HTTP traffic.",
        how_to_fix="Set `httpOnly: true`, `secure: true`, and `sameSite: 'strict'`.",
        simple="Cookies without httpOnly and secure flags risk theft via XSS and traffic interception.",
        example="res.cookie('session', sid);",
        fix_example="res.cookie('session', sid, { httpOnly: true, secure: true, sameSite: 'strict' });",
    ),
    "APS-JS-INJ-004": RuleExplanationTemplate(
        rule_id="APS-JS-INJ-004",
        language="javascript",
        cwe="CWE-1321",
        severity="high",
        title="Prototype Pollution Vulnerability",
        what="Object assignment or recursive merge allows keys like `__proto__` or `constructor.prototype`.",
        why_dangerous="Polluting `Object.prototype` alters default properties across all objects in the runtime.",
        how_attacker_uses_it="An attacker injects properties like `isAdmin` or properties altering routing.",
        how_to_fix="Validate keys to reject `__proto__`, or use `Object.create(null)`.",
        simple="Merging unvalidated objects can pollute Object.prototype and compromise application logic.",
        example="Object.assign(target, JSON.parse(userInput));",
        fix_example="// Filter keys: if (key === '__proto__' || key === 'constructor') continue;",
    ),
    "APS-JS-INJ-005": RuleExplanationTemplate(
        rule_id="APS-JS-INJ-005",
        language="javascript",
        cwe="CWE-89",
        severity="high",
        title="SQL Injection in Node.js",
        what="The application builds database queries by concatenating input strings.",
        why_dangerous="Allows arbitrary SQL execution.",
        how_attacker_uses_it="An attacker extracts or modifies database records.",
        how_to_fix="Use parameterized queries with placeholders (`$1`, `?`).",
        simple="Concatenating input into SQL strings in Node.js permits SQL injection.",
        example="db.query(`SELECT * FROM users WHERE id = ${userId}`);",
        fix_example="db.query('SELECT * FROM users WHERE id = $1', [userId]);",
    ),
    "APS-JS-OBF-001": RuleExplanationTemplate(
        rule_id="APS-JS-OBF-001",
        language="javascript",
        cwe="CWE-116",
        severity="high",
        title="Obfuscated Code Execution in JavaScript",
        what="The code decodes strings using `atob()` or hex escape decoding and evaluates them dynamically.",
        why_dangerous="Hides payload logic from standard code inspection.",
        how_attacker_uses_it="An attacker delivers malware scripts disguised as encoded text.",
        how_to_fix="Remove dynamic decoding and execution of obfuscated payloads.",
        simple="Dynamic decoding and execution of obfuscated strings suggests evasive patterns.",
        example="eval(atob('YWxlcnQoMSk='));",
        fix_example="// Use explicit, unencoded JavaScript modules",
    ),
    "APS-JS-NET-003": RuleExplanationTemplate(
        rule_id="APS-JS-NET-003",
        language="javascript",
        cwe="CWE-295",
        severity="critical",
        title="TLS Certificate Validation Disabled (Node.js)",
        what="The application sets `rejectUnauthorized: false` or `NODE_TLS_REJECT_UNAUTHORIZED=0`.",
        why_dangerous="Disables SSL/TLS identity checks, allowing Man-in-the-Middle attacks.",
        how_attacker_uses_it="An attacker intercepts and alters sensitive traffic.",
        how_to_fix="Maintain `rejectUnauthorized: true` with valid certificates.",
        simple="Disabling certificate verification in Node.js exposes traffic to MITM interception.",
        example="const agent = new https.Agent({ rejectUnauthorized: false });",
        fix_example="const agent = new https.Agent({ rejectUnauthorized: true });",
    ),
    # ── C/C++ Rules ───────────────────────────────────────────────────────────
    "APS-CPP-MEM-001": RuleExplanationTemplate(
        rule_id="APS-CPP-MEM-001",
        language="cpp",
        cwe="CWE-120",
        severity="critical",
        title="Buffer Overflow via strcpy",
        what="The code copies strings using the unbounded `strcpy()` function.",
        why_dangerous="`strcpy` does not check target buffer bounds, overwriting stack frames when the source exceeds capacity.",
        how_attacker_uses_it="An attacker provides an oversized string to overwrite the instruction pointer (EIP/RIP) and hijack execution.",
        how_to_fix="Use bounds-checked functions such as `strncpy()`, `snprintf()`, or C++ `std::string`.",
        simple="strcpy copies strings without bounds checking, leading to stack buffer overflows.",
        example="char buf[64];\nstrcpy(buf, input);",
        fix_example="std::string buf = input;\n// or strncpy(buf, input, sizeof(buf) - 1);",
    ),
    "APS-CPP-MEM-002": RuleExplanationTemplate(
        rule_id="APS-CPP-MEM-002",
        language="cpp",
        cwe="CWE-120",
        severity="critical",
        title="Buffer Overflow via sprintf",
        what="The code formats output into a fixed-size buffer using unbounded `sprintf()`.",
        why_dangerous="`sprintf` writes past the end of the destination array if formatted characters exceed buffer length.",
        how_attacker_uses_it="An attacker inputs long strings to corrupt memory structures and execute shellcode.",
        how_to_fix="Use `snprintf()` specifying the exact buffer size, or `std::ostringstream`.",
        simple="sprintf formats into destination buffers without checking maximum capacity.",
        example='char msg[128];\nsprintf(msg, "Hello %s", name);',
        fix_example='snprintf(msg, sizeof(msg), "Hello %s", name);',
    ),
    "APS-CPP-MEM-003": RuleExplanationTemplate(
        rule_id="APS-CPP-MEM-003",
        language="cpp",
        cwe="CWE-120",
        severity="critical",
        title="Dangerous Input via gets",
        what="The code reads standard input into a buffer using `gets()`.",
        why_dangerous="`gets` has no mechanism to limit input length and was removed from the C standard library.",
        how_attacker_uses_it="An attacker streams characters to overflow the stack and alter program control flow.",
        how_to_fix="Replace with `fgets()` specifying maximum buffer size or `std::getline()`.",
        simple="gets() is inherently vulnerable to buffer overflows as it lacks bound limits.",
        example="char buf[256];\ngets(buf);",
        fix_example="fgets(buf, sizeof(buf), stdin);",
    ),
    "APS-CPP-MEM-004": RuleExplanationTemplate(
        rule_id="APS-CPP-MEM-004",
        language="cpp",
        cwe="CWE-120",
        severity="critical",
        title="Buffer Overflow via strcat",
        what="The code concatenates strings using unbounded `strcat()`.",
        why_dangerous="Appends characters without verifying remaining capacity in the destination array.",
        how_attacker_uses_it="An attacker provides input that exceeds remaining buffer bytes, corrupting memory.",
        how_to_fix="Use `strncat()` with remaining space calculation, or `std::string::append()`.",
        simple="strcat concatenates strings without verifying buffer space, causing memory corruption.",
        example="strcat(path, filename);",
        fix_example="strncat(path, filename, sizeof(path) - strlen(path) - 1);",
    ),
    "APS-CPP-FMT-001": RuleExplanationTemplate(
        rule_id="APS-CPP-FMT-001",
        language="cpp",
        cwe="CWE-134",
        severity="critical",
        title="Uncontrolled Format String",
        what="The code passes user-controlled strings directly as the format argument of `printf()` or `syslog()`.",
        why_dangerous="Format specifiers like `%x`, `%s`, and `%n` read stack data or write to arbitrary memory addresses.",
        how_attacker_uses_it="An attacker supplies `%p %p %p` to dump memory addresses or `%n` to overwrite return addresses.",
        how_to_fix='Use constant format specifiers: `printf("%s", user_str)`.',
        simple="Passing dynamic strings as format specifiers allows attackers to inspect or write arbitrary memory.",
        example="printf(user_input);",
        fix_example='printf("%s", user_input);',
    ),
    "APS-CPP-INJ-001": RuleExplanationTemplate(
        rule_id="APS-CPP-INJ-001",
        language="cpp",
        cwe="CWE-78",
        severity="critical",
        title="Command Injection via system()",
        what="The program passes a constructed command string to `system()`.",
        why_dangerous="The host shell executes chained shell operators.",
        how_attacker_uses_it="An attacker injects command separators to execute arbitrary binaries.",
        how_to_fix="Use `execve()` or POSIX `posix_spawn()` with explicit argument arrays.",
        simple="system() executes command strings through the shell without argument isolation.",
        example="system(cmd_buf);",
        fix_example="// Use execv() or posix_spawnp() with an argv array",
    ),
    "APS-CPP-INJ-002": RuleExplanationTemplate(
        rule_id="APS-CPP-INJ-002",
        language="cpp",
        cwe="CWE-78",
        severity="critical",
        title="Command Injection via popen()",
        what="The application invokes `popen()` with a dynamically constructed command.",
        why_dangerous="`popen` forks a shell interpreter susceptible to argument hijacking.",
        how_attacker_uses_it="An attacker escapes the command to execute host utilities.",
        how_to_fix="Use pipe-based IPC with `fork()` and `execvp()`.",
        simple="popen() executes commands via the shell, allowing command injection.",
        example='FILE* f = popen(cmd, "r");',
        fix_example="// Use pipe(), fork(), and execvp() for safe execution",
    ),
    "APS-CPP-SEC-001": RuleExplanationTemplate(
        rule_id="APS-CPP-SEC-001",
        language="cpp",
        cwe="CWE-798",
        severity="high",
        title="Hardcoded Secret in C/C++",
        what="The binary contains hardcoded secret or cryptographic key string literals.",
        why_dangerous="Strings in compiled C/C++ binaries are extracted with the `strings` command or reverse engineering.",
        how_attacker_uses_it="An attacker runs `strings binary | grep -i key` to retrieve sensitive credentials.",
        how_to_fix="Load secrets from secure runtime configuration or environment variables.",
        simple="Hardcoded strings in compiled C/C++ binaries are easily recovered with reverse engineering.",
        example='const char* apiKey = "super_secret_key_12345";',
        fix_example='const char* apiKey = std::getenv("API_KEY");',
    ),
    "APS-CPP-CRY-001": RuleExplanationTemplate(
        rule_id="APS-CPP-CRY-001",
        language="cpp",
        cwe="CWE-330",
        severity="low",
        title="Predictable Random Number Generator (rand)",
        what="The program uses standard `rand()` for security-critical decisions.",
        why_dangerous="`rand()` produces predictable pseudorandom sequences easily reconstructed by attackers.",
        how_attacker_uses_it="An attacker predicts session tokens or security numbers.",
        how_to_fix="Use C++11 `<random>` with `std::random_device` or cryptographic OS APIs.",
        simple="rand() is predictable and unsuited for cryptographic security.",
        example="int token = rand();",
        fix_example="std::random_device rd; std::mt19937 gen(rd());",
    ),
    "APS-CPP-IO-001": RuleExplanationTemplate(
        rule_id="APS-CPP-IO-001",
        language="cpp",
        cwe="CWE-22",
        severity="high",
        title="Path Traversal in C/C++ fopen",
        what="The program passes unverified path strings to `fopen()` or `std::ifstream`.",
        why_dangerous="Enables reading or writing files outside the authorized working directory.",
        how_attacker_uses_it="An attacker retrieves sensitive system files.",
        how_to_fix="Canonicalize paths with `realpath()` and check directory prefixes.",
        simple="Unsanitized paths in fopen permit directory traversal attacks.",
        example='FILE* fp = fopen(filepath, "r");',
        fix_example='char resolved[PATH_MAX];\nif (realpath(filepath, resolved) && strncmp(resolved, base, strlen(base)) == 0) fopen(resolved, "r");',
    ),
    # ── Generic Unicode Rules ─────────────────────────────────────────────────
    "APS-ALL-UNI-001": RuleExplanationTemplate(
        rule_id="APS-ALL-UNI-001",
        language="all",
        cwe="CWE-1007",
        severity="critical",
        title="Bidi Control Character (Trojan Source, CVE-2021-42574)",
        what="Source text contains bidirectional control characters (e.g. U+202E RLO, U+202D LRO, U+2066 LRI).",
        why_dangerous="Manipulates text rendering direction in code editors and web viewers so code appears different than compiler interpretation.",
        how_attacker_uses_it="An attacker hides execution logic inside what appears to be a commented-out line or benign condition.",
        how_to_fix="Strip bidirectional override characters from source code.",
        simple="Bidirectional Unicode overrides disguise malicious code from visual code review.",
        example="/* begin admin check \u202e \u2066 if (user.isAdmin) \u2069 */",
        fix_example="/* begin admin check */ if (user.isAdmin)",
    ),
    "APS-ALL-UNI-002": RuleExplanationTemplate(
        rule_id="APS-ALL-UNI-002",
        language="all",
        cwe="CWE-1007",
        severity="high",
        title="Zero-Width or Invisible Character in Code",
        what="Source text contains invisible zero-width characters (e.g. U+200B Zero-Width Space).",
        why_dangerous="Invisible characters create distinct identifiers that visually appear identical to existing variables.",
        how_attacker_uses_it="An attacker defines a shadow variable with identical visual appearance to hijack logic.",
        how_to_fix="Purge zero-width formatting characters from code files.",
        simple="Zero-width characters create visually identical shadow identifiers.",
        example="const admin\u200b = false;",
        fix_example="const admin = false;",
    ),
    "APS-ALL-UNI-003": RuleExplanationTemplate(
        rule_id="APS-ALL-UNI-003",
        language="all",
        cwe="CWE-1007",
        severity="high",
        title="Unicode Tag Characters in Source",
        what="Source code contains invisible Unicode tag characters (U+E0000..U+E007F).",
        why_dangerous="Used to smuggle invisible payloads or fingerprint source text.",
        how_attacker_uses_it="An attacker embeds hidden metadata or bypasses token filters.",
        how_to_fix="Remove all Unicode tag plane characters from source code.",
        simple="Unicode tag plane characters smuggle invisible data inside source files.",
        example="var x\U000e0001 = 1;",
        fix_example="var x = 1;",
    ),
    "APS-ALL-UNI-004": RuleExplanationTemplate(
        rule_id="APS-ALL-UNI-004",
        language="all",
        cwe="CWE-1007",
        severity="high",
        title="Confusable Character in Identifier",
        what="An identifier contains non-ASCII characters that visually mimic ASCII letters.",
        why_dangerous="Homoglyphs trick human reviewers while pointing to completely separate variables or functions.",
        how_attacker_uses_it="An attacker overrides safety checks by replacing a character with a Cyrillic or Greek lookalike.",
        how_to_fix="Normalize all homoglyphs to ASCII equivalents.",
        simple="Unicode lookalike characters spoof trusted variable and function names.",
        example="int p\u0430ssword = 123; // Cyrillic \u0430",
        fix_example="int password = 123;",
    ),
    "APS-ALL-UNI-005": RuleExplanationTemplate(
        rule_id="APS-ALL-UNI-005",
        language="all",
        cwe="CWE-1007",
        severity="medium",
        title="Mixed-Script Identifier",
        what="An identifier combines characters from multiple distinct Unicode scripts (e.g. Latin and Cyrillic).",
        why_dangerous="Mixed scripts are an established signature of homoglyph evasion techniques.",
        how_attacker_uses_it="An attacker evades simple string search filters while masquerading as standard identifiers.",
        how_to_fix="Restrict each identifier to a single uniform script (standard ASCII).",
        simple="Combining multiple scripts inside a single identifier indicates spoofing.",
        example="int v\u0430rName = 1;",
        fix_example="int varName = 1;",
    ),
    "APS-ALL-UNI-006": RuleExplanationTemplate(
        rule_id="APS-ALL-UNI-006",
        language="all",
        cwe="CWE-1007",
        severity="critical",
        title="Confusable Recovering to Dangerous API",
        what="A homoglyph identifier normalizes to a high-risk security API (e.g. 'еxec' -> 'exec').",
        why_dangerous="Masks invocation of dangerous system APIs behind lookalike characters.",
        how_attacker_uses_it="An attacker disguises command execution calls as custom innocuous functions.",
        how_to_fix="Replace confusable homoglyphs with standard ASCII API names.",
        simple="Homoglyph identifier visually mimics dangerous execution APIs.",
        example="\u0435xec(command); // Cyrillic \u0435",
        fix_example="exec(command);",
    ),
    # ── ML Anomaly Rule ───────────────────────────────────────────────────────
    "APS-ALL-ML-001": RuleExplanationTemplate(
        rule_id="APS-ALL-ML-001",
        language="all",
        cwe="CWE-1007",
        severity="medium",
        title="Machine Learning Token Anomaly",
        what="The calibrated bidirectional LSTM model flagged this token context as anomalous and high-risk.",
        why_dangerous="Statistical context features resemble malicious exploit patterns learned from dataset training.",
        how_attacker_uses_it="An attacker introduces novel or obfuscated sequences that deviate from standard token statistics.",
        how_to_fix="Review the surrounding token sequence and verify whether the construction adheres to standard idioms.",
        simple="The ML model identified anomalous token patterns resembling malicious constructions.",
        example="// Statistical anomaly in token feature distribution",
        fix_example="// Verify token context against established project idioms",
    ),
}


def get_rule_template(rule_id: str) -> RuleExplanationTemplate | None:
    """Retrieve explanation template for given rule ID."""
    return RULE_TEMPLATES.get(rule_id.strip())


def format_explanation(
    finding: Finding,
    source: str = "",
) -> tuple[str, str]:
    """Format concrete variable and line names into simple and detailed explanations.

    Example concrete sentence:
      "Line 7 passes `name`, which comes from request.args on line 3, into os.system."

    Args:
        finding: Finding instance with coordinates, evidence, and taint path.
        source: Optional source code for extra context extraction.

    Returns:
        tuple[str, str]: (simple_explanation, detailed_explanation)
    """
    tmpl = get_rule_template(finding.rule_id)
    sink_line = finding.range.start_line

    # Concrete details from taint path or evidence
    var_name = ""
    source_expr = ""
    source_line = 0
    sink_name = ""

    if finding.taint_path:
        for step in finding.taint_path:
            step_kind = getattr(step, "step", "")
            if step_kind in ("source", "source_var"):
                source_expr = step.text or step.note or "untrusted input"
                source_line = step.range.start_line
                var_name = step.text or "input"
            elif step_kind in ("sink", "sink_call"):
                sink_name = step.text or "sink"

    if not var_name and "variable" in finding.evidence:
        var_name = str(finding.evidence["variable"])
    if not sink_name and "sink" in finding.evidence:
        sink_name = str(finding.evidence["sink"])
    if not source_expr and "source" in finding.evidence:
        source_expr = str(finding.evidence["source"])

    # Fallback to token text from message or source lines
    if not var_name:
        words = finding.message.split()
        for w in words:
            if w.startswith("`") and w.endswith("`"):
                var_name = w.strip("`")
                break

    # Build concrete trace sentence
    concrete_sentence = ""
    if source_line and var_name and sink_name and source_expr:
        concrete_sentence = f"Line {sink_line} passes `{var_name}`, which comes from {source_expr} on line {source_line}, into {sink_name}."
    elif var_name and sink_name:
        concrete_sentence = (
            f"Line {sink_line} passes `{var_name}` into `{sink_name}` without validation."
        )
    elif var_name:
        concrete_sentence = f"Line {sink_line} uses `{var_name}` in a high-risk security context."
    else:
        concrete_sentence = f"Line {sink_line} triggers rule {finding.rule_id}: {finding.message}."

    if tmpl:
        simple = f"{concrete_sentence} {tmpl.simple}"
        detailed = (
            f"### What\n{concrete_sentence}\n\n{tmpl.what}\n\n"
            f"### Why It Is Dangerous\n{tmpl.why_dangerous}\n\n"
            f"### How an Attacker Uses It\n{tmpl.how_attacker_uses_it}\n\n"
            f"### How to Fix\n{tmpl.how_to_fix}"
        )
    else:
        simple = concrete_sentence
        detailed = (
            f"### What\n{concrete_sentence}\n\n"
            f"### Why It Is Dangerous\nThis construct matches security rule `{finding.rule_id}` ({finding.cwe}).\n\n"
            f"### How an Attacker Uses It\nAn attacker can exploit unvalidated inputs reaching this execution point.\n\n"
            f"### How to Fix\nApply input validation and use safe APIs."
        )

    return simple, detailed


def generate_rules_catalogue(output_file: Path | None = None) -> str:
    """Auto-generate docs/rules_catalogue.md from the rules templates catalog.

    Includes (id, language, CWE, severity, description, example, fix).

    Args:
        output_file: Optional path to write markdown file.

    Returns:
        Generated markdown content.
    """
    lines: list[str] = [
        "# SecureLex IDE — Rules Catalogue",
        "",
        "Comprehensive inventory of all deterministic security, Unicode, and ML analysis rules supported by SecureLex IDE.",
        "",
        "| Rule ID | Language | CWE | Severity | Description |",
        "|---|---|---|---|---|",
    ]

    for rule_id, tmpl in sorted(RULE_TEMPLATES.items()):
        lines.append(
            f"| `{tmpl.rule_id}` | {tmpl.language.capitalize()} | {tmpl.cwe} | {tmpl.severity.upper()} | {tmpl.title} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Detailed Rule Specifications",
            "",
        ]
    )

    for rule_id, tmpl in sorted(RULE_TEMPLATES.items()):
        lines.extend(
            [
                f"### {tmpl.rule_id} — {tmpl.title}",
                "",
                f"- **Language:** {tmpl.language.capitalize()}",
                f"- **CWE:** {tmpl.cwe}",
                f"- **Severity:** {tmpl.severity.upper()}",
                "",
                "#### What It Detects",
                tmpl.what,
                "",
                "#### Why It Is Dangerous",
                tmpl.why_dangerous,
                "",
                "#### How an Attacker Uses It",
                tmpl.how_attacker_uses_it,
                "",
                "#### How to Fix",
                tmpl.how_to_fix,
                "",
            ]
        )
        if tmpl.example:
            lang_syntax = "python" if tmpl.language in ("python", "all") else tmpl.language
            lines.extend(
                [
                    "#### Vulnerable Example",
                    f"```{lang_syntax}",
                    tmpl.example,
                    "```",
                    "",
                ]
            )
        if tmpl.fix_example:
            lang_syntax = "python" if tmpl.language in ("python", "all") else tmpl.language
            lines.extend(
                [
                    "#### Remediated Fix",
                    f"```{lang_syntax}",
                    tmpl.fix_example,
                    "```",
                    "",
                ]
            )
        lines.append("---")
        lines.append("")

    content = "\n".join(lines)
    if output_file is not None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")

    return content
