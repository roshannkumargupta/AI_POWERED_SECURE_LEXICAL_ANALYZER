"""Parser Agent for syntactic structure analysis (Phase 15)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apsla.agents.base import BaseAgent
from apsla.agents.guard import sanitize_code_snippet
from apsla.agents.schemas import AgentObservation

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


class ParserAgent(BaseAgent):
    """Responsible for building StructTree with panic error recovery and quality scoring."""

    def __init__(self) -> None:
        super().__init__(
            name="ParserAgent",
            stage="syntax",
            goal=(
                "Parse source into structural AST (StructTree), execute panic-mode recovery on syntax breaks, "
                "and pass structure quality score to downstream analysis stages."
            ),
            allowed_tools={"parse_structure", "finish"},
            max_steps=3,
        )

    def observe(self, session: AnalysisSession) -> AgentObservation:
        facts = {
            "language": session.language,
            "has_struct_tree": session.struct_tree is not None,
            "parser_recovered": session.parser_recovered,
        }
        if session.struct_tree:
            facts["structure_quality"] = session.struct_tree.quality_score
            facts["errors_count"] = session.struct_tree.error_count
            facts["functions_count"] = len(session.struct_tree.functions)
            facts["classes_count"] = len(session.struct_tree.classes)
            facts["calls_count"] = len(session.struct_tree.calls)

        snippet = sanitize_code_snippet(session.source, line_no=1, max_lines=5)
        return AgentObservation(
            stage=self.stage,
            facts=facts,
            allowed_tools=sorted(self.allowed_tools),
            context_snippet=snippet,
        )
