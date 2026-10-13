"""Versioned, side-effect-free patch proposals for the v2 API."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from apsla.fixes.edits import apply_edits, unified_diff
from apsla.lexing.common import OffsetMap
from apsla.models import Edit


class PatchProposalV2(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_hash: str
    source_version: int = Field(ge=0)
    target_finding_id: str
    target_kind: Literal["finding", "diagnostic", "token"] = "finding"
    target_signature: str | None = None
    origin: Literal["rule", "ai"]
    edits: list[Edit]
    diff: str = ""
    rationale: str = ""
    expected_outcome: str = ""
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PatchTarget(BaseModel):
    kind: Literal["finding", "diagnostic", "token"]
    id: str = Field(min_length=1, max_length=256)


class PatchRequest(BaseModel):
    source: str = Field(max_length=512 * 1024)
    source_version: int = Field(ge=0)
    language: str = "python"
    filename: str = "<editor>"
    target: PatchTarget | None = None
    target_finding_id: str | None = None
    session_id: str = "default"
    remote_consent: bool = False
    origin: Literal["rule", "ai"] = "rule"

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_finding_target(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        target = data.get("target")
        if target is None and data.get("target_finding_id"):
            data["target"] = {"kind": "finding", "id": data["target_finding_id"]}
        elif isinstance(target, dict) and target.get("kind") == "finding":
            data.setdefault("target_finding_id", target.get("id"))
        if data.get("target") is None:
            raise ValueError("A fix target is required.")
        return data


class PatchActionRequest(BaseModel):
    source: str = Field(max_length=512 * 1024)
    source_version: int = Field(ge=0)
    language: str = "python"
    filename: str = "<editor>"
    session_id: str = "default"
    proposal: PatchProposalV2
    approved: bool = False


class UndoRequest(BaseModel):
    session_id: str = "default"


def source_sha256(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def validate_proposal(source: str, source_version: int, proposal: PatchProposalV2) -> str:
    """Validate identity, UTF-16 ranges, ordering, overlap, size and diff integrity."""
    if proposal.source_version != source_version or proposal.source_hash != source_sha256(source):
        raise ValueError("Proposal is stale: source version or hash does not match.")
    if not proposal.edits:
        raise ValueError("Proposal contains no edits.")
    if (
        len(proposal.edits) > 64
        or sum(len(e.new_text.encode("utf-8")) for e in proposal.edits) > 32768
    ):
        raise ValueError("Proposal exceeds edit count or replacement size limits.")
    offsets = OffsetMap(source)
    for edit in proposal.edits:
        for line, column in (
            (edit.range.start_line, edit.range.start_col),
            (edit.range.end_line, edit.range.end_col),
        ):
            position = offsets.pos_to_py(line, column)
            if offsets.py_to_pos(position) != (line, column):
                raise ValueError(
                    "Proposal range is outside the source or splits a UTF-16 code point."
                )
    try:
        patched = apply_edits(source, proposal.edits)
    except Exception as exc:
        raise ValueError(f"Proposal ranges are invalid or overlap: {exc}") from exc
    if patched == source:
        raise ValueError("Proposal does not change the source.")
    expected_diff = unified_diff(source, patched)
    if proposal.diff and proposal.diff != expected_diff:
        raise ValueError("Proposal diff does not match its declared edits.")
    return expected_diff


def make_proposal(
    *,
    source: str,
    source_version: int,
    target_finding_id: str,
    target_kind: Literal["finding", "diagnostic", "token"] = "finding",
    target_signature: str | None = None,
    edits: list[Edit],
    origin: Literal["rule", "ai"],
    rationale: str,
    expected_outcome: str = "",
    assumptions: list[str] | None = None,
    risks: list[str] | None = None,
) -> PatchProposalV2:
    patched = apply_edits(source, edits)
    proposal = PatchProposalV2(
        source_hash=source_sha256(source),
        source_version=source_version,
        target_finding_id=target_finding_id,
        target_kind=target_kind,
        target_signature=target_signature,
        origin=origin,
        edits=edits,
        diff=unified_diff(source, patched),
        rationale=rationale,
        expected_outcome=expected_outcome,
        assumptions=assumptions or [],
        risks=risks or [],
    )
    validate_proposal(source, source_version, proposal)
    return proposal
