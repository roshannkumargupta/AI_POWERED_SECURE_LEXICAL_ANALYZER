# SecureLex IDE — Rules Catalogue

Comprehensive inventory of all deterministic security, Unicode, and ML analysis rules supported by SecureLex IDE.

| Rule ID | Language | CWE | Severity | Description |
|---|---|---|---|---|
| `APS-ALL-ML-001` | All | CWE-1007 | MEDIUM | Machine Learning Token Anomaly |
| `APS-ALL-UNI-001` | All | CWE-1007 | CRITICAL | Bidi Control Character (Trojan Source, CVE-2021-42574) |
| `APS-ALL-UNI-002` | All | CWE-1007 | HIGH | Zero-Width or Invisible Character in Code |
| `APS-ALL-UNI-003` | All | CWE-1007 | HIGH | Unicode Tag Characters in Source |
| `APS-ALL-UNI-004` | All | CWE-1007 | HIGH | Confusable Character in Identifier |
| `APS-ALL-UNI-005` | All | CWE-1007 | MEDIUM | Mixed-Script Identifier |
| `APS-ALL-UNI-006` | All | CWE-1007 | CRITICAL | Confusable Recovering to Dangerous API |
| `APS-CPP-CRY-001` | Cpp | CWE-330 | LOW | Predictable Random Number Generator (rand) |
| `APS-CPP-FMT-001` | Cpp | CWE-134 | CRITICAL | Uncontrolled Format String |
| `APS-CPP-INJ-001` | Cpp | CWE-78 | CRITICAL | Command Injection via system() |
| `APS-CPP-INJ-002` | Cpp | CWE-78 | CRITICAL | Command Injection via popen() |
| `APS-CPP-IO-001` | Cpp | CWE-22 | HIGH | Path Traversal in C/C++ fopen |
| `APS-CPP-MEM-001` | Cpp | CWE-120 | CRITICAL | Buffer Overflow via strcpy |
| `APS-CPP-MEM-002` | Cpp | CWE-120 | CRITICAL | Buffer Overflow via sprintf |
| `APS-CPP-MEM-003` | Cpp | CWE-120 | CRITICAL | Dangerous Input via gets |
| `APS-CPP-MEM-004` | Cpp | CWE-120 | CRITICAL | Buffer Overflow via strcat |
| `APS-CPP-SEC-001` | Cpp | CWE-798 | HIGH | Hardcoded Secret in C/C++ |
| `APS-JS-CRY-001` | Javascript | CWE-327 | MEDIUM | Weak Hash Algorithm in Node.js |
| `APS-JS-CRY-002` | Javascript | CWE-327 | MEDIUM | Insecure Cipher Algorithm in Node.js |
| `APS-JS-INJ-001` | Javascript | CWE-95 | CRITICAL | Arbitrary Code Execution via eval() or Function() |
| `APS-JS-INJ-002` | Javascript | CWE-78 | CRITICAL | Command Injection via child_process.exec |
| `APS-JS-INJ-003` | Javascript | CWE-95 | MEDIUM | String Code Execution in Timer |
| `APS-JS-INJ-004` | Javascript | CWE-1321 | HIGH | Prototype Pollution Vulnerability |
| `APS-JS-INJ-005` | Javascript | CWE-89 | HIGH | SQL Injection in Node.js |
| `APS-JS-IO-001` | Javascript | CWE-22 | HIGH | Path Traversal in Node.js fs |
| `APS-JS-NET-001` | Javascript | CWE-918 | HIGH | SSRF via fetch / axios |
| `APS-JS-NET-002` | Javascript | CWE-942 | MEDIUM | Overly Permissive CORS Policy |
| `APS-JS-NET-003` | Javascript | CWE-295 | CRITICAL | TLS Certificate Validation Disabled (Node.js) |
| `APS-JS-OBF-001` | Javascript | CWE-116 | HIGH | Obfuscated Code Execution in JavaScript |
| `APS-JS-SEC-001` | Javascript | CWE-798 | HIGH | Hardcoded API Key or Secret |
| `APS-JS-SEC-002` | Javascript | CWE-614 | LOW | Insecure Cookie Flags |
| `APS-JS-XSS-001` | Javascript | CWE-79 | HIGH | DOM-Based XSS via innerHTML |
| `APS-JS-XSS-002` | Javascript | CWE-79 | HIGH | React dangerouslySetInnerHTML Vulnerability |
| `APS-JV-CRY-001` | Java | CWE-327 | MEDIUM | Weak Hash Algorithm in Java (MD5/SHA-1) |
| `APS-JV-CRY-002` | Java | CWE-327 | MEDIUM | Insecure Cipher / ECB Mode |
| `APS-JV-CRY-003` | Java | CWE-330 | LOW | Insecure Random Number Generator |
| `APS-JV-DES-001` | Java | CWE-502 | CRITICAL | Untrusted Java Deserialization |
| `APS-JV-INJ-001` | Java | CWE-78 | CRITICAL | Command Injection via Runtime.exec |
| `APS-JV-INJ-002` | Java | CWE-78 | CRITICAL | Command Injection via ProcessBuilder |
| `APS-JV-INJ-003` | Java | CWE-89 | HIGH | SQL Injection via JDBC Statement |
| `APS-JV-INJ-004` | Java | CWE-89 | HIGH | HQL / JPQL Injection |
| `APS-JV-IO-001` | Java | CWE-22 | HIGH | Path Traversal in Java File Access |
| `APS-JV-NET-001` | Java | CWE-918 | HIGH | Java SSRF via URL Connection |
| `APS-JV-NET-002` | Java | CWE-295 | CRITICAL | TLS Certificate Validation Disabled |
| `APS-JV-SEC-001` | Java | CWE-798 | HIGH | Hardcoded Password or Key in Java |
| `APS-JV-UNI-001` | Java | CWE-1007 | HIGH | Confusable or Homoglyph Identifier in Java |
| `APS-JV-XML-001` | Java | CWE-611 | HIGH | XML External Entity (XXE) Injection |
| `APS-JV-XSS-001` | Java | CWE-79 | HIGH | Reflected XSS in Servlet Response |
| `APS-PY-CRY-001` | Python | CWE-327 | MEDIUM | Broken Hash Algorithm (MD5/SHA1) |
| `APS-PY-CRY-002` | Python | CWE-327 | MEDIUM | Weak Cipher Algorithm (DES/ECB) |
| `APS-PY-DES-001` | Python | CWE-502 | CRITICAL | Untrusted Deserialization via pickle |
| `APS-PY-DES-002` | Python | CWE-502 | CRITICAL | Insecure YAML Deserialization |
| `APS-PY-INJ-001` | Python | CWE-95 | CRITICAL | Arbitrary Code Execution via eval/exec |
| `APS-PY-INJ-002` | Python | CWE-78 | CRITICAL | Command Injection via os.system |
| `APS-PY-INJ-003` | Python | CWE-78 | CRITICAL | Subprocess Shell Injection |
| `APS-PY-INJ-004` | Python | CWE-89 | HIGH | SQL Injection via Query Formatting |
| `APS-PY-INJ-005` | Python | CWE-94 | HIGH | Server-Side Template Injection |
| `APS-PY-IO-001` | Python | CWE-22 | HIGH | Path Traversal via File Access |
| `APS-PY-NET-001` | Python | CWE-918 | HIGH | Server-Side Request Forgery (SSRF) |
| `APS-PY-OBF-001` | Python | CWE-116 | HIGH | Obfuscated Payload Execution |
| `APS-PY-SEC-001` | Python | CWE-798 | HIGH | Hardcoded Credential or Secret |
| `APS-PY-XSS-001` | Python | CWE-79 | HIGH | Cross-Site Scripting via Dynamic HTML |

---

## Detailed Rule Specifications

### APS-ALL-ML-001 — Machine Learning Token Anomaly

- **Language:** All
- **CWE:** CWE-1007
- **Severity:** MEDIUM

#### What It Detects
The calibrated bidirectional LSTM model flagged this token context as anomalous and high-risk.

#### Why It Is Dangerous
Statistical context features resemble malicious exploit patterns learned from dataset training.

#### How an Attacker Uses It
An attacker introduces novel or obfuscated sequences that deviate from standard token statistics.

#### How to Fix
Review the surrounding token sequence and verify whether the construction adheres to standard idioms.

#### Vulnerable Example
```python
// Statistical anomaly in token feature distribution
```

#### Remediated Fix
```python
// Verify token context against established project idioms
```

---

### APS-ALL-UNI-001 — Bidi Control Character (Trojan Source, CVE-2021-42574)

- **Language:** All
- **CWE:** CWE-1007
- **Severity:** CRITICAL

#### What It Detects
Source text contains bidirectional control characters (e.g. U+202E RLO, U+202D LRO, U+2066 LRI).

#### Why It Is Dangerous
Manipulates text rendering direction in code editors and web viewers so code appears different than compiler interpretation.

#### How an Attacker Uses It
An attacker hides execution logic inside what appears to be a commented-out line or benign condition.

#### How to Fix
Strip bidirectional override characters from source code.

#### Vulnerable Example
```python
/* begin admin check ‮ ⁦ if (user.isAdmin) ⁩ */
```

#### Remediated Fix
```python
/* begin admin check */ if (user.isAdmin)
```

---

### APS-ALL-UNI-002 — Zero-Width or Invisible Character in Code

- **Language:** All
- **CWE:** CWE-1007
- **Severity:** HIGH

#### What It Detects
Source text contains invisible zero-width characters (e.g. U+200B Zero-Width Space).

#### Why It Is Dangerous
Invisible characters create distinct identifiers that visually appear identical to existing variables.

#### How an Attacker Uses It
An attacker defines a shadow variable with identical visual appearance to hijack logic.

#### How to Fix
Purge zero-width formatting characters from code files.

#### Vulnerable Example
```python
const admin​ = false;
```

#### Remediated Fix
```python
const admin = false;
```

---

### APS-ALL-UNI-003 — Unicode Tag Characters in Source

- **Language:** All
- **CWE:** CWE-1007
- **Severity:** HIGH

#### What It Detects
Source code contains invisible Unicode tag characters (U+E0000..U+E007F).

#### Why It Is Dangerous
Used to smuggle invisible payloads or fingerprint source text.

#### How an Attacker Uses It
An attacker embeds hidden metadata or bypasses token filters.

#### How to Fix
Remove all Unicode tag plane characters from source code.

#### Vulnerable Example
```python
var x󠀁 = 1;
```

#### Remediated Fix
```python
var x = 1;
```

---

### APS-ALL-UNI-004 — Confusable Character in Identifier

- **Language:** All
- **CWE:** CWE-1007
- **Severity:** HIGH

#### What It Detects
An identifier contains non-ASCII characters that visually mimic ASCII letters.

#### Why It Is Dangerous
Homoglyphs trick human reviewers while pointing to completely separate variables or functions.

#### How an Attacker Uses It
An attacker overrides safety checks by replacing a character with a Cyrillic or Greek lookalike.

#### How to Fix
Normalize all homoglyphs to ASCII equivalents.

#### Vulnerable Example
```python
int pаssword = 123; // Cyrillic а
```

#### Remediated Fix
```python
int password = 123;
```

---

### APS-ALL-UNI-005 — Mixed-Script Identifier

- **Language:** All
- **CWE:** CWE-1007
- **Severity:** MEDIUM

#### What It Detects
An identifier combines characters from multiple distinct Unicode scripts (e.g. Latin and Cyrillic).

#### Why It Is Dangerous
Mixed scripts are an established signature of homoglyph evasion techniques.

#### How an Attacker Uses It
An attacker evades simple string search filters while masquerading as standard identifiers.

#### How to Fix
Restrict each identifier to a single uniform script (standard ASCII).

#### Vulnerable Example
```python
int vаrName = 1;
```

#### Remediated Fix
```python
int varName = 1;
```

---

### APS-ALL-UNI-006 — Confusable Recovering to Dangerous API

- **Language:** All
- **CWE:** CWE-1007
- **Severity:** CRITICAL

#### What It Detects
A homoglyph identifier normalizes to a high-risk security API (e.g. 'еxec' -> 'exec').

#### Why It Is Dangerous
Masks invocation of dangerous system APIs behind lookalike characters.

#### How an Attacker Uses It
An attacker disguises command execution calls as custom innocuous functions.

#### How to Fix
Replace confusable homoglyphs with standard ASCII API names.

#### Vulnerable Example
```python
еxec(command); // Cyrillic е
```

#### Remediated Fix
```python
exec(command)
```

---

### APS-CPP-CRY-001 — Predictable Random Number Generator (rand)

- **Language:** Cpp
- **CWE:** CWE-330
- **Severity:** LOW

#### What It Detects
The program uses standard `rand()` for security-critical decisions.

#### Why It Is Dangerous
`rand()` produces predictable pseudorandom sequences easily reconstructed by attackers.

#### How an Attacker Uses It
An attacker predicts session tokens or security numbers.

#### How to Fix
Use C++11 `<random>` with `std::random_device` or cryptographic OS APIs.

#### Vulnerable Example
```cpp
int token = rand();
```

#### Remediated Fix
```cpp
std::random_device rd; std::mt19937 gen(rd());
```

---

### APS-CPP-FMT-001 — Uncontrolled Format String

- **Language:** Cpp
- **CWE:** CWE-134
- **Severity:** CRITICAL

#### What It Detects
The code passes user-controlled strings directly as the format argument of `printf()` or `syslog()`.

#### Why It Is Dangerous
Format specifiers like `%x`, `%s`, and `%n` read stack data or write to arbitrary memory addresses.

#### How an Attacker Uses It
An attacker supplies `%p %p %p` to dump memory addresses or `%n` to overwrite return addresses.

#### How to Fix
Use constant format specifiers: `printf("%s", user_str)`.

#### Vulnerable Example
```cpp
printf(user_input);
```

#### Remediated Fix
```cpp
printf("%s", user_input);
```

---

### APS-CPP-INJ-001 — Command Injection via system()

- **Language:** Cpp
- **CWE:** CWE-78
- **Severity:** CRITICAL

#### What It Detects
The program passes a constructed command string to `system()`.

#### Why It Is Dangerous
The host shell executes chained shell operators.

#### How an Attacker Uses It
An attacker injects command separators to execute arbitrary binaries.

#### How to Fix
Use `execve()` or POSIX `posix_spawn()` with explicit argument arrays.

#### Vulnerable Example
```cpp
system(cmd_buf);
```

#### Remediated Fix
```cpp
// Use execv() or posix_spawnp() with an argv array
```

---

### APS-CPP-INJ-002 — Command Injection via popen()

- **Language:** Cpp
- **CWE:** CWE-78
- **Severity:** CRITICAL

#### What It Detects
The application invokes `popen()` with a dynamically constructed command.

#### Why It Is Dangerous
`popen` forks a shell interpreter susceptible to argument hijacking.

#### How an Attacker Uses It
An attacker escapes the command to execute host utilities.

#### How to Fix
Use pipe-based IPC with `fork()` and `execvp()`.

#### Vulnerable Example
```cpp
FILE* f = popen(cmd, "r");
```

#### Remediated Fix
```cpp
// Use pipe(), fork(), and execvp() for safe execution
```

---

### APS-CPP-IO-001 — Path Traversal in C/C++ fopen

- **Language:** Cpp
- **CWE:** CWE-22
- **Severity:** HIGH

#### What It Detects
The program passes unverified path strings to `fopen()` or `std::ifstream`.

#### Why It Is Dangerous
Enables reading or writing files outside the authorized working directory.

#### How an Attacker Uses It
An attacker retrieves sensitive system files.

#### How to Fix
Canonicalize paths with `realpath()` and check directory prefixes.

#### Vulnerable Example
```cpp
FILE* fp = fopen(filepath, "r");
```

#### Remediated Fix
```cpp
char resolved[PATH_MAX];
if (realpath(filepath, resolved) && strncmp(resolved, base, strlen(base)) == 0) fopen(resolved, "r");
```

---

### APS-CPP-MEM-001 — Buffer Overflow via strcpy

- **Language:** Cpp
- **CWE:** CWE-120
- **Severity:** CRITICAL

#### What It Detects
The code copies strings using the unbounded `strcpy()` function.

#### Why It Is Dangerous
`strcpy` does not check target buffer bounds, overwriting stack frames when the source exceeds capacity.

#### How an Attacker Uses It
An attacker provides an oversized string to overwrite the instruction pointer (EIP/RIP) and hijack execution.

#### How to Fix
Use bounds-checked functions such as `strncpy()`, `snprintf()`, or C++ `std::string`.

#### Vulnerable Example
```cpp
char buf[64];
strcpy(buf, input);
```

#### Remediated Fix
```cpp
std::string buf = input;
// or strncpy(buf, input, sizeof(buf) - 1);
```

---

### APS-CPP-MEM-002 — Buffer Overflow via sprintf

- **Language:** Cpp
- **CWE:** CWE-120
- **Severity:** CRITICAL

#### What It Detects
The code formats output into a fixed-size buffer using unbounded `sprintf()`.

#### Why It Is Dangerous
`sprintf` writes past the end of the destination array if formatted characters exceed buffer length.

#### How an Attacker Uses It
An attacker inputs long strings to corrupt memory structures and execute shellcode.

#### How to Fix
Use `snprintf()` specifying the exact buffer size, or `std::ostringstream`.

#### Vulnerable Example
```cpp
char msg[128];
sprintf(msg, "Hello %s", name);
```

#### Remediated Fix
```cpp
snprintf(msg, sizeof(msg), "Hello %s", name);
```

---

### APS-CPP-MEM-003 — Dangerous Input via gets

- **Language:** Cpp
- **CWE:** CWE-120
- **Severity:** CRITICAL

#### What It Detects
The code reads standard input into a buffer using `gets()`.

#### Why It Is Dangerous
`gets` has no mechanism to limit input length and was removed from the C standard library.

#### How an Attacker Uses It
An attacker streams characters to overflow the stack and alter program control flow.

#### How to Fix
Replace with `fgets()` specifying maximum buffer size or `std::getline()`.

#### Vulnerable Example
```cpp
char buf[256];
gets(buf);
```

#### Remediated Fix
```cpp
fgets(buf, sizeof(buf), stdin);
```

---

### APS-CPP-MEM-004 — Buffer Overflow via strcat

- **Language:** Cpp
- **CWE:** CWE-120
- **Severity:** CRITICAL

#### What It Detects
The code concatenates strings using unbounded `strcat()`.

#### Why It Is Dangerous
Appends characters without verifying remaining capacity in the destination array.

#### How an Attacker Uses It
An attacker provides input that exceeds remaining buffer bytes, corrupting memory.

#### How to Fix
Use `strncat()` with remaining space calculation, or `std::string::append()`.

#### Vulnerable Example
```cpp
strcat(path, filename);
```

#### Remediated Fix
```cpp
strncat(path, filename, sizeof(path) - strlen(path) - 1);
```

---

### APS-CPP-SEC-001 — Hardcoded Secret in C/C++

- **Language:** Cpp
- **CWE:** CWE-798
- **Severity:** HIGH

#### What It Detects
The binary contains hardcoded secret or cryptographic key string literals.

#### Why It Is Dangerous
Strings in compiled C/C++ binaries are extracted with the `strings` command or reverse engineering.

#### How an Attacker Uses It
An attacker runs `strings binary | grep -i key` to retrieve sensitive credentials.

#### How to Fix
Load secrets from secure runtime configuration or environment variables.

#### Vulnerable Example
```cpp
const char* apiKey = "super_secret_key_12345";
```

#### Remediated Fix
```cpp
const char* apiKey = std::getenv("API_KEY");
```

---

### APS-JS-CRY-001 — Weak Hash Algorithm in Node.js

- **Language:** Javascript
- **CWE:** CWE-327
- **Severity:** MEDIUM

#### What It Detects
The application creates MD5 or SHA-1 hashes via `crypto.createHash()`.

#### Why It Is Dangerous
These algorithms have proven collision vulnerabilities.

#### How an Attacker Uses It
An attacker constructs colliding inputs with identical hash values.

#### How to Fix
Use `crypto.createHash('sha256')`.

#### Vulnerable Example
```javascript
crypto.createHash('md5').update(data).digest('hex');
```

#### Remediated Fix
```javascript
crypto.createHash('sha256').update(data).digest('hex');
```

---

### APS-JS-CRY-002 — Insecure Cipher Algorithm in Node.js

- **Language:** Javascript
- **CWE:** CWE-327
- **Severity:** MEDIUM

#### What It Detects
The application initializes DES or ECB encryption via `crypto.createCipheriv()`.

#### Why It Is Dangerous
Inadequate key lengths and lack of authentication permit cryptanalysis.

#### How an Attacker Uses It
An attacker extracts ciphertext patterns or brute-forces keys.

#### How to Fix
Use authenticated encryption such as `aes-256-gcm`.

#### Vulnerable Example
```javascript
crypto.createCipheriv('des-ecb', key, null);
```

#### Remediated Fix
```javascript
crypto.createCipheriv('aes-256-gcm', key, iv);
```

---

### APS-JS-INJ-001 — Arbitrary Code Execution via eval() or Function()

- **Language:** Javascript
- **CWE:** CWE-95
- **Severity:** CRITICAL

#### What It Detects
The code passes dynamic strings to `eval()` or `new Function()` in JavaScript.

#### Why It Is Dangerous
Strings are evaluated with access to scope variables and runtime APIs.

#### How an Attacker Uses It
An attacker injects arbitrary JavaScript to compromise frontend sessions or backend Node processes.

#### How to Fix
Use structured data parsing (`JSON.parse()`) instead of code evaluation.

#### Vulnerable Example
```javascript
eval('data = ' + userJson);
```

#### Remediated Fix
```javascript
const data = JSON.parse(userJson);
```

---

### APS-JS-INJ-002 — Command Injection via child_process.exec

- **Language:** Javascript
- **CWE:** CWE-78
- **Severity:** CRITICAL

#### What It Detects
The code executes commands using `child_process.exec()` with concatenated strings.

#### Why It Is Dangerous
The underlying shell interprets operators like `|`, `;`, and `&`.

#### How an Attacker Uses It
An attacker appends shell commands to execute unauthorized host processes.

#### How to Fix
Use `child_process.execFile()` or `spawn()` with an array of arguments.

#### Vulnerable Example
```javascript
exec('git log ' + branch);
```

#### Remediated Fix
```javascript
execFile('git', ['log', branch]);
```

---

### APS-JS-INJ-003 — String Code Execution in Timer

- **Language:** Javascript
- **CWE:** CWE-95
- **Severity:** MEDIUM

#### What It Detects
The code passes a string rather than a callback function to `setTimeout` or `setInterval`.

#### Why It Is Dangerous
Timers evaluate string parameters similarly to `eval()`.

#### How an Attacker Uses It
An attacker manipulates the timer string to run injected code.

#### How to Fix
Always pass a callback function to timers.

#### Vulnerable Example
```javascript
setTimeout('doWork(' + id + ')', 1000);
```

#### Remediated Fix
```javascript
setTimeout(() => doWork(id), 1000);
```

---

### APS-JS-INJ-004 — Prototype Pollution Vulnerability

- **Language:** Javascript
- **CWE:** CWE-1321
- **Severity:** HIGH

#### What It Detects
Object assignment or recursive merge allows keys like `__proto__` or `constructor.prototype`.

#### Why It Is Dangerous
Polluting `Object.prototype` alters default properties across all objects in the runtime.

#### How an Attacker Uses It
An attacker injects properties like `isAdmin` or properties altering routing.

#### How to Fix
Validate keys to reject `__proto__`, or use `Object.create(null)`.

#### Vulnerable Example
```javascript
Object.assign(target, JSON.parse(userInput));
```

#### Remediated Fix
```javascript
// Filter keys: if (key === '__proto__' || key === 'constructor') continue;
```

---

### APS-JS-INJ-005 — SQL Injection in Node.js

- **Language:** Javascript
- **CWE:** CWE-89
- **Severity:** HIGH

#### What It Detects
The application builds database queries by concatenating input strings.

#### Why It Is Dangerous
Allows arbitrary SQL execution.

#### How an Attacker Uses It
An attacker extracts or modifies database records.

#### How to Fix
Use parameterized queries with placeholders (`$1`, `?`).

#### Vulnerable Example
```javascript
db.query(`SELECT * FROM users WHERE id = ${userId}`);
```

#### Remediated Fix
```javascript
db.query('SELECT * FROM users WHERE id = $1', [userId]);
```

---

### APS-JS-IO-001 — Path Traversal in Node.js fs

- **Language:** Javascript
- **CWE:** CWE-22
- **Severity:** HIGH

#### What It Detects
The application passes user input to `fs.readFile()` or `fs.writeFile()` without resolution checks.

#### Why It Is Dangerous
Directory traversal sequences allow accessing files outside the target directory.

#### How an Attacker Uses It
An attacker retrieves configuration files containing keys or sensitive database info.

#### How to Fix
Resolve paths with `path.resolve()` and verify prefix containment.

#### Vulnerable Example
```javascript
fs.readFile(baseDir + '/' + req.query.file);
```

#### Remediated Fix
```javascript
const safe = path.resolve(baseDir, req.query.file);
if (safe.startsWith(baseDir)) fs.readFile(safe);
```

---

### APS-JS-NET-001 — SSRF via fetch / axios

- **Language:** Javascript
- **CWE:** CWE-918
- **Severity:** HIGH

#### What It Detects
Node.js issues HTTP requests to user-provided URLs using `fetch` or `axios`.

#### Why It Is Dangerous
Enables requests to internal cloud metadata and private microservices.

#### How an Attacker Uses It
An attacker probes internal network endpoints and accesses cloud credentials.

#### How to Fix
Validate destination hostnames against an allowlist.

#### Vulnerable Example
```javascript
await axios.get(req.query.url);
```

#### Remediated Fix
```javascript
if (isAllowedUrl(req.query.url)) await axios.get(req.query.url);
```

---

### APS-JS-NET-002 — Overly Permissive CORS Policy

- **Language:** Javascript
- **CWE:** CWE-942
- **Severity:** MEDIUM

#### What It Detects
The server sets `Access-Control-Allow-Origin: *` while accepting credentials or sensitive endpoints.

#### Why It Is Dangerous
Any website can read authenticated responses from the user's browser.

#### How an Attacker Uses It
A malicious site makes cross-origin requests to read user account details.

#### How to Fix
Specify exact trusted origin domains instead of wildcards.

#### Vulnerable Example
```javascript
res.setHeader('Access-Control-Allow-Origin', '*');
```

#### Remediated Fix
```javascript
res.setHeader('Access-Control-Allow-Origin', 'https://trusted.app.com');
```

---

### APS-JS-NET-003 — TLS Certificate Validation Disabled (Node.js)

- **Language:** Javascript
- **CWE:** CWE-295
- **Severity:** CRITICAL

#### What It Detects
The application sets `rejectUnauthorized: false` or `NODE_TLS_REJECT_UNAUTHORIZED=0`.

#### Why It Is Dangerous
Disables SSL/TLS identity checks, allowing Man-in-the-Middle attacks.

#### How an Attacker Uses It
An attacker intercepts and alters sensitive traffic.

#### How to Fix
Maintain `rejectUnauthorized: true` with valid certificates.

#### Vulnerable Example
```javascript
const agent = new https.Agent({ rejectUnauthorized: false });
```

#### Remediated Fix
```javascript
const agent = new https.Agent({ rejectUnauthorized: true });
```

---

### APS-JS-OBF-001 — Obfuscated Code Execution in JavaScript

- **Language:** Javascript
- **CWE:** CWE-116
- **Severity:** HIGH

#### What It Detects
The code decodes strings using `atob()` or hex escape decoding and evaluates them dynamically.

#### Why It Is Dangerous
Hides payload logic from standard code inspection.

#### How an Attacker Uses It
An attacker delivers malware scripts disguised as encoded text.

#### How to Fix
Remove dynamic decoding and execution of obfuscated payloads.

#### Vulnerable Example
```javascript
eval(atob('YWxlcnQoMSk='));
```

#### Remediated Fix
```javascript
// Use explicit, unencoded JavaScript modules
```

---

### APS-JS-SEC-001 — Hardcoded API Key or Secret

- **Language:** Javascript
- **CWE:** CWE-798
- **Severity:** HIGH

#### What It Detects
The JavaScript source contains hardcoded secrets or API tokens.

#### Why It Is Dangerous
Frontend bundles and server repositories expose these secrets publicly.

#### How an Attacker Uses It
An attacker inspects bundle source maps or source repositories to steal credentials.

#### How to Fix
Load secrets from environment variables (`process.env`).

#### Vulnerable Example
```javascript
const token = 'ghp_secretTokenExample';
```

#### Remediated Fix
```javascript
const token = process.env.GITHUB_TOKEN;
```

---

### APS-JS-SEC-002 — Insecure Cookie Flags

- **Language:** Javascript
- **CWE:** CWE-614
- **Severity:** LOW

#### What It Detects
A cookie is set without `httpOnly` or `secure` flags.

#### Why It Is Dangerous
Cookies are accessible via client-side script and sent over unencrypted connections.

#### How an Attacker Uses It
An attacker uses XSS to read session cookies, or sniffs HTTP traffic.

#### How to Fix
Set `httpOnly: true`, `secure: true`, and `sameSite: 'strict'`.

#### Vulnerable Example
```javascript
res.cookie('session', sid);
```

#### Remediated Fix
```javascript
res.cookie('session', sid, { httpOnly: true, secure: true, sameSite: 'strict' });
```

---

### APS-JS-XSS-001 — DOM-Based XSS via innerHTML

- **Language:** Javascript
- **CWE:** CWE-79
- **Severity:** HIGH

#### What It Detects
User input is assigned directly to `element.innerHTML` or `document.write()`.

#### Why It Is Dangerous
The browser parses HTML tags and executes embedded scripts.

#### How an Attacker Uses It
An attacker injects `<img src=x onerror=alert(1)>` to steal session tokens.

#### How to Fix
Use `element.textContent` or sanitize with DOMPurify.

#### Vulnerable Example
```javascript
div.innerHTML = location.hash;
```

#### Remediated Fix
```javascript
div.textContent = location.hash;
```

---

### APS-JS-XSS-002 — React dangerouslySetInnerHTML Vulnerability

- **Language:** Javascript
- **CWE:** CWE-79
- **Severity:** HIGH

#### What It Detects
A React component renders raw markup using `dangerouslySetInnerHTML` with user input.

#### Why It Is Dangerous
Bypasses React's built-in XSS protection.

#### How an Attacker Uses It
An attacker injects scripts that execute when other users view the component.

#### How to Fix
Sanitize with `DOMPurify.sanitize()` before passing to `__html`.

#### Vulnerable Example
```javascript
<div dangerouslySetInnerHTML={{ __html: postContent }} />
```

#### Remediated Fix
```javascript
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(postContent) }} />
```

---

### APS-JV-CRY-001 — Weak Hash Algorithm in Java (MD5/SHA-1)

- **Language:** Java
- **CWE:** CWE-327
- **Severity:** MEDIUM

#### What It Detects
The code requests an MD5 or SHA-1 instance from `MessageDigest.getInstance()`.

#### Why It Is Dangerous
MD5 and SHA-1 lack cryptographic collision resistance.

#### How an Attacker Uses It
An attacker constructs colliding payloads sharing identical hash digests.

#### How to Fix
Use `MessageDigest.getInstance("SHA-256")` or SHA-512.

#### Vulnerable Example
```java
MessageDigest md = MessageDigest.getInstance("MD5");
```

#### Remediated Fix
```java
MessageDigest md = MessageDigest.getInstance("SHA-256");
```

---

### APS-JV-CRY-002 — Insecure Cipher / ECB Mode

- **Language:** Java
- **CWE:** CWE-327
- **Severity:** MEDIUM

#### What It Detects
The application requests DES or ECB cipher modes from `Cipher.getInstance()`.

#### Why It Is Dangerous
DES has a small key space and ECB leaks structural patterns across blocks.

#### How an Attacker Uses It
An attacker extracts patterns and breaks encryption keys.

#### How to Fix
Use `Cipher.getInstance("AES/GCM/NoPadding")`.

#### Vulnerable Example
```java
Cipher c = Cipher.getInstance("DES/ECB/PKCS5Padding");
```

#### Remediated Fix
```java
Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
```

---

### APS-JV-CRY-003 — Insecure Random Number Generator

- **Language:** Java
- **CWE:** CWE-330
- **Severity:** LOW

#### What It Detects
The code uses `java.util.Random` for cryptographic tokens, salts, or passwords.

#### Why It Is Dangerous
`java.util.Random` uses a 48-bit linear congruential generator whose internal state can be deduced from a few consecutive values.

#### How an Attacker Uses It
An attacker predicts future tokens or session IDs.

#### How to Fix
Use `java.security.SecureRandom` for security-sensitive values.

#### Vulnerable Example
```java
Random r = new Random();
```

#### Remediated Fix
```java
SecureRandom sr = new SecureRandom();
```

---

### APS-JV-DES-001 — Untrusted Java Deserialization

- **Language:** Java
- **CWE:** CWE-502
- **Severity:** CRITICAL

#### What It Detects
The code deserializes untrusted streams with `ObjectInputStream.readObject()`.

#### Why It Is Dangerous
Java deserialization executes gadget chains (e.g. Apache Commons Collections) during deserialization.

#### How an Attacker Uses It
An attacker uses tools like ysoserial to craft gadget payloads that trigger remote code execution upon deserialization.

#### How to Fix
Use safe data formats like JSON/Protobuf, or enforce an `ObjectInputFilter` whitelist.

#### Vulnerable Example
```java
Object obj = new ObjectInputStream(in).readObject();
```

#### Remediated Fix
```java
// Use JSON/Jackson with safe typing or ObjectInputFilter
```

---

### APS-JV-INJ-001 — Command Injection via Runtime.exec

- **Language:** Java
- **CWE:** CWE-78
- **Severity:** CRITICAL

#### What It Detects
The application passes a dynamic command string to `Runtime.getRuntime().exec()`.

#### Why It Is Dangerous
Dynamic arguments concatenated into command strings are subject to shell interpretation and subshell injection.

#### How an Attacker Uses It
An attacker appends shell metacharacters to run arbitrary host binaries with the servlet container's UID.

#### How to Fix
Pass commands and arguments as discrete `String[]` array elements without shell invocation.

#### Vulnerable Example
```java
Runtime.getRuntime().exec("cmd.exe /c " + input);
```

#### Remediated Fix
```java
new ProcessBuilder("safe_tool", input).start();
```

---

### APS-JV-INJ-002 — Command Injection via ProcessBuilder

- **Language:** Java
- **CWE:** CWE-78
- **Severity:** CRITICAL

#### What It Detects
The application initializes a `ProcessBuilder` with command strings containing user-controllable input.

#### Why It Is Dangerous
If a shell (`sh -c` or `cmd.exe /c`) is wrapped around dynamic arguments, command injection occurs.

#### How an Attacker Uses It
An attacker injects secondary commands using shell delimiters.

#### How to Fix
Execute binaries directly using separate argument tokens without wrapping in a shell.

#### Vulnerable Example
```java
new ProcessBuilder("sh", "-c", "ping " + host).start();
```

#### Remediated Fix
```java
new ProcessBuilder("ping", host).start();
```

---

### APS-JV-INJ-003 — SQL Injection via JDBC Statement

- **Language:** Java
- **CWE:** CWE-89
- **Severity:** HIGH

#### What It Detects
The code concatenates variables directly into a SQL query executed via `Statement.executeQuery()`.

#### Why It Is Dangerous
The database engine treats the concatenated values as SQL syntax rather than literal data.

#### How an Attacker Uses It
An attacker injects quotation marks and SQL clauses (`' OR '1'='1`) to dump databases.

#### How to Fix
Use parameterized `PreparedStatement` with `?` place-holders.

#### Vulnerable Example
```java
stmt.executeQuery("SELECT * FROM users WHERE name = '" + name + "'");
```

#### Remediated Fix
```java
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE name = ?");
ps.setString(1, name);
```

---

### APS-JV-INJ-004 — HQL / JPQL Injection

- **Language:** Java
- **CWE:** CWE-89
- **Severity:** HIGH

#### What It Detects
The application builds JPA or Hibernate queries by concatenating user inputs into JPQL/HQL queries.

#### Why It Is Dangerous
HQL/JPQL supports query injection, object traversal, and arbitrary data extraction.

#### How an Attacker Uses It
An attacker alters query conditions to bypass authorization checks.

#### How to Fix
Use named query parameters (e.g., `query.setParameter("name", name)`).

#### Vulnerable Example
```java
em.createQuery("FROM User WHERE name = '" + name + "'");
```

#### Remediated Fix
```java
em.createQuery("FROM User WHERE name = :name").setParameter("name", name);
```

---

### APS-JV-IO-001 — Path Traversal in Java File Access

- **Language:** Java
- **CWE:** CWE-22
- **Severity:** HIGH

#### What It Detects
The application constructs a `File` or `Path` from user input without canonical directory verification.

#### Why It Is Dangerous
Traversal sequences allow reading or overwriting files outside the target directory.

#### How an Attacker Uses It
An attacker writes `../../conf/server.xml` to tamper with server configuration.

#### How to Fix
Call `path.normalize().toRealPath()` and verify it starts with the base directory.

#### Vulnerable Example
```java
new File(baseDir, filename);
```

#### Remediated Fix
```java
Path p = baseDir.resolve(filename).normalize();
if (!p.startsWith(baseDir)) throw new SecurityException();
```

---

### APS-JV-NET-001 — Java SSRF via URL Connection

- **Language:** Java
- **CWE:** CWE-918
- **Severity:** HIGH

#### What It Detects
The code opens an `HttpURLConnection` to a URL specified by user input.

#### Why It Is Dangerous
The server can be forced to query internal services and cloud metadata endpoints.

#### How an Attacker Uses It
An attacker targets internal administrative panels or metadata APIs.

#### How to Fix
Validate URLs against an allowlist and reject loopback/RFC1918 private IPs.

#### Vulnerable Example
```java
new URL(inputUrl).openConnection();
```

#### Remediated Fix
```java
if (isAllowed(inputUrl)) { new URL(inputUrl).openConnection(); }
```

---

### APS-JV-NET-002 — TLS Certificate Validation Disabled

- **Language:** Java
- **CWE:** CWE-295
- **Severity:** CRITICAL

#### What It Detects
The code installs a trust manager that ignores SSL/TLS certificate errors (`TrustAllCerts`).

#### Why It Is Dangerous
All HTTPS connections become vulnerable to Man-in-the-Middle (MITM) interception.

#### How an Attacker Uses It
An attacker intercepts and decrypts sensitive network communications.

#### How to Fix
Use the default system trust store or configure a specific trusted certificate authority.

#### Vulnerable Example
```java
sc.init(null, new TrustManager[]{new TrustAllCerts()}, null);
```

#### Remediated Fix
```java
// Use standard SSLContext with default trusted certificates
```

---

### APS-JV-SEC-001 — Hardcoded Password or Key in Java

- **Language:** Java
- **CWE:** CWE-798
- **Severity:** HIGH

#### What It Detects
The Java source defines hardcoded password or private key literals.

#### Why It Is Dangerous
Secrets in compiled `.class` and `.jar` files are easily extracted with decompilers.

#### How an Attacker Uses It
An attacker decompiles the binary to recover hardcoded keys.

#### How to Fix
Store secrets in environment variables or cloud key vaults.

#### Vulnerable Example
```java
String apiKey = "AIzaSyD-sample-key";
```

#### Remediated Fix
```java
String apiKey = System.getenv("API_KEY");
```

---

### APS-JV-UNI-001 — Confusable or Homoglyph Identifier in Java

- **Language:** Java
- **CWE:** CWE-1007
- **Severity:** HIGH

#### What It Detects
An identifier contains non-ASCII lookalike characters mimicking ASCII keywords or APIs.

#### Why It Is Dangerous
Developers mistake the identifier for standard APIs, masking malicious functionality.

#### How an Attacker Uses It
An attacker creates a lookalike function that appears harmless during code review.

#### How to Fix
Normalize identifiers to ASCII or restrict source files to ASCII identifiers.

#### Vulnerable Example
```java
void еxec() { ... } // Cyrillic е mimics 'exec'
```

#### Remediated Fix
```java
void exec() { ... }
```

---

### APS-JV-XML-001 — XML External Entity (XXE) Injection

- **Language:** Java
- **CWE:** CWE-611
- **Severity:** HIGH

#### What It Detects
The application parses XML with a `DocumentBuilderFactory` without disabling external entity resolution.

#### Why It Is Dangerous
The XML parser resolves external entity references, allowing reading local files or port scanning.

#### How an Attacker Uses It
An attacker submits `<!ENTITY xxe SYSTEM "file:///etc/passwd">` to read system files.

#### How to Fix
Set `factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)`.

#### Vulnerable Example
```java
DocumentBuilder db = factory.newDocumentBuilder();
```

#### Remediated Fix
```java
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
```

---

### APS-JV-XSS-001 — Reflected XSS in Servlet Response

- **Language:** Java
- **CWE:** CWE-79
- **Severity:** HIGH

#### What It Detects
The servlet writes user request parameters directly to `PrintWriter.println()` without escaping.

#### Why It Is Dangerous
The browser interprets user input as active HTML/JavaScript in the victim's session.

#### How an Attacker Uses It
An attacker crafts links with script payloads to compromise user accounts.

#### How to Fix
Encode user data using OWASP Java Encoder (`Encode.forHtml(input)`).

#### Vulnerable Example
```java
response.getWriter().println("<h1>" + user + "</h1>");
```

#### Remediated Fix
```java
response.getWriter().println("<h1>" + Encode.forHtml(user) + "</h1>");
```

---

### APS-PY-CRY-001 — Broken Hash Algorithm (MD5/SHA1)

- **Language:** Python
- **CWE:** CWE-327
- **Severity:** MEDIUM

#### What It Detects
The code uses MD5 or SHA1 cryptographic hash functions for security or integrity checks.

#### Why It Is Dangerous
MD5 and SHA1 suffer from proven practical collision attacks, permitting attackers to generate identical hashes for malicious files.

#### How an Attacker Uses It
An attacker creates a collision payload with a valid hash signature to bypass integrity verification.

#### How to Fix
Upgrade to modern collision-resistant cryptographic hashes such as SHA-256 (`hashlib.sha256()`) or SHA-3.

#### Vulnerable Example
```python
h = hashlib.md5(data).hexdigest()
```

#### Remediated Fix
```python
h = hashlib.sha256(data).hexdigest()
```

---

### APS-PY-CRY-002 — Weak Cipher Algorithm (DES/ECB)

- **Language:** Python
- **CWE:** CWE-327
- **Severity:** MEDIUM

#### What It Detects
The code initializes encryption using legacy DES or Electronic Codebook (ECB) cipher mode.

#### Why It Is Dangerous
DES uses an inadequate 56-bit key susceptible to brute force, while ECB mode preserves plaintext patterns across blocks.

#### How an Attacker Uses It
An attacker reconstructs data patterns or rapidly cracks DES keys using inexpensive cloud computing.

#### How to Fix
Use AES in GCM authenticated encryption mode (AES-GCM-256) with unique initialization vectors.

#### Vulnerable Example
```python
cipher = DES.new(key, DES.MODE_ECB)
```

#### Remediated Fix
```python
cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
```

---

### APS-PY-DES-001 — Untrusted Deserialization via pickle

- **Language:** Python
- **CWE:** CWE-502
- **Severity:** CRITICAL

#### What It Detects
The code unpickles untrusted binary data using `pickle.loads()` or `pickle.load()`.

#### Why It Is Dangerous
Python's pickle protocol supports arbitrary object instantiation via the `__reduce__` method, triggering code on load.

#### How an Attacker Uses It
An attacker crafts a serialized byte stream with a malicious `__reduce__` tuple that executes OS commands upon unpickling.

#### How to Fix
Never unpickle untrusted data. Use safe serialization formats such as JSON, Protocol Buffers, or CBOR.

#### Vulnerable Example
```python
data = pickle.loads(untrusted_bytes)
```

#### Remediated Fix
```python
import json

data = json.loads(untrusted_json)
```

---

### APS-PY-DES-002 — Insecure YAML Deserialization

- **Language:** Python
- **CWE:** CWE-502
- **Severity:** CRITICAL

#### What It Detects
The code deserializes YAML documents using `yaml.load()` without an explicit safe loader.

#### Why It Is Dangerous
Standard `yaml.load()` resolves custom tags like `!!python/object/apply` which execute arbitrary Python callables.

#### How an Attacker Uses It
An attacker submits a YAML payload containing `!!python/object/apply:os.system ['touch /tmp/pwn']` to execute code.

#### How to Fix
Always use `yaml.safe_load()` or specify `Loader=yaml.SafeLoader`.

#### Vulnerable Example
```python
obj = yaml.load(raw_yaml)
```

#### Remediated Fix
```python
obj = yaml.safe_load(raw_yaml)
```

---

### APS-PY-INJ-001 — Arbitrary Code Execution via eval/exec

- **Language:** Python
- **CWE:** CWE-95
- **Severity:** CRITICAL

#### What It Detects
The code passes dynamic or untrusted input directly to Python's `eval()` or `exec()` runtime evaluators.

#### Why It Is Dangerous
Python's `eval()` and `exec()` execute arbitrary Python bytecode in the current process context with full user permissions.

#### How an Attacker Uses It
An attacker injects payload strings like `__import__('os').system('rm -rf /')` to achieve unauthenticated remote code execution.

#### How to Fix
Replace `eval()` with `ast.literal_eval()` for safe constant parsing, or use structured parsers like `json.loads()`.

#### Vulnerable Example
```python
result = eval(user_input)
```

#### Remediated Fix
```python
import ast

result = ast.literal_eval(user_input)
```

---

### APS-PY-INJ-002 — Command Injection via os.system

- **Language:** Python
- **CWE:** CWE-78
- **Severity:** CRITICAL

#### What It Detects
The code invokes the host operating system shell via `os.system()` with concatenated or dynamic command arguments.

#### Why It Is Dangerous
The system shell interprets shell metacharacters (;, &, |, `, $) allowing attackers to append secondary malicious commands.

#### How an Attacker Uses It
An attacker submits shell chaining characters (e.g., `payload; cat /etc/passwd`) to escape the intended utility and run host commands.

#### How to Fix
Use `subprocess.run()` with argument lists and `shell=False`, or sanitize inputs using `shlex.quote()`.

#### Vulnerable Example
```python
os.system("ping " + ip)
```

#### Remediated Fix
```python
import subprocess

subprocess.run(["ping", "-c", "1", ip], check=True)
```

---

### APS-PY-INJ-003 — Subprocess Shell Injection

- **Language:** Python
- **CWE:** CWE-78
- **Severity:** CRITICAL

#### What It Detects
The code executes a subprocess call with `shell=True` using a string containing dynamic or concatenated variables.

#### Why It Is Dangerous
Enabling `shell=True` invokes `/bin/sh` or `cmd.exe` to interpret the command string, exposing it to shell metacharacter manipulation.

#### How an Attacker Uses It
An attacker injects pipes or semicolons (`|`, `;`, `&&`) into arguments to hijack command execution flow.

#### How to Fix
Pass arguments as a list and set `shell=False` (the safe default in subprocess functions).

#### Vulnerable Example
```python
subprocess.Popen(f"ls {directory}", shell=True)
```

#### Remediated Fix
```python
subprocess.Popen(["ls", directory], shell=False)
```

---

### APS-PY-INJ-004 — SQL Injection via Query Formatting

- **Language:** Python
- **CWE:** CWE-89
- **Severity:** HIGH

#### What It Detects
The code constructs a SQL query string using string concatenation, `%` formatting, `.format()`, or f-strings.

#### Why It Is Dangerous
String-interpolated parameters break out of the SQL syntax context, allowing arbitrary database querying or data modification.

#### How an Attacker Uses It
An attacker inputs quotes (`' OR '1'='1`) to bypass authentication or extract sensitive tables using `UNION SELECT`.

#### How to Fix
Use parameterized queries with DB-API placeholders (e.g. `cursor.execute(sql, (param,))`).

#### Vulnerable Example
```python
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

#### Remediated Fix
```python
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

---

### APS-PY-INJ-005 — Server-Side Template Injection

- **Language:** Python
- **CWE:** CWE-94
- **Severity:** HIGH

#### What It Detects
The application evaluates untrusted input directly inside a template engine string.

#### Why It Is Dangerous
Template engines provide expressions that can navigate object models to access built-ins and call system commands.

#### How an Attacker Uses It
An attacker inputs `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}` to execute code.

#### How to Fix
Pass data exclusively as template context variables instead of concatenating input into template strings.

#### Vulnerable Example
```python
jinja2.Template("Hello " + name).render()
```

#### Remediated Fix
```python
jinja2.Template("Hello {{ name }}").render(name=name)
```

---

### APS-PY-IO-001 — Path Traversal via File Access

- **Language:** Python
- **CWE:** CWE-22
- **Severity:** HIGH

#### What It Detects
The code passes a dynamic path into file open operations without canonical path validation.

#### Why It Is Dangerous
Directory traversal sequences (`../`) break out of the intended folder, permitting read/write across the entire filesystem.

#### How an Attacker Uses It
An attacker requests `../../../../etc/passwd` to read sensitive configuration and user accounts.

#### How to Fix
Resolve paths with `Path.resolve()` and verify that the target starts with the intended base directory.

#### Vulnerable Example
```python
open(base_path + "/" + filename, "r")
```

#### Remediated Fix
```python
safe = (base / filename).resolve()
if base in safe.parents:
    open(safe, "r")
```

---

### APS-PY-NET-001 — Server-Side Request Forgery (SSRF)

- **Language:** Python
- **CWE:** CWE-918
- **Severity:** HIGH

#### What It Detects
The application performs HTTP client requests to a URL derived from user-controlled parameters.

#### Why It Is Dangerous
The server can be coerced into issuing requests to internal loopback addresses or cloud metadata endpoints.

#### How an Attacker Uses It
An attacker submits `http://169.254.169.254/latest/meta-data/` to steal IAM roles and cloud instance credentials.

#### How to Fix
Validate URLs against strict hostname allowlists, block private/loopback IP ranges, and disable HTTP redirects.

#### Vulnerable Example
```python
requests.get(target_url)
```

#### Remediated Fix
```python
if is_allowed_domain(target_url):
    requests.get(target_url)
```

---

### APS-PY-OBF-001 — Obfuscated Payload Execution

- **Language:** Python
- **CWE:** CWE-116
- **Severity:** HIGH

#### What It Detects
The code decodes a base64 or hex-encoded payload and immediately evaluates or executes it.

#### Why It Is Dangerous
Encoding masks malicious shellcodes or droppers from static signature scanners.

#### How an Attacker Uses It
An attacker disguises malware droppers as benign encoded configuration strings.

#### How to Fix
Avoid dynamic decoding and execution of encoded strings; use explicit static modules.

#### Vulnerable Example
```python
exec(base64.b64decode(payload))
```

#### Remediated Fix
```python
# Review and write explicit, transparent logic
```

---

### APS-PY-SEC-001 — Hardcoded Credential or Secret

- **Language:** Python
- **CWE:** CWE-798
- **Severity:** HIGH

#### What It Detects
The source code contains a high-entropy string or API token assigned directly to a credential variable.

#### Why It Is Dangerous
Hardcoded secrets in source files are committed to version control and distributed in deployed code repositories.

#### How an Attacker Uses It
An attacker scans public git histories or decompiles packaged binaries to extract API keys and access cloud infrastructure.

#### How to Fix
Load credentials at runtime from environment variables (`os.environ`) or a secrets manager.

#### Vulnerable Example
```python
API_KEY = "AKIAIOSFODNN7EXAMPLE"
```

#### Remediated Fix
```python
API_KEY = os.environ["API_KEY"]
```

---

### APS-PY-XSS-001 — Cross-Site Scripting via Dynamic HTML

- **Language:** Python
- **CWE:** CWE-79
- **Severity:** HIGH

#### What It Detects
The application renders unescaped user input directly into an HTML response.

#### Why It Is Dangerous
The browser executes injected `<script>` tags in the origin context of the user.

#### How an Attacker Uses It
An attacker steals session cookies and authorization tokens, or performs actions on the victim's behalf.

#### How to Fix
Use automatic HTML escaping (e.g. Jinja2 templates) or sanitize with an HTML entity sanitizer.

#### Vulnerable Example
```python
return render_template_string("<h1>" + user + "</h1>")
```

#### Remediated Fix
```python
return render_template("profile.html", user=user)
```

---
