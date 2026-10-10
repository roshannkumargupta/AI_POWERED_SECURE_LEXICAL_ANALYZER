# UI-6: token-first review workspace

UI-6 turns the UI-5 shell into a file-oriented review workspace. The icon strip stays visible while Files, Samples, or Help opens as a 300 px overlay. Files and Samples are separate panels; `Ctrl+B` reopens the last panel, and Escape or an outside click closes it. Samples stay scoped to the selected language unless the user expands the language list. The two Python target demos appear first.

## Flyouts and open files

Files contains New, Open, Open folder, currently open files, close controls, and Save/Download. Opening a sample creates a new editable document. Opening a folder filters to supported source extensions and caps the imported list at 200 entries. When at least two documents are open, tabs appear above Monaco. The file pill in the top bar offers document switching and closing. Unsaved edits are marked in the file list and tabs, and closing a dirty document asks before discarding it.

## Selection and token table

The adapter merges dotted and namespaced call names while keeping the underlying lexer token IDs. The real HTML table defaults to security findings and lexical errors; Show all tokens reveals all non-whitespace lexemes. The fixed 13/31/17/18/21 column widths match the requested layout. Lists over 200 visible rows use a windowed table. The first chip group is one choice; the dangerous, suspicious, and malicious group is multi-select. A row selects the same source range in Monaco; moving the Monaco cursor selects its matching row or clears the table selection for a safe token. Cursor feedback is debounced by 50 ms and programmatic selection is guarded to avoid loops.

Lexical details list raw token kinds, text, and locations for merged lexemes. Unicode code points use visible `<U+XXXX>` markers. API-derived strings are rendered as React text, so markup-like lexemes remain literal.

## Why the UI shows only engine output

Security badges, lexical and syntax diagnostics, taint steps, ATT&CK tags, parser metadata, ML probabilities, and fix verification come from the analyzer response or its dedicated endpoint. A critical/high static finding is grouped as Dangerous; the Malicious filter is reserved for findings carrying an ATT&CK tag. ML-off screens never show probabilities. The Help panel states the parser boundary directly: Python AST, lexer-only for the other languages. This UI does not invent a taint path, parser result, model probability, or ML-off reason when the API did not return it.

Apply fix revalidates changed source, then calls `/api/fix`, applies the returned source through Monaco's undoable edit path, and starts a new analysis. Fix all calls `/api/fix-all` with review fixes disabled. Existing backend verification remains authoritative.

## Viva questions

1. **Why use both raw lexer tokens and merged rows?** The merged row makes a call such as `os.system` readable and selectable as one lexeme; raw token IDs preserve the exact lexer evidence and source range.
2. **How does selection stay in sync without a loop?** Monaco cursor changes are debounced; React-originated selections carry an expected cursor position that the cursor listener consumes once.
3. **Why are lexical errors separate from security issues?** A malformed token is a source/lexer diagnostic. The summary and score keep it separate from scored security findings.
4. **What makes a fix verified?** The backend verifier re-analyzes the proposed source and decides whether the target finding disappeared without introducing disallowed findings. The UI applies only a safe fix the API marked verified.
5. **What does ML off mean?** Rules and taint can still run, but the UI does not claim inference or display probabilities. It reports an ML-off reason only when the API supplies one.
