"""Generate rule reference documents from the instantiated rule registry."""

from __future__ import annotations

from pathlib import Path

from apsla.security_v2 import build_rule_registry


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    rules = build_rule_registry()
    fixture_index: dict[str, list[str]] = {rule["id"]: [] for rule in rules}
    rule_ids = tuple(fixture_index)
    for directory in (root / "tests", root / "examples"):
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".json", ".yaml", ".yml", ".txt", ".js", ".java", ".cpp", ".c"}:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for rule_id in rule_ids:
                if rule_id in content:
                    fixture_index[rule_id].append(path.relative_to(root).as_posix())
    rows = ["# Internal rule catalogue", "", f"Generated from {len(rules)} instantiated internal rules. Optional external analyzers have separate catalogs and are not included.", "", "| Rule | Language | CWE | Severity | Remediation | Safe pattern | Test fixtures mentioning rule id |", "|---|---|---|---|---|---|---|"]
    for rule in rules:
        fixtures = fixture_index[rule["id"]]
        def esc(value: object) -> str:
            return str(value).replace("|", "\\|").replace("\n", " ")

        rows.append(f"| `{rule['id']}` {esc(rule['title'])} | {rule['languages'][0]} | {', '.join(rule['cwe']) or 'Not mapped'} | {rule['severity']} | {esc(rule['remediation'])} | {esc(rule['safe_pattern'])} | {', '.join(f'`{f}`' for f in sorted(set(fixtures))) or 'No fixture reference found'} |")
    (root / "docs" / "rules_catalogue.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
