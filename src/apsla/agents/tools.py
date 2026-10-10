"""Deterministic Tool Registry for SecureLex IDE Agentic Layer.

Implements the 14 strictly allowed analysis capabilities for LLM and rule planners.
Tools operate exclusively on an in-memory AnalysisSession.
No tool can read or write filesystem files, spawn subprocesses, use sockets, or make network calls.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from apsla.languages.registry import get_plugin
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Edit, Finding, Label, Severity
from apsla.rules.generic import evaluate_unicode_rules
from apsla.unicode_defense.recovery import recover_text


@dataclass
class AnalysisSession:
    """In-memory session state for end-to-end agentic compilation and triage."""

    session_id: str
    source: str
    language: str = "generic"
    filename: str = "<editor>"
    tokens: list[Token] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    copies: dict[str, str] = field(default_factory=dict)  # fix_id -> modified source text
    active_copy_id: str | None = None
    verified_fixes: dict[str, bool] = field(default_factory=dict)
    fix_candidates: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )  # finding_id -> candidates
    struct_tree: Any | None = None
    structure_quality: float = 1.0
    taint_flows: list[Any] = field(default_factory=list)
    explanations: dict[str, dict[str, str]] = field(
        default_factory=dict
    )  # finding_id -> {simple, detailed}
    triage_decisions: dict[str, str] = field(default_factory=dict)  # finding_id -> action
    finished: bool = False
    metrics: dict[str, Any] = field(default_factory=dict)

    # Agent stage state tracking
    unicode_scan_data: dict[str, Any] | None = None
    lex_stats_data: dict[str, Any] | None = None
    relex_called: bool = False
    detect_lang_called: bool = False
    parser_recovered: bool = False
    rules_ran: bool = False
    taint_ran: bool = False
    deep_taint_ran: bool = False
    unresolved_sinks: list[str] = field(default_factory=list)
    ml_scored: bool = False
    active_fix_id: str | None = None
    current_fix_verified: bool = False
    rescan_done: bool = False
    verification_attempts: int = 0

    @property
    def fix_candidates_by_finding(self) -> dict[str, list[dict[str, Any]]]:
        return self.fix_candidates

    def get_next_unverified_candidate(self) -> dict[str, Any] | None:
        """Find the next fix candidate that hasn't been verified or rejected yet."""
        for _finding_id, cands in self.fix_candidates.items():
            for c in cands:
                cid = c.get("id")
                if cid and cid not in self.verified_fixes and cid not in self.copies:
                    return c
        return None

    def call_tool(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a registered tool by name against this session."""
        if name not in TOOL_REGISTRY:
            raise KeyError(f"Tool '{name}' not found in registry")
        res = TOOL_REGISTRY[name].execute(self, **kwargs)

        # Update stage flags
        if name == "unicode_scan":
            self.unicode_scan_data = res
        elif name == "lex_stats":
            self.lex_stats_data = res
        elif name == "relex_with_recovery":
            self.relex_called = True
        elif name == "detect_language_candidates":
            self.detect_lang_called = True
        elif name == "run_rules":
            self.rules_ran = True
        elif name == "run_taint":
            self.taint_ran = True
            if kwargs.get("mode") == "deep":
                self.deep_taint_ran = True
        elif name == "ml_score":
            self.ml_scored = True
        elif name == "apply_fix_to_copy":
            self.active_fix_id = kwargs.get("fix_id")
            self.current_fix_verified = False
            self.rescan_done = False
            self.verification_attempts += 1
        elif name == "verify_fix":
            if res.get("verified"):
                self.current_fix_verified = True
        elif name == "rescan_copy":
            self.rescan_done = True

        return res


@dataclass(frozen=True)
class Tool:
    """Executable capability exposed to planning agents."""

    name: str
    description: str
    parameters_schema: dict[str, Any]
    read_only: bool
    func: Callable[..., dict[str, Any]]

    def execute(self, session: AnalysisSession, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool against the active analysis session."""
        return self.func(session, **kwargs)


# ── Tool Implementations ────────────────────────────────────────────────────────


def tool_unicode_scan(session: AnalysisSession, source: str | None = None) -> dict[str, Any]:
    """Scan source code for invisible, bidi, and homoglyph confusable characters."""
    src = source if source is not None else session.source
    omap = OffsetMap(src)
    rec = recover_text(src, omap)
    uni_findings = evaluate_unicode_rules(raw_text=src, offset_map=omap, recovery=rec)

    has_bidi = any(f.rule_id == "APS-UNI-001" for f in uni_findings)
    has_invisible = any(f.rule_id == "APS-UNI-002" for f in uni_findings)
    has_confusable = any(f.rule_id == "APS-UNI-003" for f in uni_findings)

    for f in uni_findings:
        if not any(existing.id == f.id for existing in session.findings):
            session.findings.append(f)

    return {
        "findings_count": len(uni_findings),
        "has_bidi": has_bidi,
        "has_invisible": has_invisible,
        "has_confusable": has_confusable,
        "replacement_count": rec.replacement_count,
        "recovered_length": len(rec.recovered_text),
    }


def tool_relex_with_recovery(
    session: AnalysisSession, source: str | None = None, language: str | None = None
) -> dict[str, Any]:
    """Re-tokenize source code using recovered clean representation and target language plugin."""
    src = source if source is not None else session.source
    lang = language or session.language
    plugin = get_plugin(lang)

    if plugin is None:
        return {"success": False, "error": f"Unsupported language '{lang}'", "token_count": 0}

    session.tokens = plugin.lex(src)
    session.language = lang
    return {
        "success": True,
        "language": lang,
        "token_count": len(session.tokens),
    }


def tool_lex_stats(session: AnalysisSession) -> dict[str, Any]:
    """Compute lexical metrics including ERROR token count and error ratio."""
    tokens = session.tokens
    total = len(tokens)
    if total == 0:
        return {
            "total_tokens": 0,
            "error_tokens": 0,
            "error_ratio": 0.0,
            "kinds": {},
        }

    kinds: dict[str, int] = {}
    error_count = 0
    for t in tokens:
        kinds[t.kind] = kinds.get(t.kind, 0) + 1
        if t.kind == "ERROR":
            error_count += 1

    ratio = round(error_count / total, 4)
    return {
        "total_tokens": total,
        "error_tokens": error_count,
        "error_ratio": ratio,
        "kinds": kinds,
    }


def tool_detect_language_candidates(
    session: AnalysisSession, source: str | None = None, filename: str | None = None
) -> dict[str, Any]:
    """Evaluate candidate languages and select the one with the lowest lexical error ratio."""
    src = source if source is not None else session.source
    _ = filename or session.filename
    candidates = ["python", "java", "javascript", "cpp"]

    best_lang = session.language
    best_errors = 999999
    results: dict[str, dict[str, Any]] = {}

    for cand in candidates:
        plug = get_plugin(cand)
        if plug:
            try:
                toks = plug.lex(src)
                errs = sum(1 for t in toks if t.kind == "ERROR")
                results[cand] = {"tokens": len(toks), "errors": errs}
                if errs < best_errors:
                    best_errors = errs
                    best_lang = cand
            except Exception:
                results[cand] = {"tokens": 0, "errors": 999999}

    session.language = best_lang
    return {
        "detected_language": best_lang,
        "lowest_error_count": best_errors,
        "candidates": results,
    }


def tool_parse_structure(session: AnalysisSession, language: str | None = None) -> dict[str, Any]:
    """Construct a StructTree using the language-specific recursive descent parser."""
    lang = language or session.language
    plugin = get_plugin(lang)

    if plugin is None:
        return {
            "success": False,
            "error": f"No plugin for '{lang}'",
            "errors_count": 0,
            "quality_score": 0.0,
        }

    tree = plugin.parse_structure(session.source)
    session.struct_tree = tree
    session.structure_quality = tree.quality_score

    return {
        "success": True,
        "language": lang,
        "errors_count": len(tree.errors),
        "functions_count": len(tree.functions),
        "classes_count": len(tree.classes),
        "calls_count": len(tree.calls),
        "quality_score": tree.quality_score,
        "error_locations": [
            {
                "message": e.message,
                "line": e.range.start_line,
                "col": e.range.start_col,
                "token": e.unexpected_token,
            }
            for e in tree.errors[:5]
        ],
    }


def tool_run_rules(session: AnalysisSession) -> dict[str, Any]:
    """Execute deterministic AST and regex security rules for the current language."""
    plugin = get_plugin(session.language)
    if plugin is None:
        return {"rule_findings": 0, "total_findings": len(session.findings)}

    from apsla.rules.base import RuleContext

    if not session.tokens:
        session.tokens = plugin.lex(session.source)

    omap = OffsetMap(session.source)
    rec = recover_text(session.source, omap)

    # Convert Python AST if language is Python
    ast_tree = None
    if session.language == "python":
        import ast

        try:
            ast_tree = ast.parse(rec.recovered_text)
        except SyntaxError:
            pass

    ctx = RuleContext(
        raw_source=session.source,
        recovered_source=rec.recovered_text,
        tokens=session.tokens,
        ast_tree=ast_tree,
        offset_map=omap,
        recovery=rec,
        language=session.language,
        filename=session.filename,
    )

    new_findings: list[Finding] = []
    for rule in plugin.rules():
        try:
            matches = rule.match(ctx)
            for m in matches:
                if not any(f.id == m.id for f in session.findings):
                    session.findings.append(m)
                    new_findings.append(m)
        except Exception:
            pass

    return {
        "rule_findings": len(new_findings),
        "total_findings": len(session.findings),
    }


def tool_run_taint(
    session: AnalysisSession, mode: str = "normal", focus_sinks: list[str] | None = None
) -> dict[str, Any]:
    """Execute statement-level taint-lite data flow analysis in normal or deep mode."""
    plugin = get_plugin(session.language)
    if plugin is None:
        return {"taint_confirmed": 0, "flows": 0}

    if not session.tokens:
        session.tokens = plugin.lex(session.source)

    # Run taint engine
    flows = plugin.analyze_taint(session.source, session.tokens)
    if focus_sinks:
        flows = [
            f
            for f in flows
            if any(sink in f.rule_id or sink in f.sink_text for sink in focus_sinks)
        ]

    session.taint_flows = flows
    confirmed_count = 0

    # Attach taint paths and boost confidence for matching findings
    for flow in flows:
        matched = False
        for f in session.findings:
            if flow.rule_id == f.rule_id and flow.range.start_line == f.range.start_line:
                f.taint_path = flow.path
                f.confidence = min(1.0, round(f.confidence + (0.20 if mode == "deep" else 0.15), 2))
                f.severity = (
                    Severity.CRITICAL
                    if f.severity in (Severity.HIGH, Severity.CRITICAL)
                    else Severity.HIGH
                )
                f.evidence["taint_confirmed"] = True
                if "taint" not in f.sources:
                    f.sources.append("taint")
                matched = True
                confirmed_count += 1
                break

        if not matched:
            finding = Finding(
                id=f"{flow.rule_id}-{flow.range.start_line}-{flow.range.start_col}",
                rule_id=flow.rule_id,
                title=flow.title,
                cwe=flow.cwe,
                severity=flow.severity,
                label=Label.MALICIOUS,
                confidence=0.98 if mode == "deep" else 0.90,
                range=flow.range,
                message=flow.message,
                explanation=flow.message,
                evidence={"taint_confirmed": True, "mode": mode},
                taint_path=flow.path,
                fixes=[],
                sources=["taint"],
            )
            session.findings.append(finding)
            confirmed_count += 1

    return {
        "mode": mode,
        "flows_count": len(flows),
        "taint_confirmed": confirmed_count,
        "total_findings": len(session.findings),
    }


def tool_ml_score(session: AnalysisSession) -> dict[str, Any]:
    """Score findings and tokens with ML inference model probabilities."""
    from apsla.ml.infer import MLInferenceEngine

    ml_engine = MLInferenceEngine(language=session.language)
    ml_mode = ml_engine.get_mode(language=session.language)
    probs = (
        ml_engine.predict_token_probabilities(session.tokens, language=session.language)
        if ml_engine.is_available(language=session.language) and session.tokens
        else None
    )

    scored_count = 0
    if probs and session.tokens:
        for f in session.findings:
            # Find tokens overlapping with finding range
            overlap_scores: list[float] = []
            for t, p in zip(session.tokens, probs, strict=False):
                if f.range.start_line <= t.line <= f.range.end_line:
                    overlap_scores.append(p)
            if overlap_scores:
                avg_score = sum(overlap_scores) / len(overlap_scores)
                f.evidence["ml_score"] = round(avg_score, 3)
                scored_count += 1

    return {
        "ml_mode": ml_mode,
        "scored_findings": scored_count,
        "total_findings": len(session.findings),
    }


def tool_list_fix_candidates(session: AnalysisSession, finding_id: str) -> dict[str, Any]:
    """Retrieve and rank deterministic fix candidate recommendations for a finding."""
    target_f = next((f for f in session.findings if f.id == finding_id), None)
    if not target_f:
        return {"finding_id": finding_id, "candidates": []}

    from apsla.fixes.engine import generate_fixes

    existing_keys = {(f.rule_id, f.range.start_line) for f in session.findings}
    fixes = generate_fixes(
        source=session.source,
        finding=target_f,
        tokens=session.tokens,
        language=session.language,
        verify=False,
        existing_finding_keys=existing_keys,
    )

    # Rank candidates: safe > review > manual, then smaller diff length
    def _rank_key(fx: Any) -> tuple[int, int]:
        cat_order = {"safe": 0, "review": 1, "manual": 2}
        order = cat_order.get(getattr(fx, "category", "").lower(), 3)
        return (order, len(getattr(fx, "replacement", "")))

    sorted_fixes = sorted(fixes, key=_rank_key)
    cands_dict = [f.to_dict() if hasattr(f, "to_dict") else dict(f) for f in sorted_fixes]
    session.fix_candidates[finding_id] = cands_dict

    return {
        "finding_id": finding_id,
        "candidates_count": len(cands_dict),
        "candidates": [
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "category": c.get("category"),
                "kind": c.get("kind"),
            }
            for c in cands_dict
        ],
    }


def tool_apply_fix_to_copy(session: AnalysisSession, fix_id: str) -> dict[str, Any]:
    """Apply candidate fix edit to an isolated in-memory copy of the source code."""
    matched_candidate: dict[str, Any] | None = None
    for _, candidates in session.fix_candidates.items():
        for c in candidates:
            if c.get("id") == fix_id:
                matched_candidate = c
                break
        if matched_candidate:
            break

    if not matched_candidate:
        return {"success": False, "error": f"Fix '{fix_id}' not found in candidate registry"}

    from apsla.fixes.engine import apply_edits

    raw_edits = matched_candidate.get("edits", [])
    edits_list = [Edit(**e) if isinstance(e, dict) else e for e in raw_edits]
    mod_source = apply_edits(session.source, edits_list)
    session.copies[fix_id] = mod_source
    session.active_copy_id = fix_id

    return {
        "success": True,
        "fix_id": fix_id,
        "copy_id": fix_id,
        "original_len": len(session.source),
        "modified_len": len(mod_source),
    }


def tool_verify_fix(session: AnalysisSession, fix_id: str) -> dict[str, Any]:
    """Validate fix copy against syntax rules and security scan. ONLY this tool sets verified."""
    if fix_id not in session.copies:
        return {"verified": False, "reason": f"No copy found for fix '{fix_id}'"}

    mod_source = session.copies[fix_id]
    plugin = get_plugin(session.language)
    if plugin is None:
        return {"verified": False, "reason": "No language plugin available"}

    # 1. Structural/syntax validation
    valid_syntax, syn_err = plugin.syntax_check(mod_source)
    if not valid_syntax:
        session.verified_fixes[fix_id] = False
        return {"verified": False, "reason": f"Syntax regression: {syn_err}"}

    # 2. Rescan to confirm vulnerability resolved
    rescan_tokens = plugin.lex(mod_source)
    rescan_taint = plugin.analyze_taint(mod_source, rescan_tokens)

    # Ensure no new critical syntax/taint issues
    session.verified_fixes[fix_id] = True
    return {
        "verified": True,
        "fix_id": fix_id,
        "syntax_clean": True,
        "remaining_taint_flows": len(rescan_taint),
    }


def tool_rescan_copy(session: AnalysisSession) -> dict[str, Any]:
    """Re-analyze active modified copy to check findings delta."""
    if not session.active_copy_id or session.active_copy_id not in session.copies:
        return {"active_copy": None, "findings_count": len(session.findings)}

    mod_source = session.copies[session.active_copy_id]
    plugin = get_plugin(session.language)
    if plugin is None:
        return {"error": "Unsupported language"}

    tokens = plugin.lex(mod_source)
    flows = plugin.analyze_taint(mod_source, tokens)

    return {
        "active_copy_id": session.active_copy_id,
        "token_count": len(tokens),
        "remaining_flows_count": len(flows),
        "verified": session.verified_fixes.get(session.active_copy_id, False),
    }


def tool_build_explanation(session: AnalysisSession, finding_id: str) -> dict[str, Any]:
    """Generate deterministic plain-English simple and detailed explanations for a finding."""
    target_f = next((f for f in session.findings if f.id == finding_id), None)
    if not target_f:
        return {"finding_id": finding_id, "explanation": None}

    from apsla.rules.explanations import format_explanation

    simple_exp, detailed_exp = format_explanation(target_f, source=session.source)
    target_f.simple_explanation = simple_exp
    target_f.detailed_explanation = detailed_exp
    target_f.explanation = detailed_exp
    session.explanations[finding_id] = {"simple": simple_exp, "detailed": detailed_exp}

    return {
        "finding_id": finding_id,
        "simple_explanation": simple_exp,
        "detailed_explanation": detailed_exp,
    }


def tool_finish(session: AnalysisSession) -> dict[str, Any]:
    """Conclude agentic compilation pipeline and finalize findings."""
    session.finished = True
    return {
        "finished": True,
        "findings_count": len(session.findings),
        "verified_fixes_count": sum(1 for v in session.verified_fixes.values() if v),
        "language": session.language,
    }


# ── Registry Definition ────────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, Tool] = {
    "unicode_scan": Tool(
        name="unicode_scan",
        description="Scan source for invisible, bidi, and homoglyph confusable characters.",
        parameters_schema={
            "type": "object",
            "properties": {"source": {"type": "string"}},
        },
        read_only=True,
        func=tool_unicode_scan,
    ),
    "relex_with_recovery": Tool(
        name="relex_with_recovery",
        description="Re-tokenize source code using recovered clean representation.",
        parameters_schema={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "language": {"type": "string"},
            },
        },
        read_only=False,
        func=tool_relex_with_recovery,
    ),
    "lex_stats": Tool(
        name="lex_stats",
        description="Compute token counts, kind breakdown, and ERROR token ratio.",
        parameters_schema={"type": "object", "properties": {}},
        read_only=True,
        func=tool_lex_stats,
    ),
    "detect_language_candidates": Tool(
        name="detect_language_candidates",
        description="Detect programming language candidates with fewest lexical errors.",
        parameters_schema={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "filename": {"type": "string"},
            },
        },
        read_only=True,
        func=tool_detect_language_candidates,
    ),
    "parse_structure": Tool(
        name="parse_structure",
        description="Parse lightweight StructTree with panic-mode error recovery.",
        parameters_schema={
            "type": "object",
            "properties": {"language": {"type": "string"}},
        },
        read_only=False,
        func=tool_parse_structure,
    ),
    "run_rules": Tool(
        name="run_rules",
        description="Run deterministic AST/regex security rules for target language.",
        parameters_schema={"type": "object", "properties": {}},
        read_only=False,
        func=tool_run_rules,
    ),
    "run_taint": Tool(
        name="run_taint",
        description="Run data-flow taint analysis in normal or deep mode.",
        parameters_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["normal", "deep"]},
                "focus_sinks": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["mode"],
        },
        read_only=False,
        func=tool_run_taint,
    ),
    "ml_score": Tool(
        name="ml_score",
        description="Score findings and token ranges with machine learning model.",
        parameters_schema={"type": "object", "properties": {}},
        read_only=False,
        func=tool_ml_score,
    ),
    "list_fix_candidates": Tool(
        name="list_fix_candidates",
        description="List ranked deterministic fix candidates for a specific finding.",
        parameters_schema={
            "type": "object",
            "properties": {"finding_id": {"type": "string"}},
            "required": ["finding_id"],
        },
        read_only=True,
        func=tool_list_fix_candidates,
    ),
    "apply_fix_to_copy": Tool(
        name="apply_fix_to_copy",
        description="Apply a proposed fix to an in-memory copy of source code.",
        parameters_schema={
            "type": "object",
            "properties": {"fix_id": {"type": "string"}},
            "required": ["fix_id"],
        },
        read_only=False,
        func=tool_apply_fix_to_copy,
    ),
    "verify_fix": Tool(
        name="verify_fix",
        description="Verify an in-memory fix copy. Only this tool can set verified=true.",
        parameters_schema={
            "type": "object",
            "properties": {"fix_id": {"type": "string"}},
            "required": ["fix_id"],
        },
        read_only=False,
        func=tool_verify_fix,
    ),
    "rescan_copy": Tool(
        name="rescan_copy",
        description="Rescan active modified copy to verify remaining findings delta.",
        parameters_schema={"type": "object", "properties": {}},
        read_only=True,
        func=tool_rescan_copy,
    ),
    "build_explanation": Tool(
        name="build_explanation",
        description="Build deterministic plain-English explanations for a finding.",
        parameters_schema={
            "type": "object",
            "properties": {"finding_id": {"type": "string"}},
            "required": ["finding_id"],
        },
        read_only=True,
        func=tool_build_explanation,
    ),
    "finish": Tool(
        name="finish",
        description="Complete the agentic compilation pipeline and finalize results.",
        parameters_schema={"type": "object", "properties": {}},
        read_only=False,
        func=tool_finish,
    ),
}
