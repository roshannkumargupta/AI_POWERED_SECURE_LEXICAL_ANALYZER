"""Null / no-op LLM provider active when no LLM key is configured."""

from __future__ import annotations

from apsla.llm.provider import LLMProvider
from apsla.models import Finding, Fix


class NullProvider(LLMProvider):
    """Default no-op provider returning empty responses without network access."""

    def suggest_fix(self, source: str, finding: Finding) -> list[Fix]:
        """Return empty list of proposed fixes."""
        return []

    def explain(self, finding: Finding) -> str:
        """Return empty explanation."""
        return ""

    def is_configured(self) -> bool:
        """Always False as no keys are configured."""
        return False

    @property
    def provider_name(self) -> str:
        """Identifier name."""
        return "none"
