"""Java-specific syntax diagnostics and remediation."""

from __future__ import annotations

import re

from apsla.diagnostics.common import (
    _make_fix,
    _offset_to_range,
    make_syntax_finding,
)
from apsla.models import Edit, Finding, Range


def check_java_syntax(
    source: str,
    lines: list[str],
    prefix: str = "JAVA",
) -> list[Finding] | None:
    """Inspect Java source for syntax errors and generate deterministic fixes."""
    # 1. Illegal break outside loop or switch: break;
    m_java_break = re.search(r"^\s*break\s*;", source, re.MULTILINE)
    if m_java_break and not any(k in source for k in ("while", "for", "switch", "do")):
        start_p, end_p = m_java_break.span()
        rng = _offset_to_range(source, start_p, end_p)
        fix_edit = Edit(range=rng, new_text="while (true) { break; }")
        fix = _make_fix(
            "syn",
            "Wrap break in loop",
            "Wraps 'break;' statement inside a loop.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Illegal break outside loop or switch",
                "Illegal break outside loop or switch: 'break' can only be used in loops or switch blocks.",
                "A break statement must be enclosed within a loop or switch statement.",
                rng,
                fix,
            )
        ]

    # 2. Missing variable name: int = 10;
    m = re.search(r"\b(int|double|float|long|boolean|char|String)\s*=\s*", source)
    if m:
        eq_pos = m.end() - 1
        rng = _offset_to_range(source, m.start(1), eq_pos)
        fix_edit = Edit(range=_offset_to_range(source, m.end(1), m.end(1)), new_text=" x ")
        fix = _make_fix(
            "syn", "Insert variable name", "Inserts missing variable name 'x'.", [fix_edit]
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing variable name",
                "Missing variable name in declaration.",
                "Variable declarations require a type followed by an identifier name.",
                rng,
                fix,
            )
        ]

    # 3. Missing colon after case label: switch (x) { case 1 System.out.println(x); }
    m = re.search(r"\bcase\s+([^:]+?)\s+(System|break|return|[a-zA-Z_]\w*)", source)
    if m:
        val_end = m.end(1)
        rng = _offset_to_range(source, val_end, val_end + 1)
        fix_edit = Edit(range=_offset_to_range(source, val_end, val_end), new_text=":")
        fix = _make_fix(
            "syn",
            "Insert colon after case label",
            "Inserts missing ':' after case value.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing colon after case label",
                "Missing colon after case label in switch statement.",
                "Case labels in switch statements must be followed by a colon.",
                rng,
                fix,
            )
        ]

    # 4. Missing parentheses around condition: if x > 5 {}
    m = re.search(r"\bif\s+([^({\n]+?)\s*\{", source)
    if m:
        cond = m.group(1).strip()
        start_p, end_p = m.span(1)
        rng = _offset_to_range(source, start_p, end_p)
        fix_edit = Edit(range=rng, new_text=f"({cond})")
        fix = _make_fix(
            "syn",
            "Wrap condition in parentheses",
            "Wraps if statement condition in parentheses.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing parentheses around condition",
                "Missing parentheses around condition in if statement.",
                "In Java, conditions in if statements must be enclosed in parentheses.",
                rng,
                fix,
            )
        ]

    # 5. Missing closing parenthesis in if condition: if (x > 5 {}
    m = re.search(r"\bif\s*\([^)\n]+\s*\{", source)
    if m:
        brace_pos = source.find("{", m.start())
        rng = _offset_to_range(source, brace_pos, brace_pos + 1)
        fix_edit = Edit(range=_offset_to_range(source, brace_pos, brace_pos), new_text=") ")
        fix = _make_fix(
            "syn", "Insert closing parenthesis", "Inserts ')' before opening brace.", [fix_edit]
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing closing parenthesis",
                "Missing closing parenthesis in if condition.",
                "Parentheses around condition must be closed before the statement block.",
                rng,
                fix,
            )
        ]

    # 6. Malformed parameter list: public void test( {}
    m = re.search(r"\(\s*\{", source)
    if m:
        rng = _offset_to_range(source, m.start(), m.end())
        fix_edit = Edit(range=_offset_to_range(source, m.start(), m.start() + 1), new_text="()")
        fix = _make_fix(
            "syn",
            "Close parameter list",
            "Closes parameter list with ')' before opening brace.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Malformed parameter list",
                "Malformed parameter list: missing closing parenthesis ')'.",
                "Method parameter lists must be closed with ')' before the method body.",
                rng,
                fix,
            )
        ]

    # 7. Missing semicolon in for loop: for (int i = 0 i < 5; i++) {}
    m = re.search(r"\bfor\s*\(\s*int\s+\w+\s*=\s*\d+\s+[^;]+;", source)
    if m:
        sub = m.group(0)
        assign_m = re.search(r"=\s*\d+", sub)
        if assign_m:
            semi_insert = m.start() + assign_m.end()
            rng = _offset_to_range(source, semi_insert, semi_insert + 1)
            fix_edit = Edit(
                range=_offset_to_range(source, semi_insert, semi_insert), new_text=";"
            )
            fix = _make_fix(
                "syn",
                "Insert semicolon in for loop",
                "Inserts missing semicolon separating for loop init and condition.",
                [fix_edit],
            )
            return [
                make_syntax_finding(
                    prefix,
                    "001",
                    "Missing semicolon",
                    "Missing semicolon in for loop header.",
                    "The three clauses of a standard for loop must be separated by semicolons.",
                    rng,
                    fix,
                )
            ]

    # 8. Missing closing parenthesis in call: System.out.println("Hi"
    if ("println(" in source or "print(" in source) and source.count("(") > source.count(")"):
        rng = Range(
            start_line=len(lines),
            start_col=len(lines[-1]) + 1 if lines else 1,
            end_line=len(lines),
            end_col=len(lines[-1]) + 1 if lines else 1,
        )
        fix_edit = Edit(range=rng, new_text=");")
        fix = _make_fix(
            "syn",
            "Close method call",
            "Appends missing closing parenthesis and semicolon ');'.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing closing parenthesis",
                "Missing closing parenthesis in method call.",
                "Method invocations must be closed with ')'.",
                rng,
                fix,
            )
        ]

    # 9. Missing closing brace: class Demo {
    if source.count("{") > source.count("}"):
        rng = Range(
            start_line=len(lines),
            start_col=len(lines[-1]) + 1 if lines else 1,
            end_line=len(lines),
            end_col=len(lines[-1]) + 1 if lines else 1,
        )
        fix_edit = Edit(range=rng, new_text="\n}")
        fix = _make_fix(
            "syn", "Insert closing brace", "Appends missing closing brace '}'.", [fix_edit]
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing closing brace",
                "Missing closing brace '}' at end of class or block.",
                "Blocks and class declarations must have matching closing braces.",
                rng,
                fix,
            )
        ]

    # 10. Missing semicolon: int x = 10
    if not source.strip().endswith(";") and not source.strip().endswith("}"):
        rng = Range(
            start_line=len(lines),
            start_col=len(lines[-1]) + 1 if lines else 1,
            end_line=len(lines),
            end_col=len(lines[-1]) + 1 if lines else 1,
        )
        fix_edit = Edit(range=rng, new_text=";")
        fix = _make_fix(
            "syn",
            "Insert semicolon",
            "Appends missing semicolon ';' at end of statement.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing semicolon",
                "Missing semicolon at end of statement.",
                "Statements in Java must terminate with a semicolon ';'.",
                rng,
                fix,
            )
        ]

    return None
