"""Pydantic request and response schemas for SecureLex IDE HTTP API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from apsla.models import AnalysisResult, Fix, VerificationResult


class HealthResponse(BaseModel):
    """System health and active telemetry status."""

    status: str = "ok"
    version: str = "0.1.0"
    ml_mode: str  # "on" | "off"
    ml_model_id: str  # active model folder or "none"


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


class AgentStatusResponse(BaseModel):
    """Status of the local agent and local model provider."""

    mode: str
    ollama_reachable: bool
    model: str
    model_present: bool
    fallback_active: bool
    message: str = ""


class AnalyzeRequest(BaseModel):
    """Payload for code security analysis."""

    source: str
    language: str | None = None
    filename: str | None = None
    options: AnalyzeOptions = Field(default_factory=AnalyzeOptions)


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


class LLMStatusResponse(BaseModel):
    """Configuration status for optional LLM assistant."""

    configured: bool
    provider: str


class LLMFixRequest(BaseModel):
    """Payload to request an AI-suggested fix."""

    source: str
    finding_id: str
    rule_id: str
    language: str = "python"
    start_line: int | None = None
    start_col: int | None = None


class LLMFixResponse(BaseModel):
    """Fix response containing shadow-verified or advice-only proposals."""

    fixes: list[Fix] = Field(default_factory=list)
    notes: str = ""


class LLMExplainRequest(BaseModel):
    """Payload to request plain-English explanation."""

    finding_id: str
    rule_id: str
    message: str = ""


class LLMExplainResponse(BaseModel):
    """AI-generated plain English explanation."""

    explanation: str
    error: str | None = None
