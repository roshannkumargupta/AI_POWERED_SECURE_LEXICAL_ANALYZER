"""Core analysis pipeline coordinating Unicode defense, lexing, rules, taint, and ML fusion."""

from __future__ import annotations

import ast
import time
from typing import Any

import regex

from apsla.languages import registry
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import (
    AnalysisResult,
    EngineMetadata,
    Finding,
    Label,
    Severity,
    TokenInfo,
)
from apsla.rules.base import RuleContext
from apsla.rules.generic import evaluate_unicode_rules
from apsla.scoring import create_analysis_summary
from apsla.unicode_defense.recovery import recover_text

_WHITESPACE_TOKEN_REGEX = regex.compile(r"\S+")


def _bump_severity(sev: Severity) -> Severity:
    """Increase severity by one tier for taint-confirmed findings."""
    match sev:
        case Severity.INFO:
            return Severity.LOW
        case Severity.LOW:
            return Severity.MEDIUM
        case Severity.MEDIUM:
            return Severity.HIGH
        case Severity.HIGH | Severity.CRITICAL:
            return Severity.CRITICAL


class Analyzer:
    """Master static and hybrid security analyzer for SecureLex IDE."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        """Initialize the analyzer with optional configuration overrides."""
        self.options = options or {}

    def analyze(
        self,
        source: str,
        language: str = "generic",
        filename: str = "<editor>",
        options: dict[str, Any] | None = None,
    ) -> AnalysisResult:
        """Execute end-to-end security analysis across source code text.

        Pipeline Stages:
          1. Normalization & Coordinate Indexing (strip initial BOM, construct OffsetMap)
          2. Unicode Defense & Adversarial Token Recovery
          3. Generic Unicode Rule Evaluation
          4. Language Plugin Lookup & Lexical Analysis
          5. AST Rule Evaluation (on Recovered Source)
          6. AST Data-Flow Taint Tracking
          7. Fusion Stub (severity+1, confidence+0.15, taint_path attachment)
          8. Scoring & Summary Construction

        Args:
            source: Raw source code text.
            language: Target programming language identifier.
            filename: File name or virtual editor path.
            options: Optional per-request settings.

        Returns:
            AnalysisResult: Findings, token stream, metrics, and engine metadata.
        """
        start_time = time.perf_counter()
        opts = {**self.options, **(options or {})}

        # Stage 1: Normalization & Offset Map Construction
        offset_map = OffsetMap(source)

        # Stage 2: Unicode Defense Layer & Token Recovery
        recovery = recover_text(source, offset_map)

        # Stage 3: Generic Unicode Security Rules
        findings: list[Finding] = evaluate_unicode_rules(
            raw_text=source,
            offset_map=offset_map,
            recovery=recovery,
        )

        # Stage 4: Language Plugin Lookup & Lexing
        plugin = registry.get(language)
        if plugin is None:
            plugin = registry.detect(filename, source)
        if plugin is None and language.lower() == "python":
            from apsla.languages.python_lang import PythonPlugin

            plugin = PythonPlugin()

        raw_tokens: list[Token] = []
        if plugin is not None:
            try:
                raw_tokens = plugin.lex(source)
            except Exception:
                raw_tokens = []

        # Lexer/parser diagnostics are separate from scored security findings.
        lex_findings: list[Finding] = []
        if plugin is not None:
            lex_findings = _lexical_diagnostics(source, raw_tokens, plugin.id)
            findings.extend(lex_findings)

        # Stage 5: AST Language Rules (evaluated on RECOVERED text so homoglyphs are caught)
        taint_flows: list[Any] = []
        if plugin is not None:
            recovered_ast: ast.AST | None = None
            try:
                recovered_ast = ast.parse(recovery.recovered_text)
            except SyntaxError:
                recovered_ast = None

            ctx = RuleContext(
                raw_source=source,
                recovered_source=recovery.recovered_text,
                tokens=raw_tokens,
                ast_tree=recovered_ast,
                offset_map=offset_map,
                recovery=recovery,
                language=plugin.id,
                filename=filename,
            )

            # Evaluate language rules
            for rule in plugin.rules():
                try:
                    findings.extend(rule.match(ctx))
                except Exception:
                    pass

            findings.extend(_syntax_diagnostics(source, plugin, raw_tokens, lex_findings))

            # Stage 6: Data-Flow Taint Analysis
            if plugin.id == "python":
                from apsla.languages.python_lang.taint import PythonTaintAnalyzer

                taint_res = PythonTaintAnalyzer(ctx).analyze()
                taint_flows = taint_res.flows

            # Stage 7: Fusion Stub
            # (a) Filter out findings at sinks where all inputs were sanitized
            sanitized_keys = {
                (f.rule_id, f.sink_range.start_line) for f in taint_flows if f.sanitized
            }
            findings = [
                f for f in findings if (f.rule_id, f.range.start_line) not in sanitized_keys
            ]

            # (b) Apply confirmed taint flows: boost confidence +0.15, severity + 1, attach path
            confirmed_flows = [f for f in taint_flows if not f.sanitized]
            matched_flow_keys: set[tuple[str, int]] = set()

            for f in findings:
                for flow in confirmed_flows:
                    if (
                        flow.rule_id == f.rule_id
                        and flow.sink_range.start_line == f.range.start_line
                    ) or (
                        flow.sink_range.start_line == f.range.start_line
                        and (
                            f.rule_id.startswith("APS-PY-INJ") or f.rule_id.startswith("APS-PY-IO")
                        )
                    ):
                        matched_flow_keys.add((flow.rule_id, flow.sink_range.start_line))
                        f.confidence = min(1.0, round(f.confidence + 0.15, 2))
                        f.severity = _bump_severity(f.severity)
                        f.label = (
                            Label.MALICIOUS
                            if f.severity in (Severity.HIGH, Severity.CRITICAL)
                            else Label.SUSPICIOUS
                        )
                        f.taint_path = flow.path
                        if "taint" not in f.sources:
                            f.sources.append("taint")
                        break

            # (c) Confirmed taint flows without matching AST rule finding
            for flow in confirmed_flows:
                if (flow.rule_id, flow.sink_range.start_line) not in matched_flow_keys:
                    rule_title = "Command Injection via Tainted Data"
                    cwe = "CWE-78"
                    if "INJ-001" in flow.rule_id:
                        rule_title = "Arbitrary Code Execution via Tainted Data"
                        cwe = "CWE-95"
                    elif "INJ-004" in flow.rule_id:
                        rule_title = "SQL Injection via Tainted Query"
                        cwe = "CWE-89"
                    elif "IO-001" in flow.rule_id:
                        rule_title = "Path Traversal via Tainted Path"
                        cwe = "CWE-22"
                    elif "XSS-001" in flow.rule_id:
                        rule_title = "Cross-Site Scripting via Tainted String"
                        cwe = "CWE-79"

                    findings.append(
                        Finding(
                            id=f"{flow.rule_id}-{flow.sink_range.start_line}-{flow.sink_range.start_col}",
                            rule_id=flow.rule_id,
                            title=rule_title,
                            cwe=cwe,
                            severity=Severity.CRITICAL,
                            label=Label.MALICIOUS,
                            confidence=0.99,
                            range=flow.sink_range,
                            message=flow.message,
                            explanation=flow.message,
                            evidence={"line": flow.sink_range.start_line},
                            taint_path=flow.path,
                            fixes=[],
                            sources=["taint"],
                            suppressed=False,
                        )
                    )

        # Stage 6: Machine Learning Inference
        ml_engine = None
        requested_ml_mode = opts.get("ml_mode", "auto")
        if requested_ml_mode == "off" or not opts.get("ml", True):
            ml_mode = "off"
            ml_probs = None
            ml_threshold_malicious = 0.5
        else:
            from apsla.ml.infer import MLInferenceEngine

            ml_engine = MLInferenceEngine(model_id=opts.get("ml_model_id"), language=language)
            ml_mode = ml_engine.get_mode(language=language)
            ml_probs = (
                ml_engine.predict_token_probabilities(raw_tokens, language=language)
                if ml_engine.is_available(language=language) and raw_tokens
                else None
            )
            ml_threshold_malicious = ml_engine.threshold_malicious

        # Stage 7: Fusion (PROJECT_SPEC Section H)
        from apsla.fusion import fuse_findings

        findings = fuse_findings(
            rule_findings=findings,
            tokens=raw_tokens,
            ml_probabilities=ml_probs,
            ml_mode=ml_mode,
            ml_threshold_malicious=ml_threshold_malicious,
            filename=filename,
        )

        # Stage 7.2: Inline Code Suppression Directives (# securelex: ignore <ID>)
        from apsla.suppression import apply_code_suppressions

        findings = apply_code_suppressions(source, findings)

        # Stage 7.3: Concrete Plain-English Explanations
        from apsla.rules.explanations import format_explanation

        findings = [
            f.model_copy(
                update={
                    "simple_explanation": format_explanation(f, source=source)[0],
                    "detailed_explanation": format_explanation(f, source=source)[1],
                    "explanation": (
                        format_explanation(f, source=source)[1]
                        if not f.explanation or f.explanation == f.message
                        else f.explanation
                    ),
                }
            )
            for f in findings
        ]

        # Stage 7.4: Exploitability & Priority Calculation
        from apsla.prioritization import apply_prioritization

        findings = apply_prioritization(findings)

        # Stage 7.5: Fix Generation & Verification
        if opts.get("fixes", True):
            from apsla.fixes.engine import generate_fixes
            from apsla.languages.python_lang.fixes import register_python_fix_generators

            register_python_fix_generators()
            all_existing_keys = {(f.rule_id, f.range.start_line) for f in findings}
            findings_with_fixes: list[Finding] = []
            for f in findings:
                fixes = (
                    f.fixes
                    if f.kind in {"lexical", "syntax"}
                    else generate_fixes(
                        source=source,
                        finding=f,
                        tokens=raw_tokens,
                        language=language,
                        verify=True,
                        existing_finding_keys=all_existing_keys,
                    )
                )
                findings_with_fixes.append(f.model_copy(update={"fixes": fixes}))
            findings = apply_prioritization(findings_with_fixes)

        # Stage 8: Token Stream Construction
        tokens: list[TokenInfo] = []
        if raw_tokens:
            for tok in raw_tokens:
                tok_range = tok.to_range()
                tok_label = "SAFE"
                tok_score = 0.0
                for f in findings:
                    no_overlap = (
                        f.range.end_line < tok_range.start_line
                        or tok_range.end_line < f.range.start_line
                        or (
                            f.range.end_line == tok_range.start_line
                            and f.range.end_col <= tok_range.start_col
                        )
                        or (
                            tok_range.end_line == f.range.start_line
                            and tok_range.end_col <= f.range.start_col
                        )
                    )
                    if not no_overlap:
                        if f.label.value == "MALICIOUS" or tok_label == "SAFE":
                            tok_label = f.label.value
                        elif f.label.value == "SUSPICIOUS" and tok_label != "MALICIOUS":
                            tok_label = "SUSPICIOUS"
                        tok_score = max(tok_score, f.confidence)

                tokens.append(tok.to_token_info(label=tok_label, score=tok_score))
        else:
            # Fallback whitespace tokenization if no language lexer is active
            for m in _WHITESPACE_TOKEN_REGEX.finditer(source):
                w_start, w_end = m.span()
                w_range = offset_map.span_to_range(w_start, w_end)
                word = m.group(0)

                token_label = "SAFE"
                token_score = 0.0
                for f in findings:
                    no_overlap = (
                        f.range.end_line < w_range.start_line
                        or w_range.end_line < f.range.start_line
                        or (
                            f.range.end_line == w_range.start_line
                            and f.range.end_col <= w_range.start_col
                        )
                        or (
                            w_range.end_line == f.range.start_line
                            and w_range.end_col <= f.range.start_col
                        )
                    )
                    if not no_overlap:
                        if f.label.value == "MALICIOUS" or token_label == "SAFE":
                            token_label = f.label.value
                        elif f.label.value == "SUSPICIOUS" and token_label != "MALICIOUS":
                            token_label = "SUSPICIOUS"
                        token_score = max(token_score, f.confidence)

                tokens.append(
                    TokenInfo(
                        token=word,
                        token_type="TOKEN",
                        range=w_range,
                        label=token_label,
                        score=token_score,
                    )
                )

        # Stage 9: Summary & Security Health Score
        summary = create_analysis_summary(findings=findings, tokens=tokens)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        engine = EngineMetadata(
            ml_mode=ml_mode,
            ml_model_id=ml_engine.get_model_id() if ml_engine is not None else "none",
            taint="ast-flow" if plugin and plugin.id == "python" else "none",
            version="0.1.0",
            elapsed_ms=elapsed_ms,
            parser="python-ast" if plugin and plugin.id == "python" else "lexer-only",
        )

        # Stage 10: Agentic Compiler Stage Orchestration
        agent_mode = str(opts.get("agent") or "off").lower()
        trace_data: list[dict[str, Any]] = []
        agent_meta: dict[str, Any] = {"mode": agent_mode}
        if agent_mode in {"rules", "local"}:
            from apsla.agents.orchestrator import AgentOrchestrator

            orch = AgentOrchestrator(mode=agent_mode)
            findings, trace_steps, agent_meta = orch.run(
                source=source,
                language=language,
                filename=filename,
                initial_findings=findings,
            )
            trace_data = [
                s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in trace_steps
            ]
            summary = create_analysis_summary(findings=findings, tokens=tokens)

        return AnalysisResult(
            language=language,
            filename=filename,
            findings=findings,
            tokens=tokens,
            summary=summary,
            engine=engine,
            trace=trace_data,
            agent_meta=agent_meta,
        )


def _lexical_diagnostics(source: str, tokens: list[Token], language: str) -> list[Finding]:
    """Convert lexer tokens and source patterns into bounded, additive diagnostics with fixes."""
    from apsla.diagnostics.engine import analyze_lexical_diagnostics

    return analyze_lexical_diagnostics(source, tokens, language)


def _syntax_diagnostics(
    source: str, plugin: Any, tokens: list[Token], lexical_findings: list[Finding] | None = None
) -> list[Finding]:
    """Report parser/plugin syntax errors without adding them to the security score."""
    from apsla.diagnostics.engine import analyze_syntax_diagnostics

    return analyze_syntax_diagnostics(source, plugin, tokens, lexical_findings)
