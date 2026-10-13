from apsla.fixes.edits import apply_edits
from apsla.fixes.generators import generate_rule_fix
from apsla.models import Range


def _fix(source: str, language: str, span: tuple[int, int], message: str, *, producer: str = "lexer") -> str:
    start, end = span
    range_ = Range(start_line=1, start_col=start + 1, end_line=1, end_col=end + 1)
    generated, reason = generate_rule_fix(
        source=source,
        language=language,
        range=range_,
        category="lexical",
        message=message,
        produced_by=producer,
        lexeme=source[start:end],
    )
    assert generated is not None, reason
    assert generated.edits
    return apply_edits(source, generated.edits)


def test_unterminated_string_and_block_comment_are_closed():
    assert _fix('print("bad', "python", (6, 10), "Unterminated string") == 'print("bad"'
    assert _fix("/* broken", "cpp", (0, 9), "Unterminated block comment") == "/* broken*/"
    assert _fix("char c = 'x", "cpp", (9, 11), "Unterminated character literal") == "char c = 'x'"
    assert _fix("const s = `text", "javascript", (10, 15), "Unterminated template") == "const s = `text`"
    assert _fix('auto s = R"(text', "cpp", (9, 16), "Unterminated raw string") == 'auto s = R"(text)"'


def test_invalid_unexpected_char_smart_quote_and_invisible_control():
    assert _fix("x = 1 §", "python", (6, 7), "Unexpected character") == "x = 1 "
    assert _fix("x = ‘a’", "python", (4, 5), "Invalid character") == "x = 'a’"
    assert _fix("x = 1\u202e", "python", (5, 6), "Invalid token") == "x = 1"


def test_invalid_escape_and_documented_safe_number_normalization():
    assert _fix('x = "\\q"', "python", (5, 7), "Invalid escape sequence") == 'x = "\\\\q"'
    assert _fix("x = 1__2", "python", (4, 8), "Malformed number") == "x = 1_2"


def test_parser_missing_delimiter_inserts_only_named_expected_token():
    fixed = _fix("int f() { return 1", "cpp", (18, 18), "Missing '}'", producer="tree-sitter-cpp")
    assert fixed.endswith("}")
    generated, reason = generate_rule_fix(
        source="int f() { return 1", language="cpp",
        range=Range(start_line=1, start_col=19, end_line=1, end_col=19),
        category="syntax", message="Unexpected input", produced_by="tree-sitter-cpp",
    )
    assert generated is None
    assert reason and "No automatic fix" in reason
