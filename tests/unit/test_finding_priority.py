from apsla.config import (
    EXPLOITABILITY_DANGEROUS_SINK,
    EXPLOITABILITY_INFO,
    EXPLOITABILITY_TAINT_CONFIRMED,
    EXPLOITABILITY_WEAK_CRYPTO_CONFIG,
    SEVERITY_WEIGHTS,
)
from apsla.models import Finding, Range, Severity
from apsla.prioritization import (
    compute_priority,
    determine_exploitability,
    prioritize_and_sort_findings,
)


def _make_finding(
    rule_id: str,
    severity: Severity,
    confidence: float,
    taint_confirmed: bool = False,
    is_dangerous_sink: bool = False,
    line: int = 1,
) -> Finding:
    evidence = {}
    if taint_confirmed:
        evidence["taint_confirmed"] = True
    elif is_dangerous_sink:
        evidence["taint_candidate"] = True

    return Finding(
        id=f"f-{rule_id}-{line}",
        rule_id=rule_id,
        severity=severity,
        confidence=confidence,
        message=f"Test finding {rule_id}",
        range=Range(start_line=line, start_col=1, end_line=line, end_col=10),
        evidence=evidence,
    )


def test_exploitability_weights():
    """Verify exploitability rules adhere strictly to finding priority specifications."""
    # 1.0 if taint confirmed
    f_taint = _make_finding("APS-PY-INJ-001", Severity.HIGH, 0.9, taint_confirmed=True)
    assert determine_exploitability(f_taint) == EXPLOITABILITY_TAINT_CONFIRMED
    assert EXPLOITABILITY_TAINT_CONFIRMED == 1.0

    # 0.7 if dangerous sink but no confirmed taint path
    f_sink = _make_finding("APS-PY-INJ-001", Severity.HIGH, 0.9, is_dangerous_sink=True)
    assert determine_exploitability(f_sink) == EXPLOITABILITY_DANGEROUS_SINK
    assert EXPLOITABILITY_DANGEROUS_SINK == 0.7

    # 0.5 for weak crypto / config
    f_crypto = _make_finding("APS-PY-CRYPTO-001", Severity.MEDIUM, 0.8)
    assert determine_exploitability(f_crypto) == EXPLOITABILITY_WEAK_CRYPTO_CONFIG
    assert EXPLOITABILITY_WEAK_CRYPTO_CONFIG == 0.5

    # 0.3 for info / style / notice
    f_info = _make_finding("APS-PY-INFO-001", Severity.INFO, 0.5)
    assert determine_exploitability(f_info) == EXPLOITABILITY_INFO
    assert EXPLOITABILITY_INFO == 0.3


def test_compute_priority():
    """Verify priority = severity_weight x confidence x exploitability."""
    # High (3) x 0.8 x 1.0 = 2.40
    f = _make_finding("APS-PY-INJ-001", Severity.HIGH, 0.8, taint_confirmed=True)
    prio = compute_priority(f)
    expected = SEVERITY_WEIGHTS[Severity.HIGH] * 0.8 * 1.0
    assert prio == round(expected, 4)


def test_prioritize_and_sort_findings():
    """Verify findings are sorted descending by calculated risk priority."""
    f1 = _make_finding("APS-PY-CRYPTO-001", Severity.MEDIUM, 0.8, line=10)  # Med(2)*0.8*0.5 = 0.8
    f2 = _make_finding(
        "APS-PY-INJ-001", Severity.CRITICAL, 0.9, taint_confirmed=True, line=5
    )  # Crit(4)*0.9*1.0 = 3.6
    f3 = _make_finding("APS-PY-INFO-001", Severity.INFO, 0.5, line=2)  # Info(0)*0.5*0.3 = 0.0

    sorted_findings = prioritize_and_sort_findings([f1, f2, f3])
    assert len(sorted_findings) == 3
    assert sorted_findings[0].id == f2.id
    assert sorted_findings[1].id == f1.id
    assert sorted_findings[2].id == f3.id
    assert sorted_findings[0].priority > sorted_findings[1].priority >= sorted_findings[2].priority
