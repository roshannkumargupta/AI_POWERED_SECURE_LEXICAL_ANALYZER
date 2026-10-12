"""Deterministic supplemental lexical diagnostics for suspicious Unicode input."""

from __future__ import annotations

import hashlib
import unicodedata

from apsla.lexing.common import OffsetMap
from apsla.models import Range
from apsla.models_v2 import DiagnosticV2

_BIDI = {
    "LRE", "RLE", "LRO", "RLO", "PDF", "LRI", "RLI", "FSI", "PDI",
}
_INVISIBLE = {"Cf", "Cc", "Zl", "Zp"}
_OPEN_BIDI = {"LRE", "RLE", "LRO", "RLO", "LRI", "RLI", "FSI"}


def unicode_lexical_diagnostics(source: str, language: str, analysis_id: str) -> list[DiagnosticV2]:
    """Report suspicious source code points with exact scalar and Unicode name evidence."""
    offsets = OffsetMap(source)
    found: list[DiagnosticV2] = []
    bidi_stack: list[tuple[str, int]] = []
    for index, char in enumerate(source):
        category = unicodedata.category(char)
        name = unicodedata.name(char, "UNNAMED")
        code = f"U+{ord(char):04X}"
        issue: str | None = None
        if char in "\u2018\u2019\u201c\u201d":
            issue = "Smart quotation mark used as a source delimiter candidate"
        elif char.isspace() and char not in " \t\r\n\f\v":
            issue = "Non-ASCII whitespace in source"
        elif category in _INVISIBLE and char not in "\t\r\n\f\v":
            issue = "Invisible or control character in source"
        if char in "\u202a\u202b\u202d\u202e\u2066\u2067\u2068":
            bidi_stack.append((unicodedata.bidirectional(char), index))
        elif char in {"\u202c", "\u2069"}:
            expected = "PDF" if char == "\u202c" else "PDI"
            if not bidi_stack or (expected == "PDF" and bidi_stack[-1][0] not in {"LRE", "RLE", "LRO", "RLO"}) or (expected == "PDI" and bidi_stack[-1][0] not in {"LRI", "RLI", "FSI"}):
                issue = "Unbalanced bidirectional control"
            else:
                bidi_stack.pop()
        if issue:
            start_line, start_col = offsets.py_to_pos(index)
            end_line, end_col = offsets.py_to_pos(index + 1)
            evidence = f"raw={char!r}; codepoint={code}; unicode_name={name}; category={category}; bidi={unicodedata.bidirectional(char) or 'none'}"
            stable = hashlib.sha256(f"{analysis_id}:{index}:{issue}".encode()).hexdigest()[:20]
            found.append(DiagnosticV2(
                id=f"lex-unicode-{stable}", language=language,
                range=Range(
                    start_line=start_line, start_col=start_col,
                    end_line=end_line, end_col=end_col,
                ), category="lexical", severity="warning", message=issue,
                related_evidence=[evidence], produced_by="unicode-lexer",
                certainty="heuristic",
            ))
    for kind, index in bidi_stack:
        char = source[index]
        start_line, start_col = offsets.py_to_pos(index)
        end_line, end_col = offsets.py_to_pos(index + 1)
        stable = hashlib.sha256(f"{analysis_id}:{index}:unbalanced-bidi".encode()).hexdigest()[:20]
        found.append(DiagnosticV2(
            id=f"lex-unicode-{stable}", language=language,
            range=Range(
                start_line=start_line, start_col=start_col,
                end_line=end_line, end_col=end_col,
            ), category="lexical", severity="warning",
            message="Unbalanced bidirectional control sequence",
            related_evidence=[f"raw={char!r}; codepoint=U+{ord(char):04X}; unicode_name={unicodedata.name(char, 'UNNAMED')}; bidi={kind}"],
            produced_by="unicode-lexer", certainty="heuristic",
        ))
    return found
