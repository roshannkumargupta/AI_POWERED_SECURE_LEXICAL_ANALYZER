"""JavaScript language plugin implementation for SecureLex IDE."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from apsla.languages.base import (
    FixGenerator,
    LanguagePlugin,
    Rule,
    TaintProfile,
    TaintResult,
)
from apsla.languages.javascript_lang.fixes import register_javascript_fix_generators
from apsla.languages.javascript_lang.lexer import ALL_JS_KEYWORDS, JavaScriptLexer
from apsla.languages.javascript_lang.profile import (
    JS_DANGEROUS_APIS,
    JS_TAINT_PROFILE,
)
from apsla.languages.javascript_lang.rules import ALL_JAVASCRIPT_RULES
from apsla.lexing.token import Token
from apsla.taint.lite import TaintLiteEngine


class JavaScriptPlugin(LanguagePlugin):
    """LanguagePlugin implementation for JavaScript (plain JS, Node.js, and browser code)."""

    id: str = "javascript"
    display_name: str = "JavaScript"
    extensions: list[str] = [".js", ".mjs", ".cjs", ".jsx"]
    monaco_id: str = "javascript"
    keywords: frozenset[str] = ALL_JS_KEYWORDS

    def __init__(self) -> None:
        register_javascript_fix_generators()

    def lex(self, source: str) -> list[Token]:
        """Tokenize JavaScript source code using hand-written state machine lexer."""
        return JavaScriptLexer(source).tokenize()

    def rules(self) -> Sequence[Rule]:
        """Return all deterministic JavaScript security rules."""
        return ALL_JAVASCRIPT_RULES

    def taint_profile(self) -> TaintProfile:
        """Return the taint tracking profile for JavaScript."""
        return JS_TAINT_PROFILE

    def parse_structure(self, source: str) -> Any:
        """Parse JavaScript source into a lightweight StructTree."""
        from apsla.languages.javascript_lang.parser import parse_javascript_structure

        return parse_javascript_structure(source)

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        """Execute statement-level taint-lite data flow analysis."""
        tree = self.parse_structure(source)
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, struct_tree=tree)
        return engine.analyze()

    def fix_generators(self) -> dict[str, FixGenerator]:
        """Return rule-id mapped fix generator implementations."""
        from apsla.fixes.registry import FIX_REGISTRY

        register_javascript_fix_generators()
        res: dict[str, FixGenerator] = {}
        for rule in ALL_JAVASCRIPT_RULES:
            gens = FIX_REGISTRY.get(rule.id)
            if gens:
                res[rule.id] = gens[0]
        return res

    def syntax_check(self, source: str) -> tuple[bool, str | None]:
        """Check whether source is valid JavaScript syntax.

        Verifies:
          1. Lexer produces zero ERROR tokens.
          2. Structure parser produces zero ERROR nodes.
          3. Optional tree-sitter-javascript validation if installed.
          4. Optional 'node --check' validation if node is available and not JSX.
        """
        tokens = self.lex(source)

        # 1. Lexical error check
        for t in tokens:
            if t.kind == "ERROR":
                return False, f"Lexical error: '{t.text}' at line {t.line}, col {t.col}"

        # 2. Structural parsing check (no ERROR nodes)
        tree = self.parse_structure(source)
        if tree.errors:
            first_err = tree.errors[0]
            return (
                False,
                f"Syntax error: {first_err.message} at line {first_err.range.start_line}, col {first_err.range.start_col}",
            )

        # 3. Optional tree-sitter-javascript parse check (if installed)
        try:
            import tree_sitter_javascript as tsjs
            from tree_sitter import Language, Parser

            language = Language(tsjs.language())
            parser = Parser(language)
            tree = parser.parse(source.encode("utf-8"))
            if tree.root_node.has_error:
                return False, "Tree-sitter JavaScript syntax error detected in source."
        except (ImportError, Exception):
            pass

        return True, None

    def dangerous_apis(self) -> dict[str, str]:
        """Return mapping of dangerous JavaScript APIs."""
        return JS_DANGEROUS_APIS
