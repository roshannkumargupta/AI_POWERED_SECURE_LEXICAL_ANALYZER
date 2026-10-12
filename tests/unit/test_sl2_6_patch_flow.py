from __future__ import annotations

import pytest

from apsla.fixes.independent_verifier import verify_independently
from apsla.fixes.patch_v2 import make_proposal, source_sha256, validate_proposal
from apsla.models import Edit, Range


def test_proposal_binds_hash_version_and_diff_to_edits() -> None:
    source = "value = 1\n"
    edit = Edit(range=Range(start_line=1, start_col=9, end_line=1, end_col=10), new_text="2")
    proposal = make_proposal(
        source=source,
        source_version=3,
        target_finding_id="f-1",
        edits=[edit],
        origin="rule",
        rationale="Replace literal.",
    )
    assert proposal.source_hash == source_sha256(source)
    assert proposal.source_version == 3
    assert proposal.diff
    with pytest.raises(ValueError, match="stale"):
        validate_proposal(source, 4, proposal)
    with pytest.raises(ValueError, match="stale"):
        validate_proposal(source + "# changed\n", 3, proposal)


def test_malformed_and_overlapping_ranges_are_rejected() -> None:
    source = "abcdef\n"
    bad = Edit(range=Range(start_line=2, start_col=1, end_line=2, end_col=2), new_text="x")
    with pytest.raises(ValueError, match=r"outside the source|invalid or overlap"):
        make_proposal(
            source=source,
            source_version=0,
            target_finding_id="x",
            edits=[bad],
            origin="rule",
            rationale="bad range",
        )
    edits = [
        Edit(range=Range(start_line=1, start_col=1, end_line=1, end_col=4), new_text="x"),
        Edit(range=Range(start_line=1, start_col=3, end_line=1, end_col=5), new_text="y"),
    ]
    with pytest.raises(ValueError, match="Overlapping edits"):
        make_proposal(
            source=source,
            source_version=0,
            target_finding_id="x",
            edits=edits,
            origin="rule",
            rationale="overlap",
        )


def test_verifier_ignores_proposal_success_claim_and_measures_syntax() -> None:
    source = "value = 1\n"
    edit = Edit(range=Range(start_line=1, start_col=9, end_line=1, end_col=10), new_text="(")
    proposal = make_proposal(
        source=source,
        source_version=0,
        target_finding_id="absent",
        edits=[edit],
        origin="ai",
        rationale="claims success",
        expected_outcome="Verified for specified checks",
    )
    result = verify_independently(source, "python", "example.py", proposal, 0)
    assert result["syntax"]["passed"] is False
    assert result["outcome"] == "Verification failed"
    assert result["tests_status"] == "tests unavailable"
    assert result["patched_source"] == "value = (\n"


def test_invalid_proposal_is_rejected_before_source_changes() -> None:
    source = "x = 1\n"
    edit = Edit(range=Range(start_line=1, start_col=1, end_line=1, end_col=2), new_text="y")
    proposal = make_proposal(
        source=source,
        source_version=9,
        target_finding_id="f",
        edits=[edit],
        origin="rule",
        rationale="rename",
    )
    with pytest.raises(ValueError, match="stale"):
        verify_independently(source, "python", "x.py", proposal, 10)
    assert source == "x = 1\n"
