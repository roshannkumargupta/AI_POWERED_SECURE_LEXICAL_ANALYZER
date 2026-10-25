# SecureLex IDE User Guide

## Start checking code

Start the FastAPI backend and Vite frontend as described in the root [README](../README.md). The editor supports Python, Java, JavaScript and C/C++. Choose an example or create/open a buffer, edit it, then select **Analyze**. Analysis is performed by the backend; each result lists which checks ran and which were unavailable.

## Inspect tokens and findings

Select a token to inspect its lexeme, token type, category, lexical status and source position. Search and category filters change the displayed token rows. Syntax and semantic diagnostics are separate from lexical validity. Problems and Security views navigate to source evidence; a finding's analyzer/tool provenance, certainty and remediation describe the evidence available for that finding. “No findings detected by checks run” means only that the listed checks did not report a finding.

## AST and data flow

Open AST to navigate parser nodes and inspect their ranges and related evidence. If the parser or grammar is unavailable, the UI reports that condition. A data-flow view draws only source, propagation, sanitizer and sink steps returned by analysis; incomplete paths include their limitation.

## AI and privacy

AI Explain, Build with AI and AI fixes require a configured, reachable provider. Without one, the UI shows setup guidance. groq is the local default. Remote OpenAI-compatible providers require the explicit session consent flow; inspect the processing-location badge and consent state before sending source. Provider keys stay in the server environment.

Generated code opens as a separate candidate and is analyzed by the backend; it is not executed. A fix proposal does not change the source. Review the diff, apply only when intended, read the independent verification's four sections, and use Undo to restore the previous in-memory buffer. Verification applies to reported checks only.

## Safety Lab and exports

Harness mode runs deterministic scenarios without a model. Live mode requires a real configured model; no simulated live result is supplied when it is unavailable. Open Agent Activity to inspect the recorded operation timeline. Export reports or token data from the Export controls; exported text is neutralized for control characters.

## Settings, navigation and support

Use Settings for theme, interface size, provider state, consent, and tool availability where exposed. Use the command palette for registered actions. Optional tools are detected from the current machine; the capabilities endpoint is the authoritative runtime report. See the root README for installation, tests, analyzer coverage, and [docs/limitations.md](limitations.md) for operational boundaries.
