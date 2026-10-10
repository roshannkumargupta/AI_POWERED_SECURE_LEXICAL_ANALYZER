"""Abstract base class and context definitions for deterministic security rules."""

from __future__ import annotations

import ast
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from apsla.languages.base import Rule as BaseRule
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Finding, Label, Range, Severity
from apsla.unicode_defense.recovery import RecoveryResult


@dataclass(slots=True)
class RuleContext:
    """Execution context provided to security rule matchers."""

    raw_source: str
    recovered_source: str
    tokens: list[Token]
    ast_tree: ast.AST | None
    offset_map: OffsetMap
    recovery: RecoveryResult
    language: str = "python"
    filename: str = "<editor>"
    metadata: dict[str, Any] = field(default_factory=dict)

    def node_to_range(self, node: ast.AST) -> Range:
        """Project an AST node's coordinates in recovered text back to original document coordinates."""
        start_line = getattr(node, "lineno", 1)
        start_col = getattr(node, "col_offset", 0) + 1
        end_line = getattr(node, "end_lineno", start_line)
        end_col = getattr(node, "end_col_offset", start_col) + 1

        rec_range = Range(
            start_line=start_line,
            start_col=start_col,
            end_line=end_line,
            end_col=end_col,
        )
        return self.recovery.map_recovered_range(rec_range)



class Rule(BaseRule, ABC):
    """Base class for AST and lexical security analysis rules."""

    @abstractmethod
    def match(self, context: RuleContext) -> list[Finding]:
        """Evaluate rule over tokens and AST, returning findings."""
        ...

    def create_finding(
        self,
        rng: Range,
        message: str,
        evidence: dict[str, Any] | None = None,
        severity_override: Severity | None = None,
        confidence: float = 0.95,
        taint_path: list[Any] | None = None,
        fixes: list[Any] | None = None,
    ) -> Finding:
        """Construct a standardized Finding instance for this rule."""
        sev = severity_override if severity_override is not None else self.severity
        label = Label.MALICIOUS if sev in (Severity.CRITICAL, Severity.HIGH) else Label.SUSPICIOUS
        loc_str = f"{self.id}:{rng.start_line}:{rng.start_col}:{rng.end_line}:{rng.end_col}"
        h = hashlib.sha256(loc_str.encode("utf-8")).hexdigest()[:6]
        finding_id = f"{self.id}-{rng.start_line}-{rng.start_col}-{h}"

        return Finding(
            id=finding_id,
            rule_id=self.id,
            title=self.title,
            cwe=self.cwe,
            severity=sev,
            label=label,
            confidence=confidence,
            range=rng,
            message=message,
            explanation=self.explanation or self.description,
            evidence=evidence or {},
            taint_path=taint_path or [],
            fixes=fixes or [],
            sources=["rule"],
            suppressed=False,
        )
