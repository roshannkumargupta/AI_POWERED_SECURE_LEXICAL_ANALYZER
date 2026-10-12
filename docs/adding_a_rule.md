# Adding an internal security rule

Internal rules are implemented by the language plugins in `src/apsla/languages/<language>_lang/rules.py`; shared Unicode rules live in `src/apsla/rules/generic.py`. The plugin's `rules()` method is the registration point. Each instantiated rule should declare a stable `id`, supported language through its plugin, `cwe` when known, `severity`, title, description and evidence-bearing source range.

1. Add a deterministic rule that examines parsed/tokenized data, not broad source substring presence. Keep source and tool output untrusted.
2. Return a `Finding` with a stable rule id and an exact range. Put concrete evidence in `evidence` and add a real taint path only if the analyzer observed its steps.
3. Add a vulnerable fixture and a safe counterpart. Assert both the finding and the safe result so a textual coincidence is not enough to trigger it.
4. Record remediation and a safe pattern only when a specific pattern is supported. The generated catalogue labels absent structured safe patterns explicitly.
5. Run the applicable tests, focused Ruff, the fixture catalogue checker and golden/regression checks. Do not claim tests that did not run.
6. Regenerate the reference with `PYTHONPATH=src python scripts/generate_rules_catalogue.py` and review the generated diff.

The generated catalogue includes all currently instantiated internal plugin rules. External analyzers are adapters rather than internal rules; their native rules and statuses are reported with their own provenance. See [security adapter mappings](security_adapter_mappings.md). CWE mappings for external tools are intentionally sparse: unmapped native checks retain an empty CWE list rather than receiving an inferred mapping.

## Finding merge policy

Findings merge only when their start/end line and column match exactly and they share at least one CWE or finding category. The result unions CWE and detector/provenance lists, keeps the more severe observation, and does not lower severity. Ranges are not widened during merging.
