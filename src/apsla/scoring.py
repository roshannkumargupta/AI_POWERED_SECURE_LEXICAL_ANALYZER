"""Security score computation and finding aggregation."""

from __future__ import annotations

from apsla.config import (
    BASE_HEALTH_SCORE,
    SEVERITY_CAPS,
    SEVERITY_WEIGHTS,
)
from apsla.models import AnalysisSummary, Finding, Severity, TokenInfo


def compute_health_score(findings: list[Finding]) -> int:
    """Calculate the 0..100 security health score using capped penalties.

    Formula: max(0, 100 - sum(weight * min(count, cap)))

    Args:
        findings: List of detected security findings.

    Returns:
        int: Security health score from 0 (heavily vulnerable) to 100 (clean).
    """
    counts: dict[Severity, int] = {s: 0 for s in Severity}
    for f in findings:
        if not f.suppressed:
            counts[f.severity] = counts.get(f.severity, 0) + 1

    security_counts: dict[Severity, int] = {s: 0 for s in Severity}
    for f in findings:
        if not f.suppressed and f.kind == "security":
            security_counts[f.severity] += 1
    return calculate_health_score(security_counts)


def calculate_health_score(counts: dict[Severity, int]) -> int:
    """Calculate the 0..100 security health score directly from severity count mapping.

    Formula: max(0, 100 - sum(weight * min(count, cap)))
    """
    penalty = sum(
        SEVERITY_WEIGHTS[s] * min(counts.get(s, 0), SEVERITY_CAPS.get(s, 0))
        for s in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW)
    )
    return max(0, BASE_HEALTH_SCORE - penalty)


def create_analysis_summary(
    findings: list[Finding],
    tokens: list[TokenInfo] | None = None,
) -> AnalysisSummary:
    """Aggregate finding counts, token stats, and health score into AnalysisSummary.

    Args:
        findings: List of all findings from the analysis.
        tokens: Optional list of TokenInfo objects.

    Returns:
        AnalysisSummary: Populated summary metrics.
    """
    token_list = tokens or []
    counts: dict[Severity, int] = {s: 0 for s in Severity}
    for f in findings:
        if not f.suppressed:
            counts[f.severity] = counts.get(f.severity, 0) + 1

    score = compute_health_score(findings)

    tokens_malicious = sum(1 for t in token_list if t.label == "MALICIOUS")
    tokens_suspicious = sum(1 for t in token_list if t.label == "SUSPICIOUS")

    return AnalysisSummary(
        critical=counts[Severity.CRITICAL],
        high=counts[Severity.HIGH],
        medium=counts[Severity.MEDIUM],
        low=counts[Severity.LOW],
        info=counts[Severity.INFO],
        score=score,
        tokens_total=len(token_list),
        tokens_malicious=tokens_malicious,
        tokens_suspicious=tokens_suspicious,
        lexical_errors=sum(1 for f in findings if not f.suppressed and f.kind == "lexical"),
        syntax_errors=sum(1 for f in findings if not f.suppressed and f.kind == "syntax"),
    )
