# Demo script

The curated, 13-step walkthrough is maintained in [docs/demo_path.md](demo_path.md). Use that file for the exact click path, two-sentence narration, and expected UI evidence at each step.

## UI-6 review walkthrough

1. Open Samples. Confirm the Python **Target Demo - Security** and **Target Demo - Lexical Error** entries appear first. Open the security demo as a new file.
2. Select `os.system` in the token table. Confirm the insecure badge, CWE and severity come from the finding, inspect the verified diff, apply it, then use Ctrl+Z to undo the one edit.
3. Select the hard-coded secret, then the Cyrillic identifier. Explain only the evidence returned by the analyzer and show invisible characters as `<U+XXXX>`.
4. Open the lexical-error demo and select its unterminated string. Confirm lexical errors are separate from the score and that ML reports `n/a` for that token.
5. Open Taint path, ML insights, and Summary. Click a taint step to jump to source; inspect ML only when the engine says it ran.
6. Use Security/Lexical/Syntax and Dangerous/Suspicious/Malicious chips, toggle Show all tokens, then use F8 and Shift+F8 to navigate visible problems.
7. Open one sample for each supported language and verify the Help panel reports Python AST and lexer-only for the other languages.
