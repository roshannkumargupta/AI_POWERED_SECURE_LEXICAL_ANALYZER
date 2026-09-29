"""Integration tests for the end-to-end analysis pipeline."""

from __future__ import annotations

from apsla.models import AnalysisResult, Severity
from apsla.pipeline import Analyzer
from apsla.scoring import calculate_health_score


def test_clean_code_analysis():
    """Verify that benign code receives a perfect health score of 100 with zero findings."""
    code = """
def calculate_sum(a: int, b: int) -> int:
    # Standard clean implementation
    return a + b

result = calculate_sum(10, 20)
print(f"Result: {result}")
"""
    analyzer = Analyzer()
    result = analyzer.analyze(code, language="python", filename="math_utils.py")

    assert isinstance(result, AnalysisResult)
    assert len(result.findings) == 0
    assert result.summary.score == 100
    assert result.summary.critical == 0
    assert result.summary.high == 0
    assert result.summary.tokens_malicious == 0
    assert result.engine.version == "0.1.0"


def test_acceptance_criteria_cyrillic_exec():
    """Verify exact acceptance criteria execution from specification."""
    analyzer = Analyzer()
    # String from prompt: 'e\u0445ec(1)'
    result = analyzer.analyze("e\u0445ec(1)", language="python", filename="a.py", options={})

    assert result.summary.high >= 1
    assert result.summary.score < 100
    assert result.summary.tokens_total >= 1
    assert result.summary.tokens_malicious >= 1

    # Verify rule IDs present
    rule_ids = {f.rule_id for f in result.findings}
    assert "APS-ALL-UNI-006" in rule_ids


def test_pipeline_trojan_source_detection():
    """Verify end-to-end detection of Trojan Source attacks."""
    sample = "/* \u202e } \u2066if (isAdmin) \u2069 \u2066 */ return false;"
    analyzer = Analyzer()
    result = analyzer.analyze(sample, language="javascript", filename="auth.js")

    assert len(result.findings) >= 1
    assert any(f.rule_id == "APS-ALL-UNI-001" for f in result.findings)
    assert result.summary.high >= 1
    assert result.summary.score <= 88  # 100 - 12 = 88


def test_health_score_calculation_and_caps():
    """Verify penalty calculation and severity caps."""
    # 0 findings -> 100
    assert calculate_health_score({}) == 100

    # 1 critical (weight 25) -> 75
    assert calculate_health_score({Severity.CRITICAL: 1}) == 75

    # 5 criticals (cap 4) -> 100 - (4 * 25) = 0
    assert calculate_health_score({Severity.CRITICAL: 5}) == 0

    # 10 highs (cap 6, weight 12) -> 100 - (6 * 12) = 28
    assert calculate_health_score({Severity.HIGH: 10}) == 28

    # Mixed severities
    counts = {
        Severity.HIGH: 1,  # -12
        Severity.MEDIUM: 2,  # -10
        Severity.LOW: 3,  # -6
    }
    assert calculate_health_score(counts) == 100 - (12 + 10 + 6)


def test_pipeline_empty_string():
    """Verify analyzer handles empty source without crashing."""
    analyzer = Analyzer()
    result = analyzer.analyze("", language="python", filename="empty.py")

    assert result.summary.score == 100
    assert result.summary.tokens_total == 0
    assert len(result.findings) == 0


def test_pipeline_engine_metadata_and_timing():
    """Verify engine metadata contains valid execution timing and defaults."""
    analyzer = Analyzer({"ml_mode": "off"})
    result = analyzer.analyze("x = 42", language="python", filename="main.py")

    assert result.engine.ml_mode == "off"
    assert result.engine.elapsed_ms >= 0.0
    assert result.engine.version == "0.1.0"
