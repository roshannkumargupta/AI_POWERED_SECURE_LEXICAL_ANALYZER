# Phase 1 Explained — Shared Core, Offset Handling, Unicode Defense & Language Plugin Architecture

---

## 1. Plain-Language Explanation: What Did We Build and Why?

In **Phase 1**, we constructed the foundational shared core that powers every language supported by **SecureLex IDE** (`apsla`). Rather than jumping directly into language-specific lexing, we built the universal infrastructure that guarantees accuracy, security, and extensibility across the entire platform.

### A. Unified Data Models (`src/apsla/models.py`)
All components—lexer, rules engine, taint analyzer, machine learning models, fix verifier, and web APIs—communicate using a strictly typed, immutable Pydantic v2 schema:
- **`Range`**: 1-based, end-exclusive document coordinates measured in UTF-16 code units (the native coordinate space of the Monaco Editor / VS Code).
- **`Token` & `TokenInfo`**: Exact lexical token representations with line, column, and UTF-16 offset boundaries, paired with security labels (`SAFE`, `SUSPICIOUS`, `MALICIOUS`) and calibrated risk scores.
- **`Finding` & `Fix`**: Comprehensive vulnerability records containing severity, CWE identifiers, human-readable explanations, evidence dictionaries, and verifiable atomic text `Edit` patches.
- **`VerificationResult`**: Certification ensuring fixes are syntactically well-formed, eliminate the targeted finding, introduce zero new regressions, and operate idempotently.
- **`AnalysisResult`**: The top-level payload serializing the token stream, findings, security health score, and engine metadata.

### B. Accurate Coordinate & Offset Handling (`src/apsla/lexing/common.py`)
In web-based code editors like Monaco, cursor and selection coordinates are calculated using UTF-16 code units because JavaScript strings use UTF-16 encoding. Python strings, conversely, count Unicode codepoints. For characters inside the Basic Multilingual Plane (BMP), Python character count matches UTF-16 code unit count. However, for **astral plane characters** (such as emoji 🚀, mathematical symbols, and historic scripts), a single Python character corresponds to **two UTF-16 code units** (a surrogate pair).

If an analyzer naively reports Python character offsets, editor squiggly underlines and automated fix replacements will drift out of alignment on any file containing emojis or non-BMP symbols. Our `OffsetMap` solves this by building $O(1)$ bidirectional lookups between Python string indices, UTF-16 code units, and 1-based `(line, col)` coordinates, while gracefully handling CRLF, LF, CR newlines, and tabs.

### C. Multi-Vector Unicode Defense Layer (`src/apsla/unicode_defense/`)
Attackers exploit Unicode features to deceive both human code reviewers and naive static analyzers. Our Unicode defense layer neutralizes these threats before lexical analysis begins:
1. **Trojan Source (CVE-2021-42574):** Inspects for bidirectional control characters (U+202A–202E, U+2066–2069, U+200E/200F, U+061C) that alter visual text rendering order, disguising executable commands as comments. Flagged as `APS-ALL-UNI-001` (Severity: HIGH).
2. **Zero-Width & Invisible Characters:** Identifies hidden characters (U+200B–200D, U+2060, U+FEFF outside offset 0, U+00AD, U+180E) that enable variable shadowing and filter bypass. Flagged as `APS-ALL-UNI-002` (Severity: HIGH in identifiers).
3. **Unicode Tag Characters:** Detects deprecated tags (U+E0000–E007F) used to smuggle hidden payloads. Flagged as `APS-ALL-UNI-003` (Severity: HIGH).
4. **Confusables & Homoglyphs:** Utilizes a dataset of 1,868 look-alike character mappings compiled from Unicode Consortium definitions. When an identifier disguises a dangerous API or keyword (such as Cyrillic `ехес` or fullwidth `ｅｖａｌ`), it is flagged with `APS-ALL-UNI-006` (Severity: HIGH).
5. **Mixed-Script Identifiers:** Detects identifiers combining characters from distinct Unicode scripts (e.g., Latin and Cyrillic) using `\p{Script=...}` property escapes (`APS-ALL-UNI-005`).
6. **Adversarial Token Recovery:** Synthesizes `recovered_text` where look-alikes are mapped to canonical ASCII and invisibles are stripped, while maintaining an exact inverse mapping so all reported findings point directly to the original file coordinates.

### D. Language Plugin Interface & Registry (`src/apsla/languages/`)
Following Open-Closed Principle (Section F of `PROJECT_SPEC.md`), the `LanguagePlugin` protocol establishes the exact contract for language extensions. Language implementations register via `registry.py`, which supports automatic language detection by file extension and shebang. Adding a new programming language requires zero changes to the core pipeline, scoring, or web server.

---

## 2. Concept Glossary

- **Lexer (Lexical Analyzer / Tokenizer):** The first component of a language processor. It reads a linear sequence of characters and groups them into meaningful grammatical units called *tokens* according to lexical rules (regular expressions or finite-state automata).
- **Token:** A structured object produced by a lexer, containing a syntactic category (e.g., `KEYWORD`, `IDENTIFIER`, `STRING`, `OPERATOR`), the raw text slice, and exact document coordinates (line, column, and code unit offsets).
- **Homoglyph (Confusable):** A character from one script that visually resembles a character from another script (e.g., Cyrillic small 'е' U+0435 versus Latin small 'e' U+0065). Attackers substitute homoglyphs to trick reviewers into believing a malicious custom function is a built-in standard library routine.
- **Bidirectional (Bidi) Override (Trojan Source):** Unicode control characters (such as Right-to-Left Override `U+202E` or Left-to-Right Isolate `U+2066`) designed for typesetting bidirectional languages like Arabic and Hebrew. In code, attackers use them to invert the visual rendering order of tokens so that executable logic appears visually inside comments or string literals.
- **Offset Map:** A precomputed indexing structure that translates between internal string representations (Python byte or character indices) and display editor coordinates (UTF-16 code units and 1-based line/column numbers).
- **Adversarial Recovery:** The process of stripping invisible control characters and normalizing look-alike glyphs into their canonical ASCII equivalents, allowing downstream parsers to inspect the true semantic intent of obfuscated code.
- **Fix Idempotency:** The property that applying a proposed remediation patch once fixes the defect, and applying it any subsequent number of times results in no further changes ($f(f(x)) = f(x)$).

---

## 3. Five Viva Questions with Model Answers

### Question 1: Why is an `OffsetMap` necessary, and why can we not simply use Python's built-in string indices for Monaco Editor coordinates?
**Model Answer:**  
"Python strings are indexed by Unicode codepoints, whereas Monaco Editor (and JavaScript in general) calculates column positions and selection ranges in UTF-16 code units. For characters in the Basic Multilingual Plane (BMP), one codepoint equals one UTF-16 code unit. However, astral plane characters (such as emoji 🚀 `U+1F680`, mathematical symbols, and supplementary ideographs) require two 16-bit code units (a surrogate pair) in UTF-16. If a file contains two emojis on line 1, a token on that line would have its Python character index drift by 2 units relative to Monaco's UTF-16 column. The `OffsetMap` precomputes cumulative code unit offsets and line boundaries, ensuring pixel-perfect alignment for diagnostic squiggles and atomic fix edits without drift."

### Question 2: What is the Trojan Source vulnerability (CVE-2021-42574), and how does SecureLex IDE defend against it?
**Model Answer:**  
"Trojan Source exploits Unicode bidirectional formatting characters (such as `U+202E` Right-to-Left Override and `U+2066` Left-to-Right Isolate) to manipulate how compilers and editors visually display tokens. By inserting bidi controls, an attacker can make dangerous executable code appear visually inside a comment, or make an early return appear inside an inactive branch. SecureLex IDE scans the raw character stream for all Trojan Source bidi codepoints, flags them under rule `APS-ALL-UNI-001` with `Severity.HIGH`, marks the overlapping tokens as `MALICIOUS`, and generates verified remediation fixes that safely delete the control characters."

### Question 3: How does SecureLex IDE differentiate between harmless non-ASCII characters and malicious homoglyph attacks?
**Model Answer:**  
"SecureLex IDE employs contextual differentiation:
1. **Isolated non-ASCII in comments** (e.g., accented characters in French comments or German umlauts) are categorized as informational (`Severity.INFO`) and do not penalize the security score.
2. **Confusables in benign identifiers** (e.g., `n\u043Ede` recovering to `node`) trigger `APS-ALL-UNI-004` at `Severity.MEDIUM` to warn the developer of potential confusion.
3. **Obfuscated dangerous targets** (e.g., Cyrillic `\u0435\u0445\u0435\u0441` or fullwidth `\uFF45\uFF56\uFF41\uFF4C` recovering to execution keywords or security-sensitive APIs like `exec`, `eval`, or `system`) trigger `APS-ALL-UNI-006` at `Severity.HIGH` with label `MALICIOUS`.
4. **Mixed-script identifiers** combining glyphs across distinct script boundaries (like Latin and Cyrillic) trigger `APS-ALL-UNI-005` to alert on script spoofing."

### Question 4: Why does our pipeline execute Unicode defense and recovery *before* language-specific lexical analysis?
**Model Answer:**  
"If language-specific lexing or AST parsing is executed on raw adversarial text, the lexer will either fail to recognize obfuscated keywords (treating Cyrillic `ехес` as a custom user variable rather than the built-in `exec`) or crash on unexpected control characters. By placing the Unicode defense layer at Stage 2, SecureLex IDE detects adversarial anomalies immediately and produces a clean `recovered_text` stream. Downstream components (the resilient lexer, taint flow engine, and rule checkers) evaluate the recovered semantics while referencing the original document coordinates through the inverse offset map."

### Question 5: How does the `LanguagePlugin` architecture guarantee that adding support for a new programming language requires zero changes to the core engine?
**Model Answer:**  
"SecureLex IDE adheres to the Open-Closed Principle using the `LanguagePlugin` protocol defined in `src/apsla/languages/base.py`. Any new language (such as Go, Rust, or Ruby) simply implements this protocol—providing its lexer, rules, taint profile, and fix generators—and registers itself with `src/apsla/languages/registry.py`. The analysis pipeline (`src/apsla/pipeline.py`), fusion logic, scoring formulas, and FastAPI web routes interact strictly with the abstract `LanguagePlugin` interface and registry lookup functions (`get(id)` and `detect(filename, text)`). This design ensures that adding or modifying language plugins never requires editing core pipeline code."
