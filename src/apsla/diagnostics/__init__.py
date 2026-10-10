"""Diagnostics module providing lexical and syntax error analysis and remediation."""

from apsla.diagnostics.engine import (
    analyze_lexical_diagnostics,
    analyze_syntax_diagnostics,
)

__all__ = [
    "analyze_lexical_diagnostics",
    "analyze_syntax_diagnostics",
]
