"""Deterministic C and C++ security rules evaluating AST, token stream, and taint flows."""

from __future__ import annotations

import math
import re
from typing import Final

from apsla.languages.cpp_lang.profile import CPP_TAINT_PROFILE
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
            return tok.kind in ("COMMENT", "STRING", "RAW_STRING", "CHAR")
    return False


def _is_inside_comment_string_or_directive(
    pos: int, tokens: list[Token], allow_directive: bool = False
) -> bool:
    """Check if character index is inside comment, string, or preprocessor directive."""
    for tok in tokens:
        if tok.start <= pos < tok.end:
            if tok.kind in ("COMMENT", "STRING", "RAW_STRING", "CHAR"):
                return True
            if tok.kind == "PREPROCESSOR" and not allow_directive:
                return True
    return False


def _find_token_at(pos: int, tokens: list[Token]) -> Token | None:
    """Find token spanning character position."""
    for tok in tokens:
        if tok.start <= pos < tok.end:
            return tok
    return None


def _extract_array_size(source: str, var_name: str) -> int | None:
    """Extract declared fixed buffer size for a char array e.g. char buf[64]."""
    pat = rf"\bchar\s+{re.escape(var_name)}\s*\[\s*(\d+)\s*\]"
    m = re.search(pat, source)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


# ── Rule 1: Unbounded Copy / Inherently Dangerous Gets (CWE-120 / CWE-242) ──


class CppUnboundedCopyRule(Rule):
    """Detects unbounded buffer operations: strcpy, strcat, gets, sprintf, vsprintf."""

    id = "APS-CP-MEM-001"
    title = "Buffer Overflow via Unbounded String Copy (strcpy / strcat / gets / sprintf)"
    cwe = "CWE-120"
    severity = Severity.HIGH
    category = "memory"
    explanation = (
        "Functions like strcpy(), strcat(), sprintf(), and vsprintf() perform unbounded memory writes "
        "without checking destination buffer capacity. The gets() function is inherently unfixable and "
        "was removed from C11 (CWE-242). These flaws can lead to stack smashing and arbitrary code execution."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, context.offset_map)
        for tr in engine.analyze():
            if tr.rule_id == self.id:
                sev = Severity.CRITICAL if "gets" in tr.sink_text else Severity.HIGH
                f = self.create_finding(
                    rng=tr.range,
                    message=tr.message,
                    severity_override=sev,
                    evidence={
                        "taint_confirmed": True,
                        "source": tr.source_text,
                        "sink": tr.sink_text,
                    },
                    taint_path=tr.path,
                )
                if "gets" in tr.sink_text:
                    f.cwe = "CWE-242"
                findings.append(f)

        # 2. Syntactic inspection
        pat = re.compile(r"\b(strcpy|strcat|gets|sprintf|vsprintf)\s*\(", re.MULTILINE)
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue

            fn_name = m.group(1)
            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            if not any(f.range.start_line == line for f in findings):
                sev = Severity.CRITICAL if fn_name == "gets" else Severity.HIGH
                msg = (
                    "Inherently dangerous function gets() has no bounds checking; use fgets()."
                    if fn_name == "gets"
                    else f"Unbounded buffer operation via {fn_name}() without bounds validation."
                )
                f = self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message=msg,
                    severity_override=sev,
                    evidence={"function": fn_name, "taint_confirmed": False},
                )
                if fn_name == "gets":
                    f.cwe = "CWE-242"
                findings.append(f)

        return findings


# ── Rule 2: Out-of-Bounds Memory Access via Wrong Length (CWE-787) ──────────


class CppOutOfBoundsLengthRule(Rule):
    """Detects strncpy, memcpy, memmove, read with tainted length or wrong sizeof."""

    id = "APS-CP-MEM-002"
    title = "Out-of-Bounds Memory Write via Tainted Length or Wrong sizeof"
    cwe = "CWE-787"
    severity = Severity.HIGH
    explanation = (
        "Passing a tainted length or calculating length via sizeof(source) rather than sizeof(dest) "
        "can cause strncpy(), memcpy(), memmove(), or read() to overwrite adjacent memory structures."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, context.offset_map)
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

        # 2. Syntactic check: wrong sizeof e.g. strncpy(dest, src, sizeof(src))
        pat = re.compile(
            r"\b(strncpy|memcpy|memmove)\s*\(\s*([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)\s*,\s*sizeof\s*\(\s*([A-Za-z0-9_]+)\s*\)\s*\)",
            re.MULTILINE,
        )
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue
            dest_var = m.group(2)
            src_var = m.group(3)
            sizeof_var = m.group(4)

            # If sizeof uses source instead of destination: wrong sizeof flaw!
            if sizeof_var == src_var and sizeof_var != dest_var:
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
                            message=f"Wrong sizeof operand: {m.group(1)} uses sizeof({sizeof_var}) instead of sizeof({dest_var}).",
                            evidence={"dest": dest_var, "src": src_var, "sizeof": sizeof_var},
                        )
                    )

        return findings


# ── Rule 3: Format String Vulnerability (CWE-134) ────────────────────────────


class CppFormatStringRule(Rule):
    """Detects non-literal or tainted format string arguments in printf family."""

    id = "APS-CP-FMT-001"
    title = "Format String Vulnerability via Non-Literal Format"
    cwe = "CWE-134"
    severity = Severity.CRITICAL
    explanation = (
        "Passing a variable or tainted string directly as the format argument to printf(), fprintf(), "
        "syslog(), or snprintf() allows attackers to read arbitrary stack memory via %x and write to "
        "arbitrary memory addresses using the %n conversion specifier."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, context.offset_map)
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

        # 2. Syntactic inspection
        # Match printf(x), fprintf(stream, x), syslog(prio, x), snprintf(buf, size, x)
        pat = re.compile(
            r"\b(printf|fprintf|syslog|snprintf|vsnprintf)\s*\(([^;)]+)\)",
            re.MULTILINE,
        )
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue
            fn = m.group(1)
            raw_args = m.group(2).strip()

            fmt_idx = 0
            if fn in ("fprintf", "syslog"):
                fmt_idx = 1
            elif fn in ("snprintf", "vsnprintf"):
                fmt_idx = 2

            parts = [p.strip() for p in raw_args.split(",")]
            if len(parts) <= fmt_idx:
                continue

            fmt_arg = parts[fmt_idx]
            # Safe if format argument is a string literal starting with '"' or 'L"' or 'u8"'
            if fmt_arg.startswith(('"', 'L"', 'u8"', 'u"', 'U"', 'R"')):
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
                        message=f"Non-literal format string passed to {fn}(); use an explicit format specifier like '%s'.",
                        evidence={"call": m.group(0), "format_arg": fmt_arg},
                    )
                )

        return findings


# ── Rule 4: scanf without Width Specifier (CWE-120) ──────────────────────────


class CppScanfNoWidthRule(Rule):
    """Detects scanf('%s') without field width limit."""

    id = "APS-CP-MEM-003"
    title = "Buffer Overflow via Unbounded scanf '%s'"
    cwe = "CWE-120"
    severity = Severity.HIGH
    explanation = (
        "Using scanf(), fscanf(), or sscanf() with the '%s' specifier without an explicit maximum field "
        "width allows input to overflow the destination buffer. Always specify a maximum width (e.g., '%31s')."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pat = re.compile(r"\b(scanf|fscanf|sscanf)\s*\(\s*([^;)]+)\)", re.MULTILINE)
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue
            args_str = m.group(2)

            # Check if format contains '%s' without width
            # Valid bounded: %31s, %100s
            # Vulnerable unbounded: %s (ignoring %*s or %d)
            if re.search(r'"[^"]*%s[^"]*"', args_str) and not re.search(
                r'"[^"]*%\d+s[^"]*"', args_str
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
                        message=f"Unbounded format string '%s' in {m.group(1)}(); specify maximum field width.",
                        evidence={"call": m.group(0)},
                    )
                )

        return findings


# ── Rule 5: Command Injection (CWE-78) ───────────────────────────────────────


class CppCommandInjectionRule(Rule):
    """Detects command injection via system, popen, execl, execlp, execvp."""

    id = "APS-CP-INJ-001"
    title = "Command Injection via Shell / Process Execution"
    cwe = "CWE-78"
    severity = Severity.CRITICAL
    explanation = (
        "Invoking system() or popen() with concatenated, formatted, or tainted strings executes commands "
        "within the system command interpreter. Attackers can append shell metacharacters (; & | `) to execute "
        "arbitrary operating system commands."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, context.offset_map)
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

        # 2. Syntactic inspection: system(var) or popen(var)
        pat = re.compile(r"\b(system|popen)\s*\(\s*([^;)]+)\)", re.MULTILINE)
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue
            cmd_arg = m.group(2).split(",")[0].strip()

            # If argument is a pure constant literal string without variable expansion, skip
            if cmd_arg.startswith('"') and cmd_arg.endswith('"') and "+" not in cmd_arg:
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
                        message=f"Command execution via {m.group(1)}() with dynamic command string.",
                        evidence={"call": m.group(0), "cmd": cmd_arg},
                    )
                )

        return findings


# ── Rule 6: Integer Overflow in Allocation (CWE-190) ─────────────────────────


class CppIntegerOverflowAllocRule(Rule):
    """Detects integer overflow in allocation size: malloc(a * b), new T[n]."""

    id = "APS-CP-MEM-004"
    title = "Integer Overflow in Memory Allocation Size Arithmetic"
    cwe = "CWE-190"
    severity = Severity.HIGH
    explanation = (
        "Computing memory allocation sizes via arithmetic expressions (e.g., malloc(count * size)) "
        "can wrap around on integer overflow, resulting in a much smaller buffer being allocated "
        "than required, leading to subsequent heap buffer overflows."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # 1. Taint flow detection
        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, context.offset_map)
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

        # 2. Syntactic inspection: malloc(a * b) or calloc with multiplication
        pat = re.compile(r"\bmalloc\s*\(\s*([^;)]+\*[^;)]+)\)", re.MULTILINE)
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue
            expr = m.group(1).strip()

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
                        message=f"Potential integer overflow in malloc({expr}); validate multiplication or use calloc.",
                        evidence={"call": m.group(0), "expr": expr},
                    )
                )

        return findings


# ── Rule 7: Use-After-Free (CWE-416) ─────────────────────────────────────────


class CppUseAfterFreeRule(Rule):
    """Detects use of pointer after free() in the same function without reassignment."""

    id = "APS-CP-MEM-005"
    title = "Use-After-Free of Deallocated Pointer"
    cwe = "CWE-416"
    severity = Severity.HIGH
    explanation = (
        "Accessing or passing a pointer after calling free(p) causes undefined behavior, "
        "allowing attackers to execute arbitrary code if the memory is reallocated."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Pattern match free(p) followed by subsequent mention of p
        pat_free = re.compile(r"\bfree\s*\(\s*([A-Za-z0-9_]+)\s*\)\s*;", re.MULTILINE)
        for m in pat_free.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue
            ptr_name = m.group(1)
            free_end = m.end()

            # Look ahead in source for subsequent use of ptr_name before reassignment or function end
            rest_source = source[free_end:]
            # Check for subsequent use (e.g. *p, p->, p[, fn(p))
            # Stop if p is reassigned (p = NULL or p = malloc) or function ends '}'
            m_reassign = re.search(rf"\b{re.escape(ptr_name)}\s*=", rest_source)
            m_use = re.search(rf"\b{re.escape(ptr_name)}\b", rest_source)
            m_close_brace = re.search(r"\}", rest_source)

            close_idx = m_close_brace.start() if m_close_brace else len(rest_source)
            reassign_idx = m_reassign.start() if m_reassign else len(rest_source)

            if m_use and m_use.start() < close_idx and m_use.start() < reassign_idx:
                abs_pos = free_end + m_use.start()
                if not _is_inside_comment_string_or_directive(abs_pos, tokens):
                    start_u16 = context.offset_map.py_to_utf16(abs_pos)
                    end_u16 = context.offset_map.py_to_utf16(abs_pos + len(ptr_name))
                    line, col = context.offset_map.utf16_to_pos(start_u16)
                    end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                    findings.append(
                        self.create_finding(
                            rng=Range(
                                start_line=line, start_col=col, end_line=end_line, end_col=end_col
                            ),
                            message=f"Pointer '{ptr_name}' used after being freed without reassignment (use-after-free).",
                            evidence={"pointer": ptr_name, "noisy": True},
                        )
                    )

        return findings


# ── Rule 8: Double Free (CWE-415) ────────────────────────────────────────────


class CppDoubleFreeRule(Rule):
    """Detects double free of the same pointer without reassignment."""

    id = "APS-CP-MEM-006"
    title = "Double Free Memory Corruption"
    cwe = "CWE-415"
    severity = Severity.CRITICAL
    explanation = (
        "Calling free() twice on the same pointer without reallocating or setting it to NULL "
        "corrupts heap management metadata structures, enabling arbitrary code execution."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pat_free = re.compile(r"\bfree\s*\(\s*([A-Za-z0-9_]+)\s*\)\s*;", re.MULTILINE)
        matches = list(pat_free.finditer(source))

        for i, m1 in enumerate(matches):
            if _is_inside_comment_string_or_directive(m1.start(), tokens):
                continue
            ptr1 = m1.group(1)

            # Check if any subsequent free() frees the same pointer
            for m2 in matches[i + 1 :]:
                if _is_inside_comment_string_or_directive(m2.start(), tokens):
                    continue
                ptr2 = m2.group(1)
                if ptr1 == ptr2:
                    # Check if reassigned between m1 and m2
                    between_code = source[m1.end() : m2.start()]
                    if not re.search(rf"\b{re.escape(ptr1)}\s*=", between_code):
                        start_u16 = context.offset_map.py_to_utf16(m2.start())
                        end_u16 = context.offset_map.py_to_utf16(m2.end())
                        line, col = context.offset_map.utf16_to_pos(start_u16)
                        end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

                        findings.append(
                            self.create_finding(
                                rng=Range(
                                    start_line=line,
                                    start_col=col,
                                    end_line=end_line,
                                    end_col=end_col,
                                ),
                                message=f"Double free of pointer '{ptr1}' without reassignment.",
                                evidence={
                                    "pointer": ptr1,
                                    "first_free": m1.group(0),
                                    "second_free": m2.group(0),
                                },
                            )
                        )
                        break

        return findings


# ── Rule 9: Path Traversal (CWE-22) ──────────────────────────────────────────


class CppPathTraversalRule(Rule):
    """Detects path traversal in fopen, open, ifstream with tainted path."""

    id = "APS-CP-IO-001"
    title = "Path Traversal via Tainted File Path"
    cwe = "CWE-22"
    severity = Severity.HIGH
    explanation = (
        "Opening files using untrusted paths via fopen(), open(), or std::ifstream allows attackers "
        "to traverse directory hierarchies using '../' sequences to read or overwrite sensitive files."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, context.offset_map)
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


# ── Rule 10: Insecure Randomness (CWE-338) ───────────────────────────────────


class CppInsecureRandomRule(Rule):
    """Detects use of rand() or srand(time(0)) for sensitive operations."""

    id = "APS-CP-CRY-001"
    title = "Cryptographically Weak Pseudorandom Number Generator (rand / srand)"
    cwe = "CWE-338"
    severity = Severity.MEDIUM
    explanation = (
        "The standard C library rand() uses a linear congruential generator with predictable output. "
        "Seeding with srand(time(0)) or srand(time(NULL)) allows attackers to brute-force seeds within "
        "narrow timestamp windows. Use <random> (std::random_device) or arc4random() instead."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pat = re.compile(r"\b(rand\s*\(\s*\)|srand\s*\([^)]*\))", re.MULTILINE)
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message=f"Insecure pseudorandom generator call {m.group(0)}; unsuitable for security tokens or keys.",
                    evidence={"call": m.group(0)},
                )
            )

        return findings


# ── Rule 11: Hard-Coded Credentials (CWE-798) ────────────────────────────────


class CppHardcodedSecretRule(Rule):
    """Detects hard-coded passwords, secrets, and API keys."""

    id = "APS-CP-SEC-001"
    title = "Hard-Coded Cryptographic Secret or Credential"
    cwe = "CWE-798"
    severity = Severity.HIGH
    explanation = (
        "Embedding plaintext credentials, API keys, or private tokens inside source code allows "
        "anyone with repository access or binary disassembly tools to extract secrets."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        # Search variable assignments or #define with sensitive names
        pat = re.compile(
            r"(?i)\b(?:const\s+char\s*\*|char\s+[A-Za-z0-9_]+\[\]\s*=|#\s*define\s+)[A-Za-z0-9_]*(?:password|passwd|secret|api_key|token|private_key)[A-Za-z0-9_]*\s*=?\s*[\"']([^\"']{8,})[\"']"
        )
        for m in pat.finditer(source):
            # Check comment
            tok = _find_token_at(m.start(), tokens)
            if tok and tok.kind == "COMMENT":
                continue

            secret_val = m.group(1)
            # Filter dummy placeholders
            if any(
                dummy in secret_val.lower()
                for dummy in ("placeholder", "example", "changeme", "your_api_key")
            ):
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message="Hardcoded secret or credential detected in source code.",
                    evidence={"entropy": round(_shannon_entropy(secret_val), 2)},
                )
            )

        return findings


# ── Rule 12: Insecure Temporary File Creation (CWE-377) ──────────────────────


class CppInsecureTempFileRule(Rule):
    """Detects dangerous temporary file creation via tmpnam() or mktemp()."""

    id = "APS-CP-IO-002"
    title = "Insecure Temporary File Creation via tmpnam() or mktemp()"
    cwe = "CWE-377"
    severity = Severity.HIGH
    explanation = (
        "Functions tmpnam(), tempnam(), and mktemp() return filenames without atomically creating "
        "the file with exclusive permissions, creating a TOCTOU race condition where attackers "
        "can create symlinks to hijack files. Use mkstemp() or tmpfile() instead."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        pat = re.compile(r"\b(tmpnam|mktemp|tempnam)\s*\(", re.MULTILINE)
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue

            start_u16 = context.offset_map.py_to_utf16(m.start())
            end_u16 = context.offset_map.py_to_utf16(m.end())
            line, col = context.offset_map.utf16_to_pos(start_u16)
            end_line, end_col = context.offset_map.utf16_to_pos(end_u16)

            findings.append(
                self.create_finding(
                    rng=Range(start_line=line, start_col=col, end_line=end_line, end_col=end_col),
                    message=f"Insecure temporary file creation via {m.group(1)}(); use mkstemp() or tmpfile().",
                    evidence={"call": m.group(0)},
                )
            )

        return findings


# ── Rule 13: Uncontrolled Stack Allocation via alloca (CWE-770) ──────────────


class CppAllocaRule(Rule):
    """Detects unbounded stack allocation via alloca()."""

    id = "APS-CP-MEM-007"
    title = "Uncontrolled Stack Allocation via alloca()"
    cwe = "CWE-770"
    severity = Severity.HIGH
    explanation = (
        "Allocating memory on the stack using alloca() with tainted or variable sizes lacks "
        "boundary validation. If the requested size exceeds available stack space, stack overflow "
        "occurs without standard exception handling."
    )

    def match(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []
        source = context.recovered_source
        tokens = context.tokens

        engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, context.offset_map)
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

        pat = re.compile(r"\balloca\s*\(\s*([^;)]+)\)", re.MULTILINE)
        for m in pat.finditer(source):
            if _is_inside_comment_string_or_directive(m.start(), tokens):
                continue
            arg = m.group(1).strip()

            # Ignore small integer constants e.g. alloca(64)
            if arg.isdigit() and int(arg) <= 1024:
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
                        message="Variable stack allocation via alloca() can exhaust stack memory.",
                        evidence={"call": m.group(0), "arg": arg},
                    )
                )

        return findings


# ── Catalog of All Rules ──────────────────────────────────────────────────────

ALL_CPP_RULES: Final[list[Rule]] = [
    CppUnboundedCopyRule(),
    CppOutOfBoundsLengthRule(),
    CppFormatStringRule(),
    CppScanfNoWidthRule(),
    CppCommandInjectionRule(),
    CppIntegerOverflowAllocRule(),
    CppUseAfterFreeRule(),
    CppDoubleFreeRule(),
    CppPathTraversalRule(),
    CppInsecureRandomRule(),
    CppHardcodedSecretRule(),
    CppInsecureTempFileRule(),
    CppAllocaRule(),
]
