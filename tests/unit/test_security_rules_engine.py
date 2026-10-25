from __future__ import annotations

import json
from pathlib import Path

from apsla.models import Range, Severity
from apsla.models_v2 import SecurityFindingV2
from apsla.parsing_v2 import parse_source
from apsla.quality_v2 import measure_quality
from apsla.security_v2 import (
    build_rule_registry,
    findings_summary,
    merge_findings,
    normalize_external,
)
from apsla.server.app import app

ROOT = Path(__file__).resolve().parents[1]


def _finding(rule: str, severity: Severity, tool: str) -> SecurityFindingV2:
    return SecurityFindingV2(
        id=rule, rule_id=rule, cwe=["CWE-78"], severity=severity,
        range=Range(start_line=1, start_col=1, end_line=1, end_col=4),
        message="Detected for test.", sources=[tool], tool_provenance=[tool],
    )


def test_rule_registry_contains_declared_metadata():
    rules = build_rule_registry()
    assert rules and all(rule["id"] and rule["languages"] and "safe_pattern" in rule for rule in rules)
    assert len({rule["id"] for rule in rules}) == len(rules)


def test_security_stage_contract_exposes_summary_and_taint_paths():
    schema = app.openapi()["components"]["schemas"]["StageAnalysisResponse"]["properties"]
    assert "findings_summary" in schema
    assert "taint_paths" in schema


def test_bandit_recorded_output_normalizes_cwe_range_and_provenance():
    parsed = json.loads((ROOT / "fixtures/security_adapter_outputs/bandit.json").read_text())
    findings = normalize_external("bandit", parsed, "x = 1\neval(x)\n", "python")
    assert len(findings) == 1
    assert findings[0].cwe == ["CWE-95"]
    assert findings[0].range.start_line == 2
    assert findings[0].tool_provenance == ["bandit", "B307"]


def test_cppcheck_recorded_output_normalizes_xml_metadata():
    xml = (ROOT / "fixtures/security_adapter_outputs/cppcheck.xml").read_text()
    findings = normalize_external("cppcheck", xml, "int f() {\n  int a[1];\n  return a[2];\n}\n", "cpp")
    assert findings and findings[0].cwe == ["CWE-120"]
    assert findings[0].range.start_line == 3


def test_dedupe_keeps_highest_severity_and_combines_provenance():
    output = merge_findings([_finding("a", Severity.LOW, "internal"), _finding("b", Severity.HIGH, "bandit")])
    assert len(output) == 1
    assert output[0].severity == Severity.HIGH
    assert set(output[0].tool_provenance) == {"internal", "bandit"}
    assert findings_summary(output)["severity"] == {"high": 1}


def test_dedupe_uses_shared_cwe_when_metadata_sets_differ():
    first = _finding("a", Severity.MEDIUM, "internal")
    second = _finding("b", Severity.HIGH, "bandit").model_copy(update={"cwe": ["CWE-78", "CWE-22"]})
    output = merge_findings([first, second])
    assert len(output) == 1
    assert set(output[0].cwe) == {"CWE-78", "CWE-22"}
    assert output[0].severity == Severity.HIGH


def test_unmapped_external_rule_does_not_claim_a_cwe():
    parsed = [{"filePath": "input.js", "messages": [{"ruleId": "unknown/security", "line": 1, "message": "recorded fixture", "severity": 2}]}]
    result = normalize_external("eslint", parsed, "x();\n", "javascript")
    assert result and result[0].cwe == []


def test_quality_is_measured_from_function_nodes_for_supported_languages():
    sources = {
        "python": "def f(x):\n    if x:\n        return 1\n    return 0\n",
        "java": "class A { int f(int x) { if (x > 0) return 1; return 0; } }",
        "javascript": "function f(x) { if (x) return 1; return 0; }",
        "cpp": "int f(int x) { if (x) return 1; return 0; }",
    }
    for language, source in sources.items():
        outcome = parse_source(language, source, f"quality-{language}")
        observations = measure_quality(language, source, outcome.tree)
        assert observations and all(item.measured for item in observations)
        assert {item.kind for item in observations} == {"cyclomatic_complexity", "function_length", "nesting_depth", "parameter_count"}
