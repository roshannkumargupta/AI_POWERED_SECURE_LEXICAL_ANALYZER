"""JavaScript-specific syntax diagnostics and remediation."""

from __future__ import annotations

import re

from apsla.diagnostics.common import (
    _make_fix,
    _offset_to_range,
    make_syntax_finding,
)
from apsla.models import Edit, Finding, Range


def check_javascript_syntax(
    source: str,
    lines: list[str],
    prefix: str = "JS",
) -> list[Finding] | None:
    """Inspect JavaScript source for syntax errors and generate deterministic fixes."""
    # 1. Illegal top-level return in a normal script: return 5;
    if re.search(r"^\s*return\b", source, re.MULTILINE) and not re.search(
        r"\bfunction\b", source
    ):
        rng = Range(start_line=1, start_col=1, end_line=1, end_col=len(source) + 1)
        fix_edit = Edit(range=rng, new_text=f"function main() {{ {source} }}")
        fix = _make_fix(
            "syn",
            "Wrap in function",
            "Wraps top-level return inside a function declaration.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Illegal top-level return in a normal script",
                "Illegal top-level return in a normal script: 'return' outside function.",
                "Return statements can only appear within function bodies.",
                rng,
                fix,
            )
        ]

    # 2. Missing variable name: const = 10;
    m = re.search(r"\b(const|let|var)\s*=\s*", source)
    if m:
        rng = _offset_to_range(source, m.start(1), m.end(1))
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
                "Variable declarations require an identifier name.",
                rng,
                fix,
            )
        ]

    # 3. Constant declaration requires initializer: const x;
    m = re.search(r"\bconst\s+(\w+)\s*;", source)
    if m:
        semi_pos = m.end() - 1
        rng = _offset_to_range(source, m.start(), m.end())
        fix_edit = Edit(range=_offset_to_range(source, semi_pos, semi_pos), new_text=" = 0")
        fix = _make_fix(
            "syn",
            "Add initializer",
            "Initializes constant with default value '= 0'.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Constant declaration requires initializer",
                "Constant declaration requires initializer: missing '=' in const declaration.",
                "Constants declared with 'const' must be initialized upon declaration.",
                rng,
                fix,
            )
        ]

    # 4. Function declaration requires a name: function () {}
    m = re.search(r"\bfunction\s*\(\s*\)", source)
    if m:
        rng = _offset_to_range(source, m.start(), m.end())
        fix_edit = Edit(
            range=_offset_to_range(source, m.start() + 8, m.start() + 8), new_text=" fn"
        )
        fix = _make_fix(
            "syn", "Add function name", "Inserts function identifier 'fn'.", [fix_edit]
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Function declaration requires a name",
                "Function declaration requires a name.",
                "Standalone function declarations in statement position require an identifier.",
                rng,
                fix,
            )
        ]

    # 5. Invalid else placement: if (x > 5) else {}
    m = re.search(r"\bif\s*\([^)]+\)\s*else\b", source)
    if m:
        else_idx = source.find("else", m.start())
        rng = _offset_to_range(source, else_idx, else_idx + 4)
        fix_edit = Edit(range=_offset_to_range(source, else_idx, else_idx), new_text="{} ")
        fix = _make_fix(
            "syn",
            "Insert statement block",
            "Inserts statement block '{}' between if condition and else.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Invalid else placement",
                "Invalid else placement: missing statement between if condition and else.",
                "An if condition must have a consequent body before an else clause.",
                rng,
                fix,
            )
        ]

    # 6. Missing semicolon in for loop: for (let i = 0 i < 5; i++) {}
    m = re.search(r"\bfor\s*\(\s*(?:let|var)\s+\w+\s*=\s*\d+\s+[^;]+;", source)
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
                    "Clauses of a for loop header must be separated by semicolons.",
                    rng,
                    fix,
                )
            ]

    # 7. Missing colon after case label: switch (x) { case 1 console.log(x); }
    m = re.search(r"\bcase\s+([^:]+?)\s+(console|break|return|[a-zA-Z_]\w*)", source)
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

    # 8. Missing closing parenthesis in condition / parameters / grouping
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

    m = re.search(r"\bfunction\s+\w+\s*\([^)\n]+\s*\{", source)
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
                "Missing closing parenthesis in parameter list.",
                "Parameter lists must be closed with ')' before the function body.",
                rng,
                fix,
            )
        ]

    m = re.search(r"=\s*\([^;\)\n]+\s*;", source)
    if m:
        semi_pos = m.end() - 1
        rng = _offset_to_range(source, semi_pos, semi_pos + 1)
        fix_edit = Edit(range=_offset_to_range(source, semi_pos, semi_pos), new_text=")")
        fix = _make_fix(
            "syn", "Insert closing parenthesis", "Inserts ')' before semicolon.", [fix_edit]
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing closing parenthesis",
                "Missing closing parenthesis in expression.",
                "Opened parentheses in expressions must be closed.",
                rng,
                fix,
            )
        ]

    return None
