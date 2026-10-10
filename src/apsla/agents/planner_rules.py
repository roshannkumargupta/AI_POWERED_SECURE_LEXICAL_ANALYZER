"""Deterministic rules-based planner for compiler agents (Phase 15).

Serves as the deterministic baseline and resilient fallback when LLM is off
or produces invalid / out-of-schema outputs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apsla.agents.schemas import AgentAction, AgentObservation

if TYPE_CHECKING:
    from apsla.agents.tools import AnalysisSession


class RulesPlanner:
    """Deterministic if/else policy for each compiler stage."""

    def plan(
        self,
        agent_name: str,
        stage: str,
        observation: AgentObservation,
        allowed_tools: set[str],
        session: AnalysisSession,
    ) -> AgentAction:
        """Decide the next deterministic tool call based on current session facts."""
        _ = observation.facts

        # ── 1. Lexical Stage ──────────────────────────────────────────
        if stage == "lexical":
            if "unicode_scan" in allowed_tools and session.unicode_scan_data is None:
                return AgentAction(
                    reason="Scanning source code for hidden Unicode bidi and confusable characters.",
                    action="unicode_scan",
                    args={"source": session.source},
                )
            if "lex_stats" in allowed_tools and session.lex_stats_data is None:
                return AgentAction(
                    reason="Calculating lexical token counts and error ratios.",
                    action="lex_stats",
                    args={},
                )
            # Check if recovery or language redetection is warranted
            unicode_hits = (
                session.unicode_scan_data.get("suspicious_count", 0)
                if session.unicode_scan_data
                else 0
            )
            err_ratio = (
                session.lex_stats_data.get("error_token_ratio", 0.0)
                if session.lex_stats_data
                else 0.0
            )

            if (
                (unicode_hits > 0 or err_ratio > 0.02)
                and "relex_with_recovery" in allowed_tools
                and not session.relex_called
            ):
                return AgentAction(
                    reason="High error token ratio or Unicode anomalies detected; re-lexing with panic recovery.",
                    action="relex_with_recovery",
                    args={"source": session.source, "language": session.language},
                )

            if (
                (not session.filename or err_ratio > 0.02)
                and "detect_language_candidates" in allowed_tools
                and not session.detect_lang_called
            ):
                return AgentAction(
                    reason="Language uncertain or high lexical error rate; detecting candidate languages.",
                    action="detect_language_candidates",
                    args={"source": session.source, "filename": session.filename or ""},
                )

            return AgentAction(
                reason="Lexical analysis complete; token stream validated.",
                action="finish",
                args={},
            )

        # ── 2. Syntax Stage ───────────────────────────────────────────
        if stage == "syntax":
            if "parse_structure" in allowed_tools and session.struct_tree is None:
                return AgentAction(
                    reason="Generating lightweight structural AST with panic-mode error recovery.",
                    action="parse_structure",
                    args={"language": session.language},
                )
            if (
                session.struct_tree
                and session.struct_tree.error_count > 0
                and not session.parser_recovered
            ):
                session.parser_recovered = True
                return AgentAction(
                    reason="Syntax errors present in structure tree; logging break coordinates.",
                    action="parse_structure",
                    args={"language": session.language},
                )
            return AgentAction(
                reason="Structural syntax validation complete.",
                action="finish",
                args={},
            )

        # ── 3. Semantic Stage ─────────────────────────────────────────
        if stage == "semantic":
            if "run_rules" in allowed_tools and not session.rules_ran:
                return AgentAction(
                    reason="Executing deterministic static security rule engine across AST and tokens.",
                    action="run_rules",
                    args={},
                )
            if "run_taint" in allowed_tools and not session.taint_ran:
                return AgentAction(
                    reason="Performing standard data-flow taint propagation from sources to sinks.",
                    action="run_taint",
                    args={"mode": "normal"},
                )
            # Run deep taint if unresolved sinks or partial flows exist
            if (
                "run_taint" in allowed_tools
                and session.unresolved_sinks
                and not session.deep_taint_ran
            ):
                return AgentAction(
                    reason="Taint path reached unresolved call; running targeted deep taint analysis.",
                    action="run_taint",
                    args={"mode": "deep", "focus_sinks": session.unresolved_sinks[:3]},
                )
            return AgentAction(
                reason="Semantic checks and taint propagation finished.",
                action="finish",
                args={},
            )

        # ── 4. Triage Stage ───────────────────────────────────────────
        if stage == "triage":
            if "ml_score" in allowed_tools and not session.ml_scored:
                return AgentAction(
                    reason="Computing ML vulnerability confidence scores.",
                    action="ml_score",
                    args={},
                )
            # Review medium-confidence findings (0.40 <= confidence <= 0.60)
            if "run_taint" in allowed_tools and not session.deep_taint_ran:
                candidates = [
                    f.sink
                    for f in session.findings
                    if 0.40 <= getattr(f, "confidence", 0.5) <= 0.60 and getattr(f, "sink", None)
                ]
                if candidates:
                    return AgentAction(
                        reason="Borderline confidence finding detected; escalating sink to deep taint check.",
                        action="run_taint",
                        args={"mode": "deep", "focus_sinks": candidates[:2]},
                    )
            return AgentAction(
                reason="Triage phase complete; findings verified without suppression.",
                action="finish",
                args={},
            )

        # ── 5. Fix Stage ──────────────────────────────────────────────
        if stage == "fix":
            # Find finding needing candidates
            unfixed = [f for f in session.findings if f.id not in session.fix_candidates_by_finding]
            if unfixed and "list_fix_candidates" in allowed_tools:
                target = unfixed[0]
                return AgentAction(
                    reason=f"Retrieving deterministic automated fix candidates for finding {target.id}.",
                    action="list_fix_candidates",
                    args={"finding_id": target.id},
                )
            return AgentAction(
                reason="Fix candidates evaluated and prioritized.",
                action="finish",
                args={},
            )

        # ── 6. Verifier Stage ─────────────────────────────────────────
        if stage == "verify":
            # Has an active copy been made?
            if session.active_fix_id is None:
                cand = session.get_next_unverified_candidate()
                if (
                    cand
                    and "apply_fix_to_copy" in allowed_tools
                    and session.verification_attempts < 3
                ):
                    return AgentAction(
                        reason=f"Applying candidate fix {cand['id']} to isolated copy for validation.",
                        action="apply_fix_to_copy",
                        args={"fix_id": cand["id"]},
                    )
            elif not session.current_fix_verified:
                if "verify_fix" in allowed_tools:
                    return AgentAction(
                        reason=f"Validating semantic correctness and syntax of fix {session.active_fix_id}.",
                        action="verify_fix",
                        args={"fix_id": session.active_fix_id},
                    )
            elif not session.rescan_done:
                if "rescan_copy" in allowed_tools:
                    return AgentAction(
                        reason="Rescanning modified copy to ensure no regressions were introduced.",
                        action="rescan_copy",
                        args={},
                    )

            return AgentAction(
                reason="Verification workflow finished.",
                action="finish",
                args={},
            )

        # ── 7. Explain Stage ──────────────────────────────────────────
        if stage == "explain":
            unexplained = [f for f in session.findings if f.id not in session.explanations]
            if unexplained and "build_explanation" in allowed_tools:
                target = unexplained[0]
                return AgentAction(
                    reason=f"Synthesizing structured explanation for security finding {target.id}.",
                    action="build_explanation",
                    args={"finding_id": target.id},
                )
            return AgentAction(
                reason="Security explanations compiled.",
                action="finish",
                args={},
            )

        return AgentAction(reason="Default finish.", action="finish", args={})
