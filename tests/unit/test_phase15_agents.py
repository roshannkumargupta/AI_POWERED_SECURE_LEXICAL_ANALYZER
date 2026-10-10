"""Unit tests for Phase 15 agentic compilation pipeline and core invariants."""

from __future__ import annotations

from typing import Any

from apsla.agents.orchestrator import AgentOrchestrator
from apsla.agents.planner_rules import RulesPlanner
from apsla.agents.tools import AnalysisSession
from apsla.agents.trace import TraceLogger
from apsla.llm.local_ollama import LocalLLM
from apsla.models import Finding, Label, Range, Severity


class FakeGarbageLLM(LocalLLM):
    """Fake LLM returning non-JSON or random garbage."""

    def __init__(self) -> None:
        super().__init__(base_url="http://127.0.0.1:11434")

    def chat_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        self.call_count += 1
        return None  # Simulates failed JSON or timeout


class FakeCannedLLM(LocalLLM):
    """Fake LLM returning pre-scripted responses."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        super().__init__(base_url="http://127.0.0.1:11434")
        self.responses = list(responses)
        self.idx = 0

    def chat_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        self.call_count += 1
        if self.idx < len(self.responses):
            res = self.responses[self.idx]
            self.idx += 1
            return res
        return {"reason": "Conclude stage", "action": "finish", "args": {}}


def test_invariant_b_mode_off_byte_identical():
    """Mode 'off' output has empty trace and findings identical to baseline analysis."""
    import asyncio

    from apsla.pipeline import Analyzer
    from apsla.server.app import analyze_code
    from apsla.server.schemas import AnalyzeOptions, AnalyzeRequest

    source = "import os\ndef run(c):\n    os.system(c)\n"
    analyzer = Analyzer()
    base_res = analyzer.analyze(source, language="python")

    req_off = AnalyzeRequest(source=source, language="python", options=AnalyzeOptions(agent="off"))
    res_off = asyncio.run(analyze_code(req_off))

    assert len(res_off.findings) == len(base_res.findings)
    assert [f.id for f in res_off.findings] == [f.id for f in base_res.findings]
    assert res_off.trace == []
    assert res_off.agent_meta == {"mode": "off"}


def test_invariant_a_superset_or_equal_findings():
    """Agentic findings must be a superset-or-equal of non-agentic findings."""
    source = "import os\nos.system(cmd)"
    initial = [
        Finding(
            id="INIT-1",
            rule_id="APS-PY-001",
            title="Pre-existing finding",
            cwe="CWE-78",
            severity=Severity.HIGH,
            label=Label.MALICIOUS,
            confidence=0.8,
            range=Range(start_line=2, start_col=1, end_line=2, end_col=15),
            message="Initial finding",
        )
    ]
    orchestrator = AgentOrchestrator(mode="rules")
    findings, trace, meta = orchestrator.run(source, language="python", initial_findings=initial)

    # Initial finding MUST be present
    assert any(f.id == "INIT-1" for f in findings)
    assert len(findings) >= len(initial)


def test_invariant_c_rules_planner_is_deterministic():
    """RulesPlanner runs produce identical findings and trace actions."""
    source = "import os\nos.system('ls')"

    orch1 = AgentOrchestrator(mode="rules")
    findings1, trace1, _ = orch1.run(source, language="python")

    orch2 = AgentOrchestrator(mode="rules")
    findings2, trace2, _ = orch2.run(source, language="python")

    assert len(findings1) == len(findings2)
    assert [f.id for f in findings1] == [f.id for f in findings2]
    assert [s["action"] for s in trace1] == [s["action"] for s in trace2]


def test_invariant_d_garbage_llm_equals_rules_planner_result():
    """With an LLM returning garbage/None, result equals RulesPlanner result."""
    source = "import os\nos.system('whoami')"

    rules_orch = AgentOrchestrator(mode="rules")
    rules_findings, rules_trace, _ = rules_orch.run(source, language="python")

    garbage_llm = FakeGarbageLLM()
    llm_orch = AgentOrchestrator(mode="local", local_llm=garbage_llm)
    llm_findings, llm_trace, _ = llm_orch.run(source, language="python")

    # Finding IDs and count must match RulesPlanner
    assert [f.id for f in llm_findings] == [f.id for f in rules_findings]
    # Actions taken should match rules planner actions (though decisions marked fallback)
    assert [s["action"] for s in llm_trace] == [s["action"] for s in rules_trace]
    assert all(s["decision_source"] == "rules" for s in llm_trace)


def test_budget_enforcement():
    """Orchestrator terminates when max_steps budget is reached."""
    source = "import os\nos.system('test')"
    orch = AgentOrchestrator(mode="rules", max_steps=3)
    _, trace, meta = orch.run(source, language="python")

    # Should have executed at most 3 steps before concluding
    assert meta["total_steps"] <= 4  # max_steps + finish


def test_deep_taint_escalation_on_unresolved_sink():
    """SemanticAgent requests deep taint when unresolved sinks are present."""
    session = AnalysisSession(
        session_id="test-deep",
        source="x = input()\nsubprocess.Popen(x)",
        language="python",
        unresolved_sinks=["subprocess.Popen"],
    )
    planner = RulesPlanner()
    from apsla.agents.semantic_agent import SemanticAgent

    agent = SemanticAgent()
    trace = TraceLogger()

    # Step 1: run_rules
    agent.step(session, planner, trace)
    assert session.rules_ran is True

    # Step 2: run_taint normal
    agent.step(session, planner, trace)
    assert session.taint_ran is True

    # Step 3: run_taint deep because unresolved_sinks is not empty
    agent.step(session, planner, trace)
    assert session.deep_taint_ran is True
