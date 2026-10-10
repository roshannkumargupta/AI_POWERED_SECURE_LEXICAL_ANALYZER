# UI-9 Fix Coverage Audit Report

Generated from automated analysis of all shipped samples across Python, Java, JavaScript, and C/C++.

## 1. Summary Statistics

- **Total Finding Instances Audited**: 182
- **Findings with Fix Proposals**: 128 (70.3%)
- **Findings with Automatic Code Edits**: 88 (48.4%)
- **Verified Fixes (Syntax + Regression Checked)**: 88 (48.4%)
- **Effective Fixes (Removes Finding on Re-analysis)**: 88 (48.4%)

## 2. Per-Sample Finding and Fix Matrix

| Sample ID | Lang | Rule ID | Line | Fix Exists | Kind | Confidence | Verified | Edit Present | Re-analysis Effective |
|---|---|---|---|---|---|---|---|---|---|
| `py-b01` | python | `APS-PY-INJ-001` | 2 | Yes | rule | review | True | Edit | Removes finding |
| `py-b02` | python | `APS-PY-INJ-001` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-b03` | python | `APS-PY-INJ-002` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `py-b04` | python | `APS-PY-INJ-004` | 4 | Yes | rule | review | True | Edit | Removes finding |
| `py-b05` | python | `APS-PY-DES-001` | 5 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-b06` | python | `APS-PY-DES-002` | 3 | Yes | rule | safe | True | Edit | Removes finding |
| `py-b07` | python | `APS-PY-CRY-001` | 3 | Yes | rule | safe | True | Edit | Removes finding |
| `py-b08` | python | `APS-PY-SEC-001` | 1 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-b08` | python | `APS-PY-SEC-001` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-b09` | python | `APS-PY-NET-001` | 3 | Yes | rule | safe | True | Edit | Removes finding |
| `py-b10` | python | `APS-PY-CRY-002` | 2 | Yes | rule | review | True | Edit | Removes finding |
| `py-i01` | python | `APS-PY-INJ-002` | 9 | Yes | rule | review | True | Edit | Removes finding |
| `py-i02` | python | `APS-PY-INJ-004` | 10 | Yes | rule | review | True | Edit | Removes finding |
| `py-i03` | python | `APS-PY-INJ-003` | 4 | Yes | rule | review | True | Edit | Removes finding |
| `py-i04` | python | `APS-PY-IO-001` | 8 | Yes | rule | review | True | Edit | Removes finding |
| `py-i05` | python | `APS-PY-XSS-001` | 8 | Yes | rule | review | True | Edit | Removes finding |
| `py-i06` | python | `APS-PY-INJ-003` | 5 | Yes | rule | review | True | Edit | Removes finding |
| `py-i07` | python | `APS-PY-INJ-005` | 8 | No | — | manual | False | Advice only | N/A (advice) |
| `py-i08` | python | `APS-PY-DES-001` | 8 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-i09` | python | `APS-PY-CRY-002` | 5 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-i09` | python | `APS-PY-CRY-001` | 6 | Yes | rule | safe | True | Edit | Removes finding |
| `py-a02` | python | `APS-PY-INJ-002` | 12 | Yes | rule | review | True | Edit | Removes finding |
| `py-a03` | python | `APS-PY-INJ-002` | 12 | Yes | rule | review | True | Edit | Removes finding |
| `py-a04` | python | `APS-PY-OBF-001` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `py-a04` | python | `APS-PY-INJ-001` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-a05` | python | `APS-PY-OBF-001` | 5 | No | — | manual | False | Advice only | N/A (advice) |
| `py-a05` | python | `APS-PY-INJ-001` | 5 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-a06` | python | `APS-PY-INJ-002` | 25 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-a06` | python | `APS-PY-DES-001` | 30 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-a06` | python | `APS-PY-SEC-001` | 9 | Yes | rule | review | True | Edit | Removes finding |
| `py-a06` | python | `APS-PY-INJ-004` | 20 | Yes | rule | review | True | Edit | Removes finding |
| `py-a06` | python | `APS-PY-CRY-001` | 36 | Yes | rule | safe | True | Edit | Removes finding |
| `py-a06` | python | `APS-PY-NET-001` | 40 | Yes | rule | safe | True | Edit | Removes finding |
| `py-a07` | python | `APS-PY-INJ-003` | 10 | Yes | rule | review | True | Edit | Removes finding |
| `py-a07` | python | `APS-PY-IO-001` | 7 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-a07` | python | `APS-PY-DES-002` | 8 | Yes | rule | safe | True | Edit | Removes finding |
| `py-a08` | python | `APS-PY-INJ-002` | 9 | Yes | rule | review | True | Edit | Removes finding |
| `py-u01` | python | `APS-ALL-UNI-001` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u01` | python | `APS-ALL-UNI-001` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u01` | python | `APS-ALL-UNI-001` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u02` | python | `APS-PY-SYN-001` | 1 | No | — | manual | False | Advice only | N/A (advice) |
| `py-u02` | python | `APS-ALL-UNI-002` | 1 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-u02` | python | `APS-ALL-UNI-002` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-u02` | python | `APS-PY-LEX-003` | 1 | No | — | manual | False | Advice only | N/A (advice) |
| `py-u02` | python | `APS-PY-LEX-003` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `py-u03` | python | `APS-ALL-UNI-003` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u03` | python | `APS-ALL-UNI-003` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u03` | python | `APS-ALL-UNI-003` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u03` | python | `APS-ALL-UNI-003` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u03` | python | `APS-ALL-UNI-003` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u03` | python | `APS-ALL-UNI-003` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u04` | python | `APS-PY-INJ-001` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-u04` | python | `APS-ALL-UNI-006` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u04` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u04` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u04` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u04` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u05` | python | `APS-PY-INJ-001` | 2 | Yes | rule | review | True | Edit | Removes finding |
| `py-u05` | python | `APS-ALL-UNI-006` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u05` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u05` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u05` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u05` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `py-u06` | python | `APS-ALL-UNI-004` | 1 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-u06` | python | `APS-ALL-UNI-005` | 1 | No | — | manual | False | Advice only | N/A (advice) |
| `py-u06` | python | `APS-ALL-UNI-004` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-u06` | python | `APS-ALL-UNI-005` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `py-ui5-security` | python | `APS-PY-INJ-002` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-ui5-security` | python | `APS-ALL-UNI-006` | 5 | Yes | rule | safe | True | Edit | Removes finding |
| `py-ui5-security` | python | `APS-PY-INJ-001` | 5 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-ui5-security` | python | `APS-ALL-UNI-004` | 5 | Yes | rule | safe | True | Edit | Removes finding |
| `py-ui5-security` | python | `APS-ALL-UNI-004` | 5 | Yes | rule | safe | True | Edit | Removes finding |
| `py-ui5-security` | python | `APS-ALL-UNI-004` | 5 | Yes | rule | safe | True | Edit | Removes finding |
| `py-ui5-security` | python | `APS-ALL-UNI-004` | 5 | Yes | rule | safe | True | Edit | Removes finding |
| `py-ui5-lexical` | python | `APS-PY-LEX-001` | 5 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `py-ui5-lexical` | python | `APS-PY-SYN-001` | 5 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-b01` | java | `APS-JV-INJ-002` | 21 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-b02` | java | `APS-JV-INJ-001` | 20 | Yes | template | review | True | Edit | Removes finding |
| `jv-b03` | java | `APS-JV-CRY-001` | 19 | Yes | rule | safe | True | Edit | Removes finding |
| `jv-b04` | java | `APS-JV-CRY-001` | 19 | Yes | rule | safe | True | Edit | Removes finding |
| `jv-b05` | java | `APS-JV-CRY-002` | 19 | Yes | rule | manual | True | Edit | Removes finding |
| `jv-b06` | java | `APS-JV-CRY-002` | 19 | Yes | rule | manual | True | Edit | Removes finding |
| `jv-b07` | java | `APS-JV-CRY-003` | 19 | Yes | template | review | True | Edit | Removes finding |
| `jv-b08` | java | `APS-JV-SEC-001` | 19 | Yes | template | review | True | Edit | Removes finding |
| `jv-b09` | java | `APS-JV-DES-001` | 19 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-i01` | java | `APS-JV-INJ-002` | 22 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-i02` | java | `APS-JV-INJ-001` | 22 | Yes | template | review | True | Edit | Removes finding |
| `jv-i04` | java | `APS-JV-IO-001` | 20 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-i05` | java | `APS-JV-NET-001` | 20 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-i06` | java | `APS-JV-XML-001` | 19 | Yes | template | review | True | Edit | Removes finding |
| `jv-i07` | java | `APS-JV-INJ-002` | 22 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-i08` | java | `APS-JV-INJ-003` | 20 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-i09` | java | `APS-JV-INJ-004` | 20 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-i10` | java | `APS-JV-NET-002` | 19 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-i10` | java | `APS-JV-NET-002` | 20 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-a01` | java | `APS-JV-DES-001` | 19 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-a02` | java | `APS-JV-INJ-002` | 22 | Yes | template | review | True | Edit | Removes finding |
| `jv-a03` | java | `APS-JV-INJ-002` | 22 | Yes | template | review | True | Edit | Removes finding |
| `jv-a05` | java | `APS-JV-DES-001` | 19 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-a06` | java | `APS-JV-NET-002` | 19 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-a06` | java | `APS-JV-NET-002` | 20 | No | — | manual | False | Advice only | N/A (advice) |
| `jv-a06` | java | `APS-JV-SEC-001` | 21 | Yes | template | review | True | Edit | Removes finding |
| `jv-u01` | java | `APS-ALL-UNI-001` | 5 | Yes | rule | safe | True | Edit | Removes finding |
| `jv-u03` | java | `APS-ALL-UNI-004` | 5 | Yes | rule | safe | True | Edit | Removes finding |
| `jv-u03` | java | `APS-ALL-UNI-005` | 5 | No | — | manual | False | Advice only | N/A (advice) |
| `js-b01` | javascript | `APS-JS-INJ-001` | 4 | Yes | rule | review | True | Edit | Removes finding |
| `js-b02` | javascript | `APS-JS-INJ-001` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-b04` | javascript | `APS-JS-XSS-001` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `js-b05` | javascript | `APS-JS-XSS-001` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-b06` | javascript | `APS-JS-CRY-001` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `js-b07` | javascript | `APS-JS-CRY-002` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `js-b08` | javascript | `APS-JS-SEC-001` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-b08` | javascript | `APS-JS-SEC-001` | 4 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-b09` | javascript | `APS-JS-NET-003` | 3 | Yes | rule | safe | True | Edit | Removes finding |
| `js-i01` | javascript | `APS-JS-INJ-002` | 6 | Yes | rule | review | True | Edit | Removes finding |
| `js-i02` | javascript | `APS-JS-INJ-003` | 5 | Yes | rule | review | True | Edit | Removes finding |
| `js-i02` | javascript | `APS-JS-SYN-001` | 5 | No | — | manual | False | Advice only | N/A (advice) |
| `js-i03` | javascript | `APS-JS-IO-001` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-i04` | javascript | `APS-JS-NET-001` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-i05` | javascript | `APS-JS-NET-002` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-i06` | javascript | `APS-JS-XSS-002` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `js-i07` | javascript | `APS-JS-SEC-002` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-i08` | javascript | `APS-JS-INJ-005` | 4 | No | — | manual | False | Advice only | N/A (advice) |
| `js-i09` | javascript | `APS-JS-XSS-001` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `js-a01` | javascript | `APS-JS-INJ-004` | 4 | No | — | manual | False | Advice only | N/A (advice) |
| `js-a02` | javascript | `APS-JS-OBF-001` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-a03` | javascript | `APS-JS-OBF-001` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-a04` | javascript | `APS-JS-INJ-002` | 4 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-a04` | javascript | `APS-JS-INJ-003` | 5 | Yes | rule | review | True | Edit | Removes finding |
| `js-a04` | javascript | `APS-JS-SYN-001` | 5 | No | — | manual | False | Advice only | N/A (advice) |
| `js-a04` | javascript | `APS-JS-IO-001` | 6 | No | — | manual | False | Advice only | N/A (advice) |
| `js-a04` | javascript | `APS-JS-XSS-001` | 7 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-a04` | javascript | `APS-JS-SEC-001` | 9 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-a04` | javascript | `APS-JS-CRY-001` | 8 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-a06` | javascript | `APS-JS-INJ-002` | 4 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-a06` | javascript | `APS-JS-SYN-001` | 4 | No | — | manual | False | Advice only | N/A (advice) |
| `js-u01` | javascript | `APS-ALL-UNI-001` | 1 | Yes | rule | safe | True | Edit | Removes finding |
| `js-u02` | javascript | `APS-JS-INJ-001` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-u02` | javascript | `APS-ALL-UNI-006` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-u02` | javascript | `APS-ALL-UNI-006` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-u02` | javascript | `APS-ALL-UNI-004` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-u02` | javascript | `APS-ALL-UNI-005` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `js-u02` | javascript | `APS-ALL-UNI-004` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `js-u02` | javascript | `APS-ALL-UNI-005` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `js-l01` | javascript | `APS-JS-SYN-001` | 1 | No | — | manual | False | Advice only | N/A (advice) |
| `js-l02` | javascript | `APS-JS-SYN-001` | 6 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-b01` | cpp | `APS-CP-MEM-001` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `cp-b02` | cpp | `APS-CP-MEM-001` | 2 | Yes | rule | review | True | Edit | Removes finding |
| `cp-b03` | cpp | `APS-CP-MEM-001` | 2 | Yes | rule | review | True | Edit | Removes finding |
| `cp-b04` | cpp | `APS-CP-MEM-003` | 2 | Yes | rule | review | True | Edit | Removes finding |
| `cp-b05` | cpp | `APS-CP-FMT-001` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `cp-b06` | cpp | `APS-CP-INJ-001` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-b06` | cpp | `APS-CP-MEM-001` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `cp-b07` | cpp | `APS-CP-CRY-001` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-b07` | cpp | `APS-CP-CRY-001` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-b09` | cpp | `APS-CP-IO-002` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-i01` | cpp | `APS-CP-MEM-001` | 2 | Yes | rule | review | True | Edit | Removes finding |
| `cp-i02` | cpp | `APS-CP-FMT-001` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-i02` | cpp | `APS-CP-FMT-001` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-i03` | cpp | `APS-CP-MEM-001` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `cp-i03` | cpp | `APS-CP-INJ-001` | 3 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-i04` | cpp | `APS-CP-MEM-002` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-i05` | cpp | `APS-CP-MEM-004` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-i08` | cpp | `APS-CP-MEM-007` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-i09` | cpp | `APS-CP-INJ-001` | 4 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-a01` | cpp | `APS-CP-MEM-005` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-a02` | cpp | `APS-CP-MEM-006` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-a02` | cpp | `APS-CP-MEM-005` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-a03` | cpp | `APS-CP-MEM-001` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `cp-a05` | cpp | `APS-CP-FMT-001` | 3 | Yes | rule | safe | True | Edit | Removes finding |
| `cp-a05` | cpp | `APS-CP-MEM-001` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `cp-a06` | cpp | `APS-CP-MEM-001` | 3 | Yes | rule | review | True | Edit | Removes finding |
| `cp-u01` | cpp | `APS-ALL-UNI-001` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `cp-u01` | cpp | `APS-ALL-UNI-001` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `cp-u01` | cpp | `APS-ALL-UNI-001` | 2 | Yes | rule | safe | True | Edit | Removes finding |
| `cp-u02` | cpp | `APS-CP-SYN-001` | 1 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-u02` | cpp | `APS-ALL-UNI-004` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-u02` | cpp | `APS-ALL-UNI-004` | 2 | Yes | rule | manual | False | Advice only | N/A (advice) |
| `cp-u02` | cpp | `APS-ALL-UNI-005` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-u02` | cpp | `APS-ALL-UNI-005` | 2 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-l01` | cpp | `APS-CP-LEX-001` | 3 | No | — | manual | False | Advice only | N/A (advice) |
| `cp-l02` | cpp | `APS-CP-SYN-001` | 1 | No | — | manual | False | Advice only | N/A (advice) |

## 3. Engine Rules Without Automatic Fix Generators

| Rule ID | Language | Title | Feasibility Assessment |
|---|---|---|---|
| `APS-ALL-UNI-005` | generic | Mixed-Script Identifier Detected | Manual advice only (requires human architecture decision) |
| `APS-CP-IO-001` | cpp | Path Traversal via Tainted File Path | Manual advice only (requires human architecture decision) |
| `APS-CP-IO-002` | cpp | Insecure Temporary File Creation via tmpnam() or mktemp() | Manual advice only (requires human architecture decision) |
| `APS-CP-MEM-002` | cpp | Out-of-Bounds Memory Write via Tainted Length or Wrong sizeof | Manual advice only (requires human architecture decision) |
| `APS-CP-MEM-004` | cpp | Integer Overflow in Memory Allocation Size Arithmetic | Manual advice only (requires human architecture decision) |
| `APS-CP-MEM-005` | cpp | Use-After-Free of Deallocated Pointer | Manual advice only (requires human architecture decision) |
| `APS-CP-MEM-006` | cpp | Double Free Memory Corruption | Manual advice only (requires human architecture decision) |
| `APS-CP-MEM-007` | cpp | Uncontrolled Stack Allocation via alloca() | Manual advice only (requires human architecture decision) |
| `APS-CP-SEC-001` | cpp | Hard-Coded Cryptographic Secret or Credential | Feasible (mechanical/review template) |
| `APS-JS-INJ-004` | javascript | Prototype Pollution via Object Merge / Set | Feasible (mechanical/review template) |
| `APS-JS-INJ-005` | javascript | Regular Expression Denial of Service (ReDoS) | Feasible (mechanical/review template) |
| `APS-JS-IO-001` | javascript | Path Traversal via File System API | Manual advice only (requires human architecture decision) |
| `APS-JS-NET-001` | javascript | Client-Side Open Redirect or Event Handler Injection | Feasible (mechanical/review template) |
| `APS-JS-NET-002` | javascript | Server-Side Request Forgery (SSRF) via HTTP Client | Feasible (mechanical/review template) |
| `APS-JS-OBF-001` | javascript | Obfuscated / Encoded Dynamic Execution | Manual advice only (requires human architecture decision) |
| `APS-JS-SEC-002` | javascript | Insecure JWT Verification / Unverified Token Decoding | Feasible (mechanical/review template) |
| `APS-JV-DES-001` | java | Insecure Java Object Deserialization | Manual advice only (requires human architecture decision) |
| `APS-JV-INJ-003` | java | Unsafe Reflection via Tainted Class Name | Feasible (mechanical/review template) |
| `APS-JV-INJ-004` | java | Code Injection via ScriptEngine.eval | Feasible (mechanical/review template) |
| `APS-JV-IO-001` | java | Path Traversal via Tainted File Path | Manual advice only (requires human architecture decision) |
| `APS-JV-NET-001` | java | Server-Side Request Forgery (SSRF) via Tainted URL | Feasible (mechanical/review template) |
| `APS-JV-NET-002` | java | Insecure TLS Certificate Validation (TrustAll) | Feasible (mechanical/review template) |
| `APS-JV-UNI-001` | java | Trojan Source / Dangerous Unicode Escape in Java Source | Manual advice only (requires human architecture decision) |
| `APS-JV-XSS-001` | java | Reflected Cross-Site Scripting (XSS) | Feasible (mechanical/review template) |
| `APS-PY-INJ-005` | python | Dynamic Module Import via __import__/importlib | Feasible (mechanical/review template) |
| `APS-PY-OBF-001` | python | Execution of Decoded / Obfuscated Payload | Manual advice only (requires human architecture decision) |
