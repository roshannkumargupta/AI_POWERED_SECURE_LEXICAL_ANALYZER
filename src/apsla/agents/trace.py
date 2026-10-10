"""Trace logger for agent steps and compiler decisions (Phase 15)."""

from __future__ import annotations

import time
from typing import Any

from apsla.agents.schemas import AgentTraceStep


class TraceLogger:
    """Collects and organizes trace steps during agentic analysis."""

    def __init__(self) -> None:
        self.steps: list[AgentTraceStep] = []
        self._start_time = time.perf_counter()

    def record_step(
        self,
        agent: str,
        stage: str,
        action: str,
        args_summary: str,
        reason: str,
        observation_summary: str,
        decision_source: str,
        ms: float,
        accepted: bool,
        rejection_reason: str | None = None,
    ) -> AgentTraceStep:
        """Append a newly executed or rejected step to the trace."""
        step_num = len(self.steps) + 1
        trace_step = AgentTraceStep(
            step=step_num,
            agent=agent,
            stage=stage,
            action=action,
            args_summary=args_summary,
            reason=reason,
            observation_summary=observation_summary,
            decision_source=decision_source,
            ms=round(ms, 2),
            accepted=accepted,
            rejection_reason=rejection_reason,
        )
        self.steps.append(trace_step)
        return trace_step

    def to_list(self) -> list[dict[str, Any]]:
        """Return list of trace step dictionaries."""
        return [step.to_dict() for step in self.steps]

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def llm_step_count(self) -> int:
        return sum(1 for s in self.steps if s.decision_source == "llm")

    @property
    def rules_step_count(self) -> int:
        return sum(1 for s in self.steps if s.decision_source == "rules")
