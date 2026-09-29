"""Registry and base classes for automated vulnerability fix generators."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass

from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Finding, Fix


@dataclass(slots=True)
class FixContext:
    """Context provided to fix generators."""

    source: str
    finding: Finding
    tokens: list[Token]
    ast_tree: ast.AST | None
    offset_map: OffsetMap
    language: str = "python"


class FixGenerator(ABC):
    """Abstract base class for automated rule-specific fix generators."""

    @abstractmethod
    def generate(self, context: FixContext) -> list[Fix]:
        """Generate zero or more proposed Fix instances for the given finding."""
        ...


class FixRegistry:
    """Central registry mapping rule identifiers to fix generators."""

    def __init__(self) -> None:
        self._generators: dict[str, list[FixGenerator]] = {}

    def register(self, rule_id: str, generator: FixGenerator) -> None:
        """Register a fix generator for a specific rule ID."""
        self._generators.setdefault(rule_id, []).append(generator)

    def get(self, rule_id: str) -> list[FixGenerator]:
        """Retrieve all fix generators registered for a rule ID."""
        return self._generators.get(rule_id, [])

    def clear(self) -> None:
        """Remove all registered generators."""
        self._generators.clear()


FIX_REGISTRY = FixRegistry()
