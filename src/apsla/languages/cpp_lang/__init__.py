"""C and C++ language plugin implementation for SecureLex IDE."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Final

from apsla.languages.base import (
    FixGenerator,
    LanguagePlugin,
    Rule,
    TaintProfile,
    TaintResult,
)
from apsla.languages.cpp_lang.fixes import register_cpp_fix_generators
from apsla.languages.cpp_lang.lexer import ALL_CPP_KEYWORDS, CppLexer
from apsla.languages.cpp_lang.profile import (
    CPP_DANGEROUS_APIS,
    CPP_TAINT_PROFILE,
)
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

    def rules(self) -> list[Rule]:
        """Return all deterministic C/C++ security rules."""
        return ALL_CPP_RULES

    def taint_profile(self) -> TaintProfile:
        """Return the taint tracking profile for C/C++."""
        return CPP_TAINT_PROFILE

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        """Execute statement-level taint-lite data flow analysis."""
        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE)
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
          2. Delimiters (parentheses, braces, brackets) are balanced.
          3. Preprocessor directives #if/#ifdef/#ifndef and #endif are balanced.
          4. Optional tree-sitter-cpp validation if installed.
          5. Optional 'g++ -fsyntax-only' or 'gcc -fsyntax-only' if compiler is available.
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
            if t.kind in ("COMMENT", "STRING", "RAW_STRING", "CHAR", "PREPROCESSOR"):
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
                        f"Mismatched delimiter: opened '{open_ch}' at line {open_line}, "
                        f"closed '{t.text}' at line {t.line}",
                    )

        if stack:
            open_ch, open_line, open_col = stack[-1]
            return False, f"Unclosed delimiter '{open_ch}' opened at line {open_line}, col {open_col}"

        # 3. Preprocessor #if/#endif balance check
        if_depth = 0
        for t in tokens:
            if t.kind == "PREPROCESSOR":
                # Check for #if, #ifdef, #ifndef vs #endif
                text = t.text.strip()
                if re.match(r"#\s*(?:if|ifdef|ifndef)\b", text):
                    if_depth += 1
                elif re.match(r"#\s*endif\b", text):
                    if_depth -= 1
                    if if_depth < 0:
                        return False, f"Unmatched #endif at line {t.line}"

        if if_depth != 0:
            return False, f"Unmatched preprocessor conditional (#if/#endif depth is {if_depth})"

        # 4. Optional tree-sitter-cpp validation
        try:
            import tree_sitter_cpp as tscpp
            from tree_sitter import Language, Parser

            cpp_lang = Language(tscpp.language())
            parser = Parser(cpp_lang)
            tree = parser.parse(source.encode("utf-8"))
            if tree.root_node.has_error:
                return False, "tree-sitter parse error detected in C/C++ source"
        except (ImportError, Exception):
            pass

        # 5. Optional compiler syntax-only check (skip silently if compiler not found)
        compiler = shutil.which("g++") or shutil.which("gcc")
        if compiler:
            try:
                with tempfile.NamedTemporaryFile(suffix=".cpp", mode="w", encoding="utf-8", delete=False) as tf:
                    tf.write(source)
                    temp_path = tf.name
                try:
                    res = subprocess.run(
                        [compiler, "-fsyntax-only", "-x", "c++", temp_path],
                        capture_output=True,
                        text=True,
                        timeout=3.0,
                    )
                    # Note: missing headers or unknown libraries are expected in snippets,
                    # so only report syntax errors if obvious
                    if res.returncode != 0:
                        err_out = res.stderr.lower()
                        if "syntax error" in err_out or "expected" in err_out:
                            return False, f"Compiler syntax check error: {res.stderr.strip()[:200]}"
                finally:
                    Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass

        return True, None
