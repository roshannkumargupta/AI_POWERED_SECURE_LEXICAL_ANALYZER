"""LLM-based planner querying local Ollama model with strict security guardrails (Phase 15)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from apsla.agents.guard import (
    SYSTEM_PROMPT_GUARD,
    sanitize_reason,
    validate_decision,
)
from apsla.agents.planner_rules import RulesPlanner
from apsla.agents.schemas import AgentAction, AgentObservation
from apsla.llm.local_ollama import LocalLLM

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


class LLMPlanner:
    """Planner querying local model, falling back to RulesPlanner on any rejection or failure."""

    def __init__(
        self,
        local_llm: LocalLLM,
        rules_planner: RulesPlanner | None = None,
        tool_schemas: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.local_llm = local_llm
        self.rules_planner = rules_planner or RulesPlanner()
        self.tool_schemas = tool_schemas or {}

    def plan(
        self,
        agent_name: str,
        stage: str,
        observation: AgentObservation,
        allowed_tools: set[str],
        session: AnalysisSession,
    ) -> tuple[AgentAction, str, str | None]:
        """Propose the next tool action using local model with automatic fallback to rules.

        Returns:
            tuple[AgentAction, decision_source ("llm" | "rules"), rejection_reason (str | None)]
        """
        allowed_list = sorted(list(allowed_tools))
        schema = {
            "type": "object",
            "required": ["reason", "action", "args"],
            "properties": {
                "reason": {"type": "string"},
                "action": {"type": "string", "enum": allowed_list},
                "args": {"type": "object"},
            },
        }

        system_prompt = (
            f"{SYSTEM_PROMPT_GUARD}\n\n"
            f"You are the {agent_name} responsible for compiler stage '{stage}'.\n"
            f"Allowed tools: {', '.join(allowed_list)}.\n"
            'Return strictly a JSON object: {"reason": "...", "action": "...", "args": {...}}.\n'
            "Keep the 'reason' to one short informative sentence."
        )

        user_content_parts = [
            f"Stage: {stage}",
            f"Facts: {json.dumps(observation.facts, default=str)}",
        ]
        if observation.context_snippet:
            user_content_parts.append(observation.context_snippet)

        user_prompt = "\n\n".join(user_content_parts)

        # Call local model
        response = self.local_llm.chat_json(
            system=system_prompt,
            user=user_prompt,
            schema=schema,
        )

        if response is None:
            # Rejection / failure fallback
            fallback_action = self.rules_planner.plan(
                agent_name, stage, observation, allowed_tools, session
            )
            return (
                fallback_action,
                "rules",
                "LLM call timed out, failed JSON decoding, or violated schema",
            )

        raw_action = response.get("action", "")
        raw_args = response.get("args", {})
        raw_reason = sanitize_reason(response.get("reason", ""))

        if not isinstance(raw_args, dict):
            fallback_action = self.rules_planner.plan(
                agent_name, stage, observation, allowed_tools, session
            )
            return (
                fallback_action,
                "rules",
                f"Arguments must be an object, got {type(raw_args).__name__}",
            )

        is_valid, error = validate_decision(
            action=raw_action,
            args=raw_args,
            allowed_tools=allowed_tools,
            tool_schemas=self.tool_schemas,
        )

        if not is_valid:
            fallback_action = self.rules_planner.plan(
                agent_name, stage, observation, allowed_tools, session
            )
            return fallback_action, "rules", error or "Rejected by security policy"

        return AgentAction(reason=raw_reason, action=raw_action, args=raw_args), "llm", None
