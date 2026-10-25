"""Semantic Agent for rule matching and data-flow taint propagation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apsla.agents.base import BaseAgent
from apsla.agents.guard import sanitize_code_snippet
from apsla.agents.schemas import AgentObservation

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


class SemanticAgent(BaseAgent):
    """Responsible for static rule evaluation and targeted deep taint propagation."""

    def __init__(self) -> None:
        super().__init__(
            name="SemanticAgent",
            stage="semantic",
            goal=(
                "Execute deterministic rule matcher followed by standard data-flow taint propagation. "
                "Trigger targeted deep taint only when reaching unresolved calls or incomplete paths."
            ),
            allowed_tools={"run_rules", "run_taint", "finish"},
            max_steps=4,
        )

    def observe(self, session: AnalysisSession) -> AgentObservation:
        facts = {
            "rules_ran": session.rules_ran,
            "taint_ran": session.taint_ran,
            "deep_taint_ran": session.deep_taint_ran,
            "findings_count": len(session.findings),
            "taint_flows_count": len(session.taint_flows),
            "unresolved_sinks": session.unresolved_sinks,
        }

        # Context snippet from first finding if available
        first_line = session.findings[0].range.start_line if session.findings else 1
        snippet = sanitize_code_snippet(session.source, line_no=first_line, max_lines=5)

        return AgentObservation(
            stage=self.stage,
            facts=facts,
            allowed_tools=sorted(self.allowed_tools),
            context_snippet=snippet,
        )
