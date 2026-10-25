# SecureLex IDE Technical Documentation

Welcome to the SecureLex IDE (`apsla`) technical documentation. This directory provides detailed specifications, architectural blueprints, rule definitions, and usage guides for the platform.

---

## 1. Architecture & Core Systems

- **[System Architecture](architecture.md)**: Layered design of lexical analysis, syntactic parsing, semantic AST extraction, taint flow tracking, and ML fusion.
- **[Threat Model](threat_model.md)**: Security boundary analysis, threat vectors, untrusted input containment, and Trojan Source defenses.
- **[Rules Catalogue](rules_catalogue.md)**: Complete catalog of deterministic security rules across Python, Java, JavaScript, and C++ with CWE classifications.
- **[Adding a Rule](adding_a_rule.md)**: Developer guide and workflow for implementing, testing, and registering new static security rules.
- **[Agentic Compiler Map](agentic_map.md)**: Multi-agent compiler orchestration, deterministic tool boundaries, and AI planner integration.
- **[Design Rules](design_rules.md)**: Architectural invariants, zero-external-dependency constraints, and cross-platform guarantees.
- **[System Limitations](limitations.md)**: Explicit operational boundaries, resource caps, and unsupported edge cases.

---

## 2. API & Integration

- **[REST API Specification](api.md)**: Endpoints, OpenAPI schemas, request/response models, and error structures.
- **[API v2 Specification](api_v2.md)**: Versioned API contracts, diagnostic models, and stage-by-stage pipelines.
- **[API Request/Response Samples](api_samples/)**: Raw payload examples for automated ingestion and tooling integration.

---

## 3. UI & Developer Guides

- **[User Guide](user_guide.md)**: Web IDE walkthrough, keyboard shortcuts, panel navigation, and diff views.
- **[Safety Lab Guide](safety_lab.md)**: Security scenario evaluation harness, adversarial attack matrix, and verification reporting.
- **[Samples Guide](samples_guide.md)**: Guide to included vulnerability and safe coding test files across all supported languages.
- **[Lexer Conformance](lexer_conformance.md)**: Conformance specifications and language token mappings.
- **[Token Types](token_types.md)**: Token classification, categories, and severity mappings.
- **[Token Security Data Model](token_security_data.md)**: Security scoring and token-level attribute models.
- **[Security Adapter Mappings](security_adapter_mappings.md)**: Integration adapters for external tools and diagnostic normalizers.
- **[Product Specification v2](product_spec_v2.md)**: Core requirements, workbench workflows, and system constraints.
- **[Demo Script](demo_script.md)** & **[Demo Walkthrough Path](demo_path.md)**: Step-by-step presentation pathways for live evaluation.
