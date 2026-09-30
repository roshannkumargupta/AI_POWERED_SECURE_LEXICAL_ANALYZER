"""Pydantic request and response schemas for SecureLex IDE HTTP API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from apsla.models import AnalysisResult, VerificationResult


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

    finding_fingerprint: str
    rule_id: str
    language: str = "python"
    verdict: str = "false_positive"
    snippet: str = ""
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
    error: str | None = None
