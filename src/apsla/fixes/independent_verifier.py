"""Independent deterministic before/after verification; proposal claims are never read."""

from __future__ import annotations

from typing import Any

from apsla.fixes.edits import apply_edits
from apsla.fixes.patch_v2 import PatchProposalV2, source_sha256, validate_proposal
from apsla.parsing_v2 import parse_source, run_semantic_checks
from apsla.pipeline import Analyzer
from apsla.quality_v2 import measure_quality


def _scan(source: str, language: str, filename: str) -> dict[str, Any]:
    analysis_id = source_sha256(source)[:24]
    before = Analyzer().analyze(
        source, language=language, filename=filename, options={"fixes": False, "ml": False}
    )
    parsed = parse_source(language, source, analysis_id)
    semantic, semantic_tools, semantic_omissions = run_semantic_checks(
        language, source, analysis_id
    )
    # Security uses the same deterministic security rules/taint engines as analysis.
    from apsla.security_v2 import internal_security_findings, merge_findings

    security = internal_security_findings(before.findings)
    findings = merge_findings(security)
    quality = measure_quality(language, source, parsed.tree)
    return {
        "legacy": before,
        "parse": parsed,
        "semantic": semantic,
        "semantic_tools": semantic_tools,
        "omissions": semantic_omissions,
        "findings": findings,
        "quality": quality,
    }


def _finding_key(finding: Any) -> tuple[str, str, int, int]:
    cwes = getattr(finding, "cwe", [])
    if isinstance(cwes, str):
        cwes = [cwes]
    rng = finding.range
    return (
        str(getattr(finding, "rule_id", "")),
        ",".join(sorted(cwes)),
        rng.start_line,
        rng.start_col,
    )


def verify_independently(
    source: str, language: str, filename: str, proposal: PatchProposalV2, source_version: int
) -> dict[str, Any]:
    """Run full deterministic checks against separate in-memory source versions."""
    expected_diff = validate_proposal(source, source_version, proposal)
    patched = apply_edits(source, proposal.edits)
    if proposal.diff and expected_diff != proposal.diff:
        raise ValueError("Patch integrity check failed: rendered diff differs.")
    original = _scan(source, language, filename)
    updated = _scan(patched, language, filename)
    old_findings = {_finding_key(f): f for f in original["findings"]}
    new_findings = {_finding_key(f): f for f in updated["findings"]}
    resolved = [f.model_dump(mode="json") for k, f in old_findings.items() if k not in new_findings]
    remaining = [f.model_dump(mode="json") for k, f in old_findings.items() if k in new_findings]
    introduced = [
        f.model_dump(mode="json") for k, f in new_findings.items() if k not in old_findings
    ]
    target_before = [f for f in original["legacy"].findings if f.id == proposal.target_finding_id]
    target_rule = target_before[0].rule_id if target_before else None
    allowed_region = target_before[0].range if target_before else None
    out_of_scope: list[str] = []
    for edit in proposal.edits:
        edit_range = edit.range
        inside_target = bool(
            allowed_region
            and (edit_range.start_line, edit_range.start_col)
            >= (allowed_region.start_line, allowed_region.start_col)
            and (edit_range.end_line, edit_range.end_col)
            <= (allowed_region.end_line, allowed_region.end_col)
        )
        import_declaration = (
            edit.new_text.lstrip().startswith(
                ("import ", "from ", "#include", "using ", "package ")
            )
            and edit_range.start_line <= 20
            and bool(proposal.rationale.strip())
        )
        if not inside_target and not import_declaration:
            out_of_scope.append(
                f"Edit at {edit_range.start_line}:{edit_range.start_col} is outside the target region and is not a justified import/declaration."
            )
    target_gone = bool(target_rule) and not any(
        f.rule_id == target_rule for f in updated["legacy"].findings
    )
    syntax_errors = list(getattr(updated["parse"], "diagnostics", []))
    syntax_ok = not syntax_errors
    integrity = (
        source_sha256(patched) == source_sha256(apply_edits(source, proposal.edits))
        and not out_of_scope
    )
    quality_delta: dict[str, int] = {}
    for kind in {q.kind for q in original["quality"] + updated["quality"]}:
        old_vals = [
            q.value
            for q in original["quality"]
            if q.kind == kind and isinstance(q.value, (int, float))
        ]
        new_vals = [
            q.value
            for q in updated["quality"]
            if q.kind == kind and isinstance(q.value, (int, float))
        ]
        if old_vals and new_vals:
            quality_delta[kind] = int(sum(new_vals) - sum(old_vals))
    tool_status = [x.model_dump(mode="json") for x in updated["semantic_tools"]]
    unavailable = [
        x.name
        for x in updated["semantic_tools"]
        if not x.available or x.status in {"unavailable", "failed", "timeout"}
    ]
    unverified = [
        {
            "check": "tests",
            "reason": "User test execution is unavailable without an execution sandbox.",
        }
    ]
    unverified.extend(
        {"check": name, "reason": "Verification tool unavailable or failed."}
        for name in unavailable
    )
    if updated["omissions"]:
        unverified.extend({"check": "analysis", "reason": x} for x in updated["omissions"])
    failure = not integrity or not syntax_ok or bool(introduced)
    if failure:
        outcome = "Verification failed"
    elif target_gone and not unverified and not remaining:
        outcome = "Verified for specified checks"
    elif target_gone:
        outcome = "Partially verified"
    else:
        outcome = "Inconclusive" if not target_before else "Verification failed"
    return {
        "resolved": resolved,
        "remaining": remaining,
        "introduced": introduced,
        "unverified": unverified,
        "outcome": outcome,
        "patch_integrity": {"passed": integrity, "source_hash": source_sha256(patched)},
        "patch_scope_issues": out_of_scope,
        "syntax": {
            "passed": syntax_ok,
            "diagnostics": [getattr(x, "message", str(x)) for x in syntax_errors],
        },
        "target_resolved": target_gone,
        "target_rule": target_rule,
        "tools": tool_status,
        "semantic_diagnostic_count": len(updated["semantic"]),
        "taint_path_count": sum(
            bool(getattr(f, "taint_path", [])) for f in updated["legacy"].findings
        ),
        "quality_delta": quality_delta,
        "quality_evaluation": {
            "correctness": "Measured by before/after deterministic analyzer and parser results.",
            "security": f"Measured findings delta: {len(resolved)} resolved, {len(remaining)} remaining, {len(introduced)} introduced.",
            "complexity": quality_delta,
            "maintainability": "No standalone maintainability score is measured by the available pipeline.",
            "regression_risk": "Patch changes source bytes; behavior is not executed; user tests unavailable.",
            "unverified_assumptions": [
                "Runtime behavior and project-specific tests were not executed."
            ],
        },
        "tests_status": "tests unavailable",
        "patched_source": patched,
    }
