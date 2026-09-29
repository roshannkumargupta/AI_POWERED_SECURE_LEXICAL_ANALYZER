"""Comprehensive unit tests for the Unicode defense layer.

Tests cover:
- Trojan Source bidi controls (CVE-2021-42574)
- Zero-width & invisible characters in identifiers
- Confusables & dangerous keyword recovery ("ехес", fullwidth "ｅｖａｌ")
- BOM at offset 0 vs middle
- Tag characters
- Non-ASCII whitespace
- Script identification & mixed-script detection
- Inverse offset recovery mapping
- 200 KB performance benchmark (< 2.0 seconds)
"""

from __future__ import annotations

import time

from apsla.lexing.common import OffsetMap
from apsla.models import Severity
from apsla.rules.generic import evaluate_unicode_rules
from apsla.unicode_defense.recovery import recover_text
from apsla.unicode_defense.scanner import scan_unicode
from apsla.unicode_defense.scripts import get_scripts, is_mixed_script


def test_trojan_source_bidi_in_comment():
    """Verify Trojan Source bidi override in comments is detected with Severity.HIGH."""
    # CVE-2021-42574: RLO (U+202E) and PDI/LRI used to visually disguise code in comments
    sample = "/* \u202e } \u2066if (isAdmin) \u2069 \u2066 */ return false;"
    om = OffsetMap(sample)
    result = scan_unicode(sample, om)

    assert result.bidi_count >= 1
    bidi_hits = [h for h in result.hits if h.category == "bidi"]
    assert len(bidi_hits) >= 1
    assert any(h.severity == Severity.HIGH for h in bidi_hits)

    # Evaluate rules
    findings = evaluate_unicode_rules(sample, om)
    bidi_findings = [f for f in findings if f.rule_id == "APS-ALL-UNI-001"]
    assert len(bidi_findings) >= 1
    assert bidi_findings[0].severity == Severity.HIGH
    assert bidi_findings[0].fixes  # Verify remediation fix exists


def test_trojan_source_bidi_in_string_literal():
    """Verify bidi controls in string literals are flagged with Severity.HIGH."""
    sample = 'access_level = "\u202euser\u202dadmin"'
    om = OffsetMap(sample)
    findings = evaluate_unicode_rules(sample, om)

    bidi_findings = [f for f in findings if f.rule_id == "APS-ALL-UNI-001"]
    assert len(bidi_findings) >= 1
    assert bidi_findings[0].severity == Severity.HIGH


def test_zero_width_space_inside_identifier():
    """Verify zero-width space (U+200B) inside an identifier is flagged with Severity.HIGH."""
    # Identifier "adm\u200Bin" has hidden zero-width space
    sample = "adm\u200bin = 1\nif adm\u200bin:\n    pass"
    om = OffsetMap(sample)
    result = scan_unicode(sample, om)

    assert result.zero_width_count >= 1
    zw_hits = [h for h in result.hits if h.category == "zero_width"]
    assert len(zw_hits) >= 1
    # Because it is inside an identifier, severity must be HIGH
    assert zw_hits[0].severity == Severity.HIGH

    findings = evaluate_unicode_rules(sample, om)
    zw_findings = [f for f in findings if f.rule_id == "APS-ALL-UNI-002"]
    assert len(zw_findings) >= 1
    assert zw_findings[0].severity == Severity.HIGH


def test_zero_width_char_outside_identifier():
    """Verify zero-width character outside an identifier is detected."""
    sample = "x = 1;\u200b\n"
    om = OffsetMap(sample)
    result = scan_unicode(sample, om)
    assert result.zero_width_count == 1


def test_cyrillic_exec_recovers_to_exec_high_finding():
    """Verify purely Cyrillic 'ехес' (\u0435\u0445\u0435\u0441) recovers to 'exec' with a HIGH finding."""
    # \u0435 = cyrillic small ie, \u0445 = cyrillic small ha, \u0441 = cyrillic small es
    cyrillic_exec = "\u0435\u0445\u0435\u0441('cat /etc/passwd')"
    om = OffsetMap(cyrillic_exec)

    recovery = recover_text(cyrillic_exec, om)
    assert "exec('cat /etc/passwd')" in recovery.recovered_text
    assert recovery.changed is True
    assert recovery.confusables_replaced == 4

    findings = evaluate_unicode_rules(cyrillic_exec, om, recovery)
    exec_findings = [f for f in findings if f.rule_id == "APS-ALL-UNI-006"]
    assert len(exec_findings) == 1
    assert exec_findings[0].severity == Severity.HIGH
    assert exec_findings[0].evidence["recovered_to"] == "exec"
    assert exec_findings[0].fixes[0].edits[0].new_text == "exec"


def test_mixed_script_exec_recovers_to_exec():
    """Verify mixed Latin-Cyrillic 'e\\u0445ec' recovers to 'exec' with HIGH finding and mixed-script alert."""
    sample = "e\u0445ec(1)"  # 'e' Latin, '\u0445' Cyrillic ha, 'ec' Latin
    om = OffsetMap(sample)

    findings = evaluate_unicode_rules(sample, om)

    # Must contain APS-ALL-UNI-006 (Obfuscated dangerous keyword) with HIGH severity
    f_006 = [f for f in findings if f.rule_id == "APS-ALL-UNI-006"]
    assert len(f_006) == 1
    assert f_006[0].severity == Severity.HIGH
    assert f_006[0].evidence["recovered_to"] == "exec"

    # Must also contain APS-ALL-UNI-005 (Mixed-script identifier)
    f_005 = [f for f in findings if f.rule_id == "APS-ALL-UNI-005"]
    assert len(f_005) == 1


def test_fullwidth_eval_recovers_to_eval():
    """Verify fullwidth 'ｅｖａｌ' (U+FF45, U+FF56, U+FF41, U+FF4C) recovers to 'eval' with HIGH finding."""
    fullwidth_eval = "\uff45\uff56\uff41\uff4c('danger')"
    om = OffsetMap(fullwidth_eval)

    recovery = recover_text(fullwidth_eval, om)
    assert "eval('danger')" in recovery.recovered_text

    findings = evaluate_unicode_rules(fullwidth_eval, om, recovery)
    eval_findings = [f for f in findings if f.rule_id == "APS-ALL-UNI-006"]
    assert len(eval_findings) == 1
    assert eval_findings[0].severity == Severity.HIGH
    assert eval_findings[0].evidence["recovered_to"] == "eval"


def test_bom_at_offset_0_ignored():
    """Verify BOM (U+FEFF) strictly at offset 0 is ignored as standard encoding indicator."""
    sample = "\ufeffdef valid():\n    return 42\n"
    om = OffsetMap(sample)
    result = scan_unicode(sample, om)

    # Offset 0 BOM should not count as a zero-width vulnerability
    assert result.zero_width_count == 0
    findings = evaluate_unicode_rules(sample, om)
    assert not any(f.rule_id == "APS-ALL-UNI-002" for f in findings)


def test_bom_in_the_middle_flagged():
    """Verify BOM (U+FEFF) occurring in the middle of code is flagged."""
    sample = "x = 1\n\ufeffy = 2"
    om = OffsetMap(sample)
    result = scan_unicode(sample, om)

    assert result.zero_width_count == 1
    findings = evaluate_unicode_rules(sample, om)
    zw = [f for f in findings if f.rule_id == "APS-ALL-UNI-002"]
    assert len(zw) == 1


def test_unicode_tag_characters_flagged():
    """Verify Unicode Tag characters (U+E0000 - U+E007F) are detected with Severity.HIGH."""
    sample = "secret\U000e0001\U000e0020data = 'hidden'"
    om = OffsetMap(sample)
    result = scan_unicode(sample, om)

    assert result.tag_count == 2
    findings = evaluate_unicode_rules(sample, om)
    tag_findings = [f for f in findings if f.rule_id == "APS-ALL-UNI-003"]
    assert len(tag_findings) >= 1
    assert tag_findings[0].severity == Severity.HIGH


def test_non_ascii_whitespace_detected():
    """Verify non-ASCII whitespace characters like ideographic space (U+3000) are detected."""
    sample = "var\u3000x\u00a0=\u20005;"
    om = OffsetMap(sample)
    result = scan_unicode(sample, om)

    assert result.whitespace_count == 3


def test_script_detection_and_mixed_scripts():
    """Verify script identification and mixed-script detection."""
    # Single scripts
    assert get_scripts("hello") == {"Latin"}
    assert not is_mixed_script("hello")

    assert get_scripts("привет") == {"Cyrillic"}
    assert not is_mixed_script("привет")

    assert get_scripts("alpha_123") == {"Latin"}
    assert not is_mixed_script("alpha_123")

    # Mixed script
    # 'a' is Latin, 'd' is Latin, 'm' is Latin, '\u0456' is Cyrillic small byelorussian-ukrainian i, 'n' is Latin
    mixed_admin = "adm\u0456n"
    assert "Latin" in get_scripts(mixed_admin)
    assert "Cyrillic" in get_scripts(mixed_admin)
    assert is_mixed_script(mixed_admin)


def test_confusable_non_dangerous_identifier():
    """Verify non-dangerous confusable identifier raises APS-ALL-UNI-004 and APS-ALL-UNI-005, but not 006."""
    # 'p\u0430th' -> '\u0430' is Cyrillic small 'a', recovers to 'path' (safe identifier)
    sample = "p\u0430th = '/tmp/test'"
    om = OffsetMap(sample)
    findings = evaluate_unicode_rules(sample, om)

    # Should have confusable and mixed script
    assert any(f.rule_id == "APS-ALL-UNI-004" for f in findings)
    assert any(f.rule_id == "APS-ALL-UNI-005" for f in findings)
    # Should NOT have APS-ALL-UNI-006 because 'path' is not in DANGEROUS_TARGETS
    assert not any(f.rule_id == "APS-ALL-UNI-006" for f in findings)


def test_recovery_inverse_offset_projection():
    """Verify recovered text offset mapping correctly projects coordinates back to original text."""
    # Original text: 2 bidi characters, 1 confusable
    # 'foo \u202e bar \u0435xec()'
    orig_text = "foo \u202e bar \u0435xec()"
    om_orig = OffsetMap(orig_text)
    rec = recover_text(orig_text, om_orig)

    assert rec.changed is True
    assert "\u202e" not in rec.recovered_text
    assert "exec()" in rec.recovered_text

    # Locate 'exec' in recovered text
    rec_start = rec.recovered_text.index("exec")
    rec_end = rec_start + 4

    # Map span back to original text
    orig_start, orig_end = rec.map_span_to_original(rec_start, rec_end)
    orig_sub = orig_text[orig_start:orig_end]
    assert orig_sub == "\u0435xec"


def test_200kb_file_processes_under_two_seconds():
    """Benchmark: Ensure a 200 KB source file with mixed Unicode processes in under 2.0 seconds."""
    # Build realistic ~200 KB source text: 4000 lines of code with comments, variables, and look-alikes
    lines = []
    for i in range(4000):
        if i % 50 == 0:
            lines.append(
                f"def process_{i}(param='🚀'):\n    # Note: \u202e reversed comment\n    return param"
            )
        elif i % 70 == 0:
            lines.append(f"    v\u0430r_{i} = {i}  # Cyrillic look-alike")
        elif i == 1000:
            lines.append("    \u0435\u0445\u0435\u0441('ls')  # Trojan call")
        else:
            lines.append(f"    x_{i} = compute_value({i}, offset=10) + math.sin({i})")

    content = "\n".join(lines)
    content_bytes = content.encode("utf-8")
    assert len(content_bytes) >= 150_000  # Verify file is large (~150-220 KB)

    start_t = time.perf_counter()
    om = OffsetMap(content)
    rec = recover_text(content, om)
    findings = evaluate_unicode_rules(content, om, rec)
    duration = time.perf_counter() - start_t

    assert duration < 2.0, f"Analysis took {duration:.3f}s, exceeding 2.0s limit"
    assert len(findings) >= 3  # Detected the injected bidi, confusable, and exec


def test_isolated_non_ascii_in_comment():
    """Verify non-confusable non-ASCII characters in comments are flagged as INFO."""
    # Musical symbol U+1D11E (G clef) is not a confusable
    sample = "# Note with music symbol: \U0001d11e\nx = 10"
    om = OffsetMap(sample)
    result = scan_unicode(sample, om)

    info_hits = [h for h in result.hits if h.category == "non_ascii"]
    assert len(info_hits) >= 1
    assert info_hits[0].severity == Severity.INFO


def test_recovery_result_range_and_offset_boundaries():
    """Verify RecoveryResult boundary clamping and range mapping."""
    sample = "let \u0435xec = 42;"
    om = OffsetMap(sample)
    rec = recover_text(sample, om)

    # Test map_py_offset boundaries
    assert rec.map_py_offset(-10) == 0
    assert rec.map_py_offset(0) == 0
    assert rec.map_py_offset(9999) == om.py_len

    # Test map_recovered_range
    # In recovered text: "let exec = 42;"
    # Range of "exec" is line 1, col 5 to col 9
    from apsla.models import Range

    rec_range = Range(start_line=1, start_col=5, end_line=1, end_col=9)
    orig_range = rec.map_recovered_range(rec_range)

    assert orig_range.start_line == 1
    assert orig_range.start_col == 5
    assert orig_range.end_col == 9


def test_scripts_extended_coverage():
    """Verify edge cases in Unicode script detection."""
    from apsla.unicode_defense.scripts import get_character_script

    # Empty string
    assert get_character_script("") == "Unknown"

    # Inherited combining character (e.g. U+0300 Combining Grave Accent)
    assert get_character_script("\u0300") == "Inherited"

    # Rare script outside major list
    assert get_character_script("\U00010000") in ("Unknown", "Linear B")

    # Common script (digits, spaces)
    assert get_character_script("1") == "Common"
    assert get_scripts("12345!@#") == set()
