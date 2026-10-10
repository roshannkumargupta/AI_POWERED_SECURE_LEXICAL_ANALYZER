"""Fusion engine implementing PROJECT_SPEC Section H: Score & Finding Fusion Rules."""

from __future__ import annotations

from typing import Any, Final

import numpy as np

from apsla.config import (
    ML_ONLY_FINDINGS_CAP,
    ML_WEIGHT,
    NOISY_RULE_ML_THRESHOLD,
    RULE_WEIGHT,
    TAINT_CONFIDENCE_BONUS,
)
from apsla.cwe import get_cwe_for_category
from apsla.lexing.token import Token
from apsla.models import Finding, Label, Severity

SEVERITY_ORDER: Final[list[Severity]] = [
    Severity.INFO,
    Severity.LOW,
    Severity.MEDIUM,
    Severity.HIGH,
    Severity.CRITICAL,
]


def _load_suppressed_signatures() -> tuple[
    set[tuple[str, str, int]], set[str], set[tuple[str, int]]
]:
    """Loads suppressed finding signatures (rule_id, filename, line), fingerprints, and (rule_id, line)."""
    signatures: set[tuple[str, str, int]] = set()
    fingerprints: set[str] = set()
    rule_lines: set[tuple[str, int]] = set()

    from apsla.feedback.store import load_all_feedback

    for record in load_all_feedback():
        rule_id = record.get("rule_id", "")
        fname = record.get("filename", "")
        line_val = record.get("line")
        line_no = int(line_val) if line_val is not None else 0
        fp = record.get("fingerprint") or record.get("finding_fingerprint", "")
        if fp:
            fingerprints.add(fp)
            parts = fp.split("-")
            if len(parts) >= 4 and parts[-3].isdigit():
                rule_lines.add((rule_id or "-".join(parts[:-3]), int(parts[-3])))
            elif len(parts) >= 3 and parts[-2].isdigit():
                rule_lines.add((rule_id or "-".join(parts[:-2]), int(parts[-2])))
        if rule_id and line_no:
            rule_lines.add((rule_id, line_no))
        if rule_id and fname and line_no:
            signatures.add((rule_id, fname, line_no))
    return signatures, fingerprints, rule_lines


def fuse_findings(
    rule_findings: list[Finding],
    tokens: list[Token],
    ml_probabilities: np.ndarray | None,
    ml_mode: str = "off",
    ml_threshold_malicious: float = 0.5,
    filename: str = "<editor>",
) -> list[Finding]:
    """Applies PROJECT_SPEC Section H fusion rules across rule, taint, and ML detections.

    Rules applied:
    1. ml_p = min(1.0, max_{t in range} (P(MALICIOUS) + 0.5 * P(SUSPICIOUS)))
    2. Confidence:
       - If ML is 'on': Confidence = 0.7 * rule_conf + 0.3 * ml_p
       - If ML is 'off': Confidence = rule_conf
    3. Taint Confirmation Boost:
       If data-flow taint analysis confirms reachability from source to sink:
           Confidence = min(1.0, Confidence + 0.15)
           Severity <- min(CRITICAL, Severity + 1)
    4. Noisy Rule Suppression / Downgrade:
       If a rule triggers without taint confirmation and ml_p < 0.15:
           Severity <- max(INFO, Severity - 1)
           Note: 'downgraded: model sees this as usual code'
    5. ML-Only Anomaly Rule:
       Pure ML detections without matching rules generate findings under rule
       APS-ALL-ML-001 (capped at maximum 10 per file).
    6. Suppression:
       Findings matching data/feedback/false_positives.jsonl are marked suppressed=True.
    7. Sorting Order:
       Severity descending -> Confidence descending -> Source line ascending.

    Args:
        rule_findings: List of candidate findings from rules and taint analysis.
        tokens: Token stream from lexing.
        ml_probabilities: Optional (N, 3) array of [P(SAFE), P(SUSP), P(MAL)] per token.
        ml_mode: 'on' or 'off'.
        ml_threshold_malicious: Threshold tau for ML anomaly detection.
        filename: Target filename for suppression signature matching.

    Returns:
        Fused, calibrated, ranked, and sorted list of Finding instances.
    """
    suppressed_sigs, suppressed_fps, suppressed_rule_lines = _load_suppressed_signatures()
    fused_findings: list[Finding] = []
    claimed_token_indices: set[int] = set()

    is_ml_active = (
        ml_mode == "on"
        and ml_probabilities is not None
        and len(ml_probabilities) == len(tokens)
        and len(tokens) > 0
    )

    for finding in rule_findings:
        rng = finding.range

        # Compute token indices overlapping this finding
        overlapping_indices: list[int] = []
        for i, tok in enumerate(tokens):
            t_rng = tok.to_range()
            no_overlap = (
                t_rng.end_line < rng.start_line
                or rng.end_line < t_rng.start_line
                or (t_rng.end_line == rng.start_line and t_rng.end_col <= rng.start_col)
                or (rng.end_line == t_rng.start_line and rng.end_col <= t_rng.start_col)
            )
            if not no_overlap:
                overlapping_indices.append(i)
                claimed_token_indices.add(i)

        # 1. Compute ml_p over overlapping tokens
        ml_p = 0.0
        if is_ml_active and ml_probabilities is not None and overlapping_indices:
            token_p_vals = []
            for idx in overlapping_indices:
                p_safe, p_susp, p_mal = ml_probabilities[idx]
                token_p_vals.append(p_mal + 0.5 * p_susp)
            ml_p = min(1.0, float(max(token_p_vals)))

        # 2. Confidence Calculation
        rule_conf = finding.confidence
        conf = RULE_WEIGHT * rule_conf + ML_WEIGHT * ml_p if is_ml_active else rule_conf

        # 3. Taint Confirmation Boost
        taint_confirmed = "taint" in finding.sources or finding.evidence.get(
            "taint_confirmed", False
        )
        sev = finding.severity

        if taint_confirmed:
            conf = min(1.0, conf + TAINT_CONFIDENCE_BONUS)
            s_idx = SEVERITY_ORDER.index(sev)
            sev = SEVERITY_ORDER[min(len(SEVERITY_ORDER) - 1, s_idx + 1)]

        # 4. Noisy Rule Suppression / Downgrade
        # If rule triggers without taint confirmation and ml_p < 0.15 (when ML is ON)
        # Note: Lexical Unicode security rules (APS-ALL-UNI-*) are non-taint defenses and never suppressed/downgraded.
        notes = finding.explanation
        if (
            is_ml_active
            and not taint_confirmed
            and not finding.rule_id.startswith("APS-ALL-UNI-")
            and ml_p < NOISY_RULE_ML_THRESHOLD
        ):
            s_idx = SEVERITY_ORDER.index(sev)
            sev = SEVERITY_ORDER[max(0, s_idx - 1)]
            notes = f"{notes} (downgraded: model sees this as usual code)"

        # 6. Check suppression
        sig = (finding.rule_id, filename, finding.range.start_line)
        rule_line = (finding.rule_id, finding.range.start_line)
        fp_sig = f"{finding.rule_id}:{finding.range.start_line}"
        is_suppressed = (
            finding.suppressed
            or (sig in suppressed_sigs)
            or (finding.id in suppressed_fps)
            or (fp_sig in suppressed_fps)
            or (rule_line in suppressed_rule_lines)
        )

        evidence: dict[str, Any] = dict(finding.evidence)
        evidence["rule_score"] = round(rule_conf, 4)
        evidence["ml_score"] = round(ml_p, 4)
        evidence["ml_mode"] = ml_mode
        evidence["taint_confirmed"] = bool(taint_confirmed)
        evidence["confidence_breakdown"] = {
            "rule_score": round(rule_conf, 4),
            "ml_score": round(ml_p, 4) if is_ml_active else None,
            "ml_mode": "on" if is_ml_active else "off",
            "rule_weight": RULE_WEIGHT if is_ml_active else 1.0,
            "ml_weight": ML_WEIGHT if is_ml_active else 0.0,
            "taint_bonus": TAINT_CONFIDENCE_BONUS if taint_confirmed else 0.0,
            "taint_confirmed": bool(taint_confirmed),
            "fused": round(conf, 4),
        }

        updated_sources = list(finding.sources)
        if is_ml_active and "ml" not in updated_sources:
            updated_sources.append("ml")

        fused = finding.model_copy(
            update={
                "severity": sev,
                "confidence": round(conf, 4),
                "explanation": notes,
                "evidence": evidence,
                "sources": updated_sources,
                "suppressed": is_suppressed,
                "attack": _indicative_attack(finding),
            }
        )
        fused_findings.append(fused)

    # 5. ML-Only Anomaly Rule (APS-ALL-ML-001)
    if is_ml_active and ml_probabilities is not None:
        ml_only_count = 0
        anomaly_thresh = max(0.5, ml_threshold_malicious)
        for i, tok in enumerate(tokens):
            if ml_only_count >= ML_ONLY_FINDINGS_CAP:
                break
            if i in claimed_token_indices:
                continue
            if tok.kind in ("WHITESPACE", "NEWLINE", "COMMENT"):
                continue

            p_safe, p_susp, p_mal = ml_probabilities[i]
            if p_mal >= anomaly_thresh:
                tok_rng = tok.to_range()
                finding_id = f"ML-{tok_rng.start_line}-{tok_rng.start_col}"
                evidence_dict: dict[str, Any] = {
                    "ml_score": round(float(p_mal), 4),
                    "ml_mode": "on",
                    "p_malicious": round(float(p_mal), 4),
                    "p_suspicious": round(float(p_susp), 4),
                    "p_safe": round(float(p_safe), 4),
                    "confidence_breakdown": {
                        "rule_score": None,
                        "ml_score": round(float(p_mal), 4),
                        "ml_mode": "on",
                        "rule_weight": 0.0,
                        "ml_weight": 1.0,
                        "taint_bonus": 0.0,
                        "taint_confirmed": False,
                        "fused": round(float(p_mal), 4),
                    },
                }

                ml_finding = Finding(
                    id=finding_id,
                    rule_id="APS-ALL-ML-001",
                    title="Machine Learning Anomaly Detected",
                    cwe=get_cwe_for_category("ANOMALY"),
                    severity=Severity.LOW,
                    label=Label.SUSPICIOUS,
                    confidence=round(float(p_mal), 4),
                    range=tok_rng,
                    message=f"Token '{tok.text}' flagged as anomalous by security ML model",
                    explanation=(
                        f"The security classifier detected high anomaly probability ({p_mal:.2f}) "
                        f"over this token window without a matching AST rule pattern."
                    ),
                    evidence=evidence_dict,
                    taint_path=[],
                    fixes=[],
                    sources=["ml"],
                    suppressed=(
                        ("APS-ALL-ML-001", filename, tok_rng.start_line) in suppressed_sigs
                        or finding_id in suppressed_fps
                        or ("APS-ALL-ML-001", tok_rng.start_line) in suppressed_rule_lines
                    ),
                    attack=None,
                )
                fused_findings.append(ml_finding)
                ml_only_count += 1

    # 7. Sorting Order: Severity descending -> Confidence descending -> Source line ascending
    def sort_key(f: Finding) -> tuple[int, float, int]:
        sev_rank = SEVERITY_ORDER.index(f.severity)  # 0 to 4
        return (-sev_rank, -f.confidence, f.range.start_line)

    fused_findings.sort(key=sort_key)
    return fused_findings


def _indicative_attack(finding: Finding) -> list[str] | None:
    """Return sparse ATT&CK tags (indicative mapping, verify manually)."""
    if finding.rule_id.startswith("APS-ALL-UNI-"):
        return ["T1036"]
    if finding.cwe in {"CWE-78", "CWE-94", "CWE-95"}:
        return ["T1059"]
    if finding.cwe == "CWE-798":
        return ["T1552"]
    return None
