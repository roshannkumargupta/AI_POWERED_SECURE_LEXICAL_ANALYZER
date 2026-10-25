# Public token types and position contract

The raw lexer stream remains lossless and includes whitespace/newline trivia. The v2 token table projection omits trivia (including structural `INDENT`/`DEDENT` markers); the source and raw lexer stream remain available internally. Public token ranges are half-open. Human lines and columns are 1-based; columns and offsets in the existing lexer are UTF-16 code units, while `start_offset_codepoint` and `end_offset_codepoint` are zero-based Python Unicode code-point offsets. End positions are exclusive. CRLF is two source code points and one logical line break.

| Raw lexer kind / shape | Public `token_type` | `category` |
|---|---|---|
| KEYWORD, contextual/reserved keyword kinds | `KEYWORD` | `Keyword` |
| IDENTIFIER, NAME | `IDENTIFIER` | `Identifier` |
| OPERATOR except punctuation delimiters | `OPERATOR` | `Operator` |
| NUMBER, INTEGER, FLOAT | `NUMBER_LITERAL` | `Literal` |
| STRING | `STRING_LITERAL` | `Literal` |
| Python prefixed f-string (`f'…'`, `F"…"`) | `F_STRING` | `Literal` |
| Java/C/C++ single-quoted character token | `CHAR_LITERAL` | `Literal` |
| Java text block | `TEXT_BLOCK` | `Literal` |
| JavaScript template parts | `TEMPLATE_LITERAL` | `Literal` |
| JavaScript regular-expression token | `REGEX_LITERAL` | `Literal` |
| COMMENT, LINE_COMMENT, BLOCK_COMMENT, SHEBANG | `COMMENT` | `Comment` |
| PREPROCESSOR / directive | `PREPROCESSOR` | `Preprocessor` |
| Header-name kind when emitted separately | `HEADER_NAME` | `Header` |
| ANNOTATION | `ANNOTATION` | `Language-specific` |
| punctuation delimiters and braces/parens/brackets/separators | `DELIMITER` | `Delimiter` |
| ERROR / invalid character | `INVALID_TOKEN` | `Invalid` |
| other named language-specific kinds | `LANGUAGE_<KIND>` | `Language-specific` |

The mapper is implemented by `token_type_for` in `src/apsla/models_v2.py`. The pre-existing scanners do not all expose every distinguishable grammar form as a separate lexer kind (notably C/C++ header names and some language-specific literal subforms); those remain explicitly documented gaps rather than inferred semantic claims. Token IDs are stable for the same analysis id and token order, not across changed source versions.

Lexical status is independent of parser status. Only lexical diagnostics or an explicit invalid token can mark a public token invalid. An unclassified kind remains named and is not silently security-labelled. The current backend diagnostic engine is heuristic; it does not yet implement the full Unicode/script/bidi diagnostic contract.
