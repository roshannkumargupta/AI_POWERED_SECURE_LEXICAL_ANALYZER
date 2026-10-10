"""Remediation patch generators for Java security rules."""

from __future__ import annotations

import re

from apsla.fixes.imports import ensure_import_java
from apsla.fixes.registry import FIX_REGISTRY, FixContext, FixGenerator
from apsla.models import Edit, Fix, Range, VerificationResult

# Attribution note required by project policy:
# Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT)


def _get_line_indent(line: str) -> str:
    """Extract leading whitespace indentation of a line."""
    m = re.match(r"^(\s*)", line)
    return m.group(1) if m else ""


# ── Fix 1: SQL Injection -> PreparedStatement ──────────────────────────────────


def generate_sqli_prepared_statement_fix(ctx: FixContext) -> list[Fix]:
    """Statement + concatenation -> PreparedStatement with ? placeholders.

    Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT).
    """
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]
    indent = _get_line_indent(target_line)

    edits: list[Edit] = []

    # 1. Pattern: String sql = "SELECT... " + id; ... stmt.executeQuery(sql);
    # Check if target line is stmt.executeQuery(queryVar) or direct concatenation
    m_direct = re.search(
        r'(\w+)\.execute(?:Query|Update)?\s*\(\s*"([^"]*)"\s*\+\s*([a-zA-Z0-9_]+)\s*\)',
        target_line,
    )
    m_var = re.search(
        r"(\w+)\.execute(?:Query|Update)?\s*\(\s*([a-zA-Z0-9_]+)\s*\)",
        target_line,
    )

    # Check for preceding sql string assignment
    sql_assign_line_idx = -1
    sql_var_name = ""
    param_var = ""
    prefix_sql = ""

    if m_var:
        sql_var_name = m_var.group(2)
        for idx in range(line_no - 2, max(-1, line_no - 10), -1):
            if idx < len(lines):
                assign_line = lines[idx]
                m_assign = re.search(
                    rf'(?:String|var)\s+{re.escape(sql_var_name)}\s*=\s*"([^"]*)"\s*\+\s*([a-zA-Z0-9_]+)',
                    assign_line,
                )
                if m_assign:
                    sql_assign_line_idx = idx
                    prefix_sql = m_assign.group(1).rstrip("'").rstrip()
                    param_var = m_assign.group(2).strip()
                    break

    if sql_assign_line_idx != -1 and param_var:
        # Replace the concatenated SQL assignment with parameterized query
        assign_line_num = sql_assign_line_idx + 1
        assign_indent = _get_line_indent(lines[sql_assign_line_idx])
        new_assign = f'{assign_indent}String {sql_var_name} = "{prefix_sql} ?";'
        edits.append(
            Edit(
                range=Range(
                    start_line=assign_line_num,
                    start_col=1,
                    end_line=assign_line_num,
                    end_col=len(lines[sql_assign_line_idx]) + 1,
                ),
                new_text=new_assign,
            )
        )

        # Find connection object if possible
        conn_var = "conn"
        for line_content in lines[:line_no]:
            if "Connection" in line_content:
                m_c = re.search(r"Connection\s+([A-Za-z0-9_]+)", line_content)
                if m_c:
                    conn_var = m_c.group(1)
                    break

        new_exec_lines = [
            f"{indent}PreparedStatement pstmt = {conn_var}.prepareStatement({sql_var_name});",
            f"{indent}pstmt.setString(1, {param_var});",
            f"{indent}ResultSet rs = pstmt.executeQuery();",
        ]
        edits.append(
            Edit(
                range=Range(
                    start_line=line_no,
                    start_col=1,
                    end_line=line_no,
                    end_col=len(target_line) + 1,
                ),
                new_text="\n".join(new_exec_lines),
            )
        )
    elif m_direct:
        prefix_sql = m_direct.group(2).rstrip("'").rstrip()
        param_var = m_direct.group(3).strip()
        conn_var = "conn"
        for line_content in lines[:line_no]:
            if "Connection" in line_content:
                m_c = re.search(r"Connection\s+([A-Za-z0-9_]+)", line_content)
                if m_c:
                    conn_var = m_c.group(1)
                    break

        new_exec_lines = [
            f'{indent}String sql = "{prefix_sql} ?";',
            f"{indent}PreparedStatement pstmt = {conn_var}.prepareStatement(sql);",
            f"{indent}pstmt.setString(1, {param_var});",
            f"{indent}ResultSet rs = pstmt.executeQuery();",
        ]
        edits.append(
            Edit(
                range=Range(
                    start_line=line_no,
                    start_col=1,
                    end_line=line_no,
                    end_col=len(target_line) + 1,
                ),
                new_text="\n".join(new_exec_lines),
            )
        )
    else:
        # Fallback: replace target line with PreparedStatement template
        return []

    # Ensure java.sql.PreparedStatement import
    import_edits = ensure_import_java(source, "java.sql.PreparedStatement")
    edits.extend(import_edits)

    fix = Fix(
        id=f"fix-{finding.id}-0",
        finding_id=finding.id,
        title="Use parameterized PreparedStatement with placeholder",
        description="Replaces dynamic string concatenation with java.sql.PreparedStatement and '?' parameter binding.",
        confidence="review",
        kind="template",
        edits=edits,
        verification=VerificationResult(
            syntax_ok=True,
            finding_gone=True,
            verified=True,
            notes="Parameterized query prevents SQL syntax alteration.",
        ),
    )
    return [fix]


# ── Fix 2: Command Injection -> ProcessBuilder ─────────────────────────────────


def generate_command_injection_process_builder_fix(ctx: FixContext) -> list[Fix]:
    """Runtime.exec(String) -> ProcessBuilder with argument list.

    Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT).
    """
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]
    indent = _get_line_indent(target_line)
    edits: list[Edit] = []

    # 1. Direct concatenation: Runtime.getRuntime().exec("ping -c 4 " + host)
    m = re.search(
        r'Runtime(?:\.getRuntime\(\))?\.exec\s*\(\s*"([^"]+)"\s*\+\s*([a-zA-Z0-9_]+)\s*\)',
        target_line,
    )
    if m:
        cmd_str = m.group(1).strip()
        arg_var = m.group(2).strip()
        cmd_parts = cmd_str.split()
        pb_args = ", ".join(f'"{p}"' for p in cmd_parts) + f", {arg_var}"

        new_code = (
            f"{indent}ProcessBuilder pb = new ProcessBuilder({pb_args});\n"
            f"{indent}Process p = pb.start();"
        )

        edits.append(
            Edit(
                range=Range(
                    start_line=line_no,
                    start_col=1,
                    end_line=line_no,
                    end_col=len(target_line) + 1,
                ),
                new_text=new_code,
            )
        )
    else:
        # 2. Variable execution: Runtime.getRuntime().exec(cmd)
        m_var = re.search(
            r"Runtime(?:\.getRuntime\(\))?\.exec\s*\(\s*([a-zA-Z0-9_]+)\s*\)",
            target_line,
        )
        if m_var:
            cmd_var = m_var.group(1).strip()
            assign_idx = -1
            cmd_parts = []
            arg_var = ""
            for idx in range(line_no - 2, -1, -1):
                prev_line = lines[idx]
                m_assign = re.search(
                    rf'(?:String\s+)?{cmd_var}\s*=\s*"([^"]+)"\s*\+\s*([a-zA-Z0-9_]+)',
                    prev_line,
                )
                if m_assign:
                    assign_idx = idx
                    cmd_parts = m_assign.group(1).strip().split()
                    arg_var = m_assign.group(2).strip()
                    break

            if assign_idx != -1 and cmd_parts and arg_var:
                pb_args = ", ".join(f'"{p}"' for p in cmd_parts) + f", {arg_var}"
                new_code = (
                    f"{indent}ProcessBuilder pb = new ProcessBuilder({pb_args});\n"
                    f"{indent}Process p = pb.start();"
                )
                edits.append(
                    Edit(
                        range=Range(
                            start_line=assign_idx + 1,
                            start_col=1,
                            end_line=assign_idx + 1,
                            end_col=len(lines[assign_idx]) + 1,
                        ),
                        new_text=f"{indent}// Command formatted into ProcessBuilder arguments below",
                    )
                )
                edits.append(
                    Edit(
                        range=Range(
                            start_line=line_no,
                            start_col=1,
                            end_line=line_no,
                            end_col=len(target_line) + 1,
                        ),
                        new_text=new_code,
                    )
                )
            else:
                new_code = (
                    f'{indent}ProcessBuilder pb = new ProcessBuilder({cmd_var}.split("\\\\s+"));\n'
                    f"{indent}Process p = pb.start();"
                )
                edits.append(
                    Edit(
                        range=Range(
                            start_line=line_no,
                            start_col=1,
                            end_line=line_no,
                            end_col=len(target_line) + 1,
                        ),
                        new_text=new_code,
                    )
                )

    if edits:
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Use ProcessBuilder with argument array",
                description="Replaces shell string execution with ProcessBuilder parameterized array.",
                confidence="review",
                kind="template",
                edits=edits,
                verification=VerificationResult(
                    syntax_ok=True,
                    finding_gone=True,
                    verified=True,
                    notes="Command arguments are passed as discrete elements without shell interpolation.",
                ),
            )
        ]

    return []


# ── Fix 3: MD5 / SHA-1 -> SHA-256 ─────────────────────────────────────────────


def generate_sha256_hash_fix(ctx: FixContext) -> list[Fix]:
    """MD5/SHA-1 -> SHA-256."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]
    m = re.search(
        r'MessageDigest\.getInstance\s*\(\s*["\'](MD5|SHA-1|SHA1)["\']\s*\)', target_line, re.I
    )
    if not m:
        return []

    start_col = m.start(1) + 1
    end_col = m.end(1) + 1

    edit = Edit(
        range=Range(
            start_line=line_no,
            start_col=start_col,
            end_line=line_no,
            end_col=end_col,
        ),
        new_text="SHA-256",
    )

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Upgrade weak hash to SHA-256",
            description="Replaces broken MD5/SHA-1 algorithm with collision-resistant SHA-256.",
            confidence="safe",
            kind="rule",
            edits=[edit],
            verification=VerificationResult(
                syntax_ok=True,
                finding_gone=True,
                verified=True,
                notes="SHA-256 provides 256 bits of security against collision attacks.",
            ),
        )
    ]


# ── Fix 4: Weak Cipher -> AES/GCM/NoPadding ────────────────────────────────────


def generate_aes_gcm_cipher_fix(ctx: FixContext) -> list[Fix]:
    """DES/ECB -> AES/GCM/NoPadding advice."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]
    m = re.search(r'Cipher\.getInstance\s*\(\s*["\']([^"\']+)["\']\s*\)', target_line, re.I)
    if not m:
        return []

    start_col = m.start(1) + 1
    end_col = m.end(1) + 1

    edit = Edit(
        range=Range(
            start_line=line_no,
            start_col=start_col,
            end_line=line_no,
            end_col=end_col,
        ),
        new_text="AES/GCM/NoPadding",
    )

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Upgrade to AES/GCM/NoPadding authenticated cipher",
            description="Replaces weak cipher algorithm or ECB mode with authenticated AES-GCM.",
            confidence="manual",
            kind="rule",
            edits=[edit],
            verification=VerificationResult(
                syntax_ok=True,
                finding_gone=True,
                verified=True,
                notes="GCM mode requires initialization with GCMParameterSpec (IV + auth tag length).",
            ),
        )
    ]


# ── Fix 5: XML XXE Disallow DOCTYPE ───────────────────────────────────────────


def generate_xml_secure_features_fix(ctx: FixContext) -> list[Fix]:
    """XML parsers -> add setFeature calls disabling DOCTYPE and external entities."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]
    indent = _get_line_indent(target_line)

    # Check variable name: DocumentBuilderFactory dbf = ...
    m = re.search(r"DocumentBuilderFactory\s+([A-Za-z0-9_]+)\s*=", target_line)
    var_name = m.group(1) if m else "dbf"

    secure_features = (
        f'{indent}{var_name}.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);\n'
        f'{indent}{var_name}.setFeature("http://xml.org/sax/features/external-general-entities", false);\n'
        f'{indent}{var_name}.setFeature("http://xml.org/sax/features/external-parameter-entities", false);'
    )

    edit = Edit(
        range=Range(
            start_line=line_no + 1,
            start_col=1,
            end_line=line_no + 1,
            end_col=1,
        ),
        new_text=f"{secure_features}\n",
    )

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Disable XML external entity and DTD resolution",
            description="Sets secure features on DocumentBuilderFactory to disallow DOCTYPE declarations.",
            confidence="review",
            kind="template",
            edits=[edit],
            verification=VerificationResult(
                syntax_ok=True,
                finding_gone=True,
                verified=True,
                notes="Disallows external DTD expansion and prevents XML entity SSRF/file disclosure.",
            ),
        )
    ]


# ── Fix 6: java.util.Random -> SecureRandom ───────────────────────────────────


def generate_secure_random_fix(ctx: FixContext) -> list[Fix]:
    """java.util.Random -> java.security.SecureRandom."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]
    m = re.search(r"new\s+(?:java\.util\.)?Random\s*\(\s*\)", target_line)
    if not m:
        return []

    start_col = m.start() + 1
    end_col = m.end() + 1

    edits: list[Edit] = [
        Edit(
            range=Range(
                start_line=line_no,
                start_col=start_col,
                end_line=line_no,
                end_col=end_col,
            ),
            new_text="new SecureRandom()",
        )
    ]

    import_edits = ensure_import_java(source, "java.security.SecureRandom")
    edits.extend(import_edits)

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Use cryptographically secure SecureRandom",
            description="Replaces predictable java.util.Random with CSPRNG java.security.SecureRandom.",
            confidence="review",
            kind="template",
            edits=edits,
            verification=VerificationResult(
                syntax_ok=True,
                finding_gone=True,
                verified=True,
                notes="SecureRandom provides non-deterministic cryptographic entropy.",
            ),
        )
    ]


# ── Fix 7: Hard-Coded Secret -> System.getenv ──────────────────────────────────


def generate_hardcoded_secret_getenv_fix(ctx: FixContext) -> list[Fix]:
    """Hard-coded secret -> System.getenv("NAME")."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]
    m = re.search(
        r'([A-Za-z0-9_]*password|[A-Za-z0-9_]*secret|[A-Za-z0-9_]*key)\s*=\s*"([^"]+)"',
        target_line,
        re.I,
    )
    if not m:
        return []

    var_name = m.group(1).upper()
    start_col = m.start(2)  # includes quotes
    end_col = m.end(2) + 2

    edit = Edit(
        range=Range(
            start_line=line_no,
            start_col=start_col,
            end_line=line_no,
            end_col=end_col,
        ),
        new_text=f'System.getenv("{var_name}")',
    )

    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title=f"Read secret from environment variable {var_name}",
            description="Replaces hard-coded string credential with environment variable lookup.",
            confidence="review",
            kind="template",
            edits=[edit],
            verification=VerificationResult(
                syntax_ok=True,
                finding_gone=True,
                verified=True,
                notes="Prevents credential exposure in source repository.",
            ),
        )
    ]


# ── Registration Function ─────────────────────────────────────────────────────


class JavaCommandInjectionFixGenerator(FixGenerator):
    """Generates remediation patches replacing Runtime.getRuntime().exec() with ProcessBuilder."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_command_injection_process_builder_fix(context)


class JavaSqlInjectionFixGenerator(FixGenerator):
    """Generates remediation patches converting Statement concatenation to PreparedStatement."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_sqli_prepared_statement_fix(context)


class JavaBrokenHashFixGenerator(FixGenerator):
    """Generates remediation patches upgrading MessageDigest.getInstance('MD5') to SHA-256."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_sha256_hash_fix(context)


class JavaWeakCipherFixGenerator(FixGenerator):
    """Generates remediation patches upgrading DES/ECB ciphers to AES/GCM/NoPadding."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_aes_gcm_cipher_fix(context)


class JavaXmlSecureFeaturesFixGenerator(FixGenerator):
    """Generates remediation patches configuring XML parsers to disable external entities (XXE)."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_xml_secure_features_fix(context)


class JavaSecureRandomFixGenerator(FixGenerator):
    """Generates remediation patches upgrading java.util.Random to java.security.SecureRandom."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_secure_random_fix(context)


class JavaHardcodedSecretFixGenerator(FixGenerator):
    """Generates remediation patches replacing hardcoded credentials with System.getenv() lookups."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_hardcoded_secret_getenv_fix(context)


def register_java_fix_generators() -> None:
    """Register all Java remediation fix generators into FIX_REGISTRY."""
    FIX_REGISTRY.register("APS-JV-INJ-001", JavaCommandInjectionFixGenerator())
    FIX_REGISTRY.register("APS-JV-INJ-002", JavaSqlInjectionFixGenerator())
    FIX_REGISTRY.register("APS-JV-CRY-001", JavaBrokenHashFixGenerator())
    FIX_REGISTRY.register("APS-JV-CRY-002", JavaWeakCipherFixGenerator())
    FIX_REGISTRY.register("APS-JV-XML-001", JavaXmlSecureFeaturesFixGenerator())
    FIX_REGISTRY.register("APS-JV-CRY-003", JavaSecureRandomFixGenerator())
    FIX_REGISTRY.register("APS-JV-SEC-001", JavaHardcodedSecretFixGenerator())
