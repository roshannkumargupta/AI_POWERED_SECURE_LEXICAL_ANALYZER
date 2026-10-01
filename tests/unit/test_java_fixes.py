"""Unit tests for Java fix generators, verification, and idempotency."""

from pathlib import Path

import pytest

from apsla.fixes.edits import apply_edits
from apsla.fixes.engine import fix_all
from apsla.languages.registry import get as get_plugin
from apsla.pipeline import Analyzer

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JAVA_VULN_DIR = REPO_ROOT / "tests" / "fixtures" / "java" / "vulnerable"
JAVA_ADV_DIR = REPO_ROOT / "tests" / "fixtures" / "java" / "adversarial"


@pytest.mark.parametrize(
    ("fixture_name", "target_rule"),
    [
        ("sqli_servlet.java", "APS-JV-INJ-002"),
        ("cmd_injection_runtime_exec.java", "APS-JV-INJ-001"),
        ("crypto_md5.java", "APS-JV-CRY-001"),
        ("crypto_des.java", "APS-JV-CRY-002"),
        ("insecure_random_token.java", "APS-JV-CRY-003"),
        ("hardcoded_api_key.java", "APS-JV-SEC-001"),
        ("xxe_document_builder.java", "APS-JV-XML-001"),
    ],
)
def test_java_generator_verified_on_fixture(fixture_name: str, target_rule: str) -> None:
    """Verify that each Java fix generator produces a verified fix on its fixture."""
    file_path = JAVA_VULN_DIR / fixture_name
    assert file_path.exists(), f"Fixture missing: {file_path}"
    source = file_path.read_text(encoding="utf-8")

    analyzer = Analyzer()
    result = analyzer.analyze(
        source, language="java", filename=file_path.name, options={"fixes": True}
    )

    matching_findings = [f for f in result.findings if f.rule_id == target_rule]
    assert matching_findings, f"Target rule {target_rule} not found in {fixture_name}"

    verified_fixes = []
    for f in matching_findings:
        for fix in f.fixes:
            if fix.verification.verified:
                verified_fixes.append(fix)

    assert verified_fixes, f"No verified fix generated for {target_rule} in {fixture_name}"

    best_fix = verified_fixes[0]
    if best_fix.edits:
        fixed_source = apply_edits(source, best_fix.edits)
        post_res = analyzer.analyze(
            fixed_source, language="java", filename=file_path.name, options={"fixes": False}
        )
        post_rules = [f.rule_id for f in post_res.findings]
        assert target_rule not in post_rules, f"Rule {target_rule} still present after fix"


def test_fix_all_idempotency_on_java_vulnerable_fixtures() -> None:
    """Verify fix_all(fix_all(x)) == fix_all(x) across Java vulnerable fixtures."""
    java_files = sorted(JAVA_VULN_DIR.glob("*.java"))
    assert len(java_files) >= 20

    for jf in java_files:
        source = jf.read_text(encoding="utf-8")
        fixed_once, _, _, _, _, _ = fix_all(
            source, language="java", filename=jf.name, allow_review=True
        )
        fixed_twice, applied_2, _, _, _, _ = fix_all(
            fixed_once, language="java", filename=jf.name, allow_review=True
        )

        assert fixed_once == fixed_twice, (
            f"fix_all was not idempotent on {jf.name}!\n"
            f"Pass 2 applied additional fixes: {applied_2}"
        )


def test_verified_java_fix_preserves_syntax() -> None:
    """Verify that applying any verified fix preserves Java syntax."""
    plugin = get_plugin("java")
    analyzer = Analyzer()

    for jf in sorted(JAVA_VULN_DIR.glob("*.java")) + sorted(JAVA_ADV_DIR.glob("*.java")):
        source = jf.read_text(encoding="utf-8")
        res = analyzer.analyze(source, language="java", filename=jf.name, options={"fixes": True})
        for f in res.findings:
            for fix in f.fixes:
                if fix.verification.verified and fix.edits:
                    fixed_code = apply_edits(source, fix.edits)
                    ok, err = plugin.syntax_check(fixed_code)
                    assert ok, f"Fix for {f.rule_id} on {jf.name} broke Java syntax: {err}"
