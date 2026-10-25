"""Verifier Agent for automated fix validation and regression testing.

STRICT INVARIANT:
ONLY the verify_fix tool can set verified=true; no agent or model output can.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apsla.agents.base import BaseAgent
from apsla.agents.guard import sanitize_code_snippet
from apsla.agents.schemas import AgentObservation

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


class VerifierAgent(BaseAgent):
    """Responsible for sandboxed fix application, syntax verification, and regression scanning."""

    def __init__(self) -> None:
        super().__init__(
            name="VerifierAgent",
            stage="verify",
            goal=(
                "Apply fix candidates to isolated in-memory copies, verify syntax and security "
                "integrity via verify_fix, and rescan copies for regressions across up to 3 attempts."
            ),
            allowed_tools={"apply_fix_to_copy", "verify_fix", "rescan_copy", "finish"},
            max_steps=6,
        )

    def observe(self, session: AnalysisSession) -> AgentObservation:
        facts = {
            "active_copy_id": session.active_copy_id,
            "verification_attempts": session.verification_attempts,
            "current_fix_verified": session.current_fix_verified,
            "rescan_done": session.rescan_done,
            "verified_fixes_count": sum(1 for v in session.verified_fixes.values() if v),
            "copies_count": len(session.copies),
        }

        cand = session.get_next_unverified_candidate()
        if cand:
            facts["next_candidate_id"] = cand.get("id")

        snippet = sanitize_code_snippet(session.source, line_no=1, max_lines=5)

        return AgentObservation(
            stage=self.stage,
            facts=facts,
            allowed_tools=sorted(self.allowed_tools),
            context_snippet=snippet,
        )
