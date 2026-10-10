"""Unit tests for C/C++ syntax checking and structural validation."""

from __future__ import annotations

from apsla.languages.registry import get_plugin


def test_valid_cpp_syntax():
    plugin = get_plugin("cpp")
    source = (
        "#include <iostream>\n"
        "int main() {\n"
        '    std::cout << "Hello, world!" << std::endl;\n'
        "    return 0;\n"
        "}\n"
    )
    ok, err = plugin.syntax_check(source)
    assert ok is True
    assert err is None


def test_unmatched_closing_brace():
    plugin = get_plugin("cpp")
    source = "int main() { return 0; }}"
    ok, err = plugin.syntax_check(source)
    assert ok is False
    assert "Unmatched closing delimiter" in (err or "")


def test_unclosed_opening_paren():
    plugin = get_plugin("cpp")
    source = "int main( { return 0; }"
    ok, err = plugin.syntax_check(source)
    assert ok is False
    assert "Mismatched delimiter" in (err or "") or "Unclosed delimiter" in (err or "")


def test_unmatched_preprocessor_if():
    plugin = get_plugin("cpp")
    source = "#ifdef DEBUG\nint x = 1;\n// Missing #endif\n"
    ok, err = plugin.syntax_check(source)
    assert ok is False
    assert "preprocessor" in (err or "").lower()


def test_balanced_preprocessor_conditionals():
    plugin = get_plugin("cpp")
    source = (
        "#ifndef HEADER_H\n"
        "#define HEADER_H\n"
        "#ifdef __cplusplus\n"
        'extern "C" {\n'
        "#endif\n"
        "void func();\n"
        "#ifdef __cplusplus\n"
        "}\n"
        "#endif\n"
        "#endif\n"
    )
    ok, err = plugin.syntax_check(source)
    assert ok is True
    assert err is None
