# UI-3 token security data audit

Audited `docs/api_samples/analyze_python.json` and `analyze_java.json` (the only full analyze responses in this directory) and compared their shapes with `AnalysisResult`/`TokenInfo` and Finding models.

## Fields present in each sample token

| Field | Meaning / observed values |
|---|---|
| `token` | Exact source lexeme as text. |
| `token_type` | Lexer-emitted kind. Python observed `COMMENT`, `DEDENT`, `IDENTIFIER`, `INDENT`, `KEYWORD`, `NEWLINE`, `OPERATOR`, `STRING`, `WHITESPACE`; Java observed `IDENTIFIER`, `KEYWORD`, `OPERATOR`, `PUNCTUATION`, `STRING`, `WHITESPACE`. |
| `range` | `{start_line,start_col,end_line,end_col}`, 1-based UTF-16, end-exclusive. |
| `label` | Per-token fused label (`SAFE` in these samples; the schema allows `SUSPICIOUS` / `MALICIOUS`). |
| `score` | Per-token fused score, numeric. It is not a probability vector. |

Not present on tokens: independent `kind` alias, `line`/`column` aliases (coordinates are in `range`), recovered text, Unicode script/code-point/mixed-script/confusable metadata, per-token three-class probabilities, or feature-group evidence. No backend change is needed: ranges, source text, finding evidence and taint steps supply the UI derivations; selected-token probabilities remain an on-demand `/api/ml/insights` request. Finding-level `evidence` may include Unicode evidence, while `taint_path` carries `step`, `range`, `text`, and `note`.

## UI-derived fields

`web/src/tokens/derive.ts` derives a normalized text/kind/range view, broad lexical type, overlapping taint/rule/Unicode relationships, role, severity, detectors, categories via the Problems panel CWE map, related finding IDs, and the security-relevant flag. Unicode recovered spelling and script facts are explicitly unavailable unless present in finding evidence; the panel never invents them. Control, format, and line-separator characters are rendered as visible `<U+XXXX>` markers.

## Kind mapping

The observed Python and Java API kinds are mapped to Keyword, Identifier, String, Operator, Delimiter, Comment, Whitespace, Newline, Indent, and Dedent. `PUNCTUATION` maps to Delimiter. `NUMBER` and `ERROR` map to Number and Error when emitted. A representative direct lexer audit (not an API sample) additionally observed JavaScript `NUMBER` and C/C++ `PREPROCESSOR`; `PREPROCESSOR` maps to Other because no preprocessor category is in the requested type set. An unfamiliar kind maps to Other. For JavaScript and C/C++, `docs/api_samples/` has no analyze response, so the lexer audit cannot be described as response-sample coverage. Add real responses here when the API sample set is expanded.
