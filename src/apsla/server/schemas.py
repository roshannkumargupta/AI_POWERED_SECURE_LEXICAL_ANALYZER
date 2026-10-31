"""Pydantic request and response schemas for SecureLex IDE HTTP API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from apsla.models import AnalysisResult, VerificationResult
from apsla.models_v2 import (
    AnalysisDimension,
    DiagnosticV2,
    QualityObservationV2,
    SecurityFindingV2,
    TaintPathV2,
    TokenV2,
    ToolStatus,
)
from apsla.parsing_v2 import ASTViewV2

_DEFAULT_ANALYSIS_STAGES: list[Literal["lexical", "syntax", "semantic", "security", "quality"]] = [
    "lexical",
    "syntax",
    "semantic",
    "security",
    "quality",
]


class HealthResponse(BaseModel):
    """System health and active telemetry status."""

    status: str = "ok"
    version: str = "0.1.0"
    ml_mode: str  # "on" | "off"
    ml_model_id: str  # active model folder or "none"


class SafetyScenarioResponse(BaseModel):
    """Public, source-free catalogue entry for one Safety Lab fixture."""

    id: str
    title: str
    risk: str
    description: str
    languages: list[str]
    expected_safe_behavior: str


class LanguageInfo(BaseModel):
    """Metadata for registered programming language plugin."""

    id: str
    display_name: str
    extensions: list[str]
    monaco_id: str


class AnalyzeOptions(BaseModel):
    """Analysis configuration options."""

    fixes: bool = True
    ml: bool = True
    include_tokens: bool = True
    include_suppressed: bool = False
    agent: str = "off"  # "off" | "rules" | "local"
    stages: list[Literal["lexical", "syntax", "semantic", "security", "quality"]] = Field(
        default_factory=lambda: list(_DEFAULT_ANALYSIS_STAGES)
    )




class AnalyzeRequest(BaseModel):
    """Payload for code security analysis."""

    source: str
    language: str | None = None
    filename: str | None = None
    options: AnalyzeOptions = Field(default_factory=AnalyzeOptions)
    api_version: int = Field(default=1, ge=1, le=2)
    source_version: int = Field(default=0, ge=0)
    include_ast: bool = False
    ast_max_depth: int = Field(default=8, ge=1, le=20)
    ast_max_nodes: int = Field(default=500, ge=1, le=2000)

    @model_validator(mode="after")
    def require_v2_source_version(self) -> AnalyzeRequest:
        if self.api_version == 2 and "source_version" not in self.model_fields_set:
            raise ValueError("source_version is required when api_version is 2")
        return self


class CapabilitiesLanguage(BaseModel):
    id: str
    name: str
    extensions: list[str]
    monaco_id: str
    lexer: dict[str, object]
    parser: dict[str, object]
    semantic_tools: list[str]
    security_tools: list[str]
    formatter: str | None


class CapabilitiesResponse(BaseModel):
    version: str
    languages: list[CapabilitiesLanguage]
    tools: list[ToolStatus]
    ai: dict[str, object]
    limits: dict[str, object]
    features: dict[str, object]


class StageAnalysisResponse(BaseModel):
    analysis_id: str
    source_hash: str
    source_version: int
    language: str
    stage: str
    lexical_status: AnalysisDimension = Field(
        default_factory=lambda: AnalysisDimension(
            status="unavailable", reason="Lexical stage not run."
        )
    )
    syntax_status: AnalysisDimension = Field(
        default_factory=lambda: AnalysisDimension(
            status="unavailable", reason="Syntax stage not run."
        )
    )
    semantic_status: AnalysisDimension = Field(
        default_factory=lambda: AnalysisDimension(
            status="unavailable", reason="Semantic stage not run."
        )
    )
    tokens: list[TokenV2] = Field(default_factory=list)
    lexical_summary: dict[str, dict[str, int]] = Field(default_factory=dict)
    ast: ASTViewV2 | None = None
    diagnostics: list[DiagnosticV2] = Field(default_factory=list)
    findings: list[SecurityFindingV2] = Field(default_factory=list)
    taint_paths: list[TaintPathV2] = Field(default_factory=list)
    quality: list[QualityObservationV2] = Field(default_factory=list)
    findings_summary: dict[str, dict[str, int]] = Field(default_factory=dict)
    tools: list[ToolStatus] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    omissions: list[str] = Field(default_factory=list)


class FixRequest(BaseModel):
    """Payload to apply and verify a single specific fix."""

    source: str
    language: str = "python"
    finding_id: str
    fix_id: str
    filename: str = "<editor>"


class FixResponse(BaseModel):
    """Response returned after single fix application."""

    new_source: str
    diff: str
    verification: VerificationResult
    new_result: AnalysisResult | None = None


class FixAllRequest(BaseModel):
    """Payload for multi-pass batch remediation."""

    source: str
    language: str = "python"
    filename: str = "<editor>"
    allow_review: bool = False
    session_id: str = "default"
    source_version: int = Field(default=0, ge=0)
    approved: bool = False
    approved_diff: str | None = None


class SkippedFixItem(BaseModel):
    """Details of a skipped fix proposal."""

    fix_id: str
    reason: str


class FixAllResponse(BaseModel):
    """Response returned from multi-pass batch remediation."""

    new_source: str
    applied: list[str]
    skipped: list[SkippedFixItem]
    diff: str
    score_before: int
    score_after: int
    source_version: int | None = None
    applied_to_source: bool = False


class FeedbackRequest(BaseModel):
    """Payload for reporting a false-positive finding."""

    finding_fingerprint: str = ""
    fingerprint: str = ""
    rule_id: str
    language: str = "python"
    verdict: str = "false_positive"
    snippet: str = ""
    note: str = ""
    filename: str = "<editor>"
    line: int | None = None


class FeedbackResponse(BaseModel):
    """Response confirming persistence of feedback record."""

    saved: bool = True


class SampleItem(BaseModel):
    """Interactive code sample for testing and IDE demonstration."""

    id: str
    title: str
    category: str  # "vulnerable" | "adversarial" | "safe"
    language: str
    filename: str
    code: str
    description: str
    group: str | None = None
    kind: str | None = None
    level: str | None = None
    topic: str | None = None
    summary: str | None = None
    notes: list[str] | None = None
    expect: dict[str, object] | None = None
    fix_expected: str | None = None
    approximate: bool | None = None
    special_chars: list[str] | None = None
    demo_order: int | None = None
    senior: dict[str, object] | None = None


class MLInsightsRequest(BaseModel):
    """Payload for per-token explainability inspection."""

    source: str
    language: str = "python"
    token_index: int


class MLInsightsResponse(BaseModel):
    """Per-feature-group occlusion results for explainability."""

    ml_mode: str
    token_index: int | None = None
    token_text: str | None = None
    predicted_label: str | None = None
    probabilities: dict[str, float] | None = None
    feature_group_drops: dict[str, float] | None = None




class AIPermissionRequest(BaseModel):
    session_id: str = Field(min_length=16, max_length=128)
    consent: bool


class AIModelRequest(BaseModel):
    session_id: str = Field(min_length=16, max_length=128)
    model: str = Field(min_length=1, max_length=160)


class AIExplainRequest(BaseModel):
    session_id: str = Field(min_length=16, max_length=128)
    remote_consent: bool = False
    target: Literal["token", "diagnostic", "finding", "file", "patch"]
    source: str = Field(max_length=512 * 1024)
    language: str
    target_id: str | None = None
    source_version: int = Field(default=0, ge=0)
    patch: str | None = Field(default=None, max_length=128 * 1024)


class FormatRequest(BaseModel):
    source: str = Field(max_length=512 * 1024)
    language: Literal["python", "java", "javascript", "cpp"]


class AIGenerateRequest(BaseModel):
    session_id: str = Field(min_length=16, max_length=128)
    remote_consent: bool = False
    language: Literal["python", "java", "javascript", "cpp"]
    requirements: list[str] = Field(min_length=1, max_length=30)


class AgentEventResponse(BaseModel):
    id: str
    timestamp: str
    operation_id: str
    agent: str
    action: str
    tool: str | None
    argument_summary: str
    decision_source: str
    outcome: str
    duration: float
    error: str | None = None
    subject_type: Literal["token", "diagnostic", "finding", "file", "patch"] | None = None
    subject_id: str | None = None
    provider: str | None = None
    model: str | None = None
    tokens: int | None = None


class AITestConnectionRequest(BaseModel):
    provider: str | None = None
    model: str | None = None


class AITestConnectionResponse(BaseModel):
    ok: bool
    provider: str
    latency_ms: float = 0.0
    model: str | None = None
    available_models: list[str] = Field(default_factory=list)
    error: str | None = None


class AIChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(max_length=64 * 1024)


class AIChatContext(BaseModel):
    file: str | None = None
    language: str | None = None
    source_version: int | None = None
    selected_range: dict[str, int] | None = None
    selected_code: str | None = None
    selected_token: dict[str, Any] | None = None
    stage: str | None = None
    diagnostic: dict[str, Any] | None = None
    finding: dict[str, Any] | None = None
    findings_count: int | None = None


class AIChatRequest(BaseModel):
    session_id: str = Field(min_length=16, max_length=128)
    remote_consent: bool = False
    message: str = Field(min_length=1, max_length=16 * 1024)
    source: str = Field(default="", max_length=512 * 1024)
    language: str = Field(default="cpp")
    history: list[AIChatMessage] = Field(default_factory=list, max_length=50)
    context: AIChatContext | None = None


class AIChatResponse(BaseModel):
    operation_id: str
    reply: str
    code_snippets: list[str] = Field(default_factory=list)
    provider: str
    model: str


