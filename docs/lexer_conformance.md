# Lexer conformance results

## Scope and method

SL2-2 adds a typed public projection over the existing hand-written scanners; it does not claim standards compliance. Raw lexer tokens plus their whitespace/newline tokens are lossless, and the v2 API omits trivia from its visible token list. The Python reference suite is required to compare against `tokenize` on at least 100 standard-library files. Java, JavaScript and C/C++ are compared with tree-sitter leaf tokens when the grammar package loads, otherwise the optional native tools are reported as unavailable. Results below must be populated from an actual run of `pytest tests/unit/test_sl2_2_tokens.py` and the conformance command recorded in the evidence report.

## Accepted differences

- Whitespace and physical newline trivia are deliberately omitted from v2's visible token table; the legacy lexer stream preserves them.
- Python emits its structural `INDENT` and `DEDENT` markers for parser integration; these are not visible table tokens.
- Python `tokenize` emits encoding, end-marker, and sometimes error/indentation pseudo-tokens; the product scanner uses its own error-token recovery and does not promise identity for these markers.
- C/C++ preprocessing is currently represented by the legacy scanner as a directive token; a separate public header-name token is not yet guaranteed.
- Tree-sitter leaves may split compound lexical units differently; comparisons must report boundaries, not force parser node equivalence.

## Results (this workspace)

`python scripts/lexer_conformance.py` ran against Python 3.12.5's standard library. It compared **120 files**, **261,439 token positions** (the sum of the larger stream for each file), with mismatches in **56 files**. First examples included `_aix_support.py` (tokenize 399, product lexer 391) and `_collections_abc.py` (4,278 vs 4,216). A directly inspected mismatch is f-string granularity: standard `tokenize` emits an `f"` prefix and subsequent string/expression parts, while the current product lexer emits an entire f-string as one token. Other mismatch causes require triage; the total is not a pass claim.

The tree-sitter language pack was not installed in the active `.venv`; Java, JavaScript and C++ grammar comparisons were therefore **unavailable**, not passed. No clang/acorn fallback was exercised. Evidence is in `reports/sl2_2_evidence.md`.
