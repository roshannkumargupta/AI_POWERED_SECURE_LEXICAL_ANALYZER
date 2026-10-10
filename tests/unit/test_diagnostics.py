"""Unit tests for refactored diagnostic modules and language dispatchers."""

from __future__ import annotations

from apsla.diagnostics.common import LANG_PREFIX, _offset_to_range
from apsla.diagnostics.cpp_diag import check_cpp_syntax
from apsla.diagnostics.engine import (
    analyze_lexical_diagnostics,
    analyze_syntax_diagnostics,
)
from apsla.diagnostics.java_diag import check_java_syntax
from apsla.diagnostics.javascript_diag import check_javascript_syntax
from apsla.diagnostics.python_diag import check_python_syntax
from apsla.languages.registry import get


def test_language_prefixes_defined_for_all_supported_languages() -> None:
    assert LANG_PREFIX["python"] == "PY"
    assert LANG_PREFIX["java"] == "JAVA"
    assert LANG_PREFIX["javascript"] == "JS"
    assert LANG_PREFIX["cpp"] == "CP"


def test_offset_to_range_converts_correctly() -> None:
    source = "line1\nline2\nline3"
    rng = _offset_to_range(source, 6, 11)
    assert rng.start_line == 2
    assert rng.start_col == 1
    assert rng.end_line == 2
    assert rng.end_col == 6


def test_python_syntax_dispatcher_detects_assignment_in_if() -> None:
    source = "if x = 5:\n    pass\n"
    findings = check_python_syntax(source, source.splitlines(), "PY")
    assert findings is not None
    assert len(findings) == 1
    assert findings[0].rule_id == "APS-PY-SYN-001"
    assert findings[0].fixes
    assert "==" in findings[0].fixes[0].edits[0].new_text


def test_java_syntax_dispatcher_detects_missing_semicolon() -> None:
    source = "int x = 10"
    findings = check_java_syntax(source, source.splitlines(), "JAVA")
    assert findings is not None
    assert any(f.rule_id == "APS-JAVA-SYN-001" for f in findings)


def test_javascript_syntax_dispatcher_detects_constant_declaration() -> None:
    source = "const x;"
    findings = check_javascript_syntax(source, source.splitlines(), "JS")
    assert findings is not None
    assert any(f.rule_id == "APS-JS-SYN-001" for f in findings)


def test_cpp_syntax_dispatcher_detects_missing_closing_brace() -> None:
    source = "int main() {\n    return 0;\n"
    findings = check_cpp_syntax(source, source.splitlines(), "CP")
    assert findings is not None
    assert any(f.rule_id == "APS-CP-SYN-001" for f in findings)


def test_engine_facade_re_exports_and_dispatches() -> None:
    py_plugin = get("python")
    assert py_plugin is not None
    tokens = py_plugin.lex("val = 'bad\n")
    lex_findings = analyze_lexical_diagnostics("val = 'bad\n", tokens, "python")
    assert len(lex_findings) >= 1
    assert lex_findings[0].rule_id == "APS-PY-LEX-001"

    syn_findings = analyze_syntax_diagnostics("if a = 1:\n    pass", py_plugin, tokens)
    assert len(syn_findings) >= 1
    assert syn_findings[0].rule_id == "APS-PY-SYN-001"
