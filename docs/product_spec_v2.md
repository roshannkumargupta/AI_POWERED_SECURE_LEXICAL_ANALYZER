# MASTER BUILD SPECIFICATION — SecureLex
## AI-Powered Secure Lexical Analyzer, Intelligent Coding Tutor, and Agent Verification Platform

Act as a senior full-stack engineer, compiler engineer, application-security engineer, AI-agent architect, and UI/UX designer.

I am building an academic project called **SecureLex — AI-Powered Secure Lexical Analyzer**. I have provided an existing HTML implementation that demonstrates the intended UI. Use that implementation as the primary visual and interaction reference.

Your job is to turn this existing prototype into a complete, working, maintainable application with a real analysis engine, real backend integration, specialized AI responsibilities, independent fix verification, and an adversarial Agent Safety Lab.

**Do not stop after producing a beautiful UI. Do not replace real functionality with alerts, mock responses, hardcoded token arrays, simulated success messages, or fake security results.**

Inspect the existing codebase, understand what is already implemented, preserve useful working functionality, and implement the missing parts. If the project is currently a standalone HTML file, establish a maintainable frontend/backend structure while preserving its visual identity. If a suitable application framework already exists, extend it instead of unnecessarily rewriting everything.

Do not merely explain what should be done. Implement the application, run its available tests, fix integration failures, and document any genuine environmental limitations.

---

# PART 1 — PRODUCT VISION

SecureLex is primarily a **lexical analyzer with advanced program understanding, security analysis, AI-assisted repair, and agent verification**.

The core output is a token table. Everything else expands the value of that lexical analysis.

A beginner should be able to open the website, describe a program they want to create, inspect the resulting tokens, understand errors, identify potential security weaknesses, receive an explanation, apply a proposed fix, and inspect the independent verification results.

An experienced developer should be able to inspect source locations, token categories, parser diagnostics, AST structure, security rules, data-flow traces, patch diffs, and agent events.

The application must support:

1. Lexical analysis for Python, Java, C/C++, and JavaScript.
2. Token classification with exact positions and lexical validity.
3. Syntax parsing and AST inspection.
4. Supported semantic diagnostics.
5. Static security analysis, applicable CWE mappings, and taint analysis.
6. Beginner-friendly explanations.
7. AI-generated source code from natural-language requests.
8. AI-proposed code fixes with reviewable diffs.
9. Independent verification of generated and fixed code.
10. Code-quality and performance analysis where evidence supports it.
11. Agent Safety Lab with reproducible adversarial tests.
12. Exportable analysis and security reports.
13. A professional, VS Code-style interface with functional controls.

The defining principle is:

**The AI can propose changes. The analysis engines provide evidence. The independent verification workflow evaluates whether the changes actually worked.**

Do not claim that any analyzer can detect every possible error or prove arbitrary code completely secure.

---

# PART 2 — FIRST INSPECT THE EXISTING PROJECT

Before changing files:

1. Inspect the repository structure and identify the frontend, backend, existing dependencies, configuration, and available tests.
2. Read the existing SecureLex HTML and any relevant source files.
3. Identify which features are real, which are partially implemented, which are hardcoded, and which are only visual.
4. Preserve the existing VS Code-inspired design and working functionality.
5. Create a short implementation checklist and then proceed with implementation. Do not stop after presenting the checklist.

The attached HTML already contains a useful design foundation:
- A title bar and command palette.
- An Activity Bar.
- Explorer and file-selection controls.
- A tabbed code editor.
- Analyze and Fix with AI actions.
- A bottom analysis panel containing Tokens, Problems, Security, AI Explain, and Agent Activity.
- Token search, category filters, an inspector, and export controls.
- Build with AI.
- Agent Safety Lab.
- Fix review and verification interfaces.

Retain and improve these ideas. Avoid a wholesale visual redesign unless the current structure makes a required workflow impossible.

The current prototype also contains hardcoded token information, sample counts, alerts, simulated agent results, and a simplistic patch application flow. Replace these with real application state and actual backend operations.

Do not retain inaccurate version numbers, invented compiler identities, false scan durations, unsupported security claims, or fabricated verification outcomes.

---

# PART 3 — TECHNOLOGY AND PROJECT ARCHITECTURE

Use the existing technology when it is sound. Do not introduce a new framework merely for personal preference.

If the attached HTML is the only implementation and no application architecture exists, use this recommended starting point:

**Frontend**
- React.
- TypeScript.
- Vite.
- Monaco Editor or `@monaco-editor/react`.
- Tailwind CSS or the existing compatible styling system.
- A consistent icon library, preferably the existing Material Symbols Outlined family if retained.
- Accessible reusable components.
- Typed API clients and a single source of truth for workspace state.

**Backend**
- Python.
- FastAPI.
- Pydantic request and response models.
- Separate language-analysis adapters.
- Separate security-analysis services.
- A controlled AI model-provider adapter.
- An agent orchestrator with restricted tools.
- Persistent storage only where it is actually required.

Use the existing repository structure if it already supplies equivalent capabilities.

Suggested conceptual structure:

```text
securelex/
  frontend/
    src/
      components/
      editor/
      explorer/
      token-analysis/
      problems/
      security/
      code-fixes/
      agent-activity/
      safety-lab/
      learning/
      services/
      types/
  backend/
    app/
      api/
      schemas/
      orchestrator/
      languages/
        common/
        python/
        java/
        cpp/
        javascript/
      parsers/
      semantic/
      security/
      taint/
      quality/
      agents/
      verification/
      sandbox/
      reporting/
      tests/
  rules/
    security/
    lexical/
  examples/
    valid/
    lexical-errors/
    syntax-errors/
    security/
    adversarial/
  docs/
  .env.example
  README.md
```

This is a proposed organization, not a requirement to move every file if the current project already has a good equivalent structure.

Keep tokenization, parsing, security analysis, AI generation, fixing, and verification in separate modules. Do not implement the entire product as one giant component or one large Python file.

---

# PART 4 — FRONTEND: COMPLETE IDE EXPERIENCE

## 4.1 Visual design

Create a polished desktop-first coding IDE inspired by VS Code.

Preserve the familiar layout:

- Compact top title bar.
- Narrow Activity Bar on the far left.
- Explorer sidebar.
- Central editor with file tabs.
- Resizable bottom analysis panel.
- Contextual token inspector.
- Thin status bar.

Use the existing dark palette:

```text
Editor:          #1E1E1E
Sidebar:         #181818
Elevated panel:  #252526
Borders:         #303030
Selection:       #264F78
Primary blue:    #0078D4
Success:         #4EC9B0
Warning:         #D7BA7D
Error:           #F14C4C
AI accent:       #A78BFA
Text:            #CCCCCC
Muted text:      #999999
```

Use Inter for interface text and JetBrains Mono for source code and tabular token data.

Do not introduce giant cards, marketing sections, oversized headings, neon effects, excessive gradients, or decorative analytics charts.

The editor and token table must have enough screen space to remain genuinely useful.

## 4.2 Title bar and command palette

The header should include:
- SecureLex logo and name.
- Current workspace or project name.
- Search/command palette.
- Current language context.
- A compact Build with AI action where appropriate.
- Settings.

Implement a real command palette, not an `alert()` pretending to open one.

It should search registered application actions such as:
- Analyze current file.
- Switch language.
- Open an example.
- Show tokens.
- Show problems.
- Open Security.
- Explain selected token.
- Propose a fix.
- Open Agent Safety Lab.
- Export the current report.

Support documented keyboard shortcuts for important actions, and show the actual shortcuts in tooltips.

Avoid fake operating-system window controls in a normal browser application.

## 4.3 Activity Bar and Explorer

Provide:
- Explorer.
- Search.
- Code Structure / AST.
- Security.
- Agent Safety Lab.
- Settings.

Use consistent icons, visible selection state, keyboard focus, accessible labels, and tooltips.

The Explorer should support:
- Opening sample files.
- Creating and renaming files if supported by the storage model.
- Switching between open editor tabs.
- Identifying the current language.
- Displaying useful examples.
- Showing unsaved changes.
- Indicating detected problems without implying that file names themselves prove security.

The supported language selector must offer:
- Python.
- Java.
- C / C++.
- JavaScript.

Changing language must update the selected analyzer. Do not silently translate or rewrite the current program.

## 4.4 Real code editor

Use Monaco Editor where compatible with the project architecture.

Support:
- Syntax highlighting.
- Editable source.
- Line numbers.
- Cursor position.
- Current-line highlighting.
- Selection.
- Editor tabs.
- Scrollbars.
- Diagnostics and source markers.
- Token-to-source synchronization.
- Finding-to-source synchronization.
- Unsaved-state tracking.
- Undo and redo.
- Copy and paste.
- Find in file.
- Format code when the appropriate formatter is available.

Use a consistent internal mapping between source offsets and Monaco line/column positions. Test Unicode and newline handling.

Do not display a static HTML drawing of an editor while using a separate, unsynchronized textarea for actual input.

When the selected source changes, invalidate outdated analysis results or clearly mark them stale. Never display previous findings as though they describe newly edited code.

## 4.5 Main source example

Initially load a valid C++ example:

```cpp
#include <iostream>

int main() {
    int a = 9;
    int b = 19;
    int sum = a + b;

    std::cout << sum << '\n';
    return 0;
}
```

Create independent examples for lexical errors, syntax errors, and security issues in each supported language.

Do not label this ordinary arithmetic example insecure. The default example must not display a security finding unless a real rule actually detects one.

---

# PART 5 — TOKEN ANALYSIS ENGINE

This is the most important subsystem in the entire project.

## 5.1 Token-first experience

The bottom panel must open automatically after Analyze with **Tokens selected by default**.

The token table must be the most visible analysis result, not a secondary tab hidden behind a dashboard.

The Tokens panel should provide:

- Token count.
- Valid-token count.
- Invalid-token count.
- Analysis status.
- Token search.
- Filters for All, Invalid, Keywords, Identifiers, Operators, Literals, and other meaningful categories.
- Copy results.
- Export to CSV and JSON.
- Sort by source position and token type.
- Selected-token inspection.
- Editor-to-table synchronization.

Do not hardcode counts, categories, or selected rows.

All displayed counts must be derived from the actual current token results.

## 5.2 Token schema

Use a consistent typed token representation. At minimum, every token should contain:

```text
id
language
lexeme
token_type
category
start_offset
end_offset
start_line
start_column
end_line
end_column
lexical_status
diagnostic_ids
```

Keep token identity stable enough for selection and highlighting within a given analysis version.

Use one-based human-readable line and column values in the UI. Convert offsets and positions correctly for each editor and parser API.

Use clear categories such as:
- Keyword.
- Identifier.
- Operator.
- Number literal.
- String literal.
- Character literal where relevant.
- Delimiter.
- Comment.
- Preprocessor directive.
- Header token where appropriate.
- Language-specific token categories.

The exact rules and grammar must depend on the selected language.

## 5.3 Lexers must be language-aware

Implement or improve real deterministic lexical scanners for all four supported language choices.

Do not use a single naive regex that splits source on whitespace or punctuation.

Use language-specific scanning logic that correctly handles applicable constructs such as:
- Identifiers.
- Reserved keywords.
- Maximal-munch operators.
- Numeric literal formats.
- Quoted strings and escapes.
- Comments.
- Whitespace and newline behavior.
- Delimiters.
- Malformed literals.
- Unterminated comments and strings.
- Language-specific punctuation.
- C/C++ preprocessing constructs.
- Python indentation and string prefixes.
- Java lexical forms.
- JavaScript template literals and context-sensitive lexical edge cases.
- Unicode identifiers and suspicious invisible or look-alike characters.

For difficult grammar-specific cases, use established language libraries or native tooling to validate the scanner's results.

Python's `tokenize` module is a useful reference for Python tokenization. Use suitable parser/tokenizer tooling for the other languages where helpful. If the project's educational requirements call for custom lexers, keep your own deterministic tokenization implementation and validate it against trustworthy language tools rather than silently delegating all lexical work to an opaque service.

Do not claim full standards compliance until the implementation has been tested against an appropriate test suite.

## 5.4 Lexical validity is a separate dimension

A token can be lexically valid while the whole program is syntactically incorrect or insecure.

Report:
- **Lexical status:** Valid, Invalid, or an explicitly justified Unknown/Unclassified state.
- **Syntax status:** Based on the parser.
- **Semantic status:** Based on available semantic diagnostics.
- **Security status:** Based on relevant security rules and evidence.

Do not mark recognized tokens lexically invalid merely because the parser rejects a surrounding statement.

Do not assign generic security labels to ordinary keywords or identifiers.

For Unicode and invisible-character analysis, distinguish:
- A valid language character.
- An unexpected or disallowed character.
- A suspicious identifier.
- A character sequence that can alter the source's interpretation.

Preserve enough raw source information to explain suspicious character findings accurately.

---

# PART 6 — SYNTAX, AST, AND SEMANTIC ANALYSIS

Use real parsing tools. Do not ask an LLM to invent an AST or guess syntax errors from a prompt.

Evaluate and integrate suitable technologies:
- Tree-sitter for incremental syntax trees and error-tolerant parsing.
- Python's `ast` and native compiler diagnostics.
- Clang tooling and syntax diagnostics for C/C++.
- An appropriate Java parser and compiler diagnostics when available.
- A proper JavaScript parser and compatible diagnostics.
- Other established language tools when they offer a clear advantage.

Build adapters that return the same diagnostic schema regardless of which language tool produced the result.

Each diagnostic should contain:
- ID.
- Language.
- Source location.
- Category.
- Severity.
- Message.
- Related source evidence.
- Tool or rule that produced it.
- Whether the result is definitive, heuristic, or incomplete.

Support:
- Syntax errors.
- Missing or unexpected delimiters.
- Malformed expressions.
- Missing statement terminators where required.
- Parser error and missing-node reporting.
- AST visualization.
- Semantic checks when available.
- Undefined names and incompatible types when the relevant tool and language context support those checks.

Display an explicit incomplete or unavailable state when the required toolchain or project context is missing.

A parser success must not automatically be reported as complete semantic correctness.

## AST workspace

The AST view should show a navigable tree with:
- Node type.
- Source range.
- Parent and child relationships.
- Selected node's code range.
- A compact node-detail inspector.

Selecting a node should highlight its source span and link to relevant tokens or findings.

Keep this as an advanced workspace rather than cluttering the initial screen.

---

# PART 7 — SECURITY ANALYSIS ENGINE

Security is the second major differentiator after lexical analysis.

It must be a real static-analysis system, not merely a set of AI-generated warnings.

## 7.1 Security engine design

Create an extensible security-rule system with:
- Language-specific rules.
- Rule identifiers.
- Severity.
- Evidence.
- Source locations.
- CWE mapping where applicable.
- Confidence or uncertainty.
- Remediation guidance.
- Suggested safe coding patterns.
- Test fixtures.
- Safe counterparts for known vulnerable examples.

Evaluate appropriate tools such as Semgrep, Clang Static Analyzer, clang-tidy, cppcheck, Bandit, Ruff, ESLint and supported language-specific analyzers.

Choose the actual tools according to the repository, deployment environment, licensing and availability. Do not claim a tool is installed or executed unless it is.

The security engine should combine compatible existing tools with a maintainable internal rule registry.

## 7.2 Vulnerability categories

Cover high-value rules appropriate to the supported languages, such as:
- Command or OS injection.
- SQL injection where relevant.
- Unsafe evaluation of user-controlled text.
- Path traversal.
- Unsafe deserialization.
- Hardcoded secrets.
- Unsafe memory and buffer operations in C/C++.
- Format-string misuse.
- Dangerous API usage.
- Cross-site scripting patterns in applicable JavaScript contexts.
- Weak cryptographic usage where recognized.
- Untrusted input reaching a sensitive operation.
- Unicode and hidden-character issues.

These are intended rule families, not claims that every vulnerability in every language is already covered.

Use an extensible source–propagation–sink model for taint analysis.

Examples of conceptual sources include user input and request parameters; sinks include command execution, SQL execution, file access, and other sensitive operations. Recognize sanitization or validation steps when the available analysis engine can establish them.

## 7.3 Taint-path visualization

For an actual finding, show a trace such as:

Untrusted input → variable assignment → string construction → sensitive sink.

Each step must refer to real source ranges or an actual analysis result.

Indicate sanitization and validation where detected.

If the analysis cannot establish a complete path, state that limitation. Do not fabricate intermediate nodes to make the diagram appear complete.

## 7.4 Security result language

Use careful wording:
- Finding detected.
- Potential vulnerability.
- Confirmed by the specified rule or test.
- No findings detected by checks run.
- Analysis incomplete.
- Check unavailable.

Never present a universal security score as though it proves the program secure.

Never label the application or code "100% secure."

---

# PART 8 — AI MODEL AND AGENT ORCHESTRATOR

## 8.1 Model-provider layer

Implement a configurable model-provider interface.

Where appropriate, support:
- Local inference through Ollama.
- OpenAI-compatible endpoints.
- Additional providers through explicit adapters.

Use configuration and environment variables for model endpoints, model names, and secrets. Do not hardcode API keys or assume a provider is available.

If no model is configured, the core lexical and deterministic analysis capabilities must continue working. AI-dependent functions should display a clear setup message and recoverable error state rather than fabricate a response.

Provide configurable request timeouts, bounded retries, structured output validation and appropriate request-size limits.

## 8.2 Agent responsibilities

Implement these distinct logical roles:

### Lexer
Produces the deterministic token stream and lexical diagnostics.

### Parser
Produces syntax diagnostics and AST information from actual parsing tools.

### Semantic Analyzer
Coordinates supported language-specific semantic checks.

### Security Analyzer
Runs applicable security rules and data-flow checks.

### Triage Agent
Groups, prioritizes, and summarizes existing findings. It must not silently delete findings or downgrade severity without an evidence-based reason.

### Fix Agent
Proposes a patch for a specific issue. It must return a structured change proposal, its rationale, target finding, expected outcome, assumptions, and known risks.

### Independent Verifier Agent
Reviews the proposed and modified source independently, using the actual analyzer output, tests, patch, and verification rules.

It must not accept the Fix Agent's own self-reported success as proof.

### Explanation Agent
Explains the actual tokenization, diagnostic, vulnerability, or patch result in language appropriate to the user.

Do not create seven expensive, unrestricted autonomous LLMs merely to satisfy the names. These are responsibilities that can be orchestrated through deterministic tools, bounded model calls, and independent validation.

## 8.3 Orchestration and tool gateway

Build a controlled orchestration layer that:
1. Validates the user request.
2. Selects the relevant language and analysis stages.
3. Runs deterministic analysis.
4. Stores structured results for the current source version.
5. Invokes AI assistance when useful.
6. Validates model output.
7. Requests explicit approval for modifications.
8. Triggers independent verification after changes.
9. Returns results with provenance and limitations.

The tool gateway must enforce an explicit allowlist of tools, operations and parameters.

Do not give the LLM unrestricted shell access, filesystem access, network access or permission to modify security policies.

Treat source code, comments, strings, filenames, external documents and model outputs as untrusted data. Instructions embedded inside source code must not automatically become instructions to the orchestrator.

Use schema validation and external permission checks. A prompt saying "be secure" is not a security boundary.

---

# PART 9 — BUILD WITH AI FOR NON-CODERS

Make code generation accessible without replacing the IDE with a chatbot.

The user should be able to click Build with AI and enter something like:

"Write a Python program that reads a list of integers and returns the largest value, explaining how it works."

The user chooses the target language and submits the request.

The workflow must:
1. Interpret the requirements.
2. Generate a candidate program.
3. Display the candidate in the editor.
4. Run the actual lexical analyzer.
5. Run available syntax and semantic checks.
6. Run applicable security analysis.
7. Explain the tokens and findings.
8. Identify any unmet requirements or unverified behavior.
9. Offer reviewable improvements.

If code generation fails, show the real error and allow retry or editing.

If the model produces code that fails analysis, show the findings rather than falsely declaring success.

Generated code must use exactly the same analysis and verification pipeline as user-written code.

---

# PART 10 — COMPLETE FIX → VERIFY → ACCEPT WORKFLOW

This is a mandatory, end-to-end feature.

## Stage 1: Find an issue

The user selects a problem or security finding and clicks **Fix with AI**.

The Fix Agent receives the current source version, the specific finding, relevant source context, and the available evidence.

## Stage 2: Propose a patch

The agent returns a structured patch and explanation.

Validate that:
- The patch targets the expected file and source version.
- The changed ranges are well-formed.
- The patch does not modify unrelated content without a justified reason.
- No unexpected file operations or side effects are requested.
- The patch can be rendered as a proper diff.

Reject malformed, ambiguous, or out-of-scope changes.

## Stage 3: Review the diff

Display the original and proposed changes.

Show:
- Removed lines.
- Added lines.
- The issue being addressed.
- Why the modification should help.
- Expected behavior changes.
- Security implications.
- Remaining assumptions.

Provide explicit actions:
- Apply Fix.
- Reject.
- Cancel.

The source must not be changed merely because the model proposed a patch.

## Stage 4: Apply to a working copy

Create an undo point, apply the approved patch to a working copy, and record the source version.

Do not treat a successful text replacement as a successful repair.

## Stage 5: Independent verification

Invoke a separate Verifier Agent with a fresh verification task and the required evidence.

Run the deterministic analyzers independently of the Fix Agent:
- Lexical checks.
- Syntax and AST checks.
- Supported semantic checks.
- Relevant security rules.
- Relevant taint analysis.
- Available tests or regression checks.
- Patch integrity checks.

Compare the results against the original analysis.

The Verifier Agent must identify:
- Target issue resolved or not resolved.
- Original issues remaining.
- New findings.
- Tests passed or failed.
- Checks unavailable.
- Behavior changes requiring additional tests.
- Quality or performance claims that cannot be established.

An independent LLM review may add useful reasoning, but deterministic checks and actual tests must remain the source of truth for the conditions they cover.

## Stage 6: Verification report

Display four clear sections:

**Resolved** — Target findings that are no longer detected by the specified checks.

**Remaining** — Findings that still exist.

**Introduced** — Newly detected problems or regressions.

**Unverified** — Required checks that could not be completed.

Use an outcome such as:
- Verified for specified checks.
- Partially verified.
- Verification failed.
- Inconclusive.

Keep the original source recoverable. Allow the user to keep the patch, undo the change, or request another proposal.

## Stage 7: Honest quality evaluation

Do not claim that the solution is optimal because an AI model says so.

Evaluate:
- Correctness against available requirements and tests.
- Security evidence.
- Complexity estimates where justified.
- Measured performance only if actual benchmarks were run.
- Maintainability and readability.
- Regression risk.
- Unverified assumptions.

Every quality statement must have a reason or supporting measurement.

---

# PART 11 — AGENT SAFETY LAB

Implement the existing Agent Safety Lab as an actual, demonstrable adversarial evaluation workspace.

Do not populate it permanently with a predetermined "Attack Contained" result.

Each run must have a unique result derived from an executed scenario.

## Test scenarios

Include:
1. Prompt injection embedded in a source-code comment.
2. An attempt to persuade the agent to suppress a seeded security finding.
3. An insecure AI-generated code candidate.
4. An instruction attempting to bypass the fix verifier.
5. A patch that introduces a syntax regression.
6. A safe input that resembles an attack but should not cause a false alarm.

Use predefined test fixtures and expected outcomes. Keep arbitrary payloads out of unrestricted execution environments.

## UI layout

Use three principal sections:

**Attack Scenario**
- Scenario selection.
- Language.
- Input and scenario configuration.
- Expected safe behavior.
- Run Scenario button.

**Agent Behavior**
- Actual model response or a clearly marked no-model result.
- Requested tool operations.
- Allowed and denied actions.
- Proposed code changes.
- Observable event timeline.

**Independent Verification**
- Actual scanner results.
- Findings before and after the attack.
- Whether seeded issues were preserved or suppressed.
- Patch integrity and regression results.
- Final test outcome.

Allow these outcomes:
- Attack resisted.
- Attack contained.
- Attack succeeded.
- Inconclusive.
- Verification failed.

Do not let a model award itself a passing grade. Derive the outcome from explicit test assertions, independent analysis and the observed agent behavior.

Provide an exportable report containing scenario identifier, configuration, results, findings and limitations.

When the model is unavailable, report that the live agent test could not run. Do not simulate a successful real-world attack-defense experiment.

---

# PART 12 — API CONTRACT AND DATA FLOW

Implement documented, typed API contracts. Adapt these route names to the existing architecture where appropriate.

Suggested endpoints:

```text
GET  /api/health
GET  /api/capabilities

POST /api/analyze
POST /api/analyze/lexical
POST /api/analyze/syntax
POST /api/analyze/security
POST /api/analyze/quality

POST /api/ai/generate
POST /api/ai/explain

POST /api/fixes/propose
POST /api/fixes/verify
POST /api/fixes/apply
POST /api/fixes/undo

POST /api/agent-safety/run
GET  /api/agent-safety/results/{run_id}

POST /api/reports/export
```

Use typed request and response schemas.

The unified analysis result should include:
- Analysis ID.
- Source version or source hash.
- Language.
- Token records.
- Lexical status.
- Syntax diagnostics.
- Semantic diagnostics.
- Security findings.
- Taint paths when available.
- Quality observations.
- Tool execution status.
- Timing measurements when actually measured.
- Warnings, omissions and unavailability information.

Return source locations consistently.

Use one source of truth for findings and counts. The frontend must not maintain separate hardcoded counts that can drift away from API data.

Consider cancellation, timeouts, request validation, stale analysis responses and error recovery.

Return useful structured errors instead of raw stack traces.

---

# PART 13 — SECURITY OF THE SECURELEX APPLICATION

The website accepts arbitrary source code and uses AI agents. Protect the application itself.

Implement the following safeguards:

1. Bound source size, request size, execution time, memory use, concurrency and model request volume.
2. Do not execute arbitrary submitted source in the FastAPI process.
3. Prefer static analysis that does not execute user code.
4. If an optional Run or Test Code feature is implemented, use an isolated sandbox with resource limits, restricted filesystem access, disabled network access by default, timeouts and process cleanup.
5. Never invoke shell commands by interpolating source code, filenames or model output into a command string.
6. Use safe subprocess argument arrays and explicit executable allowlists for permitted analysis tools.
7. Keep temporary files in controlled directories and clean them up.
8. Validate every generated patch before it is applied.
9. Restrict agent operations independently of model instructions.
10. Do not allow arbitrary tool execution or unrestricted network and filesystem access.
11. Protect API keys through server-side environment configuration.
12. Avoid silently sending source code to external model providers.
13. Show users which model provider is configured and where their code is processed.
14. Validate model outputs before using them in tool operations or the user interface.
15. Render source code and model outputs as escaped text, never as trusted HTML.
16. Keep useful audit events while avoiding unnecessary storage of source code, secrets or sensitive prompts.
17. Ensure one user's files or analysis results cannot leak into another user's session.

Do not describe prompt filtering as a complete defense against prompt injection. Use restricted permissions, structured tool schemas, independent checks, and explicit approval boundaries.

---

# PART 14 — MAKE EVERY BUTTON AND ICON WORK

Audit every existing control in the attached HTML and in the final application.

No decorative button should pretend to be functional.

Implement these behaviors:

| UI control | Required behavior |
|---|---|
| SecureLex logo | Return to the primary workspace or default view. |
| Activity Bar icons | Open the correct workspace or sidebar. |
| Explorer file | Open the corresponding source and refresh the file state. |
| Language selector | Change the active language and analyzer configuration. |
| Editor tabs | Select and close tabs while respecting unsaved changes. |
| Command palette | Search and run registered commands. |
| Analyze | Execute the real analysis pipeline. |
| Format | Run the configured formatter or explain why it is unavailable. |
| Clear Output | Clear only the relevant output panel, not source code or saved files. |
| Token filters | Show the correct filtered token records. |
| Token search | Filter by lexeme, type, position or supported metadata. |
| Token row | Highlight the source token and populate the inspector. |
| Problems row | Navigate to and highlight the diagnostic's source range. |
| Security row | Show evidence and navigate to the relevant source. |
| Show Data Flow | Display the available, evidence-based trace. |
| AI Explain | Request and display a contextual explanation. |
| Build with AI | Submit a generation request and load the returned candidate. |
| Fix with AI | Request a patch based on an actual finding or explicit user request. |
| Review Diff | Display original and proposed code. |
| Apply Fix | Apply an approved, validated patch and start verification. |
| Reject Fix | Leave the source unchanged. |
| Undo | Restore the pre-patch source version. |
| Verifier | Run independent checks and display actual results. |
| Agent Activity | Display real observable event records for the current operation. |
| Agent Safety Lab | Open the safety workspace. |
| Run Adversarial Test | Execute the selected test and evaluate its assertions. |
| Export Report | Generate a real report in the selected supported format. |
| Copy Tokens | Copy the displayed token results to the clipboard. |
| Export JSON/CSV | Download the current, accurate analysis data. |
| Settings | Open real settings for available options. |
| Panel resize/maximize/close | Change the panel layout and preserve current analysis state. |
| Tooltips | Explain icon-only and technical controls. |

Use proper disabled states, loading indicators, completion feedback, and recoverable error messages. Avoid generic browser alerts for normal application workflows.

Do not implement a pretend button that always shows a successful result.

If a feature depends on an unavailable executable, model provider, compiler or external service, show a meaningful setup or unavailable state and continue supporting the other functions.

---

# PART 15 — TESTING AND VERIFICATION

Do not declare the application complete merely because the interface renders.

Build a test suite that exercises the core features and the integration between them.

## 15.1 Lexical tests

For every language, test:
- A valid program.
- A keyword and an identifier.
- Operators and delimiters.
- String and numeric literals.
- Comments.
- Escaped characters.
- Multiple-line input.
- Unterminated strings or comments.
- Malformed numeric forms where applicable.
- Invalid character sequences.
- Unicode and invisible-character edge cases.
- Correct line and column reporting.
- Correct source-offset mapping.
- Search and filtering accuracy.
- Token count accuracy.

Verify both valid and invalid examples. Confirm that syntax errors do not cause otherwise valid tokens to be mislabeled as lexically invalid.

## 15.2 Syntax and semantic tests

For every supported language, test valid code, missing delimiters, malformed statements, missing terminators where required, and representative semantic diagnostics supported by the configured tools.

Test tool failure and missing-toolchain behavior.

## 15.3 Security tests

For each supported language, create seeded examples and safe counterparts for supported security rules.

Test that:
- Findings contain valid source locations.
- A safe counterpart is not automatically flagged by a broad textual heuristic.
- Each rule's evidence is recorded.
- Findings are deduplicated appropriately.
- Taint paths use real source and sink evidence.
- Unsupported analyses are identified honestly.
- Token selection remains independent of security findings.

## 15.4 Fix and independent-verification tests

Test:
- A patch resolving its target issue.
- A patch that fails to resolve the target.
- A patch that introduces a syntax error.
- A patch that introduces a security issue.
- A patch with malformed ranges.
- Rejection without modifying source.
- Applying a patch and undoing it.
- Verification failure.
- Missing verification tools.
- Stale results after editor changes.
- Correct before/after finding comparisons.

The verifier must not simply trust a success message from the Fix Agent.

## 15.5 Agent Safety Lab tests

Test all predefined scenarios with explicit expected outcomes.

Record actual agent behavior and verify the result with independent checks. Include successful attacks, contained attacks, inconclusive cases and infrastructure failures as test outcomes.

Do not prepopulate passing results and call them executed experiments.

## 15.6 Frontend and API integration tests

Verify:
- Every visible button works.
- Every Activity Bar icon opens the right view.
- Tabs show the correct content.
- Token selection and editor selection remain synchronized.
- Filters change actual displayed rows.
- Counters match data.
- Copy/export operations work.
- Model errors display helpful feedback.
- Loading and cancellation work appropriately.
- No major control leads to a dead end.
- Generated patches pass through the approval and verifier process.
- The application handles smaller desktop widths without making the token table unusable.

Use appropriate unit, API integration, browser-based end-to-end and security tests based on the project's toolchain.

Run the tests. Fix the failures you can reproduce.

---

# PART 16 — SETUP, DOCUMENTATION, AND HANDOFF

Create a complete README that explains:
- The architecture.
- Frontend and backend setup.
- Required and optional language tools.
- How to install and configure analyzers.
- How to configure an LLM provider or local Ollama endpoint.
- Environment variables.
- How to launch the website.
- How to run tests.
- How each language is analyzed.
- Which security rules and taint flows are supported.
- Which capabilities are experimental.
- How to add a new token rule or security rule.
- How to interpret verification results.
- Limitations of static analysis and AI-assisted review.
- How to run the Agent Safety Lab scenarios.

Provide `.env.example` without real credentials.

Make tool availability discoverable through a capabilities endpoint. Avoid claiming that Clang, Java, Ollama, Semgrep or any other tool is present until the environment confirms it.

Where feasible, provide a single documented development startup command or clearly documented frontend/backend startup commands.

Do not require a paid AI API for the lexical analyzer, token table, core deterministic checks, or basic sample examples to work.

---

# PART 17 — FINAL ACCEPTANCE CRITERIA

The project is complete only when the following conditions have been addressed:

1. The original VS Code-style SecureLex identity and layout are preserved and polished.
2. The primary token table is populated by the actual lexer.
3. Python, Java, C/C++, and JavaScript use the correct language configuration.
4. Token types, locations, validity and counts are accurate for tested examples.
5. Syntax diagnostics and security findings are separate from lexical validity.
6. AST information comes from a real parser.
7. Security results come from actual configured rules or analyzers.
8. AI code generation uses the real configured provider and reports failures honestly.
9. AI fixes are reviewable, validated and reversible.
10. An independent Verifier Agent reviews fixed code alongside deterministic re-analysis and available tests.
11. Remaining issues, new issues, unresolved checks and verification limitations are visible.
12. The Agent Safety Lab performs real, controlled evaluations rather than displaying fixed success messages.
13. Every visible button, icon action, tab, export control and navigation item has a defined, tested behavior or an explicitly disabled/unavailable state.
14. No misleading success messages, fake model responses, hardcoded result counters or unsupported security guarantees remain.
15. The backend is protected against arbitrary code execution, prompt injection through untrusted content, unrestricted agent tools and unsafe model-generated patches.
16. The README and tests make the project understandable and reproducible.

Do not try to achieve these criteria through a UI-only simulation.

Implement the highest-value end-to-end path first:

**Write code → Analyze tokens → Inspect findings → Ask AI to explain → Propose a fix → Review diff → Apply patch → Independent verification → Inspect final results.**

Then complete the remaining language support, safety scenarios, exports, advanced views and testing.

If a required capability cannot be completed in the current environment, do not fake it. Implement the interface and adapter boundary where useful, document the precise blocker, and mark the capability accurately.

At the end, summarize the actual implementation, files changed, tests run and passed, tool availability, remaining limitations, and instructions for running the application. Do not claim untested functionality works.

## Final product identity

SecureLex should feel like a real developer IDE with a powerful lexical-analysis engine at its center.

**Every token must be understandable. Every finding must have evidence. Every AI fix must be reviewable. Every successful verification claim must be supported by checks that actually ran. And every advanced feature must remain accessible without making the experience complicated for beginners.**
