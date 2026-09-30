"""Language-agnostic 45-dimensional per-token feature extractor for machine learning."""

from __future__ import annotations

import base64
import binascii
import hashlib
import math
import re
import string
from typing import Final

import numpy as np

from apsla.lexing.token import Token
from apsla.unicode_defense.recovery import _CONFUSABLES_MAP, recover_text
from apsla.unicode_defense.scanner import BIDI_CONTROLS, ZERO_WIDTH_CHARS
from apsla.unicode_defense.scripts import is_mixed_script

# ── Feature Schema ────────────────────────────────────────────────────────────

FEATURE_NAMES: Final[tuple[str, ...]] = (
    # [0-3] kind id normalised, length/64 capped, is_numeric, is_keyword
    "kind_id_norm",
    "length_norm",
    "is_numeric",
    "is_keyword",
    # [4-9] zero_width_count, bidi_count, confusable_count, non_ascii_ratio, mixed_script, tag_char_count
    "zero_width_count",
    "bidi_count",
    "confusable_count",
    "non_ascii_ratio",
    "mixed_script",
    "tag_char_count",
    # [10-13] char entropy, bigram entropy, trigram entropy, normalised entropy
    "char_entropy",
    "bigram_entropy",
    "trigram_entropy",
    "normalised_entropy",
    # [14-18] digit ratio, upper ratio, punctuation ratio, whitespace ratio, max repeated-char run normalised
    "digit_ratio",
    "upper_ratio",
    "punctuation_ratio",
    "whitespace_ratio",
    "max_repeated_char_run_norm",
    # [19-22] recovery_changed, recovery_diff_ratio, recovered_is_dangerous_api, recovered_is_keyword
    "recovery_changed",
    "recovery_diff_ratio",
    "recovered_is_dangerous_api",
    "recovered_is_keyword",
    # [23-25] looks_base64, looks_hex, decoded_payload_has_danger_words
    "looks_base64",
    "looks_hex",
    "decoded_payload_has_danger_words",
    # [26-30] dangerous_api_exact, dangerous_api_substring, sql_keyword, shell_pattern, fuzzy_dangerous
    "dangerous_api_exact",
    "dangerous_api_substring",
    "sql_keyword",
    "shell_pattern",
    "fuzzy_dangerous",
    # [31-35] in_string, in_comment, is_call, is_member_access, nesting_depth/10
    "in_string",
    "in_comment",
    "is_call",
    "is_member_access",
    "nesting_depth_norm",
    # [36-38] is_first_argument, enclosing_call_has_concatenation, enclosing_call_is_known_sink
    "is_first_argument",
    "enclosing_call_has_concatenation",
    "enclosing_call_is_known_sink",
    # [39-41] neighbour danger density, neighbour string density, neighbour operator density
    "neighbour_danger_density",
    "neighbour_string_density",
    "neighbour_operator_density",
    # [42-44] is_identifier, is_string_literal, is_operator
    "is_identifier",
    "is_string_literal",
    "is_operator",
)

FEATURE_COUNT: Final[int] = len(FEATURE_NAMES)
assert FEATURE_COUNT == 45, f"Expected exactly 45 features, got {FEATURE_COUNT}"

# Canonical SHA-256 hash of the exact ordered feature schema
FEATURE_SCHEMA_HASH: Final[str] = hashlib.sha256(
    ",".join(FEATURE_NAMES).encode("utf-8")
).hexdigest()

# ── Dictionaries & Lookups ────────────────────────────────────────────────────

LANGUAGE_IDS: Final[dict[str, int]] = {
    "python": 0,
    "java": 1,
    "javascript": 2,
    "js": 2,
    "cpp": 3,
    "c++": 3,
}

DANGEROUS_APIS: Final[frozenset[str]] = frozenset(
    {
        "eval",
        "exec",
        "system",
        "popen",
        "subprocess",
        "spawn",
        "fork",
        "compile",
        "open",
        "read",
        "write",
        "loads",
        "load",
        "pickle",
        "marshal",
        "shelve",
        "yaml",
        "md5",
        "sha1",
        "cursor",
        "execute",
        "executemany",
        "render_template_string",
        "Markup",
        "import_module",
        "__import__",
        "check_output",
        "check_call",
        "run",
        "passthru",
        "shell_exec",
    }
)

SQL_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "UNION",
        "WHERE",
        "FROM",
        "TABLE",
        "INTO",
        "VALUES",
        "JOIN",
        "HAVING",
        "GROUP",
        "ORDER",
        "BY",
        "LIMIT",
        "EXEC",
        "EXECUTE",
        "TRUNCATE",
        "ALTER",
        "CREATE",
    }
)

SHELL_PATTERNS: Final[frozenset[str]] = frozenset(
    {";", "&&", "||", "|", "`", "$(", ">", "<", ">>", "2>", "&"}
)

PAYLOAD_DANGER_WORDS: Final[frozenset[str]] = frozenset(
    {"exec", "eval", "system", "sh", "bash", "cmd", "select", "drop", "import", "bin"}
)

KNOWN_SINKS: Final[frozenset[str]] = frozenset(
    {
        "system",
        "popen",
        "run",
        "check_output",
        "check_call",
        "execute",
        "executemany",
        "eval",
        "exec",
        "load",
        "loads",
        "open",
        "send_file",
        "Markup",
        "render_template_string",
    }
)

COMMON_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "def",
        "class",
        "import",
        "from",
        "return",
        "if",
        "elif",
        "else",
        "for",
        "while",
        "try",
        "except",
        "finally",
        "with",
        "as",
        "pass",
        "break",
        "continue",
        "lambda",
        "yield",
        "global",
        "nonlocal",
        "assert",
        "del",
        "async",
        "await",
        "True",
        "False",
        "None",
        "and",
        "or",
        "not",
        "is",
        "in",
    }
)

TOKEN_KIND_MAP: Final[dict[str, float]] = {
    "IDENTIFIER": 0.1,
    "KEYWORD": 0.2,
    "STRING": 0.3,
    "NUMBER": 0.4,
    "OPERATOR": 0.5,
    "DELIMITER": 0.6,
    "COMMENT": 0.7,
    "NEWLINE": 0.8,
    "INDENT": 0.85,
    "DEDENT": 0.85,
    "WHITESPACE": 0.9,
    "ERROR": 1.0,
}


# ── Mathematical & Helper Routines ────────────────────────────────────────────


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Computes exact Levenshtein edit distance with short-circuit for <= 1."""
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    if abs(len1 - len2) > 1:
        return 2
    if len1 > len2:
        s1, s2 = s2, s1
        len1, len2 = len2, len1
    if len2 - len1 == 1:
        for i in range(len2):
            if s2[:i] + s2[i + 1 :] == s1:
                return 1
        return 2
    diffs = sum(1 for a, b in zip(s1, s2, strict=False) if a != b)
    return diffs if diffs <= 1 else 2


def _compute_entropy(text: str, n: int = 1) -> float:
    """Calculates empirical Shannon entropy of n-grams (base 2)."""
    if not text or len(text) < n:
        return 0.0
    ngrams: list[str] = [text[i : i + n] for i in range(len(text) - n + 1)]
    total = len(ngrams)
    counts: dict[str, int] = {}
    for ng in ngrams:
        counts[ng] = counts.get(ng, 0) + 1
    ent = 0.0
    for count in counts.values():
        p = count / total
        ent -= p * math.log2(p)
    return float(ent)


def _max_run_length(text: str) -> int:
    """Computes maximum consecutive identical character run."""
    if not text:
        return 0
    max_run = 1
    current_run = 1
    for i in range(1, len(text)):
        if text[i] == text[i - 1]:
            current_run += 1
            if current_run > max_run:
                max_run = current_run
        else:
            current_run = 1
    return max_run


def _check_base64(text: str) -> bool:
    """Validates whether a string has typical base64 encoding characteristics."""
    clean = text.strip("'\"` \t\r\n")
    if len(clean) < 8 or len(clean) % 4 != 0:
        return False
    if not re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", clean):
        return False
    try:
        decoded = base64.b64decode(clean, validate=True)
        return len(decoded) > 0
    except (binascii.Error, ValueError):
        return False


def _check_hex(text: str) -> bool:
    """Validates whether a string has typical hex encoding characteristics."""
    clean = text.strip("'\"` \t\r\n")
    if clean.startswith(("0x", "0X")):
        clean = clean[2:]
    if len(clean) >= 8 and len(clean) % 2 == 0 and re.fullmatch(r"[0-9a-fA-F]+", clean):
        return True
    return False


def _check_decoded_payload_danger(text: str) -> bool:
    """Decodes potential base64 or hex payloads and inspects for danger words."""
    clean = text.strip("'\"` \t\r\n")
    decoded_bytes: bytes | None = None
    if _check_base64(clean):
        try:
            decoded_bytes = base64.b64decode(clean, validate=True)
        except Exception:
            pass
    elif _check_hex(clean):
        hex_str = clean[2:] if clean.startswith(("0x", "0X")) else clean
        try:
            decoded_bytes = bytes.fromhex(hex_str)
        except Exception:
            pass

    if decoded_bytes:
        try:
            decoded_str = decoded_bytes.decode("utf-8", errors="ignore").lower()
            return any(word in decoded_str for word in PAYLOAD_DANGER_WORDS)
        except Exception:
            return False
    return False


# ── Feature Extraction Core ───────────────────────────────────────────────────


def extract_token_features(
    token: Token,
    idx: int,
    tokens: list[Token],
    recovered_text_map: dict[int, str] | None = None,
    language: str = "python",
) -> tuple[list[float], int]:
    """Extracts exactly 45 features for a single token in context.

    Note: Following strict architectural rules, taint tracking and rule results
    are NEVER accessed or used as input features.

    Args:
        token: Target Token instance.
        idx: 0-based index of target token in `tokens`.
        tokens: Full sequence of tokens for context extraction.
        recovered_text_map: Optional precomputed mapping of token index to recovered text.
        language: Language identifier string (default: 'python').

    Returns:
        tuple containing:
            - features: list of exactly 45 float values in canonical order.
            - language_id: integer language encoding.
    """
    text = token.text
    t_len = len(text)
    clean_text = text.strip("'\"`")
    clean_lower = clean_text.lower()

    # Determine recovered text
    recovered = (
        recovered_text_map.get(idx)
        if recovered_text_map is not None
        else recover_text(text).recovered_text
    )
    if recovered is None:
        recovered = text

    # [0-3] kind id normalised, length/64 capped, is_numeric, is_keyword
    f0 = TOKEN_KIND_MAP.get(token.kind, 0.0)
    f1 = min(1.0, t_len / 64.0)
    f2 = 1.0 if token.kind == "NUMBER" or text.isdigit() else 0.0
    f3 = 1.0 if token.kind == "KEYWORD" or text in COMMON_KEYWORDS else 0.0

    # [4-9] Unicode features
    f4 = float(sum(1 for ch in text if ord(ch) in ZERO_WIDTH_CHARS))
    f5 = float(sum(1 for ch in text if ord(ch) in BIDI_CONTROLS))
    f6 = float(sum(1 for ch in text if ch in _CONFUSABLES_MAP))
    f7 = float(sum(1 for ch in text if ord(ch) > 127) / max(1, t_len))
    f8 = 1.0 if is_mixed_script(text) else 0.0
    f9 = float(sum(1 for ch in text if 0xE0000 <= ord(ch) <= 0xE007F))

    # [10-13] Entropy features
    f10 = _compute_entropy(text, n=1)
    f11 = _compute_entropy(text, n=2)
    f12 = _compute_entropy(text, n=3)
    max_possible_entropy = math.log2(max(2, t_len))
    f13 = min(1.0, f10 / max_possible_entropy) if t_len > 1 else 0.0

    # [14-18] Character distribution statistics
    f14 = float(sum(1 for ch in text if ch.isdigit()) / max(1, t_len))
    f15 = float(sum(1 for ch in text if ch.isupper()) / max(1, t_len))
    f16 = float(sum(1 for ch in text if ch in string.punctuation) / max(1, t_len))
    f17 = float(sum(1 for ch in text if ch.isspace()) / max(1, t_len))
    f18 = min(1.0, _max_run_length(text) / max(1, t_len))

    # [19-22] Recovery features
    f19 = 1.0 if recovered != text else 0.0
    f20 = min(1.0, _levenshtein_distance(text, recovered) / max(1, t_len))
    f21 = 1.0 if recovered.lower().strip("'\"`") in DANGEROUS_APIS else 0.0
    f22 = 1.0 if recovered in COMMON_KEYWORDS else 0.0

    # [23-25] Obfuscation / payload features
    f23 = 1.0 if _check_base64(text) else 0.0
    f24 = 1.0 if _check_hex(text) else 0.0
    f25 = 1.0 if _check_decoded_payload_danger(text) else 0.0

    # [26-30] Dangerous APIs, SQL, Shell, and Fuzzy Distance
    f26 = 1.0 if clean_lower in DANGEROUS_APIS else 0.0
    f27 = 1.0 if any(api in clean_lower for api in DANGEROUS_APIS if len(api) >= 3) else 0.0
    f28 = 1.0 if clean_text.upper() in SQL_KEYWORDS else 0.0
    f29 = 1.0 if any(sh in text for sh in SHELL_PATTERNS) else 0.0

    # Fuzzy dangerous (true Levenshtein edit distance <= 1 to any dangerous API, excluding exact matches)
    is_fuzzy = False
    if not f26:
        for api in DANGEROUS_APIS:
            if _levenshtein_distance(clean_lower, api) <= 1:
                is_fuzzy = True
                break
    f30 = 1.0 if is_fuzzy else 0.0

    # [31-35] Syntactic context features
    f31 = (
        1.0
        if token.kind == "STRING" or (text.startswith(("'", '"')) and text.endswith(("'", '"')))
        else 0.0
    )
    f32 = 1.0 if token.kind == "COMMENT" or text.startswith("#") else 0.0

    # Look ahead for call: is next non-trivia token '(' ?
    is_call_val = 0.0
    for j in range(idx + 1, min(len(tokens), idx + 5)):
        if tokens[j].kind not in ("WHITESPACE", "COMMENT", "NEWLINE"):
            if tokens[j].text == "(":
                is_call_val = 1.0
            break
    f33 = is_call_val

    # Member access: is previous non-trivia token '.' ?
    is_member_val = 0.0
    for j in range(idx - 1, max(-1, idx - 5), -1):
        if tokens[j].kind not in ("WHITESPACE", "COMMENT", "NEWLINE"):
            if tokens[j].text in (".", "->"):
                is_member_val = 1.0
            break
    f34 = is_member_val

    # Nesting depth: count open brackets vs closed brackets prior to this token on same line/scope
    depth = 0
    line_start_idx = idx
    while line_start_idx > 0 and tokens[line_start_idx - 1].kind not in ("NEWLINE",):
        line_start_idx -= 1
        tok_t = tokens[line_start_idx].text
        if tok_t in ("(", "[", "{"):
            depth += 1
        elif tok_t in (")", "]", "}"):
            depth = max(0, depth - 1)
    f35 = min(1.0, depth / 10.0)

    # [36-38] Enclosing Call features
    # Check if inside call parentheses, whether first arg, has concat, or is known sink
    is_first_arg = 0.0
    has_concat = 0.0
    is_sink = 0.0

    # Scan backwards to enclosing '('
    paren_depth = 0
    enclosing_open_idx = -1
    for j in range(idx - 1, max(-1, idx - 40), -1):
        t_char = tokens[j].text
        if t_char == ")":
            paren_depth += 1
        elif t_char == "(":
            if paren_depth > 0:
                paren_depth -= 1
            else:
                enclosing_open_idx = j
                break

    if enclosing_open_idx != -1:
        # Check if first argument (no comma between enclosing '(' and target token)
        saw_comma = False
        comma_depth = 0
        for j in range(enclosing_open_idx + 1, idx):
            if tokens[j].text in ("(", "[", "{"):
                comma_depth += 1
            elif tokens[j].text in (")", "]", "}"):
                comma_depth = max(0, comma_depth - 1)
            elif tokens[j].text == "," and comma_depth == 0:
                saw_comma = True
                break
        if not saw_comma:
            is_first_arg = 1.0

        # Check function name preceding enclosing '('
        for j in range(enclosing_open_idx - 1, max(-1, enclosing_open_idx - 6), -1):
            if tokens[j].kind not in ("WHITESPACE", "COMMENT", "NEWLINE"):
                call_func = tokens[j].text.lower()
                if call_func in KNOWN_SINKS or any(
                    tokens[j].text.lower().endswith(f".{sink}") for sink in KNOWN_SINKS
                ):
                    is_sink = 1.0
                break

        # Check if enclosing call contains '+' or string concatenation
        close_paren_idx = len(tokens)
        c_depth = 1
        for j in range(enclosing_open_idx + 1, min(len(tokens), enclosing_open_idx + 50)):
            if tokens[j].text == "(":
                c_depth += 1
            elif tokens[j].text == ")":
                c_depth -= 1
                if c_depth == 0:
                    close_paren_idx = j
                    break
        for j in range(enclosing_open_idx + 1, close_paren_idx):
            if (
                tokens[j].text in ("+", "%")
                or tokens[j].kind == "OPERATOR"
                and "+" in tokens[j].text
            ):
                has_concat = 1.0
                break

    f36 = is_first_arg
    f37 = has_concat
    f38 = is_sink

    # [39-41] Local Window / Neighbour Features (window of +/- 4 tokens)
    left_start = max(0, idx - 4)
    right_end = min(len(tokens), idx + 5)
    neighbour_tokens = [tokens[j] for j in range(left_start, right_end) if j != idx]
    num_neighbours = max(1, len(neighbour_tokens))

    danger_count = sum(
        1
        for nt in neighbour_tokens
        if nt.text.lower().strip("'\"`") in DANGEROUS_APIS
        or nt.text.upper() in SQL_KEYWORDS
        or nt.text in SHELL_PATTERNS
    )
    string_count = sum(1 for nt in neighbour_tokens if nt.kind == "STRING")
    operator_count = sum(
        1
        for nt in neighbour_tokens
        if nt.kind == "OPERATOR" or nt.text in ("+", "-", "*", "/", "%", "=", "==", "!=")
    )

    f39 = float(danger_count / num_neighbours)
    f40 = float(string_count / num_neighbours)
    f41 = float(operator_count / num_neighbours)

    # [42-44] Core Syntax Categories
    f42 = 1.0 if token.kind == "IDENTIFIER" else 0.0
    f43 = 1.0 if token.kind == "STRING" else 0.0
    f44 = 1.0 if token.kind == "OPERATOR" else 0.0

    features = [
        f0,
        f1,
        f2,
        f3,
        f4,
        f5,
        f6,
        f7,
        f8,
        f9,
        f10,
        f11,
        f12,
        f13,
        f14,
        f15,
        f16,
        f17,
        f18,
        f19,
        f20,
        f21,
        f22,
        f23,
        f24,
        f25,
        f26,
        f27,
        f28,
        f29,
        f30,
        f31,
        f32,
        f33,
        f34,
        f35,
        f36,
        f37,
        f38,
        f39,
        f40,
        f41,
        f42,
        f43,
        f44,
    ]

    lang_id = LANGUAGE_IDS.get(language.lower(), 0)
    return features, lang_id


def extract_file_features(
    tokens: list[Token],
    language: str = "python",
) -> tuple[np.ndarray, int]:
    """Extracts features for all tokens in a document into an (N, 45) matrix.

    Args:
        tokens: Sequence of tokens from lexer.
        language: Language identifier (default: 'python').

    Returns:
        tuple containing:
            - feature_matrix: np.ndarray of shape (N, 45) with dtype float32.
            - language_id: integer language identifier.
    """
    if not tokens:
        return np.empty((0, FEATURE_COUNT), dtype=np.float32), LANGUAGE_IDS.get(language, 0)

    # Precompute recovered text mapping for all tokens efficiently
    recovered_map: dict[int, str] = {}
    for i, tok in enumerate(tokens):
        if any(ord(ch) > 127 for ch in tok.text):
            recovered_map[i] = recover_text(tok.text).recovered_text
        else:
            recovered_map[i] = tok.text

    feature_rows: list[list[float]] = []
    lang_id = 0
    for i, tok in enumerate(tokens):
        feats, lang_id = extract_token_features(
            tok,
            i,
            tokens,
            recovered_text_map=recovered_map,
            language=language,
        )
        feature_rows.append(feats)

    matrix = np.array(feature_rows, dtype=np.float32)
    return matrix, lang_id
