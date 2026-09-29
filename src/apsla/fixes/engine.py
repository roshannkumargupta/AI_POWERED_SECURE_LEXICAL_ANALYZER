"""Remediation engine coordinating fix generation, verification, and batch application."""

from __future__ import annotations

import ast

from apsla.fixes.edits import OverlappingEditsError, apply_edits, unified_diff
from apsla.fixes.registry import FIX_REGISTRY, FixContext
from apsla.fixes.verifier import verify_fix
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Finding, Fix


def generate_fixes(
    source: str,
    finding: Finding,
    tokens: list[Token],
    language: str = "python",
    verify: bool = True,
    existing_finding_keys: set[tuple[str, int]] | None = None,
) -> list[Fix]:
    """Generate and verify automated fixes for a detected finding.

    Args:
        source: Original source text.
        finding: Target finding needing remediation.
        tokens: Token stream of source document.
        language: Language identifier (default: 'python').
        verify: Whether to execute verification on generated fixes (default: True).
        existing_finding_keys: Known (rule_id, line) pairs in the unpatched document.

    Returns:
        List of generated Fix instances with verification results.
    """
    generators = FIX_REGISTRY.get(finding.rule_id)
    if not generators:
        return []

    ast_tree: ast.AST | None = None
    try:
        ast_tree = ast.parse(source)
    except Exception:
        ast_tree = None

    offset_map = OffsetMap(source)
    ctx = FixContext(
        source=source,
        finding=finding,
        tokens=tokens,
        ast_tree=ast_tree,
        offset_map=offset_map,
        language=language,
    )

    candidate_fixes: list[Fix] = []
    for gen in generators:
        try:
            fixes = gen.generate(ctx)
            candidate_fixes.extend(fixes)
        except Exception:
            continue

    if not verify:
        return candidate_fixes

    verified_fixes: list[Fix] = []
    for fix in candidate_fixes:
        v_fix = verify_fix(
            source,
            fix,
            finding,
            language=language,
            existing_finding_keys=existing_finding_keys,
        )
        verified_fixes.append(v_fix)

    return verified_fixes


def fix_all(
    source: str,
    language: str = "python",
    filename: str = "<editor>",
    allow_review: bool = False,
) -> tuple[str, list[str], dict[str, str], str, int, int]:
    """Apply safe and verified fixes iteratively up to 3 passes.

    Args:
        source: Initial source text.
        language: Language identifier (default: 'python').
        filename: Optional filename for diff header.
        allow_review: If True, apply verified 'review' fixes in addition to 'safe' fixes.

    Returns:
        tuple containing:
            - new_source (str): Remediated source text.
            - applied_fix_ids (list[str]): IDs of successfully applied fixes.
            - skipped_fix_ids (dict[str, str]): Mapping of skipped fix IDs to explanations.
            - diff (str): Unified diff between before and after text.
            - score_before (int): Security health score before remediation.
            - score_after (int): Security health score after remediation.
    """
    from apsla.pipeline import Analyzer

    analyzer = Analyzer()
    initial_res = analyzer.analyze(source, language=language, filename=filename, options={"fixes": True})
    score_before = initial_res.summary.score

    current_source = source
    applied_fix_ids: list[str] = []
    skipped_fix_ids: dict[str, str] = {}

    allowed_confidences = {"safe", "review"} if allow_review else {"safe"}

    for _ in range(3):
        res = analyzer.analyze(current_source, language=language, filename=filename, options={"fixes": True})
        applicable_fixes: list[Fix] = []

        for f in res.findings:
            for fix in f.fixes:
                if fix.verification.verified and fix.edits and fix.confidence in allowed_confidences:
                    applicable_fixes.append(fix)
                elif not fix.verification.verified:
                    skipped_fix_ids[fix.id] = fix.verification.notes
                elif fix.confidence not in allowed_confidences:
                    skipped_fix_ids[fix.id] = f"Requires human review (confidence: {fix.confidence})"

        if not applicable_fixes:
            break

        pass_changed = False
        for fix in applicable_fixes:
            try:
                new_source = apply_edits(current_source, fix.edits)
                current_source = new_source
                applied_fix_ids.append(fix.id)
                pass_changed = True
                break
            except OverlappingEditsError:
                skipped_fix_ids[fix.id] = "Edits overlap with previously applied fix in same pass"
            except Exception as exc:
                skipped_fix_ids[fix.id] = f"Failed to apply: {exc}"

        if not pass_changed:
            break

    final_res = analyzer.analyze(current_source, language=language, filename=filename, options={"fixes": False})
    score_after = final_res.summary.score
    diff = unified_diff(source, current_source, filename)

    return current_source, applied_fix_ids, skipped_fix_ids, diff, score_before, score_after
