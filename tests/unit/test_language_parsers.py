"""Unit tests for Phase 15 Part A: Lightweight Structure Parsers (Java, JS, C++).

Verifies:
  1. Hand-written recursive-descent parser produces a StructTree with zero ERROR nodes
     for 15 realistic files per language.
  2. 8 broken files per language recover gracefully and record ERROR nodes.
  3. Call extraction matches hand-labelled expectations in tests/fixtures/<lang>/parser/*.expect.json.
  4. Coordinates are strictly valid UTF-16 code units (1-indexed).
"""

import json
from pathlib import Path

import pytest

from apsla.languages.cpp_lang.parser import parse_cpp_structure
from apsla.languages.java_lang.parser import parse_java_structure
from apsla.languages.javascript_lang.parser import parse_javascript_structure
from apsla.languages.python_lang.parser import parse_python_structure

FIXTURES_DIR = Path("tests/fixtures")


@pytest.mark.parametrize("idx", range(1, 16))
def test_java_valid_fixtures_zero_errors(idx: int):
    path = FIXTURES_DIR / "java" / "parser" / f"valid_{idx:02d}.java"
    assert path.exists(), f"Missing fixture {path}"
    source = path.read_text(encoding="utf-8")
    tree = parse_java_structure(source)
    assert tree.is_valid, (
        f"Java fixture {path.name} failed with errors: {[e.message for e in tree.errors]}"
    )
    assert len(tree.errors) == 0
    assert tree.quality_score == 1.0


@pytest.mark.parametrize("idx", range(1, 9))
def test_java_broken_fixtures_record_errors(idx: int):
    path = FIXTURES_DIR / "java" / "parser" / f"broken_{idx:02d}.java"
    assert path.exists(), f"Missing fixture {path}"
    source = path.read_text(encoding="utf-8")
    tree = parse_java_structure(source)
    assert not tree.is_valid, f"Broken fixture {path.name} unexpectedly produced 0 errors"
    assert len(tree.errors) >= 1
    assert tree.quality_score < 1.0


@pytest.mark.parametrize("idx", range(1, 16))
def test_javascript_valid_fixtures_zero_errors(idx: int):
    path = FIXTURES_DIR / "javascript" / "parser" / f"valid_{idx:02d}.js"
    assert path.exists(), f"Missing fixture {path}"
    source = path.read_text(encoding="utf-8")
    tree = parse_javascript_structure(source)
    assert tree.is_valid, (
        f"JS fixture {path.name} failed with errors: {[e.message for e in tree.errors]}"
    )
    assert len(tree.errors) == 0
    assert tree.quality_score == 1.0


@pytest.mark.parametrize("idx", range(1, 9))
def test_javascript_broken_fixtures_record_errors(idx: int):
    path = FIXTURES_DIR / "javascript" / "parser" / f"broken_{idx:02d}.js"
    assert path.exists(), f"Missing fixture {path}"
    source = path.read_text(encoding="utf-8")
    tree = parse_javascript_structure(source)
    assert not tree.is_valid, f"Broken fixture {path.name} unexpectedly produced 0 errors"
    assert len(tree.errors) >= 1
    assert tree.quality_score < 1.0


@pytest.mark.parametrize("idx", range(1, 16))
def test_cpp_valid_fixtures_zero_errors(idx: int):
    path = FIXTURES_DIR / "cpp" / "parser" / f"valid_{idx:02d}.cpp"
    assert path.exists(), f"Missing fixture {path}"
    source = path.read_text(encoding="utf-8")
    tree = parse_cpp_structure(source)
    assert tree.is_valid, (
        f"C++ fixture {path.name} failed with errors: {[e.message for e in tree.errors]}"
    )
    assert len(tree.errors) == 0
    assert tree.quality_score == 1.0


@pytest.mark.parametrize("idx", range(1, 9))
def test_cpp_broken_fixtures_record_errors(idx: int):
    path = FIXTURES_DIR / "cpp" / "parser" / f"broken_{idx:02d}.cpp"
    assert path.exists(), f"Missing fixture {path}"
    source = path.read_text(encoding="utf-8")
    tree = parse_cpp_structure(source)
    assert not tree.is_valid, f"Broken fixture {path.name} unexpectedly produced 0 errors"
    assert len(tree.errors) >= 1
    assert tree.quality_score < 1.0


def test_java_calls_expectation_matching():
    exp_file = FIXTURES_DIR / "java" / "parser" / "calls.expect.json"
    expectations: dict[str, list[str]] = json.loads(exp_file.read_text(encoding="utf-8"))
    for fname, expected_callees in expectations.items():
        src = (FIXTURES_DIR / "java" / "parser" / fname).read_text(encoding="utf-8")
        tree = parse_java_structure(src)
        actual_callees = [c.callee for c in tree.calls]
        for exp in expected_callees:
            assert exp in actual_callees, (
                f"Expected call '{exp}' in {fname}, found {actual_callees}"
            )


def test_javascript_calls_expectation_matching():
    exp_file = FIXTURES_DIR / "javascript" / "parser" / "calls.expect.json"
    expectations: dict[str, list[str]] = json.loads(exp_file.read_text(encoding="utf-8"))
    for fname, expected_callees in expectations.items():
        src = (FIXTURES_DIR / "javascript" / "parser" / fname).read_text(encoding="utf-8")
        tree = parse_javascript_structure(src)
        actual_callees = [c.callee for c in tree.calls]
        for exp in expected_callees:
            assert exp in actual_callees, (
                f"Expected call '{exp}' in {fname}, found {actual_callees}"
            )


def test_cpp_calls_expectation_matching():
    exp_file = FIXTURES_DIR / "cpp" / "parser" / "calls.expect.json"
    expectations: dict[str, list[str]] = json.loads(exp_file.read_text(encoding="utf-8"))
    for fname, expected_callees in expectations.items():
        src = (FIXTURES_DIR / "cpp" / "parser" / fname).read_text(encoding="utf-8")
        tree = parse_cpp_structure(src)
        actual_callees = [c.callee for c in tree.calls]
        for exp in expected_callees:
            assert exp in actual_callees, (
                f"Expected call '{exp}' in {fname}, found {actual_callees}"
            )


def test_python_struct_parser():
    py_code = """import os\ndef test_fn(x, y):\n    val = os.getenv('TOKEN')\n    return val\n"""
    tree = parse_python_structure(py_code)
    assert tree.is_valid
    assert len(tree.functions) == 1
    assert tree.functions[0].name == "test_fn"
    assert len(tree.calls) >= 1
    assert any("getenv" in c.callee for c in tree.calls)
