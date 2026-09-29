# Phase 2 Evidence Report: Hand-Written Python Lexer, Security Rules, and AST Data-Flow Taint Tracking

**Date**: 2026-09-30  
**Repository**: `securelex-ide`  
**Phase**: Phase 2 Acceptance Evidence  
**Author**: Senior Software Engineer / Antigravity AI Pair  

---

## 1. Executive Summary

Phase 2 replaces the legacy prototype tokenizer and rudimentary token-window regex matcher with:
1. **A hand-written, zero-crash Python lexer state machine** (`src/apsla/languages/python_lang/lexer.py` extending `src/apsla/lexing/base.py`) that strictly maintains trivia (`"".join(t.text for t in tokens) == source`), tracks UTF-16 coordinates matching Monaco Editor, supports Python 3.12 syntax (numbers with underscores, complex `j`, hex/bin/oct, exponents, Unicode identifiers, string prefix combinations `r/b/f/u/rb/br/fr`, nested indentation stacks, and f-strings emitting a single `STRING` token with an embedded `parts` range tuple).
2. **Fourteen deterministic security rules** (`src/apsla/languages/python_lang/rules.py`) covering CWE-95, CWE-78, CWE-89, CWE-502, CWE-327, CWE-338, CWE-798, CWE-295, CWE-22, CWE-94, CWE-506, and CWE-79.
3. **Flow-sensitive AST data-flow taint analysis engine** (`src/apsla/languages/python_lang/taint.py`) tracking sources (Flask, Django, FastAPI, `sys.argv`, `input()`, `os.environ`, sockets), intra-file function summaries, loop fixed points, branching unions, sanitizers (`shlex.quote`, `int`/`float`, `html.escape`, `secure_filename`, parameterized SQL queries), and sinks.
4. **Unified CLI** (`apsla analyze`) with Rich output and taint paths.
5. **Full test suite** with 70 fixtures (31 vulnerable, 28 safe, 11 adversarial), 35 Python stdlib cross-check files, and property-based Hypothesis fuzzing.

---

## 2. Comparative Probe Results: Senior Legacy vs SecureLex (Phase 2)

Running `python scripts/legacy_probe.py` evaluates both engines across the 6 standardized baseline probes:

| # | Probe Scenario | Senior Legacy Verdict | SecureLex (Phase 2) Verdict | Architectural Assessment |
|---|---|---|---|---|
| **1** | Flask request taint to `os.system` sink (`name = request.args.get("q"); os.system("echo " + name)`) | **SAFE (0 flagged)** *(False Negative)* | **CRITICAL** (`APS-PY-INJ-002`, 4-step taint path) | Senior regex/token window split attribute access `request.args.get` and missed the source completely. SecureLex AST taint engine tracks from source through variable assignment and string concat to sink. |
| **2** | Sequential `input()` taint propagation across lines (`u = input()\n\nv = u; os.system(v)`) | `input`: SUSPICIOUS, `v`: SUSPICIOUS *(Token Window)* | **CRITICAL** (`APS-PY-INJ-002`, 4-step taint path) | Senior checked a crude window of 4 tokens. SecureLex uses flow-sensitive AST tracking across assignments and statements. |
| **3** | Sanitized input via `shlex.quote()` (`c = shlex.quote(u); os.system("echo " + c)`) | SAFE (0 flagged) | **SAFE (0 findings)** | Senior had zero concept of sanitizers. SecureLex recognizes `shlex.quote()` as a valid command injection sanitizer and suppresses the sink finding. |
| **4** | Safe list-form subprocess call (`subprocess.run(["ls", "-l"])`) | `subprocess`: **MALICIOUS (0.900)** *(False Positive)* | **SAFE (0 findings)** | Senior blindly matched the keyword `subprocess` regardless of parameters. SecureLex checks AST arguments: list of arguments without `shell=True` is verified safe. |
| **5** | Trojan Source Bidi Override character (`s = "ADM\u202e\u202dMIN"`) | **SAFE (0 flagged)** *(Blind)* | **HIGH** (`APS-ALL-UNI-001`, `APS-ALL-UNI-001`) | Senior tokenizer and validator have zero Unicode awareness. SecureLex Unicode defense layer detects bidirectional overrides before parsing. |
| **6** | Cyrillic homoglyph look-alike `exec` (`\u0435\u0445\u0435\u0441("echo 1")`) | `\u0435\u0445\u0435\u0441`: SUSPICIOUS (0.400) | **HIGH** (`APS-ALL-UNI-004`, `APS-ALL-UNI-006`, `APS-PY-INJ-001`) | Senior tagged low confidence because string had no rule. SecureLex normalizes confusables, recovers canonical `exec("echo 1")`, and triggers `APS-PY-INJ-001` (CWE-95 code injection). |

---

## 3. Verified Taint Path Demonstration

Executing the Typer CLI on `tests/fixtures/python/vulnerable/cmd_injection_flask.py`:

```bash
$ apsla analyze tests/fixtures/python/vulnerable/cmd_injection_flask.py
```

### Formatted Rich Output:
```
         APSLA Analysis: cmd_injection_flask.py (Health Score: 75/100)         
┌────────┬──────────┬──────────────┬──────────────────────────────┬─────────────────────────────────┐
│ Line   │ Severity │ Rule ID      │ Message                      │ Taint Path                      │
├────────┼──────────┼──────────────┼──────────────────────────────┼─────────────────────────────────┤
│ 2:1    │ CRITICAL │ APS-PY-INJ-… │ Command injection risk in    │ #1 L1 (source): HTTP request    │
│        │          │              │ os.system() with dynamic     │ parameter enters via            │
│        │          │              │ built command                │ 'request.args.get'              │
│        │          │              │                              │ #2 L1 (propagate): Taint        │
│        │          │              │                              │ propagated via assignment to    │
│        │          │              │                              │ 'name'                          │
│        │          │              │                              │ #3 L2 (propagate): Tainted      │
│        │          │              │                              │ concatenation / formatting      │
│        │          │              │                              │ #4 L2 (sink): Tainted command   │
│        │          │              │                              │ reaches shell execution sink    │
│        │          │              │                              │ 'os.system()'                   │
└────────┴──────────┴──────────────┴──────────────────────────────┴─────────────────────────────────┘

Summary: Critical: 1 | High: 0 | Medium: 0 | Low: 0 | Total Tokens: 24
Exit Code: 1
```

---

## 4. Test Suite and Coverage Verification

```
Name                                          Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------
src/apsla/languages/python_lang/__init__.py      48      4    92%   55, 111-112, 144
src/apsla/languages/python_lang/fixes.py          0      0   100%
src/apsla/languages/python_lang/lexer.py        297     23    92%   41, 53, 89, 109, 215, 227, 322, 339-340, 342-343, 353-355, 370, 374, 386, 393, 397, 412-414, 421-422
src/apsla/languages/python_lang/rules.py        398     24    94%   35, 41, 56, 64-66, 84, 118, 151, 191, 235, 271, 291, 322, 331-333, 367, 407, 452, 485, 525, 558, 599
src/apsla/languages/python_lang/taint.py        347     48    86%   41, 44, 78-79, 81, 93, 170-171, 252-263, 329-343, 347-354, 375-385, 392-394, 426-433, 762, 780, 785-786
src/apsla/lexing/__init__.py                      0      0   100%
src/apsla/lexing/base.py                         49      1    98%   58
src/apsla/lexing/common.py                      106     10    91%   87, 97, 112, 120, 128, 136, 150, 152, 169-170
src/apsla/lexing/token.py                        18      0   100%
src/apsla/rules/__init__.py                       0      0   100%
src/apsla/rules/base.py                          44      0   100%
src/apsla/rules/generic.py                       92      2    98%   221, 231
src/apsla/rules/registry.py                       0      0   100%
---------------------------------------------------------------------------
TOTAL                                          1399    112    92%
```

- **Total Test Cases**: 140 passed in 4.93s.
- **Line Coverage**: **92%** across all lexing, rules, and python_lang packages ($\ge 85\%$ threshold satisfied).
- **Ruff Linter**: Zero errors (`ruff check .` clean).
