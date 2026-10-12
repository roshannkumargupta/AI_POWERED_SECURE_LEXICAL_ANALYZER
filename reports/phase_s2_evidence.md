# S-2 Java and JavaScript Sample Evidence

Generated from manifest entries and live `Analyzer` runs by `scripts/verify_samples.py`.
The verifier checks ML off and on where the corresponding artifact is available, expected rule IDs and line tolerance, declared taint paths, clean samples, fix verification, safe-fix removal, and fix-all idempotence.
- S-2 manifest entries: Java 35/35; JavaScript 34/34.
- Shipped and passing: Java 32; JavaScript 32.
- Pending with reason: 5; Python catalogue retained separately ({'basic': 12, 'intermediate': 9, 'advanced': 8}).
- Slowest shipped sample analysis: 0.569s (limit: <2s).
- API smoke: `GET /api/samples?language=java&meta=1` and the JavaScript equivalent both returned HTTP 200, grouped by language, with 36 records each (32 shipped catalogue samples plus 4 legacy entries).
- S-2 pending entries are excluded from sample APIs and require analyzer capability or sample-format follow-up.

## Pending samples

- `jv-i03`: Live Analyzer (ML off and on) emits no APS-JV-XSS-001 for servlet request data written to response.getWriter().println; sample is pending until the Java reflected-XSS detector recognizes this documented sink.
- `jv-a04`: Live Analyzer detects five of the six specified flaws but emits no APS-JV-XSS-001 for the reflected response output; the required six-distinct-rule demo is therefore pending.
- `jv-u02`: Live Analyzer reports APS-JV-UNI-001 for the Java Unicode escape, while this catalogue requires the shared APS-ALL-UNI-001 ID; current sample metadata cannot represent the decoded bidi code point as a literal source character.
- `js-b03`: Live Analyzer emits no APS-JS-INJ-001 for the specified constant-string setTimeout("doWork()", 100) form; kept pending rather than changing the rule expectation.
- `js-a05`: Live Analyzer reports the exec sink but provides no 3-step taint path through the runCmd helper parameter; pending until interprocedural JavaScript taint can verify the requested helper flow.

## Java and JavaScript verification matrix

| ID | Language | Level | Title | Expected rules | Status | Time |
|---|---|---|---|---|---|---:|
| jv-b01 | java | basic | SQL by Concatenation | APS-JV-INJ-002 | PASS | 0.200s |
| jv-b02 | java | basic | Runtime Command from Host | APS-JV-INJ-001 | PASS | 0.160s |
| jv-b03 | java | basic | MD5 Password Digest | APS-JV-CRY-001 | PASS | 0.144s |
| jv-b04 | java | basic | SHA-1 Password Digest | APS-JV-CRY-001 | PASS | 0.131s |
| jv-b05 | java | basic | DES Encryption | APS-JV-CRY-002 | PASS | 0.221s |
| jv-b06 | java | basic | AES ECB Encryption | APS-JV-CRY-002 | PASS | 0.140s |
| jv-b07 | java | basic | Predictable Random Token | APS-JV-CRY-003 | PASS | 0.155s |
| jv-b08 | java | basic | Hard-Coded Database Password | APS-JV-SEC-001 | PASS | 0.154s |
| jv-b09 | java | basic | Deserialize a Local File | APS-JV-DES-001 | PASS | 0.105s |
| jv-i01 | java | intermediate | Servlet SQL Injection | APS-JV-INJ-002 | PASS | 0.117s |
| jv-i02 | java | intermediate | Servlet Command Injection | APS-JV-INJ-001 | PASS | 0.213s |
| jv-i04 | java | intermediate | Read a Requested File | APS-JV-IO-001 | PASS | 0.107s |
| jv-i05 | java | intermediate | Fetch a Requested URL | APS-JV-NET-001 | PASS | 0.107s |
| jv-i06 | java | intermediate | Parse Request XML | APS-JV-XML-001 | PASS | 0.156s |
| jv-i07 | java | intermediate | Spring Native Query | APS-JV-INJ-002 | PASS | 0.124s |
| jv-i08 | java | intermediate | Reflect a Requested Class | APS-JV-INJ-003 | PASS | 0.112s |
| jv-i09 | java | intermediate | Evaluate a Script Expression | APS-JV-INJ-004 | PASS | 0.139s |
| jv-i10 | java | intermediate | Trust Every TLS Certificate | APS-JV-NET-002 | PASS | 0.186s |
| jv-a01 | java | advanced | Deserialize a Network Stream | APS-JV-DES-001 | PASS | 0.108s |
| jv-a02 | java | advanced | Build SQL in a Helper | APS-JV-INJ-002 | PASS | 0.181s |
| jv-a03 | java | advanced | Validation on One Branch | APS-JV-INJ-002 | PASS | 0.198s |
| jv-a05 | java | advanced | Decode an XML Object | APS-JV-DES-001 | PASS | 0.108s |
| jv-a06 | java | advanced | Trust-All HTTPS Client | APS-JV-NET-002 | PASS | 0.259s |
| jv-s01 | java | safe | Use a PreparedStatement | — | PASS | 0.102s |
| jv-s02 | java | safe | Parse an Integer Before Query | — | PASS | 0.097s |
| jv-s03 | java | safe | Use Safe Crypto and Process APIs | — | PASS | 0.173s |
| jv-s04 | java | safe | Disable XML External Entities | — | PASS | 0.090s |
| jv-s05 | java | safe | Normalize and Check a Path | — | PASS | 0.100s |
| jv-s06 | java | safe | Clean Service Class | — | PASS | 0.091s |
| jv-u01 | java | unicode | Bidi-Controlled Comment | APS-ALL-UNI-001 | PASS | 0.068s |
| jv-u03 | java | unicode | Mixed-Script Identifier | APS-ALL-UNI-004 | PASS | 0.068s |
| jv-l01 | java | lexer | Java Lexer Showcase | — | PASS | 0.097s |
| js-b01 | javascript | basic | Evaluate User Input | APS-JS-INJ-001 | PASS | 0.105s |
| js-b02 | javascript | basic | Construct a Function | APS-JS-INJ-001 | PASS | 0.102s |
| js-b04 | javascript | basic | DOM XSS from URL Hash | APS-JS-XSS-001 | PASS | 0.108s |
| js-b05 | javascript | basic | Write the Query String | APS-JS-XSS-001 | PASS | 0.094s |
| js-b06 | javascript | basic | Predictable Session Token | APS-JS-CRY-001 | PASS | 0.103s |
| js-b07 | javascript | basic | Create an MD5 Digest | APS-JS-CRY-002 | PASS | 0.111s |
| js-b08 | javascript | basic | Hard-Coded API and JWT Secrets | APS-JS-SEC-001 | PASS | 0.140s |
| js-b09 | javascript | basic | Disable TLS Verification | APS-JS-NET-003 | PASS | 0.105s |
| js-i01 | javascript | intermediate | Express Command Injection | APS-JS-INJ-002 | PASS | 0.108s |
| js-i02 | javascript | intermediate | Express SQL Injection | APS-JS-INJ-003 | PASS | 0.118s |
| js-i03 | javascript | intermediate | Read a Requested Path | APS-JS-IO-001 | PASS | 0.091s |
| js-i04 | javascript | intermediate | Redirect to a Query URL | APS-JS-NET-001 | PASS | 0.089s |
| js-i05 | javascript | intermediate | Fetch a Requested URL | APS-JS-NET-002 | PASS | 0.091s |
| js-i06 | javascript | intermediate | Render Raw React HTML | APS-JS-XSS-002 | PASS | 0.104s |
| js-i07 | javascript | intermediate | Use an Unverified JWT | APS-JS-SEC-002 | PASS | 0.091s |
| js-i08 | javascript | intermediate | Build a User Regular Expression | APS-JS-INJ-005 | PASS | 0.100s |
| js-i09 | javascript | intermediate | Write a Message into HTML | APS-JS-XSS-001 | PASS | 0.109s |
| js-a01 | javascript | advanced | Merge Untrusted Configuration | APS-JS-INJ-004 | PASS | 0.095s |
| js-a02 | javascript | advanced | Evaluate an Inert Encoded Notice | APS-JS-OBF-001 | PASS | 0.089s |
| js-a03 | javascript | advanced | Evaluate Harmless Character Codes | APS-JS-OBF-001 | PASS | 0.094s |
| js-a04 | javascript | advanced | Express Security Review | APS-JS-CRY-001, APS-JS-INJ-002, APS-JS-INJ-003, APS-JS-IO-001, APS-JS-SEC-001, APS-JS-XSS-001 | PASS | 0.300s |
| js-a06 | javascript | advanced | Destructure a Requested Host | APS-JS-INJ-002 | PASS | 0.099s |
| js-s01 | javascript | safe | Pass Arguments to execFile | — | PASS | 0.084s |
| js-s02 | javascript | safe | Use Safe DOM APIs | — | PASS | 0.095s |
| js-s03 | javascript | safe | Bind Database Parameters | — | PASS | 0.078s |
| js-s04 | javascript | safe | Reduce a Path to its Basename | — | PASS | 0.086s |
| js-s05 | javascript | safe | Use Modern Crypto and TLS | — | PASS | 0.093s |
| js-s06 | javascript | safe | Clean Modern Module | — | PASS | 0.093s |
| js-u01 | javascript | unicode | Bidi-Controlled Comment | APS-ALL-UNI-001 | PASS | 0.094s |
| js-u02 | javascript | unicode | Cyrillic Eval Look-Alike | APS-ALL-UNI-006 | PASS | 0.125s |
| js-l01 | javascript | lexer | Templates and Slash Ambiguity | — | PASS | 0.114s |
| js-l02 | javascript | lexer | Modern JavaScript Syntax | — | PASS | 0.126s |
| jv-i03 | java | intermediate | Reflected Servlet Output | APS-JV-XSS-001 | PENDING | -- |
| jv-a04 | java | advanced | Servlet Security Review | APS-JV-CRY-001, APS-JV-INJ-002, APS-JV-IO-001, APS-JV-SEC-001, APS-JV-XML-001, APS-JV-XSS-001 | PENDING | -- |
| jv-u02 | java | unicode | Escaped Bidi Character | APS-ALL-UNI-001 | PENDING | -- |
| js-b03 | javascript | basic | Schedule a String | APS-JS-INJ-001 | PENDING | -- |
| js-a05 | javascript | advanced | Pass Host Through a Helper | APS-JS-INJ-002 | PENDING | -- |
