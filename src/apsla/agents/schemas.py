"""Schemas and data models for the compiler agentic layer (Phase 15)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentAction:
    """Action proposed by an agent planner."""

    reason: str
    action: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTraceStep:
    """Record of a single decision and tool execution step."""

    step: int
    agent: str
    stage: str
    action: str
    args_summary: str
    reason: str
    observation_summary: str
    decision_source: str  # "llm" | "rules"
    ms: float
    accepted: bool
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert trace step to serialized dictionary."""
        d = asdict(self)
        if self.rejection_reason is None:
            d.pop("rejection_reason", None)
        return d


@dataclass
class AgentObservation:
    """Summary of observation passed to the planner."""

    stage: str
    facts: dict[str, Any]
    allowed_tools: list[str]
    context_snippet: str | None = None
