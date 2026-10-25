# S-3 catalogue evidence

Generated from `manifest.json` and actual `Analyzer` runs.
- Manifest entries: 146; shipped: 136; pending: 10.
- API sample-list source load: 0.0642s (timed via shared catalogue loader).
- Slowest shipped analysis: py-a06 at 0.671s.

## Counts by language and level

| Language | Level | Shipped | Pending |
|---|---|---:|---:|
| python | basic | 12 | 0 |
| python | intermediate | 9 | 0 |
| python | advanced | 7 | 1 |
| python | safe | 7 | 0 |
| python | unicode | 6 | 0 |
| python | lexer | 1 | 0 |
| java | basic | 9 | 0 |
| java | intermediate | 9 | 1 |
| java | advanced | 5 | 1 |
| java | safe | 6 | 0 |
| java | unicode | 2 | 1 |
| java | lexer | 1 | 0 |
| javascript | basic | 8 | 1 |
| javascript | intermediate | 9 | 0 |
| javascript | advanced | 5 | 1 |
| javascript | safe | 6 | 0 |
| javascript | unicode | 2 | 0 |
| javascript | lexer | 2 | 0 |
| cpp | basic | 8 | 1 |
| cpp | intermediate | 7 | 2 |
| cpp | advanced | 5 | 1 |
| cpp | safe | 5 | 0 |
| cpp | unicode | 2 | 0 |
| cpp | lexer | 3 | 0 |

## Pending entries

- `py-a01` (python, advanced): Current Python taint analysis does not carry request-derived data through a helper function parameter into os.system; no expected finding or verified fix is produced.
- `jv-i03` (java, intermediate): Live Analyzer (ML off and on) emits no APS-JV-XSS-001 for servlet request data written to response.getWriter().println; sample is pending until the Java reflected-XSS detector recognizes this documented sink.
- `jv-a04` (java, advanced): Live Analyzer detects five of the six specified flaws but emits no APS-JV-XSS-001 for the reflected response output; the required six-distinct-rule demo is therefore pending.
- `jv-u02` (java, unicode): Live Analyzer reports APS-JV-UNI-001 for the Java Unicode escape, while this catalogue requires the shared APS-ALL-UNI-001 ID; current sample metadata cannot represent the decoded bidi code point as a literal source character.
- `js-b03` (javascript, basic): Live Analyzer emits no APS-JS-INJ-001 for the specified constant-string setTimeout("doWork()", 100) form; kept pending rather than changing the rule expectation.
- `js-a05` (javascript, advanced): Live Analyzer reports the exec sink but provides no 3-step taint path through the runCmd helper parameter; pending until interprocedural JavaScript taint can verify the requested helper flow.
- `cp-b08` (cpp, basic): Live Analyzer emits no APS-CP-SEC-001 for the hard-coded C/C++ password comparison.
- `cp-i06` (cpp, intermediate): Live Analyzer emits no APS-CP-IO-001 for fopen(argv[1], "r").
- `cp-i07` (cpp, intermediate): Live Analyzer emits no APS-CP-MEM-002 for strncpy with sizeof(pointer) in the helper parameter.
- `cp-a04` (cpp, advanced): Live Analyzer detects four of five specified flaws but emits no APS-CP-SEC-001 for the hard-coded password; the required five-distinct-rule Fix all demo is pending.

## Senior comparison

- Samples with a senior result: 144; not run: 0.
- Vulnerable samples ours catches and senior missed: 60.
- Safe samples senior wrongly flagged: 9.
- Vulnerable samples both catch: 34.

