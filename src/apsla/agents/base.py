"""Base agent class for compiler pipeline stages (Phase 15)."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from apsla.agents.schemas import AgentObservation
from apsla.agents.trace import TraceLogger

if TYPE_CHECKING:
    from apsla.agents.planner_llm import LLMPlanner
    from apsla.agents.planner_rules import RulesPlanner
    from apsla.agents.tools import AnalysisSession


class BaseAgent(ABC):
    """Abstract base class for a compiler stage agent."""

    def __init__(
        self,
        name: str,
        stage: str,
        goal: str,
        allowed_tools: set[str],
        max_steps: int = 4,
    ) -> None:
        self.name = name
        self.stage = stage
        self.goal = goal
        self.allowed_tools = allowed_tools
        self.max_steps = max_steps

    @abstractmethod
    def observe(self, session: AnalysisSession) -> AgentObservation:
        """Construct the stage-specific observation and facts summary."""
        ...

    def step(
        self,
        session: AnalysisSession,
        planner: RulesPlanner | LLMPlanner,
        trace: TraceLogger,
    ) -> bool:
        """Perform one observe -> decide -> act step.

        Returns:
            True if the agent should continue, False if finished.
        """
        obs = self.observe(session)

        # Import here to avoid circular imports
        from apsla.agents.planner_llm import LLMPlanner

        t_start = time.perf_counter()
        if isinstance(planner, LLMPlanner):
            action, decision_source, rejection_reason = planner.plan(
                self.name, self.stage, obs, self.allowed_tools, session
            )
            accepted = rejection_reason is None
        else:
            action = planner.plan(self.name, self.stage, obs, self.allowed_tools, session)
            decision_source = "rules"
            accepted = True
            rejection_reason = None

        if action.action == "finish":
            t_delta = (time.perf_counter() - t_start) * 1000
            trace.record_step(
                agent=self.name,
                stage=self.stage,
                action="finish",
                args_summary="",
                reason=action.reason,
                observation_summary="Stage concluded.",
                decision_source=decision_source,
                ms=t_delta,
                accepted=accepted,
                rejection_reason=rejection_reason,
            )
            return False

        # Execute tool via session
        obs_summary = ""
        try:
            result = session.call_tool(action.action, **action.args)
            if isinstance(result, dict):
                obs_summary = ", ".join(f"{k}={v}" for k, v in list(result.items())[:3])
            elif isinstance(result, list):
                obs_summary = f"{len(result)} items returned"
            else:
                obs_summary = str(result)[:80]
        except Exception as e:
            obs_summary = f"Execution error: {e}"

        t_delta = (time.perf_counter() - t_start) * 1000
        trace.record_step(
            agent=self.name,
            stage=self.stage,
            action=action.action,
            args_summary=", ".join(f"{k}={v}" for k, v in action.args.items())[:60],
            reason=action.reason,
            observation_summary=obs_summary[:100],
            decision_source=decision_source,
            ms=t_delta,
            accepted=accepted,
            rejection_reason=rejection_reason,
        )

        return True

    def run(
        self,
        session: AnalysisSession,
        planner: RulesPlanner | LLMPlanner,
        trace: TraceLogger,
    ) -> None:
        """Run the observe -> decide -> act loop up to max_steps."""
        for _ in range(self.max_steps):
            keep_going = self.step(session, planner, trace)
            if not keep_going:
                break
