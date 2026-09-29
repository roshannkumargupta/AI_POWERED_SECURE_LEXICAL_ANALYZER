# Phase 0 Explained — Reorganization, Specification & Baseline Measurement

---

## 1. Plain-Language Explanation: What Did We Do and Why?

In Phase 0, we laid the engineering foundation for **SecureLex IDE** (`apsla`). Prior to this phase, the project consisted of two disparate folders extracted from a student zip archive: an unlicensed Python analysis and web prototype (`secure_lexer_code-Part1`) and an MIT-licensed Java-oriented prototype (`AI-Powered-Secure-Lexical-Analyzer-main`).

As professional software engineers, before writing any product code, we must:
1. **Clean and Sanitize:** Isolate legacy student code into an immutable, read-only reference directory (`legacy/`). We purged ephemeral logs, build artifacts, virtual environments, and uncommitted git metadata so the repository is clean and deterministic.
2. **Preserve History and Attribution:** We used `git mv` so every moved file retains its commit tracking. We copied raw datasets to `data/raw/`, verified their SHA-256 cryptographic hashes in `data/PROVENANCE.md`, and archived the open-source MIT license in `third_party/`.
3. **Establish the Master Contract (`PROJECT_SPEC.md`):** Complex software systems fail when architectural decisions are ambiguous. We wrote an exhaustive specification detailing the technology stack, unified Pydantic v2 data models, pipeline sequence, fusion mathematics, fix verification semantics, and UI design tokens.
4. **Honest Baseline Measurement (`scripts/legacy_probe.py`):** We probed the senior's actual codebase against 6 realistic security scenarios. Rather than assuming the senior's tool worked, we scientifically measured its capabilities and exposed its false negatives (missed Web taint, missed Trojan Source) and false positives (flagging safe subprocess calls). We also verified 5 deep architectural defects with concrete file and line citations.
5. **Project Skeleton:** We scaffolded the entire `src/apsla/` modular architecture, standard configuration files (`pyproject.toml`, `requirements.txt`, `.gitignore`, `ruff.toml`), test directories, and smoke tests.

---

## 2. Concept Glossary

- **Lexical Analysis (Tokenization):** The initial compiler phase that converts an input stream of raw characters into a sequence of structured symbols called *tokens* (e.g., keywords, identifiers, operators, literals).
- **Taint Analysis:** A data-flow analysis technique that tracks untrusted user inputs ("sources") as they propagate through program variables, checking whether they reach sensitive execution functions ("sinks") without passing through validation or sanitization routines.
- **Hybrid Detection:** Combining deterministic rule-based analysis (which is fast, precise, and verifiable) with statistical machine learning models (which recognize anomalous patterns and obfuscations) into a unified confidence score.
- **Homoglyphs & Confusables:** Characters from different Unicode scripts (such as Cyrillic 'е' and Latin 'e') that look identical or nearly identical to human readers but have distinct codepoints. Attackers use homoglyphs to disguise malicious functions.
- **Trojan Source (CVE-2021-42574):** An adversarial attack using Unicode bidirectional control characters (such as Right-to-Left Override `U+202E`) to visually reorder code displayed in editors, making dangerous code look like innocent comments or strings.
- **Zero-Crash Resilient Lexer:** A lexer designed never to throw exceptions on syntactically malformed input. Unrecognized or broken characters are emitted as `ERROR` tokens, guaranteeing that `sum(token.text) == original_input`.
- **Fix Idempotency:** The mathematical property where applying an automated fix once transforms the code, but applying it a second or third time results in zero additional changes ($f(f(x)) = f(x)$).
- **Data Provenance:** A verifiable record of the origins, lineage, size, and cryptographic hash (SHA-256) of every external dataset utilized in the system.

---

## 3. Five Viva Questions with Model Answers

### Question 1: Why did you isolate the senior's code in `legacy/` as read-only rather than building directly on top of it?
**Model Answer:**  
"Building directly on top of legacy student code would inherit unverified architectural flaws, licensing uncertainties, and severe reliability defects. The senior codebase had several critical bugs, such as a BiLSTM being fed a sequence length of 1, silent fallback to uninitialized random neural weights when loading failed, and a training script lacking an actual training loop. Additionally, Part 1 lacked an open-source license. By freezing the legacy code in `legacy/` as an immutable benchmark, we can honestly measure our improvements, reference historical patterns where legally permissible, and maintain an uncompromising engineering standard in `src/apsla`."

### Question 2: In Probe 1 (`name = request.args.get("q"); os.system("echo " + name)`), why did the senior's tool produce a false negative?
**Model Answer:**  
"The senior's `TaintTracker` used naive token-level string matching against a set of predefined source names: `_SOURCE_FUNCS = {"input", "request.args", "request.form", ...}`. However, the senior's lexer tokenizes dotted expressions into distinct tokens: `request` (IDENTIFIER), `.` (DOT), and `args` (IDENTIFIER). When `tok.raw_value in _SOURCE_FUNCS` was checked, the individual token `"request"` never matched `"request.args"`. Because taint was never initiated on `name`, the downstream call `os.system(...)` was not recognized as a tainted sink, resulting in a total false negative for command injection."

### Question 3: Why is evaluating a BiLSTM on a sequence length of 1 an architectural flaw?
**Model Answer:**  
"A Bidirectional Long Short-Term Memory (BiLSTM) network is designed to model sequential dependencies across a sequence of items, utilizing both forward and backward hidden states ($\vec{h}_t$ and $\overleftarrow{h}_t$) to capture preceding and succeeding temporal context. In the senior's `AIInferenceEngine`, each token's feature vector was isolated and unsqueezed into tensor shape `(batch=1, seq_len=1, dim=34)`. When `seq_len = 1`, the recurrent loop executes for a single step with zero previous and zero future states. This completely defeats the purpose of recurrent sequence modeling and reduces the BiLSTM to an unnecessarily expensive linear transformation."

### Question 4: How does SecureLex IDE define and guarantee "verified" fixes?
**Model Answer:**  
"In SecureLex IDE, a fix is never presented or applied blindly. When a fix generator synthesizes a candidate patch (represented as non-overlapping character range edits), the patch is applied in-memory to an isolated shadow copy of the document. The modified source is then re-parsed and re-analyzed by the entire pipeline. The fix is certified `verified = True` if and only if three conditions hold: (1) `syntax_ok` (the modified code is syntactically valid), (2) `finding_gone` (the original vulnerability is eliminated), and (3) `new_findings` (no new findings of severity `medium` or higher are introduced). Furthermore, Fix-All is engineered to be strictly idempotent."

### Question 5: Why must coordinates in our data model be represented in UTF-16 code units?
**Model Answer:**  
"Modern web code editors, specifically Monaco Editor (which powers VS Code), calculate line columns and text cursor positions using UTF-16 code units, because JavaScript strings are UTF-16 encoded. Characters outside the Basic Multilingual Plane (such as certain emojis, mathematical symbols, or uncommon Unicode glyphs) are represented in UTF-16 as surrogate pairs (two 16-bit code units), but in standard Python string slicing they count as a single character. If our backend reported raw Python character offsets or byte offsets, squiggly underlines and fix replacements in Monaco Editor would drift out of alignment on files with non-BMP or complex Unicode text. Generating a UTF-16 offset map during the normalization stage ensures pixel-perfect UI synchronization."
