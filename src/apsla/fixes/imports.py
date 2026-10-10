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
                if stmt.lineno <= insert_line + 5 or (
                    last_import_line and stmt.lineno <= last_import_line + 2
                ):
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


def ensure_import_java(source: str, import_stmt: str) -> list[Edit]:
    """Ensure a required import statement is present in Java source code.

    Inserts the import after package declarations, alphabetically sorted among
    existing import statements, with duplicate prevention.

    Args:
        source: Java source code text.
        import_stmt: Import statement or class name (e.g. 'java.sql.PreparedStatement').

    Returns:
        List of Edit instances (empty list if import already exists).
    """
    clean_stmt = import_stmt.strip()
    if not clean_stmt.startswith("import "):
        clean_stmt = f"import {clean_stmt}"
    if not clean_stmt.endswith(";"):
        clean_stmt = f"{clean_stmt};"

    # Extract target class/package
    m_import = re.match(r"import\s+(?:static\s+)?([A-Za-z0-9_.*]+)\s*;", clean_stmt)
    if not m_import:
        return []
    target_fqcn = m_import.group(1)

    lines = source.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped == clean_stmt:
            return []
        m_exist = re.match(r"import\s+(?:static\s+)?([A-Za-z0-9_.*]+)\s*;", stripped)
        if m_exist:
            exist_fqcn = m_exist.group(1)
            if exist_fqcn == target_fqcn:
                return []
            if exist_fqcn.endswith(".*"):
                pkg_prefix = exist_fqcn[:-2]
                if (
                    target_fqcn.startswith(pkg_prefix + ".")
                    and target_fqcn.count(".") == pkg_prefix.count(".") + 1
                ):
                    return []

    # Find existing imports and package line
    package_line = 0
    import_entries: list[tuple[int, str]] = []  # (line_number 1-based, import_stmt)
    first_type_line = 0

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("package ") and stripped.endswith(";"):
            package_line = idx
        elif stripped.startswith("import ") and stripped.endswith(";"):
            import_entries.append((idx, stripped))
        elif (
            not first_type_line
            and any(
                kw in stripped
                for kw in ("public ", "class ", "interface ", "enum ", "record ", "@")
            )
            and not stripped.startswith("//")
            and not stripped.startswith("/*")
        ):
            first_type_line = idx

    # If existing imports exist, insert alphabetically sorted
    if import_entries:
        insert_line = import_entries[-1][0] + 1
        for line_num, existing_imp in import_entries:
            if clean_stmt < existing_imp:
                insert_line = line_num
                break
    elif package_line > 0:
        insert_line = package_line + 1
    elif first_type_line > 0:
        insert_line = first_type_line
    else:
        insert_line = 1

    edit_range = Range(
        start_line=insert_line,
        start_col=1,
        end_line=insert_line,
        end_col=1,
    )
    new_text = f"{clean_stmt}\n"
    if not import_entries and package_line > 0 and insert_line == package_line + 1:
        new_text = f"\n{clean_stmt}\n"
    elif not import_entries and package_line == 0 and first_type_line > 0:
        new_text = f"{clean_stmt}\n\n"

    return [Edit(range=edit_range, new_text=new_text)]


def ensure_import_javascript(
    source: str,
    import_name: str,
    esm_stmt: str | None = None,
    cjs_stmt: str | None = None,
) -> list[Edit]:
    """Ensure a required import or require statement is present in JavaScript source code.

    Uses require() if the file uses CommonJS (require / module.exports),
    or import if ESM (import / export).
    Inserts after shebang, 'use strict', and existing top-of-file imports without duplicates.

    Args:
        source: JavaScript source code text.
        import_name: Name of module or identifier (e.g. 'crypto', 'dompurify', 'child_process').
        esm_stmt: Optional explicit ESM import statement (e.g. "import DOMPurify from 'dompurify';").
        cjs_stmt: Optional explicit CommonJS require statement (e.g. "const crypto = require('crypto');").

    Returns:
        List of Edit instances (empty if already imported).
    """
    clean_mod = import_name.strip().strip("'\"")

    # 1. Duplicate check: is module already imported or required?
    mod_patterns = [
        rf"require\s*\(\s*['\"]{re.escape(clean_mod)}['\"]\s*\)",
        rf"from\s+['\"]{re.escape(clean_mod)}['\"]",
        rf"import\s+['\"]{re.escape(clean_mod)}['\"]",
    ]
    if any(re.search(pat, source) for pat in mod_patterns):
        return []

    # Check if identifier itself is defined as import/require
    if re.search(rf"\b(?:const|let|var)\s+.*?\b{re.escape(clean_mod)}\b.*?=\s*require\(", source):
        return []

    # 2. Module format detection: CommonJS vs ESM
    has_cjs = bool(re.search(r"\b(?:require\s*\(|module\.exports|exports\.)", source))
    has_esm = bool(re.search(r"\b(?:import\s+|export\s+)", source))

    if has_esm and not has_cjs:
        is_esm = True
    elif has_cjs and not has_esm:
        is_esm = False
    elif has_esm and has_cjs:
        # If both are present, choose whichever statement pattern is explicitly given
        is_esm = esm_stmt is not None and cjs_stmt is None
    else:
        # Default: ESM if explicitly provided, else CommonJS
        is_esm = esm_stmt is not None and cjs_stmt is None

    if is_esm:
        chosen_stmt = esm_stmt or f"import {clean_mod} from '{clean_mod}';"
    else:
        chosen_stmt = cjs_stmt or f"const {clean_mod} = require('{clean_mod}');"

    # Check if exact statement text already appears
    if chosen_stmt in source:
        return []

    # 3. Determine insertion line
    lines = source.splitlines()
    insert_line = 1

    # Check for shebang on line 1
    if lines and lines[0].startswith("#!"):
        insert_line = 2

    # Check for 'use strict'
    for idx, line in enumerate(lines, 1):
        stripped = line.strip().strip(";")
        if stripped in ('"use strict"', "'use strict'"):
            insert_line = max(insert_line, idx + 1)
            break

    # Look for contiguous existing imports / requires near the top
    last_import_line = 0
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
            continue
        if stripped in ('"use strict";', "'use strict';", '"use strict"', "'use strict'"):
            continue
        if idx == 1 and line.startswith("#!"):
            continue
        if stripped.startswith("import ") or (
            ("require(" in stripped) and not stripped.startswith("function")
        ):
            last_import_line = idx
        else:
            break

    if last_import_line >= insert_line:
        insert_line = last_import_line + 1

    total_lines = len(lines)
    if insert_line > total_lines:
        insert_line = total_lines + 1

    edit_range = Range(
        start_line=insert_line,
        start_col=1,
        end_line=insert_line,
        end_col=1,
    )
    new_text = f"{chosen_stmt}\n"

    return [Edit(range=edit_range, new_text=new_text)]


# C to C++ header mapping
_C_TO_CPP_HEADERS: dict[str, str] = {
    "stdio.h": "cstdio",
    "stdlib.h": "cstdlib",
    "string.h": "cstring",
    "stddef.h": "cstddef",
    "stdint.h": "cstdint",
    "time.h": "ctime",
    "assert.h": "cassert",
    "ctype.h": "cctype",
    "math.h": "cmath",
    "limits.h": "climits",
    "errno.h": "cerrno",
    "float.h": "cfloat",
}
_CPP_TO_C_HEADERS: dict[str, str] = {v: k for k, v in _C_TO_CPP_HEADERS.items()}


def ensure_import_cpp(
    source: str,
    header_name: str,
    filename: str = "",
) -> list[Edit]:
    """Ensure a required C/C++ #include header is present in source code.

    Inserts after the last existing #include, or after '#pragma once' / include guard,
    avoiding duplicates. Uses <cstdio>-style headers in C++ files (.cpp, .cc, .cxx, .hpp)
    and <stdio.h>-style headers in C files (.c, .h).

    Args:
        source: C or C++ source code text.
        header_name: Header name (e.g. 'stdio.h', '<cstdio>', 'cstring', 'stdlib.h').
        filename: Optional filename to determine C vs C++ dialect.

    Returns:
        List of Edit instances (empty list if header is already included).
    """
    clean_hdr = header_name.strip().strip("<>\"'")

    # Determine if target is C++ vs C
    is_cpp = False
    if filename:
        lower_fn = filename.lower()
        if any(lower_fn.endswith(ext) for ext in (".cpp", ".cc", ".cxx", ".hpp")):
            is_cpp = True
        elif any(lower_fn.endswith(ext) for ext in (".c", ".h")):
            is_cpp = False
        else:
            is_cpp = bool(
                re.search(
                    r"\b(?:std::|namespace\b|cout\b|cin\b|template\b|<iostream>|<cstdio>)", source
                )
            )
    else:
        is_cpp = bool(
            re.search(
                r"\b(?:std::|namespace\b|cout\b|cin\b|template\b|<iostream>|<cstdio>)", source
            )
        )

    # Resolve header variants
    c_variant = _CPP_TO_C_HEADERS.get(clean_hdr, clean_hdr)
    cpp_variant = _C_TO_CPP_HEADERS.get(clean_hdr, clean_hdr)
    chosen_header = cpp_variant if is_cpp else c_variant

    # 1. Duplicate check: is any variant of this header already included?
    for h in {clean_hdr, c_variant, cpp_variant}:
        pat = rf"#\s*include\s*[<\"]{re.escape(h)}[>\"]"
        if re.search(pat, source):
            return []

    # 2. Find insertion position
    lines = source.splitlines()
    last_include_line = 0
    pragma_once_line = 0
    guard_define_line = 0

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.match(r"#\s*include\b", stripped):
            last_include_line = idx
        elif re.match(r"#\s*pragma\s+once\b", stripped):
            pragma_once_line = idx
        elif re.match(r"#\s*define\s+[A-Za-z0-9_]+", stripped):
            # Check if immediately preceded by #ifndef
            if idx > 1 and re.match(r"#\s*ifndef\s+[A-Za-z0-9_]+", lines[idx - 2].strip()):
                guard_define_line = idx

    if last_include_line > 0:
        insert_line = last_include_line + 1
    elif guard_define_line > 0:
        insert_line = guard_define_line + 1
    elif pragma_once_line > 0:
        insert_line = pragma_once_line + 1
    else:
        insert_line = 1

    total_lines = len(lines)
    if insert_line > total_lines:
        insert_line = total_lines + 1

    edit_range = Range(
        start_line=insert_line,
        start_col=1,
        end_line=insert_line,
        end_col=1,
    )
    new_text = f"#include <{chosen_header}>\n"
    return [Edit(range=edit_range, new_text=new_text)]
