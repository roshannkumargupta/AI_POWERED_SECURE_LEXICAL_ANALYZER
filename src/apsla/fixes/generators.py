from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from apsla.lexing.common import OffsetMap
from apsla.models import Edit, Range


@dataclass(frozen=True)
class RuleFix:
    edits: list[Edit]
    rationale: str
    expected_outcome: str


@dataclass(frozen=True)
class NoRuleFix:
    reason: str = "No unambiguous automatic lexical or syntax fix is available for this target."


def _position_edit(source: str, start: int, end: int, replacement: str) -> Edit:
    offsets = OffsetMap(source)
    return Edit(range=offsets.span_to_range(start, end), new_text=replacement)


def _range_offsets(source: str, range_: Range) -> tuple[int, int]:
    offsets = OffsetMap(source)
    return offsets.pos_to_py(range_.start_line, range_.start_col), offsets.pos_to_py(range_.end_line, range_.end_col)


def _at_eof(source: str) -> int:
    return len(source) - 1 if source.endswith("\n") else len(source)


def _string_closer(source: str) -> str | None:
    """Return a delimiter only for one unambiguous literal/comment open at EOF."""
    i = 0
    quote: str | None = None
    escaped = False
    triple = False
    raw_end: str | None = None
    while i < len(source):
        if raw_end:
            if source.startswith(raw_end, i):
                i += len(raw_end)
                raw_end = None
            else:
                i += 1
            continue
        if quote:
            if escaped:
                escaped = False
                i += 1
                continue
            if source[i] == "\\" and quote != "`":
                escaped = True
                i += 1
                continue
            ending = quote * (3 if triple else 1)
            if source.startswith(ending, i):
                i += len(ending)
                quote = None
                triple = False
                continue
            if source[i] in "\r\n" and not triple and quote != "`":
                quote = None
            i += 1
            continue
        if source.startswith("/*", i):
            close = source.find("*/", i + 2)
            if close < 0:
                return "*/"
            i = close + 2
            continue
        if source.startswith("//", i):
            newline = source.find("\n", i + 2)
            if newline < 0:
                break
            i = newline + 1
            continue
        if source.startswith("R\"", i):
            open_paren = source.find("(", i + 2, min(len(source), i + 20))
            if open_paren >= 0:
                delimiter = source[i + 2:open_paren]
                raw_end = ")" + delimiter + '"'
                i = open_paren + 1
                continue
        if source.startswith("\"\"\"", i) or source.startswith("'''", i):
            quote = source[i]
            triple = True
            i += 3
            continue
        char = source[i]
        if char == "#":
            newline = source.find("\n", i + 1)
            if newline < 0:
                break
            i = newline + 1
            continue
        if char in {'"', "'", "`"}:
            quote = char
        i += 1
    if raw_end:
        return raw_end
    if quote:
        # Template interpolation can contain nested quotes and needs a parser to fix safely.
        if quote == "`" and "${" in source[source.rfind("`", 0, i):]:
            return None
        return quote * (3 if triple else 1)
    return None


def generate_rule_fix(
    *,
    source: str,
    language: str,
    range: Range,
    category: str,
    message: str,
    produced_by: str,
    lexeme: str | None = None,
) -> tuple[RuleFix | None, str | None]:
    """Generate only local, deterministic edits; malformed-number cases are intentionally narrow.

    Safe numeric normalizations are limited to Python digit separators: repeated underscores
    between digits become one underscore, and a trailing separator is removed. Other numeric
    spellings may encode a different value and therefore need manual review.
    """
    start, end = _range_offsets(source, range)
    sample = source[start:end]
    lowered = message.lower()
    language = language.lower()

    for index, char in enumerate(source[start:end], start):
        if char in "\u2018\u2019":
            return RuleFix([_position_edit(source, index, index + 1, "'")], "Replace a smart single quote with an ASCII quote.", "The source uses a parser-recognized ASCII string delimiter."), None
        if char in "\u201c\u201d":
            return RuleFix([_position_edit(source, index, index + 1, '"')], "Replace a smart double quote with an ASCII quote.", "The source uses a parser-recognized ASCII string delimiter."), None
        category_code = unicodedata.category(char)
        if char in "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069" or (category_code in {"Cf", "Cc", "Zl", "Zp"} and char not in "\t\r\n\f\v"):
            return RuleFix([_position_edit(source, index, index + 1, "")], f"Remove invisible or bidi control U+{ord(char):04X}.", "The suspicious control character is removed."), None

    if "invalid escape" in lowered or "escape sequence" in lowered:
        for index, char in enumerate(source[start:max(start, end - 1)], start):
            if char == "\\" and source[index + 1] not in "\\'\"abfnrtv01234567xXuUN\n\r":
                return RuleFix([_position_edit(source, index, index, "\\")], "Escape the literal backslash so it is not parsed as an invalid escape.", "The escape is represented as a literal backslash."), None

    if "malformed number" in lowered or "invalid numeric" in lowered or "invalid number" in lowered:
        candidate = lexeme if lexeme is not None else sample
        if language == "python" and re.fullmatch(r"\d(?:[\d_]*\d)?_+", candidate):
            normalized = candidate.rstrip("_")
            if normalized and normalized != candidate:
                return RuleFix([_position_edit(source, start, end, normalized)], "Remove a trailing Python digit separator.", "The integer literal has a valid digit-separator form."), None
        if language == "python" and re.fullmatch(r"\d(?:[\d_]*\d)", candidate):
            normalized = re.sub(r"_{2,}", "_", candidate)
            if normalized != candidate:
                return RuleFix([_position_edit(source, start, end, normalized)], "Normalize repeated Python digit separators.", "The integer literal has a valid digit-separator form."), None

    if any(word in lowered for word in ("unterminated", "unclosed", "unexpected eof", "end of file while scanning")):
        closer = _string_closer(source)
        if closer:
            at = _at_eof(source)
            return RuleFix([_position_edit(source, at, at, closer)], f"Close the unterminated {('block comment' if closer == '*/' else 'raw string' if closer.startswith(')') else 'literal')}.", "The missing closing delimiter is inserted at the end of the source."), None

    if produced_by.startswith("tree-sitter-") and ("expected" in lowered or "missing" in lowered):
        expected = None
        if re.search(r"(?:expected|missing)\s+['\"]?;['\"]?", lowered):
            expected = ";"
        elif re.search(r"(?:expected|missing)\s+['\"]?\)['\"]?", lowered):
            expected = ")"
        elif re.search(r"(?:expected|missing)\s+['\"]?\}['\"]?", lowered):
            expected = "}"
        if expected is not None and start == end:
            return RuleFix([_position_edit(source, start, start, expected)], f"Insert the parser-reported missing '{expected}'.", "The exact token reported by tree-sitter is inserted."), None

    if ("unexpected" in lowered or "invalid character" in lowered or "invalid token" in lowered) and len(sample) == 1:
        return RuleFix([_position_edit(source, start, end, "")], f"Remove unexpected character U+{ord(sample):04X}.", "The unexpected character is removed; surrounding code is unchanged."), None

    # Lexer-level token reports are not always phrased as an unterminated diagnostic.
    if lexeme and lexeme.startswith(("'", '"', "`", "R\"")) and start + len(lexeme) >= len(source):
        closer = _string_closer(source)
        if closer:
            at = _at_eof(source)
            return RuleFix([_position_edit(source, at, at, closer)], "Close the unterminated literal.", "The missing closing delimiter is inserted."), None
    return None, "No automatic fix is available for this target; use Explain. The source context is ambiguous or the case is not a documented safe normalization."
