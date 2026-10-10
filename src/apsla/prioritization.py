"""Finding prioritization and exploitability calculation according to Phase 12 specification."""

from __future__ import annotations

from typing import Final

from apsla.config import (
    EXPLOITABILITY_DANGEROUS_SINK,
    EXPLOITABILITY_INFO,
    EXPLOITABILITY_TAINT_CONFIRMED,
    EXPLOITABILITY_WEAK_CRYPTO_CONFIG,
    SEVERITY_WEIGHTS,
)
from apsla.models import Finding, Severity

# Categorization heuristics for exploitability
_DANGEROUS_SINK_MARKERS: Final[tuple[str, ...]] = (
    "INJ",
    "EXEC",
    "CMD",
    "SQL",
    "XSS",
    "MEM",
    "BUF",
    "FMT",
    "IO-001",
    "DES",
    "OVERFLOW",
)

_WEAK_CRYPTO_CONFIG_MARKERS: Final[tuple[str, ...]] = (
    "CRY",
    "SEC",
    "CFG",
    "XML",
    "XXE",
    "OBF",
    "NET",
    "HARDCODED",
    "WEAK",
)


def compute_exploitability(finding: Finding) -> float:
    """Calculate exploitability factor according to Phase 12 specification.

    1.0 if taint confirmed
    0.7 if the sink is dangerous but no taint path
    0.5 for weak-crypto/config rules
    0.3 for info

    Args:
        finding: Finding instance to evaluate.

    Returns:
        float: Exploitability multiplier (1.0, 0.7, 0.5, or 0.3).
    """
    if finding.severity == Severity.INFO or finding.kind in ("lexical", "syntax"):
        return EXPLOITABILITY_INFO

    # 1.0 if taint confirmed
    taint_confirmed = (
        ("taint" in finding.sources)
        or bool(finding.evidence.get("taint_confirmed", False))
        or (
            bool(finding.taint_path)
            and any(
                getattr(step, "step", "") in ("sink", "sink_call")
                or str(getattr(step, "step", "")).lower() == "sink"
                for step in finding.taint_path
            )
        )
    )
    if taint_confirmed:
        return EXPLOITABILITY_TAINT_CONFIRMED

    # 0.7 if the sink is dangerous but no taint path
    rule_upper = finding.rule_id.upper()
    title_upper = finding.title.upper()

    is_dangerous_sink = any(m in rule_upper for m in _DANGEROUS_SINK_MARKERS) or any(
        m in title_upper
        for m in ("INJECTION", "EXEC", "COMMAND", "SQL", "BUFFER", "FORMAT STRING", "TRAVERSAL")
    )
    if is_dangerous_sink:
        return EXPLOITABILITY_DANGEROUS_SINK

    # 0.5 for weak-crypto/config rules
    is_weak_crypto_config = any(m in rule_upper for m in _WEAK_CRYPTO_CONFIG_MARKERS) or any(
        m in title_upper for m in ("CRYPTO", "HASH", "CIPHER", "SECRET", "CONFIG", "SSL", "TLS")
    )
    if is_weak_crypto_config:
        return EXPLOITABILITY_WEAK_CRYPTO_CONFIG

    # 0.3 for info / other
    return EXPLOITABILITY_INFO


def compute_priority(finding: Finding) -> float:
    """Compute overall finding priority = severity_weight x confidence x exploitability.

    Args:
        finding: Finding instance.

    Returns:
        float: Rounded priority score.
    """
    weight = SEVERITY_WEIGHTS.get(finding.severity, 0)
    exploitability = compute_exploitability(finding)
    return round(weight * finding.confidence * exploitability, 4)


def apply_prioritization(findings: list[Finding]) -> list[Finding]:
    """Calculate exploitability and priority for all findings and sort by priority descending.

    Args:
        findings: Input findings.

    Returns:
        Prioritized and sorted findings.
    """
    from apsla.fusion import SEVERITY_ORDER

    updated: list[Finding] = []
    for f in findings:
        exp = compute_exploitability(f)
        weight = SEVERITY_WEIGHTS.get(f.severity, 0)
        prio = round(weight * f.confidence * exp, 4)
        updated.append(f.model_copy(update={"exploitability": exp, "priority": prio}))

    def _sort_key(f: Finding) -> tuple[float, int, float, int]:
        sev_rank = SEVERITY_ORDER.index(f.severity) if f.severity in SEVERITY_ORDER else 0
        return (-f.priority, -sev_rank, -f.confidence, f.range.start_line)

    updated.sort(key=_sort_key)
    return updated


determine_exploitability = compute_exploitability
prioritize_and_sort_findings = apply_prioritization
