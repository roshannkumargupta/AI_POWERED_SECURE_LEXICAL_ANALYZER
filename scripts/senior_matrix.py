"""Run both archived senior analyzers against the shipped S-3 sample catalogue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from legacy_probe import setup_legacy_imports  # noqa: E402

from apsla.pipeline import Analyzer  # noqa: E402
from apsla.samples.schema import SampleMeta  # noqa: E402

OUT = ROOT / "src" / "apsla" / "samples" / "senior_results.json"
REPORT = ROOT / "reports" / "samples_senior_vs_ours.md"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    manifest = json.loads(
        (ROOT / "src" / "apsla" / "samples" / "manifest.json").read_text(encoding="utf-8")
    )
    samples = [
        (
            SampleMeta.model_validate(row),
            (ROOT / "src" / "apsla" / "samples" / row["file"]).read_text(encoding="utf-8"),
        )
        for row in manifest
    ]
    results: dict[str, dict[str, object]] = {}
    b_error = None
    try:
        for module_name in list(sys.modules):
            if (
                module_name == "lexer" or module_name.startswith(("lexer.", "ml.")) or module_name == "ml"
            ):
                sys.modules.pop(module_name, None)
        sys.path.insert(0, str(ROOT / "legacy" / "senior-part2" / "src"))
        from security.static_analyzer import StaticAnalyzer

        scanner = StaticAnalyzer()
    except Exception as exc:
        b_error = f"{type(exc).__name__}: {exc}"

    a_error = None
    try:
        if not setup_legacy_imports():
            raise RuntimeError("legacy/senior-part1 is absent")
        from ML_model.hybrid_validator import HybridValidator, RuleEngine
        from W5_6.lexer import SecureIngestionPipeline

        pipeline = SecureIngestionPipeline()
        validator = HybridValidator(rule_engine=RuleEngine(), ai_engine=None)
    except Exception as exc:  # The missing model/dependency is recorded honestly.
        a_error = f"{type(exc).__name__}: {exc}"

    comparisons: list[tuple[str, bool, bool, str]] = []
    analyzer = Analyzer()
    for meta, source in samples:
        if meta.language == "python":
            tool = "Senior Project A rules + taint (ML disabled)"
            if a_error:
                results[meta.id] = {
                    "tool": tool,
                    "flagged": None,
                    "detail": f"not run: {a_error}",
                    "note": "senior tool run without its ML model",
                }
                continue
            try:
                legacy_result = validator.validate(
                    pipeline.process_string(source, meta.file).tokens
                )
                flags = [
                    item
                    for item in legacy_result.get("explanations", [])
                    if item.get("label") != "SAFE"
                ]
                detail = (
                    "; ".join(
                        str(item.get("token", item.get("reasons", "flagged"))) for item in flags
                    )
                    or "no rule/taint flag"
                )
                flagged = bool(flags or legacy_result.get("taint_log"))
            except Exception as exc:
                flagged, detail = None, f"not run: {type(exc).__name__}: {exc}"
            note = "senior tool run without its ML model"
        else:
            tool = "Senior Project B StaticAnalyzer regex hotspot stage"
            if b_error:
                flagged, detail = None, f"not run: {b_error}"
            else:
                try:
                    flags, lines = scanner.static_analyze(source)
                    found = [name for name, yes in flags.items() if name != "Safe" and yes]
                    flagged = bool(found)
                    detail = (
                        "; ".join(f"{name} at {lines.get(name, [])}" for name in found)
                        or "no regex hotspot"
                    )
                except Exception as exc:
                    flagged, detail = None, f"not run: {type(exc).__name__}: {exc}"
            note = (
                "Java scanner, not designed for this language"
                if meta.language in {"javascript", "cpp"}
                else "regex hotspot stage only"
            )
        if flagged is None:
            results[meta.id] = {"tool": tool, "flagged": None, "detail": detail, "note": note}
            continue
        ours_result = analyzer.analyze(
            source, meta.language, meta.file, {"ml": False, "fixes": False}
        )
        ours = bool(ours_result.findings)
        vuln = meta.kind == "vulnerable"
        results[meta.id] = {"tool": tool, "flagged": flagged, "detail": detail, "note": note}
        comparisons.append(
            (
                meta.id,
                vuln,
                flagged,
                "both"
                if vuln and flagged and ours
                else "miss"
                if vuln and ours and not flagged
                else "false alarm"
                if not vuln and flagged
                else "other",
            )
        )

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    misses = [x for x in comparisons if x[3] == "miss"]
    false_alarms = [x for x in comparisons if not x[1] and x[2]]
    both = [x for x in comparisons if x[3] == "both"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Senior analyzer comparison\n\nGenerated from the shipped samples. Senior Project A ran rules and taint with ML disabled; Project B ran only its regex hotspot stage. Cross-language results are not claims of suitability.\n\n"
        f"- Samples with a senior result: {len(comparisons)}; not run: {len(results) - len(comparisons)}.\n"
        f"- Vulnerable samples ours catches and senior missed: {len(misses)}.\n"
        f"- Safe samples senior wrongly flagged: {len(false_alarms)}.\n"
        f"- Vulnerable samples both catch: {len(both)}.\n\n"
        "## Not run\n\n"
        + "\n".join(
            f"- `{sid}`: {row['detail']}" for sid, row in results.items() if row["flagged"] is None
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(results)} results; A init error={a_error!r}; B init error={b_error!r}")


if __name__ == "__main__":
    main()
