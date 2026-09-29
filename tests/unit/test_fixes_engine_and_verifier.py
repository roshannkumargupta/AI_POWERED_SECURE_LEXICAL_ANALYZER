"""Unit tests for fix verification engine, regression detection, and generator error handling."""

from apsla.fixes.verifier import verify_fix
from apsla.models import Edit, Finding, Fix, Label, Range, Severity, VerificationResult


def _create_finding(rule_id: str, line: int = 1) -> Finding:
    return Finding(
        id=f"f-{rule_id}-{line}",
        rule_id=rule_id,
        title="Test Finding",
        cwe="CWE-78",
        severity=Severity.HIGH,
        label=Label.MALICIOUS,
        confidence=0.9,
        range=Range(start_line=line, start_col=1, end_line=line, end_col=10),
        message="Test message",
        explanation="Test explanation",
        evidence={},
        taint_path=[],
        fixes=[],
        sources=["rule"],
    )


def test_verifier_downgrades_on_syntax_error():
    source = "import os\nos.system('echo 1')\n"
    finding = _create_finding("APS-PY-INJ-002", line=2)

    # Deliberately broken syntax fix
    bad_edit = Edit(
        range=Range(start_line=2, start_col=1, end_line=2, end_col=20),
        new_text="def broken syntax ::: !!!\n",
    )
    bad_fix = Fix(
        id="fix-bad-1",
        finding_id=finding.id,
        title="Bad syntax fix",
        description="Introduces syntax error",
        confidence="safe",
        kind="rule",
        edits=[bad_edit],
        verification=VerificationResult(syntax_ok=False, finding_gone=False, verified=False),
    )

    verified_fix = verify_fix(source, bad_fix, finding, language="python")
    assert verified_fix.confidence == "manual"
    assert verified_fix.edits == []
    assert verified_fix.verification.verified is False
    assert verified_fix.verification.syntax_ok is False
    assert "Syntax check failed" in verified_fix.verification.notes


def test_verifier_downgrades_when_finding_not_eliminated():
    source = "import os\nos.system('echo 1')\n"
    finding = _create_finding("APS-PY-INJ-002", line=2)

    # Fix that changes variable name but keeps os.system vulnerable
    dummy_edit = Edit(
        range=Range(start_line=2, start_col=1, end_line=2, end_col=20),
        new_text="os.system('echo ' + 'unresolved')\n",
    )
    incomplete_fix = Fix(
        id="fix-inc-1",
        finding_id=finding.id,
        title="Incomplete fix",
        description="Fails to remove vulnerability",
        confidence="review",
        kind="rule",
        edits=[dummy_edit],
        verification=VerificationResult(syntax_ok=False, finding_gone=False, verified=False),
    )

    verified_fix = verify_fix(source, incomplete_fix, finding, language="python")
    assert verified_fix.confidence == "manual"
    assert verified_fix.edits == []
    assert verified_fix.verification.verified is False
    assert verified_fix.verification.finding_gone is False
    assert "still present" in verified_fix.verification.notes


def test_verifier_downgrades_when_introducing_new_finding():
    source = "import os\nopen('file.txt', 'r')\n"
    finding = _create_finding("APS-PY-IO-001", line=2)

    # Fix that replaces open with eval(input()) -> introduces APS-PY-INJ-001
    regressive_edit = Edit(
        range=Range(start_line=2, start_col=1, end_line=2, end_col=22),
        new_text="eval(input())\n",
    )
    regressive_fix = Fix(
        id="fix-reg-1",
        finding_id=finding.id,
        title="Regressive fix",
        description="Introduces code injection",
        confidence="safe",
        kind="rule",
        edits=[regressive_edit],
        verification=VerificationResult(syntax_ok=False, finding_gone=False, verified=False),
    )

    verified_fix = verify_fix(source, regressive_fix, finding, language="python")
    assert verified_fix.confidence == "manual"
    assert verified_fix.edits == []
    assert verified_fix.verification.verified is False
    assert len(verified_fix.verification.new_findings) > 0
    assert "APS-PY-INJ-001" in verified_fix.verification.new_findings


def test_verifier_handles_timeout(monkeypatch):
    import time

    from apsla.fixes import verifier

    def slow_worker(*args, **kwargs):
        time.sleep(0.05)
        return True, True, [], ""

    monkeypatch.setattr(verifier, "_verify_worker", slow_worker)

    source = "import os\nos.system('echo 1')\n"
    finding = _create_finding("APS-PY-INJ-002", line=2)

    edit = Edit(
        range=Range(start_line=2, start_col=1, end_line=2, end_col=20),
        new_text="pass\n",
    )
    timed_fix = Fix(
        id="fix-time-1",
        finding_id=finding.id,
        title="Slow fix",
        description="Timeout simulation",
        confidence="safe",
        kind="rule",
        edits=[edit],
        verification=VerificationResult(syntax_ok=False, finding_gone=False, verified=False),
    )

    verified_fix = verify_fix(source, timed_fix, finding, language="python", timeout_seconds=0.005)
    assert verified_fix.confidence == "manual"
    assert verified_fix.edits == []
    assert verified_fix.verification.verified is False
    assert "timed out" in verified_fix.verification.notes
