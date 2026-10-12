from __future__ import annotations

import uuid

from apsla.agents.provider_v2 import FakeProvider
from apsla.safety_lab import (
    RUNS,
    SCENARIOS,
    SafetyRunRequest,
    _assertion,
    _classify,
    execute_harness,
    execute_live,
    get_run,
    live_unavailable,
    render_export,
    save_run,
)


def test_all_harness_scenarios_and_supported_languages_have_real_expected_outcomes() -> None:
    for scenario_id, scenario in SCENARIOS.items():
        for language in scenario["languages"]:
            result = execute_harness(scenario_id, language)
            assert result["outcome"] == scenario["expected_harness_outcome"]
            assert result["assertions"]
            assert all(item["passed"] for item in result["assertions"])
            assert result["mode_label"] == "Deterministic harness - no model involved"
            assert "source" not in result["scenario"]
            assert all("timestamp" in event for event in result["timeline"])


def test_safe_lookalike_has_no_security_false_alarm_in_each_language() -> None:
    scenario = SCENARIOS["attack-like-safe-input"]
    for language in scenario["languages"]:
        result = execute_harness("attack-like-safe-input", language)
        assertion = next(
            item for item in result["assertions"] if item["name"] == "no_false_security_alarm"
        )
        assert assertion["passed"] is True


def test_live_mode_uses_fake_provider_only_as_a_test_double() -> None:
    fake = FakeProvider(
        [
            {
                "response": "I will preserve the finding.",
                "requested_operations": [
                    {
                        "tool": "suppress_finding",
                        "operation": "read",
                        "parameters": {"finding_id": "x"},
                    }
                ],
                "candidate_source": "",
            }
        ]
    )
    result = execute_live("finding-suppression", "python", fake)
    assert fake.call_count == 1
    assert result["configuration"]["provider"] == "fake"
    assert result["operations"][0]["allowed"] is False
    assert result["outcome"] == "Attack contained"


def test_no_model_result_does_not_substitute_harness_outcome() -> None:
    result = live_unavailable("comment-injection", "python", "provider unavailable in test")
    assert (
        result["agent_behavior"]["response"] == "Live agent test could not run (model unavailable)"
    )
    assert result["outcome"] is None
    assert result["assertions"] == []
    assert "No harness result was substituted." in result["limitations"]


def test_safety_configuration_cannot_override_provider_or_mode() -> None:
    import pytest

    with pytest.raises(ValueError, match="only session_id"):
        SafetyRunRequest(
            scenario_id="comment-injection",
            language="python",
            mode="HARNESS",
            config={"provider": "fake"},
        )


def test_runs_are_not_prepopulated_and_are_unique() -> None:
    RUNS.clear()
    missing = str(uuid.uuid4())
    assert get_run(missing) is None
    one = execute_harness("comment-injection", "python")
    two = execute_harness("comment-injection", "python")
    assert one["run_id"] != two["run_id"]
    save_run(one)
    assert get_run(one["run_id"]) is one
    assert get_run(two["run_id"]) is None


def test_outcome_requires_assertions_and_observed_tool_decisions() -> None:
    denied = [{"tool": "suppress_finding", "operation": "read", "allowed": False}]
    assert (
        _classify(
            [_assertion("denied", True, "policy")],
            denied,
            None,
            ["f1"],
            ["f1"],
            False,
            "finding-suppression",
        )
        == "Attack contained"
    )
    assert (
        _classify(
            [_assertion("denied", False, "policy")],
            denied,
            None,
            ["f1"],
            ["f1"],
            False,
            "finding-suppression",
        )
        == "Inconclusive"
    )
    assert _classify([], [], None, ["f1"], [], False, "comment-injection") == "Attack succeeded"
    assert _classify([], [], None, [], [], True, "comment-injection") == "Inconclusive"


def test_report_export_formats_escape_and_include_provenance() -> None:
    report = {
        "analysis_id": "a-1",
        "source_hash": "sha256",
        "limitations": ["<script>"],
        "tokens": [
            {
                "text": "token",
                "token_type": "IDENTIFIER",
                "range": {"start_line": 1, "start_col": 1, "end_line": 1, "end_col": 6},
            }
        ],
    }
    json_text, _ = render_export(report, "json")
    markdown, _ = render_export(report, "markdown")
    html, _ = render_export(report, "html")
    csv_text, _ = render_export(report, "csv")
    assert '"source_hash": "sha256"' in json_text
    assert "a-1" in markdown and "sha256" in markdown
    assert "&lt;script&gt;" in html and "<script>" not in html
    assert "analysis_id,source_hash,tool_versions,limitations" in csv_text
    assert "a-1,sha256" in csv_text
    assert "token,IDENTIFIER,1,1,1,6" in csv_text
