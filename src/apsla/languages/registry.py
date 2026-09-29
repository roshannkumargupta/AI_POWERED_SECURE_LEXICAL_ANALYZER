"""Language plugin registry and lookup mechanisms."""

from __future__ import annotations

from pathlib import Path

from apsla.languages.base import LanguagePlugin

_REGISTRY: dict[str, LanguagePlugin] = {}


def register(plugin: LanguagePlugin) -> None:
    """Register a language plugin implementation.

    Args:
        plugin: Instance conforming to the LanguagePlugin protocol.
    """
    key = plugin.id.lower()
    if key in _REGISTRY:
        raise ValueError(f"Language plugin '{plugin.id}' is already registered")
    _REGISTRY[key] = plugin


def get(plugin_id: str) -> LanguagePlugin | None:
    """Retrieve a registered language plugin by its identifier.

    Args:
        plugin_id: Case-insensitive language identifier (e.g. 'python', 'java').

    Returns:
        LanguagePlugin | None: The matching plugin or None if not registered.
    """
    return _REGISTRY.get(plugin_id.lower())


def detect(filename: str, text: str = "") -> LanguagePlugin | None:
    """Infer the appropriate LanguagePlugin from a filename or text content.

    Args:
        filename: Name or path of the source file.
        text: Optional source text for shebang inspection.

    Returns:
        LanguagePlugin | None: Detected plugin, or None if unrecognized.
    """
    ext = Path(filename).suffix.lower()
    if ext:
        for plugin in _REGISTRY.values():
            if ext in plugin.extensions:
                return plugin

    # Shebang detection
    if text.startswith("#!"):
        first_line = text.split("\n", 1)[0].lower()
        for plugin in _REGISTRY.values():
            if plugin.id in first_line:
                return plugin

    return None


def list_plugins() -> list[LanguagePlugin]:
    """Return a list of all registered language plugins."""
    return list(_REGISTRY.values())


def clear_registry() -> None:
    """Clear all registered language plugins (primarily for test isolation)."""
    _REGISTRY.clear()
