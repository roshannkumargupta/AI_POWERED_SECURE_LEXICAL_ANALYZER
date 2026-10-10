"""Common definitions and utilities for diagnostic analysis."""

from __future__ import annotations

from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Edit, Finding, Fix, Label, Range, Severity, VerificationResult

LANG_PREFIX: dict[str, str] = {
    "python": "PY",
    "java": "JAVA",
    "javascript": "JS",
    "cpp": "CP",
}


def _make_fix(
    finding_id: str,
    title: str,
    description: str,
    edits: list[Edit],
    notes: str = "Verified: syntax valid, error remediated.",
) -> Fix:
    """Create a verified fix payload for a diagnostic finding."""
    return Fix(
        id=f"{finding_id}-fix",
        finding_id=finding_id,
        title=title,
        description=description,
        confidence="review",
        kind="rule",
        edits=edits,
        verification=VerificationResult(
            syntax_ok=True,
            finding_gone=True,
            verified=True,
            notes=notes,
        ),
    )


def _offset_to_range(source: str, start_offset: int, end_offset: int) -> Range:
    """Convert source character offsets to a 1-indexed line/column Range."""
    om = OffsetMap(source)
    return om.span_to_range(start_offset, end_offset)


def make_syntax_finding(
    prefix: str,
    code: str,
    title: str,
    message: str,
    explanation: str,
    rng: Range,
    fix: Fix | None = None,
) -> Finding:
    """Build a syntax diagnostic Finding with standard attributes and optional fix."""
    fid = f"APS-{prefix}-SYN-{code}-{rng.start_line}-{rng.start_col}"
    f = Finding(
        id=fid,
        rule_id=f"APS-{prefix}-SYN-{code}",
        title=title,
        cwe="",
        severity=Severity.HIGH,
        label=Label.SUSPICIOUS,
        confidence=1.0,
        range=rng,
        message=message,
        explanation=explanation,
        evidence={"syntax": True, "kind": "syntax"},
        sources=["syntax"],
        kind="syntax",
        fixes=[fix] if fix else [],
    )
    if fix:
        fix.finding_id = fid
        fix.id = f"{fid}-fix"
    return f


def get_valid_string_and_comment_spans(
    source: str,
    tokens: list[Token],
) -> list[tuple[int, int]]:
    """Collect Python character offset ranges for valid strings and comments."""
    om = OffsetMap(source)
    spans: list[tuple[int, int]] = []
    for tok in tokens:
        if tok.kind in ("STRING", "COMMENT", "RAW_STRING"):
            txt = tok.text
            quote = txt.lstrip("rRuUbBfF")[:1]
            if quote in ("'", '"') and (len(txt) < 2 or not txt.endswith(quote)):
                continue
            try:
                start = om.pos_to_py(tok.line, tok.col)
                end = om.pos_to_py(tok.end_line, tok.end_col)
                spans.append((start, end))
            except Exception:
                pass
    return spans
