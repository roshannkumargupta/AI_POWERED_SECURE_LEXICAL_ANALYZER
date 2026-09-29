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
    pass


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
            help="Target language identifier (default: python).",
        ),
    ] = "python",
) -> None:
    """Analyze a source file for security vulnerabilities and taint propagation."""
    _configure_windows_encoding()
    console = Console()

    source = file.read_text(encoding="utf-8", errors="replace")
    analyzer = Analyzer()
    result = analyzer.analyze(source=source, language=language, filename=str(file))

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

        console.print()
        console.print(
            f"[bold]Summary:[/bold] Critical: {result.summary.critical} | "
            f"High: {result.summary.high} | Medium: {result.summary.medium} | "
            f"Low: {result.summary.low} | Total Tokens: {result.summary.tokens_total}"
        )
        console.print()

    has_high_or_crit = any(
        f.severity in (Severity.HIGH, Severity.CRITICAL)
        for f in result.findings
        if not f.suppressed
    )
    if has_high_or_crit:
        raise typer.Exit(code=1)


def main() -> None:
    """Entry point for the apsla CLI application."""
    app()


if __name__ == "__main__":
    main()
