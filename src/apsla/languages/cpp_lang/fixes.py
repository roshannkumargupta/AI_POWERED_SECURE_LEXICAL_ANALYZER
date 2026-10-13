"""Automated fix generators for C and C++ security findings."""

from __future__ import annotations

import re

from apsla.fixes.imports import ensure_import_cpp
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


# ── Fix 1: Unbounded Copy: strcpy / gets / sprintf ───────────────────────────


def generate_unbounded_copy_fix(ctx: FixContext) -> list[Fix]:
    """Remediate unbounded copy findings (APS-CP-MEM-001)."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    # Case A: gets(buf) -> fgets(buf, sizeof(buf), stdin)
    m_gets = re.search(r"\bgets\s*\(\s*([A-Za-z0-9_]+)\s*\)", target_line)
    if m_gets:
        buf = m_gets.group(1)
        col_start = m_gets.start() + 1
        col_end = m_gets.end() + 1
        call_edit = Edit(
            range=Range(start_line=line_no, start_col=col_start, end_line=line_no, end_col=col_end),
            new_text=f"fgets({buf}, sizeof({buf}), stdin)",
        )
        import_edits = ensure_import_cpp(source, "stdio.h", filename=getattr(ctx, "filename", ""))
        all_edits = [*import_edits, call_edit]
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Replace gets() with fgets()",
                description="Replaces inherently dangerous gets() with bounded fgets(buf, sizeof buf, stdin).",
                confidence="safe",
                kind="rule",
                edits=all_edits,
                verification=_create_initial_verification(),
            )
        ]

    # Case B: strcpy(dst, src) -> snprintf(dst, sizeof(dst), "%s", src)
    m_strcpy = re.search(r"\bstrcpy\s*\(\s*([A-Za-z0-9_]+)\s*,\s*([^)]+)\s*\)", target_line)
    if m_strcpy:
        dst = m_strcpy.group(1)
        src = m_strcpy.group(2).strip()
        col_start = m_strcpy.start() + 1
        col_end = m_strcpy.end() + 1

        # Check if dst is a fixed array declared in source
        arr_size = _extract_array_size(source, dst)
        if arr_size is not None:
            call_edit = Edit(
                range=Range(
                    start_line=line_no, start_col=col_start, end_line=line_no, end_col=col_end
                ),
                new_text=f'snprintf({dst}, sizeof({dst}), "%s", {src})',
            )
            import_edits = ensure_import_cpp(
                source, "stdio.h", filename=getattr(ctx, "filename", "")
            )
            all_edits = [*import_edits, call_edit]
            return [
                Fix(
                    id=f"fix-{finding.id}-0",
                    finding_id=finding.id,
                    title="Replace strcpy() with snprintf() bounded copy",
                    description='Replaces strcpy() with snprintf(dst, sizeof(dst), "%s", src) guaranteeing bounds and null termination.',
                    confidence="safe",
                    kind="rule",
                    edits=all_edits,
                    verification=_create_initial_verification(),
                )
            ]
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Replace strcpy with bounded copy",
                description="Manual remediation required: ensure destination buffer is bounded using snprintf() or strncpy().",
                confidence="manual",
                kind="rule",
                edits=[],
                verification=VerificationResult(
                    syntax_ok=True,
                    finding_gone=False,
                    new_findings=[],
                    verified=False,
                    notes="Manual review required: destination buffer size could not be determined statically.",
                ),
            )
        ]

    # Case C: sprintf(buf, fmt, ...) -> snprintf(buf, sizeof(buf), fmt, ...)
    m_sprintf = re.search(r"\bsprintf\s*\(\s*([A-Za-z0-9_]+)\s*,\s*(.+)\)", target_line)
    if m_sprintf:
        buf = m_sprintf.group(1)
        rest = m_sprintf.group(2)
        col_start = m_sprintf.start() + 1
        col_end = m_sprintf.end() + 1
        call_edit = Edit(
            range=Range(start_line=line_no, start_col=col_start, end_line=line_no, end_col=col_end),
            new_text=f"snprintf({buf}, sizeof({buf}), {rest})",
        )
        import_edits = ensure_import_cpp(source, "stdio.h", filename=getattr(ctx, "filename", ""))
        all_edits = [*import_edits, call_edit]
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Replace sprintf() with snprintf()",
                description="Replaces unbounded sprintf() with bounded snprintf(buf, sizeof(buf), ...).",
                confidence="review",
                kind="rule",
                edits=all_edits,
                verification=_create_initial_verification(),
            )
        ]

    return []


# ── Fix 2: Format String -> printf("%s", x) ──────────────────────────────────


def generate_format_string_fix(ctx: FixContext) -> list[Fix]:
    """Remediate format string vulnerability (APS-CP-FMT-001)."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    # printf(x) -> printf("%s", x)
    m_printf = re.search(r"\bprintf\s*\(\s*([A-Za-z0-9_]+(?:\s*\[[^\]]+\])?)\s*\)", target_line)
    if m_printf:
        arg = m_printf.group(1).strip()
        col_start = m_printf.start() + 1
        col_end = m_printf.end() + 1
        call_edit = Edit(
            range=Range(start_line=line_no, start_col=col_start, end_line=line_no, end_col=col_end),
            new_text=f'printf("%s", {arg})',
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Add explicit '%s' format specifier to printf()",
                description="Prevents format string injection by supplying static '%s' specifier.",
                confidence="safe",
                kind="rule",
                edits=[call_edit],
                verification=_create_initial_verification(),
            )
        ]

    # fprintf(stream, x) -> fprintf(stream, "%s", x)
    m_fprintf = re.search(
        r"\bfprintf\s*\(\s*([^,]+)\s*,\s*([A-Za-z0-9_]+(?:\s*\[[^\]]+\])?)\s*\)",
        target_line,
    )
    if m_fprintf:
        stream = m_fprintf.group(1).strip()
        arg = m_fprintf.group(2).strip()
        col_start = m_fprintf.start() + 1
        col_end = m_fprintf.end() + 1
        call_edit = Edit(
            range=Range(start_line=line_no, start_col=col_start, end_line=line_no, end_col=col_end),
            new_text=f'fprintf({stream}, "%s", {arg})',
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Add explicit '%s' format specifier to fprintf()",
                description="Prevents format string injection by supplying static '%s' specifier.",
                confidence="safe",
                kind="rule",
                edits=[call_edit],
                verification=_create_initial_verification(),
            )
        ]

    return []


# ── Fix 3: scanf without Width -> scanf("%<size-1>s", buf) ───────────────────


def generate_scanf_fix(ctx: FixContext) -> list[Fix]:
    """Remediate unbounded scanf '%s' (APS-CP-MEM-003)."""
    source = ctx.source
    finding = ctx.finding
    line_no = finding.range.start_line
    lines = source.splitlines()

    if not (1 <= line_no <= len(lines)):
        return []

    target_line = lines[line_no - 1]

    m_scanf = re.search(r'\bscanf\s*\(\s*"%s"\s*,\s*([A-Za-z0-9_]+)\s*\)', target_line)
    if m_scanf:
        buf = m_scanf.group(1).strip()
        col_start = m_scanf.start() + 1
        col_end = m_scanf.end() + 1

        arr_size = _extract_array_size(source, buf)
        width = (arr_size - 1) if (arr_size and arr_size > 1) else 63
        call_edit = Edit(
            range=Range(start_line=line_no, start_col=col_start, end_line=line_no, end_col=col_end),
            new_text=f'scanf("%{width}s", {buf})',
        )
        return [
            Fix(
                id=f"fix-{finding.id}-0",
                finding_id=finding.id,
                title="Add explicit field width to scanf()",
                description=f"Constrains maximum input length to %{width}s to prevent buffer overflow.",
                confidence="review",
                kind="rule",
                edits=[call_edit],
                verification=_create_initial_verification(),
            )
        ]

    return []


# ── Fix 4: Command Injection -> execv advice (manual) ─────────────────────────


def generate_command_injection_fix(ctx: FixContext) -> list[Fix]:
    """Provide remediation advice for command injection (APS-CP-INJ-001)."""
    finding = ctx.finding
    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Replace system() with execv() argument array",
            description="Manual remediation required: replace system() with execv() or posix_spawn() passing discrete argument vectors.",
            confidence="manual",
            kind="rule",
            edits=[],
            verification=VerificationResult(
                syntax_ok=True,
                finding_gone=False,
                new_findings=[],
                verified=False,
                notes="Manual refactor: pass arguments as an argv array rather than concatenating into a shell command.",
            ),
        )
    ]


# ── Fix 5: Weak Random -> std::random_device advice (manual) ─────────────────


def generate_random_fix(ctx: FixContext) -> list[Fix]:
    """Provide remediation advice for rand() / srand() (APS-CP-CRY-001)."""
    finding = ctx.finding
    return [
        Fix(
            id=f"fix-{finding.id}-0",
            finding_id=finding.id,
            title="Replace rand() with <random> (std::random_device)",
            description="Manual remediation required: use <random> (std::random_device, std::mt19937) in C++ or arc4random() in C.",
            confidence="manual",
            kind="rule",
            edits=[],
            verification=VerificationResult(
                syntax_ok=True,
                finding_gone=False,
                new_findings=[],
                verified=False,
                notes="Manual refactor: use modern cryptographically secure RNG libraries.",
            ),
        )
    ]


# ── Fix Generator Classes ─────────────────────────────────────────────────────


class CppUnboundedCopyFixGenerator(FixGenerator):
    """Generates remediation patches for unbounded C buffer copies (strcpy, gets)."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_unbounded_copy_fix(context)


class CppFormatStringFixGenerator(FixGenerator):
    """Generates remediation patches for non-literal format strings (printf, syslog)."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_format_string_fix(context)


class CppScanfFixGenerator(FixGenerator):
    """Generates remediation patches for unbounded scanf %s buffer reads."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_scanf_fix(context)


class CppCommandInjectionFixGenerator(FixGenerator):
    """Generates remediation patches for system/popen command execution calls."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_command_injection_fix(context)


class CppRandomFixGenerator(FixGenerator):
    """Generates remediation patches upgrading rand() to std::random_device."""

    def generate(self, context: FixContext) -> list[Fix]:
        return generate_random_fix(context)


def register_cpp_fix_generators() -> None:
    """Register all C/C++ remediation fix generators into FIX_REGISTRY."""
    FIX_REGISTRY.register("APS-CP-MEM-001", CppUnboundedCopyFixGenerator())
    FIX_REGISTRY.register("APS-CP-FMT-001", CppFormatStringFixGenerator())
    FIX_REGISTRY.register("APS-CP-MEM-003", CppScanfFixGenerator())
    FIX_REGISTRY.register("APS-CP-INJ-001", CppCommandInjectionFixGenerator())
    FIX_REGISTRY.register("APS-CP-CRY-001", CppRandomFixGenerator())
