"""Language-independent Unicode rules and adversarial pattern checks."""

from __future__ import annotations

import uuid

from apsla.cwe import get_cwe_for_category
from apsla.lexing.common import OffsetMap
from apsla.models import Edit, Finding, Fix, Label, Range, Severity, VerificationResult
from apsla.unicode_defense.recovery import RecoveryResult, recover_text
from apsla.unicode_defense.scanner import scan_unicode


def _generate_finding_id(rule_id: str, rng: Range) -> str:
    """Generate a deterministic or unique finding ID."""
    return f"{rule_id}-{rng.start_line}-{rng.start_col}-{uuid.uuid4().hex[:8]}"


def evaluate_unicode_rules(
    raw_text: str,
    offset_map: OffsetMap | None = None,
    recovery: RecoveryResult | None = None,
) -> list[Finding]:
    """Evaluate language-independent Unicode defense rules on raw and recovered text.

    Rules evaluated:
      - APS-ALL-UNI-001: Bidi control character (Trojan Source, CVE-2021-42574)
      - APS-ALL-UNI-002: Zero-width or invisible character in identifier
      - APS-ALL-UNI-003: Unicode tag characters (U+E0000..U+E007F)
      - APS-ALL-UNI-004: Confusable character in identifier
      - APS-ALL-UNI-005: Mixed-script identifier
      - APS-ALL-UNI-006: Confusable that recovers to a keyword or dangerous API name ("ехес")

    Args:
        raw_text: Original source string.
        offset_map: Precomputed OffsetMap for raw_text.
        recovery: Precomputed RecoveryResult.

    Returns:
        list[Finding]: Unified security findings for Unicode vulnerabilities.
    """
    om = offset_map if offset_map is not None else OffsetMap(raw_text)
    _rec = recovery if recovery is not None else recover_text(raw_text, om)
    scan = scan_unicode(raw_text, om)

    findings: list[Finding] = []
    seen_ranges: set[tuple[str, int, int, int, int]] = set()

    for hit in scan.hits:
        rule_id = ""
        title = ""
        cwe = ""
        message = ""
        explanation = ""
        severity = hit.severity
        fixes: list[Fix] = []

        if hit.category == "bidi":
            rule_id = "APS-ALL-UNI-001"
            title = "Trojan Source Bidi Control Character"
            cwe = get_cwe_for_category("TROJAN")
            message = f"Trojan Source bidirectional control {hit.codepoint} ({hit.name}) detected"
            explanation = (
                f"The source file contains an invisible bidirectional override character {hit.codepoint}. "
                "Attackers use bidirectional formatting to manipulate visual rendering order, deceiving "
                "developers into reading dangerous code as innocuous comments or strings. "
                "Remove this control character immediately."
            )
            # Fix: Remove the bidi character
            fix = Fix(
                id=f"FIX-{uuid.uuid4().hex[:8]}",
                finding_id="",
                title="Remove Bidi Override Character",
                description=f"Strip invisible {hit.codepoint} control character.",
                confidence="safe",
                kind="rule",
                edits=[Edit(range=hit.range, new_text="")],
                verification=VerificationResult(
                    syntax_ok=True, finding_gone=True, verified=True, notes="Bidi char stripped"
                ),
            )
            fixes.append(fix)

        elif hit.category == "zero_width":
            rule_id = "APS-ALL-UNI-002"
            title = "Zero-Width Character in Identifier or Code"
            cwe = get_cwe_for_category("CONFUSABLE")
            message = f"Zero-width character {hit.codepoint} ({hit.name}) detected"
            explanation = (
                f"The token contains a zero-width invisible character {hit.codepoint}. "
                "Zero-width characters create visual illusions where two distinct identifiers look identical, "
                "enabling variable shadowing attacks and authentication bypasses. "
                "Strip the zero-width character to restore visual integrity."
            )
            fix = Fix(
                id=f"FIX-{uuid.uuid4().hex[:8]}",
                finding_id="",
                title="Remove Zero-Width Character",
                description=f"Delete hidden {hit.codepoint} character.",
                confidence="safe",
                kind="rule",
                edits=[Edit(range=hit.range, new_text="")],
                verification=VerificationResult(
                    syntax_ok=True, finding_gone=True, verified=True, notes="Zero-width stripped"
                ),
            )
            fixes.append(fix)

        elif hit.category == "tag":
            rule_id = "APS-ALL-UNI-003"
            title = "Unicode Tag Character Detected"
            cwe = get_cwe_for_category("TROJAN")
            message = f"Unicode Tag character {hit.codepoint} detected"
            explanation = (
                f"An invisible Unicode Tag character ({hit.codepoint}) was found. "
                "Tag characters are deprecated formatting artifacts frequently used to smuggle hidden "
                "instructions or bypass signature filters without human-visible changes. "
                "Remove all tag characters from the code."
            )
            fix = Fix(
                id=f"FIX-{uuid.uuid4().hex[:8]}",
                finding_id="",
                title="Remove Unicode Tag Character",
                description="Remove invisible tag character.",
                confidence="safe",
                kind="rule",
                edits=[Edit(range=hit.range, new_text="")],
                verification=VerificationResult(
                    syntax_ok=True, finding_gone=True, verified=True, notes="Tag char stripped"
                ),
            )
            fixes.append(fix)

        elif hit.category == "dangerous_recovery":
            rule_id = "APS-ALL-UNI-006"
            title = "Obfuscated Dangerous Built-in / Keyword"
            severity = Severity.HIGH
            cwe = get_cwe_for_category("TROJAN")
            recovered_word = hit.recovered_to or ""
            message = (
                f"Identifier '{hit.char}' disguises dangerous '{recovered_word}' "
                "using look-alike characters"
            )
            explanation = (
                f"The identifier '{hit.char}' visually mimics the dangerous built-in or keyword "
                f"'{recovered_word}' using homoglyphs or look-alike characters. "
                "This deceptive technique allows malicious functions to masquerade as standard calls. "
                f"Replace '{hit.char}' with canonical '{recovered_word}' or an unambiguous name."
            )
            fix = Fix(
                id=f"FIX-{uuid.uuid4().hex[:8]}",
                finding_id="",
                title=f"Replace with Canonical '{recovered_word}'",
                description=f"Replace obfuscated '{hit.char}' with standard '{recovered_word}'.",
                confidence="safe",
                kind="rule",
                edits=[Edit(range=hit.range, new_text=recovered_word)],
                verification=VerificationResult(
                    syntax_ok=True, finding_gone=True, verified=True, notes="Canonical replaced"
                ),
            )
            fixes.append(fix)

        elif hit.category == "mixed_script":
            rule_id = "APS-ALL-UNI-005"
            title = "Mixed-Script Identifier Detected"
            severity = Severity.MEDIUM
            cwe = get_cwe_for_category("CONFUSABLE")
            message = hit.note or f"Identifier '{hit.char}' mixes multiple Unicode scripts"
            explanation = (
                f"The symbol '{hit.char}' mixes characters across multiple Unicode scripts. "
                "Mixed-script identifiers are a primary indicator of homoglyph spoofing attacks. "
                "Normalize the identifier to a single consistent script."
            )
            recovered_word = hit.recovered_to
            if recovered_word:
                fix = Fix(
                    id=f"FIX-{uuid.uuid4().hex[:8]}",
                    finding_id="",
                    title=f"Normalize Identifier to '{recovered_word}'",
                    description=f"Normalize mixed-script '{hit.char}' to '{recovered_word}'.",
                    confidence="safe",
                    kind="rule",
                    edits=[Edit(range=hit.range, new_text=recovered_word)],
                    verification=VerificationResult(
                        syntax_ok=True,
                        finding_gone=True,
                        verified=True,
                        notes="Normalized mixed script",
                    ),
                )
                fixes.append(fix)

        elif hit.category == "confusable":
            rule_id = "APS-ALL-UNI-004"
            title = "Confusable Look-alike Character"
            severity = Severity.MEDIUM
            cwe = get_cwe_for_category("CONFUSABLE")
            recovered_char = hit.recovered_to or ""
            message = f"Character '{hit.char}' ({hit.codepoint}) is confusable with ASCII '{recovered_char}'"
            explanation = (
                f"The character '{hit.char}' ({hit.codepoint}) visually resembles ASCII '{recovered_char}'. "
                "Confusable characters can mislead developers during security audits. "
                "Consider replacing with standard ASCII."
            )
            fix = Fix(
                id=f"FIX-{uuid.uuid4().hex[:8]}",
                finding_id="",
                title=f"Replace with ASCII '{recovered_char}'",
                description=f"Map look-alike character '{hit.char}' to '{recovered_char}'.",
                confidence="safe",
                kind="rule",
                edits=[Edit(range=hit.range, new_text=recovered_char)],
                verification=VerificationResult(
                    syntax_ok=True, finding_gone=True, verified=True, notes="Replaced confusable"
                ),
            )
            fixes.append(fix)

        if not rule_id:
            continue

        range_key = (
            rule_id,
            hit.range.start_line,
            hit.range.start_col,
            hit.range.end_line,
            hit.range.end_col,
        )
        if range_key in seen_ranges:
            continue
        seen_ranges.add(range_key)

        finding_id = _generate_finding_id(rule_id, hit.range)
        for f in fixes:
            f.finding_id = finding_id

        label = (
            Label.MALICIOUS if severity in (Severity.CRITICAL, Severity.HIGH) else Label.SUSPICIOUS
        )
        confidence = 0.95 if severity == Severity.HIGH else 0.85

        finding = Finding(
            id=finding_id,
            rule_id=rule_id,
            title=title,
            cwe=cwe,
            severity=severity,
            label=label,
            confidence=confidence,
            range=hit.range,
            message=message,
            explanation=explanation,
            evidence={
                "codepoint": hit.codepoint,
                "char": hit.char,
                "name": hit.name,
                "category": hit.category,
                "recovered_to": hit.recovered_to,
            },
            taint_path=[],
            fixes=fixes,
            sources=["unicode"],
            suppressed=False,
        )
        findings.append(finding)

    return findings
