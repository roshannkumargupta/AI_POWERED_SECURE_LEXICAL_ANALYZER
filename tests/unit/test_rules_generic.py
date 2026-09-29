"""Tests for language-independent Unicode defense rules (APS-ALL-UNI-001 through 006)."""

from __future__ import annotations

from apsla.models import Label, Severity
from apsla.rules.generic import evaluate_unicode_rules


def test_rule_uni_001_bidi_trojan_source():
    """Verify APS-ALL-UNI-001 flags Trojan Source bidi control characters."""
    sample = "x = 1; \u202e # sneaky comment"
    findings = evaluate_unicode_rules(sample)

    matches = [f for f in findings if f.rule_id == "APS-ALL-UNI-001"]
    assert len(matches) == 1
    f = matches[0]
    assert f.severity == Severity.HIGH
    assert f.label == Label.MALICIOUS
    assert f.fixes[0].edits[0].new_text == ""


def test_rule_uni_002_zero_width_in_identifier():
    """Verify APS-ALL-UNI-002 flags zero-width invisible characters."""
    sample = "auth\u200btoken = 'secret'"
    findings = evaluate_unicode_rules(sample)

    matches = [f for f in findings if f.rule_id == "APS-ALL-UNI-002"]
    assert len(matches) == 1
    f = matches[0]
    assert f.severity == Severity.HIGH
    assert f.label == Label.MALICIOUS
    assert f.fixes[0].edits[0].new_text == ""


def test_rule_uni_003_unicode_tags():
    """Verify APS-ALL-UNI-003 flags deprecated Unicode tag characters."""
    sample = "key\U000e0020value = 1"
    findings = evaluate_unicode_rules(sample)

    matches = [f for f in findings if f.rule_id == "APS-ALL-UNI-003"]
    assert len(matches) == 1
    f = matches[0]
    assert f.severity == Severity.HIGH
    assert f.label == Label.MALICIOUS


def test_rule_uni_004_confusable_character():
    """Verify APS-ALL-UNI-004 flags confusable look-alike character in safe identifiers."""
    # Cyrillic small 'o' (U+043E) in variable name 'n\u043Ede'
    sample = "n\u043ede = 5"
    findings = evaluate_unicode_rules(sample)

    matches = [f for f in findings if f.rule_id == "APS-ALL-UNI-004"]
    assert len(matches) == 1
    f = matches[0]
    assert f.severity == Severity.MEDIUM
    assert f.evidence["recovered_to"] == "o"


def test_rule_uni_005_mixed_script_identifier():
    """Verify APS-ALL-UNI-005 flags mixed-script identifier."""
    # 'test_\u0430' (Latin 'test_' and Cyrillic '\u0430')
    sample = "test_\u0430 = True"
    findings = evaluate_unicode_rules(sample)

    matches = [f for f in findings if f.rule_id == "APS-ALL-UNI-005"]
    assert len(matches) == 1
    f = matches[0]
    assert f.severity == Severity.MEDIUM
    assert "Latin" in f.message and "Cyrillic" in f.message


def test_rule_uni_006_dangerous_recovery():
    """Verify APS-ALL-UNI-006 flags obfuscated dangerous built-ins/keywords."""
    # Pure Cyrillic '\u0435\u0445\u0435\u0441' -> 'exec'
    cyrillic_exec = "\u0435\u0445\u0435\u0441('rm -rf /')"
    findings = evaluate_unicode_rules(cyrillic_exec)

    matches = [f for f in findings if f.rule_id == "APS-ALL-UNI-006"]
    assert len(matches) == 1
    f = matches[0]
    assert f.severity == Severity.HIGH
    assert f.label == Label.MALICIOUS
    assert f.evidence["recovered_to"] == "exec"
    assert f.fixes[0].edits[0].new_text == "exec"
