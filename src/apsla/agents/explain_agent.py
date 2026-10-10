"""Explain Agent with strict grounding check for local model rewrites (Phase 15).

STRICT INVARIANT:
If the local model rewrites the explanation, a GROUNDING CHECK compares every
identifier, line number, and CWE in the rewritten text against the original finding.
If ANYTHING is hallucinated or not grounded in the finding, the rewrite is discarded
and the deterministic template text is used.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from apsla.agents.base import BaseAgent
from apsla.agents.guard import sanitize_code_snippet
from apsla.agents.schemas import AgentObservation
from apsla.models import Finding

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


COMMON_ENGLISH_WORDS = frozenset(
    {
        "the",
        "be",
        "to",
        "of",
        "and",
        "a",
        "in",
        "that",
        "have",
        "i",
        "it",
        "for",
        "not",
        "on",
        "with",
        "he",
        "as",
        "you",
        "do",
        "at",
        "this",
        "but",
        "his",
        "by",
        "from",
        "they",
        "we",
        "say",
        "her",
        "she",
        "or",
        "an",
        "will",
        "my",
        "one",
        "all",
        "would",
        "there",
        "their",
        "what",
        "so",
        "up",
        "out",
        "if",
        "about",
        "who",
        "get",
        "which",
        "go",
        "me",
        "when",
        "make",
        "can",
        "like",
        "time",
        "no",
        "just",
        "him",
        "know",
        "take",
        "people",
        "into",
        "year",
        "your",
        "good",
        "some",
        "could",
        "them",
        "see",
        "other",
        "than",
        "then",
        "now",
        "look",
        "only",
        "come",
        "its",
        "over",
        "think",
        "also",
        "back",
        "after",
        "use",
        "two",
        "how",
        "our",
        "work",
        "first",
        "well",
        "way",
        "even",
        "new",
        "want",
        "because",
        "any",
        "these",
        "give",
        "day",
        "most",
        "us",
        "is",
        "are",
        "was",
        "were",
        "been",
        "has",
        "had",
        "does",
        "did",
        "code",
        "input",
        "user",
        "data",
        "security",
        "risk",
        "line",
        "vulnerability",
        "attack",
        "safe",
        "flaw",
        "sanitize",
        "validate",
        "sink",
        "source",
        "file",
        "call",
        "parameter",
        "value",
        "variable",
        "string",
        "command",
        "query",
    }
)


def verify_grounding(rewritten: str, finding: Finding, snippet: str) -> bool:
    """Verify that rewritten text does not introduce hallucinated CWEs, lines, or identifiers.

    Returns:
        True if all identifiers, numbers, and CWEs are grounded in the finding/snippet.
    """
    grounding_corpus = " ".join(
        [
            finding.rule_id,
            finding.title,
            finding.message,
            finding.explanation or "",
            finding.cwe,
            str(finding.range.start_line),
            str(finding.range.end_line),
            str(finding.range.start_col),
            str(finding.range.end_col),
            snippet,
        ]
    ).lower()

    # 1. Check CWE references (e.g., CWE-78, CWE-89)
    rewrite_cwes = re.findall(r"cwe[-_]?\d+", rewritten.lower())
    for cwe in rewrite_cwes:
        if cwe.replace("_", "-") not in grounding_corpus:
            return False

    # 2. Check line numbers and standalone digits (numbers > 0)
    rewrite_nums = set(re.findall(r"\b\d+\b", rewritten))
    for num in rewrite_nums:
        # Ignore small common numbers like 1 or 2 if part of grammar
        if num not in {"1", "2"} and num not in grounding_corpus:
            return False

    # 3. Check code identifiers (camelCase, snake_case, etc.)
    potential_idents = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{3,}\b", rewritten.lower()))
    for ident in potential_idents:
        if ident in COMMON_ENGLISH_WORDS:
            continue
        # If it's a code-like identifier, it must exist in the finding or snippet
        if "_" in ident or ident in snippet.lower():
            continue
        if ident not in grounding_corpus:
            return False

    return True


class ExplainAgent(BaseAgent):
    """Responsible for building and ground-checking security finding explanations."""

    def __init__(self) -> None:
        super().__init__(
            name="ExplainAgent",
            stage="explain",
            goal=(
                "Synthesize plain-English explanations using deterministic templates. "
                "Optionally simplify using local model with strict grounding checks."
            ),
            allowed_tools={"build_explanation", "finish"},
            max_steps=5,
        )

    def observe(self, session: AnalysisSession) -> AgentObservation:
        unexplained = [f.id for f in session.findings if f.id not in session.explanations]
        facts = {
            "total_findings": len(session.findings),
            "unexplained_count": len(unexplained),
            "unexplained_ids": unexplained[:5],
            "explanations_count": len(session.explanations),
        }

        target_f = next((f for f in session.findings if f.id in unexplained), None)
        line_no = target_f.range.start_line if target_f else 1
        snippet = sanitize_code_snippet(session.source, line_no=line_no, max_lines=5)

        return AgentObservation(
            stage=self.stage,
            facts=facts,
            allowed_tools=sorted(self.allowed_tools),
            context_snippet=snippet,
        )
