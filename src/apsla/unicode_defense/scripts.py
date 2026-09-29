"""Unicode script identification and mixed-script detection."""

from __future__ import annotations

import unicodedata

import regex

# Compiled script matchers using Unicode property escapes
_MAJOR_SCRIPTS = [
    "Latin",
    "Cyrillic",
    "Greek",
    "Arabic",
    "Hebrew",
    "Devanagari",
    "Han",
    "Hiragana",
    "Katakana",
    "Hangul",
    "Bengali",
    "Armenian",
    "Georgian",
    "Thai",
    "Ethiopic",
]

_SCRIPT_PATTERNS: list[tuple[str, regex.Pattern]] = [
    (script, regex.compile(rf"^\p{{Script={script}}}$")) for script in _MAJOR_SCRIPTS
]

_COMMON_PATTERN = regex.compile(r"^\p{Script=Common}$")
_INHERITED_PATTERN = regex.compile(r"^\p{Script=Inherited}$")


def get_character_script(ch: str) -> str:
    """Identify the Unicode script of a single character.

    Args:
        ch: A single character string.

    Returns:
        str: Name of the script (e.g. 'Latin', 'Cyrillic', 'Common', 'Unknown').
    """
    if not ch:
        return "Unknown"

    char = ch[0]
    if _COMMON_PATTERN.match(char):
        return "Common"
    if _INHERITED_PATTERN.match(char):
        return "Inherited"

    for script, pat in _SCRIPT_PATTERNS:
        if pat.match(char):
            return script

    # Fallback to checking unicodedata name
    name = unicodedata.name(char, "")
    for script in _MAJOR_SCRIPTS:
        if script.upper() in name:
            return script

    return "Unknown"


def get_scripts(text: str) -> set[str]:
    """Return the set of distinct substantive Unicode scripts present in text.

    Excludes 'Common' and 'Inherited' scripts (digits, punctuation, spaces).

    Args:
        text: Input string.

    Returns:
        set[str]: Set of script names found in the text.
    """
    scripts: set[str] = set()
    for ch in text:
        script = get_character_script(ch)
        if script not in ("Common", "Inherited", "Unknown"):
            scripts.add(script)
    return scripts


def is_mixed_script(identifier: str) -> bool:
    """Determine whether an identifier combines characters from multiple scripts.

    Identifiers containing characters from 2 or more distinct substantive scripts
    (e.g. Latin and Cyrillic) are flagged as mixed-script homoglyph risks.

    Args:
        identifier: Variable or symbol name to inspect.

    Returns:
        bool: True if the identifier contains characters from > 1 substantive script.
    """
    scripts = get_scripts(identifier)
    return len(scripts) > 1
