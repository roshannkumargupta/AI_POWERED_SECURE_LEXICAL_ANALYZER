"""Lexical diagnostic analysis and remediation."""

from __future__ import annotations

import re

from apsla.diagnostics.common import (
    LANG_PREFIX,
    _make_fix,
    _offset_to_range,
    get_valid_string_and_comment_spans,
)
from apsla.diagnostics.numeric_lexical import check_numeric_lexical_diagnostics
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Edit, Finding, Fix, Label, Range, Severity


def analyze_lexical_diagnostics(
    source: str,
    tokens: list[Token],
    language: str,
) -> list[Finding]:
    """Inspect source and token stream for lexical errors across Python, Java, JS, and C++."""
    prefix = LANG_PREFIX.get(language, "ALL")
    findings: list[Finding] = []
    lines = source.splitlines()

    def add_finding(
        code: str,
        title: str,
        message: str,
        explanation: str,
        rng: Range,
        fix: Fix | None = None,
        severity: Severity = Severity.HIGH,
    ) -> None:
        fid = f"APS-{prefix}-LEX-{code}-{rng.start_line}-{rng.start_col}-{len(findings)}"
        f = Finding(
            id=fid,
            rule_id=f"APS-{prefix}-LEX-{code}",
            title=title,
            cwe="",
            severity=severity,
            label=Label.SUSPICIOUS,
            confidence=1.0,
            range=rng,
            message=message,
            explanation=explanation,
            evidence={"lexical": True, "kind": "lexical"},
            sources=["lexical"],
            kind="lexical",
            fixes=[fix] if fix else [],
        )
        if fix:
            fix.finding_id = fid
            fix.id = f"{fid}-fix"
        findings.append(f)

    valid_str_spans = get_valid_string_and_comment_spans(source, tokens)

    def is_inside_string_or_comment(offset: int) -> bool:
        return any(s <= offset < e for s, e in valid_str_spans)

    # 1. Unterminated Triple-Quoted Strings (Python)
    if language == "python":
        for tq in ("'''", '"""'):
            if source.startswith(tq) or f"={tq}" in source.replace(" ", "") or f" {tq}" in source:
                count = source.count(tq)
                if count % 2 != 0:
                    last_idx = source.rfind(tq)
                    rng = _offset_to_range(source, last_idx, len(source))
                    fix_edit = Edit(
                        range=Range(
                            start_line=len(lines),
                            start_col=len(lines[-1]) + 1 if lines else 1,
                            end_line=len(lines),
                            end_col=len(lines[-1]) + 1 if lines else 1,
                        ),
                        new_text=tq,
                    )
                    fix = _make_fix(
                        "lex",
                        "Close triple-quoted string",
                        f"Appends missing {tq} delimiter to close string literal.",
                        [fix_edit],
                    )
                    add_finding(
                        "002",
                        "Unterminated triple-quoted string",
                        f"Unterminated triple-quoted string literal starting with {tq}.",
                        "The triple-quoted string literal was not closed before end of file.",
                        rng,
                        fix,
                    )
                    return findings

    # 2. Unterminated Block Comments (/* ...)
    if "/*" in source and "*/" not in source:
        idx = source.rfind("/*")
        rng = _offset_to_range(source, idx, len(source))
        fix_edit = Edit(
            range=Range(
                start_line=len(lines),
                start_col=len(lines[-1]) + 1 if lines else 1,
                end_line=len(lines),
                end_col=len(lines[-1]) + 1 if lines else 1,
            ),
            new_text=" */",
        )
        fix = _make_fix(
            "lex",
            "Close block comment",
            "Appends ' */' to terminate block comment.",
            [fix_edit],
        )
        add_finding(
            "002",
            "Unterminated block comment",
            "Unterminated block comment: missing closing '*/'.",
            "Block comment reached end of file without closing delimiter.",
            rng,
            fix,
        )
        return findings

    # 3. Unterminated Template Literals (JavaScript: `...)
    if language == "javascript":
        backtick_matches = [m.start() for m in re.finditer(r"(?<!\\)`", source)]
        if len(backtick_matches) % 2 != 0:
            last_bt = backtick_matches[-1]
            semi_idx = source.find(";", last_bt)
            if semi_idx != -1:
                rng = _offset_to_range(source, last_bt, semi_idx)
                fix_edit = Edit(
                    range=_offset_to_range(source, semi_idx, semi_idx),
                    new_text="`",
                )
            else:
                rng = _offset_to_range(source, last_bt, len(source))
                fix_edit = Edit(
                    range=Range(
                        start_line=len(lines),
                        start_col=len(lines[-1]) + 1 if lines else 1,
                        end_line=len(lines),
                        end_col=len(lines[-1]) + 1 if lines else 1,
                    ),
                    new_text="`",
                )
            fix = _make_fix(
                "lex",
                "Close template literal",
                "Closes unterminated template literal with backtick.",
                [fix_edit],
            )
            add_finding(
                "004",
                "Unterminated template literal",
                "Unterminated template literal: missing closing backtick '`'.",
                "Template literal was not closed before end of line or file.",
                rng,
                fix,
            )
            return findings

    # 4. Invalid Regular Expression Literal (JavaScript: let r = /[/;)
    if language == "javascript":
        for m in re.finditer(r"/(?:\\.|[^/\n\\])+/?", source):
            raw = m.group(0)
            if re.search(r"(?<!\\)\[", raw) and "]" not in raw:
                start_p, end_p = m.span()
                rng = _offset_to_range(source, start_p, end_p)
                fixed_regex = raw.replace("[", r"\[")
                if not fixed_regex.endswith("/") or fixed_regex.count("/") < 2:
                    fixed_regex += "/"
                fix_edit = Edit(range=rng, new_text=fixed_regex)
                fix = _make_fix(
                    "lex",
                    "Fix regular-expression literal",
                    "Escapes unclosed delimiter in regular expression literal.",
                    [fix_edit],
                )
                add_finding(
                    "005",
                    "Invalid regular-expression literal",
                    "Invalid regular-expression literal: unclosed character class or delimiter.",
                    "Regular expression contains an unclosed character class '['.",
                    rng,
                    fix,
                )
                return findings

    # 5. Unterminated String Literals and Trailing Backslash Escapes
    om = OffsetMap(source)
    for tok in tokens:
        raw = tok.text.lstrip("rRuUbBfF")
        q = raw[:1]
        is_unclosed = False
        if tok.kind == "STRING":
            if q in ('"', "'") and not raw.endswith(q):
                is_unclosed = True
        elif tok.kind == "ERROR" and q in ('"', "'"):
            is_unclosed = True

        if is_unclosed:
            t_no_semi = tok.text.rstrip(";\r\n")
            if t_no_semi.endswith("\\"):
                bs_idx = source.rfind("\\", 0, om.pos_to_py(tok.end_line, tok.end_col))
                rng = om.span_to_range(bs_idx, bs_idx + 1)
                close_text = q + (";" if language in ("java", "cpp") and ";" not in source else "")
                fix_edit = Edit(range=rng, new_text=close_text)
                fix = _make_fix(
                    "lex",
                    "Terminate string literal",
                    "Replaces trailing backslash with closing quote.",
                    [fix_edit],
                )
                add_finding(
                    "001",
                    "Unterminated string or invalid line continuation",
                    "Unterminated string or invalid line continuation: trailing backslash escapes delimiter.",
                    "String literal ended with backslash without a valid escape sequence or closed delimiter.",
                    rng,
                    fix,
                )
                return findings
            semi_pos = tok.text.find(";")
            if semi_pos != -1:
                rng = Range(
                    start_line=tok.line,
                    start_col=tok.col,
                    end_line=tok.line,
                    end_col=tok.col + semi_pos,
                )
                fix_range = Range(
                    start_line=tok.line,
                    start_col=tok.col + semi_pos,
                    end_line=tok.line,
                    end_col=tok.col + semi_pos,
                )
                fix_text = q
            else:
                rng = tok.to_range()
                fix_range = Range(
                    start_line=tok.end_line,
                    start_col=tok.end_col,
                    end_line=tok.end_line,
                    end_col=tok.end_col,
                )
                fix_text = q + (";" if language in ("java", "cpp") and ";" not in tok.text else "")

            fix_edit = Edit(range=fix_range, new_text=fix_text)
            fix = _make_fix(
                "lex",
                "Insert missing closing quote",
                f"Inserts closing quote {q} to terminate string literal.",
                [fix_edit],
            )
            add_finding(
                "001",
                "Unterminated string literal",
                f"Unterminated string literal at line {tok.line}, col {tok.col}. The closing quote is missing.",
                "The string literal was not closed before the end of the line.",
                rng,
                fix,
            )
            return findings

    # 7. Invalid Character Literal (Java: char c = 'ab';)
    if language in ("java", "cpp"):
        for m in re.finditer(r"'([^'\\]{2,})'", source):
            if is_inside_string_or_comment(m.start()):
                continue
            start_p, end_p = m.span()
            inner = m.group(1)
            rng = _offset_to_range(source, start_p, end_p)
            fix_edit = Edit(range=rng, new_text=f"'{inner[0]}'")
            fix = _make_fix(
                "lex",
                "Convert to single-character literal",
                "Replaces multi-character literal with a single character.",
                [fix_edit],
            )
            add_finding(
                "020",
                "Invalid character literal",
                f"Invalid character literal '{m.group(0)}': character literals must contain exactly one character.",
                "In this language, character literals enclosed in single quotes must contain exactly one character.",
                rng,
                fix,
            )
            return findings

    # 8. Malformed / Illegal Escape in String / Char Literals
    if language == "java":
        for m in re.finditer(r"""(?<!\\)\\q""", source):
            start_p, end_p = m.span()
            rng = _offset_to_range(source, start_p, end_p)
            fix_edit = Edit(range=rng, new_text=r"\\q")
            fix = _make_fix(
                "lex",
                "Escape backslash",
                "Escapes backslash to form valid escape sequence '\\\\q'.",
                [fix_edit],
            )
            add_finding(
                "021",
                "Illegal escape character",
                r"Illegal escape character '\q' in string literal.",
                r"Java supports escape sequences \b, \t, \n, \f, \r, \", \', \\, but not \q.",
                rng,
                fix,
            )
            return findings

        for m in re.finditer(r"""'\\x'""", source):
            start_p, end_p = m.span()
            rng = _offset_to_range(source, start_p, end_p)
            fix_edit = Edit(range=rng, new_text="'x'")
            fix = _make_fix(
                "lex",
                "Replace invalid escape",
                "Replaces '\\x' with valid character literal 'x'.",
                [fix_edit],
            )
            add_finding(
                "022",
                "Illegal escape in character literal",
                r"Illegal escape '\x' in character literal.",
                r"Java does not support '\x' hexadecimal escape sequences in character literals; use '\uXXXX'.",
                rng,
                fix,
            )
            return findings

    if language == "cpp":
        for m in re.finditer(r"""'\\x'""", source):
            start_p, end_p = m.span()
            rng = _offset_to_range(source, start_p, end_p)
            fix_edit = Edit(range=rng, new_text="'x'")
            fix = _make_fix(
                "lex",
                "Complete or replace hexadecimal escape",
                "Replaces '\\x' with valid character literal 'x'.",
                [fix_edit],
            )
            add_finding(
                "023",
                "Incomplete hexadecimal escape",
                r"Incomplete hexadecimal escape '\x' in character literal: missing hex digits.",
                r"In C++, '\x' must be followed by one or more hexadecimal digits.",
                rng,
                fix,
            )
            return findings

    if language == "python":
        for m in re.finditer(r"""(?<!\\)\\u([0-9a-zA-Z]{1,4})""", source):
            hex_part = m.group(1)
            if not re.fullmatch(r"[0-9a-fA-F]{4}", hex_part):
                start_p, end_p = m.span()
                rng = _offset_to_range(source, start_p, end_p)
                fix_edit = Edit(range=rng, new_text=r"\\u" + hex_part)
                fix = _make_fix(
                    "lex",
                    "Escape Unicode backslash",
                    "Escapes backslash to prevent invalid Unicode decoding.",
                    [fix_edit],
                )
                add_finding(
                    "024",
                    "Malformed Unicode escape",
                    rf"Malformed Unicode escape '\u{hex_part}': requires 4 hexadecimal digits.",
                    r"The \u escape in Python string literals requires exactly 4 valid hex digits [0-9a-fA-F].",
                    rng,
                    fix,
                )
                return findings

    # 9-14. Numeric literal checks
    num_res = check_numeric_lexical_diagnostics(
        source, language, is_inside_string_or_comment, add_finding
    )
    if num_res is not None:
        return findings

    # 15. Invalid / Illegal Characters (§, @, #)
    for m in re.finditer(r"§", source):
        if is_inside_string_or_comment(m.start()):
            continue
        start_p, end_p = m.span()
        rng = _offset_to_range(source, start_p, end_p)
        fix_edit = Edit(range=rng, new_text="%")
        fix = _make_fix(
            "lex",
            "Replace invalid character",
            "Replaces illegal character '§' with valid operator '%'.",
            [fix_edit],
        )
        title = "Illegal character" if language == "java" else "Invalid character/token"
        add_finding(
            "003",
            title,
            f"{title} '§' at line {rng.start_line}, col {rng.start_col}.",
            "The section sign '§' is not a recognized operator or identifier character.",
            rng,
            fix,
        )
        return findings

    if language in ("javascript", "cpp"):
        for m in re.finditer(r"@(?!=)", source):
            if is_inside_string_or_comment(m.start()):
                continue
            start_p, end_p = m.span()
            rng = _offset_to_range(source, start_p, end_p)
            fix_edit = Edit(range=rng, new_text="0")
            fix = _make_fix(
                "lex",
                "Replace invalid token",
                "Replaces invalid token '@' with '0'.",
                [fix_edit],
            )
            add_finding(
                "003",
                "Invalid token",
                f"Invalid token '@' at line {rng.start_line}, col {rng.start_col}.",
                "The '@' character cannot be tokenized in this language at this location.",
                rng,
                fix,
            )
            return findings

    if language == "javascript":
        for m in re.finditer(r"(?<![a-zA-Z0-9_\$])#(?![a-zA-Z0-9_\$])", source):
            if is_inside_string_or_comment(m.start()):
                continue
            start_p, end_p = m.span()
            rng = _offset_to_range(source, start_p, end_p)
            fix_edit = Edit(range=rng, new_text="0")
            fix = _make_fix(
                "lex",
                "Replace unexpected hash character",
                "Replaces unexpected '#' character with '0'.",
                [fix_edit],
            )
            add_finding(
                "003",
                "Unexpected hash character",
                f"Unexpected hash character '#' at line {rng.start_line}, col {rng.start_col}.",
                "The '#' character is only valid in JavaScript for private class fields (#field).",
                rng,
                fix,
            )
            return findings

    # 16. Fallback check for any lexer ERROR tokens
    for token in tokens:
        if token.kind == "ERROR":
            raw_txt = token.text
            code = "001" if raw_txt.startswith(('"', "'")) else "003"
            add_finding(
                code,
                "Lexical error",
                f"Lexical error at line {token.line}, col {token.col}: {raw_txt!r}.",
                "Unrecognized token or character sequence.",
                token.to_range(),
            )

    return findings
