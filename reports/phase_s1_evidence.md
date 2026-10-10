# S-1 Python Sample Catalogue Evidence

Historical S-1 record. The catalogue was verified using the in-process Analyzer by `scripts/verify_samples.py` before Java and JavaScript rows were added.

- Manifest entries: 41 Python samples.
- Shipped: 40; pending with reason: 1 (`py-a01`, helper-parameter taint propagation).
- All 40 shipped Python samples passed the S-1 verifier.
- `ruff check .` passed; the S-1 isolated catalogue tests passed (3 tests).
- Full-suite pytest had Windows `WinError 5` failures creating temporary directories/named pipes in unrelated C++/JavaScript/Trojan Source/ML tests; it was not a clean full-suite run.
- Python API smoke returned 44 records (40 catalogue plus 4 legacy), preserved legacy sample fields, omitted source when metadata was requested, and provided detail/404 behavior.
- The verifier checks expected findings and line tolerance, declared taint paths, clean examples, verified fixes, safe-fix removal, and fix-all idempotence.

## Pending

- `py-a01`: Request-derived data is not propagated through a helper parameter into `os.system`; no expected finding or verified fix is produced.

## Python verification matrix

| ID | Level | Title | Expected rules | Status | Time | Fix confidence |
|---|---|---|---|---|---:|---|
| py-b01 | basic | Evaluate Console Expression | APS-PY-INJ-001 | PASS | 0.038s | review |
| py-b02 | basic | Execute Supplied Script | APS-PY-INJ-001 | PASS | 0.015s | manual, expected:review |
| py-b03 | basic | Ping a Supplied Host | APS-PY-INJ-002 | PASS | 0.020s | review |
| py-b04 | basic | Look Up a User | APS-PY-INJ-004 | PASS | 0.022s | review |
| py-b05 | basic | Restore a Socket Message | APS-PY-DES-001 | PASS | 0.020s | manual |
| py-b06 | basic | Read a YAML Configuration | APS-PY-DES-002 | PASS | 0.022s | safe |
| py-b07 | basic | Create a Password Digest | APS-PY-CRY-001 | PASS | 0.022s | safe |
| py-b08 | basic | Configure Service Credentials | APS-PY-SEC-001 | PASS | 0.021s | manual, expected:review |
| py-b09 | basic | Fetch a Status Page | APS-PY-NET-001 | PASS | 0.021s | safe |
| py-b10 | basic | Generate a Session Code | APS-PY-CRY-002 | PASS | 0.020s | review, expected:safe |
| py-i01 | intermediate | Flask Host Diagnostics | APS-PY-INJ-002 | PASS | 0.050s | review |
| py-i02 | intermediate | Flask Account Search | APS-PY-INJ-004 | PASS | 0.049s | review |
| py-i03 | intermediate | Run a Host Check | APS-PY-INJ-003 | PASS | 0.043s | review |
| py-i04 | intermediate | Open an Uploaded Report | APS-PY-IO-001 | PASS | 0.049s | review |
| py-i05 | intermediate | Render a Greeting | APS-PY-XSS-001 | PASS | 0.047s | review |
| py-i06 | intermediate | Django Maintenance View | APS-PY-INJ-003 | PASS | 0.045s | review |
| py-i07 | intermediate | Load a Requested Plugin | APS-PY-INJ-005 | PASS | 0.037s | none |
| py-i08 | intermediate | Restore a Submitted Session | APS-PY-DES-001 | PASS | 0.033s | manual |
| py-i09 | intermediate | Issue a Session Identifier | APS-PY-CRY-001, APS-PY-CRY-002 | PASS | 0.047s | manual, safe |
| py-a02 | advanced | Select a Diagnostic Target | APS-PY-INJ-002 | PASS | 0.107s | review |
| py-a03 | advanced | Build a Multi-Stage Task | APS-PY-INJ-002 | PASS | 0.108s | review |
| py-a04 | advanced | Decode a Harmless Message | APS-PY-OBF-001 | PASS | 0.069s | manual |
| py-a05 | advanced | Unpack a Harmless Notice | APS-PY-OBF-001 | PASS | 0.075s | manual |
| py-a06 | advanced | Small Flask Service Review | APS-PY-CRY-001, APS-PY-DES-001, APS-PY-INJ-002, APS-PY-INJ-004, APS-PY-NET-001, APS-PY-SEC-001 | PASS | 0.336s | manual, review, safe |
| py-a07 | advanced | Process a Submitted Archive Name | APS-PY-DES-002, APS-PY-INJ-003, APS-PY-IO-001 | PASS | 0.137s | manual, review, safe |
| py-a08 | advanced | Quote the Wrong Value | APS-PY-INJ-002 | PASS | 0.100s | review |
| py-s01 | safe | Run a Fixed Argument List | — | PASS | 0.023s | none |
| py-s02 | safe | Quote a Search Term | — | PASS | 0.021s | none |
| py-s03 | safe | Search with a Bound Parameter | — | PASS | 0.018s | none |
| py-s04 | safe | Load Trusted Configuration | — | PASS | 0.032s | none |
| py-s05 | safe | Convert a Port to an Integer | — | PASS | 0.020s | none |
| py-s06 | safe | Security Terms in Documentation | — | PASS | 0.017s | none |
| py-s07 | safe | Clean Service Module | — | PASS | 0.037s | none |
| py-u01 | unicode | Review a Bidi-Controlled Comment | APS-ALL-UNI-001 | PASS | 0.019s | safe |
| py-u02 | unicode | Find an Invisible Name Character | APS-ALL-UNI-002 | PASS | 0.017s | manual, expected:safe |
| py-u03 | unicode | Inspect Hidden Tag Text | APS-ALL-UNI-003 | PASS | 0.020s | safe |
| py-u04 | unicode | Inspect a Disguised Exec Call | APS-ALL-UNI-006, APS-PY-INJ-001 | PASS | 0.022s | manual, safe, expected:review |
| py-u05 | unicode | Inspect a Fullwidth Eval Call | APS-ALL-UNI-006 | PASS | 0.027s | review, safe |
| py-u06 | unicode | Review a Mixed-Script Name | APS-ALL-UNI-004 | PASS | 0.018s | manual, expected:safe |
| py-l01 | lexer | Exercise Python Lexer Forms | — | PASS | 0.033s | none |
| py-a01 | advanced | Dispatch a Diagnostic Job | APS-PY-INJ-002 | PENDING | -- | -- |

## Sample gaps

- `py-a01`: Current Python taint analysis does not carry request-derived data through a helper function parameter into os.system; no expected finding or verified fix is produced.
