# SL2-0 Prototype Audit

Audited the prototype bundled in `files (1).zip` and placed at `docs/ui_reference_v2/prototype.html`. It is 78,451 bytes. Source counts: 52 `<button>` opening tags, 37 `data-token-id` token elements, and 91 `onclick` attributes. The pre-existing workspace copy had 36 token elements; this attached prototype has 37. Both make the displayed “22 tokens” false. The screenshot `docs/ui_reference_v2/prototype.png` is not available: Edge headless returned no usable file, and the browser-use surface rejected `file:` URLs. No rendered screenshot is claimed.

## Prototype control inventory and required behavior

| Visible control | Real behavior required |
|---|---|
| SecureLex logo | Return to the primary workspace/default view. |
| Activity Bar icons: Explorer, Search, Code Structure/AST, Security, Safety Lab, Settings | Open the corresponding real workspace/sidebar and show selected/focus state, tooltip and accessible label. |
| Explorer project, folder, and file rows; rescan/refresh | Load real workspace files and sample catalog entries; refresh only on user action; filenames must not imply security state. |
| Language/compiler profile and language selector | Show actual language and analyzer availability. Selector offers Python, Java, C/C++, JavaScript; changing it must not rewrite source. The shown Clang identity is fake. |
| Editor tabs, close-tab, split-editor, more-actions | Select/close actual documents while respecting unsaved state; split/layout commands work or are disabled with an explanation. |
| Command-palette/search field | Search and run registered actions/files; no `alert()` placeholder. Show actual keyboard shortcuts. |
| Build with AI / AI Code Scaffold / prompt textarea / language dropdown / Generate & Analyze | Submit a real configured provider request, show processing location and remote consent where applicable, load the candidate, then run actual analysis. Unavailable provider and errors remain visible. |
| Fix Agent Lab / Compare-Patch / Fix with AI | Use current source and actual finding; request a patch, validate it, show reviewable diff and do not apply before user approval; use the independent verifier after apply. |
| Analyze / F5 | Run the actual backend analysis for the current document and options; update Tokens by default and mark previous results stale after edits. |
| Format | Run a configured formatter or show unavailable; do not claim formatting occurred when it did not. |
| Bottom tabs: Tokens, Problems, Security, AI Explain, Agent Activity | Render current analysis data, selected details and real trace. Counts come from returned data; empty/stale/unavailable states are distinct. |
| Inspector open/close/collapse | Change the actual panel layout without losing analysis state. |
| Token search and category filters | Filter current token records by real lexeme/type/location/category, including Invalid when present. |
| Clickable token / token table row | Select the precise source range and synchronize editor and inspector. |
| Copy Tokens | Copy current displayed rows to clipboard and report clipboard failure; no alert. |
| Export Tokens JSON | Export the current analysis data. |
| Export CSV | Add the requested CSV export for current token results. |
| Problems row | Navigate to and highlight the diagnostic’s exact source range. |
| Security row | Show evidence and navigate to the relevant source location. |
| Show Data Flow | Display only available evidence-based taint trace; disclose incomplete path. |
| AI Explain | Request a contextual explanation for the current selected token/finding and display actual provider errors. |
| Clear Output | Clear only the relevant output panel, never source or saved files. |
| Review Diff | Show original/proposed code, removed/added lines, finding, rationale, behavior/security implications and assumptions. |
| Apply Fix | Apply an approved, validated patch to a working copy and start independent verification. |
| Reject Fix / Cancel | Leave source unchanged and close or dismiss the proposal. |
| Undo | Restore the pre-patch source version. |
| Verifier | Run deterministic checks independently and report resolved, remaining, introduced, and unavailable checks. |
| Safety Lab scenario cards | Select a real fixture and configuration; do not preload results. |
| Run Adversarial Test | Execute a bounded fixture scenario and derive outcome from assertions, observed behavior and independent analysis. Live model and deterministic harness modes remain separate. |
| Agent Activity timeline | Display real events for this source version/operation, with actual times and decision provenance. |
| Export Safety Report / Export Report | Generate a report from actual scenario/analysis results in the chosen supported format; identify limitations. |
| Return to Code Editor | Return to the editor view without losing current workspace state. |
| Settings / interface-size / theme controls | Open working settings. Keep light theme and test both light and dark themes. |
| Tooltips, shortcuts and focusable icons | Provide accurate behavior descriptions, documented shortcuts, keyboard access, visible focus and accessible names. |
| Minimize/maximize/close window glyphs | Remove fake OS controls from a browser page; implement only via a real desktop-shell API if one exists. |

## Content that must not be copied

- Invented product version `v2.5-lex`, compiler identity `Clang 16.0.0 (Lexer)`, Clang/ISO C++ parser validation claims, and fixed sub-millisecond timing.
- “22 tokens identified”, “All (22)”, category subtotals and “22 Tokens” in the status bar. This archive’s code sample has 37 token elements; the earlier checked-in version had 36. Neither is a product-wide token count.
- `alert()` flows for the command palette, formatting, patch application, undo, generation, copying, Safety Lab run/export and settings. Replace each with functional UI states and recoverable errors.
- Preloaded Safety Lab scenario cards/results, payload `#ADV-804`, “ATTACK CONTAINED & RESISTED”, policy decision and static timeline timestamps/results. Start with no run result and derive each run from actual execution.
- Fake minimize/maximize/close window controls in page content.
- Hard-coded patch converting `int a = 9;` to `constexpr int a = 9;` and its unsupported “type safety”, performance, compile-time and verification rationale.
- Claims “100% lexically valid”, “Memory Safety: 100% Deterministic Stack Allocation”, “22 tokens validated without syntax discrepancies”, and similar guarantees. Report measured results only and never imply universal security.
- CDN dependencies: Tailwind at `https://cdn.tailwindcss.com`, Google Fonts stylesheets, and remote Material Symbols. They break offline use; use bundled styling, `@fontsource` and `lucide-react` with no CDN.

Layout, information hierarchy and panel relationships are visual references. Use live workspace/API/analysis state for every result. Keep the existing workspace reducer, theme tokens, manual-analysis model and adapted QA tooling under decisions D1/D10.
