"""Comprehensive tests for all rule-specific fix generators, idempotency, and syntax safety."""

import ast
from pathlib import Path

import pytest

from apsla.fixes.edits import apply_edits
from apsla.fixes.engine import fix_all
from apsla.pipeline import Analyzer

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VULN_DIR = REPO_ROOT / "tests" / "fixtures" / "python" / "vulnerable"
ADV_DIR = REPO_ROOT / "tests" / "fixtures" / "python" / "adversarial"


@pytest.mark.parametrize(
    ("fixture_rel", "target_rule"),
    [
        ("tests/fixtures/python/vulnerable/yaml_load_unsafe.py", "APS-PY-DES-002"),
        ("tests/fixtures/python/vulnerable/requests_verify_false.py", "APS-PY-NET-001"),
        ("tests/fixtures/python/vulnerable/crypto_md5_hash.py", "APS-PY-CRY-001"),
        ("tests/fixtures/python/vulnerable/cmd_injection_flask.py", "APS-PY-INJ-002"),
        ("tests/fixtures/python/vulnerable/subprocess_shell_true.py", "APS-PY-INJ-003"),
        ("tests/fixtures/python/vulnerable/sql_injection_concat.py", "APS-PY-INJ-004"),
        ("tests/fixtures/python/vulnerable/path_traversal_open.py", "APS-PY-IO-001"),
        ("tests/fixtures/python/vulnerable/xss_raw_markup.py", "APS-PY-XSS-001"),
        ("tests/fixtures/python/vulnerable/weak_random_secret.py", "APS-PY-CRY-002"),
        ("tests/fixtures/python/vulnerable/hardcoded_api_key.py", "APS-PY-SEC-001"),
        ("tests/fixtures/python/vulnerable/eval_dynamic_input.py", "APS-PY-INJ-001"),
        ("tests/fixtures/python/adversarial/trojan_source_bidi.py", "APS-ALL-UNI-001"),
        ("tests/fixtures/python/adversarial/zero_width_space_ident.py", "APS-ALL-UNI-002"),
        ("tests/fixtures/python/adversarial/cyrillic_homoglyph_exec.py", "APS-ALL-UNI-004"),
    ],
)
def test_generator_verified_on_fixture(fixture_rel: str, target_rule: str):
    file_path = REPO_ROOT / fixture_rel
    assert file_path.exists(), f"Fixture missing: {file_path}"
    source = file_path.read_text(encoding="utf-8")

    analyzer = Analyzer()
    result = analyzer.analyze(source, language="python", filename=file_path.name, options={"fixes": True})

    matching_findings = [f for f in result.findings if f.rule_id == target_rule]
    assert matching_findings, f"Target rule {target_rule} not detected in {fixture_rel}"

    # Verify at least one fix exists and is verified
    verified_fixes = []
    for f in matching_findings:
        for fix in f.fixes:
            if fix.verification.verified:
                verified_fixes.append(fix)

    assert verified_fixes, f"No verified fix generated for {target_rule} in {fixture_rel}"

    # Apply the verified fix and assert target rule is eliminated in fixed file
    best_fix = verified_fixes[0]
    if best_fix.edits:
        fixed_source = apply_edits(source, best_fix.edits)
        post_res = analyzer.analyze(fixed_source, language="python", filename=file_path.name, options={"fixes": False})
        post_rules = [f.rule_id for f in post_res.findings]
        assert target_rule not in post_rules, f"Rule {target_rule} still present in fixed file"


def test_fix_all_idempotency_on_all_vulnerable_fixtures():
    """Verify fix_all(fix_all(x)) == fix_all(x) across all vulnerable fixtures."""
    py_files = sorted(VULN_DIR.glob("*.py"))
    assert len(py_files) >= 20

    for py_file in py_files:
        source = py_file.read_text(encoding="utf-8")
        # Run fix_all with allow_review=True to ensure multi-pass convergence
        fixed_once, _, _, _, _, _ = fix_all(source, language="python", filename=py_file.name, allow_review=True)
        fixed_twice, applied_2, _, _, _, _ = fix_all(fixed_once, language="python", filename=py_file.name, allow_review=True)

        assert fixed_once == fixed_twice, (
            f"fix_all was not idempotent on {py_file.name}!\n"
            f"Pass 2 applied additional fixes: {applied_2}"
        )


def test_property_verified_fix_never_breaks_syntax():
    """Verify that applying any verified fix never causes ast.parse to fail."""
    py_files = sorted(VULN_DIR.glob("*.py")) + sorted(ADV_DIR.glob("*.py"))
    analyzer = Analyzer()

    for py_file in py_files:
        source = py_file.read_text(encoding="utf-8")
        res = analyzer.analyze(source, language="python", filename=py_file.name, options={"fixes": True})

        for finding in res.findings:
            for fix in finding.fixes:
                if fix.verification.verified and fix.edits:
                    fixed_code = apply_edits(source, fix.edits)
                    # Must parse cleanly without SyntaxError
                    try:
                        ast.parse(fixed_code)
                    except SyntaxError as exc:
                        pytest.fail(f"Verified fix for {finding.rule_id} produced invalid syntax: {exc}\n{fixed_code}")
