"""Unit tests for Section H Score & Finding Fusion rules."""

from __future__ import annotations

import numpy as np

from apsla.fusion import fuse_findings
from apsla.lexing.token import Token
from apsla.models import Finding, Label, Range, Severity


def _make_dummy_token(text: str, line: int = 1, col: int = 1, kind: str = "IDENTIFIER") -> Token:
    return Token(
        kind=kind,
        text=text,
        start=0,
        end=len(text),
        line=line,
        col=col,
        end_line=line,
        end_col=col + len(text),
    )


def _make_dummy_finding(
    rule_id: str = "APS-PY-INJ-002",
    line: int = 1,
    col: int = 1,
    severity: Severity = Severity.HIGH,
    confidence: float = 0.8,
    sources: list[str] | None = None,
) -> Finding:
    rng = Range(start_line=line, start_col=col, end_line=line, end_col=col + 5)
    return Finding(
        id=f"TEST-{line}-{col}",
        rule_id=rule_id,
        title="Test Finding",
        cwe="CWE-78",
        severity=severity,
        label=Label.MALICIOUS,
        confidence=confidence,
        range=rng,
        message="Test vulnerability message",
        explanation="Test explanation",
        evidence={},
        taint_path=[],
        fixes=[],
        sources=sources or ["rule"],
        suppressed=False,
    )


def test_fusion_ml_off():
    tok = _make_dummy_token("system", line=1, col=1)
    finding = _make_dummy_finding(line=1, col=1, confidence=0.8)

    fused = fuse_findings([finding], [tok], ml_probabilities=None, ml_mode="off")
    assert len(fused) == 1
    res = fused[0]

    # When ML is OFF: confidence equals rule_conf exactly
    assert res.confidence == 0.8
    assert res.evidence["ml_mode"] == "off"
    assert "ml" not in res.sources


def test_fusion_ml_on_blend():
    tok = _make_dummy_token("system", line=1, col=1)
    finding = _make_dummy_finding(line=1, col=1, confidence=0.8)

    # Token has P(MAL)=0.6, P(SUSP)=0.0 -> ml_p = 0.6
    probs = np.array([[0.4, 0.0, 0.6]], dtype=np.float32)

    fused = fuse_findings([finding], [tok], ml_probabilities=probs, ml_mode="on")
    assert len(fused) == 1
    res = fused[0]

    # 0.7 * 0.8 + 0.3 * 0.6 = 0.56 + 0.18 = 0.74
    assert res.confidence == 0.74
    assert res.evidence["ml_mode"] == "on"
    assert "ml" in res.sources


def test_fusion_taint_boost():
    tok = _make_dummy_token("system", line=1, col=1)
    finding = _make_dummy_finding(
        line=1, col=1, severity=Severity.HIGH, confidence=0.8, sources=["rule", "taint"]
    )

    fused = fuse_findings([finding], [tok], ml_probabilities=None, ml_mode="off")
    assert len(fused) == 1
    res = fused[0]

    # Taint confirmed: +0.15 boost (0.8 + 0.15 = 0.95), severity HIGH -> CRITICAL
    assert round(res.confidence, 2) == 0.95
    assert res.severity == Severity.CRITICAL


def test_fusion_noisy_rule_downgrade():
    tok = _make_dummy_token("safe_call", line=1, col=1)
    finding = _make_dummy_finding(line=1, col=1, severity=Severity.HIGH, confidence=0.5)

    # ML sees this token as completely safe: ml_p = 0.0 < 0.15
    probs = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)

    fused = fuse_findings([finding], [tok], ml_probabilities=probs, ml_mode="on")
    assert len(fused) == 1
    res = fused[0]

    # No taint and ml_p < 0.15 -> Severity downgraded HIGH -> MEDIUM
    assert res.severity == Severity.MEDIUM
    assert "downgraded: model sees this as usual code" in res.explanation


def test_fusion_ml_only_anomaly_and_cap():
    tokens = [_make_dummy_token(f"tok_{i}", line=i + 1, col=1) for i in range(15)]
    # All 15 tokens have P(MAL) = 0.9
    probs = np.zeros((15, 3), dtype=np.float32)
    probs[:, 2] = 0.9

    fused = fuse_findings(
        [], tokens, ml_probabilities=probs, ml_mode="on", ml_threshold_malicious=0.5
    )

    # Must be capped at exactly 10 findings (ML_ONLY_FINDINGS_CAP)
    assert len(fused) == 10
    for f in fused:
        assert f.rule_id == "APS-ALL-ML-001"
        assert f.severity == Severity.LOW
        assert "ml" in f.sources


def test_fusion_sorting_order():
    tok = _make_dummy_token("var", line=1, col=1)
    f1 = _make_dummy_finding(line=10, severity=Severity.LOW, confidence=0.9)
    f2 = _make_dummy_finding(line=5, severity=Severity.HIGH, confidence=0.5)
    f3 = _make_dummy_finding(line=2, severity=Severity.HIGH, confidence=0.9)

    fused = fuse_findings([f1, f2, f3], [tok], ml_probabilities=None, ml_mode="off")

    # Sorting order: Severity desc -> Confidence desc -> Line asc
    # f3 (HIGH, 0.9) should be first, f2 (HIGH, 0.5) second, f1 (LOW, 0.9) third
    assert fused[0].id == f3.id
    assert fused[1].id == f2.id
    assert fused[2].id == f1.id
