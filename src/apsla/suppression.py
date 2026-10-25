"""Inline suppression comment detection and formatting for inline comments."""

from __future__ import annotations

import re
from typing import Any, Final

from apsla.models import Finding

# Suppression comment regex patterns
# Matches:
#   # securelex: ignore APS-PY-INJ-002
#   // securelex: ignore APS-JV-INJ-001, APS-JV-SQL-002
_SUPPRESSION_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?:#|//)\s*securelex:\s*ignore\s+([^\r\n]+)",
    re.IGNORECASE,
)


def extract_suppressions_from_source(
    source: str, language: str | None = None
) -> dict[int, set[str]]:
    """Scan source code line-by-line for inline suppression directives.

    Args:
        source: Source code text.
        language: Optional language identifier.

    Returns:
        Mapping of 1-based line number to set of suppressed rule IDs (uppercase).
    """
    suppressions: dict[int, set[str]] = {}
    lines = source.splitlines()

    for idx, line in enumerate(lines, start=1):
        for match in _SUPPRESSION_REGEX.finditer(line):
            raw_rules = match.group(1)
            # Split by comma, semicolon or whitespace
            tokens = [r.strip().upper() for r in re.split(r"[,;\s]+", raw_rules) if r.strip()]
            if tokens:
                if idx not in suppressions:
                    suppressions[idx] = set()
                suppressions[idx].update(tokens)

    return suppressions


parse_suppression_comments = extract_suppressions_from_source


def apply_code_suppressions(arg1: Any, arg2: Any, *args: Any) -> list[Finding]:
    """Check same line or previous line for suppression comment directives.

    Accepts either (source: str, findings: list[Finding]) or (findings: list[Finding], source: str).

    If matched, marks finding as suppressed=True with reason "suppressed in code".
    """
    if isinstance(arg1, str):
        source = arg1
        findings = list(arg2)
    else:
        findings = list(arg1)
        source = str(arg2)

    line_suppressions = extract_suppressions_from_source(source)
    if not line_suppressions:
        return findings

    updated: list[Finding] = []
    for f in findings:
        target_rule = f.rule_id.upper()
        start_line = f.range.start_line
        prev_line = start_line - 1

        same_line_rules = line_suppressions.get(start_line, set())
        prev_line_rules = line_suppressions.get(prev_line, set())

        is_suppressed_by_code = (
            target_rule in same_line_rules
            or "ALL" in same_line_rules
            or target_rule in prev_line_rules
            or "ALL" in prev_line_rules
        )

        if is_suppressed_by_code:
            updated.append(
                f.model_copy(
                    update={
                        "suppressed": True,
                        "suppression_reason": "suppressed in code",
                    }
                )
            )
        else:
            updated.append(f)

    return updated


def format_suppression_comment(rule_id: str, language: str = "python") -> str:
    """Format the appropriate comment syntax for the target language.

    Args:
        rule_id: Vulnerability rule ID (e.g. APS-PY-INJ-002).
        language: Programming language.

    Returns:
        Formatted comment string.
    """
    lang = language.lower()
    if lang in ("python", "py"):
        return f"# securelex: ignore {rule_id}"
    return f"// securelex: ignore {rule_id}"
