"""Deterministic Java security rules evaluating AST and token stream patterns."""

from __future__ import annotations

import math
import re
from typing import Final

from apsla.languages.java_lang.profile import JAVA_TAINT_PROFILE
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
            return tok.kind in ("COMMENT", "STRING", "CHAR")
    return False


def _get_non_trivia_tokens(tokens: list[Token]) -> list[Token]:
    """Filter out whitespace and comment tokens."""
    return [t for t in tokens if t.kind not in ("WHITESPACE", "COMMENT")]


# ── Rule 1: Command Injection ──────────────────────────────────────────────────


class JavaCommandInjectionRule(Rule):
    """Detects OS command execution with unvalidated or concatenated input (CWE-78)."""

    id = "APS-JV-INJ-001"
    title = "Command Injection via Runtime.exec / ProcessBuilder"
    cwe = "CWE-78"
    severity = Severity.CRITICAL
    category = "injection"
    description = "Executing OS commands with dynamic string concatenation can lead to arbitrary command execution."
    explanation = (
        "Invoking Runtime.getRuntime().exec() or ProcessBuilder with concatenated strings or untrusted variables "
        "allows attackers to inject shell metacharacters and execute unauthorized commands on the host operating system."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. First run taint-lite to check for confirmed data flows
        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, context.offset_map)
        taint_results = engine.analyze()
        for tr in taint_results:
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

        # 2. Syntactic inspection for concatenation inside exec call:
        # e.g., Runtime.getRuntime().exec("ping " + host);
        pattern = re.compile(
            r"(?:Runtime\.getRuntime\(\)\.exec|Runtime\.exec)\s*\(\s*([^;)]+)\s*\)",
            re.MULTILINE,
        )
        for m in pattern.finditer(source):
            start_pos = m.start()
            if _is_inside_comment_or_string(start_pos, tokens):
                continue

            arg_str = m.group(1).strip()
            # If argument has concatenation '+' and is not just pure constants
            if "+" in arg_str and not re.fullmatch(r'"[^"]*"\s*\+\s*"[^"]*"', arg_str):
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
                rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

                if not any(f.range.start_line == line for f in findings):
                    findings.append(
                        self.create_finding(
                            rng=rng,
                            message="Command execution invoked with concatenated string argument.",
                            evidence={"arg": arg_str},
                        )
                    )

        return findings


# ── Rule 2: SQL Injection ──────────────────────────────────────────────────────


class JavaSqlInjectionRule(Rule):
    """Detects dynamic SQL query concatenation in Statement.execute* (CWE-89)."""

    id = "APS-JV-INJ-002"
    title = "SQL Injection via Dynamic Query Construction"
    cwe = "CWE-89"
    severity = Severity.CRITICAL
    category = "injection"
    description = "Constructing SQL queries using dynamic string concatenation allows attackers to manipulate query logic."
    explanation = (
        "Executing SQL statements created by concatenating user-controlled variables into query strings "
        "enables SQL injection. Attackers can bypass authentication, extract sensitive records, or modify the database. "
        "Use parameterized queries with java.sql.PreparedStatement and '?' placeholders instead."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint-lite analysis
        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, context.offset_map)
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

        # 2. Syntactic check: Statement.executeQuery/executeUpdate/execute with '+'
        pattern = re.compile(
            r"(?:\bstmt|\bstatement|\bconn|\bconnection|\bem)\s*\.\s*(?:executeQuery|executeUpdate|execute|createQuery|createNativeQuery)\s*\(\s*([^;)]+)\s*\)",
            re.MULTILINE,
        )
        for m in pattern.finditer(source):
            start_pos = m.start()
            if _is_inside_comment_or_string(start_pos, tokens):
                continue

            arg_str = m.group(1).strip()
            # If argument has concatenation '+'
            if "+" in arg_str:
                # Exclude purely concatenated string literals like "SELECT * " + "FROM users"
                if re.fullmatch(r'"[^"]*"\s*\+\s*"[^"]*"', arg_str):
                    continue

                # Exclude concatenation of purely numeric primitives or sanitized variables
                unquoted_arg = re.sub(r'"[^"]*"', "", arg_str)
                var_names = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", unquoted_arg)
                if var_names and all(
                    re.search(rf"\b(?:int|long|float|double)\s+{v}\b", source)
                    or re.search(rf"\b{v}\s*=\s*(?:Integer|Long|Float|Double)\.parse", source)
                    for v in var_names
                ):
                    continue

                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
                rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

                if not any(f.range.start_line == line for f in findings):
                    findings.append(
                        self.create_finding(
                            rng=rng,
                            message="SQL query executed with dynamic string concatenation.",
                            evidence={"query_arg": arg_str},
                        )
                    )

        return findings


# ── Rule 3: Insecure Deserialization ───────────────────────────────────────────


class JavaInsecureDeserializationRule(Rule):
    """Detects unsafe Java object deserialization via ObjectInputStream, XMLDecoder, XStream (CWE-502)."""

    id = "APS-JV-DES-001"
    title = "Insecure Java Object Deserialization"
    cwe = "CWE-502"
    severity = Severity.CRITICAL
    category = "deserialization"
    description = "Deserializing untrusted object streams can trigger remote code execution via gadget chains."
    explanation = (
        "Calling ObjectInputStream.readObject(), XMLDecoder.readObject(), or XStream.fromXML() on untrusted data "
        "allows attackers to instantiate arbitrary classes and trigger gadget chains, leading to remote code execution."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pattern = re.compile(
            r"(?:\bObjectInputStream\b[^\n;]*\.readObject\(\)|\bXMLDecoder\b[^\n;]*\.readObject\(\)|\bXStream\b[^\n;]*\.fromXML\s*\([^)]*\)|\.readObject\(\)|\.fromXML\s*\([^)]*\))",
            re.MULTILINE,
        )
        for m in pattern.finditer(source):
            start_pos = m.start()
            if _is_inside_comment_or_string(start_pos, tokens):
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
            rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

            findings.append(
                self.create_finding(
                    rng=rng,
                    message="Untrusted object deserialization detected via readObject() / fromXML().",
                    evidence={"match": m.group(0)},
                )
            )
        return findings


# ── Rule 4: Broken Cryptographic Hash ─────────────────────────────────────────


class JavaBrokenHashRule(Rule):
    """Detects usage of broken hash algorithms such as MD5 and SHA-1 (CWE-327)."""

    id = "APS-JV-CRY-001"
    title = "Broken Cryptographic Hash Algorithm (MD5 / SHA-1)"
    cwe = "CWE-327"
    severity = Severity.HIGH
    category = "cryptography"
    description = "MD5 and SHA-1 have known collision and preimage vulnerabilities."
    explanation = (
        "MessageDigest.getInstance('MD5') and SHA-1 are cryptographically broken and prone to collision attacks. "
        "Use SHA-256, SHA-384, SHA-512, or SHA3-256 instead."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pattern = re.compile(
            r'MessageDigest\.getInstance\s*\(\s*["\'](MD5|SHA-1|SHA1)["\']\s*\)',
            re.IGNORECASE,
        )
        for m in pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                # Note: m.start() is the start of MessageDigest call, not a comment
                pass
            # Verify that MessageDigest token is not inside a comment
            is_comm = False
            for tok in tokens:
                if tok.start <= context.offset_map.py_to_utf16(m.start()) < tok.end:
                    if tok.kind in ("COMMENT", "STRING"):
                        is_comm = True
                        break
            if is_comm:
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
            rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

            algo = m.group(1).upper()
            findings.append(
                self.create_finding(
                    rng=rng,
                    message=f"Cryptographically weak hash algorithm '{algo}' in MessageDigest.getInstance().",
                    evidence={"algorithm": algo},
                )
            )
        return findings


# ── Rule 5: Weak Cipher / Mode ────────────────────────────────────────────────


class JavaWeakCipherRule(Rule):
    """Detects usage of weak cryptographic ciphers (DES, RC4) or ECB mode (CWE-327)."""

    id = "APS-JV-CRY-002"
    title = "Weak Cryptographic Cipher or Mode (DES / ECB)"
    cwe = "CWE-327"
    severity = Severity.HIGH
    category = "cryptography"
    description = "DES and ECB mode do not provide semantic security or confidentiality."
    explanation = (
        "Cipher.getInstance() initialized with DES, Blowfish, RC4, or ECB mode provides weak encryption. "
        "ECB mode encrypts identical plaintext blocks into identical ciphertext blocks, leaking patterns. "
        "Use AES in GCM mode (AES/GCM/NoPadding) with authenticated encryption instead."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pattern = re.compile(
            r'Cipher\.getInstance\s*\(\s*["\']([^"\']+)["\']\s*\)',
            re.IGNORECASE,
        )
        weak_ciphers = ("des", "rc4", "blowfish", "desede")

        for m in pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue

            cipher_str = m.group(1).strip()
            cipher_lower = cipher_str.lower()
            is_weak = any(w in cipher_lower for w in weak_ciphers) or "ecb" in cipher_lower

            if is_weak:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
                rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

                findings.append(
                    self.create_finding(
                        rng=rng,
                        message=f"Insecure cipher algorithm or mode '{cipher_str}' in Cipher.getInstance().",
                        evidence={"cipher": cipher_str},
                    )
                )
        return findings


# ── Rule 6: Insecure Randomness ────────────────────────────────────────────────


class JavaInsecureRandomRule(Rule):
    """Detects usage of java.util.Random for security tokens or keys (CWE-338)."""

    id = "APS-JV-CRY-003"
    title = "Insecure Randomness for Security Tokens"
    cwe = "CWE-338"
    severity = Severity.MEDIUM
    category = "cryptography"
    description = (
        "java.util.Random is a linear congruential generator whose internal state can be computed."
    )
    explanation = (
        "java.util.Random generates predictable pseudo-random sequences. When generating session IDs, "
        "authentication tokens, password reset links, or cryptographic nonces, use java.security.SecureRandom."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Check for new Random() associated with security terms
        sec_keywords = (
            "token",
            "key",
            "secret",
            "password",
            "session",
            "nonce",
            "salt",
            "auth",
            "otp",
            "code",
        )
        pattern = re.compile(
            r"(?:([A-Za-z0-9_]+)\s*=\s*)?new\s+(?:java\.util\.)?Random\s*\(\s*\)",
            re.MULTILINE,
        )

        for m in pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue

            var_name = (m.group(1) or "").lower()
            # Also check the entire statement or line
            line_start = source.rfind("\n", 0, m.start()) + 1
            line_end = source.find("\n", m.end())
            line_text = source[line_start : line_end if line_end != -1 else len(source)].lower()

            is_sec = (
                any(kw in var_name for kw in sec_keywords)
                or any(kw in line_text for kw in sec_keywords)
                or any(
                    kw in source.lower()
                    for kw in (
                        "token",
                        "secret",
                        "password",
                        "session",
                        "nonce",
                        "salt",
                        "auth",
                        "otp",
                        "credential",
                    )
                )
            )
            if is_sec:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
                rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

                findings.append(
                    self.create_finding(
                        rng=rng,
                        message="Insecure java.util.Random used for security-sensitive token/key generation.",
                        evidence={"variable": var_name or "Random instance"},
                    )
                )

        return findings


# ── Rule 7: Hard-Coded Secret ──────────────────────────────────────────────────


class JavaHardcodedSecretRule(Rule):
    """Detects hard-coded passwords, API keys, and secret tokens in code (CWE-798)."""

    id = "APS-JV-SEC-001"
    title = "Hard-Coded Secret or Password in Source Code"
    cwe = "CWE-798"
    severity = Severity.HIGH
    category = "secrets"
    description = "Embedding credentials in source code exposes them to repository commit leaks."
    explanation = (
        "Hard-coding passwords, API tokens, or secrets directly in Java source code compromises credentials "
        "when shared or checked into version control. Store secrets in environment variables or a vault."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pattern = re.compile(
            r'(?:String|var)\s+([A-Za-z0-9_]*(?:password|passwd|secret|apikey|api_key|token|auth_token|private_key)[A-Za-z0-9_]*)\s*=\s*"([^"]+)"',
            re.IGNORECASE,
        )

        placeholders = (
            "password",
            "dummy",
            "test",
            "admin",
            "changeit",
            "changeme",
            "todo",
            "xxx",
            "123456",
            "",
        )

        for m in pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue

            var_name = m.group(1)
            literal_val = m.group(2).strip()

            if literal_val.lower() in placeholders or len(literal_val) < 8:
                continue

            entropy = _shannon_entropy(literal_val)
            if entropy > 2.8 or len(literal_val) >= 16:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
                rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

                findings.append(
                    self.create_finding(
                        rng=rng,
                        message=f"Hard-coded secret detected in variable '{var_name}'.",
                        evidence={"variable": var_name, "entropy": round(entropy, 2)},
                    )
                )

        return findings


# ── Rule 8: XML External Entity (XXE) ──────────────────────────────────────────


class JavaXmlExternalEntityRule(Rule):
    """Detects DocumentBuilderFactory / SAXParserFactory instantiated without disabling external entities (CWE-611)."""

    id = "APS-JV-XML-001"
    title = "XML External Entity (XXE) Injection"
    cwe = "CWE-611"
    severity = Severity.HIGH
    category = "xml"
    description = "Parsing XML without disabling external entity resolution exposes servers to SSRF and file disclosure."
    explanation = (
        "DocumentBuilderFactory and SAXParserFactory resolve external DTDs and entities by default. "
        "Attackers can leverage XML entity injection (XXE) to read local server files or launch SSRF attacks. "
        "Configure factory.setFeature('http://apache.org/xml/features/disallow-doctype-decl', true)."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        factories = (
            "DocumentBuilderFactory.newInstance",
            "SAXParserFactory.newInstance",
            "XMLInputFactory.newInstance",
            "XMLInputFactory.newFactory",
        )

        for fact in factories:
            for m in re.finditer(re.escape(fact), source):
                if _is_inside_comment_or_string(m.start(), tokens):
                    continue

                # Check if setFeature is called within the next 15 lines
                chunk_start = m.start()
                chunk_end = min(len(source), m.start() + 1500)
                chunk = source[chunk_start:chunk_end]

                is_safe = (
                    "disallow-doctype-decl" in chunk
                    or "FEATURE_SECURE_PROCESSING" in chunk
                    or "setFeature" in chunk
                )

                if not is_safe:
                    start_u16 = context.offset_map.py_to_utf16(m.start())
                    end_u16 = context.offset_map.py_to_utf16(m.end())
                    line, col = context.offset_map.utf16_to_pos(start_u16)
                    end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
                    rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

                    findings.append(
                        self.create_finding(
                            rng=rng,
                            message=f"XML parser '{fact}' initialized without disabling external DTD / entity processing.",
                            evidence={"factory": fact},
                        )
                    )

        return findings


# ── Rule 9: Path Traversal ─────────────────────────────────────────────────────


class JavaPathTraversalRule(Rule):
    """Detects unvalidated user paths passed to File, Paths.get, or FileInputStream (CWE-22)."""

    id = "APS-JV-IO-001"
    title = "Path Traversal via Tainted File Path"
    cwe = "CWE-22"
    severity = Severity.HIGH
    category = "io"
    description = "Constructing file paths with user input without canonicalization allows directory traversal."
    explanation = (
        "Instantiating new File() or Paths.get() with untrusted parameters enables attackers to provide "
        "'../' sequences to access unauthorized system files. Validate paths using normalize() and startsWith()."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint-lite analysis
        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, context.offset_map)
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

        # 2. Syntactic check: new File(base + path) or new FileInputStream(...)
        pattern = re.compile(
            r"new\s+(?:File|FileInputStream|FileReader)\s*\(\s*([^;)]*\+[^;)]*)\s*\)",
            re.MULTILINE,
        )
        for m in pattern.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            arg = m.group(1).strip()
            # If normalized with startsWith, it is safe
            if "normalize" in source and "startsWith" in source:
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
            rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

            if not any(f.range.start_line == line for f in findings):
                findings.append(
                    self.create_finding(
                        rng=rng,
                        message="File system path constructed with concatenated input without traversal validation.",
                        evidence={"path_arg": arg},
                    )
                )

        return findings


# ── Rule 10: Reflected XSS ─────────────────────────────────────────────────────


class JavaReflectedXssRule(Rule):
    """Detects unescaped user data written directly to servlet HTTP response (CWE-79)."""

    id = "APS-JV-XSS-001"
    title = "Reflected Cross-Site Scripting (XSS)"
    cwe = "CWE-79"
    severity = Severity.HIGH
    category = "xss"
    description = "Writing unencoded user input into HTML response streams enables script injection in browser."
    explanation = (
        "Writing unsanitized request data via response.getWriter().println() or print() allows cross-site scripting (XSS). "
        "Attackers can execute malicious JavaScript in victims' browsers to hijack sessions or steal cookies. "
        "Encode all dynamic output using StringEscapeUtils.escapeHtml4() or ESAPI."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Taint-lite analysis
        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, context.offset_map)
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

        return findings


# ── Rule 11: Server-Side Request Forgery (SSRF) ────────────────────────────────


class JavaSsrfRule(Rule):
    """Detects HTTP requests to unvalidated URLs from user input (CWE-918)."""

    id = "APS-JV-NET-001"
    title = "Server-Side Request Forgery (SSRF) via Tainted URL"
    cwe = "CWE-918"
    severity = Severity.HIGH
    category = "network"
    description = "Sending network requests to user-specified URLs enables access to internal network services."
    explanation = (
        "Instantiating new URL() or executing HttpClient calls with user-controlled URLs allows attackers to target "
        "internal cloud metadata endpoints (e.g. 169.254.169.254) or intranet microservices. Validate URLs with an allowlist."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, context.offset_map)
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

        return findings


# ── Rule 12: Insecure TLS / Certificate Validation ─────────────────────────────


class JavaInsecureTlsRule(Rule):
    """Detects TrustAll TrustManagers and HostnameVerifiers accepting all certs (CWE-295)."""

    id = "APS-JV-NET-002"
    title = "Insecure TLS Certificate Validation (TrustAll)"
    cwe = "CWE-295"
    severity = Severity.HIGH
    category = "network"
    description = "Disabling SSL/TLS certificate or hostname verification enables Man-in-the-Middle (MitM) attacks."
    explanation = (
        "Implementing an X509TrustManager with empty checkServerTrusted() methods or a HostnameVerifier that returns true "
        "disables SSL/TLS verification, allowing attackers to intercept or modify encrypted traffic in transit."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Check for empty checkServerTrusted or TrustManager with no validation
        pattern1 = re.compile(
            r"void\s+checkServerTrusted\s*\([^)]*\)\s*\{\s*\}",
            re.MULTILINE,
        )
        for m in pattern1.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
            rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

            findings.append(
                self.create_finding(
                    rng=rng,
                    message="Empty checkServerTrusted() implementation disables TLS certificate validation.",
                    evidence={"pattern": "empty checkServerTrusted"},
                )
            )

        # Check for HostnameVerifier returning true: (hostname, session) -> true or return true;
        pattern2 = re.compile(
            r"HostnameVerifier\s+[A-Za-z0-9_]+\s*=\s*(?:\([^)]*\)\s*->\s*true|new\s+HostnameVerifier\s*\(\s*\)\s*\{[^}]*return\s+true;[^}]*\})",
            re.MULTILINE,
        )
        for m in pattern2.finditer(source):
            if _is_inside_comment_or_string(m.start(), tokens):
                continue
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
            rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

            findings.append(
                self.create_finding(
                    rng=rng,
                    message="HostnameVerifier unconditionally returning true disables TLS hostname verification.",
                    evidence={"pattern": "HostnameVerifier true"},
                )
            )

        return findings


# ── Rule 13: Unsafe Reflection ─────────────────────────────────────────────────


class JavaUnsafeReflectionRule(Rule):
    """Detects Class.forName or ClassLoader.loadClass with untrusted class names (CWE-470)."""

    id = "APS-JV-INJ-003"
    title = "Unsafe Reflection via Tainted Class Name"
    cwe = "CWE-470"
    severity = Severity.MEDIUM
    category = "injection"
    description = "Dynamically loading classes with unvalidated names can trigger unauthorized code execution."
    explanation = (
        "Invoking Class.forName() with user-controlled input can trigger class static initializers with dangerous side effects. "
        "Validate class names against a strict whitelist before dynamic loading."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, context.offset_map)
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

        return findings


# ── Rule 14: Script / Code Injection ───────────────────────────────────────────


class JavaScriptInjectionRule(Rule):
    """Detects ScriptEngine.eval with unvalidated code strings (CWE-94)."""

    id = "APS-JV-INJ-004"
    title = "Code Injection via ScriptEngine.eval"
    cwe = "CWE-94"
    severity = Severity.CRITICAL
    category = "injection"
    description = (
        "Evaluating untrusted scripts in ScriptEngine allows execution of arbitrary commands."
    )
    explanation = (
        "Passing dynamic user input to ScriptEngine.eval() enables attackers to execute arbitrary code "
        "within the JVM process. Avoid dynamic script evaluation or apply strict sandboxing."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, context.offset_map)
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

        return findings


# ── Rule 15: Trojan Source via Unicode Escape ──────────────────────────────────


class JavaUnicodeEscapeAttackRule(Rule):
    r"""Detects Unicode escapes (\uXXXX) producing Trojan Source bidi or control characters (CWE-1007)."""

    id = "APS-JV-UNI-001"
    title = "Trojan Source / Dangerous Unicode Escape in Java Source"
    cwe = "CWE-1007"
    severity = Severity.CRITICAL
    category = "unicode"
    description = "Using Java \\uXXXX escape sequences to inject invisible bidi overrides or control characters."
    explanation = (
        "Java processes \\uXXXX escapes prior to parsing. Injecting bidi controls (e.g. \\u202E) or zero-width "
        "characters inside comments or code alters visual reading order while executing differently in the JVM (CVE-2021-42574)."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        raw = context.raw_source

        # Scan for \uXXXX where codepoint is in BIDI_AND_CONTROL_CODEPOINTS
        pattern = re.compile(r"\\u+([0-9a-fA-F]{4})")
        dangerous_cps = {
            0x202A,
            0x202B,
            0x202C,
            0x202D,
            0x202E,
            0x2066,
            0x2067,
            0x2068,
            0x2069,
            0x200E,
            0x200F,
            0x061C,
            0x200B,
            0x200C,
            0x200D,
            0xFEFF,
        }

        for m in pattern.finditer(raw):
            hex_code = m.group(1)
            cp = int(hex_code, 16)
            if cp in dangerous_cps:
                start_u16 = context.offset_map.py_to_utf16(m.start())
                end_u16 = context.offset_map.py_to_utf16(m.end())
                line, col = context.offset_map.utf16_to_pos(start_u16)
                end_line, end_col = context.offset_map.utf16_to_pos(end_u16)
                rng = Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col)

                findings.append(
                    self.create_finding(
                        rng=rng,
                        message=f"Trojan Source bidi/control character injected via Unicode escape \\u{hex_code}.",
                        evidence={"hex": hex_code, "codepoint": f"U+{hex_code.upper()}"},
                    )
                )

        return findings


ALL_JAVA_RULES: Final[list[Rule]] = [
    JavaCommandInjectionRule(),
    JavaSqlInjectionRule(),
    JavaInsecureDeserializationRule(),
    JavaBrokenHashRule(),
    JavaWeakCipherRule(),
    JavaInsecureRandomRule(),
    JavaHardcodedSecretRule(),
    JavaXmlExternalEntityRule(),
    JavaPathTraversalRule(),
    JavaReflectedXssRule(),
    JavaSsrfRule(),
    JavaInsecureTlsRule(),
    JavaUnsafeReflectionRule(),
    JavaScriptInjectionRule(),
    JavaUnicodeEscapeAttackRule(),
]
