"""Unit tests for agentic compilation pipeline and core invariants."""

from __future__ import annotations

from apsla.agents.orchestrator import AgentOrchestrator
from apsla.agents.planner_rules import RulesPlanner
from apsla.agents.tools import AnalysisSession
from apsla.agents.trace import TraceLogger
from apsla.models import Finding, Label, Range, Severity


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
