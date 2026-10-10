"""Typer command-line interface for APSLA."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from apsla.models import Severity
from apsla.pipeline import Analyzer

app = typer.Typer(
    name="apsla",
    help="SecureLex IDE - Intelligent Static Security Analyzer",
    no_args_is_help=True,
)


@app.callback()
def main_callback() -> None:
    """SecureLex IDE Command Line Interface."""


def _configure_windows_encoding() -> None:
    """Safely configure Windows stdout/stderr UTF-8 encoding inside command runtime."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding:
            if sys.stdout.encoding.lower() != "utf-8":
                try:
                    sys.stdout.reconfigure(encoding="utf-8")
                except Exception:
                    pass
        if hasattr(sys.stderr, "reconfigure") and sys.stderr.encoding:
            if sys.stderr.encoding.lower() != "utf-8":
                try:
                    sys.stderr.reconfigure(encoding="utf-8")
                except Exception:
                    pass


@app.command(name="analyze")
def analyze(
    file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Path to source file to analyze.",
        ),
    ],
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: 'text' or 'json'.",
        ),
    ] = "text",
    language: Annotated[
        str,
        typer.Option(
            "--language",
            "-l",
            help="Target language identifier (default: auto).",
        ),
    ] = "auto",
    ml: Annotated[
        bool,
        typer.Option(
            "--ml/--no-ml",
            help="Enable or disable token machine learning model fusion (default: True).",
        ),
    ] = True,
) -> None:
    """Analyze a source file for security vulnerabilities and taint propagation."""
    _configure_windows_encoding()
    console = Console()

    source = file.read_text(encoding="utf-8", errors="replace")

    from apsla.languages import registry

    if language.lower() == "auto":
        detected = registry.detect(str(file), source)
        target_lang = detected.id if detected else "python"
    else:
        target_lang = language

    analyzer = Analyzer()
    result = analyzer.analyze(
        source=source,
        language=target_lang,
        filename=str(file),
        options={"ml": ml, "fixes": True},
    )

    if format.lower() == "json":
        console.print_json(result.model_dump_json(indent=2))
    else:
        table = Table(
            title=f"APSLA Analysis: {file.name} (Health Score: {result.summary.score}/100)",
            header_style="bold cyan",
            show_lines=True,
        )
        table.add_column("Line", style="bold", width=8, justify="right")
        table.add_column("Severity", width=10, justify="center")
        table.add_column("Rule ID", width=18)
        table.add_column("Message", width=40)
        table.add_column("Taint Path", width=42)

        sev_colors = {
            Severity.CRITICAL: "bold red",
            Severity.HIGH: "red",
            Severity.MEDIUM: "yellow",
            Severity.LOW: "blue",
            Severity.INFO: "dim",
        }

        for f in result.findings:
            if f.suppressed:
                continue

            sev_style = sev_colors.get(f.severity, "white")
            sev_text = f"[{sev_style}]{f.severity.value}[/{sev_style}]"
            line_str = f"{f.range.start_line}:{f.range.start_col}"

            # Format taint path if present
            if f.taint_path:
                path_lines = []
                for idx, step in enumerate(f.taint_path, 1):
                    kind_val = step.step.value if hasattr(step.step, "value") else str(step.step)
                    path_lines.append(
                        f"[cyan]#{idx}[/cyan] [bold]L{step.range.start_line}[/bold] ({kind_val}): {step.note}"
                    )
                taint_str = "\n".join(path_lines)
            else:
                taint_str = "[dim]-[/dim]"

            table.add_row(line_str, sev_text, f.rule_id, f.message, taint_str)

        console.print()
        if result.findings:
            console.print(table)
        else:
            console.print(
                Panel(
                    f"[bold green]No security findings detected in {file.name}. Health score: 100/100[/bold green]",
                    title="Clean",
                )
            )

        # Display verified automated fixes if available
        verified_fixes = []
        for f in result.findings:
            for fix in f.fixes:
                if fix.verification.verified:
                    verified_fixes.append((f, fix))
        if verified_fixes:
            console.print()
            console.print("[bold green]Verified Automated Fixes Available:[/bold green]")
            for f, fix in verified_fixes:
                console.print(
                    f"  • [bold]{fix.title}[/bold] (for {f.rule_id} at line {f.range.start_line})"
                )
                console.print(f"    [dim]{fix.description}[/dim]")

        console.print()
        ml_status = f"{result.engine.ml_mode.upper()} ({result.engine.ml_model_id})"
        console.print(
            f"[bold]Summary:[/bold] Critical: {result.summary.critical} | "
            f"High: {result.summary.high} | Medium: {result.summary.medium} | "
            f"Low: {result.summary.low} | ML: {ml_status} | Total Tokens: {result.summary.tokens_total}"
        )
        console.print()

    has_high_or_crit = any(
        f.severity in (Severity.HIGH, Severity.CRITICAL)
        for f in result.findings
        if not f.suppressed
    )
    if has_high_or_crit:
        raise typer.Exit(code=1)


@app.command(name="fix")
def fix_command(
    file: Path = typer.Argument(..., help="Path to source file to remediate."),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Apply safe and verified fixes to disk, creating a .bak backup.",
    ),
    all_safe: bool = typer.Option(
        False,
        "--all-safe",
        help="Only apply strictly safe fixes (exclude review fixes).",
    ),
    language: str | None = typer.Option(
        None,
        "--language",
        "-l",
        help="Explicit language identifier (auto-detected if omitted).",
    ),
) -> None:
    """Propose or apply automated, verified security fixes to a source file."""
    _configure_windows_encoding()
    console = Console()

    if not file.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {file}")
        raise typer.Exit(code=2)

    try:
        source = file.read_text(encoding="utf-8")
    except Exception as exc:
        console.print(f"[bold red]Error reading file:[/bold red] {exc}")
        raise typer.Exit(code=2)

    from apsla.languages.registry import detect

    plugin = detect(str(file), source) if not language else None
    target_lang = language or (plugin.id if plugin else "python")

    from rich.syntax import Syntax

    from apsla.fixes.engine import fix_all

    allow_review = not all_safe

    new_source, applied_ids, skipped_ids, diff, score_before, score_after = fix_all(
        source,
        language=target_lang,
        filename=file.name,
        allow_review=allow_review,
    )

    console.print()
    console.print(
        Panel(
            f"[bold cyan]APSLA Fix Proposer: {file.name}[/bold cyan]\n"
            f"Health Score: [bold yellow]{score_before}/100[/bold yellow] -> "
            f"[bold green]{score_after}/100[/bold green]\n"
            f"Applied Fixes: {len(applied_ids)} | Skipped / Manual: {len(skipped_ids)}",
            title="Remediation Summary",
        )
    )
    console.print()

    if diff:
        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
        console.print(syntax)
        console.print()
    else:
        console.print("[dim]No verified fixes available or file already clean.[/dim]\n")

    if apply and diff:
        backup_path = file.with_name(f"{file.name}.bak")
        try:
            backup_path.write_text(source, encoding="utf-8")
            file.write_text(new_source, encoding="utf-8")
            console.print(
                f"[bold green]Applied {len(applied_ids)} fix(es). Backup saved to {backup_path.name}[/bold green]\n"
            )
        except Exception as exc:
            console.print(f"[bold red]Failed to write fixed file:[/bold red] {exc}\n")
            raise typer.Exit(code=1)
    elif not apply and diff:
        console.print(
            "[italic dim]Run with --apply to write changes to disk (creates .bak backup).[/italic dim]\n"
        )


@app.command(name="serve")
def serve_command(
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Bind socket to this host (default: 127.0.0.1).",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            help="Bind socket to this port (default: 8000).",
        ),
    ] = 8000,
    reload: Annotated[
        bool,
        typer.Option(
            "--reload",
            help="Enable auto-reload on code change.",
        ),
    ] = False,
) -> None:
    """Start the APSLA FastAPI backend server."""
    _configure_windows_encoding()
    import uvicorn

    console = Console()
    console.print(f"[bold cyan]Starting APSLA server on http://{host}:{port}...[/bold cyan]")
    uvicorn.run("apsla.server.app:app", host=host, port=port, reload=reload)


def main() -> None:
    """Entry point for the apsla CLI application."""
    app()


if __name__ == "__main__":
    main()
