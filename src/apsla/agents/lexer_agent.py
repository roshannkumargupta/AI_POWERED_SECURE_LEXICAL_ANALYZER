"""Lexer Agent for lexical analysis and encoding validation (Phase 15)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apsla.agents.base import BaseAgent
from apsla.agents.guard import sanitize_code_snippet
from apsla.agents.schemas import AgentObservation

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


class LexerAgent(BaseAgent):
    """Responsible for Unicode sanitization, lexical statistics, and token recovery."""

    def __init__(self) -> None:
        super().__init__(
            name="LexerAgent",
            stage="lexical",
            goal=(
                "Scan source for invisible/bidi unicode vulnerabilities, verify token stream integrity, "
                "re-lex with recovery if errors exceed threshold, and confirm language choice."
            ),
            allowed_tools={
                "unicode_scan",
                "lex_stats",
                "relex_with_recovery",
                "detect_language_candidates",
                "finish",
            },
            max_steps=4,
        )

    def observe(self, session: AnalysisSession) -> AgentObservation:
        facts = {
            "language": session.language,
            "filename": session.filename,
            "tokens_count": len(session.tokens),
            "has_unicode_scan": session.unicode_scan_data is not None,
            "has_lex_stats": session.lex_stats_data is not None,
            "relex_called": session.relex_called,
            "detect_lang_called": session.detect_lang_called,
        }
        if session.lex_stats_data:
            facts["error_token_ratio"] = session.lex_stats_data.get("error_token_ratio", 0.0)
            facts["error_tokens"] = session.lex_stats_data.get("error_tokens", 0)
        if session.unicode_scan_data:
            facts["unicode_findings"] = session.unicode_scan_data.get("findings_count", 0)

        snippet = sanitize_code_snippet(session.source, line_no=1, max_lines=5)
        return AgentObservation(
            stage=self.stage,
            facts=facts,
            allowed_tools=sorted(list(self.allowed_tools)),
            context_snippet=snippet,
        )
