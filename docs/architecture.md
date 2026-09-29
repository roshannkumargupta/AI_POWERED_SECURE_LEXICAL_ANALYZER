# SecureLex IDE (`apsla`) — Architecture & System Design

SecureLex IDE is an extensible, hybrid static analysis and security auditing system engineered for multi-language lexical, data-flow, and adversarial analysis.

---

## 1. System Architecture Overview

```
                        +----------------------------+
                        |  Raw Source Code Input     |
                        +--------------+-------------+
                                       |
                                       v
                     +----------------------------------+
                     | Stage 1: Text Normalization      |
                     |  - BOM strip, line normalization |
                     |  - UTF-16 Monaco coordinate map  |
                     +-----------------+----------------+
                                       |
                                       v
                     +----------------------------------+
                     | Stage 2: Unicode Defense Layer   |
                     |  - Bidi override scanner         |
                     |  - Zero-width & invisible filter |
                     |  - Confusable skeleton recovery  |
                     +-----------------+----------------+
                                       |
                                       v
                     +----------------------------------+
                     | Stage 3: Resilient Lexer         |
                     |  - Hand-crafted per language     |
                     |  - Total input reconstruction    |
                     |  - Error-resilient token stream  |
                     +--------+----------------+--------+
                              |                |
             +----------------+                +----------------+
             |                                                  |
             v                                                  v
+------------------------+                             +------------------------+
| Stage 4: Deterministic |                             | Stage 5: Taint Flow    |
| Security Rules         |                             | Analysis               |
| - Language AST rules   |                             | - Python: AST data-flow|
| - Generic token checks |                             | - Java/JS/C++: Profile |
+------------+-----------+                             +------------+-----------+
             |                                                      |
             +------------------------+-----------------------------+
                                      |
                                      v
                     +----------------------------------+
                     | Stage 6: Machine Learning (ML)   |
                     |  - 45 Language-Agnostic Features |
                     |  - 9-Token Sliding Window BiLSTM |
                     |  - 3-Class Probabilities         |
                     +-----------------+----------------+
                                       |
                                       v
                     +----------------------------------+
                     | Stage 7: Confidence & Severity   |
                     |          Fusion Engine           |
                     |  - Score boosting & damping      |
                     |  - False-positive suppression    |
                     +-----------------+----------------+
                                       |
                                       v
                     +----------------------------------+
                     | Stage 8: Fix Engine & Verifier   |
                     |  - Reverse-order atomic edits    |
                     |  - Shadow re-parse verification  |
                     |  - Idempotent Fix-All            |
                     +-----------------+----------------+
                                       |
                                       v
                        +----------------------------+
                        | AnalysisResult (API / UI)  |
                        +----------------------------+
```

---

## 2. Directory Layout & Module Responsibilities

```
src/apsla/
├── models.py            # Pydantic v2 data contracts (Range, Finding, Fix, AnalysisResult)
├── config.py            # Global constants, severity weights, thresholds, and limits
├── pipeline.py          # Master Analyzer orchestrating analysis stages
├── fusion.py            # Mathematical fusion of rules, taint paths, and ML predictions
├── scoring.py           # Security health score calculator (0 to 100)
├── cwe.py               # Common Weakness Enumeration database and metadata
├── cli.py               # Developer CLI built with Typer and Rich
│
├── unicode_defense/     # Adversarial Unicode detection and token recovery
│   ├── scanner.py       # Scans raw byte/text stream for Trojan Source and invisible chars
│   ├── confusables.py   # Unicode confusable mapping and skeleton calculation
│   ├── scripts.py       # Script detection and mixed-script homoglyph analyzer
│   └── recovery.py      # Transforms obfuscated tokens into canonical ASCII equivalents
│
├── lexing/              # Multi-language lexical analysis infrastructure
│   ├── base.py          # Abstract base lexer defining the tokenization contract
│   ├── token.py         # Token data structures, source spans, and token kinds
│   └── common.py        # Shared scanner utilities and column calculation routines
│
├── languages/           # Pluggable language backends
│   ├── base.py          # LanguagePlugin abstract base interface
│   ├── registry.py      # Language registration and file extension routing
│   ├── python_lang/     # Python: Lexer, AST rules, AST data-flow taint, fixes
│   ├── java_lang/       # Java: Lexer, rules, taint-lite profile, fixes
│   ├── javascript_lang/ # JavaScript: Lexer, rules, taint-lite profile, fixes
│   └── cpp_lang/        # C++: Lexer, rules, taint-lite profile, fixes
│
├── taint/               # Interprocedural and intra-procedural taint flow
│   ├── lite.py          # Shared profile-driven taint engine for Java, JS, and C++
│   └── paths.py         # Source-to-sink graph path traversal and trace rendering
│
├── rules/               # Deterministic security rules
│   ├── base.py          # Rule definition interface with metadata and severity
│   ├── registry.py      # Rule registry by language and category
│   └── generic.py       # Universal pattern checks (entropy, credentials, URL leaks)
│
├── ml/                  # Feature engineering, model architectures, and inference
│   ├── features.py      # 45-dimensional language-agnostic per-token feature extractor
│   ├── windows.py       # 9-token sliding context window generator
│   ├── models.py        # PyTorch BiLSTM and scikit-learn model topologies
│   ├── train.py         # Group-aware cross-validation and training routines
│   ├── evaluate.py      # Metrics computation and confusion matrices
│   ├── infer.py         # Runtime inference with feature-schema hash validation
│   ├── explain.py       # Per-token feature attribution and SHAP/gradient signals
│   └── calibrate.py     # Probability calibration and temperature scaling
│
├── fixes/               # Automated remediation and safety verification
│   ├── engine.py        # Applies edits in reverse document order (end-to-start)
│   ├── verifier.py      # Executes shadow re-analysis to guarantee bug remediation
│   ├── edits.py         # Text replacement abstractions
│   ├── imports.py       # Language-specific import statement injection
│   └── registry.py      # Fix generator registry mapped to rule IDs
│
├── feedback/            # Active learning and developer feedback
│   └── store.py         # Append-only storage for local false-positive signatures
│
├── llm/                 # Optional generative suggestions
│   ├── provider.py      # LLM suggestion provider interface
│   └── null.py          # Zero-overhead default provider when LLM is disabled
│
└── server/              # FastAPI application service
    ├── app.py           # Endpoint definitions and static file mounting
    ├── schemas.py       # HTTP request and response models
    └── samples.py       # Bundled vulnerable and safe demonstration snippets
```

---

## 3. Core Architectural Decisions

### Zero-Crash Resilient Lexing
Compilers traditionally crash or throw parsing exceptions when encountering malformed syntax. In a security IDE, malicious code is deliberately malformed. All APSLA lexers are designed to never raise exceptions; invalid character sequences are emitted as `TokenType.ERROR`, while preserving complete source fidelity:
$$\sum_{t \in \text{tokens}} t.\text{text} \equiv \text{source\_code}$$

### Strict UTF-16 Coordinate Mapping
Web editors such as Monaco calculate column positions in UTF-16 code units (surrogate pairs count as two units). Standard Python strings measure length in Unicode codepoints. APSLA maintains an exact coordinate mapping during normalization so all diagnostic ranges (`start_col`, `end_col`) align pixel-perfectly with Monaco Editor squiggly underlines.

### Verification-Guaranteed Remediation
Security fixes must never break code. Every fix generated by APSLA is tested against a sandboxed in-memory copy of the source code. The fix is re-parsed and re-analyzed:
1. `syntax_ok`: The modified source must pass syntactic validation.
2. `finding_gone`: The target finding that triggered the fix must no longer appear.
3. `new_findings`: No new findings of severity `MEDIUM`, `HIGH`, or `CRITICAL` may be introduced.
Only if all conditions are satisfied is the fix marked `verified = True`.
