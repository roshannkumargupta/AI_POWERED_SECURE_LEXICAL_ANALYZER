"""Enforce that every rule ID used in fixtures, samples, and UI matches the registry."""

from __future__ import annotations

import glob
import json
from pathlib import Path

from apsla.languages.cpp_lang.rules import ALL_CPP_RULES
from apsla.languages.java_lang.rules import ALL_JAVA_RULES
from apsla.languages.javascript_lang.rules import ALL_JAVASCRIPT_RULES
from apsla.languages.python_lang.rules import ALL_PYTHON_RULES


def get_all_registered_rule_ids() -> set[str]:
    """Retrieve full set of valid rule identifiers recognized by SecureLex IDE."""
    ids: set[str] = set()

    # Deterministic language rules
    for rule in (
        ALL_PYTHON_RULES
        + ALL_JAVA_RULES
        + ALL_JAVASCRIPT_RULES
        + ALL_CPP_RULES
    ):
        ids.add(rule.id)

    # Lexical and syntax diagnostic rules across languages
    for lang in ("PY", "JAVA", "JV", "JS", "CP"):
        ids.add(f"APS-{lang}-LEX-001")
        ids.add(f"APS-{lang}-SYN-001")

    # Generic Unicode defense rules
    for i in range(1, 7):
        ids.add(f"APS-ALL-UNI-{i:03d}")

    # Machine learning anomaly rule
    ids.add("APS-ALL-ML-001")

    return ids


def test_samples_manifest_rules_exist_in_registry() -> None:
    """Verify all rule IDs mentioned in sample manifests exist in the registry."""
    manifest_path = Path("src/apsla/samples/manifest.json")
    assert manifest_path.exists(), "samples manifest.json must exist"

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    samples = manifest if isinstance(manifest, list) else manifest.get("samples", [])
    registry_rules = get_all_registered_rule_ids()

    for sample in samples:
        expected = sample.get("expect", {})
        for finding in expected.get("findings", []):
            rule_id = finding.get("rule_id")
            if rule_id:
                assert rule_id in registry_rules, (
                    f"Sample '{sample.get('id')}' references unregistered rule ID '{rule_id}'"
                )


def test_fixture_expectations_exist_in_registry() -> None:
    """Verify all rule IDs mentioned in test fixture expectations exist in the registry."""
    registry_rules = get_all_registered_rule_ids()
    fixture_files = glob.glob("tests/fixtures/**/expect.json", recursive=True)
    assert fixture_files, "At least one expect.json fixture must be present"

    for path in fixture_files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for cat_name, cat_entries in data.items():
            if isinstance(cat_entries, dict):
                for entry_name, entry_data in cat_entries.items():
                    if isinstance(entry_data, dict):
                        for finding in entry_data.get("findings", []):
                            rule_id = finding.get("rule_id")
                            if rule_id:
                                assert rule_id in registry_rules, (
                                    f"Fixture '{path}' ({cat_name}/{entry_name}) "
                                    f"references unregistered rule ID '{rule_id}'"
                                )
