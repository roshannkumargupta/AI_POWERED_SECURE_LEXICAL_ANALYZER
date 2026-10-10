"""Automated fix generators for JavaScript security findings.

Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT).
"""

from __future__ import annotations

import re

from apsla.fixes.imports import ensure_import_javascript
from apsla.fixes.registry import FIX_REGISTRY, FixContext, FixGenerator
from apsla.models import Edit, Fix, Range, VerificationResult


def _create_initial_verification() -> VerificationResult:
    return VerificationResult(
        syntax_ok=False,
        finding_gone=False,
        new_findings=[],
        verified=False,
        notes="Pending shadow verification",
    )


def _get_line_indent(line: str) -> str:
    m = re.match(r"^(\s*)", line)
    return m.group(1) if m else ""


# ── Fix 1: DOM XSS -> textContent (review) / document.write (manual) ─────────


def generate_dom_xss_fix(ctx: FixContext) -> list[Fix]:
    """Remediate DOM XSS by replacing innerHTML/outerHTML with textContent."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    # Case A: innerHTML / outerHTML assignment -> textContent
    m_html = re.search(r"\.(innerHTML|outerHTML)\b", target_line)
    if m_html:
        prop = m_html.group(1)
        col_start = m_html.start() + 2  # right after the dot
        col_end = col_start + len(prop)
        edit = Edit(
            range=Range(
                start_line=line_no,
                start_col=col_start,
                end_line=line_no,
                end_col=col_end,
            ),
            new_text="textContent",
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Replace innerHTML with textContent",
                description="Assigns data as plain text via textContent, eliminating HTML parsing and XSS.",
                confidence="review",
                kind="rule",
                edits=[edit],
                verification=_create_initial_verification(),
            )
        ]

    # Case B: document.write -> manual guidance
    if "document.write" in target_line or "document.writeln" in target_line:
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Replace document.write with DOM manipulation",
                description="Manual remediation: replace document.write() with document.getElementById(...).textContent.",
                confidence="manual",
                kind="rule",
                edits=[],
                verification=VerificationResult(
                    syntax_ok=True,
                    finding_gone=False,
                    new_findings=[],
                    verified=False,
                    notes="Manual review required: refactor document.write to modern DOM manipulation.",
                ),
            )
        ]

    return []


# ── Fix 2: React dangerouslySetInnerHTML -> DOMPurify wrapper (review) ───────


def generate_react_xss_fix(ctx: FixContext) -> list[Fix]:
    """Wrap dangerouslySetInnerHTML HTML expressions with DOMPurify.sanitize()."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    # Pattern: dangerouslySetInnerHTML={{ __html: expr }}
    m = re.search(r"(__html\s*:\s*)([^}]+)", target_line)
    if not m:
        return []

    expr = m.group(2).strip()
    if "DOMPurify.sanitize" in expr:
        return []

    expr_start_col = m.start(2) + 1
    expr_end_col = expr_start_col + len(m.group(2))

    edits: list[Edit] = [
        Edit(
            range=Range(
                start_line=line_no,
                start_col=expr_start_col,
                end_line=line_no,
                end_col=expr_end_col,
            ),
            new_text=f"DOMPurify.sanitize({expr})",
        )
    ]

    # Add DOMPurify import
    import_edits = ensure_import_javascript(
        source,
        "dompurify",
        esm_stmt="import DOMPurify from 'dompurify';",
        cjs_stmt="const DOMPurify = require('dompurify');",
    )
    edits.extend(import_edits)

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Sanitize HTML with DOMPurify.sanitize()",
            description="Wraps raw HTML content with DOMPurify.sanitize() before rendering in React.",
            confidence="review",
            kind="rule",
            edits=edits,
            verification=_create_initial_verification(),
        )
    ]


# ── Fix 3: eval -> JSON.parse (review) ───────────────────────────────────────


def generate_eval_fix(ctx: FixContext) -> list[Fix]:
    """Replace eval(str) with JSON.parse(str) for safe deserialization."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    m = re.search(r"\beval\s*\(", target_line)
    if not m:
        return []

    start_col = m.start() + 1
    end_col = m.start() + 5  # "eval"

    edit = Edit(
        range=Range(
            start_line=line_no,
            start_col=start_col,
            end_line=line_no,
            end_col=end_col,
        ),
        new_text="JSON.parse",
    )

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Replace eval() with JSON.parse()",
            description="Replaces dynamic code evaluation with safe JSON data deserialization.",
            confidence="review",
            kind="rule",
            edits=[edit],
            verification=_create_initial_verification(),
        )
    ]


# ── Fix 4: Command Injection -> execFile with argument array (review) ────────


def generate_command_injection_fix(ctx: FixContext) -> list[Fix]:
    """Replace child_process.exec with child_process.execFile and argument array."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    # Pattern: exec("ping -c 1 " + ip, callback) or exec(`ping -c 1 ${ip}`, callback)
    m_concat = re.search(
        r'(\b(?:child_process\.)?)exec\s*\(\s*["\']([a-zA-Z0-9_\-]+)\s+([^"\']*)["\']\s*\+\s*([a-zA-Z0-9_$.]+)\s*(?:,\s*([^)]+))?\)',
        target_line,
    )
    if m_concat:
        prefix = m_concat.group(1)
        binary = m_concat.group(2)
        flag_str = m_concat.group(3).strip()
        var_name = m_concat.group(4)
        rest = m_concat.group(5)

        flags = [f'"{f}"' for f in flag_str.split() if f]
        arg_array = ", ".join([*flags, var_name])

        new_call = f'{prefix}execFile("{binary}", [{arg_array}]'
        if rest:
            new_call += f", {rest}"
        new_call += ")"

        start_col = m_concat.start() + 1
        end_col = m_concat.end() + 1

        edit = Edit(
            range=Range(
                start_line=line_no,
                start_col=start_col,
                end_line=line_no,
                end_col=end_col,
            ),
            new_text=new_call,
        )

        edits = [edit]
        if not prefix:
            # Need to import execFile
            edits.extend(
                ensure_import_javascript(
                    source,
                    "child_process",
                    esm_stmt="import { execFile } from 'child_process';",
                    cjs_stmt="const { execFile } = require('child_process');",
                )
            )

        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Replace exec() with execFile() and argument array",
                description="Executes binary directly with discrete arguments, bypassing shell interpolation.",
                confidence="review",
                kind="rule",
                edits=edits,
                verification=_create_initial_verification(),
            )
        ]

    # Simpler pattern: exec(cmd, callback) -> execFile
    m_simple = re.search(r"\bexec\s*\(", target_line)
    if m_simple:
        start_col = m_simple.start() + 1
        end_col = m_simple.start() + 5
        edit = Edit(
            range=Range(
                start_line=line_no,
                start_col=start_col,
                end_line=line_no,
                end_col=end_col,
            ),
            new_text="execFile",
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Use execFile instead of exec",
                description="Switches to execFile to avoid invoking a system shell.",
                confidence="review",
                kind="rule",
                edits=[edit],
                verification=_create_initial_verification(),
            )
        ]

    return []


# ── Fix 5: SQL Injection -> Parameterized Query (review) ─────────────────────


def generate_sqli_fix(ctx: FixContext) -> list[Fix]:
    """Replace SQL concatenation or template literal with parameterized query placeholders."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    # Pattern: db.query("SELECT ... WHERE id = " + id) or db.query(`SELECT ... ${id}`)
    m_direct_concat = re.search(
        r'(\b\w+\.query\s*\(\s*)["\']([^"\']+)["\']\s*\+\s*([a-zA-Z0-9_$.]+)\s*\)',
        target_line,
    )
    if m_direct_concat:
        call_prefix = m_direct_concat.group(1)
        sql_prefix = m_direct_concat.group(2).rstrip()
        var_name = m_direct_concat.group(3)

        new_call = f'{call_prefix}"{sql_prefix} ?", [{var_name}])'
        edit = Edit(
            range=Range(
                start_line=line_no,
                start_col=m_direct_concat.start() + 1,
                end_line=line_no,
                end_col=m_direct_concat.end() + 1,
            ),
            new_text=new_call,
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Parameterize SQL query with ? placeholder",
                description="Substitutes concatenated variables with ? placeholder and parameter list.",
                confidence="review",
                kind="rule",
                edits=[edit],
                verification=_create_initial_verification(),
            )
        ]

    # Pattern: db.query(`SELECT ... ${id}`)
    m_direct_template = re.search(
        r"(\b\w+\.query\s*\(\s*)`([^`]*)\$\{([a-zA-Z0-9_$.]+)\}([^`]*)`\s*\)",
        target_line,
    )
    if m_direct_template:
        call_prefix = m_direct_template.group(1)
        sql_pre = m_direct_template.group(2)
        var_name = m_direct_template.group(3)
        sql_post = m_direct_template.group(4)

        new_call = f'{call_prefix}"{sql_pre}?{sql_post}", [{var_name}])'
        edit = Edit(
            range=Range(
                start_line=line_no,
                start_col=m_direct_template.start() + 1,
                end_line=line_no,
                end_col=m_direct_template.end() + 1,
            ),
            new_text=new_call,
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Parameterize template literal query",
                description="Replaces template interpolation with ? placeholder and parameter array.",
                confidence="review",
                kind="rule",
                edits=[edit],
                verification=_create_initial_verification(),
            )
        ]

    # Check for preceding assignment: const query = "..." + id or `...${id}`
    m_var_call = re.search(r"(\b\w+\.query\s*\(\s*)([a-zA-Z0-9_]+)\s*\)", target_line)
    if m_var_call:
        query_var = m_var_call.group(2)
        for idx in range(line_no - 2, max(-1, line_no - 8), -1):
            if idx < len(lines):
                line_text = lines[idx]
                m_assign_t = re.search(
                    rf"\b(?:const|let|var)\s+{re.escape(query_var)}\s*=\s*`([^`]*)\$\{{([a-zA-Z0-9_$.]+)\}}([^`]*)`",
                    line_text,
                )
                if m_assign_t:
                    sql_pre = m_assign_t.group(1)
                    param_var = m_assign_t.group(2)
                    sql_post = m_assign_t.group(3)
                    indent = _get_line_indent(line_text)

                    new_assign = f'{indent}const {query_var} = "{sql_pre}?{sql_post}";'
                    edit_assign = Edit(
                        range=Range(
                            start_line=idx + 1,
                            start_col=1,
                            end_line=idx + 1,
                            end_col=len(line_text) + 1,
                        ),
                        new_text=new_assign,
                    )
                    new_call = f"{m_var_call.group(1)}{query_var}, [{param_var}])"
                    edit_call = Edit(
                        range=Range(
                            start_line=line_no,
                            start_col=m_var_call.start() + 1,
                            end_line=line_no,
                            end_col=m_var_call.end() + 1,
                        ),
                        new_text=new_call,
                    )
                    return [
                        Fix(
                            id=f"fix-{finding.id}-0",
                            finding_id=finding.id,
                            title="Parameterize query variable with ? placeholder",
                            description="Converts template query to placeholder and passes parameters array.",
                            confidence="review",
                            kind="rule",
                            edits=[edit_assign, edit_call],
                            verification=_create_initial_verification(),
                        )
                    ]

    return []


# ── Fix 6: Math.random -> crypto.randomUUID (review) ─────────────────────────


def generate_random_fix(ctx: FixContext) -> list[Fix]:
    """Replace Math.random() with crypto.randomUUID() for tokens/keys."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    m_math = re.search(r"Math\.random\s*\(\s*\)(?:\s*\.\s*toString\s*\([^)]*\))?", target_line)
    if not m_math:
        return []

    start_col = m_math.start() + 1
    end_col = m_math.end() + 1

    edits = [
        Edit(
            range=Range(
                start_line=line_no,
                start_col=start_col,
                end_line=line_no,
                end_col=end_col,
            ),
            new_text="crypto.randomUUID()",
        )
    ]

    # Ensure crypto import in Node.js environments
    if "require(" in source or "module.exports" in source:
        import_edits = ensure_import_javascript(
            source,
            "crypto",
            esm_stmt="import crypto from 'crypto';",
            cjs_stmt="const crypto = require('crypto');",
        )
        edits.extend(import_edits)

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Replace Math.random() with crypto.randomUUID()",
            description="Uses cryptographically secure random UUID generation instead of pseudo-randomness.",
            confidence="review",
            kind="rule",
            edits=edits,
            verification=_create_initial_verification(),
        )
    ]


# ── Fix 7: Weak Hash MD5/SHA1 -> SHA-256 (review) ────────────────────────────


def generate_weak_hash_fix(ctx: FixContext) -> list[Fix]:
    """Replace md5 or sha1 with sha256."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    m = re.search(r"createHash\s*\(\s*([\"'])(md5|sha1)\1\s*\)", target_line, re.IGNORECASE)
    if not m:
        return []

    algo_start_col = m.start(2) + 1
    algo_end_col = algo_start_col + len(m.group(2))

    edit = Edit(
        range=Range(
            start_line=line_no,
            start_col=algo_start_col,
            end_line=line_no,
            end_col=algo_end_col,
        ),
        new_text="sha256",
    )

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Upgrade weak hash to SHA-256",
            description="Replaces broken MD5/SHA1 hash algorithm with cryptographically strong SHA-256.",
            confidence="review",
            kind="rule",
            edits=[edit],
            verification=_create_initial_verification(),
        )
    ]


# ── Fix 8: Hard-Coded Secret -> process.env (review) ─────────────────────────


def generate_hardcoded_secret_fix(ctx: FixContext) -> list[Fix]:
    """Replace hard-coded credential string with process.env.NAME lookup."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    m = re.search(
        r"\b(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*(['\"][^'\"]{8,}['\"])",
        target_line,
    )
    if not m:
        return []

    var_name = m.group(1)
    env_name = re.sub(r"([a-z])([A-Z])", r"\1_\2", var_name).upper()

    val_start_col = m.start(2) + 1
    val_end_col = val_start_col + len(m.group(2))

    edit = Edit(
        range=Range(
            start_line=line_no,
            start_col=val_start_col,
            end_line=line_no,
            end_col=val_end_col,
        ),
        new_text=f"process.env.{env_name} || ''",
    )

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title=f"Read credential from process.env.{env_name}",
            description="Eliminates hard-coded secret by reading from environment variables at runtime.",
            confidence="review",
            kind="rule",
            edits=[edit],
            verification=_create_initial_verification(),
        )
    ]


# ── Fix 9: Disabled TLS -> rejectUnauthorized: true / remove (safe) ──────────


def generate_disabled_tls_fix(ctx: FixContext) -> list[Fix]:
    """Enable TLS verification by fixing rejectUnauthorized: true or removing disable flag."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    # Case A: rejectUnauthorized: false -> rejectUnauthorized: true
    m_opt = re.search(r"rejectUnauthorized\s*:\s*false", target_line)
    if m_opt:
        edit = Edit(
            range=Range(
                start_line=line_no,
                start_col=m_opt.start() + 1,
                end_line=line_no,
                end_col=m_opt.end() + 1,
            ),
            new_text="rejectUnauthorized: true",
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Enable TLS certificate verification",
                description="Sets rejectUnauthorized: true to enforce authentic SSL/TLS certificate validation.",
                confidence="safe",
                kind="rule",
                edits=[edit],
                verification=_create_initial_verification(),
            )
        ]

    # Case B: NODE_TLS_REJECT_UNAUTHORIZED = "0" -> comment out
    m_env = re.search(
        r"process\.env\.NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0['\"]?", target_line
    )
    if m_env:
        indent = _get_line_indent(target_line)
        edit = Edit(
            range=Range(
                start_line=line_no,
                start_col=1,
                end_line=line_no,
                end_col=len(target_line) + 1,
            ),
            new_text=f"{indent}// process.env.NODE_TLS_REJECT_UNAUTHORIZED = '1';",
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Remove global TLS verification disablement",
                description="Comments out NODE_TLS_REJECT_UNAUTHORIZED='0' to restore default TLS validation.",
                confidence="safe",
                kind="rule",
                edits=[edit],
                verification=_create_initial_verification(),
            )
        ]

    return []


# ── Registration Function ─────────────────────────────────────────────────────


class JSDOMXSSFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_dom_xss_fix(context)


class JSReactXSSFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_react_xss_fix(context)


class JSCodeInjectionFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_eval_fix(context)


class JSCommandInjectionFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_command_injection_fix(context)


class JSSQLInjectionFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_sqli_fix(context)


class JSRandomFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_random_fix(context)


class JSWeakHashFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_weak_hash_fix(context)


class JSHardcodedSecretFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_hardcoded_secret_fix(context)


class JSDisabledTLSFixGenerator(FixGenerator):
    def generate(self, context: FixContext) -> list[Fix]:
        return generate_disabled_tls_fix(context)


def register_javascript_fix_generators() -> None:
    """Register all JavaScript remediation fix generators into FIX_REGISTRY."""
    FIX_REGISTRY.register("APS-JS-XSS-001", JSDOMXSSFixGenerator())
    FIX_REGISTRY.register("APS-JS-XSS-002", JSReactXSSFixGenerator())
    FIX_REGISTRY.register("APS-JS-INJ-001", JSCodeInjectionFixGenerator())
    FIX_REGISTRY.register("APS-JS-INJ-002", JSCommandInjectionFixGenerator())
    FIX_REGISTRY.register("APS-JS-INJ-003", JSSQLInjectionFixGenerator())
    FIX_REGISTRY.register("APS-JS-CRY-001", JSRandomFixGenerator())
    FIX_REGISTRY.register("APS-JS-CRY-002", JSWeakHashFixGenerator())
    FIX_REGISTRY.register("APS-JS-SEC-001", JSHardcodedSecretFixGenerator())
    FIX_REGISTRY.register("APS-JS-NET-003", JSDisabledTLSFixGenerator())
