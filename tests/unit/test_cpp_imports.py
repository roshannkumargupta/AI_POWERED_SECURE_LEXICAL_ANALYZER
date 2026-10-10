"""Tests for C/C++ header import insertion and deduplication."""

from __future__ import annotations

from apsla.fixes.imports import ensure_import_cpp


def test_insert_header_after_existing_include_c():
    source = "#include <stdlib.h>\n\nint main() { return 0; }\n"
    edits = ensure_import_cpp(source, "stdio.h", filename="test.c")
    assert len(edits) == 1
    assert edits[0].range.start_line == 2
    assert edits[0].new_text == "#include <stdio.h>\n"


def test_insert_header_cpp_dialect():
    source = "#include <iostream>\n\nint main() { return 0; }\n"
    edits = ensure_import_cpp(source, "stdio.h", filename="test.cpp")
    assert len(edits) == 1
    assert edits[0].range.start_line == 2
    assert edits[0].new_text == "#include <cstdio>\n"


def test_insert_header_deduplicate():
    source = "#include <cstdio>\n#include <iostream>\n\nint main() { return 0; }\n"
    edits = ensure_import_cpp(source, "stdio.h", filename="test.cpp")
    assert len(edits) == 0


def test_insert_header_after_pragma_once():
    source = "#pragma once\n\nvoid foo();\n"
    edits = ensure_import_cpp(source, "string.h", filename="foo.h")
    assert len(edits) == 1
    assert edits[0].range.start_line == 2
    assert edits[0].new_text == "#include <string.h>\n"


def test_insert_header_after_include_guard():
    source = "#ifndef FOO_H\n#define FOO_H\n\nvoid foo();\n#endif\n"
    edits = ensure_import_cpp(source, "stdio.h", filename="foo.h")
    assert len(edits) == 1
    assert edits[0].range.start_line == 3
    assert edits[0].new_text == "#include <stdio.h>\n"
