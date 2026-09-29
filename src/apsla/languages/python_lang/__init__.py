"""Python language plugin implementation for SecureLex IDE."""

from __future__ import annotations

import ast
from typing import Final

from apsla.languages.base import (
    FixGenerator,
    LanguagePlugin,
    Rule,
    TaintProfile,
    TaintResult,
)
from apsla.languages.python_lang.lexer import PYTHON_KEYWORDS, PythonLexer
from apsla.languages.python_lang.rules import ALL_PYTHON_RULES
from apsla.languages.python_lang.taint import PythonTaintAnalyzer
from apsla.lexing.token import Token
from apsla.rules.base import RuleContext

PYTHON_DANGEROUS_APIS: Final[dict[str, str]] = {
    "eval": "Dynamic code evaluation (CWE-95)",
    "exec": "Dynamic code execution (CWE-95)",
    "os.system": "Command injection via shell execution (CWE-78)",
    "os.popen": "Command injection via pipe execution (CWE-78)",
    "subprocess.Popen": "Subprocess execution risk (CWE-78)",
    "subprocess.call": "Subprocess execution risk (CWE-78)",
    "subprocess.run": "Subprocess execution risk (CWE-78)",
    "pickle.loads": "Arbitrary object deserialization (CWE-502)",
    "yaml.load": "Unsafe YAML deserialization without SafeLoader (CWE-502)",
    "hashlib.md5": "Broken cryptographic hash (CWE-327)",
    "hashlib.sha1": "Broken cryptographic hash (CWE-327)",
}


class PythonPlugin(LanguagePlugin):
    """LanguagePlugin implementation for Python source files."""

    id: str = "python"
    display_name: str = "Python"
    extensions: list[str] = [".py", ".pyw"]
    monaco_id: str = "python"
    keywords: frozenset[str] = PYTHON_KEYWORDS

    def lex(self, source: str) -> list[Token]:
        """Tokenize Python source using hand-written state machine lexer."""
        return PythonLexer(source).tokenize()

    def rules(self) -> list[Rule]:
        """Return all deterministic Python security rules."""
        return ALL_PYTHON_RULES

    def taint_profile(self) -> TaintProfile:
        """Return taint tracking profile for Python."""
        return TaintProfile(
            language="python",
            sources=frozenset({
                "input",
                "sys.argv",
                "os.environ",
                "os.getenv",
                "sys.stdin.read",
                "sys.stdin.readline",
                "request.args",
                "request.form",
                "request.values",
                "request.json",
                "request.data",
                "request.cookies",
                "request.headers",
                "request.GET",
                "request.POST",
                "socket.recv",
            }),
            sinks=frozenset({
                "eval",
                "exec",
                "os.system",
                "os.popen",
                "subprocess.run",
                "subprocess.Popen",
                "subprocess.call",
                "cursor.execute",
                "pickle.loads",
                "yaml.load",
                "open",
                "send_file",
                "render_template_string",
            }),
            sanitizers=frozenset({
                "shlex.quote",
                "int",
                "float",
                "html.escape",
                "markupsafe.escape",
                "os.path.basename",
                "werkzeug.utils.secure_filename",
            }),
            dangerous_apis=PYTHON_DANGEROUS_APIS,
        )

    def analyze_taint(self, source: str, tokens: list[Token]) -> list[TaintResult]:
        """Perform AST flow-sensitive taint tracking."""
        from apsla.lexing.common import OffsetMap
        from apsla.unicode_defense.recovery import recover_text

        offset_map = OffsetMap(source)
        rec = recover_text(source, offset_map)
        try:
            tree = ast.parse(rec.recovered_text)
        except SyntaxError:
            return []

        ctx = RuleContext(
            raw_source=source,
            recovered_source=rec.recovered_text,
            tokens=tokens,
            ast_tree=tree,
            offset_map=offset_map,
            recovery=rec,
        )
        taint_res = PythonTaintAnalyzer(ctx).analyze()
        # Adapt internal TaintResult flows to list of base TaintResult
        results: list[TaintResult] = []
        for flow in taint_res.flows:
            if not flow.sanitized:
                results.append(
                    TaintResult(
                        rule_id=flow.rule_id,
                        title="Taint Confirmed Vulnerability",
                        cwe="",
                        severity=ALL_PYTHON_RULES[0].severity,
                        range=flow.sink_range,
                        source_text="",
                        sink_text="",
                        path=flow.path,
                        message=flow.message,
                    )
                )
        return results

    def fix_generators(self) -> dict[str, FixGenerator]:
        """Return rule-id mapped fix generator implementations."""
        from apsla.fixes.registry import FIX_REGISTRY
        from apsla.languages.python_lang.fixes import register_python_fix_generators

        register_python_fix_generators()
        res: dict[str, FixGenerator] = {}
        for rule in ALL_PYTHON_RULES:
            gens = FIX_REGISTRY.get(rule.id)
            if gens:
                res[rule.id] = gens[0]
        return res

    def syntax_check(self, source: str) -> tuple[bool, str | None]:
        """Check whether source is valid Python syntax."""
        try:
            ast.parse(source)
            return (True, None)
        except SyntaxError as exc:
            return (False, str(exc))

    def dangerous_apis(self) -> dict[str, str]:
        """Return mapping of dangerous Python APIs."""
        return PYTHON_DANGEROUS_APIS
