# SecureLex IDE User Guide

## Start checking code

The editor opens with no file selected. Choose **New file** to create an empty buffer, **Open file** to load source from your computer, or select one of the example links. Examples are copied into the editor so you can change them freely.

Use the language selector to choose Auto-detect or a supported language. Type or paste code in Monaco; use **Analyze** or Ctrl+Enter to request an analysis when the backend is available. Findings appear in Problems and the inspector panels.

## Explorer

Use the Explorer rail or Ctrl+B to show and hide the sidebar. Search within samples and use **Show all languages** to inspect samples from other language groups. The **New file** and **Open file** controls are also available in the sidebar.

## Appearance

Use the sun/moon button beside the top-right **More actions** menu to switch between dark and light. Open **Help** in the left rail and choose **Dark**, **Light**, or **System** under Appearance to set a mode explicitly. System follows your operating-system color preference. Your choice is saved in this browser and also appears as **Theme: Dark**, **Theme: Light**, **Theme: System**, and **Toggle theme** in the command palette.

## Files and keyboard shortcuts

## Samples, levels, and demo path

The SAMPLES sidebar follows the active language. With language set to Auto, expand a language group; **Show all languages** opens all language groups. Samples are grouped as Basic, Intermediate, Advanced, Safe code, Unicode, and Lexer showcase. Basic starts expanded and search covers titles, topics, summaries, and rule IDs. Selecting a sample loads it into the editable editor buffer; edits pause the expected-result comparison in Demo notes. Use the collapsed **DEMO PATH** list and its Previous/Next controls to follow the 13-step tour in [demo_path.md](demo_path.md). The [sample guide](samples_guide.md) lists catalogue entries and verification status.

- Ctrl+B: toggle Explorer
- Ctrl+N: start an empty untitled buffer
- Ctrl+O: open source files
- Ctrl+S: download the current source
- Ctrl+Enter: analyze code
- F8 / Shift+F8: move between findings

File input accepts Python, Java, JavaScript, and C/C++ source extensions up to 512 KB. Opened files are read as UTF-8. A browser warning appears when the current buffer has unsaved edits.

## Remediation and analysis

Use a finding’s quick-fix action to inspect a verified remediation. **Fix all** applies safe, verified fixes offered by the engine. The diff and analysis panels explain the result. Backend availability is required for analysis and verified fixes; the editor remains usable if the service is offline.
# UI-2 workspace notes

- Use the Problems panel severity filters and Sort menu to navigate findings; enable Group to sort findings by their CWE security category.
- The editor minimap and bracket-pair colorization are off by default to keep code readable.
- Fix all is enabled only when safe, verified fixes are available. Individual findings remain selectable from Problems.
- Finding breadcrumbs include the best-effort enclosing symbol and jump to its source location.
- Review the Summary and ML Insights tabs for aggregate and advanced evidence.
- Press Ctrl+Shift+P to search commands, samples, and language changes. Press `?` outside editable fields for keyboard help.
- The More actions menu holds Download, Keyboard shortcuts, Toggle minimap, and backend availability.
- Click the shield in the status bar for engine state details. Taint-flow steps jump to their source locations; use Show Flow in Editor to toggle the matching decorations.

## Token security inspector (UI-3)

- Open **Tokens** in the right inspector or press Ctrl+Shift+T. Security-relevant tokens are shown first; turn off **Security-relevant only** to browse the complete lexer output.
- Use Token type, Security, search, and category chips to narrow the list. Selecting a category also marks its related source-to-sink tokens in Monaco.
- Click a token to select its exact range. The detail block shows lexer kind, evidence detectors, severity, categories, CWE, related findings, and taint flow when available. Clicking in Monaco also selects and scrolls to the matching token row.
- **Token map** Off clears map marks, Security underlines only related tokens, and Full marks only the selected token. Hover marks for their role and severity.
- **Load ML evidence** fetches per-token insight only when requested. If ML is off, the inspector states that without fabricating probabilities.
- Unicode control, format, and line-separator characters are shown as `<U+XXXX>`. Recovered spellings and script facts appear only when Unicode finding evidence supplies enough data; current analyze responses do not include independent per-token recovered text or script metadata.
- Palette commands: **Show Token Security**, **Toggle Token Map**, **Next Security Token**, and **Previous Security Token**.

## UI-6 file workspace and token review

Use the always-visible strip to open Files, Samples, or Help. `Ctrl+B` toggles the last opened panel; Escape closes it. Samples show the active language, with **Show all languages** to browse the full catalogue. Each sample opens as an editable file. Open folder imports supported source files, up to 200 files.

When two or more files are open, select them from the tabs above the editor or the file pill. Unsaved files show a dot. `Ctrl+S` downloads the active file; `Ctrl+W` closes it after an unsaved-change warning.

## UI-9 Manual Analysis, Stale Results, and Fix Review

### Manual Analysis by Default
Analysis does NOT run automatically on every keystroke. It runs strictly when you click **Analyze** or press `Ctrl+Enter`. This prevents cursor jump storms and keeps editing completely responsive.
- **Analyze While Typing Setting**: If you prefer automatic analysis as you type, open **Help** in the activity strip and check **Analyze while typing**. When enabled, analysis debounces at 600 ms while respecting cursor stability. The setting is persisted in your browser's local storage.

### 5-State Document Lifecycle & Stale Detection
Each open file tracks its own lifecycle status, shown in the top bar and status bar:
1. **Not analysed**: File opened or created; press Analyze to scan.
2. **Analysing...**: Request in flight to the backend engine; previous results can be viewed.
3. **Analysed (X ms)**: Analysis is up to date; token table, findings, and fixes reflect current buffer.
4. **Edited since last analysis (Stale)**: The buffer has been edited since the last analysis run. A visible "Out of date" tag marks the token table and explanations. The **[Apply fix]** button is disabled with the tooltip *"Analyse again first"* because token ranges in the editor have shifted.
5. **Analysis error**: Server or network failure; a clear retry action is presented without blanking the workspace.

### Pinned Fix Actions, Review Fixes, and Rule Advice
- **Pinned Action Row**: The fix action row (`[Apply fix]`, fix switcher, Mark as false positive, Copy) is pinned at the bottom of the Explanation panel across all viewport resolutions.
- **Review-Level Fixes**: Fixes requiring developer oversight (e.g., parameterised queries, cryptographic algorithm migrations, environment variable secrets) show **[Apply fix]** with the diff as the review.
- **Review Fixes Modal**: When review-level fixes are present and no safe automatic fixes exist, the top bar button reads **Review fixes (M)**. Clicking it opens a modal dialog listing each review fix with its diff and a checkbox. Clicking **[Apply selected]** applies all chosen fixes in a single undoable edit group.
- **Advice for Non-Edit Rules**: For rules that cannot be mechanically repaired with safety (e.g., untrusted deserialization or memory lifetime bugs), SecureLex IDE renders a plain-language **Advice** block with a **[Copy advice]** button. The fix area is never left empty or dead.

### File Loader Hardening & Encoding Boundaries
- **512 KB Limit**: Files over 512 KB are refused upfront with a clear size warning.
- **Binary Rejection**: Files containing NUL bytes (e.g., compiled binaries or images renamed with source extensions) are refused with a human-readable message.
- **UTF-8 BOM Stripping**: Byte Order Marks (`0xEF, 0xBB, 0xBF`) are stripped on load and not re-saved.
- **Invalid UTF-8 Handling**: Files with corrupt byte sequences are opened using Unicode replacement characters (`U+FFFD`) and a non-blocking warning toast.
- **Line Ending Preservation**: Files formatted with CRLF (`\r\n`) keep CRLF line endings when saved.


Open **Help** and set **Interface size** to Compact, Reference, or Large. The choice is saved locally when browser storage is available. The workspace scales to the 768×480 design frame as the browser viewport changes. To check contrast and scrolling during a demo, open the app with `?ui7qa=1`; press `Ctrl+Shift+Alt+F9` to print a fresh browser diagnostic report.

The Tokens view lists security and lexical problems first. Turn on **Show all tokens** to inspect other non-whitespace lexemes. Select a row to jump to its source and review its explanation, fix, taint path, ML insights, or summary. ML-off and parser states describe only information returned by the engine.
