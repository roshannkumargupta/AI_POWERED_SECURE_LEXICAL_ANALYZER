"""Taint path construction, normalization, and explanation utilities."""

from __future__ import annotations

from apsla.models import Range, TaintPathStep, TaintStepKind


def create_taint_step(
    kind: TaintStepKind | str,
    range: Range,
    text: str,
    note: str = "",
) -> TaintPathStep:
    """Create a standardized TaintPathStep object.

    Args:
        kind: Type of step (source, propagate, sink, sanitizer, sanitizer_missing).
        range: 1-based, UTF-16 coordinate range in source document.
        text: Code snippet representing this step.
        note: Descriptive explanation of data-flow action.

    Returns:
        TaintPathStep: Formatted path step.
    """
    step_enum = TaintStepKind(kind.lower()) if isinstance(kind, str) else kind

    return TaintPathStep(
        step=step_enum,
        range=range,
        text=text.strip(),
        note=note,
    )


def assemble_taint_path(
    source_step: TaintPathStep,
    propagate_steps: list[TaintPathStep] | None = None,
    sink_step: TaintPathStep | None = None,
) -> list[TaintPathStep]:
    """Assemble an ordered source-to-sink taint propagation sequence.

    Args:
        source_step: Origin of untrusted data (source).
        propagate_steps: Optional intermediate propagation steps.
        sink_step: Optional vulnerable execution point (sink).

    Returns:
        List of TaintPathStep instances in chronological execution order.
    """
    path: list[TaintPathStep] = [source_step]
    if propagate_steps:
        path.extend(propagate_steps)
    if sink_step is not None:
        path.append(sink_step)
    return path


def format_taint_trace(path: list[TaintPathStep]) -> str:
    """Format a taint path into a human-readable trace string.

    Example output:
      [1] SOURCE (line 12): request.getParameter("cmd") — Untrusted HTTP request parameter
      [2] PROPAGATE (line 14): cmd = "ping " + input — String concatenation
      [3] SINK (line 16): Runtime.getRuntime().exec(cmd) — OS command execution sink
    """
    if not path:
        return "No taint path available."

    lines: list[str] = []
    for idx, step in enumerate(path, 1):
        step_name = step.step.value.upper()
        line_num = step.range.start_line
        note_str = f" — {step.note}" if step.note else ""
        lines.append(f"[{idx}] {step_name} (line {line_num}): {step.text}{note_str}")

    return "\n".join(lines)
