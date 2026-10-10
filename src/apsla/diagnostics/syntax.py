"""Syntax diagnostic analysis orchestrator."""

from __future__ import annotations

import re
from typing import Any

from apsla.diagnostics.common import (
    LANG_PREFIX,
    make_syntax_finding,
)
from apsla.diagnostics.cpp_diag import check_cpp_syntax
from apsla.diagnostics.java_diag import check_java_syntax
from apsla.diagnostics.javascript_diag import check_javascript_syntax
from apsla.diagnostics.python_diag import check_python_syntax
from apsla.lexing.token import Token
from apsla.models import Finding, Range


def analyze_syntax_diagnostics(
    source: str,
    plugin: Any,
    tokens: list[Token],
    lexical_findings: list[Finding] | None = None,
) -> list[Finding]:
    """Inspect source and AST/parser for syntax errors across Python, Java, JS, and C++."""
    language = getattr(plugin, "id", "python")
    prefix = LANG_PREFIX.get(language, "ALL")
    lines = source.splitlines()

    if language == "python":
        findings = check_python_syntax(source, lines, prefix)
        if findings is not None:
            return findings
    elif language == "java":
        findings = check_java_syntax(source, lines, prefix)
        if findings is not None:
            return findings
    elif language == "javascript":
        findings = check_javascript_syntax(source, lines, prefix)
        if findings is not None:
            return findings
    elif language == "cpp":
        findings = check_cpp_syntax(source, lines, prefix)
        if findings is not None:
            return findings

    # General plugin syntax check fallback
    ok, detail = plugin.syntax_check(source)
    if not ok and detail:
        if "lexical error" in detail.lower():
            return []
        line, col = 1, 1
        match = re.search(r"line (\d+)(?:, col(?:umn)? (\d+))?", detail, re.IGNORECASE)
        if match:
            line, col = int(match.group(1)), int(match.group(2) or 1)
        message = f"Syntax error at line {line}, col {col}: {detail}."
        rng = Range(start_line=line, start_col=col, end_line=line, end_col=col + 1)
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Syntax error",
                message,
                "The parser cannot interpret this source at the reported location.",
                rng,
            )
        ]

    return []
