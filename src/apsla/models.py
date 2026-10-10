"""Pydantic v2 data models for tokens, findings, fixes, and analysis results."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    """Vulnerability severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Label(StrEnum):
    """Classification label for findings and tokens."""

    MALICIOUS = "MALICIOUS"
    SUSPICIOUS = "SUSPICIOUS"
    SAFE = "SAFE"


class TaintStepKind(StrEnum):
    """Kinds of steps in a taint path."""

    SOURCE = "source"
    PROPAGATE = "propagate"
    SINK = "sink"
    SANITIZER = "sanitizer"
    SANITIZER_MISSING = "sanitizer_missing"


class Range(BaseModel):
    """1-based text coordinates, end-exclusive, UTF-16 code units."""

    model_config = ConfigDict(frozen=True)

    start_line: int = Field(ge=1, description="1-based start line number")
    start_col: int = Field(ge=1, description="1-based start column in UTF-16 code units")
    end_line: int = Field(ge=1, description="1-based end line number")
    end_col: int = Field(ge=1, description="1-based end column in UTF-16 code units (exclusive)")


class TokenInfo(BaseModel):
    """Token metadata reported in API responses."""

    token: str
    token_type: str
    range: Range
    label: str = "SAFE"
    score: float = 0.0


class Token(BaseModel):
    """Lexer token representation."""

    kind: str
    text: str
    start: int
    end: int
    line: int
    col: int
    end_line: int
    end_col: int

    @property
    def range(self) -> Range:
        """Convert token line and col coordinates to a Range."""
        return Range(
            start_line=self.line,
            start_col=self.col,
            end_line=self.end_line,
            end_col=self.end_col,
        )

    def to_token_info(self, label: str = "SAFE", score: float = 0.0) -> TokenInfo:
        """Convert this Token to a TokenInfo object."""
        return TokenInfo(
            token=self.text,
            token_type=self.kind,
            range=self.range,
            label=label,
            score=score,
        )


class Edit(BaseModel):
    """Atomic text edit replacing a Range with new text."""

    range: Range
    new_text: str


class VerificationResult(BaseModel):
    """Result of fix safety and idempotency verification."""

    syntax_ok: bool
    finding_gone: bool
    new_findings: list[str] = Field(default_factory=list)
    verified: bool
    notes: str = ""


# Alias for backward compatibility / specification naming
Verification = VerificationResult


class Fix(BaseModel):
    """Remediation proposal with verified atomic edits."""

    id: str
    finding_id: str
    title: str
    description: str
    confidence: str = "safe"  # safe | review | manual
    kind: str = "rule"  # rule | template | llm
    edits: list[Edit] = Field(default_factory=list)
    verification: VerificationResult


class TaintPathStep(BaseModel):
    """Single step in a taint propagation path."""

    step: TaintStepKind
    range: Range
    text: str
    note: str = ""


# Alias for specification naming
TaintStep = TaintPathStep


class Finding(BaseModel):
    """A detected security issue, malicious pattern, or anomaly."""

    id: str
    rule_id: str  # Format: APS-<LANG>-<CAT>-<NNN>
    title: str = ""
    cwe: str = "CWE-000"
    severity: Severity = Severity.MEDIUM
    label: Label = Label.MALICIOUS
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    range: Range
    message: str = ""
    explanation: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
    taint_path: list[TaintPathStep] = Field(default_factory=list)
    fixes: list[Fix] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)  # rule, taint, ml, unicode
    suppressed: bool = False
    suppression_reason: str | None = None
    kind: str = "security"  # security | lexical | syntax
    attack: list[str] | None = None
    exploitability: float = 0.5
    priority: float = 0.0
    simple_explanation: str | None = None
    detailed_explanation: str | None = None


class AnalysisSummary(BaseModel):
    """Summary counts and health score of an analysis run."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    score: int = 100
    tokens_total: int = 0
    tokens_malicious: int = 0
    tokens_suspicious: int = 0
    lexical_errors: int = 0
    syntax_errors: int = 0


# Alias for specification naming
Summary = AnalysisSummary


class EngineMetadata(BaseModel):
    """Metadata regarding engine execution and models used."""

    ml_mode: str = "off"  # "on" | "off"
    ml_model_id: str = "none"
    taint: str = "ast"  # "ast" | "lite"
    version: str = "0.1.0"
    elapsed_ms: float = 0.0
    parser: str = "lexer-only"


# Alias for specification naming
Engine = EngineMetadata


class AnalysisResult(BaseModel):
    """Top-level container returned by Analyzer.analyze()."""

    language: str
    filename: str
    findings: list[Finding] = Field(default_factory=list)
    tokens: list[TokenInfo] = Field(default_factory=list)
    summary: AnalysisSummary = Field(default_factory=AnalysisSummary)
    engine: EngineMetadata = Field(default_factory=EngineMetadata)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    agent_meta: dict[str, Any] = Field(default_factory=dict)
