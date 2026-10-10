# Agentic Compiler Architecture Map (Phase 15)

SecureLex IDE integrates deterministic compiler tools with an agentic orchestration layer. Local agents act strictly as navigators choosing which deterministic compiler tool to invoke next, while the underlying parsers, rule engines, and verifiers remain the sole authoritative source of truth.

## Compiler Stage to Agent Mapping

| Stage | Compiler Concept | Agent | Allowed Tools | Value Added Beyond Fixed Pipeline | Invariant Constraints (What It Cannot Do) |
|---|---|---|---|---|---|
| **1. Lexical** | Tokenization, Lexical Analysis, Encoding | `LexerAgent` | `unicode_scan`, `lex_stats`, `relex_with_recovery`, `detect_language_candidates` | Dynamically triggers token stream recovery when BiDi/confusables/invisible chars or high error token ratios (>2%) are detected; evaluates multi-language candidates to minimize error rates. | Cannot forge tokens, edit raw source, suppress lexical diagnostics, or access the file system. |
| **2. Syntax** | Abstract Structure & Error Recovery | `ParserAgent` | `parse_structure` | Invokes hand-written recursive descent structure parsers with panic-mode recovery; computes structure quality score and pinpoints broken syntax blocks. | Cannot alter grammar rules, execute code, or bypass syntax errors. |
| **3. Semantic** | Data-Flow, Taint Propagation, Rules | `SemanticAgent` | `run_rules`, `run_taint` | Selectively triggers computationally expensive deep taint analysis with targeted sinks only when unresolved calls or partial flows exist, saving runtime on simple cases. | Cannot invent taint sources/sinks, fabricate flow paths, or execute analyzed code. |
| **4. Triage** | Confidence Scoring & Triage Decision | `TriageAgent` | `ml_score` | Inspects borderline findings (confidence between 0.40 and 0.60) to escalate for deep taint verification or tag for human security review. | **NEVER** deletes, suppresses, or downgrades findings. All deterministic findings are preserved. |
| **5. Fix** | Code Transformation & Synthesis | `FixAgent` | `list_fix_candidates` | Ranks available fixes by safety (`safe` > `review` > `manual`) and minimal edit distance; synthesizes atomic candidate fixes when none exist. | Cannot apply fixes directly to source or mark fixes as verified. |
| **6. Verify** | Formal Equivalence & Regression Check | `VerifierAgent` | `apply_fix_to_copy`, `verify_fix`, `rescan_copy` | Evaluates candidate fixes in isolated in-memory buffer copies; validates syntax and verifies vulnerability elimination up to 3 attempts. | **ONLY** the deterministic `verify_fix` tool can set `verified=true`. No model or agent prompt can assert verification. |
| **7. Explain** | Grounding & Remediation Reporting | `ExplainAgent` | `build_explanation` | Synthesizes plain-English explanations with strict factual grounding checks (validates identifiers, line numbers, and CWEs against finding). | Hallucinated rewrites failing grounding checks are discarded in favor of deterministic templates. |

---

## Orchestrator Loop Architecture

```mermaid
flowchart TD
    Start([Start Analysis Session]) --> Init[Initialize In-Memory Session<br/>Source, Language, Budget: 12 Steps / 8 LLM Calls]
    Init --> CheckBudget{Budget / Timeout Exceeded?}
    CheckBudget -- Yes --> Baseline[Fallback to Deterministic Pipeline Findings]
    CheckBudget -- No --> S1[1. Lexical Stage<br/>LexerAgent]
    
    S1 --> S2[2. Syntax Stage<br/>ParserAgent]
    S2 --> S3[3. Semantic Stage<br/>SemanticAgent]
    S3 --> S4[4. Triage Stage<br/>TriageAgent]
    S4 --> S5[5. Fix Stage<br/>FixAgent]
    S5 --> S6[6. Verifier Stage<br/>VerifierAgent]
    S6 --> S7[7. Explain Stage<br/>ExplainAgent]
    
    subgraph AgentStepLoop [Single Agent Observe-Decide-Act Loop]
        Observe[Observe Session State] --> Planner{Planner Selection}
        Planner -- Rules Mode / Fallback --> RulesPlanner[RulesPlanner<br/>Deterministic If/Else Policy]
        Planner -- Local Mode --> LLMPlanner[LLMPlanner<br/>Local Ollama qwen2.5-coder:3b]
        LLMPlanner --> Guard[Security Guard & Schema Validator]
        Guard -- Valid Action & Args --> ExecTool[Execute Allowed Tool]
        Guard -- Invalid Action / Injection --> FallbackAction[Reject & Fallback to Rules Action]
        RulesPlanner --> ExecTool
        FallbackAction --> ExecTool
        ExecTool --> Trace[Record Step Trace<br/>Stage, Reason, Action, Decision Source]
    end

    S7 --> Finish[Tool: finish()]
    Finish --> Output([Final AnalysisResult<br/>Verified Findings + Trace Timeline])
    Baseline --> Output
```

---

## Invariant Guarantees

1. **Findings Superset-or-Equal**: Agentic results never drop, suppress, or delete findings produced by deterministic rules (`Findings_agentic >= Findings_deterministic`).
2. **Deterministic Baseline**: In `off` mode, output is bit-for-bit identical to Phase 14. In `rules` mode, execution is completely deterministic and reproducible.
3. **Loopback Isolation**: The local model provider strictly allows only `127.0.0.1`, `localhost`, or `::1`. Outbound network calls = 0.
4. **Verification Authority**: Verification status is solely produced by running the deterministic parser and re-scanner against the modified AST. No LLM generation can assert a fix as verified.
