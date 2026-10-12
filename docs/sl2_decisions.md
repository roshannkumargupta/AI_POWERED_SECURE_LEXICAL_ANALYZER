# SL2-0 Product v2 Decisions

These are the proposed defaults supplied for SL2-0. They become implementation constraints for later SL2 phases after the missing product spec is restored and conflicts are reconciled.

| ID | Options considered | Choice | Reason |
|---|---|---|---|
| D1 | Keep fluid-scale mockup / adopt prototype layout | Adopt prototype VS Code layout; retire the 2x fluid-scale mockup; retain theme tokens, workspace reducer, manual analysis and adapted QA tooling | The current product already has these reusable foundations, while the prototype supplies the target information architecture. |
| D2 | Preserve current varied sizing / fixed compact sizing | VS Code density at 13 px base with optional interface-size setting | Supports the requested dense workbench while retaining user control over readability. |
| D3 | Loopback-only local model / configurable provider | Configurable providers: Ollama default, optional OpenAI-compatible provider; explicit consent before source leaves the machine; processing location always visible | Supports local-first operation and makes remote processing an informed action. This replaces the conflicting loopback-only prohibition in `PROJECT_SPEC.md` Part 20; later phases must update that old policy text to match the approved v2 decision. |
| D4 | Replace or reuse agent layer | Reuse existing agents and tool registry, aligned to spec roles | Preserves tested work and focuses changes on role mapping. |
| D5 | Replace endpoints / additive migration | Add spec endpoints; retain current routes as deprecated aliases until SL2-10 | Enables staged migration without breaking existing clients. |
| D6 | External analyzer as core / adapter | External analyzers are optional adapters; internal engine remains core | Keeps deterministic engine behavior available offline and avoids hard dependency on optional tools. |
| D7 | Move to proposed tree / preserve current | Keep repository layout; do not move to spec-suggested tree | Avoid broad path churn with no product benefit. |
| D8 | CDN assets / bundled assets | Offline icons/fonts with `lucide-react` and `@fontsource`; no CDN | The existing project already declares these dependencies locally; offline use should not require external fetches. |
| D9 | Mixed or preloaded lab results / separated modes | Safety Lab deterministic harness and live-model mode remain distinct; never mix; no preloaded results | Makes provenance of outcomes clear and prevents simulated output appearing live. |
| D10 | Dark-only / theme selection | Keep light theme and test both light and dark themes | Existing UI-8/9 work already provides both themes. |
