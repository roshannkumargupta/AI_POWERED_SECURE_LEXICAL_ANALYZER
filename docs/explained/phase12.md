# Phase 12 Explained: Human-in-the-Loop Feedback, Hard Negatives, Verified LLM Assistance, and Risk-Weighted Prioritization

---

## 1. Executive Summary & Plain-English Overview

Phase 12 transforms SecureLex IDE (`apsla`) from a static rule scanner into an **intelligent pair-programming security assistant**. Rather than emitting static, unranked lists of warnings, SecureLex IDE now:
1. **Learns from Human-in-the-Loop Feedback:** Developers report false positives directly from the IDE. The system records them in an append-only ledger (`data/feedback/false_positives.jsonl`) and converts them into **hard-negative SAFE-labelled training windows** during offline retraining.
2. **Enforces a Rigorous Safety Gate:** Retrained models must improve or maintain validation metrics and external benchmark accuracy (`evaluate_external_benchmarks`). If external performance regresses, the retraining pipeline strictly refuses to replace production model artifacts.
3. **Prioritizes Real Risk over Raw Counts:** Findings are ranked using a multi-factor formula:
   $$\text{Priority} = \text{Severity Weight} \times \text{Confidence} \times \text{Exploitability}$$
   Exploitability accounts for data-flow taint confirmation ($1.0$), dangerous sinks without verified taint ($0.7$), weak cryptographic/config errors ($0.5$), and informational notices ($0.3$). Top 3 findings receive a prominent `⚡ Fix first` badge.
4. **Delivers Concrete Explanations & Rules Catalogue:** Every rule provides plain-English explanations answering: *What is this? Why is it dangerous? How can an attacker exploit it? How to fix it?* Concrete variable names and source lines are dynamically resolved. Users can toggle between **Simple** (1-sentence summary) and **Detailed** (full structured guidance) modes in the UI.
5. **Supports Inline Suppression Comments:** Standardized comments (`# securelex: ignore <RULE_ID>` for Python, `// securelex: ignore <RULE_ID>` for Java, JS, and C++) allow surgical silencing on the same or immediately preceding line. A one-click code action applies undoable workspace edits in the editor.
6. **Integrates Guarded, Shadow-Verified LLM Fix Generation:** Developers can optionally enable state-of-the-art LLMs (Claude via Anthropic, Gemini via Google, or any OpenAI-compatible API). LLMs are **strictly opt-in, offline by default, and isolated from telemetry**. Crucially, every LLM-proposed code fix must pass the **exact same AST/lexical/rule verification engine** as built-in fixes. If an LLM hallucination breaks code syntax or leaves vulnerabilities intact, it is automatically downgraded to non-executable "advice only".

---

## 2. Deep Dive: Architectural Innovations

### A. Human-in-the-Loop Active Learning & Hard Negatives (`feedback/` & `scripts/retrain_with_feedback.py`)

#### 1. Feedback Ledger Schema
When a user flags a false positive in the UI Problems or Finding tab, the backend appends an immutable record to `data/feedback/false_positives.jsonl` (git-ignored to protect proprietary codebases):
```json
{
  "timestamp": "2026-10-09T19:02:23.056137+00:00",
  "language": "python",
  "rule_id": "APS-PY-INJ-001",
  "fingerprint": "APS-PY-INJ-001:5:os.system",
  "snippet": "os.system(safe_command_list[0])",
  "verdict": "false_positive",
  "note": "Validated via internal whitelist",
  "filename": "service.py",
  "line": 5
}
```

#### 2. The Science of Hard Negatives
In machine learning for code analysis, general benign code examples are plentiful (e.g. `x = 1`, `return True`). However, **hard negatives** are tokens that appear in high-risk contexts (such as calls to `system`, `execute`, or `eval`) that the human expert has certified as **benign or safe** under business logic.
- During retraining, `scripts/retrain_with_feedback.py` extracts 9-token sliding windows centered on the tokens overlapping the reported finding range.
- These windows are explicitly assigned the ground-truth label **`SAFE` (0)**.
- **Strict Data Partitioning Rule:** Feedback-derived windows are incorporated strictly into the **TRAIN** split. They are **never** injected into the validation set or the test set. Injecting feedback into validation/test splits would cause severe distribution leakage and artificially inflate evaluation metrics.

#### 3. Safety Gate & Model Replacement Policy
Active learning runs the risk of *catastrophic forgetting* or *over-suppression*, where a model trained on false positives learns to ignore genuine vulnerabilities. To prevent this, `retrain_with_feedback.py` enforces a two-stage evaluation:
1. Retrains baseline and augmented models across identical cross-validation splits.
2. Evaluates macro-F1, precision, and recall on the held-out validation set and on external hand-written benchmark suites (`evaluate_external_benchmarks`).
3. **Safety Gate:** If `augmented_ext_f1 < baseline_ext_f1 - 0.005`, the script prints an explicit refusal reason and aborts without overwriting the production artifact in `src/apsla/ml/artifacts/`:
   ```
   [SAFETY GATE ACTIVATED] External benchmark F1 degraded from 0.8842 to 0.8120.
   Refusing to replace production model artifact to protect detection recall.
   ```
4. Full before vs. after metrics are formatted into `reports/phase_12_evidence.md`.

---

### B. Multi-Factor Risk Prioritization (`apsla/prioritization.py`)

Traditional SAST tools overwhelm developers with flat lists of hundreds of warnings, creating alert fatigue. SecureLex IDE prioritizes findings based on real operational risk:

$$\text{Priority} = w_{\text{severity}} \times c_{\text{finding}} \times E_{\text{exploitability}}$$

Where:
- $w_{\text{severity}} \in \{1.0 \text{ (CRITICAL)}, 0.8 \text{ (HIGH)}, 0.5 \text{ (MEDIUM)}, 0.2 \text{ (LOW)}, 0.05 \text{ (INFO)}\}$ (defined in `config.py`)
- $c_{\text{finding}} \in [0.1, 1.0]$: Fused confidence score combining rule confidence, AST taint confirmation bonus ($+0.2$), and calibrated ML probabilities.
- $E_{\text{exploitability}}$:
  - **$1.0$ (Taint Confirmed):** Data flow path successfully traced from untrusted source to dangerous sink.
  - **$0.7$ (Dangerous Sink):** Vulnerable sink invoked, but static data flow path is unconfirmed or truncated.
  - **$0.5$ (Weak Crypto / Config):** Insecure algorithms (MD5, DES) or hardcoded credentials.
  - **$0.3$ (Informational / Code Quality):** Low-risk stylistic or debug notices.

Findings are sorted primarily by **Priority (descending)**. In the UI Problems table and right-pane drawer, the top 3 highest-priority findings are highlighted with a distinct `⚡ Fix first` badge, immediately guiding developer remediation to the most critical threats.

---

### C. Plain-English Concrete Explanations & Rules Catalogue (`apsla/rules/explanations.py`)

Every security finding in SecureLex IDE is backed by an educational, structured explanation template containing four required sections:
1. **What:** Precise technical classification of the pattern.
2. **Why It Is Dangerous:** Architectural impact (confidentiality, integrity, availability).
3. **How an Attacker Uses It:** Concrete exploitation vector or payload.
4. **How to Fix:** Recommended parameterized, hashed, or sanitized alternative.

#### Concrete Dynamic Interpolation
Generic templates are instantiated with concrete variable, function, and line identifiers:
- *Template:* `Line {sink_line} passes \`{var_name}\`, which comes from untrusted input on line {source_line}, into \`{sink_func}\`.`
- *Rendered:* `Line 20 passes \`name\`, which comes from request.args on line 17, into \`db.execute\`.`

#### Simple vs. Detailed Toggle
The IDE Finding tab provides an instant in-memory toggle:
- **Simple Mode:** A single concise sentence explaining the immediate hazard for fast skimming.
- **Detailed Mode:** Comprehensive multi-section tutorial with threat mechanics and best practices.

The rules engine also auto-generates `docs/rules_catalogue.md` directly from rule registries, ensuring documentation remains 100% synchronized with detection implementations.

---

### D. Inline Suppression Comments (`apsla/suppression.py`)

SecureLex IDE recognizes standard suppression comments across all four supported languages:
- **Python:** `# securelex: ignore <RULE_ID>`
- **Java / JavaScript / C++:** `// securelex: ignore <RULE_ID>`
- **Multiple Rules:** `# securelex: ignore APS-PY-INJ-001, APS-PY-INJ-002`

#### Rules of Precedence & Scoping
- The suppression comment can appear on the **same line** as the flagged code or on the **immediately preceding line** (ignoring blank lines).
- When detected, the finding is marked `suppressed = True` with `suppression_reason = "suppressed in code"`.
- The IDE provides a one-click QuickFix code action and a "Suppress this finding" button in the Finding tab that inserts the comment as a single undoable workspace edit (`Ctrl+Z`).

---

### E. Guarded LLM Assistant with Shadow Verification (`apsla/llm/`)

#### 1. Architecture & Provider Abstraction
```
                  ┌──────────────────────┐
                  │    User Requests     │
                  │   "Ask AI for Fix"   │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Provider Interface   │
                  │   (llm/provider.py)  │
                  └──────────┬───────────┘
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│AnthropicProvider│ │ GeminiProvider  │ │ OpenAICompat    │
│(Claude 3.5 Son.)│ │(Gemini 1.5 Pro) │ │(OpenAI/vLLM)    │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         └───────────────────┼───────────────────┘
                             │ Returns candidate Fix
                             ▼
                  ┌──────────────────────┐
                  │  Shadow Verification │
                  │  (apsla.fixes.verify)│
                  │                      │
                  │ 1. Syntax check      │
                  │ 2. Finding removed   │
                  │ 3. No new findings   │
                  └──────────┬───────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
           Passed verification     Failed verification
                 │                       │
                 ▼                       ▼
         ┌───────────────┐       ┌───────────────┐
         │ Kind: "llm"   │       │ Confidence:   │
         │ Verified Safe │       │ "manual"      │
         │ Executable Fix│       │ Advice Only   │
         └───────────────┘       └───────────────┘
```

#### 2. Strict Zero-Trust Security & Privacy Principles
1. **Offline & Disabled by Default:** If no API key is set in the environment, the system instantiates `NullLLMProvider`, completely disabling network communication. The UI "Ask AI for another fix" button is dimmed and disabled with an explanatory tooltip.
2. **Context Minimization:** Only a 200-line slice centered around the finding range is sent to the LLM. Whole repositories are never uploaded.
3. **Privacy Transparency:** Code is transmitted to external providers **only** when the user explicitly clicks "Ask AI for another fix".
4. **Credential Isolation:** Keys (`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`) are read strictly from local `.env`. Keys are never logged, never exposed via REST API, and never sent to the frontend.
5. **Enforced Timeouts:** All HTTP requests via `httpx` are capped at a strict 15-second timeout.

#### 3. Mandatory Shadow Verification
LLMs are notorious for plausible-sounding hallucinations—generating syntactically invalid code, introducing secondary vulnerabilities, or altering unrelated business logic. SecureLex IDE mandates that **every LLM-generated fix undergoes the exact same multi-stage verification pipeline as deterministic rule fixes**:
- **Stage 1 (Syntax Check):** The patched code is parsed with the language's native parser. If syntax errors occur, the fix is immediately rejected.
- **Stage 2 (Vulnerability Elimination):** The patched code is analyzed again. If the target finding persists, verification fails.
- **Stage 3 (Regression Check):** Analysis ensures no new security findings of equal or higher severity were introduced.
- **Enforcement:** If verification fails, the fix is downgraded from an executable QuickFix to `confidence = "manual"`, labeled as experimental advice, and prevented from being applied via "Fix all".

---

## 3. Concept Glossary

- **Hard Negative:** A training sample that closely resembles known malicious patterns in token composition or API usage, but is certified as benign by human expertise.
- **Active Learning:** A machine learning paradigm where the algorithm queries human experts to label ambiguous or misclassified instances, iteratively expanding the training distribution.
- **Shadow Verification:** Executing deterministic semantic and syntactic tests on non-deterministic model outputs prior to presenting them to the user.
- **Exploitability Factor:** A scalar modifier ($E \in [0.3, 1.0]$) reflecting the technical feasibility of exploiting a vulnerability based on taint reachability and sink danger.
- **Inline Suppression:** Silencing specific security warnings directly in source code comments using scoped, deterministic rule identifiers.
- **Alert Fatigue:** The psychological phenomenon where security engineers and developers begin ignoring tool warnings due to high volumes of unranked or false-positive alarms.

---

## 4. Viva Voce Q&A (Phase 12: Human-in-the-Loop & Intelligent Assistance)

### Q1: Why must false positive feedback data be incorporated exclusively into the training split and NEVER into the validation or test splits during active learning retraining?
**Answer:**  
In machine learning, validation and test sets must accurately represent the unbiased, natural distribution of real-world code to evaluate model generalization.  
False positive feedback is highly concentrated and biased—it consists exclusively of anomalous, corner-case patterns that human developers manually reviewed and flagged. If these specific feedback instances were leaked into the validation or test partitions, the model would be evaluated on the very samples it was explicitly corrected on. This would artificially inflate accuracy and F1 metrics (optimism bias) while masking potential degradation on broader, unseen codebases. Restricting feedback strictly to the training partition ensures that validation and external test sets remain uncontaminated benchmarks.

### Q2: Why is it dangerous to accept LLM-generated security fixes directly without deterministic shadow verification?
**Answer:**  
Large Language Models generate text based on statistical token likelihoods rather than formal program semantics. Consequently, LLM fixes exhibit three critical failure modes:
1. **Syntactic Hallucinations:** Introducing unbalanced brackets, invalid imports, or deprecated API signatures that fail compilation or cause runtime crashes.
2. **Incomplete Remediation:** Modifying the code cosmetically (e.g., renaming a variable) while leaving the underlying tainted data-flow path intact.
3. **Secondary Vulnerabilities (Regressions):** Replacing one vulnerability with another (e.g., fixing SQL injection by string-formatting into another unescaped function, or disabling TLS verification).  

SecureLex IDE treats LLMs as untrusted proposal generators. By running every candidate fix through `verify_fix()`—which compiles the code with native parsers, re-runs static analysis, and checks for new findings—the system guarantees that no broken or insecure code is ever applied automatically.

### Q3: Explain the multi-factor prioritization formula ($Priority = Severity \times Confidence \times Exploitability$) and why a CRITICAL finding might have a lower priority than a HIGH finding.
**Answer:**  
Raw severity only measures the theoretical maximum impact of a vulnerability if successfully exploited; it ignores the likelihood and feasibility of exploitation. In SecureLex IDE:
- A CRITICAL finding (e.g. Remote Code Execution via `os.system`) where data flow cannot confirm untrusted input reachability has $Exploitability = 0.7$. If rule confidence is $0.6$, its priority is:
  $$Priority = 1.0 \times 0.6 \times 0.7 = 0.42$$
- Conversely, a HIGH finding (e.g. SQL Injection via `db.execute`) where taint analysis confirms reachability from `request.args` has $Exploitability = 1.0$ and confidence $0.9$ (boosted by taint confirmation). Its priority is:
  $$Priority = 0.8 \times 0.9 \times 1.0 = 0.72$$

Because $0.72 > 0.42$, the confirmed SQL injection is prioritized ahead of the unconfirmed command execution. This directs developer focus to verified, actively exploitable risks first.

### Q4: How does the retraining safety gate prevent active learning feedback from causing catastrophic forgetting?
**Answer:**  
When a token classifier is retrained on false positive examples labeled as `SAFE`, the optimizer shifts decision boundaries away from flagging those token sequences. If over-optimized, the model may inadvertently lower its sensitivity to genuine vulnerabilities that share subtle lexical features with the false positive.  
To prevent this, `scripts/retrain_with_feedback.py` enforces an automated **Safety Gate**:
1. It runs both the baseline model and the retrained model against the held-out validation set and the external hand-written benchmark suite (`evaluate_external_benchmarks`).
2. If the external benchmark F1 score drops by more than $0.005$ ($\Delta F1 < -0.005$), the script detects generalization regression.
3. The script prints a detailed explanation and exits with a non-zero code, strictly refusing to overwrite the active model artifact in `src/apsla/ml/artifacts/`.

### Q5: What is the purpose of scoping suppression comments to both the same line and the immediately preceding line, and how is it implemented without degrading analysis speed?
**Answer:**  
In different programming styles and formatting guidelines (e.g., PEP 8, Google Java Style), developers place suppression comments in two ways:
- **Same line:** E.g., `os.system(cmd)  # securelex: ignore APS-PY-INJ-002` (common for concise lines).
- **Previous line:** E.g., `# securelex: ignore APS-PY-INJ-002` placed immediately above a long or multi-line function call to avoid exceeding line-length limits (80/120 characters).  

To support both without performance overhead, `src/apsla/suppression.py` performs a single linear scan over lines using compiled regular expressions (`#\s*securelex:\s*ignore\s+([\w\s,-]+)` and `//\s*securelex:\s*ignore\s+([\w\s,-]+)`). It builds a map from `line_number` to set of suppressed `rule_ids`. During finding filtering, for each finding at line $L$, it checks whether `rule_id` is present in `suppressed_at(L)` or `suppressed_at(L - 1)`. This $O(N)$ pass executes in sub-millisecond time and requires no AST manipulation.
