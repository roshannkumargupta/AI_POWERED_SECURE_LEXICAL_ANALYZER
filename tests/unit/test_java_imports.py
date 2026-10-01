"""Unit tests for Java import insertion utility."""

from apsla.fixes.edits import apply_edits
from apsla.fixes.imports import ensure_import_java


def test_insert_import_with_package():
    source = "package com.example.app;\n\npublic class Main {}\n"
    edits = ensure_import_java(source, "java.security.SecureRandom")
    res = apply_edits(source, edits) if edits else source
    expected = (
        "package com.example.app;\n\nimport java.security.SecureRandom;\n\npublic class Main {}\n"
    )
    assert res == expected


def test_insert_import_without_package():
    source = "public class Main {}\n"
    edits = ensure_import_java(source, "java.util.List")
    res = apply_edits(source, edits) if edits else source
    expected = "import java.util.List;\n\npublic class Main {}\n"
    assert res == expected


def test_insert_import_sorted_among_existing():
    source = (
        "package com.example;\n\n"
        "import java.io.File;\n"
        "import java.util.Map;\n\n"
        "public class App {}\n"
    )
    edits = ensure_import_java(source, "java.security.SecureRandom")
    res = apply_edits(source, edits) if edits else source
    assert "import java.io.File;\nimport java.security.SecureRandom;\nimport java.util.Map;" in res


def test_insert_import_duplicate_no_change():
    source = "package com.example;\n\nimport java.security.SecureRandom;\n\npublic class App {}\n"
    edits = ensure_import_java(source, "java.security.SecureRandom")
    res = apply_edits(source, edits) if edits else source
    assert res == source


def test_insert_import_wildcard_no_change():
    source = "package com.example;\n\nimport java.security.*;\n\npublic class App {}\n"
    edits = ensure_import_java(source, "java.security.SecureRandom")
    res = apply_edits(source, edits) if edits else source
    assert res == source
