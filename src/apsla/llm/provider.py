"""LLM provider interface and factory for optional remediation assistance.

Phase 12: OFF by default, configured ONLY via environment variables in .env.
API keys are never hardcoded, never logged, and never sent to frontend.
Context is truncated to 200 lines around the finding. Requests time out in 15 seconds.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from apsla.models import Finding, Fix


def _load_env_file() -> None:
    """Best-effort reading of root .env file without external dependencies."""
    root_env = Path(__file__).resolve().parents[3] / ".env"
    if root_env.is_file():
        try:
            for raw_line in root_env.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
        except Exception:
            pass


class LLMProvider(ABC):
    """Abstract interface for optional LLM assistants."""

    @abstractmethod
    def suggest_fix(self, source: str, finding: Finding) -> list[Fix]:
        """Propose automated remediation fixes for a security finding."""
        ...

    @abstractmethod
    def explain(self, finding: Finding) -> str:
        """Provide a plain-English explanation of the security finding."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if required API credentials are validly configured."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier name of the provider."""
        ...

    @property
    def name(self) -> str:
        """Alias for provider_name."""
        return self.provider_name


def truncate_context_lines(source: str, line_no: int, max_lines: int = 200) -> tuple[str, int, int]:
    """Truncate source code to maximum 200 lines centered around the target line.

    Args:
        source: Full source code text.
        line_no: 1-based target line number.
        max_lines: Maximum total lines in snippet (default 200).

    Returns:
        tuple[snippet, start_line_1_based, end_line_1_based]
    """
    lines = source.splitlines()
    total = len(lines)
    if total <= max_lines:
        return source, 1, total

    half = max_lines // 2
    start_idx = max(0, line_no - 1 - half)
    end_idx = min(total, start_idx + max_lines)
    if end_idx - start_idx < max_lines:
        start_idx = max(0, end_idx - max_lines)

    snippet = "\n".join(lines[start_idx:end_idx])
    return snippet, start_idx + 1, end_idx


def get_llm_provider(
    custom_transport: httpx.BaseTransport | None = None,
    override_provider: str | None = None,
) -> LLMProvider:
    """Instantiate configured LLM provider according to environment variables.

    Priority order:
      1. ANTHROPIC_API_KEY -> AnthropicProvider
      2. GEMINI_API_KEY -> GeminiProvider
      3. OPENAI_API_KEY -> OpenAICompatProvider
      4. NullProvider (default)

    Args:
        custom_transport: Optional mock transport for hermetic testing.
        override_provider: Optional explicit provider selection.

    Returns:
        LLMProvider instance.
    """
    _load_env_file()

    chosen = (override_provider or "").lower()

    if chosen == "anthropic" or (not chosen and os.environ.get("ANTHROPIC_API_KEY")):
        from apsla.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(transport=custom_transport)

    if chosen == "gemini" or (not chosen and os.environ.get("GEMINI_API_KEY")):
        from apsla.llm.gemini_provider import GeminiProvider

        return GeminiProvider(transport=custom_transport)

    if chosen == "openai" or (not chosen and os.environ.get("OPENAI_API_KEY")):
        from apsla.llm.openai_compat import OpenAICompatProvider

        return OpenAICompatProvider(transport=custom_transport)

    from apsla.llm.null import NullProvider

    return NullProvider()


get_configured_llm_provider = get_llm_provider
