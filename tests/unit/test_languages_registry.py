"""Tests for language plugin protocol, registry, and extensibility."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from apsla.languages.base import (
    FixGenerator,
    LanguagePlugin,
    Rule,
    TaintProfile,
    TaintResult,
)
from apsla.languages.registry import (
    clear_registry,
    detect,
    get,
    list_plugins,
    register,
)
from apsla.lexing.token import Token
from apsla.models import Severity
from apsla.pipeline import Analyzer


@dataclass
class DummyPlugin:
    """A minimal mock language plugin conforming to LanguagePlugin."""

    id: str = "dummy"
    display_name: str = "Dummy Language"
    extensions: list[str] = field(default_factory=lambda: [".dum", ".dummy"])
    monaco_id: str = "dummy"
    keywords: frozenset[str] = frozenset({"fn", "let", "mut"})

    def lex(self, source: str) -> list[Token]:
        return []

    def rules(self) -> list[Rule]:
        return [
            Rule(
                id="APS-DUM-001",
                title="Dummy Insecure Pattern",
                cwe="CWE-78",
                severity=Severity.HIGH,
                category="INJECTION",
                description="Flags dangerous dummy functions.",
            )
        ]

    def taint_profile(self) -> TaintProfile:
        return TaintProfile(
            language="dummy", sources=frozenset({"user_input"}), sinks=frozenset({"dummy_exec"})
        )

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        return []

    def fix_generators(self) -> dict[str, FixGenerator]:
        return {}

    def syntax_check(self, source: str) -> tuple[bool, str | None]:
        return (True, None)

    def dangerous_apis(self) -> dict[str, str]:
        return {"dummy_exec": "Executes raw string command"}


def test_language_plugin_protocol_conformance():
    """Verify that DummyPlugin satisfies the LanguagePlugin Protocol."""
    plugin = DummyPlugin()
    assert isinstance(plugin, LanguagePlugin)


def test_registry_registration_and_retrieval():
    """Verify registering, retrieving, and listing plugins."""
    try:
        clear_registry()
        assert len(list_plugins()) == 0

        plugin = DummyPlugin()
        register(plugin)

        assert get("dummy") is plugin
        assert get("nonexistent") is None
        assert plugin in list_plugins()

        # Duplicate registration raises ValueError
        with pytest.raises(ValueError, match="already registered"):
            register(plugin)
    finally:
        clear_registry()


def test_plugin_detection_by_extension_and_shebang():
    """Verify plugin auto-detection by filename and shebang."""
    try:
        clear_registry()
        plugin = DummyPlugin()
        register(plugin)

        # Detection by extension
        detected_ext = detect("sample.dummy", "print(1)")
        assert detected_ext is plugin

        detected_dum = detect("module.dum", "x = 1")
        assert detected_dum is plugin

        # Detection by shebang
        detected_shebang = detect("script_without_ext", "#!/usr/bin/env dummy\nx = 1")
        assert detected_shebang is plugin

        # Unrecognized file
        assert detect("unknown.txt", "some plain text") is None
    finally:
        clear_registry()


def test_new_language_requires_no_change_to_pipeline():
    """Prove that an external/new language plugin works seamlessly through Analyzer without modifying pipeline.py."""
    try:
        clear_registry()
        plugin = DummyPlugin()
        register(plugin)

        # Execute analysis targeting the newly registered dummy language
        analyzer = Analyzer()
        result = analyzer.analyze(
            source="custom_token = 123",
            language="dummy",
            filename="test.dummy",
            options={},
        )

        assert result.summary.tokens_total >= 1
        assert result.summary.score == 100
        assert len(result.findings) == 0
    finally:
        clear_registry()
