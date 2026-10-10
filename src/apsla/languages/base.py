"""Abstract base class and contracts for language plugin implementations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from apsla.fixes.registry import FixGenerator
from apsla.lexing.token import Token
from apsla.models import Finding, Range, Severity, TaintPathStep


class Rule:
    """Deterministic security rule metadata and execution interface."""

    id: str = ""
    title: str = ""
    cwe: str = ""
    severity: Severity = Severity.MEDIUM
    category: str = ""
    description: str = ""
    explanation_template: str = ""
    explanation: str = ""
    noisy: bool = False

    def __init__(
        self,
        id: str = "",
        title: str = "",
        cwe: str = "",
        severity: Severity = Severity.MEDIUM,
        category: str = "",
        description: str = "",
        explanation_template: str = "",
        explanation: str = "",
        noisy: bool = False,
    ) -> None:
        if id:
            self.id = id
        if title:
            self.title = title
        if cwe:
            self.cwe = cwe
        if severity != Severity.MEDIUM or not hasattr(self, "severity"):
            self.severity = severity
        if category:
            self.category = category
        if description:
            self.description = description
        if explanation_template:
            self.explanation_template = explanation_template
        if explanation:
            self.explanation = explanation
        if noisy:
            self.noisy = noisy

    def match(self, context: Any) -> list[Finding]:
        """Evaluate rule against context."""
        return []



@dataclass(slots=True)
class TaintProfile:
    """Declarative taint specifications for a programming language."""

    language: str
    sources: frozenset[str] = field(default_factory=frozenset)
    sinks: frozenset[str] = field(default_factory=frozenset)
    sanitizers: frozenset[str] = field(default_factory=frozenset)
    dangerous_apis: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class SyntaxResult:
    """Result of language syntax validation."""

    ok: bool
    error: str | None = None
    line: int | None = None
    col: int | None = None


@dataclass(slots=True)
class TaintResult:
    """A detected data-flow taint trace from source to sink."""

    rule_id: str
    title: str
    cwe: str
    severity: Severity
    range: Range
    source_text: str
    sink_text: str
    path: list[TaintPathStep] = field(default_factory=list)
    message: str = ""


# Alias for compatibility
TaintFinding = TaintResult



@runtime_checkable
class LanguagePlugin(Protocol):
    """Protocol establishing the interface required for all language plugins.

    Section F: Adding a language must need NO change in pipeline.py, fusion.py,
    ml/ or server/.
    """

    id: str
    display_name: str
    extensions: list[str]
    monaco_id: str
    keywords: frozenset[str]

    def lex(self, source: str) -> list[Token]:
        """Tokenize source string without raising exceptions."""
        ...

    def rules(self) -> Sequence[Rule]:
        """Return all deterministic rules for this language."""
        ...

    def taint_profile(self) -> TaintProfile:
        """Return the taint tracking profile (sources, sinks, sanitizers)."""
        ...

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        """Execute data-flow taint analysis over source and token stream."""
        ...

    def fix_generators(self) -> dict[str, FixGenerator]:
        """Return rule-id mapped fix generator implementations."""
        ...

    def syntax_check(self, source: str) -> tuple[bool, str | None]:
        """Check whether source is syntactically well-formed."""
        ...

    def parse_structure(self, source: str) -> Any:
        """Parse source into a lightweight StructTree representation."""
        ...

    def dangerous_apis(self) -> dict[str, str]:
        """Return mapping of dangerous API functions to descriptions."""
        ...
