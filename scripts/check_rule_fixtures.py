"""Rule fixture coverage and schema validation script.

Verifies that:
1. All expect.json and *.expect.json files in tests/fixtures are valid according to their schemas:
   - Security rule expect fixtures (in vulnerable/safe/adversarial): dicts with valid rule_id and optional line.
   - Parser expect fixtures (in parser/): mappings of filename to list of function call names.
2. Every rule in the APSLA rule catalogue has at least one test fixture in tests/fixtures.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apsla.languages.registry import get_plugin, list_plugins  # noqa: E402

RULE_ID_PATTERN = re.compile(r"^APS-[A-Z0-9]+-[A-Z0-9]+-[0-9]{3}$")


def validate_rule_expect_item(item: dict[str, object], file_path: Path, index: int) -> list[str]:
    """Validate a single expected rule finding dictionary against schema."""
    errors: list[str] = []
    if not isinstance(item, dict):
        return [f"{file_path} item {index}: expected dict, got {type(item).__name__}"]

    rule_id = item.get("rule_id")
    if not rule_id or not isinstance(rule_id, str):
        errors.append(f"{file_path} item {index}: missing or invalid 'rule_id'")
    elif not RULE_ID_PATTERN.match(rule_id):
        errors.append(f"{file_path} item {index}: rule_id '{rule_id}' does not match pattern")

    line = item.get("line")
    if line is not None and (not isinstance(line, int) or line <= 0):
        errors.append(f"{file_path} item {index}: line must be a positive integer, got {line}")

    return errors


def validate_parser_expect(content: object, file_path: Path) -> list[str]:
    """Validate a parser expect file (mapping of filename to list of call strings)."""
    errors: list[str] = []
    if not isinstance(content, dict):
        return [f"{file_path}: expected dictionary mapping filenames to call lists"]

    for fn, calls in content.items():
        if not isinstance(fn, str):
            errors.append(f"{file_path}: filename key must be string, got {fn}")
        if not isinstance(calls, list):
            errors.append(f"{file_path}: calls for {fn} must be a list, got {type(calls).__name__}")
        else:
            for call in calls:
                if not isinstance(call, str):
                    errors.append(f"{file_path}: call in {fn} must be string, got {call}")

    return errors


def _walk_category_expect(obj: object, path: Path, tested_rules: set[str], errors: list[str]) -> None:
    if isinstance(obj, dict):
        if "rule_id" in obj:
            item_errors = validate_rule_expect_item(obj, path, 0)
            errors.extend(item_errors)
            if not item_errors:
                tested_rules.add(str(obj["rule_id"]))
        else:
            for val in obj.values():
                _walk_category_expect(val, path, tested_rules, errors)
    elif isinstance(obj, list):
        for item in obj:
            _walk_category_expect(item, path, tested_rules, errors)


def collect_fixtures_and_validate(fixtures_dir: Path) -> tuple[set[str], list[str]]:
    """Scan all expect files in tests/fixtures, validate schema, return (tested_rules, errors)."""
    tested_rules: set[str] = set()
    errors: list[str] = []

    # 1. Individual *.expect.json files
    for path in sorted(fixtures_dir.rglob("*.expect.json")):
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"Failed to parse JSON in {path}: {e}")
            continue

        # Check if parser fixture
        if "parser" in path.parts:
            errors.extend(validate_parser_expect(content, path))
            continue

        if isinstance(content, list):
            for i, item in enumerate(content):
                item_errors = validate_rule_expect_item(item, path, i)
                errors.extend(item_errors)
                if not item_errors and "rule_id" in item:
                    tested_rules.add(str(item["rule_id"]))
        elif isinstance(content, dict):
            for key, val in content.items():
                if key == "rule_id":
                    item_errors = validate_rule_expect_item(content, path, 0)
                    errors.extend(item_errors)
                    if not item_errors:
                        tested_rules.add(str(content["rule_id"]))
                    break
                if isinstance(val, list):
                    for i, item in enumerate(val):
                        item_errors = validate_rule_expect_item(item, path, i)
                        errors.extend(item_errors)
                        if not item_errors and "rule_id" in item:
                            tested_rules.add(str(item["rule_id"]))

    # 2. Category expect.json files
    for path in sorted(fixtures_dir.rglob("expect.json")):
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"Failed to parse JSON in {path}: {e}")
            continue

        if "parser" in path.parts:
            errors.extend(validate_parser_expect(content, path))
            continue

        _walk_category_expect(content, path, tested_rules, errors)

    return tested_rules, errors


def main() -> int:
    # Initialize all plugins to load rules
    for lang in ("python", "java", "javascript", "cpp"):
        get_plugin(lang)

    catalog_rules: dict[str, str] = {}
    for plugin in list_plugins():
        for rule in plugin.rules():
            catalog_rules[rule.id] = getattr(rule, "title", "")

    fixtures_dir = ROOT / "tests" / "fixtures"
    tested_rules, validation_errors = collect_fixtures_and_validate(fixtures_dir)

    print(f"Catalog rules found: {len(catalog_rules)}")
    print(f"Rules covered in fixtures: {len(tested_rules)}")

    if validation_errors:
        print(f"\n[FAIL] Found {len(validation_errors)} expect.json schema validation error(s):")
        for err in validation_errors[:20]:
            print(f"  - {err}")
        if len(validation_errors) > 20:
            print(f"  ... and {len(validation_errors) - 20} more.")
        return 1

    missing_rules = set(catalog_rules.keys()) - tested_rules
    if missing_rules:
        print(f"\n[FAIL] {len(missing_rules)} rule(s) lack fixtures in tests/fixtures:")
        for r_id in sorted(missing_rules):
            print(f"  - {r_id}: {catalog_rules.get(r_id, '')}")
        return 1

    print("\n[OK] All rules have fixture coverage and all expect.json files match schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
