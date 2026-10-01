# Phase 8 Explained: JavaScript Language Plugin, Context-Sensitive Lexing, DOM XSS & Prototype Pollution Defense

---

## 1. Executive Summary & Plain-English Overview

Phase 8 expands SecureLex IDE (`apsla`) into the JavaScript and Node.js ecosystem, implementing a full language plugin that covers plain client-side ECMAScript, modern browser code, and backend Node.js applications.

JavaScript presents unique lexical and data-flow analysis challenges unlike Python or Java:
1. **Context-Sensitive Lexical Ambiguities:** The forward slash character (`/`) is ambiguous in JavaScript grammar. It can denote a division operator (`a / b`), a compound assignment operator (`a /= b`), a single-line comment (`//`), a block comment (`/* */`), a JSX self-closing tag (`<div />`), or the delimiter of a regular expression literal (`/^[a-z]+$/i`). This ambiguity cannot be resolved by standard context-free Chomsky Type-3 regular grammars without tracking preceding token context.
2. **Arbitrarily Nested Template Literals:** ECMAScript 2015 introduced template literals (`` `Hello, ${name}!` ``) with expression interpolation. Because template expressions can contain full JavaScript expressions—including nested template literals—the lexer must support arbitrary recursion using a modal stack.
3. **Complex Client-Side & Server-Side Sink Ecosystem:** Web applications face distinct attack surfaces across the browser (DOM-based Cross-Site Scripting via `innerHTML`, `outerHTML`, `location.href`, and `document.write`) and the server (Remote Code Execution via `child_process.exec`, Prototype Pollution via recursive object mergers, and Path Traversal via `fs.readFile`).

### Primary Objectives Delivered in Phase 8:
- **Resilient Lexer State Machine (`lexer.py`):** Hand-written, zero-crash, lossless state machine supporting ES2024 contextual keywords, BigInt (`10n`), numeric separators (`1_000`), template literal modal recursion, regex vs division disambiguation, private fields (`#field`), and JSX tolerance without error tokens.
- **Unified Taint Profile (`profile.py`):** Express and browser sources (`req.query`, `location.hash`, `URLSearchParams`, `document.cookie`), critical sinks mapped to CWEs, and verified sanitizers (`DOMPurify.sanitize`, `encodeURIComponent`, `path.basename`, `parseInt`).
- **Deterministic Security Rules (`rules.py`):** 16 deterministic rules covering code injection (CWE-95), command injection (CWE-78), DOM XSS (CWE-79), open redirect (CWE-601), SQL injection (CWE-89), path traversal (CWE-22), SSRF (CWE-918), weak cryptography (CWE-327, CWE-338), hard-coded secrets (CWE-798), invalid JWT verification (CWE-347), prototype pollution (CWE-1321), ReDoS (CWE-1333), Trojan Source / Unicode tricks (CWE-506), and disabled TLS verification (CWE-295).
- **Verified Remediation Engine (`fixes.py` & `imports.py`):** Automated patch generators with CommonJS (`require`) vs ESM (`import`) detection, preserving "use strict" directives and shebangs.
- **Full Architecture Preservation:** Zero modifications to `src/apsla/pipeline.py`, `src/apsla/fusion.py`, `src/apsla/ml/`, and `src/apsla/server/app.py`.

---

## 2. Deep-Dive Architecture & Core Theoretical Concepts

### A. The Regex-vs-Division Disambiguation Problem

In formal language theory, a lexical analyzer is typically modeled as a deterministic finite automaton (DFA) recognizing regular expressions (Chomsky Type-3 language). However, standard ECMAScript lexing is strictly **context-sensitive**.

Consider these two syntactically valid JavaScript lines:
```javascript
// Case 1: Division followed by division
let result = (a + b) / 2 / c;

// Case 2: Function call or grouping followed by a Regular Expression
return (x + y); /abc/.test(z);

// Case 3: Block statement followed by a Regular Expression
if (isValid) { } /abc/.test(z);
```

In isolation, when the lexer encounters the `/` character, it cannot decide whether to emit an `OPERATOR` token (`/`) or consume a `REGEX` token (`/abc/`) without examining prior significant tokens.

#### The Lookback Disambiguation Algorithm
SecureLex IDE resolves this in `JavaScriptLexer._should_lex_regex` using a deterministic lookback table over the most recent non-whitespace, non-comment token:

```
                  ┌───────────────────────────────┐
                  │      Encounter '/' Character   │
                  └──────────────┬────────────────┘
                                 │
                 Is next character '/' or '*'?
                  ┌──────────────┴──────────────┐
                 Yes                            No
                  │                              │
         [Lex Line/Block Comment]    Is next character '>'? (JSX '/>')
                                      ┌──────────┴──────────┐
                                     Yes                    No
                                      │                      │
                             [Lex JSX Operator '/>']  Inspect Previous
                                                      Significant Token
                                                             │
                  ┌──────────────────────────────────────────┴──────────────────────────┐
                  │                                                                     │
        Previous Token is:                                                    Previous Token is:
   • Number, String, Identifier                                          • Delimiter: ( , = : [ ! & | ? { } ;
   • Value Keyword: this, super, true, false, null                       • Expression Keyword: return, typeof,
   • Closing Group: ), ]                                                   throw, delete, void, await, yield
   • Completed Template: `...`                                           • Binary/Unary Operator: +, -, *, ==, =>
   • Postfix ++ or --                                                    • Start of File
                  │                                                                     │
                  ▼                                                                     ▼
         [Lex Division Operator /]                                           [Lex Regular Expression /.../]
```

#### Grammar Rule Table
| Preceding Significant Token | Meaning of Following `/` | Example |
| :--- | :--- | :--- |
| `IDENTIFIER`, `NUMBER`, `STRING` | Division (`OPERATOR`) | `total / count`, `10 / 2`, `"str" / 2` |
| `)`, `]` | Division (`OPERATOR`) | `(x + y) / 2`, `arr[0] / 5` |
| `this`, `super`, `true`, `false`, `null` | Division (`OPERATOR`) | `this / 2`, `false / 1` |
| `++`, `--` (postfix) | Division (`OPERATOR`) | `x++ / y` |
| `(`, `[`, `{` | Regular Expression (`REGEX`) | `foo(/abc/)`, `[/abc/]`, `{ re: /abc/ }` |
| `=`, `+=`, `-=`, `*=`, `/=` | Regular Expression (`REGEX`) | `pattern = /abc/` |
| `,`, `:`, `;` | Regular Expression (`REGEX`) | `fn(x, /abc/)`, `case: /abc/`, `; /abc/.test(s)` |
| `!`, `&`, `|`, `?`, `^`, `~` | Regular Expression (`REGEX`) | `!/abc/.test(s)`, `cond ? /a/ : /b/` |
| `return`, `typeof`, `yield`, `await` | Regular Expression (`REGEX`) | `return /abc/.test(s)` |
| `=>` | Regular Expression (`REGEX`) | `x => /abc/.test(x)` |

---

### B. Template Literal Recursion via Modal Lexer State Machine

ECMAScript template literals support embedded expressions using `${ ... }`. Crucially, embedded expressions can themselves contain template literals to arbitrary depth:

```javascript
const message = `Outer: ${ `Inner 1: ${ `Inner 2: ${x}` }` }`;
```

A flat regular expression cannot match balanced nested constructs (as balanced parentheses require at least a Chomsky Type-2 Context-Free Grammar with a pushdown automaton).

#### Modal Stack Implementation
SecureLex IDE implements a **Modal State Machine** with two synchronized stacks:
1. `_mode_stack: list[int]`: Tracks current lexer mode:
   - `_MODE_NORMAL` (0): Standard JavaScript code.
   - `_MODE_TEMPLATE` (1): Raw template string scanning for closing backtick (`` ` ``) or interpolation entry (`${`).
   - `_MODE_TEMPLATE_EXPR` (2): JavaScript expression scanning inside `${ ... }`.
2. `_template_brace_depth: list[int]`: Tracks curly brace nesting depth specifically within the current `${ ... }` expression.

```
       ` (Backtick)                ${ (Interpolation)
NORMAL ─────────────► TEMPLATE ────────────────────────► TEMPLATE_EXPR
                      (Mode 1)                          (Mode 2)
                         │                                 │
                         │ ` (Backtick)                    │ } (Matching brace)
                         ▼                                 ▼
                       NORMAL ◄────────────────────── TEMPLATE
```

#### State Transition Algorithm:
1. Encountering `` ` `` in `_MODE_NORMAL`:
   - Emits `` ` `` as a `TEMPLATE` token.
   - Pushes `_MODE_TEMPLATE` onto `_mode_stack`.
2. In `_MODE_TEMPLATE`:
   - Scans characters verbatim (including newlines and escapes).
   - If `${` is encountered: emits accumulated characters as `TEMPLATE` token, consumes `${`, pushes `_MODE_TEMPLATE_EXPR` onto `_mode_stack`, and initializes `_template_brace_depth.append(0)`.
   - If `` ` `` is encountered: emits closing `TEMPLATE` token, pops `_MODE_TEMPLATE`, returns to prior mode.
3. In `_MODE_TEMPLATE_EXPR`:
   - Normal lexing resumes (keywords, identifiers, numbers, operators).
   - If `{` is encountered: increments `_template_brace_depth[-1] += 1`.
   - If `}` is encountered:
     - If `_template_brace_depth[-1] > 0`: decrements brace counter (ordinary block/object inside expression).
     - If `_template_brace_depth[-1] == 0`: marks interpolation exit! Pops `_mode_stack`, pops `_template_brace_depth`, and returns to `_MODE_TEMPLATE`.

This guarantees exact, lossless tokenization to infinite recursion depth while preventing stack overflow.

---

### C. DOM-Based Cross-Site Scripting (DOM XSS)

DOM XSS occurs when an application contains client-side JavaScript that processes data from an untrusted source in an unsafe way, usually by writing the data back to the Document Object Model (DOM).

#### Source-Sink Data Flow
```
Untrusted Sources:
 • location.hash      ─┐
 • location.search     ├─► [ Client-Side Script ] ─► Unsafe DOM Sinks:
 • document.referrer   │                             • element.innerHTML = tainted
 • window.name        ─┘                             • element.outerHTML = tainted
                                                     • document.write(tainted)
                                                     • dangerouslySetInnerHTML={{ __html: tainted }}
```

#### Vulnerability Mechanics
When untrusted data (e.g., `location.hash`) is assigned to `element.innerHTML`, the browser's HTML parser parses the string into DOM nodes. If an attacker passes:
```html
#<img src=x onerror=alert(document.cookie)>
```
The browser instantiates the `<img>` element, fails to load `x`, and immediately executes the JavaScript inside `onerror` in the context of the vulnerable origin.

#### Remediation Approaches:
1. **Safe Sink Assignment (`textContent`):**
   ```javascript
   // Vulnerable:
   document.getElementById("output").innerHTML = location.hash.slice(1);

   // Verified Fix:
   document.getElementById("output").textContent = location.hash.slice(1);
   ```
   `textContent` assigns the value as raw character text. The HTML parser is never invoked, completely neutralizing script execution.
2. **HTML Sanitization (`DOMPurify.sanitize`):**
   When HTML formatting must be preserved (e.g., user-submitted rich text):
   ```javascript
   // Vulnerable:
   div.innerHTML = userBio;

   // Verified Fix:
   div.innerHTML = DOMPurify.sanitize(userBio);
   ```

---

### D. Prototype Pollution in JavaScript & Node.js

Prototype pollution is a critical vulnerability unique to prototype-based languages like JavaScript. Every JavaScript object inherits properties from its prototype (`Object.prototype`).

#### Mechanics of Prototype Pollution
If an application recursively merges an untrusted JSON object into an existing object without validating object keys:

```javascript
function merge(target, source) {
    for (let key in source) {
        if (typeof source[key] === 'object' && source[key] !== null) {
            if (!target[key]) target[key] = {};
            merge(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}

// Attacker-controlled JSON payload:
const payload = JSON.parse('{"__proto__": {"isAdmin": true}}');
merge({}, payload);

// Later in application:
const normalUser = {};
console.log(normalUser.isAdmin); // Outputs: true!
```

#### Consequences
1. **Privilege Escalation:** Injecting properties like `isAdmin`, `authorized`, or `role` modifies the behavior of authorization checks across all objects in the Node.js runtime.
2. **Remote Code Execution (RCE Gadgets):** In Node.js, libraries often check optional properties. For example, child process spawning libraries check options like `shell` or `env`. Polluting `Object.prototype.shell = "/bin/sh"` can trigger arbitrary command execution when any innocent `spawn()` call is made.

#### SecureLex Defense Strategies:
1. **Rule Detection (`APS-JS-INJ-004`):** Flags unsafe calls to `Object.assign` or merge routines handling untrusted inputs.
2. **Key Sanitization:** Rejecting keys matching `__proto__`, `constructor`, or `prototype`.
3. **Prototype-Free Dictionaries:**
   ```javascript
   const safeMap = Object.create(null); // No prototype to pollute!
   ```
4. **Freezing the Prototype:**
   ```javascript
   Object.freeze(Object.prototype);
   ```

---

## 3. Comprehensive Rule Taxonomy

| Rule ID | Title | CWE | Severity | Default Fix |
| :--- | :--- | :--- | :--- | :--- |
| `APS-JS-INJ-001` | Dynamic Code Injection (eval / new Function) | CWE-95 | Critical | Replace `eval(json)` with `JSON.parse` |
| `APS-JS-INJ-002` | Command Injection (`child_process`) | CWE-78 | Critical | Convert `exec(cmd)` to `execFile` array |
| `APS-JS-INJ-003` | SQL Injection (Concatenation / Template) | CWE-89 | Critical | Parameterized queries with `?` or `$1` |
| `APS-JS-INJ-004` | Prototype Pollution (`Object.assign` / merge) | CWE-1321 | High | Key sanitization / `Object.create(null)` |
| `APS-JS-INJ-005` | Regular Expression Denial of Service (ReDoS) | CWE-1333 | Medium | Static regex / escape regex metachars |
| `APS-JS-XSS-001` | DOM Cross-Site Scripting (`innerHTML`) | CWE-79 | High / Crit | Replace `innerHTML` with `textContent` |
| `APS-JS-XSS-002` | React `dangerouslySetInnerHTML` XSS | CWE-79 | High / Crit | Wrap with `DOMPurify.sanitize()` |
| `APS-JS-NET-001` | Open Redirect (`location.href` assignment) | CWE-601 | Medium | URL validation / relative path whitelist |
| `APS-JS-NET-002` | Server-Side Request Forgery (`axios` / `fetch`) | CWE-918 | High | Whitelist check / URL validation |
| `APS-JS-NET-003` | Disabled TLS Verification (`rejectUnauthorized`) | CWE-295 | High | Enforce `rejectUnauthorized: true` |
| `APS-JS-IO-001` | Path Traversal (`fs.readFile`) | CWE-22 | High | Validate with `path.basename()` |
| `APS-JS-CRY-001` | Insecure Pseudorandom Number (`Math.random`) | CWE-338 | Medium | `crypto.randomUUID()` / `randomBytes` |
| `APS-JS-CRY-002` | Weak Cryptographic Hash (`md5` / `sha1`) | CWE-327 | Medium | Replace with `sha256` |
| `APS-JS-SEC-001` | Hard-Coded Secret / API Key | CWE-798 | High | Replace with `process.env.VAR` |
| `APS-JS-SEC-002` | Insecure JWT Verification (`none` alg / decode) | CWE-347 | High | Enforce HMAC/RSA algorithm verify |
| `APS-JS-OBF-001` | Obfuscated Execution (`atob` / `fromCharCode`) | CWE-506 | High | Manual review / eliminate eval wrapper |

---

## 4. Viva Voce Examination Questions & Authoritative Answers

### Q1: Why is lexical analysis of JavaScript context-sensitive rather than context-free?
**Answer:**  
In standard compiler design (Chomsky hierarchy), a lexical analyzer is context-free and implemented as a finite state automaton where each token depends only on the current character stream. JavaScript breaks this property due to the ambiguity of the forward slash (`/`). Depending on the preceding syntactic token, `/` can be a binary division operator (`x / y`), compound assignment (`x /= y`), a comment delimiter (`//`, `/*`), or the beginning of a regular expression literal (`/pattern/flags`). Because the grammatical category of `/` depends on whether the preceding token was an operand (like an identifier, number, or closing parenthesis) or an operator/delimiter (like `(`, `=`, or `return`), the lexer must maintain lookback context over the prior significant token, rendering JavaScript lexical analysis context-sensitive.

---

### Q2: How does SecureLex IDE handle arbitrarily nested template literals in a state machine without recursion limits?
**Answer:**  
SecureLex IDE uses a modal state machine with two synchronized stacks:
1. `_mode_stack`: Tracks the active mode (`_MODE_NORMAL`, `_MODE_TEMPLATE`, `_MODE_TEMPLATE_EXPR`).
2. `_template_brace_depth`: A stack of integer counters tracking curly brace balance per nesting level.

When a template literal opens with `` ` ``, `_MODE_TEMPLATE` is pushed onto `_mode_stack`. When interpolation `${` is encountered, `_MODE_TEMPLATE_EXPR` is pushed and a brace counter initialized to 0 is pushed onto `_template_brace_depth`. Expressions inside `${}` are then tokenized normally. If curly braces `{}` appear within the expression (e.g. object literals or block statements), `_template_brace_depth[-1]` increments and decrements accordingly. When a `}` is encountered while `_template_brace_depth[-1] == 0`, the interpolation exits, popping the stack and returning to template string scanning. Because this relies on heap-allocated Python lists rather than recursive function calls, template literal nesting depth is arbitrarily deep and never risks call stack exhaustion.

---

### Q3: Why is `textContent` considered a safe sink for untrusted data while `innerHTML` is vulnerable to DOM XSS?
**Answer:**  
When untrusted data is assigned to `element.innerHTML`, the browser engine invokes its HTML parser and tokenizes the input as markup. If the data contains `<script>`, `<img>` with `onerror`, or `<svg onload>`, the browser creates corresponding DOM elements and executes the embedded script in the application's origin context. Conversely, assigning to `element.textContent` (or `innerText`) accesses the DOM node's string content directly without invoking the HTML parser. The browser renders the text verbatim, treating characters like `<` and `>` as literal glyphs rather than HTML tag delimiters. Consequently, script injection is physically impossible via `textContent`.

---

### Q4: What is prototype pollution in Node.js and how does it escalate from property injection to remote code execution?
**Answer:**  
In JavaScript, objects inherit methods and properties from their prototype chain up to `Object.prototype`. If an application merges untrusted input into an existing object without validating property keys, an attacker can specify property paths containing `__proto__` or `constructor.prototype`. The merge operation assigns the property directly to `Object.prototype`, which instantly reflects across every object in the runtime.  
This escalates to Remote Code Execution (RCE) via "gadget chains": many Node.js core modules and third-party libraries inspect configuration objects. For instance, when Node's `child_process.fork()` or `spawn()` is called, it checks `options.shell` or `options.env`. If `Object.prototype.shell` has been polluted with an attacker-specified shell command, subsequent innocent process executions invoke the injected shell, yielding full server compromise.

---

### Q5: How does SecureLex IDE ensure that verified automated fixes in JavaScript remain strictly idempotent under `fix_all`?
**Answer:**  
SecureLex IDE enforces fix idempotency ($f(f(x)) = f(x)$) through three structural mechanisms:
1. **Target Finding Elimination:** Fix generators are designed so that applying the patch removes the syntactic pattern targeted by the rule. For example, replacing `element.innerHTML = x` with `element.textContent = x` eliminates the `innerHTML` property access, ensuring the rule cannot trigger on subsequent passes.
2. **Duplicate Import Prevention:** The `ensure_import_javascript` utility inspects the entire file before injecting statements like `const crypto = require('crypto');` or `import DOMPurify from 'dompurify';`. If the module is already required or imported, the edit set returned is empty (`[]`).
3. **Convergence Verification Loop:** `fix_all` iteratively analyzes and applies fixes up to 3 passes or until zero fixes are generated. If a fix produces new syntax errors or secondary rule regressions, the shadow verification sandbox rejects the candidate patch and reverts the change.
