"""Deterministic Python security rules (AST and lexical inspection)."""

from __future__ import annotations

import ast
import math
from typing import Final

import regex

from apsla.models import Finding, Severity
from apsla.rules.base import Rule, RuleContext


# Helpers
def _is_constant_str(node: ast.AST) -> bool:
    """Check if AST node is a string constant literal."""
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _get_call_name(node: ast.Call) -> str:
    """Extract dotted or simple function name from an ast.Call node."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = []
        curr: ast.AST = func
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        return ".".join(reversed(parts))
    return ""


def _shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy in bits per character."""
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    length = len(s)
    return -sum((cnt / length) * math.log2(cnt / length) for cnt in freq.values())


def _is_built_string(node: ast.AST) -> bool:
    """Check if AST node is a dynamically constructed string (concatenation, f-string, or %/format)."""
    if isinstance(node, (ast.JoinedStr, ast.BinOp)):
        return True
    if isinstance(node, ast.Call):
        call_name = _get_call_name(node)
        if call_name.endswith(".format"):
            return True
    return False


def _has_sanitizer_call(node: ast.AST) -> bool:
    """Check if AST node contains a call to shlex.quote or similar sanitizer."""
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = _get_call_name(child)
            if "quote" in name or "secure_filename" in name or "basename" in name:
                return True
    return False


class EvalExecRule(Rule):
    """APS-PY-INJ-001: eval/exec on non-constant input."""

    id = "APS-PY-INJ-001"
    title = "Arbitrary Code Execution via eval/exec"
    cwe = "CWE-95"
    severity = Severity.HIGH
    category = "EVAL_INJECTION"
    description = "Dynamic evaluation of non-constant input allows arbitrary code execution."
    explanation = "Passing untrusted expressions or variables to eval() or exec() allows attackers to execute arbitrary system commands or Python code."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name in ("eval", "exec") and node.args:
                    arg = node.args[0]
                    # exec() is always dangerous; eval() is flagged on non-constant strings
                    if name == "exec" or not _is_constant_str(arg):
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message=f"Dynamic {name}() call allows arbitrary code execution",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class OsSystemRule(Rule):
    """APS-PY-INJ-002: os.system / os.popen with built string."""

    id = "APS-PY-INJ-002"
    title = "Command Injection via os.system/os.popen"
    cwe = "CWE-78"
    severity = Severity.HIGH
    category = "COMMAND_INJECTION"
    description = "Executing OS commands via string construction permits command injection."
    explanation = "os.system and os.popen spawn shell processes. Constructing commands with variables or dynamic formatting enables shell injection."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name in ("os.system", "os.popen") and node.args:
                    arg = node.args[0]
                    if _is_built_string(arg) and not _has_sanitizer_call(arg):
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message=f"Command injection risk in {name}() with dynamic built command",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class SubprocessShellRule(Rule):
    """APS-PY-INJ-003: subprocess with shell=True and non-constant command."""

    id = "APS-PY-INJ-003"
    title = "Command Injection via subprocess with shell=True"
    cwe = "CWE-78"
    severity = Severity.HIGH
    category = "COMMAND_INJECTION"
    description = "Invoking subprocess with shell=True allows command chaining and injection."
    explanation = "Using shell=True with dynamically constructed strings bypasses argument separation. Use a list of arguments without shell=True instead."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name.startswith("subprocess.") and node.args:
                    has_shell_true = False
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            has_shell_true = True
                            break

                    arg = node.args[0]
                    # List form without shell=True is SAFE
                    if has_shell_true and not _is_constant_str(arg):
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message=f"{name}() executed with shell=True and dynamic command",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class SqlInjectionRule(Rule):
    """APS-PY-INJ-004: SQL query built via string formatting or concatenation."""

    id = "APS-PY-INJ-004"
    title = "SQL Injection via Dynamic Query Construction"
    cwe = "CWE-89"
    severity = Severity.HIGH
    category = "SQL_INJECTION"
    description = "SQL queries built by string concatenation or formatting are vulnerable to SQL injection."
    explanation = "Always use parameterized queries with query parameters (e.g., execute(sql, params)) rather than embedding variables directly into SQL strings."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        dynamic_vars: set[str] = set()
        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Assign) and _is_built_string(node.value):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        dynamic_vars.add(t.id)

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if (name.endswith(".execute") or name.endswith(".executemany")) and node.args:
                    query_arg = node.args[0]
                    is_dynamic_sql = _is_built_string(query_arg) or (
                        isinstance(query_arg, ast.Name) and query_arg.id in dynamic_vars
                    )

                    if is_dynamic_sql:
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message="Dynamic SQL query passed to execute(); use parameterized queries",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class PickleDeserializationRule(Rule):
    """APS-PY-DES-001: Insecure deserialization via pickle, marshal, or shelve."""

    id = "APS-PY-DES-001"
    title = "Insecure Deserialization via pickle/marshal"
    cwe = "CWE-502"
    severity = Severity.HIGH
    category = "DESERIALIZATION"
    description = "Deserializing untrusted pickle, marshal, or shelve data allows remote code execution."
    explanation = "pickle and marshal are not secure against malicious data. Use safer serialization formats such as JSON or Protocol Buffers."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name in (
                    "pickle.loads", "pickle.load",
                    "_pickle.loads", "_pickle.load",
                    "marshal.loads", "marshal.load",
                    "shelve.open",
                ):
                    rng = context.node_to_range(node)
                    findings.append(
                        self.create_finding(
                            rng=rng,
                            message=f"Insecure deserialization using {name}()",
                            evidence={"call": name, "line": getattr(node, "lineno", 1)},
                        )
                    )
        return findings


class YamlDeserializationRule(Rule):
    """APS-PY-DES-002: Insecure YAML loading without SafeLoader."""

    id = "APS-PY-DES-002"
    title = "Insecure YAML Deserialization"
    cwe = "CWE-502"
    severity = Severity.HIGH
    category = "DESERIALIZATION"
    description = "yaml.load without SafeLoader allows arbitrary Python object instantiation."
    explanation = "Use yaml.safe_load() or specify Loader=yaml.SafeLoader to prevent executing arbitrary code during YAML parsing."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name == "yaml.unsafe_load":
                    rng = context.node_to_range(node)
                    findings.append(
                        self.create_finding(
                            rng=rng,
                            message="yaml.unsafe_load() called; use yaml.safe_load()",
                            evidence={"call": name, "line": getattr(node, "lineno", 1)},
                        )
                    )
                elif name == "yaml.load":
                    has_safe_loader = False
                    for kw in node.keywords:
                        if kw.arg == "Loader":
                            loader_name = ""
                            if isinstance(kw.value, ast.Name):
                                loader_name = kw.value.id
                            elif isinstance(kw.value, ast.Attribute):
                                loader_name = kw.value.attr
                            if "Safe" in loader_name or "CSafe" in loader_name:
                                has_safe_loader = True
                    if not has_safe_loader:
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message="yaml.load() without SafeLoader is vulnerable to code execution",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class WeakCryptoHashRule(Rule):
    """APS-PY-CRY-001: Use of broken or weak cryptographic hash (MD5, SHA1)."""

    id = "APS-PY-CRY-001"
    title = "Weak Cryptographic Hash Algorithm (MD5/SHA1)"
    cwe = "CWE-327"
    severity = Severity.MEDIUM
    category = "WEAK_CRYPTO"
    description = "MD5 and SHA-1 have known collision weaknesses and should not be used for security."
    explanation = "Replace MD5 and SHA-1 with modern collision-resistant cryptographic hashes such as SHA-256 or SHA-512."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                is_weak = False
                if name in ("hashlib.md5", "hashlib.sha1"):
                    is_weak = True
                elif name == "hashlib.new" and node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant) and str(first_arg.value).lower() in ("md5", "sha1"):
                        is_weak = True

                if is_weak:
                    # Check usedforsecurity=False exception
                    for kw in node.keywords:
                        if kw.arg == "usedforsecurity" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                            is_weak = False

                if is_weak:
                    rng = context.node_to_range(node)
                    findings.append(
                        self.create_finding(
                            rng=rng,
                            message=f"Weak hash algorithm detected: {name}()",
                            evidence={"call": name, "line": getattr(node, "lineno", 1)},
                        )
                    )
        return findings


class WeakRandomRule(Rule):
    """APS-PY-CRY-002: Insecure pseudo-random number generator used for security secrets."""

    id = "APS-PY-CRY-002"
    title = "Insecure Randomness for Security Tokens"
    cwe = "CWE-338"
    severity = Severity.MEDIUM
    category = "WEAK_CRYPTO"
    description = "standard random module is predictable and unsuitable for security tokens or keys."
    explanation = "Use the 'secrets' module (e.g. secrets.token_hex(), secrets.token_urlsafe()) for cryptographic keys and session tokens."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        sensitive_names = regex.compile(r"(?i)(token|secret|password|passwd|key|auth|session|nonce|salt)")

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Assign):
                target_is_sensitive = False
                for t in node.targets:
                    if isinstance(t, ast.Name) and sensitive_names.search(t.id):
                        target_is_sensitive = True
                        break

                if target_is_sensitive and isinstance(node.value, ast.Call):
                    call_name = _get_call_name(node.value)
                    if call_name.startswith("random."):
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message=f"Predictable random generator '{call_name}' assigned to sensitive variable",
                                evidence={"call": call_name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class HardcodedSecretRule(Rule):
    """APS-PY-SEC-001: Hard-coded credentials, passwords, or API keys."""

    id = "APS-PY-SEC-001"
    title = "Hard-coded Secret / Password / API Key"
    cwe = "CWE-798"
    severity = Severity.HIGH
    category = "HARDCODED_SECRET"
    description = "Hard-coding passwords or private API tokens in source code exposes credentials."
    explanation = "Load credentials dynamically from environment variables (os.environ) or a secure secrets vault rather than hard-coding."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        secret_var_re = regex.compile(r"(?i)(password|passwd|api_key|secret_key|auth_token|private_key|access_key)")
        placeholder_re = regex.compile(r"(?i)^(none|null|todo|test|example|changeme|default|secret|password)$")

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Assign):
                target_matches = False
                target_name = ""
                for t in node.targets:
                    if isinstance(t, ast.Name) and secret_var_re.search(t.id):
                        target_matches = True
                        target_name = t.id
                        break

                if target_matches and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    val = node.value.value
                    if len(val) >= 8 and not placeholder_re.match(val):
                        entropy = _shannon_entropy(val)
                        if entropy >= 2.8 or len(val) >= 20:
                            rng = context.node_to_range(node)
                            findings.append(
                                self.create_finding(
                                    rng=rng,
                                    message=f"Hard-coded credential detected in variable '{target_name}'",
                                    evidence={"variable": target_name, "entropy": round(entropy, 2)},
                                )
                            )
        return findings


class InsecureRequestsVerifyRule(Rule):
    """APS-PY-NET-001: Insecure HTTP requests with SSL certificate verification disabled."""

    id = "APS-PY-NET-001"
    title = "Disabled SSL/TLS Certificate Verification"
    cwe = "CWE-295"
    severity = Severity.MEDIUM
    category = "GENERIC"
    description = "Disabling SSL verification (verify=False) exposes HTTP requests to man-in-the-middle attacks."
    explanation = "Ensure verify=True (the default) is maintained so requests validate trusted CA certificates."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name.startswith("requests.") or name in ("get", "post", "put", "delete", "request"):
                    for kw in node.keywords:
                        if kw.arg == "verify" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                            rng = context.node_to_range(node)
                            findings.append(
                                self.create_finding(
                                    rng=rng,
                                    message=f"{name}() executed with verify=False",
                                    evidence={"call": name, "line": getattr(node, "lineno", 1)},
                                )
                            )
        return findings


class PathTraversalIoRule(Rule):
    """APS-PY-IO-001: Path traversal via open() or send_file with dynamic path."""

    id = "APS-PY-IO-001"
    title = "Potential Path Traversal via open()/send_file()"
    cwe = "CWE-22"
    severity = Severity.HIGH
    category = "PATH_TRAVERSAL"
    description = "Opening file paths without sanitization allows directory traversal attacks."
    explanation = "Use os.path.basename() or werkzeug.utils.secure_filename() to prevent '../' directory traversal."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name in ("open", "send_file", "flask.send_file") and node.args:
                    arg = node.args[0]
                    # Constant strings are safe; dynamic expressions or variables are risky
                    is_safe = _is_constant_str(arg)
                    if isinstance(arg, ast.Call):
                        inner_call = _get_call_name(arg)
                        if "basename" in inner_call or "secure_filename" in inner_call:
                            is_safe = True

                    if not is_safe:
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message=f"Dynamic path passed to {name}() without sanitization",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class DynamicImportRule(Rule):
    """APS-PY-INJ-005: Arbitrary code execution via dynamic import."""

    id = "APS-PY-INJ-005"
    title = "Dynamic Module Import via __import__/importlib"
    cwe = "CWE-94"
    severity = Severity.HIGH
    category = "CODE_INJECTION"
    description = "Importing modules dynamically based on user input allows arbitrary code execution."
    explanation = "Restrict dynamically imported modules to an explicit whitelist."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name in ("__import__", "importlib.import_module") and node.args:
                    arg = node.args[0]
                    if not _is_constant_str(arg):
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message=f"Dynamic {name}() on non-constant module name",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class ObfuscatedPayloadExecutionRule(Rule):
    """APS-PY-OBF-001: Execution of decoded payload (base64/zlib/hex)."""

    id = "APS-PY-OBF-001"
    title = "Execution of Decoded / Obfuscated Payload"
    cwe = "CWE-506"
    severity = Severity.CRITICAL
    category = "MALICIOUS_CODE"
    description = "Directly executing decoded base64, zlib, or hex streams is an obfuscated malware pattern."
    explanation = "Decompressing and immediately evaluating payloads with exec() or eval() is a primary indicator of encoded malware droppers."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        decoder_names = ("b64decode", "base64.b64decode", "zlib.decompress", "codecs.decode", "decode")

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name in ("exec", "eval") and node.args:
                    arg = node.args[0]
                    is_decoded = False
                    if isinstance(arg, ast.Call):
                        inner = _get_call_name(arg)
                        if any(d in inner for d in decoder_names):
                            is_decoded = True

                    if is_decoded:
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message=f"{name}() executing decoded/decompressed payload",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


class TemplateInjectionXssRule(Rule):
    """APS-PY-XSS-001: Server-side template injection or XSS via render_template_string/Markup."""

    id = "APS-PY-XSS-001"
    title = "Cross-Site Scripting / SSTI via Template String"
    cwe = "CWE-79"
    severity = Severity.HIGH
    category = "XSS"
    description = "Rendering dynamic templates or creating raw Markup from user data causes XSS or SSTI."
    explanation = "Use render_template() with static template files and automatic escaping, or Markup.escape() for dynamic content."

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        if context.ast_tree is None:
            return findings

        for node in ast.walk(context.ast_tree):
            if isinstance(node, ast.Call):
                name = _get_call_name(node)
                if name in ("render_template_string", "Markup", "markupsafe.Markup") and node.args:
                    arg = node.args[0]
                    # Dynamic expressions
                    if isinstance(arg, (ast.JoinedStr, ast.BinOp, ast.Name)):
                        rng = context.node_to_range(node)
                        findings.append(
                            self.create_finding(
                                rng=rng,
                                message=f"Dynamic string passed to {name}() without sanitization",
                                evidence={"call": name, "line": getattr(node, "lineno", 1)},
                            )
                        )
        return findings


ALL_PYTHON_RULES: Final[list[Rule]] = [
    EvalExecRule(),
    OsSystemRule(),
    SubprocessShellRule(),
    SqlInjectionRule(),
    PickleDeserializationRule(),
    YamlDeserializationRule(),
    WeakCryptoHashRule(),
    WeakRandomRule(),
    HardcodedSecretRule(),
    InsecureRequestsVerifyRule(),
    PathTraversalIoRule(),
    DynamicImportRule(),
    ObfuscatedPayloadExecutionRule(),
    TemplateInjectionXssRule(),
]
