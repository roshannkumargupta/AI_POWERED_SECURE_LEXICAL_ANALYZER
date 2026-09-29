# Phase 2 Explained — Hand-Written Python Lexer, Security Rule Engine & AST Data-Flow Taint Analysis

---

## 1. Plain-Language Explanation: What Did We Build and Why?

In **Phase 2**, we replaced the prototype tokenizer with a production-grade, hand-written lexical analyzer for Python, implemented a deterministic security rule engine with 14 specialized rules, and built a flow-sensitive AST data-flow taint analyzer that resolves the architectural flaws found in the legacy baseline.

---

### A. Hand-Written Lexer State Machine vs. "One Big Regex" (`src/apsla/languages/python_lang/lexer.py`)

A common shortcut in introductory compiler projects is using a single giant regular expression (e.g., `re.Scanner` or regex alternation `(?P<ID>[a-zA-Z_]\w*)|(?P<NUM>\d+)|...`). While tempting, this approach suffers from fatal deficiencies:
1. **Catastrophic Backtracking & ReDoS:** Complex nested patterns (like f-strings or multiline comments) can exhibit exponential runtime on pathological or malformed inputs.
2. **Context-Sensitive Syntax:** Python's lexical grammar is context-sensitive. An indent or dedent can only be emitted at the beginning of a physical line, and indentation must be tracked using a stateful integer stack. Furthermore, newlines inside unclosed parentheses, brackets, or braces `( [ {` are ignored, requiring an active delimiter-nesting counter (`paren_depth`).
3. **Lossless Trivia Preservation:** Standard tokenizers discard whitespace, indentation, comments, and line continuations (`\`). In SecureLex IDE, the invariant `"".join(token.text for token in tokens) == source` is strictly guaranteed. This allows the editor to render exact character overlays, provide syntax highlighting, and perform verifiable, automated atomic code fixes without losing user formatting.
4. **Resilience (Zero Crash Guarantee):** The lexer never raises exceptions. If unexpected characters or unclosed strings are encountered, the state machine captures them as `ERROR` tokens, records their position, advances the cursor, and continues tokenizing the remaining file.

#### F-String Token Architecture
F-strings in Python 3.12 can contain nested quotes, format specifiers, and arbitrary expressions (`f"{user.name.upper()}"`). Rather than splitting an f-string into disjointed chunks that confuse downstream token classifiers, our lexer parses the f-string into a single unified `STRING` token, while attaching a tuple of exact character `parts: tuple[Range, ...]` corresponding to the embedded expressions. This provides both high-level semantic encapsulation for the token stream and fine-grained coordinate precision for taint analysis.

---

### B. Deterministic Security Rule Engine (`src/apsla/rules/base.py` & `src/apsla/languages/python_lang/rules.py`)

Rather than relying solely on black-box machine learning models, SecureLex IDE uses deterministic static rules that inspect both the lexical token stream and the Python Abstract Syntax Tree (AST):
- **Recovered Text Execution:** Rules evaluate the *adversarially recovered* AST (produced by Phase 1's Unicode normalization). When an attacker writes Cyrillic `ехес("payload")`, the AST rule catches it as a high-severity `APS-PY-INJ-001` (CWE-95) code injection finding, alongside the Unicode homoglyph alerts (`APS-ALL-UNI-004` and `APS-ALL-UNI-006`).
- **Comprehensive Rule Coverage:**
  1. `APS-PY-INJ-001`: Dynamic `eval()` / `exec()` with non-constant expressions (CWE-95).
  2. `APS-PY-INJ-002`: `os.system()` / `os.popen()` with dynamic or concatenated commands (CWE-78).
  3. `APS-PY-INJ-003`: `subprocess` calls with `shell=True` and dynamic arguments (CWE-78). Note: list-form `subprocess.run(["ls", "-l"])` without `shell=True` is verified safe and never flagged.
  4. `APS-PY-INJ-004`: SQL queries constructed via string concatenation, `%`-formatting, or f-strings passed to `.execute()` (CWE-89).
  5. `APS-PY-DES-001`: Insecure deserialization via `pickle.load(s)`, `marshal`, or `shelve` (CWE-502).
  6. `APS-PY-DES-002`: `yaml.load()` without specifying `SafeLoader` (CWE-502).
  7. `APS-PY-CRY-001`: Broken cryptographic hashes `hashlib.md5()` / `hashlib.sha1()` (CWE-327).
  8. `APS-PY-CRY-002`: Insecure pseudorandom generator (`random` module) used for secrets or tokens (CWE-338).
  9. `APS-PY-SEC-001`: Hard-coded credentials, API keys, or JWT tokens detected via entropy and naming heuristics (CWE-798).
  10. `APS-PY-NET-001`: Disabling SSL verification via `requests.get(..., verify=False)` (CWE-295).
  11. `APS-PY-IO-001`: Arbitrary file read / path traversal via `open()` or `send_file()` on untrusted paths (CWE-22).
  12. `APS-PY-INJ-005`: Dynamic module loading via `__import__()` or `importlib.import_module()` on dynamic variables (CWE-94).
  13. `APS-PY-OBF-001`: Obfuscated execution of base64-, zlib-, or hex-decoded strings inside `exec()` / `eval()` (CWE-506).
  14. `APS-PY-XSS-001`: Cross-site scripting (XSS) via `render_template_string()` or `Markup()` containing unescaped variables (CWE-79).

---

### C. AST-Based Data-Flow Taint Analysis (`src/apsla/languages/python_lang/taint.py`)

#### Why the Senior's Token-Window Approach Failed
The legacy project attempted taint tracking by scanning a linear window of tokens: if a dangerous function (like `os.system`) appeared within 4 tokens of an identifier, it guessed that taint occurred. This led to disastrous failure modes:
- **Attribute Access Blindness:** When examining `request.args.get("q")`, the tokenizer split the expression into `request`, `.`, `args`, `.`, `get`. The senior's window matcher failed to recognize that `request.args` was an untrusted HTTP source.
- **Distance Blindness:** If user input was assigned on line 1 (`u = input()`) and passed to `os.system(u)` on line 5, the distance exceeded 4 tokens and the vulnerability was completely missed.
- **False Positives on Sanitized Code:** If `shlex.quote(u)` was used, the senior's model still flagged `os.system` because it could not understand semantic sanitization.

#### How SecureLex IDE Performs Real AST Taint Tracking
SecureLex IDE parses Python into a structured Abstract Syntax Tree (`ast`) and performs true data-flow analysis:
1. **Sources:** Recognizes untrusted entry points including `input()`, `sys.argv`, `os.environ` / `os.getenv`, `sys.stdin.read()`, network socket `.recv()`, Flask `request.args`, `request.form`, `request.json`, `request.headers`, Django `request.GET`/`POST`, and route parameters in FastAPI (`@app.get`).
2. **Propagation:** Tracks variable assignments (`v = u`), augmented assignments (`cmd += arg`), tuple unpacking (`a, b = ('clean', u)`), string concatenation (`"echo " + name`), `%`-formatting, `.format()`, f-strings (`f"echo {name}"`), and dictionary / list containers.
3. **Flow Sensitivity:** Reassigning a variable to a clean constant (`x = input(); x = "safe"`) purges taint immediately.
4. **Control Flow:**
   - **Branching:** Merges environments from `if` and `else` branches using set union.
   - **Loops:** Iterates `while` and `for` loop bodies up to 3 rounds to compute a fixed point of tainted variables.
5. **Intra-File Function Summaries:** Pre-analyzes helper functions to determine which arguments flow to their return values. If `def wrapper(arg): return arg + "!"` is called on a tainted variable, the return value is tracked as tainted.
6. **Sanitizers:** Recognizes category-specific sanitizers:
   - `shlex.quote()` clears command injection taint.
   - `int()` and `float()` type casts clear all injection taint.
   - `html.escape()` and `markupsafe.escape()` clear XSS taint.
   - `os.path.basename()` and `secure_filename()` clear path traversal taint.
   - Parameterized SQL queries (`cursor.execute(sql, (param,))`) clear SQL injection taint.
7. **Taint Paths:** When tainted data reaches an execution sink, SecureLex IDE constructs a verified `TaintPathStep` trace:
   `SOURCE (where input enters) -> PROPAGATE (intermediate assignments / concatenations) -> SINK (execution call)`
   This trace is displayed directly in the CLI and Monaco Editor.

---

## 2. Concept Glossary

- **Lexer State Machine:** An algorithmic scanner that moves sequentially through text character-by-character, transitioning between explicit states (e.g., `START`, `IDENTIFIER`, `NUMBER`, `STRING_SINGLE`, `STRING_TRIPLE`, `COMMENT`) rather than attempting to match entire multi-line constructs with global regular expressions.
- **Trivia Tokens:** Non-semantic tokens (such as spaces, tabs, line breaks, and comments) that are preserved in the token stream so that the original document can be reconstructed without loss.
- **Delimiter Nesting Counter:** An integer tracking open parentheses `(`, square brackets `[`, and curly braces `{`. In Python, newlines inside open delimiters are soft line continuations rather than logical line breaks.
- **Taint Analysis:** A form of information-flow analysis that tracks the propagation of untrusted external data (taint) through program variables to determine if it can reach sensitive execution points without validation.
- **Taint Source:** An expression where untrusted external data enters the application (e.g., HTTP request parameters, environment variables, command-line arguments, file reads).
- **Taint Sink:** A critical function or method whose execution depends on data safety (e.g., `os.system`, `eval`, `cursor.execute`, `open`).
- **Taint Sanitizer:** A function or operation that neutralizes malicious payloads for a specific vulnerability class (e.g., `shlex.quote` for shell commands, `html.escape` for HTML rendering).
- **Flow Sensitivity:** Analysis that respects the order of program statements. In a flow-sensitive analysis, a variable is considered tainted only at program points *after* it receives tainted data and *before* it is overwritten by clean data.
- **Fixed-Point Iteration:** An algorithmic technique for analyzing loops: the analyzer executes the loop body repeatedly until the set of tainted variables stops changing (stabilizes), guaranteeing termination within a bounded number of iterations.
- **Intra-File Function Summary:** A computed mapping describing how a function's parameters propagate to its return value, allowing callers to determine return-value taint without inlining the entire function body.

---

## 3. Five Viva Questions with Model Answers

### Question 1: Why is a hand-written state-machine lexer superior to a single giant regular expression for Python?
**Model Answer:**  
"A hand-written state-machine lexer is superior for three reasons:
1. **Context-Sensitive Indentation:** Python requires emitting `NEWLINE`, `INDENT`, and `DEDENT` tokens based on an indentation stack and delimiter nesting depth (`()`, `[]`, `{}`). Pure regular expressions cannot track stateful delimiter depth or compare whitespace indentation widths against a dynamic stack.
2. **ReDoS Elimination:** Complex nested constructs (such as Python 3.12 f-strings with nested quotes and format specifiers) can cause regular expressions to suffer exponential catastrophic backtracking on malformed input. A deterministic cursor-based state machine runs in guaranteed $O(N)$ linear time.
3. **Zero-Crash Resilience and Trivia Preservation:** A state machine can capture syntax errors as localized `ERROR` tokens without crashing or aborting the scan. Furthermore, it easily retains whitespace and comment tokens so that `"".join(t.text for t in tokens)` matches the input string byte-for-byte, enabling lossless IDE overlays and automated code fixes."

---

### Question 2: What is taint analysis, and what are its three fundamental components (source, sink, sanitizer)?
**Model Answer:**  
"Taint analysis is a static data-flow analysis technique that verifies whether untrusted data can influence sensitive program operations. Its three components are:
1. **Source:** The point of entry for external, untrusted input. Examples include `request.args.get()`, `sys.argv`, and `input()`.
2. **Sink:** A security-critical API whose misuse leads to a vulnerability. Examples include `os.system()` (command injection), `cursor.execute()` (SQL injection), and `eval()` (code execution).
3. **Sanitizer:** A transformation function that renders tainted input safe for a specific sink. For example, `shlex.quote()` escapes shell metacharacters, transforming command injection taint into safe string literals. If data reaches a sink through an effective sanitizer, the analyzer marks the flow as sanitized and suppresses false-positive vulnerability alerts."

---

### Question 3: Why did the senior student's token-window approach fail on real security vulnerabilities?
**Model Answer:**  
"The senior's approach relied on checking whether a dangerous token appeared within a narrow window of 4 tokens from another keyword. This failed because:
1. **Syntax Splitting:** High-level APIs like `request.args.get("param")` were tokenized into five separate tokens (`request`, `.`, `args`, `.`, `get`). The token window failed to recognize this multi-part chain as an untrusted HTTP source.
2. **Distance Blindness:** In idiomatic code, input is captured in one statement and used several lines later (e.g., `u = input()` followed 10 lines later by `os.system(u)`). Because the physical distance exceeded the token window, the taint connection was lost.
3. **False Positives on Safe Code:** The senior's token window had no awareness of syntax structure: a safe list-form call like `subprocess.run(["ls", "-l"])` was flagged as malicious simply because the word `subprocess` appeared.
By contrast, AST-based data-flow analysis follows variable definitions and uses along the Abstract Syntax Tree, ignoring token distance and accurately modeling variable flow, container indexing, and argument passing."

---

### Question 4: How does SecureLex IDE handle loop fixed-point iteration and branching in AST taint analysis?
**Model Answer:**  
"In conditional statements (`if` / `else`), SecureLex IDE clones the current variable environment and evaluates both the `if` body and the `else` body independently. It then computes the set union of tainted variables across both branches. If a variable is tainted along *either* path, it remains tainted downstream (conservative over-approximation).  
For loops (`for` and `while`), statements can re-taint variables across multiple iterations (e.g., `x = x + input()`). SecureLex IDE evaluates the loop body repeatedly, tracking the set of tainted variables. As soon as the set of tainted variables does not change between consecutive passes (a mathematical fixed point), iteration terminates. To prevent infinite analysis on pathological code, the analyzer bounds loop evaluation to a maximum of 3 iterations."

---

### Question 5: Why must security rules execute on the adversarial recovered text rather than only on the raw input, and how does this catch the `ехес` attack?
**Model Answer:**  
"Attackers use Unicode homoglyphs (such as Cyrillic small 'е' `U+0435` or fullwidth 'ｅ' `U+FF45`) to visually mimic ASCII identifiers like `exec` or `eval`. If an AST parser or keyword matcher inspects only the raw input, Python treats `\u0435\u0445\u0435\u0441` as a distinct identifier from built-in `exec`. Consequently, standard security tools fail to recognize that a dynamic code execution sink is being invoked.  
SecureLex IDE solves this in two coordinated steps:
1. **Adversarial Text Recovery:** The Unicode defense layer translates confusable glyphs to canonical ASCII while logging `APS-ALL-UNI-004` and `APS-ALL-UNI-006` homoglyph findings.
2. **Dual-Finding AST Inspection:** The security rule engine parses the *recovered* text into an AST, where the function call is correctly recognized as the built-in `exec()`. The rule engine flags `APS-PY-INJ-001` (CWE-95) with `HIGH` severity. The `OffsetMap` maps the recovered AST node range back to the exact byte and column positions in the original file, ensuring that the finding points directly to the attacker's obfuscated token."
