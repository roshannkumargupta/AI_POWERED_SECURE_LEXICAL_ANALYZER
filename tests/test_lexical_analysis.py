import pytest
from apsla.languages import registry
from apsla.models_v2 import adapt_analysis_result, TokenV2
from apsla.scoring import create_analysis_summary
from apsla.models import AnalysisResult, EngineMetadata

def _analyze_lexical_only(source: str, language: str) -> list[TokenV2]:
    plugin = registry.get(language)
    assert plugin is not None, f"Plugin for {language} must be registered"
    raw_tokens = plugin.lex(source)
    
    legacy_result = AnalysisResult(
        filename="test_file",
        findings=[],
        tokens=[],
        summary=create_analysis_summary(findings=[], tokens=[]),
        language=language,
        engine=EngineMetadata(elapsed_ms=1.0),
    )
    v2_result = adapt_analysis_result(
        source,
        legacy_result,
        source_version=1,
        plugin=plugin,
        include_tokens=True,
        stages=["lexical"],
    )
    return v2_result.tokens

def test_cpp_lexical_tokens():
    cpp_code = """#include <iostream>
int main() {
    // line comment
    int count = 42;
    double ratio = 3.14;
    const char* msg = "hello world";
    count += 1;
    return 0;
}
"""
    tokens = _analyze_lexical_only(cpp_code, "cpp")
    assert len(tokens) > 0

    types = {t.token_type for t in tokens}
    categories = {t.category for t in tokens}

    # Verify language-appropriate categories
    assert "KEYWORD" in types
    assert "IDENTIFIER" in types
    assert "DELIMITER" in types
    assert "OPERATOR" in types
    assert "NUMBER_LITERAL" in types
    assert "STRING_LITERAL" in types
    assert "PREPROCESSOR" in types

    assert "Keyword" in categories
    assert "Identifier" in categories
    assert "Delimiter" in categories
    assert "Operator" in categories
    assert "Literal" in categories

    # All standard tokens should be valid
    for t in tokens:
        assert t.lexical_status == "valid"
        assert t.start_line >= 1
        assert t.start_column >= 1
        assert t.end_line >= t.start_line

def test_python_lexical_tokens():
    py_code = """# Python sample
def calculate_sum(a: int, b: float = 1.5) -> float:
    \"\"\"Docstring\"\"\"
    total = a + b
    name = 'SecureLex'
    if total > 10:
        return total * 2
    return total
"""
    tokens = _analyze_lexical_only(py_code, "python")
    assert len(tokens) > 0

    types = {t.token_type for t in tokens}
    assert "KEYWORD" in types
    assert "IDENTIFIER" in types
    assert "DELIMITER" in types or "OPERATOR" in types

    # Check that keywords like def, if, return are recognized
    lexemes = [t.lexeme for t in tokens]
    assert "def" in lexemes
    assert "if" in lexemes
    assert "return" in lexemes

def test_java_lexical_tokens():
    java_code = """package com.securelex;
public class Runner {
    /* multiline comment */
    public static void main(String[] args) {
        int x = 100;
        String title = "Java17";
        boolean flag = true;
    }
}
"""
    tokens = _analyze_lexical_only(java_code, "java")
    assert len(tokens) > 0

    types = {t.token_type for t in tokens}
    assert "KEYWORD" in types
    assert "IDENTIFIER" in types
    assert "DELIMITER" in types

    lexemes = [t.lexeme for t in tokens]
    assert "public" in lexemes
    assert "class" in lexemes
    assert "Runner" in lexemes
    assert "String" in lexemes

def test_javascript_lexical_tokens():
    js_code = """const compute = (val) => {
    // Single line
    let result = val * 2.5;
    const greeting = `Value: ${result}`;
    return result >= 10 ? true : false;
};
"""
    tokens = _analyze_lexical_only(js_code, "javascript")
    assert len(tokens) > 0

    types = {t.token_type for t in tokens}
    assert "KEYWORD" in types
    assert "IDENTIFIER" in types
    assert "OPERATOR" in types

    lexemes = [t.lexeme for t in tokens]
    assert "const" in lexemes
    assert "let" in lexemes
    assert "return" in lexemes

def test_invalid_tokens_and_unicode_handling():
    # C++ code containing an invalid character and zero-width non-break space
    cpp_with_invalid = "int x = 10 @ 5;\nint y = 0 \uFEFF+ 1;\n"
    plugin = registry.get("cpp")
    assert plugin is not None

    legacy_result = AnalysisResult(
        filename="test_file",
        findings=[],
        tokens=[],
        summary=create_analysis_summary(findings=[], tokens=[]),
        language="cpp",
        engine=EngineMetadata(elapsed_ms=1.0),
    )
    v2_result = adapt_analysis_result(
        cpp_with_invalid,
        legacy_result,
        source_version=1,
        plugin=plugin,
        include_tokens=True,
        stages=["lexical"],
    )

    # Invalid token @ should be marked invalid
    invalid_tokens = [t for t in v2_result.tokens if t.lexical_status == "invalid" or t.token_type == "INVALID_TOKEN"]
    assert len(invalid_tokens) >= 1
    assert any("@" in t.lexeme for t in invalid_tokens)

def test_empty_source_and_zero_tokens():
    empty_code = ""
    tokens = _analyze_lexical_only(empty_code, "cpp")
    assert len(tokens) == 0

    whitespace_code = "   \n\t\n   "
    tokens_ws = _analyze_lexical_only(whitespace_code, "cpp")
    assert len(tokens_ws) == 0

def test_source_offsets_and_multiline_positions():
    multiline_code = "int a = 1;\nint b = 2;\nint c = a + b;\n"
    tokens = _analyze_lexical_only(multiline_code, "cpp")

    for t in tokens:
        # Offsets must be strictly non-negative and properly ordered
        assert t.start_offset >= 0
        assert t.end_offset >= t.start_offset
        assert t.start_line >= 1
        assert t.end_line >= t.start_line
        assert t.start_column >= 1
        assert t.end_column >= t.start_column
        # Slice should match the lexeme
        assert multiline_code[t.start_offset:t.end_offset] == t.lexeme
