"""Inspect findings on each fixture and generate expect.json."""

from __future__ import annotations

import json
from pathlib import Path

from apsla.pipeline import Analyzer

REPO_ROOT = Path(r"c:\Users\ROSHAN GUPTA\OneDrive\Documents\Desktop\AIDS -Nitw\sem3\toc\securelex-ide")
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "cpp"

analyzer = Analyzer()
expect_data: dict[str, dict[str, list[dict[str, str | int]]]] = {
    "vulnerable": {},
    "safe": {},
    "adversarial": {},
}

for cat in ("vulnerable", "safe", "adversarial"):
    cat_dir = FIXTURES_DIR / cat
    for fpath in sorted(cat_dir.glob("*.*")):
        if fpath.suffix not in (".c", ".cpp", ".h", ".hpp"):
            continue
        source = fpath.read_text(encoding="utf-8")
        res = analyzer.analyze(source, language="cpp", filename=fpath.name, options={"ml": False})
        findings = [f for f in res.findings if not f.suppressed]
        entry = [{"rule_id": f.rule_id, "line": f.range.start_line} for f in findings]
        expect_data[cat][fpath.name] = entry
        print(f"[{cat}] {fpath.name}: {entry}")

(FIXTURES_DIR / "expect.json").write_text(json.dumps(expect_data, indent=2), encoding="utf-8")
print("\nWrote expect.json successfully!")
