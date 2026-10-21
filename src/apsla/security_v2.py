"""Security analyzer facade, external result normalization and merge policy."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from apsla.languages import registry
from apsla.models import Range, Severity
from apsla.models_v2 import SecurityFindingV2

_SEVERITY = {Severity.INFO: 0, Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}
_BANDIT_CWE = {"B102": "CWE-78", "B301": "CWE-502", "B307": "CWE-95", "B602": "CWE-78", "B608": "CWE-89"}
_CPPCHECK_CWE = {"bufferAccessOutOfBounds": "CWE-120", "sprintfCalled": "CWE-134", "unsafeFunctionUsage": "CWE-676"}
_CLANG_TIDY_CWE: dict[str, str] = {}
_ESLINT_CWE: dict[str, str] = {}


@lru_cache(maxsize=1)
def build_rule_registry() -> list[dict[str, Any]]:
    """Describe every instantiated language rule using its declared metadata."""
    entries: list[dict[str, Any]] = []
    for language in ("python", "java", "javascript", "cpp"):
        plugin = registry.get(language)
        if plugin is None:
            continue
        for rule in plugin.rules():
            entries.append({
                "id": rule.id,
                "title": rule.title or rule.id,
                "languages": [language],
                "cwe": [rule.cwe] if rule.cwe and rule.cwe != "CWE-000" else [],
                "severity": getattr(rule.severity, "value", str(rule.severity)),
                "remediation": rule.explanation or rule.description or "No remediation guidance is declared by this rule.",
                "safe_pattern": _safe_pattern(rule),
                "fixtures": [],
            })
    root = Path(__file__).resolve().parents[2]
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
            for entry in entries:
                if entry["id"] in content:
                    entry["fixtures"].append(path.relative_to(root).as_posix())
    return entries


def _safe_pattern(rule: Any) -> str:
    from apsla.rules.explanations import get_rule_template

    template = get_rule_template(rule.id)
    if template is not None and template.fix_example.strip():
        return template.fix_example.strip()
    return "No structured safe-code example is declared by this rule."


def internal_security_findings(findings: Sequence[Any]) -> list[SecurityFindingV2]:
    """Adapt internal deterministic/taint/ML fused findings into the v2 facade."""
    rules_by_id = {item["id"]: item for item in build_rule_registry()}
    adapted: list[SecurityFindingV2] = []
    for finding in findings:
        data = finding.model_dump()
        if isinstance(finding.cwe, list):
            data["cwe"] = [str(x) for x in finding.cwe if x and x != "CWE-000"]
        elif finding.cwe and finding.cwe != "CWE-000":
            data["cwe"] = [str(finding.cwe)]
        else:
            data["cwe"] = []
        provenance = list(dict.fromkeys(["internal", *finding.sources]))
        data.update(
            tool_provenance=provenance,
            detectors_fired=list(dict.fromkeys([*finding.sources, finding.rule_id])),
            certainty="definitive" if "taint" in finding.sources else "heuristic",
            remediation=finding.fixes[0].description if finding.fixes else None,
            safe_pattern=rules_by_id.get(finding.rule_id, {}).get("safe_pattern"),
        )
        adapted.append(SecurityFindingV2(**data))
    return adapted


def normalize_external(name: str, parsed: Any, source: str, language: str) -> list[SecurityFindingV2]:
    """Normalize bounded, structured analyzer output; unknown metadata stays unmapped."""
    records: list[dict[str, Any]] = []
    if name in {"bandit", "eslint", "semgrep"} and isinstance(parsed, (str, dict, list)):
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except json.JSONDecodeError:
                return []
        if name == "bandit":
            records = list(parsed.get("results", []))
        elif name == "eslint":
            records = [message for file in parsed if isinstance(file, dict) for message in file.get("messages", [])]
        else:
            records = list(parsed.get("results", []))
    elif name == "cppcheck":
        try:
            root = ET.fromstring(str(parsed))
        except ET.ParseError:
            return []
        for error in root.findall(".//error"):
            loc = error.find("location")
            records.append({"rule": error.get("id", "cppcheck"), "message": error.get("msg", ""), "line": int(loc.get("line", "1")) if loc is not None else 1, "column": int(loc.get("column", "1")) if loc is not None else 1, "severity": error.get("severity", "warning"), "cwe": error.get("cwe")})
    elif name == "clang-tidy" and isinstance(parsed, list):
        for line in parsed:
            match = re.match(r".*?:(\d+):(\d+):\s+warning:\s+(.*?)\s+\[([\w.-]+)\]", str(line))
            if match:
                records.append({"line": int(match.group(1)), "column": int(match.group(2)), "message": match.group(3), "rule": match.group(4), "severity": "warning"})
    results: list[SecurityFindingV2] = []
    lines = source.splitlines() or [""]
    for i, item in enumerate(records):
        if not isinstance(item, dict):
            continue
        rid = str(item.get("test_id") or item.get("check_id") or item.get("rule") or item.get("ruleId") or item.get("rule_id") or name)
        line = item.get("line_number") or item.get("line") or item.get("start", {}).get("line", 1)
        try:
            line = max(1, min(int(line), len(lines)))
        except (ValueError, TypeError):
            line = 1
        col = item.get("start", {}).get("col", 1)
        if name == "bandit":
            col = int(item.get("col_offset", 0)) + 1
        elif name in {"cppcheck", "clang-tidy", "eslint"}:
            col = item.get("column", 1)
        try:
            col = max(1, int(col))
        except (ValueError, TypeError):
            col = 1
        endcol = min(len(lines[line - 1]) + 1, col + 1)
        cwe = item.get("cwe")
        if isinstance(cwe, dict):
            cwe = cwe.get("id")
        if not cwe:
            cwe = {"bandit": _BANDIT_CWE, "cppcheck": _CPPCHECK_CWE, "clang-tidy": _CLANG_TIDY_CWE, "eslint": _ESLINT_CWE}.get(name, {}).get(rid)
        cwe_values = ([str(cwe) if str(cwe).startswith("CWE-") else f"CWE-{cwe}"] if cwe else [])
        rawsev = str(item.get("issue_severity") or item.get("severity") or "medium").lower()
        severity = {"critical": Severity.CRITICAL, "high": Severity.HIGH, "error": Severity.HIGH, "medium": Severity.MEDIUM, "warning": Severity.MEDIUM, "low": Severity.LOW, "info": Severity.INFO}.get(rawsev, Severity.MEDIUM)
        rng = Range(start_line=line, start_col=col, end_line=line, end_col=endcol)
        message = str(item.get("issue_text") or item.get("message") or item.get("extra", {}).get("message") or "External analyzer reported an issue.")
        results.append(SecurityFindingV2(
            id=f"{name}-{rid}-{line}-{col}-{i}", rule_id=rid, title=rid, cwe=cwe_values,
            severity=severity, range=rng, message=message, confidence=0.6,
            sources=[name], tool_provenance=[name, rid], detectors_fired=[rid],
            certainty="heuristic", kind="security", evidence={"tool": name, "native_rule": rid},
        ))
    return results


def merge_findings(findings: list[SecurityFindingV2]) -> list[SecurityFindingV2]:
    """Merge only identical ranges and shared CWE/category; preserve max severity and provenance."""
    merged: list[SecurityFindingV2] = []
    for item in findings:
        old_index = next((
            index for index, candidate in enumerate(merged)
            if (
                candidate.range.start_line, candidate.range.start_col,
                candidate.range.end_line, candidate.range.end_col,
            ) == (
                item.range.start_line, item.range.start_col,
                item.range.end_line, item.range.end_col,
            ) and (
                bool(set(candidate.cwe).intersection(item.cwe))
                or candidate.kind == item.kind
            )
        ), None)
        if old_index is None:
            merged.append(item)
            continue
        old = merged[old_index]
        winner = item if _SEVERITY.get(item.severity, 0) > _SEVERITY.get(old.severity, 0) else old
        provenance = list(dict.fromkeys([*old.tool_provenance, *item.tool_provenance]))
        detectors = list(dict.fromkeys([*old.detectors_fired, *item.detectors_fired]))
        sources = list(dict.fromkeys([*old.sources, *item.sources]))
        cwe = list(dict.fromkeys([*old.cwe, *item.cwe]))
        merged[old_index] = winner.model_copy(update={"tool_provenance": provenance, "detectors_fired": detectors, "sources": sources, "cwe": cwe})
    return merged


def findings_summary(findings: list[SecurityFindingV2]) -> dict[str, dict[str, int]]:
    severity = Counter(getattr(f.severity, "value", str(f.severity)) for f in findings)
    cwe = Counter(cwe for f in findings for cwe in f.cwe)
    known_tools = {"internal", "bandit", "cppcheck", "semgrep", "clang-tidy", "eslint"}
    tool = Counter(source for f in findings for source in set(f.tool_provenance or f.sources) if source in known_tools)
    return {"severity": dict(severity), "cwe": dict(cwe), "tool": dict(tool)}
