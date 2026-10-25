"""Regression coverage for the additive UI-5 API model fields."""

from __future__ import annotations

import pytest

from apsla.fusion import _indicative_attack
from apsla.models import Finding, Range, Severity
from apsla.pipeline import Analyzer
from apsla.scoring import compute_health_score, create_analysis_summary


def _finding(
    *, kind: str = "security", cwe: str = "CWE-78", rule_id: str = "APS-PY-INJ-002"
) -> Finding:
    return Finding(
        id="f",
        rule_id=rule_id,
        title="test",
        cwe=cwe,
        severity=Severity.HIGH,
        label="MALICIOUS",
        confidence=0.8,
        range=Range(start_line=1, start_col=1, end_line=1, end_col=2),
        message="test",
        explanation="test",
        kind=kind,
    )


def test_lexical_and_syntax_diagnostics_do_not_change_security_score() -> None:
    security = _finding()
    extra = [_finding(kind="lexical"), _finding(kind="syntax")]
    assert compute_health_score([security]) == compute_health_score([security, *extra])
    summary = create_analysis_summary([*extra])
    assert summary.lexical_errors == 1
    assert summary.syntax_errors == 1
    assert summary.score == 100


def test_ui5_demo_reports_lexical_and_parser_findings_without_taint_path() -> None:
    source = 'import os\nname = request.args.get("q")\nos.system("ls " + name)\npw = "admin123"\nmsg = "hello with no closing quote.\n'
    result = Analyzer().analyze(
        source, language="python", filename="ui5-lexical.py", options={"ml": False}
    )
    lexical = next(f for f in result.findings if f.kind == "lexical")
    syntax = next(f for f in result.findings if f.kind == "syntax")
    assert lexical.rule_id == "APS-PY-LEX-001"
    assert lexical.severity == Severity.HIGH
    assert "line 5, col 7" in lexical.message
    assert lexical.fixes and lexical.fixes[0].confidence in {"review", "manual"}
    assert syntax.rule_id == "APS-PY-SYN-001"
    assert result.engine.parser == "python-ast"
    # ast.parse rejects this file before Python taint analysis can recover the earlier source-to-sink path.
    injection = next((f for f in result.findings if f.rule_id == "APS-PY-INJ-002"), None)
    assert injection is None or not injection.taint_path


def test_backend_metadata_is_additive_and_attack_mapping_is_sparse() -> None:
    source = "import os\nname = input()\nos.system(name)\n"
    result = Analyzer().analyze(source, language="python", options={"ml": False})
    finding = next(f for f in result.findings if f.cwe == "CWE-78")
    assert finding.attack == ["T1059"]
    assert result.engine.parser == "python-ast"
    assert result.engine.taint == "ast-flow"
    assert finding.evidence["confidence_breakdown"]["fused"] == finding.confidence
    assert finding.evidence["confidence_breakdown"]["ml_mode"] == "off"
    assert _finding(cwe="CWE-89").attack is None


def test_indicative_attack_tags_cover_unicode_and_credentials_only() -> None:
    assert _indicative_attack(_finding(cwe="CWE-798")) == ["T1552"]
    assert _indicative_attack(_finding(rule_id="APS-ALL-UNI-006", cwe="CWE-1007")) == ["T1036"]
    assert _indicative_attack(_finding(cwe="CWE-89")) is None


def test_non_python_parser_metadata_remains_lexer_only() -> None:
    sources = {
        "java": "class Demo {}",
        "javascript": "const value = 1;",
        "cpp": "int main() { return 0; }",
    }
    for language, source in sources.items():
        result = Analyzer().analyze(
            source, language=language, options={"ml": False, "fixes": False}
        )
        assert result.engine.parser == "lexer-only"


def test_valid_python_file_gets_no_parser_or_lexer_diagnostic() -> None:
    result = Analyzer().analyze("value = 'ok'\n", language="python", options={"ml": False})
    assert not [f for f in result.findings if f.kind in {"lexical", "syntax"}]


@pytest.mark.parametrize(
    ("language", "source", "rule_id"),
    [
        ("python", 'value = "bad\n', "APS-PY-LEX-001"),
        ("java", 'class Demo { String value = "bad; }', "APS-JAVA-LEX-001"),
        ("javascript", 'const value = "bad;', "APS-JS-LEX-001"),
        ("cpp", 'const char* value = "bad;', "APS-CP-LEX-001"),
    ],
)
def test_unterminated_string_diagnostic_and_verified_fix_are_available(
    language: str, source: str, rule_id: str
) -> None:
    result = Analyzer().analyze(source, language=language, options={"ml": False})
    finding = next(item for item in result.findings if item.kind == "lexical")
    assert finding.rule_id == rule_id
    assert finding.fixes
    assert finding.fixes[0].confidence in {"review", "manual"}
    if finding.fixes[0].verification.verified:
        assert finding.fixes[0].edits[0].new_text == '"'
