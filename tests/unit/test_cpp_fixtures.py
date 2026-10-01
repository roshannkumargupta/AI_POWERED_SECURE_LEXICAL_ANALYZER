"""Test runner executing all C/C++ fixtures and verifying exact (rule_id, line) matches."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apsla.pipeline import Analyzer

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "cpp"


def get_all_cpp_fixtures() -> list[tuple[Path, list[dict[str, str | int]]]]:
    """Collect all C/C++ fixture paths along with their expected findings."""
    expect_path = FIXTURES_ROOT / "expect.json"
    if not expect_path.exists():
        return []

    data = json.loads(expect_path.read_text(encoding="utf-8"))
    fixtures: list[tuple[Path, list[dict[str, str | int]]]] = []

    for cat in ("vulnerable", "safe", "adversarial"):
        cat_dir = FIXTURES_ROOT / cat
        if not cat_dir.exists():
            continue

        cat_expect = data.get(cat, {})
        for cf in sorted(cat_dir.glob("*.*")):
            if cf.suffix not in (".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"):
                continue
            expected = cat_expect.get(cf.name, [])
            fixtures.append((cf, expected))

    return fixtures


ALL_CPP_FIXTURES = get_all_cpp_fixtures()


@pytest.mark.parametrize(
    "cpp_file,expected", ALL_CPP_FIXTURES, ids=[f[0].name for f in ALL_CPP_FIXTURES]
)
def test_cpp_fixture(cpp_file: Path, expected: list[dict[str, str | int]]) -> None:
    """Verify that analyzing a C/C++ fixture produces the exact expected (rule_id, line) findings."""
    source = cpp_file.read_text(encoding="utf-8")
    analyzer = Analyzer()
    result = analyzer.analyze(
        source=source, language="cpp", filename=cpp_file.name, options={"ml": False}
    )

    actual_pairs = {(f.rule_id, f.range.start_line) for f in result.findings if not f.suppressed}
    expected_pairs = {(str(e["rule_id"]), int(e["line"])) for e in expected}

    assert actual_pairs == expected_pairs, (
        f"Fixture {cpp_file.name} mismatch!\n"
        f"Expected: {sorted(expected_pairs)}\n"
        f"Actual:   {sorted(actual_pairs)}\n"
        f"Findings: {result.findings}"
    )
