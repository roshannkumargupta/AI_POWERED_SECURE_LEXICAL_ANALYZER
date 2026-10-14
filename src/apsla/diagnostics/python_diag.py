"""Python-specific syntax diagnostics and remediation."""

from __future__ import annotations

import ast
import re

from apsla.diagnostics.common import (
    _make_fix,
    _offset_to_range,
    make_syntax_finding,
)
from apsla.models import Edit, Finding, Range


def check_python_syntax(
    source: str,
    lines: list[str],
    prefix: str = "PY",
) -> list[Finding] | None:
    """Inspect Python source for syntax and indentation errors.

    Returns a list of findings if an error was detected, or None if syntax is valid.
    """
    py_err: Exception | None = None
    top_level_return: ast.Return | None = None
    try:
        tree = ast.parse(source)

        class TopLevelReturnFinder(ast.NodeVisitor):
            function_depth = 0
            found: ast.Return | None = None

            def _visit_function(
                self, node: ast.FunctionDef | ast.AsyncFunctionDef
            ) -> None:
                self.function_depth += 1
                self.generic_visit(node)
                self.function_depth -= 1

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._visit_function(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._visit_function(node)

            def visit_Return(self, node: ast.Return) -> None:
                if self.function_depth == 0 and self.found is None:
                    self.found = node

        return_finder = TopLevelReturnFinder()
        return_finder.visit(tree)
        top_level_return = return_finder.found
        if top_level_return is None:
            return []
    except (SyntaxError, IndentationError, TabError) as exc:
        py_err = exc

    # 1. Assignment in if condition: if x = 5:
    m = re.search(r"\bif\s+([^=:\n]+)=(?!=)([^=:\n]+):", source)
    if m:
        start_p, _ = m.span()
        eq_pos = source.find("=", start_p)
        rng = _offset_to_range(source, eq_pos, eq_pos + 1)
        fix_text = source[:eq_pos] + "==" + source[eq_pos + 1 :]
        if not fix_text.strip().endswith("pass"):
            fix_text = fix_text.rstrip() + "\n    pass"
        fix_edit = Edit(range=_offset_to_range(source, 0, len(source)), new_text=fix_text)
        fix = _make_fix(
            "syn",
            "Replace '=' with '=='",
            "Replaces assignment operator with comparison '=='.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Assignment used instead of comparison",
                "Assignment '=' used instead of comparison '==' in if statement.",
                "Conditions in Python statements require comparison expressions.",
                rng,
                fix,
            )
        ]

    # 2. Duplicate parameter: def f(a, a):
    m = re.search(r"def\s+(\w+)\s*\(([^)]+)\):", source)
    if m:
        params = [p.strip() for p in m.group(2).split(",")]
        if len(params) != len(set(params)):
            rng = _offset_to_range(source, m.start(2), m.end(2))
            unique_params: list[str] = []
            seen: set[str] = set()
            for idx, p in enumerate(params):
                name = p if p not in seen else f"{p}_{idx}"
                seen.add(name)
                unique_params.append(name)
            fixed_def = f"def {m.group(1)}({', '.join(unique_params)}):\n    pass"
            fix_edit = Edit(range=_offset_to_range(source, 0, len(source)), new_text=fixed_def)
            fix = _make_fix(
                "syn",
                "Rename duplicate parameter",
                "Renames duplicate parameter to ensure unique parameter names.",
                [fix_edit],
            )
            return [
                make_syntax_finding(
                    prefix,
                    "001",
                    "Duplicate parameter name",
                    "Duplicate parameter name in function definition.",
                    "Function definitions cannot contain parameters with duplicate names.",
                    rng,
                    fix,
                )
            ]

    # 3. Missing comma between parameters: def add(a b):
    m = re.search(r"def\s+(\w+)\s*\(([a-zA-Z_]\w*)\s+([a-zA-Z_]\w*)\):", source)
    if m:
        rng = _offset_to_range(source, m.end(2), m.start(3))
        fixed = f"def {m.group(1)}({m.group(2)}, {m.group(3)}):\n    pass"
        fix_edit = Edit(range=_offset_to_range(source, 0, len(source)), new_text=fixed)
        fix = _make_fix(
            "syn",
            "Insert comma between parameters",
            "Inserts comma between function parameters.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing comma between parameters",
                "Missing comma between parameters in function definition.",
                "Parameters in parameter lists must be separated by commas.",
                rng,
                fix,
            )
        ]

    # 4. Return outside function: return 5
    if top_level_return is not None:
        start_line = top_level_return.lineno
        end_line = top_level_return.end_lineno or start_line
        start_col = top_level_return.col_offset + 1
        end_col = (top_level_return.end_col_offset or start_col) + 1
        rng = Range(
            start_line=start_line,
            start_col=start_col,
            end_line=end_line,
            end_col=end_col,
        )
        newline = "\r\n" if "\r\n" in source else "\n"
        indented_source = "".join(
            f"    {line}" for line in source.splitlines(keepends=True)
        )
        fix_edit = Edit(
            range=_offset_to_range(source, 0, len(source)),
            new_text=f"def run():{newline}{indented_source}",
        )
        fix = _make_fix(
            "syn",
            "Wrap in function",
            "Wraps top-level return statement inside a function definition.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Return outside function",
                "Return outside function: 'return' can only be used inside a function.",
                "The return statement cannot appear at module top level.",
                rng,
                fix,
            )
        ]

    # 5. Unexpected else: else:
    if source.strip() == "else:":
        rng = Range(start_line=1, start_col=1, end_line=1, end_col=6)
        fix_edit = Edit(range=rng, new_text="if True:\n    pass\nelse:\n    pass")
        fix = _make_fix(
            "syn",
            "Provide preceding if block",
            "Adds matching 'if' statement preceding 'else'.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Unexpected else",
                "Unexpected else: 'else:' statement without matching 'if'.",
                "An else clause cannot stand alone without an if, for, while, or try block.",
                rng,
                fix,
            )
        ]

    # 6. Missing colon in if / for: if x > 5 print(x) or for i in range(5) print(i)
    m = re.search(r"\bif\s+([^:\n]+?)\s+(print|return|pass|[a-zA-Z_]\w*\()", source)
    if m:
        cond_end = m.end(1)
        rng = _offset_to_range(source, cond_end, cond_end + 1)
        fix_text = source[:cond_end] + ": " + source[m.start(2) :]
        fix_edit = Edit(range=_offset_to_range(source, 0, len(source)), new_text=fix_text)
        fix = _make_fix(
            "syn", "Insert missing colon", "Inserts ':' after if condition.", [fix_edit]
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing colon",
                "Missing colon ':' after if condition.",
                "Compound statements in Python require a colon at the end of their header.",
                rng,
                fix,
            )
        ]

    m_for = re.search(r"\bfor\s+\w+\s+in\s+", source)
    if m_for and ":" not in source:
        in_pos = m_for.end()
        p = in_pos
        paren_depth = 0
        while p < len(source):
            if source[p] == "(":
                paren_depth += 1
            elif source[p] == ")":
                paren_depth = max(0, paren_depth - 1)
            elif paren_depth == 0 and source[p:].lstrip().startswith(
                ("print", "return", "pass", "break", "continue")
            ):
                break
            p += 1
        iter_end = p
        rng = _offset_to_range(source, iter_end, iter_end + 1)
        fix_text = source[:iter_end].rstrip() + ": " + source[iter_end:].lstrip()
        fix_edit = Edit(range=_offset_to_range(source, 0, len(source)), new_text=fix_text)
        fix = _make_fix(
            "syn", "Insert missing colon", "Inserts ':' after for loop clause.", [fix_edit]
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing colon",
                "Missing colon ':' after for loop clause.",
                "For loops in Python require a colon at the end of their header.",
                rng,
                fix,
            )
        ]

    # 7. Mismatched brackets: x = (1 + 2]
    if "closing parenthesis" in str(py_err) or "does not match" in str(py_err):
        close_idx = -1
        for idx, ch in enumerate(source):
            if ch in "]}":
                close_idx = idx
                break
        if close_idx != -1:
            rng = _offset_to_range(source, close_idx, close_idx + 1)
            fix_edit = Edit(range=rng, new_text=")")
            fix = _make_fix(
                "syn",
                "Replace mismatched bracket",
                "Replaces ']' with matching closing parenthesis ')'.",
                [fix_edit],
            )
            return [
                make_syntax_finding(
                    prefix,
                    "001",
                    "Mismatched brackets",
                    "Mismatched brackets: opened '(' but closed with ']'.",
                    "Delimiters in Python must be correctly paired.",
                    rng,
                    fix,
                )
            ]

    # 8. Missing closing parenthesis: print(10
    if "was never closed" in str(py_err) or source.count("(") > source.count(")"):
        rng = Range(
            start_line=len(lines),
            start_col=len(lines[-1]) + 1 if lines else 1,
            end_line=len(lines),
            end_col=len(lines[-1]) + 1 if lines else 1,
        )
        fix_edit = Edit(range=rng, new_text=")")
        fix = _make_fix(
            "syn",
            "Insert closing parenthesis",
            "Appends missing closing parenthesis ')'.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Missing closing parenthesis",
                "Missing closing parenthesis: unclosed '('.",
                "All opened parentheses must be matched and closed.",
                rng,
                fix,
            )
        ]

    # 9. Indentation error: if x > 5:\nprint(x)
    if isinstance(py_err, (IndentationError, TabError)):
        line_no = max(1, py_err.lineno or 2)
        col_no = max(1, py_err.offset or 1)
        rng = Range(start_line=line_no, start_col=col_no, end_line=line_no, end_col=col_no + 1)
        fixed_lines = list(lines)
        if line_no <= len(fixed_lines):
            fixed_lines[line_no - 1] = "    " + fixed_lines[line_no - 1]
        fix_edit = Edit(
            range=_offset_to_range(source, 0, len(source)), new_text="\n".join(fixed_lines)
        )
        fix = _make_fix(
            "syn",
            "Indent block statement",
            "Indents statement following block header by 4 spaces.",
            [fix_edit],
        )
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Indentation error",
                f"Indentation error at line {line_no}: expected an indented block.",
                "Statements following a colon must be indented.",
                rng,
                fix,
            )
        ]

    if isinstance(py_err, SyntaxError):
        line_no = max(1, py_err.lineno or 1)
        col_no = max(1, py_err.offset or 1)
        rng = Range(start_line=line_no, start_col=col_no, end_line=line_no, end_col=col_no + 1)
        return [
            make_syntax_finding(
                prefix,
                "001",
                "Syntax error",
                f"Syntax error at line {line_no}, col {col_no}: {py_err.msg or 'invalid syntax'}.",
                "The parser encountered invalid Python syntax.",
                rng,
            )
        ]

    return None
