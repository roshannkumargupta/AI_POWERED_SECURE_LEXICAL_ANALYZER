# SL2-0 to SL2-10 Plan

Recommended order: **SL2-0, SL2-1, SL2-2, SL2-8a, SL2-3, SL2-4, SL2-5, SL2-6, SL2-7, SL2-8b, SL2-9, SL2-10.** SL2-0 is this audit phase; it is listed first for traceability. Restore `docs/product_spec_v2.md` before treating any requirement-specific acceptance as final.

| Phase | Scope | Dependencies | Acceptance |
|---|---|---|---|
| SL2-1 | Restore spec traceability; lock Part 7.4 wording, API contract and core service boundary; reconcile audit conflicts | SL2-0 and authoritative product spec | Every spec requirement mapped to evidence/test/work; decisions approved by product spec alignment; contracts recorded. |
| SL2-2 | Backend API compatibility, new spec endpoints and deprecated aliases; truthful status/error contracts | SL2-1 | OpenAPI and request/response tests cover old and new routes; golden contract changes reviewed; no false statuses. |
| SL2-8a | Prototype shell/workbench migration: dense VS Code layout, 13 px base, offline assets, existing workspace/reducer/manual analysis/QA reuse | SL2-1, UI-9 baseline | Browser evidence at target viewports; no CDN requests; light and dark coverage; existing editing and manual analysis preserved. |
| SL2-3 | Configurable local and OpenAI-compatible model provider, consent boundary, visible processing location | SL2-1, SL2-2 | Offline default tested; provider status truthful; explicit consent tested before any source transmission. |
| SL2-4 | Agent roles and tool registry alignment with product spec; trace/provenance behavior | SL2-1, current Phase 15 | Deterministic mode and model mode separated; allowlist/security tests pass; trace maps to roles. |
| SL2-5 | External analyzer adapter interfaces and optional integrations | SL2-1, SL2-2 | Internal engine remains default/core; unavailable adapter states tested; subprocess limits enforced. |
| SL2-6 | Analysis engine/rules/taint/fix behavior gaps identified by the completed spec matrix | SL2-1, SL2-2 | Requirement-specific regression/golden tests pass with real sample evidence. |
| SL2-7 | Fix workflow, independent verifier, review state and safety lab deterministic harness | SL2-1, SL2-4, SL2-6 | Deterministic harness never mixes with live model; no preloaded outcomes; verification evidence is reproducible. |
| SL2-8b | Complete workbench interactions, diagnostics and usability gaps after shell and engine integration | SL2-8a, SL2-2, SL2-6 | Full manual-analysis, token, finding, fix, settings, theme and keyboard acceptance matrix passes. |
| SL2-9 | Hardening, privacy, accessibility, offline behavior and full system QA | SL2-2 through SL2-8b | Security/regression suites, both themes, offline audit and real evidence report pass. |
| SL2-10 | Final migration/deprecation cleanup, docs and release certification | SL2-9 | Alias deprecation removed only with migration coverage; all spec rows pass or have explicit accepted disposition; final tag and state accurate. |

Phase scopes are provisional where spec parts are unavailable; SL2-1 must refine them from the exact source requirements.
