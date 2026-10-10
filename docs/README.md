# SecureLex IDE Documentation Index

Welcome to the SecureLex IDE (`apsla`) technical documentation. This directory provides detailed specifications, architectural blueprints, rule definitions, and phase retrospectives for the platform.

---

## 1. Architecture & Core Systems

- **[System Architecture](architecture.md)**: Layered design of lexical analysis, syntactic parsing, semantic AST extraction, taint flow tracking, and ML fusion.
- **[Threat Model](threat_model.md)**: Security boundary analysis, threat vectors, untrusted input containment, and Trojan Source defenses.
- **[Rules Catalogue](rules_catalogue.md)**: Complete catalog of deterministic security rules across Python, Java, JavaScript, and C++ with CWE classifications.
- **[Agentic Compiler Map](agentic_map.md)**: Phase 15 multi-agent compiler orchestration, deterministic tool boundaries, and local Ollama planner integration.
- **[Design Rules](design_rules.md)**: Architectural invariants, zero-external-dependency constraints, and cross-platform guarantees.
- **[System Limitations](limitations.md)**: Explicit operational boundaries, resource caps, and unsupported edge cases.

---

## 2. API & Integration

- **[REST API Specification](api.md)**: Endpoints, OpenAPI schemas, request/response models, and error structures.
- **[API Request/Response Samples](api_samples/)**: Raw payload examples for automated ingestion and tooling integration.

---

## 3. UI, Frontend & Testing Protocol

- **[User Guide](user_guide.md)**: Desktop-style web IDE walkthrough, keyboard shortcuts, panel navigation, and diff views.
- **[Samples Guide](samples_guide.md)**: Guide to included vulnerability and safe coding test files across all supported languages.
- **[UI QA Protocol](ui_qa_protocol.md)**: Rigorous QA testing protocol covering theme contrast, layout resilience, and event isolation.
- **[UI QA Checklist](ui_qa_checklist.md)**: Checkpoint list for visual, keyboard, and functional verification.
- **[UI Bug Audit](ui_bug_audit.md)**: Root cause analysis and fixes for historical interface defects.
- **[Token Security Data Model](token_security_data.md)**: Security scoring and token-level attribute models.
- **[Demo Script](demo_script.md)** & **[Demo Walkthrough Path](demo_path.md)**: Step-by-step presentation pathways for live evaluation.

---

## 4. Phase Retrospectives & Technical Notes

Detailed phase explanations are located in the [`explained/`](explained/) directory:

| Phase Track | Focus Area | Documentation |
|---|---|---|
| **Phase 0–3** | Foundation, Tokenizer, AST & Rules | [Phase 0](explained/phase0.md), [Phase 1](explained/phase1.md), [Phase 2](explained/phase2.md), [Phase 3](explained/phase3.md) |
| **Phase 4–6** | Taint Engine, CFG, Multi-Language | [Phase 4](explained/phase4.md), [Phase 5](explained/phase5.md), [Phase 6](explained/phase6.md) |
| **Phase 8–10** | Unicode Defense, ML Scoring & Calibration | [Phase 8](explained/phase8.md), [Phase 9](explained/phase9.md), [Phase 10](explained/phase10.md) |
| **Phase 12–15** | Prioritization, Fix Engine, Agentic Loop | [Phase 12](explained/phase12.md), [Phase 15](explained/phase15.md) |
| **UI 1–9** | Desktop UI, Monaco Integration, Themes, Guards | [UI 1–9 Explanations](explained/) |
| **Samples** | Benchmark Catalogue | [Samples Matrix](explained/samples.md), [Phase S1](explained/phaseS1.md) |

---

## 5. Repository Cleanup & Safety Registers

Registers and evidence generated during repository hygiene (CLEAN-1 & CLEAN-2):

- **[Repository Inventory](cleanup/inventory.md)**: Depth-3 folder tree and component purpose index.
- **[Dead Code Candidates](cleanup/dead_code_candidates.md)**: Audit of unreferenced symbols and justification for dynamic preservation.
- **[Architectural Decisions](cleanup/needs_decision.md)**: Decisions on retained components, datasets, and dependencies.
- **[Deleted Files Register](cleanup/deleted_files.md)**: Traceable record of verified obsolete files removed.
- **[Skipped Items Register](cleanup/skipped.md)**: Intentionally preserved legacy, ML weights, and benchmark corpora.

---

## 6. Project State Tracker

- **[Master State Tracker](STATE.md)**: Authoritative phase progress, pass criteria, commit hashes, and verification milestones.
