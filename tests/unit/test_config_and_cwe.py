"""Tests for config constants and CWE mappings."""

from __future__ import annotations

from apsla.config import (
    FILE_SIZE_LIMIT_BYTES,
    FUSION_WEIGHT_ML,
    FUSION_WEIGHT_RULE,
    HEALTH_SCORE_BASE,
    ML_ONLY_CAP,
    ML_WINDOW_SIZE,
    RANDOM_SEED,
    SEVERITY_CAPS,
    SEVERITY_WEIGHTS,
    TAINT_CONFIRMATION_BONUS,
    TIMEOUT_ANALYSIS_SECONDS,
    TIMEOUT_ML_SECONDS,
    TIMEOUT_TAINT_SECONDS,
)
from apsla.cwe import (
    HUMAN_REVIEW_DISCLAIMER,
    RULE_CATEGORY_TO_CWE,
    get_cwe_for_category,
)
from apsla.models import Severity


def test_config_constants_match_specification():
    """Verify all constant values defined in PROJECT_SPEC section D and E."""
    assert SEVERITY_WEIGHTS[Severity.CRITICAL] == 25
    assert SEVERITY_WEIGHTS[Severity.HIGH] == 12
    assert SEVERITY_WEIGHTS[Severity.MEDIUM] == 5
    assert SEVERITY_WEIGHTS[Severity.LOW] == 2
    assert SEVERITY_WEIGHTS[Severity.INFO] == 0

    assert SEVERITY_CAPS[Severity.CRITICAL] == 4
    assert SEVERITY_CAPS[Severity.HIGH] == 6
    assert SEVERITY_CAPS[Severity.MEDIUM] == 8
    assert SEVERITY_CAPS[Severity.LOW] == 10

    assert HEALTH_SCORE_BASE == 100
    assert FUSION_WEIGHT_RULE == 0.7
    assert FUSION_WEIGHT_ML == 0.3
    assert TAINT_CONFIRMATION_BONUS == 0.15
    assert ML_ONLY_CAP == 10
    assert ML_WINDOW_SIZE == 9
    assert RANDOM_SEED == 42
    assert FILE_SIZE_LIMIT_BYTES == 512 * 1024

    assert TIMEOUT_ANALYSIS_SECONDS == 30.0
    assert TIMEOUT_TAINT_SECONDS == 10.0
    assert TIMEOUT_ML_SECONDS == 5.0


def test_cwe_mappings():
    """Verify CWE mappings for every security vulnerability category."""
    expected_categories = [
        ("COMMAND_INJECTION", "CWE-78"),
        ("SQL_INJECTION", "CWE-89"),
        ("XSS", "CWE-79"),
        ("CODE_INJECTION", "CWE-94"),
        ("EVAL_INJECTION", "CWE-95"),
        ("DESERIALIZATION", "CWE-502"),
        ("WEAK_CRYPTO", "CWE-327"),
        ("HARDCODED_SECRET", "CWE-798"),
        ("PATH_TRAVERSAL", "CWE-22"),
        ("SSRF", "CWE-918"),
        ("BUFFER_OVERFLOW", "CWE-120"),
        ("OUT_OF_BOUNDS_WRITE", "CWE-787"),
        ("FORMAT_STRING", "CWE-134"),
        ("XXE", "CWE-611"),
        ("CONFUSABLE", "CWE-1007"),
        ("IMPROPER_ENCODING", "CWE-116"),
        ("MALICIOUS_CODE", "CWE-506"),
    ]

    for cat, cwe in expected_categories:
        assert cat in RULE_CATEGORY_TO_CWE, f"Missing category {cat}"
        assert cwe in RULE_CATEGORY_TO_CWE[cat], f"Expected {cwe} in {cat}"
        assert cwe in get_cwe_for_category(cat)


def test_cwe_human_review_disclaimer():
    """Verify the presence of mandatory human double-check disclaimer."""
    assert "human" in HUMAN_REVIEW_DISCLAIMER.lower()
    assert (
        "double-check" in HUMAN_REVIEW_DISCLAIMER.lower()
        or "verify" in HUMAN_REVIEW_DISCLAIMER.lower()
    )
