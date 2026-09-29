"""Test runner executing all Phase 2 Python fixtures and verifying exact (rule_id, line) matches."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsla.models import Severity
from apsla.pipeline import Analyzer

FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "python"


def get_all_fixtures() -> list[tuple[Path, list[dict[str, str | int]]]]:
    """Collect all python fixture paths along with their expected findings."""
    fixtures: list[tuple[Path, list[dict[str, str | int]]]] = []

    for cat in ("vulnerable", "safe", "adversarial"):
        cat_dir = FIXTURES_ROOT / cat
        if not cat_dir.exists():
            continue

        for py_file in sorted(cat_dir.glob("*.py")):
            expect_file = cat_dir / f"{py_file.stem}.expect.json"
            if expect_file.exists():
                expected = json.loads(expect_file.read_text(encoding="utf-8"))
            else:
                expected = []
            fixtures.append((py_file, expected))

    return fixtures


ALL_FIXTURES = get_all_fixtures()


@pytest.mark.parametrize("py_file,expected", ALL_FIXTURES, ids=[f[0].name for f in ALL_FIXTURES])
def test_python_fixture(py_file: Path, expected: list[dict[str, str | int]]) -> None:
    """Verify that analyzing a fixture produces the exact expected (rule_id, line) findings."""
    source = py_file.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language="python", filename=py_file.name)

    actual_pairs = {
        (f.rule_id, f.range.start_line)
        for f in result.findings
        if not f.suppressed
    }
    expected_pairs = {
        (str(e["rule_id"]), int(e["line"]))
        for e in expected
    }

    assert actual_pairs == expected_pairs, (
        f"Fixture {py_file.name} mismatch!\n"
        f"Expected: {sorted(expected_pairs)}\n"
        f"Actual:   {sorted(actual_pairs)}\n"
        f"Findings: {result.findings}"
    )


def test_senior_probe_1_flask_taint_path():
    """Probe 1: Flask request taint reaches os.system sink with 3+ taint steps."""
    fixture_path = FIXTURES_ROOT / "vulnerable" / "cmd_injection_flask.py"
    source = fixture_path.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language="python", filename=fixture_path.name)

    # 1. Finding must exist
    inj_findings = [f for f in result.findings if f.rule_id == "APS-PY-INJ-002" and not f.suppressed]
    assert len(inj_findings) == 1, "Expected exactly 1 finding for APS-PY-INJ-002"

    f = inj_findings[0]
    assert f.severity == Severity.CRITICAL, "Taint-confirmed finding must be boosted to CRITICAL"
    assert f.range.start_line == 2

    # 2. Taint path must contain at least 3 steps: source -> propagate -> sink
    assert len(f.taint_path) >= 3, f"Expected 3+ taint steps, got {len(f.taint_path)}: {f.taint_path}"
    assert f.taint_path[0].step.value == "source"
    assert f.taint_path[-1].step.value == "sink"


def test_senior_probe_2_input_seq_taint():
    """Probe 2: Sequential input() taint reaches os.system(v) with full path."""
    fixture_path = FIXTURES_ROOT / "vulnerable" / "cmd_injection_input_seq.py"
    source = fixture_path.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language="python", filename=fixture_path.name)

    inj_findings = [f for f in result.findings if f.rule_id == "APS-PY-INJ-002" and not f.suppressed]
    assert len(inj_findings) == 1
    f = inj_findings[0]
    assert len(f.taint_path) >= 3


def test_senior_probe_3_shlex_quote_not_flagged():
    """Probe 3: Sanitized input via shlex.quote() is NOT flagged."""
    fixture_path = FIXTURES_ROOT / "safe" / "cmd_sanitized_shlex.py"
    source = fixture_path.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language="python", filename=fixture_path.name)

    active_findings = [f for f in result.findings if not f.suppressed]
    assert len(active_findings) == 0, f"Expected 0 findings for shlex.quote fixture, got: {active_findings}"
    assert result.summary.score == 100


def test_senior_probe_4_subprocess_list_safe():
    """Probe 4: Subprocess list form without shell=True is NOT flagged."""
    fixture_path = FIXTURES_ROOT / "safe" / "subprocess_list_safe.py"
    source = fixture_path.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language="python", filename=fixture_path.name)

    active_findings = [f for f in result.findings if not f.suppressed]
    assert len(active_findings) == 0
    assert result.summary.score == 100


def test_senior_probe_5_bidi_flagged():
    """Probe 5: Trojan Source bidi control override is flagged."""
    fixture_path = FIXTURES_ROOT / "adversarial" / "trojan_source_bidi.py"
    source = fixture_path.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language="python", filename=fixture_path.name)

    uni_findings = [f for f in result.findings if f.rule_id == "APS-ALL-UNI-001" and not f.suppressed]
    assert len(uni_findings) >= 1


def test_senior_probe_6_cyrillic_exec_is_high():
    """Probe 6: Cyrillic exec homoglyph is flagged as Unicode and high APS-PY-INJ-001."""
    fixture_path = FIXTURES_ROOT / "adversarial" / "cyrillic_homoglyph_exec.py"
    source = fixture_path.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language="python", filename=fixture_path.name)

    uni_findings = [f for f in result.findings if f.rule_id in ("APS-ALL-UNI-004", "APS-ALL-UNI-006")]
    assert len(uni_findings) >= 1

    inj_findings = [f for f in result.findings if f.rule_id == "APS-PY-INJ-001" and not f.suppressed]
    assert len(inj_findings) == 1
    assert inj_findings[0].severity in (Severity.HIGH, Severity.CRITICAL)


def test_senior_wrong_variable_bug_gone():
    """Verify that using an un-tainted variable alongside a tainted variable does not flag."""
    fixture_path = FIXTURES_ROOT / "safe" / "cmd_wrong_variable_safe.py"
    source = fixture_path.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language="python", filename=fixture_path.name)

    active_findings = [f for f in result.findings if not f.suppressed]
    assert len(active_findings) == 0, f"Expected 0 findings for wrong variable safe fixture, got: {active_findings}"
    assert result.summary.score == 100
