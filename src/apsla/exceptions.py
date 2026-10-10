"""Domain-specific exceptions for SecureLex IDE."""

from __future__ import annotations


class SecureLexError(Exception):
    """Base exception for all domain errors within SecureLex."""


class OverlappingEditsError(SecureLexError, ValueError):
    """Raised when two or more text edits overlap in source coordinates."""


class LanguageNotSupportedError(SecureLexError):
    """Raised when an operation targets an unregistered or unsupported programming language."""


class RuleNotFoundError(SecureLexError):
    """Raised when a rule identifier is not found in the rule registry."""


class ParseError(SecureLexError):
    """Raised when source code cannot be parsed into the required syntax tree."""


class TaintAnalysisError(SecureLexError):
    """Raised when data-flow taint analysis encounters an invalid or corrupt state."""
