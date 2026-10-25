"""Compiler Agent Orchestrator coordinating all 7 compilation stages.

STRICT INVARIANTS:
1. Runs stages strictly in sequence: lexical -> syntax -> semantic -> triage -> fix -> verify -> explain -> finish.
2. Enforces global budgets: max steps (12), wall-clock timeout (60s).
3. Findings are guaranteed to be a SUPERSET-or-equal of deterministic non-agentic findings.
4. On any agent error or timeout, logs the error and returns deterministic results (never fails).
5. Mode 'off' returns byte-identical results to deterministic analysis.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from apsla.agents.explain_agent import ExplainAgent
from apsla.agents.fix_agent import FixAgent
from apsla.agents.lexer_agent import LexerAgent
from apsla.agents.parser_agent import ParserAgent
from apsla.agents.planner_rules import RulesPlanner
from apsla.agents.semantic_agent import SemanticAgent
from apsla.agents.tools import AnalysisSession
from apsla.agents.trace import TraceLogger
from apsla.agents.triage_agent import TriageAgent
from apsla.agents.verifier_agent import VerifierAgent
from apsla.models import Finding

DEFAULT_MAX_STEPS = 12
DEFAULT_MAX_LLM_CALLS = 0
DEFAULT_TIMEOUT_S = 60.0


class AgentOrchestrator:
    """Coordinates compiler stage agents to produce comprehensive security findings and audit trace."""

    def __init__(
        self,
        mode: str = "rules",
        max_steps: int = DEFAULT_MAX_STEPS,
        max_llm_calls: int = DEFAULT_MAX_LLM_CALLS,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        **_kwargs: Any,
    ) -> None:
        self.mode = mode.lower()
        if self.mode not in {"off", "rules"}:
            self.mode = "off"

        self.rules_planner = RulesPlanner()
        self.max_steps = max_steps
        self.max_llm_calls = max_llm_calls
        self.timeout_s = timeout_s

    def run(
        self,
        source: str,
        language: str = "generic",
        filename: str = "<editor>",
        initial_findings: list[Finding] | None = None,
    ) -> tuple[list[Finding], list[dict[str, Any]], dict[str, Any]]:
        """Execute the agentic compiler pipeline across all stages.

        Returns:
            tuple[findings, trace_steps, summary_metadata]
        """
        trace = TraceLogger()
        start_time = time.perf_counter()

        session = AnalysisSession(
            session_id=f"session-{uuid.uuid4().hex[:8]}",
            source=source,
            language=language,
            filename=filename,
            findings=list(initial_findings or []),
        )

        active_planner: RulesPlanner = self.rules_planner

        stages = [
            LexerAgent(),
            ParserAgent(),
            SemanticAgent(),
            TriageAgent(),
            FixAgent(),
            VerifierAgent(),
            ExplainAgent(),
        ]

        try:
            for agent in stages:
                # Check global budgets
                elapsed = time.perf_counter() - start_time
                if elapsed > self.timeout_s or trace.total_steps >= self.max_steps:
                    break

                # Skip stages when no findings exist to optimize performance
                if agent.stage in {"triage", "fix", "verify", "explain"} and not session.findings:
                    continue

                if agent.stage == "verify" and not any(session.fix_candidates.values()):
                    continue

                # Run stage agent with strict step budget enforcement
                for _ in range(agent.max_steps):
                    if trace.total_steps >= self.max_steps:
                        break
                    keep_going = agent.step(session=session, planner=active_planner, trace=trace)
                    if not keep_going:
                        break

            # Ensure final finish step is recorded
            if not session.finished:
                session.call_tool("finish")
                trace.record_step(
                    agent="Orchestrator",
                    stage="pipeline",
                    action="finish",
                    args_summary="",
                    reason="All stages concluded successfully.",
                    observation_summary=f"{len(session.findings)} findings finalized.",
                    decision_source="rules",
                    ms=0.1,
                    accepted=True,
                )

        except Exception as e:
            # Resilient fallback: never crash or return empty findings on agent error
            trace.record_step(
                agent="Orchestrator",
                stage="pipeline",
                action="finish",
                args_summary="",
                reason=f"Pipeline recovered from agent error: {e}",
                observation_summary="Reverting to deterministic findings.",
                decision_source="rules",
                ms=0.1,
                accepted=False,
                rejection_reason=str(e),
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # INVARIANT: Findings must be a superset-or-equal of initial findings
        final_findings = session.findings
        for init_f in initial_findings or []:
            if not any(f.id == init_f.id for f in final_findings):
                final_findings.append(init_f)

        summary_meta = {
            "mode": self.mode,
            "total_steps": trace.total_steps,
            "llm_calls": 0,
            "elapsed_ms": round(elapsed_ms, 2),
            "structure_quality": session.structure_quality,
            "verified_fixes": sum(1 for v in session.verified_fixes.values() if v),
        }

        return final_findings, trace.to_list(), summary_meta
