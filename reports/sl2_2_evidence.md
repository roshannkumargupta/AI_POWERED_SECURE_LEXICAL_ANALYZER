# SL2-2 verification evidence

Date: 2026-10-12. Python runtime: `.venv` Python 3.12.5.

## Implemented and exercised

- Added public token kind/category mapping and lexical-stage token serialization. Raw scanner output remains lossless; the API projection omits whitespace/newline and structural indentation trivia.
- Added exact source offsets in both existing UTF-16 code units and Python code points, end-exclusive ranges, token IDs, lexical status, linked diagnostic IDs and status/category summaries.
- Added supplemental Unicode diagnostics that preserve raw character representations, code points, Unicode character names, categories and bidi class; ordinary CR/LF/tab are explicitly excluded from invisible-character findings.
- Added valid, lexical-error, syntax-error, security and adversarial example files for Python, Java, C++ and JavaScript.
- Added hand-reviewed Part 4.5 C++ token fixture. The current public projection has **35** tokens; the fixture tests both the exact entries and derived count, and explicitly rejects the prototype count of 22.
- Unit tests invoke the lexical route handler's synchronous lexical branch directly for every language. A live HTTP request was not exercised because Windows event-loop socketpair creation is blocked by this environment.

## Commands and output

Focused lint command:

```text
.venv\Scripts\ruff.exe check src/apsla/models_v2.py src/apsla/lexing/diagnostics_v2.py src/apsla/server/app.py src/apsla/server/schemas.py tests/unit/test_sl2_2_tokens.py scripts/lexer_conformance.py
All checks passed!
```

Focused pytest command:

```text
.venv\Scripts\pytest.exe tests/unit/test_sl2_2_tokens.py tests/unit/test_python_lexer.py tests/unit/test_java_lexer.py tests/unit/test_cpp_lexer.py tests/unit/test_javascript_lexer.py tests/unit/test_offset_map.py -o addopts='' -q
137 passed in 13.11s
```

After adding direct route-handler coverage and the Unicode fix, rerun:

```text
.venv\Scripts\ruff.exe check src tests/unit scripts/lexer_conformance.py
All checks passed!

.venv\Scripts\pytest.exe tests/unit/test_sl2_2_tokens.py tests/unit/test_python_lexer.py tests/unit/test_java_lexer.py tests/unit/test_cpp_lexer.py tests/unit/test_javascript_lexer.py tests/unit/test_offset_map.py -o addopts='' -q
137 passed in 13.11s
```

The repository-wide `.venv\Scripts\ruff.exe check .` returned 11 errors: intentional invalid/adversarial example inputs are linted as Python source and the pre-existing root `run_tests.py` has I001. No submitted example or user-owned root script was altered to hide those findings. A first `pytest tests/unit` collection attempt failed because this project root was missing from `PYTHONPATH` for `scripts.retrain_with_feedback`; retrying with `PYTHONPATH=src;.` continued beyond two minutes without a summary and was interrupted. The selected lexer suite is the complete passing pytest claim for this phase.

Additional compatibility regression command, using an in-workspace pytest temp directory because the sandbox cannot create pytest's default temp directory:

```text
.venv\Scripts\ruff.exe check src tests/unit scripts/lexer_conformance.py
All checks passed!

.venv\Scripts\pytest.exe tests/unit/test_sl2_2_tokens.py tests/unit/test_sl2_v2.py -o addopts='' --basetemp=.pytest-temp-sl2-2 -q
287 passed in 10.21s
```

The broader unit command's first attempt produced one setup error from pytest's default `%LOCALAPPDATA%\Temp\pytest-of-...` directory creation; the in-workspace temp retry above passed the two relevant phase suites. The full unrelated unit collection remains unclaimed.

Conformance command: `.venv\Scripts\python.exe scripts/lexer_conformance.py`

```json
{
  "reference": "python tokenize",
  "stdlib_files": 120,
  "files_with_mismatch": 56,
  "token_boundaries_compared": 261439,
  "examples": [
    "_aix_support.py: tokenize=399, securelex=391",
    "_collections_abc.py: tokenize=4278, securelex=4216",
    "_osx_support.py: tokenize=2057, securelex=2051",
    "_py_abc.py: tokenize=658, securelex=628",
    "_pydatetime.py: tokenize=12058, securelex=11902",
    "_pydecimal.py: tokenize=21628, securelex=21622",
    "_pyio.py: tokenize=10121, securelex=10055",
    "_strptime.py: tokenize=2902, securelex=2894"
  ],
  "other_grammars": {
    "java": "unavailable: package not installed",
    "javascript": "unavailable: package not installed",
    "cpp": "unavailable: package not installed"
  }
}
```

Focused Python mismatch inspection found an f-string granularity difference: `tokenize` yields the prefix and string/expression pieces, while SecureLex currently emits a whole f-string token. The 56-file mismatch total includes other not-yet-triaged differences and is not represented as a conformance pass. Java, JavaScript and C++ external grammar comparisons remain unavailable.

## Remaining SL2-2 limitations

- This is not full acceptance. The legacy lexical diagnostic engine has heuristic coverage and does not yet robustly cover every requested malformed numeric form, invalid escape, invalid identifier, smart-quote delimiter, unclosed raw string/comment/character form, and three-follow-on diagnostic bound.
- Full script-property analysis (mixed scripts/look-alike detection) is not implemented. Unicode diagnostics currently give code point and Unicode name, not a formal script property.
- Existing C/C++ lexer emits `#include <...>` as one PREPROCESSOR token; separate HEADER_NAME projection is not implemented. Some contextual/language-specific token distinctions are represented only by the existing generic lexer kind.
- Live HTTP transport and full repository pytest were not run in this phase. The focused route-handler checks and selected lexer tests passed; no full-suite claim is made.
