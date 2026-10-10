# SecureLex IDE — Master Project Specification

**Product Name:** SecureLex IDE  
**Package Name:** `apsla` (AI-Powered Secure Lexical Analyzer)  
**Supported Languages:** Python, Java, JavaScript, C++  
**Architecture:** IDE-style static/hybrid code analysis platform with verified automated fixes  

---

## A. System Identity & Mission

SecureLex IDE (`apsla`) is a high-performance, developer-first code security platform designed to inspect source code, highlight dangerous and malicious patterns, explain vulnerabilities via exact source-to-sink paths, and provide automated remediations that are rigorously verified before application.

Unlike conventional linters that produce noisy syntactic alerts or black-box ML models that hallucinate vulnerabilities, SecureLex IDE synthesizes deterministic AST/token rules, interprocedural taint flow tracking, Unicode defense, and calibrated machine learning into a single actionable confidence score.

---

## B. Definition of "Intelligent"

In SecureLex IDE, "Intelligent" is strictly defined by six verifiable capabilities:

1. **Hybrid Detection Fusion:** Deterministic rule checking + real data-flow (taint) analysis + a trained ML model fused mathematically into a calibrated confidence score.
2. **Path-Level Explainability:** Every finding includes an exact source-to-sink trace (`source -> propagate -> sanitizer_missing -> sink`) detailing how untrusted data reaches dangerous execution points.
3. **Fix and Verification Loop:** Automated patches are applied to an isolated syntax tree / document copy, re-parsed, and re-analyzed. A fix is marked `verified` only if the original finding is eliminated and no new `medium` or higher severity issues are introduced.
4. **Active Learning from Feedback:** User-marked false positives are stored in a local append-only dataset (`data/feedback/false_positives.jsonl`) and integrated as hard negative examples during scheduled retraining.
5. **Multi-Factor Ranking:** Findings are prioritized by $\text{Severity} \times \text{Confidence} \times \text{Exploitability}$, preventing alert fatigue.
6. **Constrained LLM Suggestions:** Optional LLM-generated fixes (disabled by default) are subjected to the identical verification harness before presentation to the developer.

---

## C. Fixed Technology Stack

### Backend & Core
- **Language & Runtime:** Python 3.12 (Strict typing, `from __future__ import annotations`)
- **API Framework:** FastAPI with Uvicorn
- **Data Modeling & Validation:** Pydantic v2
- **CLI Framework:** Typer with Rich formatting
- **Machine Learning & Math:** PyTorch (CPU build), scikit-learn, NumPy, pandas, joblib
- **Regular Expressions:** `regex` (Unicode-aware regex engine)
- **Testing & Quality:** pytest, pytest-cov, ruff (linter/formatter), hypothesis, codecarbon

### Frontend (Phase 6)
- **Framework & Build:** Vite, React 18, TypeScript (strict mode)
- **Code Editor:** Monaco Editor (`@monaco-editor/react`)
- **Layout & Icons:** `react-resizable-panels`, `lucide-react`
- **Typography & Assets:** `@fontsource/inter` and `@fontsource/jetbrains-mono` bundled locally
- **Offline Guarantee:** Zero external CDN dependencies; full functionality with network interface disabled
- **Cross-Platform:** Windows, macOS, Linux (`pathlib`, UTF-8 encoding across all file I/O)

---

## D. Unified Data Model (`src/apsla/models.py`)

All coordinates use 1-based indexing for line numbers and 1-based indexing for columns, with column offsets calculated in UTF-16 code units for 1:1 compatibility with Monaco Editor. Ranges are end-exclusive.

### Coordinate Range
```python
class Range(BaseModel):
    start_line: int
    start_col: int
    end_line: int
    end_col: int
```

### Finding Model
```python
class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Label(str, Enum):
    MALICIOUS = "MALICIOUS"  # critical, high
    SUSPICIOUS = "SUSPICIOUS"  # medium, low, info


class Finding(BaseModel):
    id: str
    rule_id: str  # Format: APS-<LANG>-<CAT>-<NNN>
    title: str
    cwe: str
    severity: Severity
    label: Label
    confidence: float  # 0.0 .. 1.0
    range: Range
    message: str  # Single-line summary
    explanation: str  # 2 to 4 plain English sentences
    evidence: EvidenceDict  # tokens, rule_score, taint_confirmed, ml_score, ml_mode, unicode
    taint_path: list[
        TaintPathStep
    ]  # step (source|propagate|sink|sanitizer_missing), range, text, note
    fixes: list[Fix]
    sources: list[str]  # subset of ["rule", "taint", "ml", "unicode"]
    suppressed: bool = False
```

### Fix and Verification Model
```python
class Edit(BaseModel):
    range: Range
    new_text: str


class VerificationResult(BaseModel):
    syntax_ok: bool
    finding_gone: bool
    new_findings: list[str]
    verified: bool
    notes: str


class Fix(BaseModel):
    id: str
    finding_id: str
    title: str
    description: str
    confidence: str  # safe | review | manual
    kind: str  # rule | template | llm
    edits: list[Edit]
    verification: VerificationResult
```

### Analysis Result & Health Score
```python
class AnalysisSummary(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    info: int
    score: int  # Security Health Score 0 .. 100
    tokens_total: int
    tokens_malicious: int
    tokens_suspicious: int


class EngineMetadata(BaseModel):
    ml_mode: str  # "on" | "off"
    ml_model_id: str
    taint: str  # "ast" | "lite"
    version: str
    elapsed_ms: float


class AnalysisResult(BaseModel):
    language: str
    filename: str
    findings: list[Finding]
    tokens: list[TokenInfo]
    summary: AnalysisSummary
    engine: EngineMetadata
```

### Security Health Score Formula
$$\text{Score} = \max\left(0, 100 - \sum \text{weight} \times \min(\text{count}, \text{cap})\right)$$

| Severity | Weight | Cap | Max Penalty |
|---|---|---|---|
| Critical | 25 | 4 | 100 |
| High | 12 | 6 | 72 |
| Medium | 5 | 8 | 40 |
| Low | 2 | 10 | 20 |
| Info | 0 | $\infty$ | 0 |

---

## E. End-to-End Analysis Pipeline

The top-level analysis entrypoint is `Analyzer.analyze(source: str, language: str, filename: str, options: dict) -> AnalysisResult`. Execution follows eight discrete stages:

1. **Normalization & Mapping:** Strip UTF-8 BOM, validate line endings, and generate a bidirectional character offset map connecting raw string offsets to UTF-16 Monaco coordinates.
2. **Unicode Defense Layer:** Inspect raw text for bidirectional overrides (Trojan Source U+202E, etc.), zero-width spaces, tag characters, and mixed-script confusables. Produce a sanitized `recovered_text` alongside explicit Unicode findings.
3. **Resilient Lexing:** Execute hand-written lexer for the target language. The lexer never raises exceptions; malformed characters become `ERROR` tokens, and the concatenation of all token texts exactly reconstructs the input.
4. **Deterministic Rule Engine:** Evaluate language-specific and generic AST/token pattern rules.
5. **Taint Analysis Engine:**
   - **Python:** Full AST data-flow analysis with intra-file function summaries.
   - **Java / JavaScript / C++:** Shared taint-lite engine configured via declarative language profiles (`profile.py`).
6. **Machine Learning Inference:** Extract 45 language-agnostic features per token over a sliding 9-token window. Compute 3-class probabilities (`SAFE`, `SUSPICIOUS`, `MALICIOUS`).
7. **Fusion & Ranking:** Reconcile rule detections, taint propagation traces, and ML probabilities into calibrated confidence values.
8. **Fix Generation & Verification:** Synthesize patches, verify them against shadow AST instances, and serialize the final `AnalysisResult`.

---

## F. Language Plugin Interface (`src/apsla/languages/base.py`)

Adding a programming language requires implementing the `LanguagePlugin` abstract base class and registering it in `src/apsla/languages/registry.py`. No modifications to `pipeline.py`, `fusion.py`, `ml/`, or `server/` are permitted.

```python
class LanguagePlugin(ABC):
    id: str  # e.g., "python", "java", "javascript", "cpp"
    display_name: str  # e.g., "Python 3", "Java"
    extensions: list[str]  # e.g., [".py", ".pyw"]
    monaco_id: str  # Monaco editor language identifier
    keywords: frozenset[str]

    @abstractmethod
    def lex(self, source: str) -> list[Token]: ...

    @abstractmethod
    def rules(self) -> list[Rule]: ...

    @abstractmethod
    def taint_profile(self) -> TaintProfile: ...

    @abstractmethod
    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintFinding]: ...

    @abstractmethod
    def fix_generators(self) -> dict[str, FixGenerator]: ...

    @abstractmethod
    def syntax_check(self, source: str) -> tuple[bool, str | None]: ...

    @abstractmethod
    def dangerous_apis(self) -> dict[str, str]: ...
```

---

## G. Machine Learning Architecture & Policy

- **Feature Space:** 45 language-agnostic lexical, structural, statistical, and Unicode features per token, augmented with a one-hot language identifier.
- **Model Architectures Evaluated:** LogisticRegression (baseline), RandomForest, HistGradientBoosting, and a Windowed BiLSTM.
- **BiLSTM Topology:**
  $$\text{Input}(45) \xrightarrow{\text{Linear}} 64 \xrightarrow{\text{LayerNorm}} \text{ReLU} \xrightarrow{\text{BiLSTM}(d=64, \text{win}=9)} \text{Center State} \xrightarrow{\text{MLP}(128 \to 64 \to 3)} \text{Softmax}$$
- **Data Integrity & Grouping:** Group-aware cross-validation splitting by `(language, template_family, snippet_id)` to prevent data leakage. Token-level random splitting is strictly prohibited.
- **Feature Cleanliness:** Taint flags and deterministic rule outputs must **NEVER** be used as ML input features.
- **No Silent Fallback Policy:** If the neural weights file is missing, corrupted, or its feature-schema SHA-256 hash differs from the runtime definition, ML mode is set to `"off"`. This state is explicitly declared in all API responses and visually highlighted as a red pill in the IDE status bar. Silent fallbacks with random uninitialized weights are forbidden.

---

## H. Score & Finding Fusion Rules (`src/apsla/fusion.py`)

Deterministic rules and taint analysis create the base findings; machine learning adjusts confidence and severity.

1. **Token Window Probability:**
   $$ml\_p = \min\left(1.0, \max_{t \in \text{range}} \left(P(\text{MALICIOUS}) + 0.5 \times P(\text{SUSPICIOUS})\right)\right)$$
2. **Confidence Calculation (when ML is ON):**
   $$\text{Confidence} = 0.7 \times \text{rule\_conf} + 0.3 \times ml\_p$$
3. **Taint Confirmation Boost:** If data-flow taint analysis confirms reachability from source to sink:
   $$\text{Confidence} = \min(1.0, \text{Confidence} + 0.15)$$
   $$\text{Severity} \leftarrow \min(\text{CRITICAL}, \text{Severity} + 1)$$
4. **Noisy Rule Suppression / Downgrade:** If a rule triggers without taint confirmation and $ml\_p < 0.15$:
   $$\text{Severity} \leftarrow \max(\text{INFO}, \text{Severity} - 1)$$
   The finding note records: `"downgraded: model sees this as usual code"`.
5. **ML-Only Anomaly Rule:** Pure ML detections without matching rules generate findings under rule `APS-ALL-ML-001` (capped at maximum 10 per file).
6. **Suppression:** Findings matching signatures in `data/feedback/false_positives.jsonl` are marked `suppressed=True`.
7. **Sorting Order:** Severity descending $\to$ Confidence descending $\to$ Source line ascending.

---

## I. Fix & Verification Engine (`src/apsla/fixes/`)

- **Atomic Edits:** Each fix consists of a set of non-overlapping character range replacements.
- **Application Order:** Edits are sorted in reverse document order (end-to-start) before application to maintain character offset validity.
- **Conflict Avoidance:** Any fix containing overlapping ranges is rejected immediately.
- **Language-Aware Import Insertion:** If a fix requires a library (e.g., `import shlex` or `import html`), imports are placed cleanly at the top of the file following language conventions.
- **Fix-All Action:** Applies all non-conflicting `safe` + `verified` fixes across up to 3 passes. The transformation must be strictly idempotent: running Fix-All twice must produce the exact same text as running it once.

---

## J. HTTP API Contract (`/api`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status, active version, ML engine status (`on`/`off`), model hash |
| `GET` | `/api/languages` | List registered languages, file extensions, and capabilities |
| `POST` | `/api/analyze` | Full file analysis returning `AnalysisResult` |
| `POST` | `/api/fix` | Apply and verify a single fix |
| `POST` | `/api/fix-all` | Apply and verify all safe fixes iteratively |
| `POST` | `/api/feedback` | Record a false positive finding to local feedback storage |
| `GET` | `/api/samples` | Fetch bundled test snippets (vulnerable, safe, adversarial) |
| `POST` | `/api/ml/insights` | Per-token feature extraction and probability breakdown for explainability |
| `GET` | `/` | Serves the production React IDE frontend build |

---

## K. UI Design System — "SecureLex Night"

A distraction-free, high-contrast dark theme designed for security code review.

### Color Tokens
- **Background Root:** `#0B0F17`
- **Panel Background:** `#111826`
- **Raised Surfaces / Cards:** `#161E2E`
- **Borders & Dividers:** `#223049`
- **Primary Text:** `#E6EDF7`
- **Muted / Secondary Text:** `#8FA1BB`
- **Accent Blue:** `#4F8CFF`
- **Success / Verified:** `#3DDC97`

### Severity Color Hierarchy & Non-Color Redundancy
Severity is **never** communicated by color alone. Every badge pairs a color with a distinctive icon and explicit text label:
- **Critical:** `#FF4D6D` (Hexagon Alert + "CRITICAL")
- **High:** `#FF8A3D` (Shield Alert + "HIGH")
- **Medium:** `#F5C542` (Triangle Warning + "MEDIUM")
- **Low:** `#5CC8FF` (Circle Info + "LOW")
- **Info:** `#8FA1BB` (Info Icon + "INFO")

### Typography & Spacing
- **UI Font:** Inter (bundled via `@fontsource/inter`)
- **Code Font:** JetBrains Mono (bundled via `@fontsource/jetbrains-mono`)
- **Spacing Scale:** 4px, 8px, 12px, 16px, 24px, 32px
- **Border Radius:** 8px standard

### IDE Window Layout
```
+-----------------------------------------------------------------------------------------+
| [SecureLex IDE Logo]  [Language Select]  [Health Score: 88] [Fix All (3)]  [ML: ON pill] | 48px Header
+-------------------+---------------------------------------------+-----------------------+
| SAMPLES & FILES   | MONACO CODE EDITOR                          | FINDINGS PANEL        |
|                   |                                             |                       |
| - python/vuln1.py | 1 | name = request.args.get('q')            | [CRITICAL] APS-PY-001 |
| - python/safe1.py | 2 | os.system('echo ' + name) ~~~~~~~~~~~~  | Command Injection     |
| - java/vuln.java  | 3 |                                         | Taint: req -> system  |
|                   |                                             | [Apply Verified Fix]  |
| (240px)           |                                             | (380px)               |
+-------------------+---------------------------------------------+-----------------------+
| PROBLEMS & TAINT LOG (Terminal / Drawer)                                                | 160px Bottom
+-----------------------------------------------------------------------------------------+
| Ready | Python 3.12 | UTF-8 | UTF-16 Monaco Pos: Ln 2, Col 14 | Elapsed: 18ms          | 24px Status
+-----------------------------------------------------------------------------------------+
```

---

## L. Testing & Quality Assurance Architecture

- **Fixtures Directory:** `tests/fixtures/<lang>/{vulnerable, safe, adversarial}/NAME.ext` with corresponding `NAME.expect.json` declaring expected `(rule_id, line)`.
- **Rule Test Requirement:** Every registered rule must have at least one vulnerable test fixture and one safe counterpart fixture.
- **Property-Based Testing:** `hypothesis` tests validating that lexers never crash on arbitrary byte/character streams and that the fix engine remains idempotent.
- **Coverage Target:** Minimum 80% line coverage across `src/apsla/`.
- **Hermetic Tests:** The complete test suite (`pytest`) must pass without internet access, without a GPU, and without API keys.

---

## M. Engineering Standards

- **Type Annotations:** Exhaustive type hinting on all functions, methods, and public interfaces.
- **Linter & Formatter:** 100% clean check under `ruff check .` and `ruff format --check .`.
- **Documentation:** Every public class and function must include a clear docstring explaining *what* it does and *why*.
- **Standard Output Hygiene:** Zero `print()` statements in library code; all telemetry uses structured logging (`logging.getLogger("apsla.*")`).
- **Determinism:** Seed fixed to `42` across random generators and model runs.
- **CLI Utility:** All standalone scripts must provide `--help` and accept command-line arguments.

---

## N. Legacy Code Policy

1. `legacy/` is strictly **read-only**. No active production imports from `legacy/` are permitted in `src/apsla`.
2. **Senior Part 1 (secure_lexer_code-Part1):** Unlicensed university project. Algorithms and architectural concepts may be reimplemented cleanly; data files are copied only with recorded SHA-256 provenance.
3. **Senior Part 2 (AI-Powered-Secure-Lexical-Analyzer-main):** MIT Licensed ((c) 2026 Himanshu Sharma). Any adapted AST grammar patterns must include attribution: `"Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT)"`.

---

## O. Development Phases & Git Milestones

| Phase | Milestone Tag | Objective |
|---|---|---|
| **0** | `phase-0` | Repository reorganization, master specification, baseline probes, skeleton |
| **1** | `phase-1` | Unicode defense engine, confusable mapping, bidi detection |
| **2** | `phase-2` | Resilient Python lexer, Python security rules, AST taint flow analysis |
| **3** | `phase-3` | Fix generation and verification engine with idempotent Fix-All |
| **4** | `phase-4` | Feature extraction (45 dims), dataset pipeline, ML model training & calibration |
| **5** | `phase-5` | FastAPI service, schema serialization, telemetry, and health endpoints |
| **6** | `phase-6` | IDE Web Application (Vite + React + Monaco + SecureLex Night design) |
| **7** | `phase-7` | Java language plugin (Lexer, rules, taint-lite profile, fixes) |
| **8** | `phase-8` | JavaScript language plugin (Lexer, rules, taint-lite profile, fixes) |
| **9** | `phase-9` | C++ language plugin (Lexer, rules, taint-lite profile, fixes) |
| **10** | `phase-10` | Multi-language ML fine-tuning and cross-language evaluation |
| **11** | `phase-11` | Carbon emission measurements, throughput, and latency benchmarks |
| **12** | `phase-12` | Intelligence polish, active learning feedback loop, explainability |
| **13** | `v1.0` | Comprehensive test suite, packaging, documentation, viva preparation |
| **14** | `phase-14` | Privacy-preserving telemetry, offline guarantees, and sandbox hardening |
| **15** | `phase-15` | Local agentic compiler layer (lexical, syntax, semantic, triage, fix, verify, explain) |

---

## P. Global Agent Rules & Operating Protocol

1. Read `PROJECT_SPEC.md` and `docs/STATE.md` at the start of every session.
2. Execute **only** the scope of the current designated phase; do not write ahead.
3. Never edit files in `legacy/`.
4. Never commit `.env`, `node_modules`, `.venv`, or large model/dataset files exceeding limits.
5. Personally execute all acceptance validation commands and capture genuine terminal output into `reports/phase_N_evidence.md`. Never fabricate test metrics or probe outputs.
6. At the completion of each phase:
   - Update `docs/STATE.md`
   - Author `docs/explained/phaseN.md` (plain-English overview, concept glossary, and 5 viva questions with answers)
   - Commit phase milestone tag and cleanly stop.

---

## 20. Agentic layer

### Goals & Core Philosophy
SecureLex IDE embeds a modular agent at every stage of the compilation and security analysis pipeline:
1. **Lexical Stage (`LexerAgent`):** Inspects Unicode anomalies, lexer statistics, and dynamically re-lexes with error recovery or disambiguates ambiguous multi-language files.
2. **Syntax Stage (`ParserAgent`):** Builds lightweight recursive-descent structure trees (`StructTree`) for Java, JavaScript, and C++, recovering from syntax errors and computing structure quality scores.
3. **Semantic Stage (`SemanticAgent`):** Executes deterministic AST/token rules and runs normal taint analysis; conditionally activates targeted deep taint tracking only when tainted values reach unresolved calls.
4. **Triage Stage (`TriageAgent`):** Reviews findings in ambiguous confidence intervals ($[0.40, 0.60]$) to request targeted taint depth or flag items for human review; **strictly prohibited** from deleting, suppressing, or downgrading findings.
5. **Fix Generation Stage (`FixAgent`):** Ranks deterministic fix candidates (safe > review > manual); if no candidate exists and local LLM is enabled, generates a single alternative edit proposal (kind `llm`).
6. **Verification Stage (`VerifierAgent`):** Isolates proposed fixes in memory copies, verifies syntax and security elimination via `verify_fix`, and loops with `FixAgent` up to 3 attempts. Only deterministic verification sets `verified = True`.
7. **Explanation Stage (`ExplainAgent`):** Generates structured plain-English guidance and applies strict token grounding verification against finding facts if LLM rephrasing is enabled.
8. **Orchestrator (`Orchestrator`):** Coordinates sequential execution, enforces global step/LLM/timeout budgets, maintains immutable audit traces, and provides safe fallback to deterministic outputs.

### Local-Only & Zero-Trust Constraints
- **Strictly Local:** Powered exclusively by local Ollama instances (e.g., `qwen2.5-coder:3b` at `http://127.0.0.1:11434` or `localhost`). Remote hosts, external cloud APIs, and runtime internet connections are strictly prohibited ("outbound network calls: 0").
- **Deterministic Authority:** Agents never replace compiler and analyzer engines; they only observe analysis state and choose tools from an explicit 14-tool allowlist.
- **Robust Prompt-Injection Defense:** Untrusted source code is framed as data between fixed delimiters with line and character limits; LLM outputs are restricted to strict JSON schemas; agent planners cannot delete findings or bypass the fix verifier.
