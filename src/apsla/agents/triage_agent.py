"""Triage Agent for risk scoring and human-review triage (Phase 15).

STRICT INVARIANT:
The Triage Agent may NEVER delete, suppress, or downgrade a finding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apsla.agents.base import BaseAgent
from apsla.agents.guard import sanitize_code_snippet
from apsla.agents.schemas import AgentObservation

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


class TriageAgent(BaseAgent):
    """Responsible for ML vulnerability confidence scoring and human-review flagging."""

    def __init__(self) -> None:
        super().__init__(
            name="TriageAgent",
            stage="triage",
            goal=(
                "Evaluate finding confidence distributions, request deep taint for borderline "
                "findings (confidence 0.40 to 0.60), and mark items for human review without "
                "ever suppressing, deleting, or downgrading any finding."
            ),
            allowed_tools={"ml_score", "run_taint", "finish"},
            max_steps=3,
        )

    def observe(self, session: AnalysisSession) -> AgentObservation:
        borderline_findings = [
            f.id for f in session.findings if 0.40 <= getattr(f, "confidence", 0.5) <= 0.60
        ]
        facts = {
            "ml_scored": session.ml_scored,
            "total_findings": len(session.findings),
            "borderline_count": len(borderline_findings),
            "borderline_ids": borderline_findings[:5],
            "deep_taint_ran": session.deep_taint_ran,
        }

        # Context snippet from first borderline finding or first finding
        target_f = next((f for f in session.findings if f.id in borderline_findings), None)
        line_no = (
            target_f.range.start_line
            if target_f
            else (session.findings[0].range.start_line if session.findings else 1)
        )
        snippet = sanitize_code_snippet(session.source, line_no=line_no, max_lines=5)

        return AgentObservation(
            stage=self.stage,
            facts=facts,
            allowed_tools=sorted(list(self.allowed_tools)),
            context_snippet=snippet,
        )
