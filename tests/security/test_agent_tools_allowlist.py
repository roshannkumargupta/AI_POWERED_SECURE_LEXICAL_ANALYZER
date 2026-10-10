"""Security test for tool registry allowlist and capability containment."""

import ast
from pathlib import Path

import pytest

from apsla.agents.tools import TOOL_REGISTRY

ALLOWED_TOOL_NAMES = {
    "unicode_scan",
    "relex_with_recovery",
    "lex_stats",
    "detect_language_candidates",
    "parse_structure",
    "run_rules",
    "run_taint",
    "ml_score",
    "list_fix_candidates",
    "apply_fix_to_copy",
    "verify_fix",
    "rescan_copy",
    "build_explanation",
    "finish",
}

FORBIDDEN_IMPORTS = {"subprocess", "socket", "requests", "urllib.request"}
FORBIDDEN_CALLS = {"system", "popen", "spawn"}


@pytest.mark.security
def test_tool_registry_contains_only_allowed_names():
    registry_names = set(TOOL_REGISTRY.keys())
    assert registry_names == ALLOWED_TOOL_NAMES, (
        f"Tool registry mismatch: extra={registry_names - ALLOWED_TOOL_NAMES}, "
        f"missing={ALLOWED_TOOL_NAMES - registry_names}"
    )
    assert len(TOOL_REGISTRY) == 14


@pytest.mark.security
def test_tools_file_does_not_import_dangerous_modules():
    tools_path = Path("src/apsla/agents/tools.py")
    assert tools_path.exists()

    tree = ast.parse(tools_path.read_text(encoding="utf-8"))

    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module)

    for forbidden in FORBIDDEN_IMPORTS:
        assert forbidden not in imported_names, (
            f"tools.py illegally imports forbidden module '{forbidden}'"
        )

    # Also verify no calls to os.system or subprocess
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in FORBIDDEN_CALLS
        ):
            pytest.fail(f"tools.py invokes forbidden OS call '{node.func.attr}'")
