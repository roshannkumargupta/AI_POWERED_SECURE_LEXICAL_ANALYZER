"""Deterministic JavaScript security rules evaluating AST, token stream, and taint flows."""

from __future__ import annotations

import math
import re
from typing import Final

from apsla.languages.javascript_lang.profile import JS_TAINT_PROFILE
from apsla.lexing.token import Token
from apsla.models import Finding, Range, Severity
from apsla.rules.base import Rule, RuleContext
from apsla.taint.lite import TaintLiteEngine


def _shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy in bits per character."""
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    length = len(s)
    return -sum((cnt / length) * math.log2(cnt / length) for cnt in freq.values())


def _is_inside_comment_or_string(pos: int, tokens: list[Token]) -> bool:
    """Check if character index is strictly inside a comment or string token."""
    for tok in tokens:
        if tok.start <= pos < tok.end:
            return tok.kind in ("COMMENT", "STRING")
    return False


def _is_inside_comment(pos: int, tokens: list[Token]) -> bool:
    """Check if character index is inside a comment."""
    for tok in tokens:
        if tok.start <= pos < tok.end:
            return tok.kind == "COMMENT"
    return False


def _get_non_trivia_tokens(tokens: list[Token]) -> list[Token]:
    """Filter out whitespace and comment tokens."""
    return [t for t in tokens if t.kind not in ("WHITESPACE", "COMMENT")]


# ── Rule 1: Code Injection (CWE-95) ──────────────────────────────────────────


class JSCodeInjectionRule(Rule):
    """Detects dynamic code evaluation via eval(), Function(), or string setTimeout/setInterval."""

    id = "APS-JS-INJ-001"
    title = "Code Injection via Dynamic Evaluation (eval / Function / setTimeout)"
    cwe = "CWE-95"
    severity = Severity.CRITICAL
    category = "injection"
    description = "Dynamic evaluation of untrusted strings enables arbitrary code execution."
    explanation = (
        "Invoking eval(), new Function(), or passing a string argument to setTimeout() / setInterval() "
        "executes dynamic code with full privileges of the JavaScript runtime. If influenced by untrusted data, "
        "attackers can execute arbitrary JavaScript commands."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for eval(...) or new Function(...)
        eval_pattern = re.compile(
            r"\b(?:eval|new\s+Function|Function)\s*\(\s*([^;)]+)\s*\)", re.MULTILINE
        )
        for m in eval_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            arg = m.group(1).strip()
            # If JSON.parse is used or pure static number/boolean, skip
            if arg.startswith("JSON.parse") or arg in ("true", "false", "null", "undefined"):
                continue
            # Obfuscation patterns are specifically handled by APS-JS-OBF-001
            if any(obf in arg for obf in ("atob", "String.fromCharCode", "Buffer.from")):
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message=f"Dynamic code evaluation via {m.group(0).split('(')[0].strip()}() detected.",
                        evidence={"call": m.group(0), "taint_confirmed": False},
                    )
                )

        # 3. Syntactic inspection for setTimeout / setInterval with string concatenation or template literal
        timer_pattern = re.compile(
            r"\bset(?:Timeout|Interval)\s*\(\s*(?:([\"'`][^\"'`]*[\"'`]\s*\+)|`[^`]*\${)",
            re.MULTILINE,
        )
        for m in timer_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message="String-based timer evaluation behaves like eval() and executes dynamic code.",
                        evidence={"timer_call": m.group(0), "taint_confirmed": False},
                    )
                )

        return findings


# ── Rule 2: Command Injection (CWE-78) ────────────────────────────────────────


class JSCommandInjectionRule(Rule):
    """Detects OS command execution via child_process.exec, execSync, or spawn with shell: true."""

    id = "APS-JS-INJ-002"
    title = "Command Injection via child_process Execution"
    cwe = "CWE-78"
    severity = Severity.CRITICAL
    category = "injection"
    description = (
        "Executing OS commands with dynamic string concatenation allows arbitrary shell execution."
    )
    explanation = (
        "Invoking child_process.exec(), execSync(), or spawn() with shell: true using concatenated strings "
        "or tainted parameters permits command injection. Attackers can append shell metacharacters (&, |, ;) "
        "to run unauthorized commands."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for exec / execSync call with concatenation or template literal
        exec_pattern = re.compile(
            r"\b(?:child_process\.)?(?:exec|execSync)\s*\(\s*([^,;)]+)",
            re.MULTILINE,
        )
        for m in exec_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            arg = m.group(1).strip()
            # If string concatenation or template literal with interpolation is used
            is_dynamic = (
                (
                    "+" in arg
                    and not re.fullmatch(r'["\'][^"\']*["\']\s*\+\s*["\'][^"\']*["\']', arg)
                )
                or ("`" in arg and "${" in arg)
                or (
                    re.search(r"\b[A-Za-z0-9_]+\b", arg)
                    and not re.fullmatch(r'["\'][^"\']*["\']', arg)
                )
            )

            if is_dynamic:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                if not any(f.range.start_line == line for f in findings):
                    findings.append(
                        self.create_finding(
                            rng=Range(
                                start_line=line, start_col=col, end_line=end_line, end_col=end_col
                            ),
                            message="OS command execution with dynamic argument enables command injection.",
                            evidence={"exec_call": m.group(0), "taint_confirmed": False},
                        )
                    )

        # 3. Syntactic inspection for spawn with shell: true
        spawn_pattern = re.compile(
            r"\b(?:child_process\.)?spawn\s*\([^;)]*shell\s*:\s*true",
            re.MULTILINE,
        )
        for m in spawn_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message="child_process.spawn invoked with shell: true enables command injection.",
                        evidence={"spawn_call": m.group(0), "taint_confirmed": False},
                    )
                )

        return findings


# ── Rule 3: DOM Cross-Site Scripting (CWE-79) ────────────────────────────────


class JSDOMXSSRule(Rule):
    """Detects DOM-based Cross-Site Scripting via innerHTML, outerHTML, or document.write."""

    id = "APS-JS-XSS-001"
    title = "DOM Cross-Site Scripting (XSS) via HTML Insertion"
    cwe = "CWE-79"
    severity = Severity.HIGH
    category = "xss"
    description = "Assigning unescaped or tainted data to innerHTML or document.write causes XSS."
    explanation = (
        "Writing untrusted data directly to innerHTML, outerHTML, insertAdjacentHTML, or document.write() "
        "causes the browser to parse and execute embedded script tags and event handlers. Use textContent "
        "or sanitize data using DOMPurify."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for innerHTML / outerHTML assignment without sanitizer
        sink_pattern = re.compile(
            r"([A-Za-z0-9_$.]+)\s*\.\s*(?:innerHTML|outerHTML)\s*=\s*([^;]+)",
            re.MULTILINE,
        )
        for m in sink_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            rhs = m.group(2).strip()
            # If wrapped with DOMPurify.sanitize or escapeHtml, safe
            if "DOMPurify.sanitize" in rhs or "escapeHtml" in rhs or "validator.escape" in rhs:
                continue
            # If pure string constant without HTML or simple constant
            if re.fullmatch(r'["\'][^<>&"\'`]*["\']', rhs):
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message=f"Unsanitized assignment to {m.group(1)}.{m.group(0).split('=')[0].split('.')[-1].strip()} enables DOM XSS.",
                        evidence={"sink": m.group(0), "taint_confirmed": False},
                    )
                )

        # 3. document.write / document.writeln with dynamic data
        doc_write_pattern = re.compile(
            r"\bdocument\.(?:write|writeln)\s*\(\s*([^;)]+)\s*\)", re.MULTILINE
        )
        for m in doc_write_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            arg = m.group(1).strip()
            if "DOMPurify.sanitize" in arg or "escapeHtml" in arg:
                continue
            if re.fullmatch(r'["\'][^<>&"\'`]*["\']', arg):
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message="document.write() with dynamic content enables DOM Cross-Site Scripting.",
                        evidence={"write_call": m.group(0), "taint_confirmed": False},
                    )
                )

        return findings


# ── Rule 4: React dangerouslySetInnerHTML (CWE-79) ───────────────────────────


class JSReactXSSRule(Rule):
    """Detects React dangerouslySetInnerHTML usage without DOMPurify sanitization."""

    id = "APS-JS-XSS-002"
    title = "React XSS via dangerouslySetInnerHTML"
    cwe = "CWE-79"
    severity = Severity.HIGH
    category = "xss"
    description = "Rendering raw HTML via dangerouslySetInnerHTML without sanitization allows XSS."
    explanation = (
        "In React applications, dangerouslySetInnerHTML bypasses JSX automatic string escaping. "
        "If untrusted data is provided to __html without passing through DOMPurify.sanitize(), "
        "attackers can inject executable script payloads into the DOM."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Pattern: dangerouslySetInnerHTML={{ __html: value }}
        pattern = re.compile(
            r"dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:\s*([^}]+)\}\s*\}",
            re.MULTILINE,
        )
        for m in pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            html_val = m.group(1).strip()
            # If sanitized with DOMPurify.sanitize, safe!
            if "DOMPurify.sanitize" in html_val or "sanitizeHtml" in html_val:
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message="dangerouslySetInnerHTML without DOMPurify sanitization enables XSS.",
                    evidence={"prop": m.group(0), "html_expr": html_val},
                )
            )

        return findings


# ── Rule 5: Open Redirect / Insecure Attribute Injection (CWE-601) ───────────


class JSOpenRedirectRule(Rule):
    """Detects client-side open redirect or inline event attribute injection."""

    id = "APS-JS-NET-001"
    title = "Client-Side Open Redirect or Event Handler Injection"
    cwe = "CWE-601"
    severity = Severity.MEDIUM
    category = "network"
    description = "Assigning untrusted data to location.href or setAttribute('on...') enables redirection or XSS."
    explanation = (
        "Redirecting users based on untrusted parameters (such as location.hash, search params, or query string) "
        "enables phishing attacks. Setting attributes starting with 'on' (e.g. onclick, onerror) with tainted data "
        "allows event-based script execution."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for location assignment with tainted-looking identifiers
        loc_pattern = re.compile(
            r"(?:window\.)?location(?:\.href)?\s*=\s*([^;]+)",
            re.MULTILINE,
        )
        for m in loc_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            rhs = m.group(1).strip()
            # If static string literal or relative path, safe
            if re.fullmatch(r'["\'][^"\']*["\']', rhs):
                continue
            # If encodeURIComponent, URL validation, or whitelist is applied
            if "encodeURIComponent" in rhs or "isValidUrl" in rhs or "whitelist" in source.lower():
                continue
            # Check if variable was assigned a relative path constant (e.g. '/dashboard')
            if re.search(rf"\b(?:const|let|var)\s+{re.escape(rhs)}\s*=\s*['\"]/", source):
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message="Dynamic URL redirection via location assignment enables open redirect attacks.",
                        evidence={"assignment": m.group(0), "taint_confirmed": False},
                    )
                )

        # 3. setAttribute with 'on' event handler
        attr_pattern = re.compile(
            r"\.setAttribute\s*\(\s*[\"']on[a-zA-Z]+[\"']\s*,\s*([^;)]+)\s*\)",
            re.MULTILINE,
        )
        for m in attr_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message="Inline event attribute assigned via setAttribute enables script execution.",
                        evidence={"call": m.group(0), "taint_confirmed": False},
                    )
                )

        return findings


# ── Rule 6: SQL Injection (CWE-89) ───────────────────────────────────────────


class JSSQLInjectionRule(Rule):
    """Detects SQL injection via string concatenation or unparameterized template literals."""

    id = "APS-JS-INJ-003"
    title = "SQL Injection via Concatenation or Template Literal"
    cwe = "CWE-89"
    severity = Severity.CRITICAL
    category = "injection"
    description = "Constructing SQL queries via string concatenation or template interpolation enables SQL injection."
    explanation = (
        "Building database queries via string concatenation (+) or template literals (${...}) allows attackers "
        "to break out of SQL string literals and manipulate the query structure. Always use parameterized queries "
        "with placeholders (? or $1) and a parameter list."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for query / execute / raw with concatenation or template literal
        query_pattern = re.compile(
            r"\b(?:db|connection|pool|client|sequelize|knex)\.(?:query|execute|raw)\s*\(\s*([^,;)]+)",
            re.MULTILINE,
        )
        for m in query_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            arg = m.group(1).strip()
            # If parameterized placeholders are used (?, $1) and arguments array follows, safe!
            full_call = (
                source[m.start() : source.find(")", m.start()) + 1]
                if ")" in source[m.start() :]
                else ""
            )
            if ("?" in arg or "$1" in arg) and ("[" in full_call or "," in full_call):
                continue

            # Template literal check: `SELECT ... ${var}`
            has_template_injection = "`" in arg and "${" in arg
            # String concatenation check: "SELECT ... " + var
            has_concat_injection = "+" in arg and not re.fullmatch(
                r'["\'][^"\']*["\']\s*\+\s*["\'][^"\']*["\']', arg
            )

            if has_template_injection or has_concat_injection:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                if not any(f.range.start_line == line for f in findings):
                    findings.append(
                        self.create_finding(
                            rng=Range(
                                start_line=line, start_col=col, end_line=end_line, end_col=end_col
                            ),
                            message="SQL query built with string concatenation or template literal enables SQL injection.",
                            evidence={"query_call": m.group(0), "taint_confirmed": False},
                        )
                    )

        return findings


# ── Rule 7: Path Traversal (CWE-22) ──────────────────────────────────────────


class JSPathTraversalRule(Rule):
    """Detects file system access with unvalidated or concatenated path parameters."""

    id = "APS-JS-IO-001"
    title = "Path Traversal via File System API"
    cwe = "CWE-22"
    severity = Severity.HIGH
    category = "io"
    description = "Reading or serving files using tainted paths allows arbitrary file access."
    explanation = (
        "Passing unvalidated user inputs or concatenated paths to fs.readFile(), fs.readFileSync(), "
        "fs.createReadStream(), or res.sendFile() enables directory traversal via '../' sequences. "
        "Sanitize paths with path.basename() or validate against a strict whitelist."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for fs.readFile / res.sendFile with concat/template literal without path.basename
        fs_pattern = re.compile(
            r"\b(?:fs\.(?:readFile|readFileSync|createReadStream)|(?:res|response)\.sendFile)\s*\(\s*([^,;)]+)",
            re.MULTILINE,
        )
        for m in fs_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            arg = m.group(1).strip()
            if "path.basename" in arg:
                continue
            if re.fullmatch(r'["\'][^"\']*["\']', arg):
                continue

            has_concat = "+" in arg and not re.fullmatch(
                r'["\'][^"\']*["\']\s*\+\s*["\'][^"\']*["\']', arg
            )
            has_template = "`" in arg and "${" in arg

            if has_concat or has_template:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                if not any(f.range.start_line == line for f in findings):
                    findings.append(
                        self.create_finding(
                            rng=Range(
                                start_line=line, start_col=col, end_line=end_line, end_col=end_col
                            ),
                            message="File system operation with dynamic path parameter enables directory traversal.",
                            evidence={"fs_call": m.group(0), "taint_confirmed": False},
                        )
                    )

        return findings


# ── Rule 8: Server-Side Request Forgery / SSRF (CWE-918) ──────────────────────


class JSSSRFRule(Rule):
    """Detects server-side HTTP requests using untrusted or dynamic URLs."""

    id = "APS-JS-NET-002"
    title = "Server-Side Request Forgery (SSRF) via HTTP Client"
    cwe = "CWE-918"
    severity = Severity.HIGH
    category = "network"
    description = "Performing backend HTTP requests to user-supplied URLs risks SSRF attacks."
    explanation = (
        "Server-side calls to axios, fetch, or http.get() using user-controlled parameters enable attackers "
        "to probe internal network services, cloud metadata endpoints (e.g. 169.254.169.254), or bypass firewalls. "
        "Validate target URLs against an explicit domain allowlist."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for axios/fetch/http.get with non-constant URL
        ssrf_pattern = re.compile(
            r"\b(?:axios(?:\.get|\.post)?|fetch|http\.get|https\.get)\s*\(\s*([^,;)]+)",
            re.MULTILINE,
        )
        for m in ssrf_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            arg = m.group(1).strip()
            # If pure string constant or whitelisted function, skip
            if (
                re.fullmatch(r'["\'][^"\']*["\']', arg)
                or "isAllowedDomain" in arg
                or "ALLOWED_HOSTS" in source
            ):
                continue

            has_concat = "+" in arg and not re.fullmatch(
                r'["\'][^"\']*["\']\s*\+\s*["\'][^"\']*["\']', arg
            )
            has_template = "`" in arg and "${" in arg
            is_var = re.fullmatch(r"[A-Za-z0-9_$.]+", arg) is not None

            if has_concat or has_template or is_var:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                if not any(f.range.start_line == line for f in findings):
                    findings.append(
                        self.create_finding(
                            rng=Range(
                                start_line=line, start_col=col, end_line=end_line, end_col=end_col
                            ),
                            message="Backend HTTP request using dynamic URL parameter enables SSRF.",
                            evidence={"http_call": m.group(0), "taint_confirmed": False},
                        )
                    )

        return findings


# ── Rule 9: Insecure Randomness (CWE-338) ────────────────────────────────────


class JSInsecureRandomnessRule(Rule):
    """Detects Math.random() used in security-sensitive contexts (tokens, keys, IDs)."""

    id = "APS-JS-CRY-001"
    title = "Insecure Pseudo-Random Number Generation (Math.random)"
    cwe = "CWE-338"
    severity = Severity.MEDIUM
    category = "crypto"
    description = "Math.random() is cryptographically weak and predictable."
    explanation = (
        "Math.random() uses a predictable pseudo-random number generator (xorshift128+) that can be reverse-engineered "
        "after observing a sequence of outputs. For tokens, session identifiers, passwords, or encryption keys, "
        "use crypto.randomUUID() or crypto.randomBytes()."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pattern = re.compile(r"\bMath\.random\s*\(\s*\)", re.MULTILINE)
        for m in pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue

            # Check context line for token/key/id/secret/auth words
            line_start = source.rfind("\n", 0, m.start()) + 1
            line_end = source.find("\n", m.end())
            if line_end == -1:
                line_end = len(source)
            line_str = source[line_start:line_end].lower()

            sec_keywords = (
                "token",
                "session",
                "key",
                "secret",
                "auth",
                "password",
                "id",
                "nonce",
                "salt",
            )
            if any(kw in line_str for kw in sec_keywords):
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message="Math.random() used to generate security-sensitive tokens or identifiers.",
                        evidence={"matched": m.group(0), "context_line": line_str.strip()},
                    )
                )

        return findings


# ── Rule 10: Broken Cryptographic Hash (CWE-327) ─────────────────────────────


class JSWeakHashRule(Rule):
    """Detects usage of broken hash algorithms (MD5 or SHA1)."""

    id = "APS-JS-CRY-002"
    title = "Broken Cryptographic Hash Algorithm (MD5 / SHA1)"
    cwe = "CWE-327"
    severity = Severity.HIGH
    category = "crypto"
    description = "MD5 and SHA-1 suffer from collision and preimage vulnerabilities."
    explanation = (
        "The MD5 and SHA-1 hashing algorithms are cryptographically broken due to practical collision attacks. "
        "Do not use them for digital signatures, password hashing, or integrity verification. Use SHA-256 (sha256) "
        "or secure password hashing functions like bcrypt or argon2."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pattern = re.compile(
            r"\b(?:crypto\.)?createHash\s*\(\s*[\"'](md5|sha1)[\"']\s*\)",
            re.IGNORECASE | re.MULTILINE,
        )
        for m in pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            algo = m.group(1).upper()
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message=f"Insecure cryptographic hash algorithm {algo} detected.",
                    evidence={"algorithm": algo, "call": m.group(0)},
                )
            )

        return findings


# ── Rule 11: Hard-Coded Secrets (CWE-798) ────────────────────────────────────


class JSHardcodedSecretsRule(Rule):
    """Detects high-entropy hard-coded secrets, tokens, and credentials in source code."""

    id = "APS-JS-SEC-001"
    title = "Hard-Coded Secret or API Key"
    cwe = "CWE-798"
    severity = Severity.HIGH
    category = "secrets"
    description = "Hard-coded credentials stored in source code risk unauthorized access."
    explanation = (
        "Embedding secrets, API keys, private tokens, or database passwords in source code exposes credentials "
        "to version control history, package artifacts, and unauthorized developers. Move credentials into "
        "environment variables (process.env) or a secret manager."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pattern = re.compile(
            r"\b(?:const|let|var)\s+([A-Za-z0-9_]*(?:secret|api_key|apikey|token|password|jwt_secret)[A-Za-z0-9_]*)\s*=\s*[\"']([^\"']{8,})[\"']",
            re.IGNORECASE | re.MULTILINE,
        )
        for m in pattern.finditer(source):
            if _is_inside_comment(m.start(), tokens):
                continue
            var_name = m.group(1)
            secret_val = m.group(2)

            # Skip obvious placeholders
            if any(
                ph in secret_val.lower()
                for ph in ("your_", "placeholder", "xxx", "todo", "sample", "test")
            ):
                continue
            # Entropy check
            if len(secret_val) >= 8 and _shannon_entropy(secret_val) >= 3.0:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message=f"Hard-coded secret detected in variable '{var_name}'.",
                        evidence={"variable": var_name, "entropy": _shannon_entropy(secret_val)},
                    )
                )

        return findings


# ── Rule 12: Insecure JWT Verification (CWE-347) ─────────────────────────────


class JSInsecureJWTRule(Rule):
    """Detects jwt.verify configured with 'none' algorithm or jwt.decode used for auth."""

    id = "APS-JS-SEC-002"
    title = "Insecure JWT Verification / Unverified Token Decoding"
    cwe = "CWE-347"
    severity = Severity.CRITICAL
    category = "secrets"
    description = (
        "Allowing 'none' algorithm or decoding tokens without verification bypasses authentication."
    )
    explanation = (
        "Configuring jwt.verify() to accept the 'none' algorithm or using jwt.decode() directly for authorization "
        "decisions allows attackers to forge arbitrary tokens with forged administrative claims without knowing "
        "the signing key. Always specify trusted algorithms (e.g. HS256, RS256)."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Check jwt.verify with algorithms: ['none']
        none_pattern = re.compile(
            r"\bjwt\.verify\s*\([^;)]*algorithms\s*:\s*\[[^\]]*[\"']none[\"'][^\]]*\]",
            re.IGNORECASE | re.MULTILINE,
        )
        for m in none_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message="jwt.verify configured with insecure 'none' algorithm.",
                    evidence={"call": m.group(0)},
                )
            )

        # Check jwt.decode used in authorization/role logic
        decode_pattern = re.compile(
            r"\b(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*jwt\.decode\s*\(",
            re.MULTILINE,
        )
        for m in decode_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            var_name = m.group(1)
            # If the decoded variable is later checked for role/admin/user, flag it
            if re.search(
                rf"\b{re.escape(var_name)}\.(?:role|admin|user|auth|permissions)\b", source
            ):
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message=f"Unverified jwt.decode() result '{var_name}' used in authorization logic.",
                        evidence={"variable": var_name, "call": m.group(0)},
                    )
                )

        return findings


# ── Rule 13: Prototype Pollution (CWE-1321) ──────────────────────────────────


class JSPrototypePollutionRule(Rule):
    """Detects Object.assign or lodash merge/set operations on untrusted inputs."""

    id = "APS-JS-INJ-004"
    title = "Prototype Pollution via Object Merge / Set"
    cwe = "CWE-1321"
    severity = Severity.HIGH
    category = "injection"
    description = "Merging unvalidated objects into target instances enables prototype pollution."
    explanation = (
        "Recursively merging user-supplied JSON or parameters using Object.assign(), lodash.merge(), or _.set() "
        "allows attackers to inject '__proto__' or 'constructor.prototype' properties, corrupting Object.prototype "
        "and potentially causing denial of service or remote code execution."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for Object.assign or merge with req.body / untrusted input
        pollute_pattern = re.compile(
            r"\b(?:Object\.assign|_\.(?:merge|set)|lodash\.(?:merge|set))\s*\(\s*([^;)]+)\s*\)",
            re.MULTILINE,
        )
        for m in pollute_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            args = m.group(1)
            # If tainted sources like req.body or JSON.parse appear directly
            if any(src in args for src in ("req.body", "request.body", "req.query", "JSON.parse")):
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                if not any(f.range.start_line == line for f in findings):
                    findings.append(
                        self.create_finding(
                            rng=Range(
                                start_line=line, start_col=col, end_line=end_line, end_col=end_col
                            ),
                            message="Object merge with untrusted input enables prototype pollution.",
                            evidence={"call": m.group(0), "taint_confirmed": False},
                        )
                    )

        return findings


# ── Rule 14: Regular Expression Denial of Service / ReDoS (CWE-1333) ─────────


class JSReDoSRule(Rule):
    """Detects dynamic RegExp construction from untrusted user inputs."""

    id = "APS-JS-INJ-005"
    title = "Regular Expression Denial of Service (ReDoS)"
    cwe = "CWE-1333"
    severity = Severity.MEDIUM
    category = "injection"
    description = (
        "Constructing regular expressions from user inputs risks catastrophic backtracking."
    )
    explanation = (
        "Instantiating new RegExp() with unescaped user inputs enables attackers to supply evil regex patterns "
        "causing catastrophic exponential backtracking (ReDoS), exhausting server CPU and starving concurrent requests. "
        "Use static regex literals or escape special metacharacters."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                findings.append(
                    self.create_finding(
                        rng=tr.range,
                        message=tr.message,
                        evidence={
                            "taint_confirmed": True,
                            "source": tr.source_text,
                            "sink": tr.sink_text,
                        },
                        taint_path=tr.path,
                    )
                )

        # 2. Syntactic inspection for new RegExp with non-constant input
        regexp_pattern = re.compile(
            r"\b(?:new\s+RegExp|RegExp)\s*\(\s*([^,;)]+)",
            re.MULTILINE,
        )
        for m in regexp_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            arg = m.group(1).strip()
            # If pure string constant or escaped regex, safe
            if re.fullmatch(r'["\'][^"\']*["\']', arg) or "escapeRegExp" in arg:
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=Range(
                            start_line=line, start_col=col, end_line=end_line, end_col=end_col
                        ),
                        message="Dynamic regular expression constructed from variable input risks ReDoS.",
                        evidence={"call": m.group(0), "taint_confirmed": False},
                    )
                )

        return findings


# ── Rule 15: Obfuscated Code Execution (CWE-506) ─────────────────────────────


class JSObfuscationRule(Rule):
    """Detects malicious obfuscation patterns (eval(atob(...)), String.fromCharCode chains)."""

    id = "APS-JS-OBF-001"
    title = "Obfuscated / Encoded Dynamic Execution"
    cwe = "CWE-506"
    severity = Severity.CRITICAL
    category = "obfuscation"
    description = "Evaluating base64 or charCode decoded strings indicates malicious evasion."
    explanation = (
        "Patterns such as eval(atob(...)), eval(Buffer.from(..., 'base64').toString()), "
        "or eval(String.fromCharCode(...)) are standard dropper/malware obfuscation techniques designed "
        "to conceal malicious payloads from security scanners."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Check eval(atob(...)) or eval(Buffer.from(...)) or eval(String.fromCharCode(...))
        obf_pattern = re.compile(
            r"\b(?:eval|Function)\s*\(\s*(?:atob|Buffer\.from|String\.fromCharCode|unescape)\s*\(",
            re.MULTILINE,
        )
        for m in obf_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message="Obfuscated execution via eval(atob / fromCharCode) detected.",
                    evidence={"pattern": m.group(0)},
                )
            )

        # Check Function("return this")() pattern
        fn_pattern = re.compile(
            r"Function\s*\(\s*[\"']return\s+this[\"']\s*\)\s*\(\s*\)", re.MULTILINE
        )
        for m in fn_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message="Obfuscated global scope retrieval via Function('return this')() detected.",
                    evidence={"pattern": m.group(0)},
                )
            )

        return findings


# ── Rule 16: Disabled TLS Validation (CWE-295) ───────────────────────────────


class JSDisabledTLSRule(Rule):
    """Detects disabled SSL/TLS certificate validation (NODE_TLS_REJECT_UNAUTHORIZED = '0')."""

    id = "APS-JS-NET-003"
    title = "Disabled TLS Certificate Validation"
    cwe = "CWE-295"
    severity = Severity.CRITICAL
    category = "network"
    description = "Disabling TLS certificate validation enables Man-in-the-Middle (MITM) attacks."
    explanation = (
        "Setting process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0' or configuring rejectUnauthorized: false "
        "disables SSL/TLS authenticity checks across all Node.js HTTPS connections, allowing network adversaries "
        "to intercept, decrypt, and alter network traffic."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Check NODE_TLS_REJECT_UNAUTHORIZED = "0"
        env_pattern = re.compile(
            r"NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*[\"']?0[\"']?",
            re.MULTILINE,
        )
        for m in env_pattern.finditer(source):
            if _is_inside_comment(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message="TLS certificate verification globally disabled via NODE_TLS_REJECT_UNAUTHORIZED='0'.",
                    evidence={"setting": m.group(0)},
                )
            )

        # Check rejectUnauthorized: false
        opt_pattern = re.compile(
            r"\brejectUnauthorized\s*:\s*false\b",
            re.MULTILINE,
        )
        for m in opt_pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message="TLS certificate verification disabled via rejectUnauthorized: false.",
                    evidence={"setting": m.group(0)},
                )
            )

        return findings


# ── Registered Rule List ──────────────────────────────────────────────────────

ALL_JAVASCRIPT_RULES: Final[list[Rule]] = [
    JSCodeInjectionRule(),
    JSCommandInjectionRule(),
    JSDOMXSSRule(),
    JSReactXSSRule(),
    JSOpenRedirectRule(),
    JSSQLInjectionRule(),
    JSPathTraversalRule(),
    JSSSRFRule(),
    JSInsecureRandomnessRule(),
    JSWeakHashRule(),
    JSHardcodedSecretsRule(),
    JSInsecureJWTRule(),
    JSPrototypePollutionRule(),
    JSReDoSRule(),
    JSObfuscationRule(),
    JSDisabledTLSRule(),
]
