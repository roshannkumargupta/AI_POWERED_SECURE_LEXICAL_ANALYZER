# SL2-4 Evidence

Date: 2026-10-12. Source code remains untrusted and was analyzed statically; no submitted fixture/source was executed.

## Implemented

- Added a v2 security facade for internal findings, rule registry extraction, external result normalization, exact-range deduplication and findings summary.
- Added Bandit JSON and cppcheck XML recorded-output fixtures. ESLint, Semgrep and clang-tidy normalizers preserve native provenance and do not invent a CWE where no mapping is known.
- Updated the allowlisted runner's cppcheck profile to request XML v2. Semgrep uses only `rules/semgrep/` with `--metrics=off` and `--disable-version-check`; without local rules it reports unavailable. The host's network-isolated process sandbox is unavailable, so external execution remains fail-closed.
- Added syntax-tree quality measurements for functions recognized in Python, Java, JavaScript and C/C++ parse trees.
- Replaced the CLI's clean-result claim with the Part 7.4 wording constant and removed displayed health-score values from analysis and fix summaries. Existing score fields remain for legacy API compatibility and internal prioritization.
- Generated `docs/rules_catalogue.md` from 58 instantiated rules. `docs/adding_a_rule.md` documents the registry and evidence policy.

## Commands and observed results

Focused lint command:

```text
.venv\Scripts\ruff.exe check src/apsla/cli.py src/apsla/security_v2.py src/apsla/quality_v2.py src/apsla/server/app.py src/apsla/server/schemas.py src/apsla/server/tool_runner.py scripts/generate_rules_catalogue.py tests/unit/test_sl2_4_security.py
All checks passed!
```

Focused phase plus SL2-1..3 regression command:

```text
PYTHONPATH=src .venv\Scripts\python.exe -m pytest tests/unit/test_sl2_4_security.py tests/unit/test_sl2_3_parsing.py tests/unit/test_sl2_2_tokens.py tests/unit/test_sl2_v2.py -o addopts='' --basetemp=.pytest-temp-sl2-4-final4 -q
309 passed in 12.39s
```

The final focused run includes the code-point coordinate refinement, external column normalization, CLI wording change, and rule-to-safe-pattern lookup.

```text
Catalog rules found: 58
Rules covered in fixtures: 64
[OK] All rules have fixture coverage and all expect.json files match schema.
OpenAPI paths: 20; findings_summary and taint_paths present: True
```

The recorded-output tests validate Bandit/CWE and cppcheck XML conversion, unknown CWE handling, provenance union, severity-preserving dedupe including shared-CWE merge, findings summary, all-language measured quality observations, and the OpenAPI response contract for both findings summary and taint paths. OpenAPI and its golden schema were regenerated and compared equal to the live FastAPI schema. A direct attempt to exercise the async security handler did not return within the observed wait window and was interrupted; live `/api/analyze/security` transport and route execution are not claimed as verified in this sandbox.

## Coverage and remaining limits

The existing repository has vulnerable and safe source fixture directories for Python, Java, JavaScript and C++; this phase did not create a proven family-by-family paired matrix for every applicable language. Do not interpret broad catalogue fixture references as family-level coverage. The machine's external adapters were not run, and live HTTP was not verified. The rules catalogue and OpenAPI/golden schema are generated artifacts, not execution evidence.
