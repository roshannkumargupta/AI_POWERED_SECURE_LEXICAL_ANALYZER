"""Java language plugin implementation for SecureLex IDE."""

from __future__ import annotations

from typing import Final

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

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        """Execute statement-level taint-lite data flow analysis."""
        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE)
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
          2. Delimiters (parentheses, braces, brackets) are balanced.
          3. Optional tree-sitter-java validation if installed.
        """
        tokens = self.lex(source)

        # 1. Lexical error check
        for t in tokens:
            if t.kind == "ERROR":
                return False, f"Lexical error: '{t.text}' at line {t.line}, col {t.col}"

        # 2. Balanced delimiters check
        delim_pairs = {")": "(", "}": "{", "]": "["}
        stack: list[tuple[str, int, int]] = []

        for t in tokens:
            if t.kind in ("COMMENT", "STRING", "CHAR"):
                continue
            if t.text in ("(", "{", "["):
                stack.append((t.text, t.line, t.col))
            elif t.text in (")", "}", "]"):
                expected_open = delim_pairs[t.text]
                if not stack:
                    return False, f"Unmatched closing delimiter '{t.text}' at line {t.line}"
                open_ch, open_line, _ = stack.pop()
                if open_ch != expected_open:
                    return (
                        False,
                        f"Mismatched delimiter: opened '{open_ch}' at line {open_line}, closed '{t.text}' at line {t.line}",
                    )

        if stack:
            unclosed_ch, unclosed_line, _ = stack[-1]
            return False, f"Unclosed delimiter '{unclosed_ch}' from line {unclosed_line}"

        # 3. Optional tree-sitter parse check (if installed)
        try:
            import tree_sitter_java as tsjava
            from tree_sitter import Language, Parser

            language = Language(tsjava.language())
            parser = Parser(language)
            tree = parser.parse(source.encode("utf-8"))
            if tree.root_node.has_error:
                return False, "Tree-sitter Java syntax error detected in source."
        except (ImportError, Exception):
            pass

        return True, None

    def dangerous_apis(self) -> dict[str, str]:
        """Return mapping of dangerous Java APIs."""
        return JAVA_DANGEROUS_APIS
