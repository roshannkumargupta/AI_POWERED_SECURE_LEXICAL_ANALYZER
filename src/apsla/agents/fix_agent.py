"""Fix Agent for remediation candidate retrieval and prioritization (Phase 15)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apsla.agents.base import BaseAgent
from apsla.agents.guard import sanitize_code_snippet
from apsla.agents.schemas import AgentObservation, PatchProposal

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


class FixAgent(BaseAgent):
    """Responsible for retrieving, ranking, and proposing automated fix candidates."""

    def __init__(self) -> None:
        super().__init__(
            name="FixAgent",
            stage="fix",
            goal=(
                "List automated fix candidates, rank safe > review > manual with minimal edits first, "
                "and propose LLM-assisted remediation edit if no deterministic template exists."
            ),
            allowed_tools={"list_fix_candidates", "finish"},
            max_steps=4,
        )

    def observe(self, session: AnalysisSession) -> AgentObservation:
        unfixed_ids = [f.id for f in session.findings if f.id not in session.fix_candidates]
        total_candidates = sum(len(c) for c in session.fix_candidates.values())

        facts = {
            "findings_count": len(session.findings),
            "unfixed_finding_ids": unfixed_ids[:5],
            "total_candidates": total_candidates,
            "has_candidates": total_candidates > 0,
        }

        # Target finding context
        target_f = next((f for f in session.findings if f.id in unfixed_ids), None)
        line_no = target_f.range.start_line if target_f else 1
        snippet = sanitize_code_snippet(session.source, line_no=line_no, max_lines=5)

        return AgentObservation(
            stage=self.stage,
            facts=facts,
            allowed_tools=sorted(self.allowed_tools),
            context_snippet=snippet,
        )

    @staticmethod
    def proposal_from_candidate(
        finding_id: str,
        candidate: dict[str, object],
        *,
        rationale: str = "Deterministic fix candidate; review before applying.",
        assumptions: list[str] | None = None,
        known_risks: list[str] | None = None,
    ) -> PatchProposal:
        """Adapt an existing fix candidate to a structured, non-applied draft."""
        raw_edits = candidate.get("edits", [])
        edits = (
            [item for item in raw_edits if isinstance(item, dict)]
            if isinstance(raw_edits, list)
            else []
        )
        raw_diff = candidate.get("diff", "")
        return PatchProposal(
            target_finding_id=finding_id,
            edits=edits,
            diff=raw_diff if isinstance(raw_diff, str) else "",
            rationale=rationale,
            expected_outcome=str(candidate.get("expected_outcome", candidate.get("title", ""))),
            assumptions=list(assumptions or []),
            known_risks=list(known_risks or []),
        )
