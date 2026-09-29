"""Automated fix verification engine executing syntax validation and re-analysis."""

from __future__ import annotations

import concurrent.futures
from typing import TYPE_CHECKING

from apsla.fixes.edits import apply_edits
from apsla.languages.registry import get_plugin
from apsla.models import Finding, Fix, Severity, VerificationResult

if TYPE_CHECKING:
    pass


def _verify_worker(
    modified_source: str,
    finding: Finding,
    language: str,
    existing_finding_keys: set[tuple[str, int]],
) -> tuple[bool, bool, list[str], str]:
    """Inner worker executing syntax check and shadow re-analysis.

    Returns:
        tuple[syntax_ok, finding_gone, new_findings, notes]
    """
    plugin = get_plugin(language)
    if plugin is None:
        return False, False, [], f"Unsupported language plugin: {language}"

    # 1. Syntax check
    syntax_ok, syntax_err = plugin.syntax_check(modified_source)
    if not syntax_ok:
        return False, False, [], f"Syntax check failed after fix: {syntax_err}"

    # 2. Re-run analysis on modified source copy without recursive fixes
    from apsla.pipeline import Analyzer

    analyzer = Analyzer()
    re_result = analyzer.analyze(
        modified_source,
        language=language,
        filename="<shadow_verification>",
        options={"fixes": False},
    )

    # 3. Check if target finding is gone near the original logical location
    orig_line = finding.range.start_line
    finding_still_present = False
    for f in re_result.findings:
        if f.rule_id == finding.rule_id:
            # Check proximity allowing for minor line offset shifts (+/- 5 lines)
            if abs(f.range.start_line - orig_line) <= 5:
                finding_still_present = True
                break

    finding_gone = not finding_still_present

    # 4. Check for newly introduced medium/high/critical findings
    new_findings: list[str] = []
    med_plus = {Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM}
    for f in re_result.findings:
        if f.severity in med_plus:
            key = (f.rule_id, f.range.start_line)
            # If not in existing findings and not the original finding
            if key not in existing_finding_keys and f.rule_id != finding.rule_id:
                new_findings.append(f.rule_id)

    notes = ""
    if not finding_gone:
        notes = f"Finding '{finding.rule_id}' still present near line {orig_line}."
    elif new_findings:
        notes = f"Fix introduced new severe findings: {', '.join(new_findings)}."
    else:
        notes = "Verified: syntax valid, target finding eliminated, zero regressions."

    return syntax_ok, finding_gone, new_findings, notes


def verify_fix(
    source: str,
    fix: Fix,
    finding: Finding,
    language: str = "python",
    existing_finding_keys: set[tuple[str, int]] | None = None,
    timeout_seconds: float = 2.0,
) -> Fix:
    """Verify an automated fix against a sandboxed document copy.

    Applies the edits, performs syntax checking, re-runs full analysis, and checks
    that the targeted finding is eliminated without introducing new severe issues.
    If unverified, downgrades confidence to 'manual' and purges edits.

    Args:
        source: Original source text.
        fix: Proposed Fix instance.
        finding: Target finding being remediated.
        language: Language identifier (default: "python").
        existing_finding_keys: Known (rule_id, line) pairs in the unpatched document.
        timeout_seconds: Maximum time allowed for verification (default: 2.0s).

    Returns:
        Updated Fix with verified VerificationResult.
    """
    if not fix.edits:
        # Advice-only fix with no atomic edits
        res = VerificationResult(
            syntax_ok=True,
            finding_gone=False,
            new_findings=[],
            verified=False,
            notes=fix.verification.notes if fix.verification else "Manual review advice only.",
        )
        return fix.model_copy(update={"verification": res, "confidence": "manual"})

    # Apply edits to isolated copy
    try:
        modified_source = apply_edits(source, fix.edits)
    except Exception as exc:
        res = VerificationResult(
            syntax_ok=False,
            finding_gone=False,
            new_findings=[],
            verified=False,
            notes=f"Failed to apply edits: {exc}",
        )
        return fix.model_copy(update={"verification": res, "confidence": "manual", "edits": []})

    if existing_finding_keys is None:
        existing_finding_keys = {(finding.rule_id, finding.range.start_line)}

    # Execute verification with timeout
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _verify_worker,
                modified_source,
                finding,
                language,
                existing_finding_keys,
            )
            syntax_ok, finding_gone, new_findings, notes = future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError:
        res = VerificationResult(
            syntax_ok=False,
            finding_gone=False,
            new_findings=[],
            verified=False,
            notes="Verification timed out (>2.0s).",
        )
        return fix.model_copy(update={"verification": res, "confidence": "manual", "edits": []})
    except Exception as exc:
        res = VerificationResult(
            syntax_ok=False,
            finding_gone=False,
            new_findings=[],
            verified=False,
            notes=f"Verification worker error: {exc}",
        )
        return fix.model_copy(update={"verification": res, "confidence": "manual", "edits": []})

    verified = syntax_ok and finding_gone and (len(new_findings) == 0)

    res = VerificationResult(
        syntax_ok=syntax_ok,
        finding_gone=finding_gone,
        new_findings=new_findings,
        verified=verified,
        notes=notes,
    )

    if verified:
        return fix.model_copy(update={"verification": res})
    else:
        # Downgrade to manual and remove edits
        return fix.model_copy(update={"verification": res, "confidence": "manual", "edits": []})
