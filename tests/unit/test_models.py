"""Unit tests for Pydantic v2 data models and JSON round-tripping."""

from __future__ import annotations

from apsla.models import (
    AnalysisResult,
    AnalysisSummary,
    Edit,
    EngineMetadata,
    Finding,
    Fix,
    Label,
    Range,
    Severity,
    TaintPathStep,
    TaintStepKind,
    Token,
    VerificationResult,
)


def test_range_model():
    """Verify Range coordinate validation and immutability."""
    r = Range(start_line=1, start_col=1, end_line=1, end_col=10)
    assert r.start_line == 1
    assert r.start_col == 1
    assert r.end_line == 1
    assert r.end_col == 10

    # JSON round trip
    json_data = r.model_dump_json()
    r2 = Range.model_validate_json(json_data)
    assert r == r2


def test_token_model():
    """Verify Token representation and to_range conversion."""
    t = Token(
        kind="IDENTIFIER",
        text="my_var",
        start=0,
        end=6,
        line=1,
        col=1,
        end_line=1,
        end_col=7,
    )
    rng = t.range
    assert rng.start_line == 1
    assert rng.start_col == 1
    assert rng.end_col == 7

    token_info = t.to_token_info(label="SAFE", score=0.0)
    assert token_info.token == "my_var"
    assert token_info.label == "SAFE"

    # JSON round trip
    json_data = t.model_dump_json()
    t2 = Token.model_validate_json(json_data)
    assert t == t2


def test_fix_and_verification_roundtrip():
    """Verify Fix and VerificationResult models serialize cleanly."""
    edit = Edit(
        range=Range(start_line=2, start_col=5, end_line=2, end_col=15),
        new_text="safe_function()",
    )
    vr = VerificationResult(
        syntax_ok=True,
        finding_gone=True,
        new_findings=[],
        verified=True,
        notes="Remediation verified safely",
    )
    fix = Fix(
        id="FIX-001",
        finding_id="FIND-001",
        title="Sanitize Input",
        description="Neutralize command parameters",
        confidence="safe",
        kind="rule",
        edits=[edit],
        verification=vr,
    )

    json_str = fix.model_dump_json()
    fix2 = Fix.model_validate_json(json_str)
    assert fix2.id == "FIX-001"
    assert fix2.verification.verified is True
    assert len(fix2.edits) == 1
    assert fix2.edits[0].new_text == "safe_function()"


def test_finding_and_analysis_result_roundtrip():
    """Verify Finding and AnalysisResult models round-trip through JSON."""
    rng = Range(start_line=10, start_col=1, end_line=10, end_col=20)
    taint_step = TaintPathStep(
        step=TaintStepKind.SOURCE,
        range=rng,
        text="request.args.get()",
        note="User controlled input source",
    )
    finding = Finding(
        id="APS-PY-INJ-001-10-1",
        rule_id="APS-PY-INJ-001",
        title="Command Injection",
        cwe="CWE-78",
        severity=Severity.CRITICAL,
        label=Label.MALICIOUS,
        confidence=0.95,
        range=rng,
        message="Untrusted user input reaches os.system()",
        explanation="Untrusted input is passed to an OS command execution sink.",
        evidence={"sink": "os.system", "taint_confirmed": True},
        taint_path=[taint_step],
        fixes=[],
        sources=["rule", "taint"],
        suppressed=False,
    )

    summary = AnalysisSummary(
        critical=1,
        high=0,
        medium=0,
        low=0,
        info=0,
        score=75,
        tokens_total=50,
        tokens_malicious=1,
        tokens_suspicious=0,
    )

    engine = EngineMetadata(
        ml_mode="off",
        ml_model_id="none",
        taint="ast",
        version="0.1.0",
        elapsed_ms=12.5,
    )

    result = AnalysisResult(
        language="python",
        filename="vuln.py",
        findings=[finding],
        tokens=[],
        summary=summary,
        engine=engine,
    )

    json_str = result.model_dump_json()
    result2 = AnalysisResult.model_validate_json(json_str)

    assert result2.language == "python"
    assert len(result2.findings) == 1
    assert result2.findings[0].severity == Severity.CRITICAL
    assert result2.findings[0].label == Label.MALICIOUS
    assert result2.summary.score == 75
    assert result2.engine.elapsed_ms == 12.5
