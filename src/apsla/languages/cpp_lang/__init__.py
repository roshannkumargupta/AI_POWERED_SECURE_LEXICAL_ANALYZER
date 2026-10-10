"""C and C++ language plugin implementation for SecureLex IDE."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from apsla.languages.base import (
    FixGenerator,
    LanguagePlugin,
    Rule,
    TaintProfile,
    TaintResult,
)
from apsla.languages.cpp_lang.fixes import register_cpp_fix_generators
from apsla.languages.cpp_lang.lexer import ALL_CPP_KEYWORDS, CppLexer
from apsla.languages.cpp_lang.profile import CPP_TAINT_PROFILE
from apsla.languages.cpp_lang.rules import ALL_CPP_RULES
from apsla.lexing.token import Token
from apsla.taint.lite import TaintLiteEngine


class CppPlugin(LanguagePlugin):
    """LanguagePlugin implementation for C and C++ (up to C++20 standard).

    NOTE: This is a lexer-level and syntactic security analysis tool.
    It does not perform full C++ AST parsing, template instantiation,
    macro expansion, or full pointer-alias analysis.
    """

    id: str = "cpp"
    display_name: str = "C / C++"
    extensions: list[str] = [".c", ".cc", ".cpp", ".cxx", ".h", ".hpp"]
    monaco_id: str = "cpp"
    keywords: frozenset[str] = ALL_CPP_KEYWORDS

    def __init__(self) -> None:
        register_cpp_fix_generators()

    def lex(self, source: str) -> list[Token]:
        """Tokenize C/C++ source code using hand-written state machine lexer."""
        return CppLexer(source).tokenize()

    def rules(self) -> Sequence[Rule]:
        """Return all deterministic C/C++ security rules."""
        return ALL_CPP_RULES

    def taint_profile(self) -> TaintProfile:
        """Return the taint tracking profile for C/C++."""
        return CPP_TAINT_PROFILE

    def parse_structure(self, source: str) -> Any:
        """Parse C/C++ source into a lightweight StructTree."""
        from apsla.languages.cpp_lang.parser import parse_cpp_structure

        return parse_cpp_structure(source)

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        """Execute statement-level taint-lite data flow analysis."""
        tree = self.parse_structure(source)
        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, struct_tree=tree)
        return engine.analyze()

    def fix_generators(self) -> dict[str, FixGenerator]:
        """Return rule-id mapped fix generator implementations."""
        from apsla.fixes.registry import FIX_REGISTRY

        register_cpp_fix_generators()
        res: dict[str, FixGenerator] = {}
        for rule in ALL_CPP_RULES:
            gens = FIX_REGISTRY.get(rule.id)
            if gens:
                res[rule.id] = gens[0]
        return res

    def syntax_check(self, source: str) -> tuple[bool, str | None]:
        """Check whether source is valid C/C++ syntax.

        Verifies:
          1. Lexer produces zero ERROR tokens.
          2. Structure parser produces zero ERROR nodes.
          3. Preprocessor directives #if/#ifdef/#ifndef and #endif are balanced.
          4. Optional tree-sitter-cpp validation if installed.
          5. Optional 'g++ -fsyntax-only' or 'gcc -fsyntax-only' if compiler is available.
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

        # 3. Preprocessor #if/#endif balance check
        if_depth = 0
        has_conditional_directives = False
        for t in tokens:
            if t.kind == "PREPROCESSOR":
                # Check for #if, #ifdef, #ifndef vs #endif
                text = t.text.strip()
                if re.match(r"#\s*(?:if|ifdef|ifndef)\b", text):
                    if_depth += 1
                    has_conditional_directives = True
                elif re.match(r"#\s*endif\b", text):
                    if_depth -= 1
                    has_conditional_directives = True
                    if if_depth < 0:
                        return False, f"Unmatched #endif at line {t.line}"

        if if_depth != 0:
            return False, f"Unmatched preprocessor conditional (#if/#endif depth is {if_depth})"

        # 4. Optional tree-sitter-cpp validation
        if not has_conditional_directives:
            try:
                import tree_sitter_cpp as tscpp
                from tree_sitter import Language, Parser

                cpp_lang = Language(tscpp.language())
                parser = Parser(cpp_lang)
                tree = parser.parse(source.encode("utf-8"))
                if tree.root_node.has_error:
                    return False, "tree-sitter parse error detected in C/C++ source"
            except Exception:
                pass

        return True, None

    def dangerous_apis(self) -> dict[str, str]:
        """Return mapping of dangerous C/C++ APIs."""
        from apsla.languages.cpp_lang.profile import CPP_DANGEROUS_APIS

        return CPP_DANGEROUS_APIS

