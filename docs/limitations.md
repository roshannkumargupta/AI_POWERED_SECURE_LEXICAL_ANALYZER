# Operational Limitations & Design Trade-offs (Phase 15)

## 1. Local Model Quality and Reasoning Depth
- **Small Parameter Size (3B)**: By default, SecureLex IDE integrates `qwen2.5-coder:3b` to operate efficiently on developer workstations with limited memory (such as 8 GB RAM machines) without requiring dedicated discrete GPUs.
- **Weaker Strategic Planning**: While 3B code models excel at syntactic pattern matching and concise tool choice, they occasionally generate sub-optimal step sequences, propose irrelevant argument combinations, or hallucinate fix syntax compared to larger cloud models (e.g., 70B+ parameter models).
- **Compensating Architecture**: SecureLex IDE does not treat model outputs as authoritative. Any invalid tool invocation, schema mismatch, or out-of-vocabulary action is immediately rejected and redirected to the deterministic `RulesPlanner`. Grounding checks discard any explanation with hallucinated details.

---

## 2. Latency and Performance Overhead
- **Multi-Step Execution Overhead**: The deterministic baseline pipeline (Phase 14) executes in 5–25 milliseconds per file. Invoking the agentic layer in `rules` mode introduces a small overhead (5–20 ms) due to multi-stage observation and isolated fix verification.
- **Local LLM Inference Latency**: When running in `local` AI mode, each model prompt to Ollama takes between 200 ms and 2,500 ms depending on CPU/GPU capabilities. A typical 3-step LLM-guided triage and fix cycle adds 1–5 seconds per file.
- **Strict Budget Guards**: To prevent unbounded lag, analysis sessions enforce strict budgets:
  - Global wall-clock timeout: 60 seconds.
  - Per-analysis step limit: 12 steps.
  - Per-analysis LLM call limit: 8 calls.

---

## 3. The LLM Planner is Entirely Optional
- **Zero-Dependency Baseline**: SecureLex IDE functions completely offline without any local LLM installed or running.
- **RulesPlanner Always Available**: In `off` mode, the deterministic compiler pipeline operates identically to Phase 14. In `rules` mode, the deterministic rule-based planner executes the full agentic stage lifecycle with zero neural network inference overhead and 100% deterministic reproducibility.
- **Offline / Air-Gapped Environments**: Secure environments without Ollama can operate permanently in `rules` mode with complete feature availability across all 7 compiler stages.

---

## 4. Parser Scope and Grammar Approximations
- **Lightweight Structure Parser**: Hand-written recursive descent parsers for Java, JavaScript, and C++ focus on scoping and structural units (classes, functions, calls, returns). They intentionally omit full language grammar complexities such as C++ template metaprogramming, C preprocessor macro expansions, complex type inference, and dynamic evaluation semantics.
- **Panic-Mode Synchronization**: On malformed inputs, parsers synchronize on delimiters (`;`, `}`, `)`); highly truncated or heavily corrupted snippets may produce approximate AST structures.
