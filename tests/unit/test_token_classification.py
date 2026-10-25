from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import TypeAdapter

from apsla.languages import registry
from apsla.lexing.common import OffsetMap
from apsla.lexing.diagnostics_v2 import unicode_lexical_diagnostics
from apsla.models_v2 import TokenV2, token_type_for
from apsla.server.app import _stage_only, app
from apsla.server.schemas import AnalyzeRequest

LANGUAGE_SAMPLES = {
    "python": 'x = f"hi {name}"  # comment\n',
    "java": 'class X { String s = "ok"; }\n',
    "cpp": '#include <x>\nint main(){ return 0; }\n',
    "javascript": 'const x = `hello ${name}`;\n',
}


def _run_sync_coroutine(coroutine):
    """Run the lexical route's no-await path without opening OS event-loop sockets."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("Expected the lexical stage path to complete without suspension")


def test_raw_tokens_and_trivia_rebuild_each_language_source() -> None:
    for language, source in LANGUAGE_SAMPLES.items():
        tokens = registry.get(language).lex(source)
        assert "".join(token.text for token in tokens) == source
        assert all(token.start <= token.end for token in tokens)


def test_lexical_endpoint_schema_exposes_tokens() -> None:
    schema = app.openapi()
    response_schema = schema["components"]["schemas"]["StageAnalysisResponse"]["properties"]
    assert "tokens" in response_schema
    assert "lexical_summary" in response_schema
    assert "/api/analyze/lexical" in schema["paths"]


def test_lexical_endpoint_returns_visible_tokens_for_all_languages() -> None:
    for language, source in LANGUAGE_SAMPLES.items():
        result = _run_sync_coroutine(
            _stage_only(AnalyzeRequest(source=source, language=language, source_version=4), "lexical")
        )
        assert result.tokens
        assert result.language == language
        assert sum(result.lexical_summary["status"].values()) == len(result.tokens)


def test_lexical_endpoint_positions_and_parser_independence() -> None:
    result = _run_sync_coroutine(
        _stage_only(AnalyzeRequest(source="int x = ;\r\n", language="cpp", source_version=5), "lexical")
    )
    assert all(token.lexical_status == "valid" for token in result.tokens)
    unicode_result = _run_sync_coroutine(
        _stage_only(AnalyzeRequest(source='x = "😀"\r\n', language="python", source_version=6), "lexical")
    )
    string_token = next(token for token in unicode_result.tokens if "😀" in token.lexeme)
    assert string_token.end_offset - string_token.start_offset == len(string_token.lexeme.encode("utf-16-le")) // 2
    assert string_token.end_offset_codepoint - string_token.start_offset_codepoint == len(string_token.lexeme)
    bidi_result = _run_sync_coroutine(
        _stage_only(AnalyzeRequest(source='x = "\u202e"', language="python", source_version=7), "lexical")
    )
    assert bidi_result.diagnostics
    assert all(token.lexical_status == "valid" for token in bidi_result.tokens)


def test_v2_token_schema_round_trip() -> None:
    value = TokenV2(
        id="tok-1", language="python", lexeme="name", token_type="IDENTIFIER",
        category="Identifier", start_offset=0, end_offset=4,
        start_offset_codepoint=0, end_offset_codepoint=4, start_line=1,
        start_column=1, end_line=1, end_column=5, lexical_status="valid",
    )
    assert TypeAdapter(TokenV2).validate_python(value.model_dump()) == value


def test_cpp_default_example_tokens_match_hand_reviewed_fixture() -> None:
    fixture = json.loads(Path("tests/fixtures/cpp/lexical/default_example.tokens.json").read_text())
    raw = registry.get("cpp").lex(fixture["source"])
    actual = []
    for token in raw:
        mapped = token_type_for("cpp", token.kind, token.text)
        if mapped is None:
            continue
        actual.append(
            {
                "lexeme": token.text,
                "token_type": mapped[0],
                "category": mapped[1],
                "start_line": token.line,
                "start_column": token.col,
                "end_line": token.end_line,
                "end_column": token.end_col,
            }
        )
    assert actual == fixture["tokens"]
    assert len(actual) == fixture["token_count"]
    assert fixture["token_count"] != 22


def test_syntax_error_does_not_change_lexically_valid_tokens() -> None:
    source = "int x = ;\n"
    raw_tokens = registry.get("cpp").lex(source)
    visible = [token for token in raw_tokens if token_type_for("cpp", token.kind, token.text)]
    assert visible
    assert all(token.kind != "ERROR" for token in visible)


def test_utf16_and_codepoint_position_mapping_with_crlf_and_emoji() -> None:
    source = "😀\r\nx"
    offsets = OffsetMap(source)
    assert offsets.py_to_utf16(3) == 4
    assert offsets.py_to_pos(3) == (2, 1)
    assert offsets.utf16_to_py(4) == 3


def test_public_mapping_keeps_delimiters_and_literals_distinct() -> None:
    assert token_type_for("java", "PUNCTUATION", ";") == ("DELIMITER", "Delimiter")
    assert token_type_for("cpp", "STRING", "'x'") == ("CHAR_LITERAL", "Literal")
    assert token_type_for("javascript", "TEMPLATE", "`abc`") == ("TEMPLATE_LITERAL", "Literal")


def test_unicode_diagnostic_preserves_raw_codepoint_and_character_name() -> None:
    items = unicode_lexical_diagnostics("x\u202e", "python", "analysis-x")
    assert any("U+202E" in evidence for item in items for evidence in item.related_evidence)
    assert any("RIGHT-TO-LEFT OVERRIDE" in evidence for item in items for evidence in item.related_evidence)


@settings(max_examples=150, deadline=None)
@given(st.sampled_from(list(LANGUAGE_SAMPLES)), st.text(max_size=180))
def test_property_lexing_never_raises_and_stream_rebuilds(language: str, source: str) -> None:
    tokens = registry.get(language).lex(source)
    assert "".join(token.text for token in tokens) == source
