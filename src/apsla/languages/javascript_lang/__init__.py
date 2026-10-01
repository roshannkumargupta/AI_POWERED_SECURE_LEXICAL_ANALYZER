"""JavaScript language plugin implementation for SecureLex IDE."""

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

    def rules(self) -> list[Rule]:
        """Return all deterministic JavaScript security rules."""
        return ALL_JAVASCRIPT_RULES

    def taint_profile(self) -> TaintProfile:
        """Return the taint tracking profile for JavaScript."""
        return JS_TAINT_PROFILE

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        """Execute statement-level taint-lite data flow analysis."""
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE)
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
          2. Delimiters (parentheses, braces, brackets) are balanced.
          3. Optional tree-sitter-javascript validation if installed.
          4. Optional 'node --check' validation if node is available and not JSX.
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
            if t.kind in ("COMMENT", "STRING", "REGEX"):
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

        # 4. Optional node --check validation on temp file (skip silently when node is missing or on JSX)
        has_jsx = "</" in source or bool(re.search(r"<[A-Za-z0-9_]+(?:\s+[^>]*?)?\/?>", source))
        if not has_jsx and shutil.which("node"):
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
                    tmp.write(source)
                    tmp_path = tmp.name
                try:
                    res = subprocess.run(
                        ["node", "--check", tmp_path],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if res.returncode != 0:
                        err_msg = res.stderr.strip() or "Node.js syntax error"
                        # Skip ESM module declaration warnings on standalone files
                        if (
                            "Cannot use import statement outside a module" not in err_msg
                            and "Unexpected token 'export'" not in err_msg
                        ):
                            return False, f"Node.js syntax error: {err_msg}"
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

        return True, None

    def dangerous_apis(self) -> dict[str, str]:
        """Return mapping of dangerous JavaScript APIs."""
        return JS_DANGEROUS_APIS
