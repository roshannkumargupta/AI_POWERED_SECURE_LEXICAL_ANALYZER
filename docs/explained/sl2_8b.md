# SL2-8b: API-wired analysis workspace

## What changed

The UI now has a workspace navigation surface for diagnostics, security evidence, AST inspection, AI explanations, agent activity, code generation, fix proposals, Safety Lab runs, settings and export. Data is requested from the existing backend routes rather than embedded into the new views. Unavailable providers disable dependent actions; backend failures appear as error text with retry controls.

Problems combines lexical and syntax-stage diagnostics. Security shows returned CWE, severity, certainty, provenance, evidence, remediation and taint steps. AST expansion is lazy. AI generation opens a distinct `AI candidate` file, and the view shows the returned analysis, explanation, assumptions and requirement checklist. Fix proposals remain unapplied until the explicit Apply action; verification and undo use the server endpoints. Safety Lab displays a fetched run result and marks harness mode as deterministic.

The command palette includes Explain selected token, Propose a fix, Open Safety Lab, Export report, Open AST, Show Security, Build with AI and Undo fix. The corresponding Ctrl+Shift shortcuts are listed in the shortcuts dialog.

## Verification limits

Vitest passed 152 tests across 23 files; the production build passed. The real browser acceptance remains blocked: this Windows sandbox denied loopback sockets to 127.0.0.1, and the CDP browser runner reported `connect EACCES 127.0.0.1:9222`. Therefore the four-language browser flow, both-theme five-viewport diagnostics and requested screenshots were not verified. No screenshots are fabricated. The full details are in `reports/sl2_8b_evidence.md`.

## Viva questions and answers

1. **How are Problems populated?** The view requests the lexical and syntax stage endpoints using the current source and monotonically increasing source version, then groups only diagnostics returned by those endpoints.
2. **What prevents a proposed fix from changing the code immediately?** Proposal creation stores and displays a server-issued proposal. Source changes only after the user invokes Apply, and that endpoint requires explicit approval and independent verification.
3. **How does AST expansion handle large files?** Syntax analysis requests a bounded AST view. Selecting a node can request its children from the server's lazy AST endpoint.
4. **What happens if an AI provider is missing?** Capabilities are used to disable AI-dependent controls and show setup/unavailability guidance. The UI does not substitute a canned explanation or generated program.
5. **Which acceptance checks are still outstanding?** A real-browser end-to-end run across Python, Java, JavaScript and C++, the five-viewport diagnostics in both themes, and screenshots are outstanding because localhost/DevTools socket access is denied in this environment.
