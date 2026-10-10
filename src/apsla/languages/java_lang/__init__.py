"""Java language plugin implementation for SecureLex IDE."""

from __future__ import annotations

from typing import Any, Final

from apsla.languages.base import (
    FixGenerator,
    LanguagePlugin,
    Rule,
    TaintProfile,
    TaintResult,
)
from apsla.languages.java_lang.fixes import register_java_fix_generators
from apsla.languages.java_lang.lexer import ALL_JAVA_KEYWORDS, JavaLexer
from apsla.languages.java_lang.profile import JAVA_DANGEROUS_APIS, JAVA_TAINT_PROFILE
from apsla.languages.java_lang.rules import ALL_JAVA_RULES
from apsla.lexing.token import Token
from apsla.taint.lite import TaintLiteEngine


class JavaPlugin(LanguagePlugin):
    """LanguagePlugin implementation for Java source code."""

    id: str = "java"
    display_name: str = "Java"
    extensions: list[str] = [".java"]
    monaco_id: str = "java"
    keywords: frozenset[str] = ALL_JAVA_KEYWORDS

    def __init__(self) -> None:
        register_java_fix_generators()

    def lex(self, source: str) -> list[Token]:
        """Tokenize Java source code using hand-written state machine lexer."""
        return JavaLexer(source).tokenize()

    def rules(self) -> list[Rule]:
        """Return all deterministic Java security rules."""
        return ALL_JAVA_RULES

    def taint_profile(self) -> TaintProfile:
        """Return the taint tracking profile for Java."""
        return JAVA_TAINT_PROFILE

    def parse_structure(self, source: str) -> Any:
        """Parse Java source into a lightweight StructTree."""
        from apsla.languages.java_lang.parser import parse_java_structure

        return parse_java_structure(source)

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        """Execute statement-level taint-lite data flow analysis."""
        tree = self.parse_structure(source)
        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, struct_tree=tree)
        return engine.analyze()

    def fix_generators(self) -> dict[str, FixGenerator]:
        """Return rule-id mapped fix generator implementations."""
        from apsla.fixes.registry import FIX_REGISTRY

        register_java_fix_generators()
        res: dict[str, FixGenerator] = {}
        for rule in ALL_JAVA_RULES:
            gens = FIX_REGISTRY.get(rule.id)
            if gens:
                res[rule.id] = gens[0]
        return res

    def syntax_check(self, source: str) -> tuple[bool, str | None]:
        """Check whether source is valid Java syntax.

        Verifies:
          1. Lexer produces zero ERROR tokens.
          2. Structure parser produces zero ERROR nodes.
          3. Optional tree-sitter-java validation if installed.
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

        # 3. Optional tree-sitter parse check (if installed)
        try:
            import tree_sitter_java as tsjava
            from tree_sitter import Language, Parser

            language = Language(tsjava.language())
            parser = Parser(language)
            ts_tree = parser.parse(source.encode("utf-8"))
            if ts_tree.root_node.has_error:
                return False, "Syntax error detected by tree-sitter-java"
        except (ImportError, Exception):
            pass
        return True, None

    def dangerous_apis(self) -> dict[str, str]:
        """Return mapping of dangerous Java APIs."""
        return JAVA_DANGEROUS_APIS
