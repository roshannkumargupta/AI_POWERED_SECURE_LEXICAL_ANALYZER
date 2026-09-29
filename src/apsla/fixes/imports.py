"""Python import insertion and deduplication utilities."""

from __future__ import annotations

import ast
import re

from apsla.models import Edit, Range


def ensure_import_python(source: str, import_stmt: str) -> list[Edit]:
    """Ensure a required import statement is present in Python source code.

    Inserts the import after module docstrings and 'from __future__' lines,
    merging with existing import blocks without duplicate imports.

    Args:
        source: Python source code.
        import_stmt: Import statement (e.g., 'import shlex', 'shlex', 'from os import path').

    Returns:
        List of Edit instances (empty list if import already exists).
    """
    clean_stmt = import_stmt.strip()
    if not (clean_stmt.startswith("import ") or clean_stmt.startswith("from ")):
        clean_stmt = f"import {clean_stmt}"

    # Determine what module or names this import provides
    try:
        import_ast = ast.parse(clean_stmt)
        needed_node = import_ast.body[0] if import_ast.body else None
    except Exception:
        needed_node = None

    # Check if already present in source
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and isinstance(needed_node, ast.Import):
                existing_names = {alias.name for alias in node.names}
                needed_names = {alias.name for alias in needed_node.names}
                if needed_names.issubset(existing_names):
                    return []
            elif isinstance(node, ast.ImportFrom) and isinstance(needed_node, ast.ImportFrom):
                if node.module == needed_node.module:
                    existing_names = {alias.name for alias in node.names}
                    needed_names = {alias.name for alias in needed_node.names}
                    if needed_names.issubset(existing_names):
                        return []
            elif isinstance(node, ast.Import) and isinstance(needed_node, ast.ImportFrom):
                # e.g. source has 'import os' and we need 'from os import path' -> os is already there!
                pass
    except SyntaxError:
        # Fallback to regex check on raw source
        if re.search(rf"\b{re.escape(clean_stmt)}\b", source):
            return []

    # Determine optimal insertion line
    insert_line = 1
    try:
        tree = ast.parse(source)
        # 1. Skip module docstring
        if tree.body and isinstance(tree.body[0], ast.Expr):
            val = getattr(tree.body[0], "value", None)
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                insert_line = tree.body[0].end_lineno + 1

        # 2. Skip __future__ imports
        for stmt in tree.body:
            if isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__":
                insert_line = max(insert_line, stmt.end_lineno + 1)

        # 3. If there are other top-level imports right after, merge after the last contiguous import
        last_import_line = 0
        for stmt in tree.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                # Only consider imports near the top of the file
                if stmt.lineno <= insert_line + 5 or (last_import_line and stmt.lineno <= last_import_line + 2):
                    last_import_line = max(last_import_line, stmt.end_lineno)
        if last_import_line >= insert_line:
            insert_line = last_import_line + 1

    except SyntaxError:
        # Fallback line scanning: skip shebang, coding, docstrings
        lines = source.splitlines()
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                insert_line = idx + 1
            else:
                break

    lines = source.splitlines(keepends=True)
    total_lines = len(lines)
    if insert_line > total_lines:
        insert_line = total_lines + 1

    edit_range = Range(
        start_line=insert_line,
        start_col=1,
        end_line=insert_line,
        end_col=1,
    )

    new_text = f"{clean_stmt}\n"

    return [Edit(range=edit_range, new_text=new_text)]
