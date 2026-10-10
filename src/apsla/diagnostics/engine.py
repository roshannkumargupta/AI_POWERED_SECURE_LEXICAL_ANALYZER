"""Unified Lexical and Syntax Diagnostic Engine with automated fix generation.

Provides:
  - analyze_lexical_diagnostics(source, tokens, language)
  - analyze_syntax_diagnostics(source, plugin, tokens, lexical_findings)
  - Deterministic, verified fixes for all lexical and syntax errors.
"""

from __future__ import annotations

from apsla.diagnostics.common import (
    LANG_PREFIX,
    _make_fix,
    _offset_to_range,
)
from apsla.diagnostics.lexical import analyze_lexical_diagnostics
from apsla.diagnostics.syntax import analyze_syntax_diagnostics

__all__ = [
    "LANG_PREFIX",
    "_make_fix",
    "_offset_to_range",
    "analyze_lexical_diagnostics",
    "analyze_syntax_diagnostics",
]
