import json
import re
from pathlib import Path

from apsla.languages.cpp_lang.lexer import CppLexer
from apsla.models_v2 import token_type_for


FIXTURE = Path(__file__).parents[1] / "fixtures" / "ui-p3" / "default_cpp_tokens.json"
PROTOTYPE = Path(__file__).parents[2] / "web" / "ui-reference" / "prototype.html"


def test_default_cpp_example_token_count_matches_hand_verified_fixture():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    prototype = PROTOTYPE.read_text(encoding="utf-8")
    token_ids = set(re.findall(r'data-token-id="(tok-\d+)"', prototype))
    mapped_tokens = [
        token
        for token in CppLexer(fixture["source"]).tokenize()
        if token_type_for("cpp", token.kind, token.text) is not None
    ]
    assert len(token_ids) == fixture["prototype_token_span_count_hand_count"]
    assert fixture["prototype_claimed_token_count"] == 22
    assert fixture["cpp_v2_non_trivia_token_count_hand_verified"] == 35
    assert len(mapped_tokens) == fixture["cpp_v2_non_trivia_token_count_hand_verified"]
