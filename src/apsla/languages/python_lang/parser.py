"""Structure parser for Python converting ast.parse into StructTree representation."""

from __future__ import annotations

import ast

from apsla.languages.struct_tree import (
    AssignmentNode,
    CallNode,
    ClassNode,
    ErrorNode,
    FileNode,
    FunctionNode,
    ImportNode,
    StructTree,
)
from apsla.lexing.token import Token
from apsla.models import Range


def _ast_range(node: ast.AST, lines: list[str]) -> Range:
    """Calculate 1-indexed line and col Range for an AST node."""
    start_line = getattr(node, "lineno", 1)
    start_col = getattr(node, "col_offset", 0) + 1
    end_line = getattr(node, "end_lineno", start_line)
    end_col = (
        getattr(
            node,
            "end_col_offset",
            len(lines[start_line - 1]) if 0 <= start_line - 1 < len(lines) else 1,
        )
        + 1
    )
    return Range(
        start_line=start_line,
        start_col=start_col,
        end_line=end_line,
        end_col=end_col,
    )


def _get_call_name(node: ast.expr) -> str:
    """Resolve callee name string from AST call node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _get_call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def parse_python_structure(source: str, tokens: list[Token] | None = None) -> StructTree:
    """Parse Python source into a StructTree."""
    lines = source.splitlines()
    file_range = Range(
        start_line=1,
        start_col=1,
        end_line=max(1, len(lines)),
        end_col=len(lines[-1]) + 1 if lines else 1,
    )
    root = FileNode(range=file_range, language="python")

    errors: list[ErrorNode] = []
    calls: list[CallNode] = []
    functions: list[FunctionNode] = []
    classes: list[ClassNode] = []
    assignments: list[AssignmentNode] = []
    imports: list[ImportNode] = []

    try:
        parsed_ast = ast.parse(source)
    except SyntaxError as e:
        err_line = e.lineno or 1
        err_col = (e.offset or 0) + 1
        err_node = ErrorNode(
            message=f"Syntax error: {e.msg}",
            range=Range(
                start_line=err_line, start_col=err_col, end_line=err_line, end_col=err_col + 1
            ),
            unexpected_token=e.text or "",
        )
        errors.append(err_node)
        root.children.append(err_node)
        return StructTree(
            root=root,
            language="python",
            errors=errors,
            calls=calls,
            functions=functions,
            classes=classes,
            assignments=assignments,
            imports=imports,
        )

    for stmt in ast.walk(parsed_ast):
        if isinstance(stmt, ast.ClassDef):
            c_node = ClassNode(
                name=stmt.name,
                range=_ast_range(stmt, lines),
                is_struct=False,
            )
            classes.append(c_node)
            root.children.append(c_node)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = [arg.arg for arg in stmt.args.args]
            f_node = FunctionNode(
                name=stmt.name,
                range=_ast_range(stmt, lines),
                params=params,
                is_method=False,
            )
            functions.append(f_node)
            root.children.append(f_node)
        elif isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            target = ""
            if isinstance(stmt, ast.Assign) and stmt.targets:
                if isinstance(stmt.targets[0], ast.Name):
                    target = stmt.targets[0].id
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                target = stmt.target.id
            a_node = AssignmentNode(
                target=target,
                range=_ast_range(stmt, lines),
            )
            assignments.append(a_node)
            root.children.append(a_node)
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
            mod_name = ""
            names: list[str] = []
            if isinstance(stmt, ast.Import):
                mod_name = ", ".join(alias.name for alias in stmt.names)
            else:
                mod_name = stmt.module or ""
                names = [alias.name for alias in stmt.names]
            imp_node = ImportNode(
                module=mod_name,
                range=_ast_range(stmt, lines),
                names=names,
                is_include=False,
            )
            imports.append(imp_node)
            root.children.append(imp_node)
        elif isinstance(stmt, ast.Call):
            callee = _get_call_name(stmt.func)
            if callee:
                arg_ranges = [_ast_range(arg, lines) for arg in stmt.args]
                call_node = CallNode(
                    callee=callee,
                    range=_ast_range(stmt, lines),
                    args=arg_ranges,
                )
                calls.append(call_node)

    return StructTree(
        root=root,
        language="python",
        errors=errors,
        calls=calls,
        functions=functions,
        classes=classes,
        assignments=assignments,
        imports=imports,
    )
