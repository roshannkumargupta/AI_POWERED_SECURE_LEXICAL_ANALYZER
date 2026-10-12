# External security adapter mappings

Mappings are intentionally conservative. A native rule without metadata or an explicit mapping retains an empty CWE list. External results are marked heuristic because adapters do not independently establish exploitability.

| Adapter | Native id | CWE mapping | Severity mapping |
|---|---|---|---|
| Bandit | B102 | CWE-78 | Bandit `issue_severity`: critical/high/medium/low/info map to the matching severity |
| Bandit | B301 | CWE-502 | Same |
| Bandit | B307 | CWE-95 | Same |
| Bandit | B602 | CWE-78 | Same |
| Bandit | B608 | CWE-89 | Same |
| cppcheck | `bufferAccessOutOfBounds` | CWE-120, unless the tool reports a CWE directly | error→high; warning→medium; style/info→info where reported |
| cppcheck | `sprintfCalled` | CWE-134, unless the tool reports a CWE directly | Same |
| cppcheck | `unsafeFunctionUsage` | CWE-676, unless the tool reports a CWE directly | Same |
| Semgrep | Native `check_id` | CWE metadata in result when present | Native severity |
| clang-tidy | Native check id | No default mapping; future entries require a reviewed explicit mapping | warning→medium |
| ESLint | Native `ruleId` | No default mapping; future entries require a reviewed explicit mapping | error→high; warning→medium |

The Bandit and cppcheck mappings are code constants in `src/apsla/security_v2.py`. Semgrep is invoked only against a repository-local rules directory and has no remote registry configuration. Do not infer CWE from a message's wording.
