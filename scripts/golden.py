"""Golden characterisation tests for SecureLex IDE (APSLA).

Records and verifies deterministic in-process characterisation baselines:
- Full analysis of all fixtures in tests/fixtures/** (ML off & ML on)
- Full analysis of all samples in src/apsla/samples/** (ML off & ML on)
- OpenAPI schema (app.openapi())
- CLI --help text for all Typer commands
- Registered rule IDs per language
- API responses (/api/samples and /api/languages)

Usage:
    python scripts/golden.py --record
    python scripts/golden.py --check
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

GOLDEN_DIR = ROOT_DIR / "tests" / "golden"


def normalize_finding(finding: Any) -> dict[str, Any]:
    """Normalize a Finding into a deterministic dict."""
    return {
        "rule_id": str(finding.rule_id),
        "title": str(finding.title),
        "cwe": str(finding.cwe),
        "severity": str(
            finding.severity.value if hasattr(finding.severity, "value") else finding.severity
        ),
        "label": str(finding.label.value if hasattr(finding.label, "value") else finding.label),
        "confidence": round(float(finding.confidence), 4),
        "range": {
            "start_line": finding.range.start_line,
            "start_col": finding.range.start_col,
            "end_line": finding.range.end_line,
            "end_col": finding.range.end_col,
        },
        "message": str(finding.message),
        "explanation": str(finding.explanation),
        "taint_path": [
            {
                "kind": str(step.kind.value if hasattr(step.kind, "value") else step.kind),
                "range": {
                    "start_line": step.range.start_line,
                    "start_col": step.range.start_col,
                    "end_line": step.range.end_line,
                    "end_col": step.range.end_col,
                },
                "text": str(step.text),
                "note": str(step.note),
            }
            for step in getattr(finding, "taint_path", [])
        ],
        "fixes": [
            {
                "title": str(fix.title),
                "confidence": str(fix.confidence),
                "kind": str(fix.kind),
                "verification": {
                    "syntax_ok": bool(fix.verification.syntax_ok),
                    "finding_gone": bool(fix.verification.finding_gone),
                    "verified": bool(fix.verification.verified),
                    "notes": str(fix.verification.notes),
                },
                "edits": [
                    {
                        "range": {
                            "start_line": e.range.start_line,
                            "start_col": e.range.start_col,
                            "end_line": e.range.end_line,
                            "end_col": e.range.end_col,
                        },
                        "new_text": str(e.new_text),
                    }
                    for e in getattr(fix, "edits", [])
                ],
            }
            for fix in sorted(
                getattr(finding, "fixes", []), key=lambda f: (str(f.title), str(f.kind))
            )
        ],
    }


def normalize_analysis_result(res: Any, rel_path: str) -> dict[str, Any]:
    """Normalize an AnalysisResult into a stable deterministic dictionary."""
    sorted_findings = sorted(
        res.findings,
        key=lambda f: (
            str(f.rule_id),
            f.range.start_line,
            f.range.start_col,
            f.range.end_line,
            f.range.end_col,
        ),
    )
    normalized_findings = [normalize_finding(f) for f in sorted_findings]

    return {
        "file": rel_path.replace("\\", "/"),
        "language": str(res.language),
        "summary": {
            "critical": int(res.summary.critical),
            "high": int(res.summary.high),
            "medium": int(res.summary.medium),
            "low": int(res.summary.low),
            "info": int(res.summary.info),
            "score": int(res.summary.score),
            "tokens_total": int(res.summary.tokens_total),
            "tokens_malicious": int(res.summary.tokens_malicious),
            "tokens_suspicious": int(res.summary.tokens_suspicious),
        },
        "engine": {
            "ml_mode": str(res.engine.ml_mode),
            "taint": str(res.engine.taint),
            "parser": getattr(res.engine, "parser", ""),
        },
        "findings": normalized_findings,
    }


def collect_file_analyses(paths: list[Path], ml_mode: bool) -> dict[str, Any]:
    """Run Analyzer on a list of paths and return a normalized dict keyed by relative path."""
    from apsla.pipeline import Analyzer

    analyzer = Analyzer()
    results: dict[str, Any] = {}

    for path in sorted(paths, key=lambda p: str(p.relative_to(ROOT_DIR)).replace("\\", "/")):
        rel_key = str(path.relative_to(ROOT_DIR)).replace("\\", "/")
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            res = analyzer.analyze(
                source,
                filename=path.name,
                options={"fixes": True, "ml": ml_mode},
            )
            results[rel_key] = normalize_analysis_result(res, rel_key)
        except Exception as exc:
            results[rel_key] = {"error": f"{type(exc).__name__}: {exc}"}

    return results


def collect_openapi_schema() -> dict[str, Any]:
    """Return normalized OpenAPI schema."""
    from apsla.server.app import app

    schema = app.openapi()
    return schema


def collect_cli_help() -> dict[str, str]:
    """Return Typer CLI --help outputs."""
    from typer.testing import CliRunner

    from apsla.cli import app

    runner = CliRunner()
    commands = [
        [],
        ["analyze", "--help"],
        ["fix", "--help"],
        ["serve", "--help"],
    ]

    out: dict[str, str] = {}
    for cmd in commands:
        cmd_name = "apsla " + " ".join(cmd) if cmd else "apsla --help"
        inv_args = cmd if cmd else ["--help"]
        res = runner.invoke(app, inv_args)
        out[cmd_name] = res.stdout.strip()

    return out


def collect_rules_per_language() -> dict[str, list[dict[str, str]]]:
    """Return rule IDs and titles for all registered languages."""
    from apsla.languages.registry import get_plugin, list_plugins

    for lang in ("python", "java", "javascript", "cpp"):
        get_plugin(lang)

    plugins = list_plugins()
    out: dict[str, list[dict[str, str]]] = {}

    for plugin in sorted(plugins, key=lambda p: p.id):
        rules = plugin.rules()
        out[plugin.id] = [
            {
                "id": str(getattr(r, "id", "")),
                "title": str(getattr(r, "title", "")),
                "cwe": str(getattr(r, "cwe", "")),
                "severity": str(
                    r.severity.value if hasattr(r.severity, "value") else getattr(r, "severity", "")
                ),
                "category": str(getattr(r, "category", "")),
            }
            for r in sorted(rules, key=lambda r: str(getattr(r, "id", "")))
        ]

    return out


def collect_api_metadata() -> dict[str, Any]:
    """Return /api/languages and /api/samples responses."""
    from fastapi.testclient import TestClient

    from apsla.server.app import app

    # The request-boundary middleware intentionally accepts localhost outside
    # pytest; this also makes standalone `--record`/`--check` calls representative.
    client = TestClient(app, base_url="http://localhost")
    resp_langs = client.get("/api/languages")
    resp_samples = client.get("/api/samples")

    samples_data = resp_samples.json()
    # Normalize sample entries: remove volatile fields if any, sort by id
    # Older and failed responses may be an object (for example a FastAPI error).
    # Golden collection must report that response instead of treating its keys as
    # sample entries and crashing on ``str.get``.
    sample_entries = samples_data if isinstance(samples_data, list) else []
    normalized_samples = sorted(
        [
            {
                "id": s.get("id"),
                "title": s.get("title"),
                "language": s.get("language"),
                "category": s.get("category"),
                "filename": s.get("filename"),
            }
            for s in sample_entries
            if isinstance(s, dict)
        ],
        key=lambda s: str(s.get("id")),
    )

    return {
        "languages": resp_langs.json(),
        "samples": normalized_samples if isinstance(samples_data, list) else samples_data,
    }


def find_fixture_files() -> list[Path]:
    """Find all fixture files to be tested."""
    fixtures_dir = ROOT_DIR / "tests" / "fixtures"
    candidates = []
    for p in fixtures_dir.rglob("*"):
        # Token snapshots and adapter payloads are inputs to dedicated unit
        # tests, not source programs for Analyzer characterization.
        if (
            p.is_file()
            and not p.name.endswith((".expect.json", ".tokens.json"))
            and "security_adapter_outputs" not in p.parts
            and "ui-p3" not in p.parts
        ):
            candidates.append(p)
    return candidates


def find_sample_files() -> list[Path]:
    """Find all shipped and pending sample files."""
    samples_dir = ROOT_DIR / "src" / "apsla" / "samples"
    candidates = []
    for p in samples_dir.rglob("*"):
        if p.is_file() and p.suffix in (".py", ".java", ".js", ".c", ".cpp"):
            candidates.append(p)
    return candidates


def record_golden() -> None:
    """Record all golden baseline files into tests/golden/."""
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    print("Finding fixture files...")
    fixture_files = find_fixture_files()
    print(f"Found {len(fixture_files)} fixture files.")

    print("Finding sample files...")
    sample_files = find_sample_files()
    print(f"Found {len(sample_files)} sample files.")

    print("Running fixture analysis (ML off)...")
    fix_ml_off = collect_file_analyses(fixture_files, ml_mode=False)
    with open(GOLDEN_DIR / "fixtures_ml_off.json", "w", encoding="utf-8") as f:
        json.dump(fix_ml_off, f, indent=2, sort_keys=True)

    print("Running fixture analysis (ML on)...")
    fix_ml_on = collect_file_analyses(fixture_files, ml_mode=True)
    with open(GOLDEN_DIR / "fixtures_ml_on.json", "w", encoding="utf-8") as f:
        json.dump(fix_ml_on, f, indent=2, sort_keys=True)

    print("Running sample analysis (ML off)...")
    samp_ml_off = collect_file_analyses(sample_files, ml_mode=False)
    with open(GOLDEN_DIR / "samples_ml_off.json", "w", encoding="utf-8") as f:
        json.dump(samp_ml_off, f, indent=2, sort_keys=True)

    print("Running sample analysis (ML on)...")
    samp_ml_on = collect_file_analyses(sample_files, ml_mode=True)
    with open(GOLDEN_DIR / "samples_ml_on.json", "w", encoding="utf-8") as f:
        json.dump(samp_ml_on, f, indent=2, sort_keys=True)

    print("Collecting OpenAPI schema...")
    openapi = collect_openapi_schema()
    with open(GOLDEN_DIR / "openapi_schema.json", "w", encoding="utf-8") as f:
        json.dump(openapi, f, indent=2, sort_keys=True)

    print("Collecting CLI help...")
    cli_help = collect_cli_help()
    with open(GOLDEN_DIR / "cli_help.json", "w", encoding="utf-8") as f:
        json.dump(cli_help, f, indent=2, sort_keys=True)

    print("Collecting rules per language...")
    rules = collect_rules_per_language()
    with open(GOLDEN_DIR / "rules_per_language.json", "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, sort_keys=True)

    print("Collecting API metadata...")
    api_meta = collect_api_metadata()
    with open(GOLDEN_DIR / "api_metadata.json", "w", encoding="utf-8") as f:
        json.dump(api_meta, f, indent=2, sort_keys=True)

    print("\nGolden characterisation baselines recorded successfully in tests/golden/.")


def check_golden() -> int:
    """Check current outputs against golden baselines and print diffs on mismatch."""
    if not GOLDEN_DIR.exists():
        print(f"Error: Golden directory does not exist: {GOLDEN_DIR}. Run with --record first.")
        return 1

    failures: list[str] = []

    def diff_and_compare(name: str, actual: Any) -> None:
        target_path = GOLDEN_DIR / f"{name}.json"
        if not target_path.exists():
            failures.append(f"Missing golden baseline file: {target_path}")
            return

        expected_text = target_path.read_text(encoding="utf-8")
        actual_text = json.dumps(actual, indent=2, sort_keys=True)

        if expected_text.strip() != actual_text.strip():
            print(f"\n[DIFF DETECTED] in {name}.json:")
            diff = difflib.unified_diff(
                expected_text.splitlines(keepends=True),
                actual_text.splitlines(keepends=True),
                fromfile=f"golden/{name}.json",
                tofile=f"current/{name}.json",
                n=3,
            )
            sys.stdout.writelines(list(diff)[:50])
            failures.append(name)
        else:
            print(f"[OK] {name}.json")

    print("Checking Golden Characterisation Tests...")
    fixture_files = find_fixture_files()
    sample_files = find_sample_files()

    diff_and_compare("fixtures_ml_off", collect_file_analyses(fixture_files, ml_mode=False))
    diff_and_compare("fixtures_ml_on", collect_file_analyses(fixture_files, ml_mode=True))
    diff_and_compare("samples_ml_off", collect_file_analyses(sample_files, ml_mode=False))
    diff_and_compare("samples_ml_on", collect_file_analyses(sample_files, ml_mode=True))
    diff_and_compare("openapi_schema", collect_openapi_schema())
    diff_and_compare("cli_help", collect_cli_help())
    diff_and_compare("rules_per_language", collect_rules_per_language())
    diff_and_compare("api_metadata", collect_api_metadata())

    if failures:
        print(f"\nFAILED: {len(failures)} golden baselines mismatched: {', '.join(failures)}")
        return 1

    print("\nALL GOLDEN CHARACTERISATION TESTS PASSED (0 differences).")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Golden characterisation test harness for SecureLex IDE."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--record", action="store_true", help="Record current baseline into tests/golden/"
    )
    group.add_argument(
        "--check", action="store_true", help="Check current behaviour against golden baseline"
    )

    args = parser.parse_args()

    if args.record:
        record_golden()
    elif args.check:
        sys.exit(check_golden())


if __name__ == "__main__":
    main()
