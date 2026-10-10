# UI-5: dark inspection workspace

UI-5 puts the editor, token inspector, taint path, model insights, and summary into one compact shell. The editor stays the main work area. A narrow strip opens files or samples, the right pane contains four analysis views, and the bottom explanation area follows the selected finding.

## Design tokens

The dark surfaces are `#151515`, `#1A1A19`, and `#20201F`. Borders use translucent white. Text has primary, secondary, muted, and blue accent colors. Green communicates safe or verified, amber communicates valid but insecure, and red communicates errors. Each status also has a text label. Monaco uses a 13 px monospace face with a 24 px line height; tables use compact 12 px text.

## Why the UI derives token status

The lexer reports token kind and position. The analyzer reports findings with a primary source range and may separately report the source and propagation steps of a taint path. `adapt.ts` joins these records by range so that only the sink, secret literal, or confusable identifier is marked insecure. Source and propagation tokens remain ordinary valid tokens and are described in the taint view. This keeps the engine focused on detection and lets the UI present one consistent token table across languages.

The adapter is tolerant of older payloads and unknown token kinds. It maps unknown kinds to `OTHER`, keeps raw token IDs for merged calls, and renders control or bidi characters using visible `<U+XXXX>` markers. React text nodes escape code text before display.

## Lexical, syntax, and security findings

- A lexical finding describes a malformed token or unterminated construct.
- A syntax finding describes a parser rejecting the file. Python uses `ast.parse`; the other supported plugins currently report lexer-only parser metadata.
- A security finding describes a risky behavior such as command injection. These findings continue to determine the health score. Lexical and syntax diagnostics are counted separately and do not change the score formula.

The malformed UI-5 Python demo is detected by Python's lexer as a `STRING`, rather than `ERROR`, and `ast.parse` then rejects the file. The additive diagnostic recognizes this unterminated string token. Since AST parsing fails, taint analysis cannot return the earlier request-to-command path for this malformed file. The separate valid security demo retains its taint path.

## Viva questions

1. **Why does the UI have an adapter?** It converts language-specific token kinds and analyzer findings into a stable table model without making detection rules depend on presentation.
2. **Why is a taint source not colored insecure?** It identifies untrusted input, while the primary finding range identifies where that input reaches a risky operation.
3. **How are merged calls traced back to tokens?** Each merged row preserves the IDs of all raw lexer tokens that formed the call.
4. **Why are lexical and syntax errors not included in the health score?** They describe code validity and parser capability; the score continues to measure security findings under its existing formula.
5. **Why is the lexical demo's taint path missing?** Python AST parsing rejects the malformed file, preventing its AST-based taint analyzer from building the path.
