"""Validated metadata model for bundled SecureLex samples."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExpectedFinding(BaseModel):
    """Rule and approximate source line expected from the analyzer."""

    rule_id: str
    line: int = Field(ge=1)


class SampleExpect(BaseModel):
    """Expected analyzer behavior for one sample."""

    findings: list[ExpectedFinding] = Field(default_factory=list)
    min_findings: int = Field(default=0, ge=0)
    clean_below: Literal["medium"] | None = None
    taint: bool = False


class SampleMeta(BaseModel):
    """Manifest entry and source metadata used by the API and verification tools."""

    model_config = ConfigDict(extra="forbid")

    id: str
    language: Literal["python", "java", "javascript", "cpp"]
    file: str
    title: str = Field(max_length=50)
    kind: Literal["vulnerable", "safe", "unicode", "lexer"]
    level: Literal["basic", "intermediate", "advanced"] | None = None
    topic: str
    summary: str
    notes: list[str] = Field(min_length=2, max_length=4)
    expect: SampleExpect
    fix_expected: Literal["safe", "review", "manual", "none"]
    approximate: bool = False
    special_chars: list[str] = Field(default_factory=list)
    demo_order: int | None = None
    pending_reason: str | None = None

    @model_validator(mode="after")
    def validate_classification(self) -> SampleMeta:
        """Keep vulnerable levels and clean expectations consistent with kind."""
        if self.kind == "vulnerable" and self.level is None:
            raise ValueError("vulnerable samples require a level")
        if self.kind != "vulnerable" and self.level is not None:
            raise ValueError("only vulnerable samples have a level")
        if self.kind in {"safe", "lexer"} and self.expect.clean_below != "medium":
            raise ValueError("safe and lexer samples require clean_below='medium'")
        if self.kind == "unicode" and not self.special_chars:
            raise ValueError("unicode samples require special_chars")
        return self
