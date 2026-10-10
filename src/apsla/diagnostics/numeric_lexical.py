"""Numeric literal lexical diagnostics and remediation."""

from __future__ import annotations

import re
from collections.abc import Callable

from apsla.diagnostics.common import (
    _make_fix,
    _offset_to_range,
)
from apsla.models import Edit, Finding, Fix, Range, Severity


def check_numeric_lexical_diagnostics(
    source: str,
    language: str,
    is_inside_string_or_comment: Callable[[int], bool],
    add_finding: Callable[
        [str, str, str, str, Range, Fix | None, Severity],
        None,
    ],
) -> list[Finding] | None:
    """Check for malformed or invalid numeric literals across languages."""
    # 9. Invalid Binary Literal (0b102)
    for m in re.finditer(r"\b0b([01]*)([2-9a-zA-Z_]+)\b", source):
        if is_inside_string_or_comment(m.start()):
            continue
        start_p, end_p = m.span()
        valid_part = m.group(1) or "1"
        rng = _offset_to_range(source, start_p, end_p)
        fix_edit = Edit(range=rng, new_text=f"0b{valid_part}")
        fix = _make_fix(
            "lex",
            "Fix binary literal",
            f"Removes non-binary digits from binary literal to form '0b{valid_part}'.",
            [fix_edit],
        )
        add_finding(
            "010",
            "Invalid binary literal",
            f"Invalid binary literal '{m.group(0)}': binary literals may only contain digits 0 and 1.",
            "Binary literals starting with 0b or 0B may only contain 0 and 1 digits.",
            rng,
            fix,
            Severity.HIGH,
        )
        return []

    # 10. Invalid Hexadecimal Literal (0xG1, 0x;)
    for m in re.finditer(r"\b0x([0-9a-fA-F]*)([g-zG-Z_][0-9a-zA-Z_]*)\b", source):
        if is_inside_string_or_comment(m.start()):
            continue
        start_p, end_p = m.span()
        rng = _offset_to_range(source, start_p, end_p)
        fix_edit = Edit(range=rng, new_text="0x01")
        fix = _make_fix(
            "lex",
            "Fix hexadecimal literal",
            "Replaces invalid hexadecimal literal with valid hex literal '0x01'.",
            [fix_edit],
        )
        add_finding(
            "011",
            "Invalid hexadecimal literal",
            f"Invalid hexadecimal literal '{m.group(0)}': invalid hexadecimal digit.",
            "Hexadecimal literals starting with 0x or 0X may only contain digits 0-9 and a-f/A-F.",
            rng,
            fix,
            Severity.HIGH,
        )
        return []

    for m in re.finditer(r"\b0x(?=[;,\s\)\}\]]|$)", source):
        if is_inside_string_or_comment(m.start()):
            continue
        start_p, end_p = m.span()
        rng = _offset_to_range(source, start_p, end_p)
        fix_edit = Edit(range=rng, new_text="0x0")
        fix = _make_fix(
            "lex",
            "Complete hexadecimal literal",
            "Appends '0' to complete hexadecimal literal '0x0'.",
            [fix_edit],
        )
        add_finding(
            "011",
            "Invalid hexadecimal literal",
            "Invalid hexadecimal literal: 0x has no hexadecimal digits.",
            "Hexadecimal literals must have at least one valid hex digit after the prefix.",
            rng,
            fix,
            Severity.HIGH,
        )
        return []

    # 11. Invalid Exponent (1e+, 1e-) - must NOT be followed by a digit
    for m in re.finditer(r"\b(\d+(?:\.\d+)?)[eE](?:[+-](?!\d)|(?![+-]|\d))", source):
        if is_inside_string_or_comment(m.start()):
            continue
        start_p, end_p = m.span()
        rng = _offset_to_range(source, start_p, end_p)
        full_match = m.group(0)
        fix_edit = Edit(range=rng, new_text=f"{full_match}0")
        fix = _make_fix(
            "lex",
            "Add exponent digit",
            f"Appends '0' to complete exponent '{full_match}0'.",
            [fix_edit],
        )
        title = "Invalid numeric exponent" if language == "javascript" else "Invalid exponent"
        add_finding(
            "014",
            title,
            f"{title} '{full_match}': exponent requires at least one digit.",
            "Scientific notation exponent (e or E) must be followed by digits.",
            rng,
            fix,
            Severity.HIGH,
        )
        return []

    # 12. Invalid Numeric Literal: Consecutive Underscores (1__2)
    for m in re.finditer(r"\b(\d+)__+(\d+)\b", source):
        if is_inside_string_or_comment(m.start()):
            continue
        start_p, end_p = m.span()
        rng = _offset_to_range(source, start_p, end_p)
        d1, d2 = m.group(1), m.group(2)
        fix_edit = Edit(range=rng, new_text=f"{d1}_{d2}")
        fix = _make_fix(
            "lex",
            "Replace consecutive underscores",
            f"Replaces consecutive underscores with single underscore '{d1}_{d2}'.",
            [fix_edit],
        )
        add_finding(
            "012",
            "Invalid numeric literal",
            f"Invalid numeric literal '{m.group(0)}': consecutive underscores are not allowed.",
            "Numeric literals may only have single underscore separators between digits.",
            rng,
            fix,
            Severity.HIGH,
        )
        return []

    # 13. Invalid Numeric Literal / Token: Number directly followed by identifier (12abc)
    for m in re.finditer(r"\b(\d+)([a-zA-Z_]\w*)\b", source):
        if is_inside_string_or_comment(m.start()):
            continue
        prefix_digit, suffix = m.group(1), m.group(2)
        if prefix_digit == "0" and suffix[:1].lower() in ("x", "b", "o"):
            continue
        if re.fullmatch(r"(?:_\d+)+", suffix):
            continue
        if suffix[:1].lower() == "e" and re.match(
            r"\d+(?:\.\d+)?[eE][+-]?\d+", source[m.start() :]
        ):
            continue
        is_valid_suffix = False
        if (
            (language == "python" and suffix.lower() == "j")
            or (
                language in ("java", "cpp")
                and suffix
                in (
                    "L",
                    "l",
                    "f",
                    "F",
                    "d",
                    "D",
                    "u",
                    "U",
                    "ul",
                    "UL",
                    "ll",
                    "LL",
                )
            )
            or (language == "javascript" and suffix == "n")
        ):
            is_valid_suffix = True

        if not is_valid_suffix:
            start_p, end_p = m.span()
            rng = _offset_to_range(source, start_p, end_p)
            fix_edit = Edit(range=rng, new_text=prefix_digit)
            fix = _make_fix(
                "lex",
                "Remove invalid identifier suffix",
                f"Removes suffix '{suffix}' from numeric literal '{prefix_digit}'.",
                [fix_edit],
            )
            title = (
                "Malformed numeric literal/token"
                if language == "java"
                else "Invalid numeric literal/token"
                if language == "javascript"
                else "Invalid numeric literal"
            )
            add_finding(
                "013",
                title,
                f"{title} '{m.group(0)}': identifier attached to numeric literal.",
                "Numeric literals cannot have identifier characters attached without a space or operator.",
                rng,
                fix,
                Severity.HIGH,
            )
            return []

    # 14. Malformed Numeric Literal: Multiple Decimal Points (1.2.3)
    for m in re.finditer(r"\b\d+\.\d+\.\d+(?:\.\d+)*\b", source):
        if is_inside_string_or_comment(m.start()):
            continue
        start_p, end_p = m.span()
        rng = _offset_to_range(source, start_p, end_p)
        first_float = m.group(0).split(".")[0] + "." + m.group(0).split(".")[1]
        fix_edit = Edit(range=rng, new_text=first_float)
        fix = _make_fix(
            "lex",
            "Fix multiple decimal points",
            f"Simplifies malformed literal to '{first_float}'.",
            [fix_edit],
        )
        add_finding(
            "015",
            "Malformed numeric literal",
            f"Malformed numeric literal '{m.group(0)}': multiple decimal points in number.",
            "Floating point numbers can only contain a single decimal point.",
            rng,
            fix,
            Severity.HIGH,
        )
        return []

    return None
