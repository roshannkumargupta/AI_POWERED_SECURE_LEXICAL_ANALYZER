#!/usr/bin/env python3
"""
scripts/audit_fix_coverage.py
Audits fix coverage for EVERY sample across all 4 languages.
Writes reports/ui9/fix_coverage.md according to fix coverage specifications.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apsla.fixes.engine import apply_edits  # noqa: E402
from apsla.pipeline import Analyzer  # noqa: E402
from apsla.samples.loader import load_samples  # noqa: E402


def audit_fix_coverage() -> None:
    output_dir = ROOT / "reports" / "ui9"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "fix_coverage.md"

    samples = load_samples()
    analyzer = Analyzer()

    rows: list[dict] = []
    rule_coverage: dict[str, dict] = {}

    print(f"Auditing fix coverage across {len(samples)} samples...")

    for meta, source in samples:
        try:
            res = analyzer.analyze(source, meta.language, meta.file, {"fixes": True, "ml": False})
        except Exception as e:
            print(f"Error analyzing {meta.id}: {e}")
            continue

        for finding in res.findings:
            rule_id = finding.rule_id
            if rule_id not in rule_coverage:
                rule_coverage[rule_id] = {
                    "language": meta.language,
                    "sample_count": 0,
                    "fix_count": 0,
                    "verified_count": 0,
                    "effective_count": 0,
                }
            rule_coverage[rule_id]["sample_count"] += 1

            fixes = finding.fixes or []
            if not fixes:
                rows.append(
                    {
                        "sample_id": meta.id,
                        "language": meta.language,
                        "rule_id": rule_id,
                        "line": finding.range.start_line,
                        "has_fix": False,
                        "kind": "—",
                        "confidence": "manual",
                        "verified": False,
                        "has_edit": False,
                        "removes_finding": False,
                    }
                )
            else:
                for fix in fixes:
                    rule_coverage[rule_id]["fix_count"] += 1
                    is_verified = bool(fix.verification and fix.verification.verified)
                    if is_verified:
                        rule_coverage[rule_id]["verified_count"] += 1

                    has_edit = bool(fix.edits and len(fix.edits) > 0)
                    removes_finding = False

                    if has_edit:
                        try:
                            # Apply edit and re-analyze
                            patched = apply_edits(source, fix.edits)
                            re_res = analyzer.analyze(
                                patched, meta.language, meta.file, {"fixes": False, "ml": False}
                            )
                            # Check if the specific finding on the line is gone
                            remains = any(
                                f.rule_id == rule_id
                                and abs(f.range.start_line - finding.range.start_line) <= 2
                                for f in re_res.findings
                            )
                            removes_finding = not remains
                            if removes_finding:
                                rule_coverage[rule_id]["effective_count"] += 1
                        except Exception:
                            removes_finding = False

                    rows.append(
                        {
                            "sample_id": meta.id,
                            "language": meta.language,
                            "rule_id": rule_id,
                            "line": finding.range.start_line,
                            "has_fix": True,
                            "kind": fix.kind or "template",
                            "confidence": fix.confidence,
                            "verified": is_verified,
                            "has_edit": has_edit,
                            "removes_finding": removes_finding,
                        }
                    )

    # Find rules in engine that have no fix generator
    from apsla.fixes.registry import FIX_REGISTRY
    from apsla.languages.cpp_lang.rules import ALL_CPP_RULES
    from apsla.languages.java_lang.rules import ALL_JAVA_RULES
    from apsla.languages.javascript_lang.rules import ALL_JAVASCRIPT_RULES
    from apsla.languages.python_lang.rules import ALL_PYTHON_RULES

    all_engine_rules = {
        "APS-ALL-UNI-001": ("generic", "Trojan Source Bidi Control Character"),
        "APS-ALL-UNI-002": ("generic", "Zero-Width Character in Identifier or Code"),
        "APS-ALL-UNI-003": ("generic", "Unicode Tag Character Detected"),
        "APS-ALL-UNI-004": ("generic", "Confusable Look-alike Character"),
        "APS-ALL-UNI-005": ("generic", "Mixed-Script Identifier Detected"),
        "APS-ALL-UNI-006": ("generic", "Obfuscated Dangerous Built-in / Keyword"),
    }
    for r in ALL_PYTHON_RULES:
        all_engine_rules[r.id] = ("python", r.title)
    for r in ALL_JAVA_RULES:
        all_engine_rules[r.id] = ("java", r.title)
    for r in ALL_JAVASCRIPT_RULES:
        all_engine_rules[r.id] = ("javascript", r.title)
    for r in ALL_CPP_RULES:
        all_engine_rules[r.id] = ("cpp", r.title)

    rules_without_fix = []
    for r_id, (lang, title) in sorted(all_engine_rules.items()):
        if not FIX_REGISTRY.get(r_id):
            feasible = (
                "Feasible (mechanical/review template)"
                if any(k in r_id for k in ["INJ", "XSS", "SEC", "NET", "CRY"])
                else "Manual advice only (requires human architecture decision)"
            )
            rules_without_fix.append((r_id, lang, title, feasible))

    # Write report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# UI-9 Fix Coverage Audit Report\n\n")
        f.write(
            "Generated from automated analysis of all shipped samples across Python, Java, JavaScript, and C/C++.\n\n"
        )
        f.write("## 1. Summary Statistics\n\n")
        total_findings = len(rows)
        with_fixes = sum(1 for r in rows if r["has_fix"])
        with_edits = sum(1 for r in rows if r["has_edit"])
        verified = sum(1 for r in rows if r["verified"])
        effective = sum(1 for r in rows if r["removes_finding"])

        f.write(f"- **Total Finding Instances Audited**: {total_findings}\n")
        f.write(
            f"- **Findings with Fix Proposals**: {with_fixes} ({with_fixes / max(1, total_findings) * 100:.1f}%)\n"
        )
        f.write(
            f"- **Findings with Automatic Code Edits**: {with_edits} ({with_edits / max(1, total_findings) * 100:.1f}%)\n"
        )
        f.write(
            f"- **Verified Fixes (Syntax + Regression Checked)**: {verified} ({verified / max(1, total_findings) * 100:.1f}%)\n"
        )
        f.write(
            f"- **Effective Fixes (Removes Finding on Re-analysis)**: {effective} ({effective / max(1, total_findings) * 100:.1f}%)\n\n"
        )

        f.write("## 2. Per-Sample Finding and Fix Matrix\n\n")
        f.write(
            "| Sample ID | Lang | Rule ID | Line | Fix Exists | Kind | Confidence | Verified | Edit Present | Re-analysis Effective |\n"
        )
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            fix_str = "Yes" if r["has_fix"] else "No"
            ver_str = "True" if r["verified"] else "False"
            edit_str = "Edit" if r["has_edit"] else "Advice only"
            eff_str = (
                "Removes finding"
                if r["removes_finding"]
                else ("N/A (advice)" if not r["has_edit"] else "Finding remains")
            )
            f.write(
                f"| `{r['sample_id']}` | {r['language']} | `{r['rule_id']}` | {r['line']} | {fix_str} | {r['kind']} | {r['confidence']} | {ver_str} | {edit_str} | {eff_str} |\n"
            )

        f.write("\n## 3. Engine Rules Without Automatic Fix Generators\n\n")
        f.write("| Rule ID | Language | Title | Feasibility Assessment |\n")
        f.write("|---|---|---|---|\n")
        for r_id, lang, title, feas in rules_without_fix:
            f.write(f"| `{r_id}` | {lang} | {title} | {feas} |\n")

    print(f"Report written to {report_file}")


if __name__ == "__main__":
    audit_fix_coverage()
