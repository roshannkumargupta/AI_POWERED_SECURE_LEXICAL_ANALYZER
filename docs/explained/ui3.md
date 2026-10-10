# UI-3: Reading the Tokens Inspector

A **token** is one unit produced by a language's lexer. Its **lexeme** is the exact text from the source that the token represents. For example, `os.system` may be an identifier lexeme with an `IDENTIFIER` kind; the kind describes its lexical class, while its text is the spelling actually present in the file.

Most tokens are neutral. A keyword, space, string, or identifier is ordinary source unless a deterministic rule, a taint path, Unicode analysis, or available ML evidence connects it to a security finding. The Tokens tab keeps that distinction visible: lexical identity is always shown, while security role and severity appear only when there is evidence.

Lexical analysis gives later security analysis reliable units and source ranges. Rules can recognize dangerous APIs, taint analysis can connect a request value through assignments to a sink, and Unicode analysis can report invisible or confusable characters. The inspector overlays those finding relationships on exact token ranges, so a developer can move from the spelling in the editor to the evidence and back.

The analyzer returns token text, lexer kind, UTF-16 source range, fused label, and score. Finding responses provide the rule, severity, taint steps, and any Unicode evidence. Per-token probability details are fetched on demand. The current API samples do not include recovered token text or script/code-point metadata; the UI labels that data unavailable rather than manufacturing it.

## Viva questions

1. **What is the difference between a token and a lexeme?** A token is the lexer’s classified unit; a lexeme is the exact source text for that unit.
2. **Why are most tokens shown as neutral?** Their presence alone is not a security signal. A security role needs evidence tying the token range to a rule, taint step, Unicode finding, or ML result.
3. **How does lexical analysis help taint analysis?** Stable token boundaries and source ranges let the analyzer identify inputs, propagation, and dangerous sinks and show where each occurs.
4. **Why are token ranges end-exclusive and UTF-16 based?** That coordinate convention matches Monaco’s positions, including columns around non-BMP characters.
5. **Why does a token show no recovered Unicode spelling?** The current analyze response contains token spelling and finding evidence but no per-token recovered spelling or script metadata; the UI only reports fields the API supplied.
