"""Raw text scanner for bidi overrides, zero-width spaces, tag chars, and confusables."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import regex

from apsla.lexing.common import OffsetMap
from apsla.models import Range, Severity
from apsla.unicode_defense.scripts import get_scripts, is_mixed_script

DATA_DIR = Path(__file__).resolve().parent / "data"
CONFUSABLES_PATH = DATA_DIR / "confusables.json"

# (a) Bidi controls
BIDI_CONTROLS: Final[frozenset[int]] = frozenset(
    {
        0x202A,
        0x202B,
        0x202C,
        0x202D,
        0x202E,  # LRE, RLE, PDF, LRO, RLO
        0x2066,
        0x2067,
        0x2068,
        0x2069,  # LRI, RLI, FSI, PDI
        0x200E,
        0x200F,  # LRM, RLM
        0x061C,  # ALM
    }
)

# (b) Zero-width & invisible characters
ZERO_WIDTH_CHARS: Final[frozenset[int]] = frozenset(
    {
        0x200B,
        0x200C,
        0x200D,
        0x2060,  # ZWSP, ZWNJ, ZWJ, WJ
        0x00AD,  # Soft Hyphen
        0x180E,  # Mongolian Vowel Separator
        0xFEFF,  # ZWNBSP / BOM (flagged when not at offset 0)
    }
)

# (e) Non-ASCII whitespace
NON_ASCII_WHITESPACE: Final[frozenset[int]] = frozenset(
    {
        0x00A0,
        0x1680,
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
        *range(0x2000, 0x200B),
    }
)

# Dangerous execution APIs and keywords to check recovery against
DANGEROUS_TARGETS: Final[frozenset[str]] = frozenset(
    {
        "exec",
        "eval",
        "system",
        "compile",
        "popen",
        "check_call",
        "check_output",
        "subprocess",
        "run",
        "execute",
        "loads",
        "pickle",
        "marshal",
        "import",
        "__import__",
        "open",
        "read",
        "write",
        "passthru",
        "shell_exec",
        "Runtime",
        "ProcessBuilder",
        "child_process",
        "require",
        "if",
        "else",
        "for",
        "while",
        "def",
        "class",
        "return",
        "import",
        "from",
    }
)


def _load_confusables() -> dict[str, str]:
    """Load pre-generated confusables dictionary from JSON."""
    if CONFUSABLES_PATH.exists():
        try:
            with open(CONFUSABLES_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


_CONFUSABLES_MAP: dict[str, str] = _load_confusables()

# Match comments: Python (# ...), C++/Java/JS (// ... or /* ... */)
COMMENT_REGEX = regex.compile(r"(?m)(#[^\n]*|//[^\n]*|/\*[\s\S]*?\*/)")
IDENTIFIER_REGEX = regex.compile(r"\b[\p{L}\p{N}_]+\b")


@dataclass(slots=True)
class UnicodeHit:
    """Represents an adversarial or anomalous Unicode character occurrence."""

    codepoint: str  # e.g. 'U+202E'
    name: str  # e.g. 'RIGHT-TO-LEFT OVERRIDE'
    char: str
    category: (
        str  # 'bidi', 'zero_width', 'tag', 'confusable', 'mixed_script', 'whitespace', 'non_ascii'
    )
    severity: Severity
    start_py: int
    end_py: int
    range: Range
    recovered_to: str | None = None
    note: str = ""


@dataclass(slots=True)
class UnicodeScanResult:
    """Aggregated outcome of Unicode defense scanning."""

    hits: list[UnicodeHit] = field(default_factory=list)
    bidi_count: int = 0
    zero_width_count: int = 0
    tag_count: int = 0
    confusable_count: int = 0
    mixed_script_count: int = 0
    whitespace_count: int = 0


def scan_unicode(text: str, offset_map: OffsetMap | None = None) -> UnicodeScanResult:
    """Scan raw text for Trojan Source bidi controls, zero-width spaces, tag chars,

    confusables, and mixed-script identifiers.

    Args:
        text: Source code string to scan.
        offset_map: Optional precomputed OffsetMap for coordinate translations.

    Returns:
        UnicodeScanResult: Detected Unicode anomalies with exact ranges and severities.
    """
    om = offset_map if offset_map is not None else OffsetMap(text)
    result = UnicodeScanResult()

    # Pre-compute comment character intervals
    comment_spans: list[tuple[int, int]] = [m.span() for m in COMMENT_REGEX.finditer(text)]

    def is_in_comment(pos: int) -> bool:
        return any(s <= pos < e for s, e in comment_spans)

    # 1. Scan character-by-character
    i = 0
    py_len = len(text)
    while i < py_len:
        ch = text[i]
        code = ord(ch)

        # Ignore standard ASCII except when checking context
        if code < 128:
            i += 1
            continue

        c_name = unicodedata.name(ch, "UNKNOWN")
        cp_str = f"U+{code:04X}"
        char_range = om.span_to_range(i, i + 1)
        in_comment = is_in_comment(i)

        # (a) Bidi controls (Trojan Source: CVE-2021-42574)
        if code in BIDI_CONTROLS:
            hit = UnicodeHit(
                codepoint=cp_str,
                name=c_name,
                char=ch,
                category="bidi",
                severity=Severity.HIGH,
                start_py=i,
                end_py=i + 1,
                range=char_range,
                note="Trojan Source bidirectional control override character detected",
            )
            result.hits.append(hit)
            result.bidi_count += 1
            i += 1
            continue

        # (b) Zero-width & invisible characters
        if code in ZERO_WIDTH_CHARS:
            # BOM U+FEFF at offset 0 is ignored as standard encoding indicator
            if code == 0xFEFF and i == 0:
                i += 1
                continue

            in_ident = (i > 0 and (text[i - 1].isalnum() or text[i - 1] == "_")) or (
                i + 1 < py_len and (text[i + 1].isalnum() or text[i + 1] == "_")
            )
            hit = UnicodeHit(
                codepoint=cp_str,
                name=c_name,
                char=ch,
                category="zero_width",
                severity=Severity.HIGH if in_ident else Severity.MEDIUM,
                start_py=i,
                end_py=i + 1,
                range=char_range,
                note=f"Invisible / zero-width character ({c_name}) detected"
                + (" in identifier" if in_ident else ""),
            )
            result.hits.append(hit)
            result.zero_width_count += 1
            i += 1
            continue

        # (c) Unicode Tag characters (U+E0000 - U+E007F)
        if 0xE0000 <= code <= 0xE007F:
            hit = UnicodeHit(
                codepoint=cp_str,
                name=c_name,
                char=ch,
                category="tag",
                severity=Severity.HIGH,
                start_py=i,
                end_py=i + 1,
                range=char_range,
                note="Invisible Unicode Tag character detected",
            )
            result.hits.append(hit)
            result.tag_count += 1
            i += 1
            continue

        # (f) Non-ASCII whitespace
        if code in NON_ASCII_WHITESPACE:
            hit = UnicodeHit(
                codepoint=cp_str,
                name=c_name,
                char=ch,
                category="whitespace",
                severity=Severity.LOW,
                start_py=i,
                end_py=i + 1,
                range=char_range,
                note=f"Non-ASCII whitespace ({c_name}) detected",
            )
            result.hits.append(hit)
            result.whitespace_count += 1
            i += 1
            continue

        # (d) Confusable characters
        if ch in _CONFUSABLES_MAP:
            target = _CONFUSABLES_MAP[ch]
            hit = UnicodeHit(
                codepoint=cp_str,
                name=c_name,
                char=ch,
                category="confusable",
                severity=Severity.MEDIUM,
                start_py=i,
                end_py=i + 1,
                range=char_range,
                recovered_to=target,
                note=f"Confusable character '{ch}' resolves to ASCII '{target}'",
            )
            result.hits.append(hit)
            result.confusable_count += 1
            i += 1
            continue

        # (g) Isolated non-ASCII in comments
        if in_comment:
            hit = UnicodeHit(
                codepoint=cp_str,
                name=c_name,
                char=ch,
                category="non_ascii",
                severity=Severity.INFO,
                start_py=i,
                end_py=i + 1,
                range=char_range,
                note="Non-ASCII character in comment",
            )
            result.hits.append(hit)
            i += 1
            continue

        i += 1

    # 2. Identifier-level scan for mixed-scripts and dangerous confusable recoveries
    for m in IDENTIFIER_REGEX.finditer(text):
        word = m.group(0)
        start_p, end_p = m.span()
        word_range = om.span_to_range(start_p, end_p)

        # Check recovery of the full word
        recovered_word = "".join(_CONFUSABLES_MAP.get(c, c) for c in word)

        # Check if the word recovers to a dangerous API or keyword (the "ехес" case)
        if recovered_word != word and recovered_word.lower() in DANGEROUS_TARGETS:
            hit = UnicodeHit(
                codepoint="homoglyph_recovery",
                name="Dangerous Identifier Recovery",
                char=word,
                category="dangerous_recovery",
                severity=Severity.HIGH,
                start_py=start_p,
                end_py=end_p,
                range=word_range,
                recovered_to=recovered_word,
                note=(
                    f"Obfuscated dangerous identifier: '{word}' recovers "
                    f"to keyword/API '{recovered_word}'"
                ),
            )
            result.hits.append(hit)

        # (e) Mixed-script identifier detection
        if is_mixed_script(word):
            scripts_found = get_scripts(word)
            hit = UnicodeHit(
                codepoint=f"mixed({','.join(sorted(scripts_found))})",
                name="Mixed Script Identifier",
                char=word,
                category="mixed_script",
                severity=Severity.MEDIUM,
                start_py=start_p,
                end_py=end_p,
                range=word_range,
                recovered_to=recovered_word if recovered_word != word else None,
                note=f"Identifier '{word}' mixes scripts: {', '.join(sorted(scripts_found))}",
            )
            result.hits.append(hit)
            result.mixed_script_count += 1

    return result
