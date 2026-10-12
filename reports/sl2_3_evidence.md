# SL2-3 syntax, AST and semantic-tool evidence

Date: 2026-10-12. Tests ran with the project `.venv` (Python 3.12.5).

## Tree-sitter API probe

Executed with `$env:PYTHONPATH='src'` and `.venv\Scripts\python.exe`. The probe used `Language(module.language())`, `Parser(language)`, and `parser.parse(source.encode())` on the installed API:

```text
tree-sitter 0.26.0
python loaded module error False children 1 field-api True
 node api [('start_byte', True), ('end_byte', True), ('is_error', True), ('is_missing', True), ('children', True), ('named_children', True), ('child_count', True), ('parent', True), ('id', True)]
java loaded program error False children 1 field-api True
 node api [('start_byte', True), ('end_byte', True), ('is_error', True), ('is_missing', True), ('children', True), ('named_children', True), ('child_count', True), ('parent', True), ('id', True)]
javascript loaded program error False children 1 field-api True
 node api [('start_byte', True), ('end_byte', True), ('is_error', True), ('is_missing', True), ('children', True), ('named_children', True), ('child_count', True), ('parent', True), ('id', True)]
cpp loaded translation_unit error False children 1 field-api True
 node api [('start_byte', True), ('end_byte', True), ('is_error', True), ('is_missing', True), ('children', True), ('named_children', True), ('child_count', True), ('parent', True), ('id', True)]
```

The API exposes UTF-8 byte spans, so the adapter maps byte boundaries back through the original Unicode source into one-based UTF-16 editor ranges. Python first uses `ast.parse`; on `SyntaxError`/indentation failure it returns the AST diagnostic plus a tree-sitter recovery tree when the grammar loads.

## Implemented

- Added `src/apsla/parsing_v2.py`: parser loader/status, Python AST and partial fallback, tree-sitter Java/JavaScript/C++ parsing, ERROR/MISSING diagnostics with context, UTF-16 ranges, AST node IDs/fields/parents/children/previews/token links/overlapping diagnostic IDs, configurable bounds, truncation marker, and child expansion lookup.
- `POST /api/analyze/syntax` accepts `include_ast`, `ast_max_depth`, and `ast_max_nodes`. `GET /api/ast/{analysis_id}/node/{node_id}` expands a retained node while enforcing limits. AST cache is bounded to 24 analyses.
- Added independent lexical/syntax/semantic dimensions to v2 results and stage responses. Syntax parser success is explicitly not semantic correctness.
- Added optional static-tool profiles for Ruff F rules, pyflakes, mypy, `g++`/`clang++` with syntax-only/standard/error/color flags, javac with annotation processing disabled and public class filename selection, Node `--check`, and eslint no-undef/no-unused-vars. Output adapters emit unified semantic diagnostics.
- Static tool execution is fail-closed on this host because no OS-enforced network-isolated subprocess sandbox is configured. Tools found on PATH are reported in capability metadata; attempted stage checks report `unavailable` with `Check unavailable: <tool>` guidance and make semantic status incomplete. No submitted program was executed.
- Regenerated `docs/api_v2.md` and the OpenAPI golden schema for the syntax and AST API additions.

## Actual tool detection

The executed probe called `detect_tool` for each name; results:

```text
g++: available=False; status=unavailable; version=None; reason='Executable could not start (OSError); check runtime libraries and PATH.'
clang++: available=False; status=unavailable; version=None; reason='Install the tool and make it available on PATH.'
javac: available=False; status=unavailable; version=None; reason='Install the tool and make it available on PATH.'
node: available=True; status=ok; version='v24.11.1'; reason=None
ruff: available=True; status=ok; version='ruff 0.16.8'; reason=None
pyflakes: available=False; status=unavailable; version=None; reason='Install the tool and make it available on PATH.'
mypy: available=False; status=unavailable; version=None; reason='Install the tool and make it available on PATH.'
eslint: available=False; status=unavailable; version=None; reason='Install the tool and make it available on PATH.'
```

The repository environment notes a project-venv mypy installation, but this actual process `PATH` probe could not locate it. The endpoint uses actual `ToolStatus` discovery, not the earlier environment note.

## Verification

Executed:

```text
.venv\Scripts\ruff.exe check src tests/unit scripts/lexer_conformance.py
All checks passed!

.venv\Scripts\pytest.exe tests/unit/test_sl2_3_parsing.py tests/unit/test_sl2_2_tokens.py tests/unit/test_sl2_v2.py tests/unit/test_phase15_parsers.py -o addopts='' --basetemp=.pytest-temp-sl2-3 -q
374 passed in 12.25s
```

The tests cover valid and malformed programs in all four languages, Python AST fallback, delimiter/terminator diagnostics, schema/API paths, AST links/ranges/limits/on-demand expansion, emoji UTF-16 ranges, source-valid lexical status despite syntax errors, missing PATH tools, compiler/tool output parsing, javac filename selection, tool timeout/failure, existing SL2-1 contracts, and the existing parser regression suite.

The test suite invokes the syntax handler directly (without socket-based HTTP transport) because Windows asyncio socketpair creation is blocked in this sandbox. OpenAPI confirms the route contracts, but a live HTTP request is not claimed. External semantic checks were unavailable under the fail-closed subprocess policy, so their real diagnostics were not exercised on this machine. These limitations do not change the passing selected test result.
