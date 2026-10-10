"""Unit tests for C/C++ automated fix generators, verification, and idempotency."""

from __future__ import annotations

from apsla.fixes.engine import fix_all
from apsla.pipeline import Analyzer


def test_strcpy_to_snprintf_fix_and_verification():
    source = (
        "#include <stdio.h>\n"
        "#include <string.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32];\n"
        "    char *src = argv[1];\n"
        "    strcpy(dest, src);\n"
        "    return 0;\n"
        "}\n"
    )
    analyzer = Analyzer()
    res = analyzer.analyze(
        source, language="cpp", filename="test.c", options={"fixes": True, "ml": False}
    )
    findings = [f for f in res.findings if f.rule_id == "APS-CP-MEM-001"]
    assert len(findings) == 1
    assert len(findings[0].fixes) >= 1
    fix = findings[0].fixes[0]
    assert fix.verification.verified is True
    assert "snprintf" in fix.edits[0].new_text


def test_gets_to_fgets_fix_and_verification():
    source = (
        "#include <stdio.h>\n\nint main() {\n    char buf[64];\n    gets(buf);\n    return 0;\n}\n"
    )
    analyzer = Analyzer()
    res = analyzer.analyze(
        source, language="cpp", filename="test.c", options={"fixes": True, "ml": False}
    )
    findings = [f for f in res.findings if f.rule_id == "APS-CP-MEM-001"]
    assert len(findings) == 1
    assert len(findings[0].fixes) >= 1
    fix = findings[0].fixes[0]
    assert fix.verification.verified is True
    assert "fgets" in fix.edits[0].new_text


def test_sprintf_to_snprintf_fix_and_verification():
    source = (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char buf[64];\n"
        '    sprintf(buf, "%s", argv[1]);\n'
        "    return 0;\n"
        "}\n"
    )
    analyzer = Analyzer()
    res = analyzer.analyze(
        source, language="cpp", filename="test.c", options={"fixes": True, "ml": False}
    )
    findings = [f for f in res.findings if f.rule_id == "APS-CP-MEM-001"]
    assert len(findings) == 1
    assert len(findings[0].fixes) >= 1
    fix = findings[0].fixes[0]
    assert fix.verification.verified is True
    assert "snprintf" in fix.edits[0].new_text


def test_printf_format_string_fix_and_verification():
    source = (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char buf[64];\n"
        "    fgets(buf, sizeof(buf), stdin);\n"
        "    printf(buf);\n"
        "    return 0;\n"
        "}\n"
    )
    analyzer = Analyzer()
    res = analyzer.analyze(
        source, language="cpp", filename="test.c", options={"fixes": True, "ml": False}
    )
    findings = [f for f in res.findings if f.rule_id == "APS-CP-FMT-001"]
    assert len(findings) == 1
    assert len(findings[0].fixes) >= 1
    fix = findings[0].fixes[0]
    assert fix.verification.verified is True
    assert 'printf("%s", buf)' in fix.edits[0].new_text


def test_scanf_field_width_fix_and_verification():
    source = (
        "#include <stdio.h>\n\n"
        "int main() {\n"
        "    char buf[32];\n"
        '    scanf("%s", buf);\n'
        "    return 0;\n"
        "}\n"
    )
    analyzer = Analyzer()
    res = analyzer.analyze(
        source, language="cpp", filename="test.c", options={"fixes": True, "ml": False}
    )
    findings = [f for f in res.findings if f.rule_id == "APS-CP-MEM-003"]
    assert len(findings) == 1
    assert len(findings[0].fixes) >= 1
    fix = findings[0].fixes[0]
    assert fix.verification.verified is True
    assert 'scanf("%31s", buf)' in fix.edits[0].new_text


def test_system_manual_advice():
    source = (
        "#include <stdlib.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char *cmd = argv[1];\n"
        "    system(cmd);\n"
        "    return 0;\n"
        "}\n"
    )
    analyzer = Analyzer()
    res = analyzer.analyze(
        source, language="cpp", filename="test.c", options={"fixes": True, "ml": False}
    )
    findings = [f for f in res.findings if f.rule_id == "APS-CP-INJ-001"]
    assert len(findings) == 1
    assert len(findings[0].fixes) >= 1
    fix = findings[0].fixes[0]
    assert fix.confidence == "manual"
    assert "execv" in fix.description


def test_rand_manual_advice():
    source = "#include <stdlib.h>\n\nint gen_token() {\n    return rand();\n}\n"
    analyzer = Analyzer()
    res = analyzer.analyze(
        source, language="cpp", filename="test.c", options={"fixes": True, "ml": False}
    )
    findings = [f for f in res.findings if f.rule_id == "APS-CP-CRY-001"]
    assert len(findings) == 1
    assert len(findings[0].fixes) >= 1
    fix = findings[0].fixes[0]
    assert fix.confidence == "manual"
    assert "random" in fix.description


def test_fix_all_idempotent():
    """Verify that applying fix_all to a vulnerable C file is idempotent."""
    source = (
        "#include <stdio.h>\n"
        "#include <string.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32];\n"
        "    char *src = argv[1];\n"
        "    strcpy(dest, src);\n"
        "    return 0;\n"
        "}\n"
    )
    fixed_code, applied1, skipped, diff, s_before, s_after = fix_all(
        source, language="cpp", filename="test.c", allow_review=True
    )
    assert len(applied1) >= 1
    assert "snprintf" in fixed_code

    # Second pass on already-fixed code
    fixed_code_2, applied2, skipped2, diff2, s_before2, s_after2 = fix_all(
        fixed_code, language="cpp", filename="test.c", allow_review=True
    )
    assert len(applied2) == 0
    assert fixed_code_2 == fixed_code
