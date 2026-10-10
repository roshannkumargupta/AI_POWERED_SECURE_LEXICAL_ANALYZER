from apsla.models import Finding, Range, Severity
from apsla.suppression import apply_code_suppressions, parse_suppression_comments


def _dummy_finding(rule_id: str, line: int) -> Finding:
    return Finding(
        id=f"find-{rule_id}-{line}",
        rule_id=rule_id,
        severity=Severity.HIGH,
        confidence=0.85,
        message=f"Violation of {rule_id}",
        range=Range(start_line=line, start_col=1, end_line=line, end_col=20),
    )


def test_python_suppression_same_and_previous_line():
    """Verify # securelex: ignore <RULE> works on previous and same lines in Python."""
    code = """# line 1
# securelex: ignore APS-PY-INJ-001
os.system(user_cmd)  # line 3

eval(user_code)  # securelex: ignore APS-PY-INJ-002
"""
    suppressed_map = parse_suppression_comments(code, "python")
    assert 2 in suppressed_map
    assert "APS-PY-INJ-001" in suppressed_map[2]

    assert 5 in suppressed_map
    assert "APS-PY-INJ-002" in suppressed_map[5]

    f1 = _dummy_finding("APS-PY-INJ-001", 3)
    f2 = _dummy_finding("APS-PY-INJ-002", 5)
    f3 = _dummy_finding("APS-PY-INJ-003", 3)  # Not suppressed

    results = apply_code_suppressions([f1, f2, f3], code, "python")
    assert results[0].suppressed is True
    assert results[0].suppression_reason == "suppressed in code"
    assert results[1].suppressed is True
    assert results[1].suppression_reason == "suppressed in code"
    assert results[2].suppressed is False
    assert results[2].suppression_reason is None


def test_java_suppression_same_and_previous_line():
    """Verify // securelex: ignore <RULE> works in Java."""
    code = """
// securelex: ignore APS-JAVA-SQLI-001
stmt.executeQuery(query);
Runtime.getRuntime().exec(cmd); // securelex: ignore APS-JAVA-CMD-001
"""
    f1 = _dummy_finding("APS-JAVA-SQLI-001", 3)
    f2 = _dummy_finding("APS-JAVA-CMD-001", 4)
    results = apply_code_suppressions([f1, f2], code, "java")
    assert results[0].suppressed is True
    assert results[0].suppression_reason == "suppressed in code"
    assert results[1].suppressed is True
    assert results[1].suppression_reason == "suppressed in code"


def test_javascript_suppression_same_and_previous_line():
    """Verify // securelex: ignore <RULE> works in JavaScript."""
    code = """
// securelex: ignore APS-JS-XSS-001
document.write(userInput);
eval(str); // securelex: ignore APS-JS-EVAL-001
"""
    f1 = _dummy_finding("APS-JS-XSS-001", 3)
    f2 = _dummy_finding("APS-JS-EVAL-001", 4)
    results = apply_code_suppressions([f1, f2], code, "javascript")
    assert results[0].suppressed is True
    assert results[0].suppression_reason == "suppressed in code"
    assert results[1].suppressed is True
    assert results[1].suppression_reason == "suppressed in code"


def test_cpp_suppression_same_and_previous_line():
    """Verify // securelex: ignore <RULE> works in C++."""
    code = """
// securelex: ignore APS-CPP-BUF-001
strcpy(dest, src);
system(cmd); // securelex: ignore APS-CPP-CMD-001
"""
    f1 = _dummy_finding("APS-CPP-BUF-001", 3)
    f2 = _dummy_finding("APS-CPP-CMD-001", 4)
    results = apply_code_suppressions([f1, f2], code, "cpp")
    assert results[0].suppressed is True
    assert results[0].suppression_reason == "suppressed in code"
    assert results[1].suppressed is True
    assert results[1].suppression_reason == "suppressed in code"


def test_multiple_rules_in_single_suppression_comment():
    """Verify comma/space separated rule IDs in one ignore comment."""
    code = """
// securelex: ignore APS-JS-XSS-001, APS-JS-INJ-002
runDangerousCode();
"""
    f1 = _dummy_finding("APS-JS-XSS-001", 3)
    f2 = _dummy_finding("APS-JS-INJ-002", 3)
    f3 = _dummy_finding("APS-JS-OTHER-003", 3)

    results = apply_code_suppressions([f1, f2, f3], code, "javascript")
    assert results[0].suppressed is True
    assert results[1].suppressed is True
    assert results[2].suppressed is False
