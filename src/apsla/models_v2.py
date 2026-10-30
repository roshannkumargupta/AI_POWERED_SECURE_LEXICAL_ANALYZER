"""Versioned analysis API models and an adapter from the established v1 result."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from apsla.lexing.common import OffsetMap
from apsla.models import AnalysisResult, Finding, Range


class TokenV2(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    language: str
    lexeme: str
    token_type: str
    category: str
    start_offset: int = Field(ge=0, description="UTF-16 code-unit offset, zero-based")
    end_offset: int = Field(ge=0, description="UTF-16 code-unit offset, zero-based, exclusive")
    start_offset_codepoint: int = Field(
        ge=0, description="Python Unicode code-point offset, zero-based"
    )
    end_offset_codepoint: int = Field(
        ge=0, description="Python Unicode code-point offset, zero-based, exclusive"
    )
    start_line: int = Field(ge=1)
    start_column: int = Field(ge=1, description="UTF-16 code-unit column, one-based")
    end_line: int = Field(ge=1)
    end_column: int = Field(ge=1, description="UTF-16 code-unit column, one-based, exclusive")
    lexical_status: Literal["valid", "invalid", "unknown"]
    diagnostic_ids: list[str] = Field(default_factory=list)


class DiagnosticV2(BaseModel):
    id: str
    language: str
    range: Range
    category: Literal["lexical", "syntax", "semantic", "security", "quality"]
    severity: str
    message: str
    related_evidence: list[str] = Field(default_factory=list)
    produced_by: str
    certainty: Literal["definitive", "heuristic", "incomplete"]


class SecurityFindingV2(Finding):
    # The V2 contract normalizes one-or-more CWE identifiers to a list.
    cwe: list[str] = Field(default_factory=list)  # type: ignore[assignment]
    taint_path_id: str | None = None
    certainty: Literal["definitive", "heuristic", "incomplete"] = "heuristic"
    remediation: str | None = None
    tool_provenance: list[str] = Field(default_factory=list)
    safe_pattern: str | None = None
    detectors_fired: list[str] = Field(default_factory=list)


class TaintPathStepV2(BaseModel):
    range: Range
    text: str
    role: Literal["source", "propagation", "sanitizer", "sink"]
    note: str = ""


class TaintPathV2(BaseModel):
    id: str
    steps: list[TaintPathStepV2]
    complete: bool
    limitation: str | None = None


class QualityObservationV2(BaseModel):
    id: str
    kind: str
    range: Range | None = None
    value: Any = None
    evidence: list[str] = Field(default_factory=list)
    measured: bool


class ToolStatus(BaseModel):
    name: str
    kind: str
    available: bool
    version: str | None = None
    executed: bool = False
    duration_ms: float | None = None
    status: Literal["ok", "failed", "timeout", "unavailable", "skipped"]
    reason: str | None = None


class AnalysisDimension(BaseModel):
    status: Literal["ok", "issues", "incomplete", "unavailable"]
    reason: str | None = None


class AnalysisResultV2(BaseModel):
    analysis_id: str
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_version: int = Field(ge=0)
    language: str
    lexical_status: AnalysisDimension = Field(
        default_factory=lambda: AnalysisDimension(status="unavailable", reason="Lexical stage not run.")
    )
    syntax_status: AnalysisDimension = Field(
        default_factory=lambda: AnalysisDimension(status="unavailable", reason="Syntax stage not run.")
    )
    semantic_status: AnalysisDimension = Field(
        default_factory=lambda: AnalysisDimension(status="unavailable", reason="Semantic stage not run.")
    )
    tokens: list[TokenV2] = Field(default_factory=list)
    lexical_summary: dict[str, dict[str, int]] = Field(default_factory=dict)
    syntax_diagnostics: list[DiagnosticV2] = Field(default_factory=list)
    semantic_diagnostics: list[DiagnosticV2] = Field(default_factory=list)
    security_findings: list[SecurityFindingV2] = Field(default_factory=list)
    taint_paths: list[TaintPathV2] = Field(default_factory=list)
    quality: list[QualityObservationV2] = Field(default_factory=list)
    tools: list[ToolStatus] = Field(default_factory=list)
    timing: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    omissions: list[str] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    agent_meta: dict[str, Any] = Field(default_factory=dict)


def result_matches_source(
    result: AnalysisResultV2 | dict[str, Any], source: str, source_version: int
) -> bool:
    """Return whether a result belongs to the current text and monotonic version."""
    data = result if isinstance(result, dict) else result.model_dump()
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return data.get("source_version") == source_version and data.get("source_hash") == digest


def _category(token_type: str) -> str:
    upper = token_type.upper()
    if "KEYWORD" in upper:
        return "Keyword"
    if "IDENT" in upper or "NAME" in upper:
        return "Identifier"
    if "NUMBER" in upper or "INTEGER" in upper or "FLOAT" in upper:
        return "Number literal"
    if "STRING" in upper:
        return "String literal"
    if "CHAR" in upper:
        return "Character literal"
    if "COMMENT" in upper:
        return "Comment"
    if "PREPROCESSOR" in upper:
        return "Preprocessor directive"
    if "ERROR" in upper:
        return "Unknown"
    if "OP" in upper:
        return "Operator"
    if "DELIM" in upper or "PUNCT" in upper:
        return "Delimiter"
    return token_type.title().replace("_", " ")


_TRIVIA_KINDS = {"WHITESPACE", "NEWLINE", "NL", "INDENT", "DEDENT", "EOF"}


def token_type_for(language: str, kind: str, lexeme: str) -> tuple[str, str] | None:
    """Map an input lexer kind to the v2 public token type and category.

    None denotes trivia/EOF, which remains present in the raw lexer stream.
    """
    upper = kind.upper()
    if upper in _TRIVIA_KINDS or "WHITESPACE" in upper or "NEWLINE" in upper:
        return None
    if upper in {"COMMENT", "LINE_COMMENT", "BLOCK_COMMENT", "SHEBANG"}:
        return "COMMENT", "Comment"
    if upper in {"PREPROCESSOR", "DIRECTIVE"}:
        return "PREPROCESSOR", "Preprocessor"
    if upper in {"HEADER", "HEADER_NAME"}:
        return "HEADER_NAME", "Header"
    if "ANNOTATION" in upper or upper == "AT":
        return "ANNOTATION", "Language-specific"
    if "REGEX" in upper:
        return "REGEX_LITERAL", "Literal"
    if "TEMPLATE" in upper or upper in {"BACKTICK"}:
        return "TEMPLATE_LITERAL", "Literal"
    if "TEXT_BLOCK" in upper:
        return "TEXT_BLOCK", "Literal"
    if "F_STRING" in upper:
        return "F_STRING", "Literal"
    if "CHAR" in upper:
        return "CHAR_LITERAL", "Literal"
    if lexeme[:1] == "'" and language in {"cpp", "java"}:
        return "CHAR_LITERAL", "Literal"
    if "STRING" in upper or upper in {"STRING", "STR"}:
        if (language == "python" and lexeme[:2].lower() in {"fr", "rf"}) or (
            language == "python" and lexeme[:1].lower() == "f"
        ):
            return "F_STRING", "Literal"
        return "STRING_LITERAL", "Literal"
    if "NUMBER" in upper or "INTEGER" in upper or "FLOAT" in upper:
        return "NUMBER_LITERAL", "Literal"
    if "KEYWORD" in upper:
        return "KEYWORD", "Keyword"
    if "IDENT" in upper or "NAME" in upper:
        return "IDENTIFIER", "Identifier"
    if upper in {"ERROR", "INVALID", "INVALID_CHARACTER"}:
        return "INVALID_TOKEN", "Invalid"
    if any(x in upper for x in ("DELIMITER", "DELIM", "PUNCT", "BRACKET")):
        return "DELIMITER", "Delimiter"
    if lexeme in {"(", ")", "[", "]", "{", "}", ",", ":", ".", ";", "${"}:
        return "DELIMITER", "Delimiter"
    if any(x in upper for x in ("OPERATOR", "OP", "ASSIGN", "COMPARISON")):
        return "OPERATOR", "Operator"
    return f"LANGUAGE_{upper}", "Language-specific"


def adapt_analysis_result(
    source: str,
    result: AnalysisResult,
    source_version: int,
    *,
    plugin: Any = None,
    include_tokens: bool = True,
    elapsed_ms: float | None = None,
    stages: Sequence[str] | None = None,
) -> AnalysisResultV2:
    """Adapt the old pipeline result into v2 without changing the old result."""
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    analysis_id = hashlib.sha256(
        f"{digest}:{source_version}:{result.language}".encode()
    ).hexdigest()[:24]
    legacy_findings = list(result.findings)
    diagnostics: list[DiagnosticV2] = []
    security: list[SecurityFindingV2] = []
    taint_paths: list[TaintPathV2] = []
    taint_ids: dict[str, str] = {}

    requested_stages = set(
        stages if stages is not None else ["lexical", "syntax", "semantic", "security", "quality"]
    )
    for finding in legacy_findings:
        if finding.taint_path:
            path_id = f"taint-{finding.id}"
            taint_ids[finding.id] = path_id
            steps = []
            for item in finding.taint_path:
                old_kind = getattr(item.step, "value", item.step)
                if old_kind == "sanitizer_missing":
                    # This is evidence of an absent sanitizer, not a sanitizer step.
                    continue
                role = {"propagate": "propagation"}.get(
                    old_kind, old_kind
                )
                if role not in {"source", "propagation", "sanitizer", "sink"}:
                    role = "propagation"
                steps.append(
                    TaintPathStepV2(
                        range=item.range,
                        text=item.text,
                        role=cast(Literal["source", "propagation", "sanitizer", "sink"], role),
                        note=item.note,
                    )
                )
            taint_paths.append(
                TaintPathV2(
                    id=path_id,
                    steps=steps,
                    complete=False,
                    limitation="The current taint engine emits evidence steps but does not certify path completeness.",
                )
            )
        is_lex = finding.kind == "lexical" or "lexical" in finding.sources
        is_syntax = finding.kind == "syntax" or "syntax" in finding.sources
        if is_lex or is_syntax:
            category = "lexical" if is_lex else "syntax"
            if category not in requested_stages:
                continue
            diagnostics.append(
                DiagnosticV2(
                    id=finding.id,
                    language=result.language,
                    range=finding.range,
                    category=cast(Literal["lexical", "syntax", "semantic", "security", "quality"], category),
                    severity=finding.severity.value,
                    message=finding.message or finding.title,
                    related_evidence=[f"{key}: {value}" for key, value in finding.evidence.items()],
                    produced_by=finding.rule_id,
                    certainty="definitive",
                )
            )
        elif "security" in requested_stages:
            finding_data = finding.model_dump()
            finding_data["cwe"] = [finding.cwe]
            security.append(
                SecurityFindingV2(
                    **finding_data,
                    taint_path_id=taint_ids.get(finding.id),
                    certainty="heuristic",
                    remediation=(finding.fixes[0].description if finding.fixes else None),
                    tool_provenance=list(dict.fromkeys([*finding.sources, finding.rule_id])),
                )
            )

    offset_map = OffsetMap(source)
    tokens: list[TokenV2] = []
    category_counts: dict[str, int] = {}
    statuses = {"valid": 0, "invalid": 0, "unknown": 0}
    if include_tokens and plugin is not None and "lexical" in requested_stages:
        try:
            raw_tokens = plugin.lex(source)
        except Exception:
            raw_tokens = []
        for index, token in enumerate(raw_tokens):
            mapped = token_type_for(result.language, token.kind, token.text)
            if mapped is None:
                continue
            ttype, category = mapped
            linked = [
                d.id
                for d in diagnostics
                if d.category == "lexical"
                and (
                    d.range.start_line < token.end_line
                    or (d.range.start_line == token.end_line and d.range.start_col < token.end_col)
                )
                and (
                    d.range.end_line > token.line
                    or (d.range.end_line == token.line and d.range.end_col > token.col)
                )
            ]
            lexical_error = any(
                diagnostic.id in linked
                and diagnostic.severity.lower() not in {"warning", "info"}
                for diagnostic in diagnostics
            )
            lexical_status = (
                "invalid" if ttype == "INVALID_TOKEN" or lexical_error else "valid"
            )
            token_id = hashlib.sha256(
                f"{analysis_id}:{index}:{token.start}:{token.end}:{token.text}".encode()
            ).hexdigest()[:24]
            tokens.append(
                TokenV2(
                    id=token_id,
                    language=result.language,
                    lexeme=token.text,
                    token_type=ttype,
                    category=category,
                    start_offset=token.start,
                    end_offset=token.end,
                    start_offset_codepoint=offset_map.utf16_to_py(token.start),
                    end_offset_codepoint=offset_map.utf16_to_py(token.end),
                    start_line=token.line,
                    start_column=token.col,
                    end_line=token.end_line,
                    end_column=token.end_col,
                    lexical_status=cast(Literal["valid", "invalid", "unknown"], lexical_status),
                    diagnostic_ids=linked,
                )
            )
            statuses[lexical_status] += 1
            category_counts[category] = category_counts.get(category, 0) + 1
    else:
        statuses["unknown"] = len(result.tokens)
    timing = {"total_ms": float(elapsed_ms)} if elapsed_ms is not None else {}
    tools = []
    for stage, name, kind in (
        ("lexical", "internal-lexer", "lexer"),
        ("syntax", "internal-parser", "parser"),
        ("security", "internal-security", "analyzer"),
    ):
        if stage in requested_stages:
            tools.append(
                ToolStatus(
                    name=name,
                    kind=kind,
                    available=plugin is not None,
                    executed=plugin is not None,
                    status="ok" if plugin is not None else "unavailable",
                    reason=None if plugin is not None else "No language adapter is registered.",
                )
            )
    omissions = []
    if "semantic" in requested_stages:
        omissions.append("Semantic diagnostics are not emitted by the current pipeline.")
    if "quality" in requested_stages:
        omissions.append("Quality observations are not emitted by the current pipeline.")
    if requested_stages != {"lexical", "syntax", "semantic", "security", "quality"}:
        omissions.append(
            "The current analysis pipeline evaluates all supported stages; stages filters the returned result only."
        )
    return AnalysisResultV2(
        analysis_id=analysis_id,
        source_hash=digest,
        source_version=source_version,
        language=result.language,
        lexical_status=AnalysisDimension(
            status=("issues" if any(d.category == "lexical" for d in diagnostics) else "ok")
            if plugin is not None and "lexical" in requested_stages
            else "unavailable",
            reason=None if plugin is not None and "lexical" in requested_stages else "Lexical stage was not run or no lexer is registered.",
        ),
        syntax_status=AnalysisDimension(
            status=("issues" if any(d.category == "syntax" for d in diagnostics) else "ok")
            if plugin is not None and "syntax" in requested_stages
            else "unavailable",
            reason=None if plugin is not None and "syntax" in requested_stages else "Syntax stage was not run or no parser is registered.",
        ),
        semantic_status=AnalysisDimension(
            status=("issues" if any(d.category == "semantic" for d in diagnostics) else "incomplete")
            if "semantic" in requested_stages
            else "unavailable",
            reason=(
                "No semantic analyzer diagnostics are emitted by the current pipeline."
                if "semantic" in requested_stages
                else "Semantic stage was not requested."
            ),
        ),
        tokens=tokens,
        lexical_summary={"status": statuses, "category": category_counts},
        syntax_diagnostics=[d for d in diagnostics if d.category == "syntax"],
        semantic_diagnostics=[d for d in diagnostics if d.category == "semantic"],
        security_findings=security,
        taint_paths=taint_paths,
        quality=[],
        tools=tools,
        timing=timing,
        warnings=[],
        omissions=omissions,
        trace=result.trace,
        agent_meta=result.agent_meta,
    )
