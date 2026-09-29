"""
Phase 1 & 2 — Unicode Recovery Engine + 45-Feature Extractor
============================================================
Implements:
  Phase 1 -> Unicode detection (ZWS, Bidi), NFKC normalization,
             confusable mapping, recovery pipeline
  Phase 2 -> 45-dimensional feature vector per token
"""

from __future__ import annotations

import base64
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────
# PHASE 1: CONSTANTS
# ─────────────────────────────────────────────────────────────────

# Zero-width / invisible characters
ZWS_CHARS = ['\u200b', '\u200c', '\u200d', '\u2060', '\ufeff']
ZWS_SET   = set(ZWS_CHARS)

# Bidirectional override characters
BIDI_SET  = set(chr(c) for c in range(0x202A, 0x202F))
BIDI_SET |= {'\u200e', '\u200f', '\u2066', '\u2067', '\u2068', '\u2069'}

# Confusable map: visually similar unicode -> ASCII equivalent
# Expanded from the roadmap's starter set
CONFUSABLE: Dict[str, str] = {
    # Cyrillic -> Latin
    '\u0430': 'a',   # а -> a
    '\u0435': 'e',   # е -> e
    '\u043e': 'o',   # о -> o
    '\u043f': 'n',   # п -> n  (less common but used)
    '\u0441': 'c',   # с -> c
    '\u0445': 'x',   # х -> x
    '\u0443': 'y',   # у -> y
    '\u04cf': 'i',   # ӏ -> i
    '\u0455': 's',   # ѕ -> s
    '\u0456': 'i',   # і -> i
    '\u0440': 'r',   # р -> r
    '\u0442': 't',   # т (sometimes used)
    # Greek -> Latin
    '\u03b1': 'a',   # α -> a
    '\u03b2': 'b',   # β -> b  (loose)
    '\u03b3': 'y',   # γ
    '\u03b5': 'e',   # ε -> e
    '\u03c1': 'p',   # ρ -> p
    '\u03bf': 'o',   # ο -> o
    '\u03bd': 'v',   # ν -> v
    # Fullwidth ASCII
    **{chr(0xFF01 + i): chr(0x21 + i) for i in range(94)},
}

# Dangerous API keywords (for feature scoring)
DANGEROUS_APIS = frozenset({
    "exec", "eval", "compile", "__import__", "getattr", "setattr",
    "delattr", "globals", "locals", "vars", "dir",
    "os", "system", "popen", "subprocess", "call", "check_call",
    "check_output", "Popen", "pickle", "marshal", "shelve",
    "importlib", "ctypes", "cffi", "socket", "urllib", "requests",
})

# SQL keywords
SQL_KEYWORDS = frozenset({
    "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
    "ALTER", "TRUNCATE", "UNION", "EXEC", "FROM", "WHERE",
})

# Shell patterns
SHELL_PATTERNS = frozenset({
    "rm", "wget", "curl", "chmod", "chown", "bash", "sh",
    "nc", "netcat", "powershell", "cmd", "cat", "passwd","exec"
})


# ─────────────────────────────────────────────────────────────────
# PHASE 1: RECOVERY ENGINE
# ─────────────────────────────────────────────────────────────────

@dataclass
class RecoveryResult:
    """Holds both original and recovered token plus transformation log."""
    original:        str
    recovered:       str
    changed:         bool
    zws_removed:     int   = 0
    bidi_removed:    int   = 0
    confusables_mapped: int = 0
    normalized:      bool  = False
    log:             List[str] = field(default_factory=list)

    @property
    def diff_ratio(self) -> float:
        """How different is recovered from original (0=same, 1=completely different)."""
        if not self.original:
            return 0.0
        diffs = sum(a != b for a, b in zip(self.original, self.recovered))
        diffs += abs(len(self.original) - len(self.recovered))
        return min(diffs / max(len(self.original), 1), 1.0)


class RecoveryEngine:
    """
    Implements the full Phase 1 recovery pipeline:
      normalize -> map confusables -> strip zero-width -> strip bidi
    Original token is NEVER overwritten — both are preserved.
    """

    def recover(self, token: str) -> RecoveryResult:
        result = RecoveryResult(original=token, recovered=token, changed=False)

        t = token

        # Step 1: NFKC normalization (compatibility decomposition + composition)
        t_norm = unicodedata.normalize('NFKC', t)
        if t_norm != t:
            result.normalized = True
            result.log.append(f"NFKC normalized: {repr(t)} -> {repr(t_norm)}")
            t = t_norm

        # Step 2: Map confusable characters
        t_conf, n_conf = self._map_confusables(t)
        if n_conf:
            result.confusables_mapped = n_conf
            result.log.append(f"Confusables mapped: {n_conf} chars")
            t = t_conf

        # Step 3: Remove zero-width characters
        t_zws, n_zws = self._remove_chars(t, ZWS_SET)
        if n_zws:
            result.zws_removed = n_zws
            result.log.append(f"Zero-width removed: {n_zws} chars")
            t = t_zws

        # Step 4: Remove bidi override characters
        t_bidi, n_bidi = self._remove_chars(t, BIDI_SET)
        if n_bidi:
            result.bidi_removed = n_bidi
            result.log.append(f"Bidi chars removed: {n_bidi} chars")
            t = t_bidi

        result.recovered = t
        result.changed   = (t != token)
        return result

    def _map_confusables(self, text: str) -> Tuple[str, int]:
        count  = 0
        result = []
        for ch in text:
            mapped = CONFUSABLE.get(ch)
            if mapped:
                result.append(mapped)
                count += 1
            else:
                result.append(ch)
        return ''.join(result), count

    def _remove_chars(self, text: str, char_set: set) -> Tuple[str, int]:
        removed = 0
        result  = []
        for ch in text:
            if ch in char_set:
                removed += 1
            else:
                result.append(ch)
        return ''.join(result), removed

    def scan_for_unicode_threats(self, text: str) -> Dict:
        """Quick scan of raw source for unicode threats before tokenization."""
        zws_count  = sum(text.count(c) for c in ZWS_CHARS)
        bidi_count = sum(text.count(c) for c in BIDI_SET)
        conf_count = sum(1 for ch in text if ch in CONFUSABLE)
        return {
            "zws_count":   zws_count,
            "bidi_count":  bidi_count,
            "conf_count":  conf_count,
            "has_threats": (zws_count + bidi_count + conf_count) > 0,
        }


# ─────────────────────────────────────────────────────────────────
# PHASE 2: 45-FEATURE EXTRACTOR
# ─────────────────────────────────────────────────────────────────

_recovery_engine = RecoveryEngine()   # module-level singleton


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total  = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


def _keyword_score(text: str) -> float:
    """0–1 score based on exact or substring match with dangerous keywords."""
    lower = text.lower()
    # Exact match
    if lower in DANGEROUS_APIS or text.upper() in SQL_KEYWORDS:
        return 1.0
    # Substring match (partial)
    for kw in DANGEROUS_APIS:
        if kw in lower:
            return 0.6
    for kw in SQL_KEYWORDS:
        if kw in text.upper():
            return 0.6
    for kw in SHELL_PATTERNS:
        if kw in lower:
            return 0.5
    return 0.0


def _fuzzy_keyword_score(text: str) -> float:
    """
    Simple character-overlap fuzzy score against dangerous keywords.
    Catches obfuscated variants like 'ex_ec', 'ev4l', etc.
    """
    lower = text.lower()
    best  = 0.0
    for kw in list(DANGEROUS_APIS)[:20]:   # top-20 for speed
        if len(kw) < 3:
            continue
        overlap = sum(1 for ch in kw if ch in lower)
        score   = overlap / len(kw)
        if score > best:
            best = score
    return min(best, 1.0)


def _is_base64(text: str) -> bool:
    """Heuristic: long alphanum string with optional = padding."""
    stripped = text.strip('"\'')
    if len(stripped) < 12:
        return False
    if not re.fullmatch(r'[A-Za-z0-9+/]+=*', stripped):
        return False
    # Accept if length is divisible by 4 OR close to it (within 1-2 chars with padding)
    padded = stripped + '=' * (-len(stripped) % 4)
    try:
        base64.b64decode(padded)
        return True
    except Exception:
        return False

def _decoded_keyword_score(text: str) -> float:
    """Try to base64-decode and score the decoded content."""
    stripped = text.strip('"\'')
    try:
        decoded = base64.b64decode(stripped + '==').decode('utf-8', errors='ignore')
        return _keyword_score(decoded)
    except Exception:
        return 0.0


def _count_zws(text: str) -> int:
    return sum(text.count(c) for c in ZWS_CHARS)


def _count_bidi(text: str) -> int:
    return sum(1 for ch in text if ch in BIDI_SET)


def _count_confusables(text: str) -> int:
    return sum(1 for ch in text if ch in CONFUSABLE)


def extract_45_features(token, neighbor_tokens: Optional[List] = None) -> List[float]:
    """
    Extract exactly 45 features from a SecureToken.
    neighbor_tokens: list of nearby SecureTokens (window around current token)

    Feature groups:
      [0-3]   Token type & length
      [4-9]   Unicode counts
      [10-13] Entropy
      [14-18] Character composition ratios
      [19-22] Recovery features
      [23-25] Encoding features
      [26-30] Security / keyword scores
      [31-35] Context flags
      [36-38] Rule-based security
      [39-41] Neighbor density
      [42-44] Token type one-hot (identifier / string / keyword)
    """
    raw = token.raw_value if token.raw_value else ""

    # ── Recovery ──────────────────────────────────────────────────
    rec = _recovery_engine.recover(raw)

    features = [0.0] * 45

    # [0] Token type (normalised)
    features[0] = token.token_type.value / 50.0

    # [1] Length
    length = len(raw)
    features[1] = min(length / 100.0, 1.0)

    # [2] Word count (spaces + 1)
    features[2] = min((raw.count(' ') + 1) / 10.0, 1.0)

    # [3] Is numeric literal
    try:
        float(raw)
        features[3] = 1.0
    except (ValueError, TypeError):
        features[3] = 0.0

    # [4] Zero-width char count
    features[4] = min(_count_zws(raw) / 5.0, 1.0)

    # [5] Bidi char count
    features[5] = min(_count_bidi(raw) / 5.0, 1.0)

    # [6] Confusable char count
    features[6] = min(_count_confusables(raw) / 10.0, 1.0)

    # [7] Non-ASCII ratio
    non_ascii = sum(1 for ch in raw if ord(ch) >= 128)
    features[7] = non_ascii / max(length, 1)

    # [8] Homoglyph count (from pre-computed unicode props if available)
    if token.unicode:
        features[8] = min(token.unicode.homoglyph_count / 10.0, 1.0)
    else:
        features[8] = features[6]   # fall back to confusable count

    # [9] Script count (mixed scripts signal)
    if token.unicode:
        features[9] = min(len(token.unicode.scripts_present) / 5.0, 1.0)
    else:
        features[9] = 0.0

    # [10] Character entropy
    features[10] = min(_shannon_entropy(raw) / 5.0, 1.0)

    # [11] Bigram entropy
    bigrams = [raw[i:i+2] for i in range(len(raw) - 1)]
    features[11] = min(_shannon_entropy(''.join(bigrams)) / 5.0, 1.0) if bigrams else 0.0

    # [12] Trigram entropy
    trigrams = [raw[i:i+3] for i in range(len(raw) - 2)]
    features[12] = min(_shannon_entropy(''.join(trigrams)) / 5.0, 1.0) if trigrams else 0.0

    # [13] Normalised entropy (char_entropy / log2(unique_chars))
    unique = len(set(raw))
    if unique > 1 and length > 0:
        features[13] = min(_shannon_entropy(raw) / math.log2(unique), 1.0)

    # [14] Digit ratio
    features[14] = sum(c.isdigit() for c in raw) / max(length, 1)

    # [15] Uppercase ratio
    features[15] = sum(c.isupper() for c in raw) / max(length, 1)

    # [16] Special character ratio
    features[16] = sum(not c.isalnum() and c not in ('_', ' ') for c in raw) / max(length, 1)

    # [17] Lowercase ratio
    features[17] = sum(c.islower() for c in raw) / max(length, 1)

    # [18] Underscore ratio
    features[18] = raw.count('_') / max(length, 1)

    # [19] Recovery changed flag
    features[19] = 1.0 if rec.changed else 0.0

    # [20] Normalized diff ratio
    features[20] = rec.diff_ratio

    # [21] ZWS removed count (from recovery)
    features[21] = min(rec.zws_removed / 5.0, 1.0)

    # [22] Confusables mapped count (from recovery)
    features[22] = min(rec.confusables_mapped / 10.0, 1.0)

    # [23] Is Base64
    features[23] = 1.0 if _is_base64(raw) else 0.0

    # [24] Decoded keyword score (only meaningful if base64)
    features[24] = _decoded_keyword_score(raw) if features[23] > 0 else 0.0

    # [25] Entropy of RECOVERED token (catches obfuscation that recovery fixes)
    features[25] = min(_shannon_entropy(rec.recovered) / 5.0, 1.0)

    # [26] Keyword score (raw)
    features[26] = _keyword_score(raw)

    # [27] Keyword score (recovered) — catches homoglyph-obfuscated keywords
    features[27] = _keyword_score(rec.recovered)

    # [28] Fuzzy keyword score
    features[28] = _fuzzy_keyword_score(raw)

    # [29] Dangerous API flag
    features[29] = 1.0 if raw.lower() in DANGEROUS_APIS else 0.0

    # [30] SQL keyword flag
    features[30] = 1.0 if raw.upper() in SQL_KEYWORDS else 0.0

    # [31] Context: nesting depth
    if token.context:
        features[31] = min(token.context.nesting_depth / 10.0, 1.0)
    
    # [32] Context: follows import
    if token.context:
        features[32] = 1.0 if token.context.follows_import else 0.0

    # [33] Context: near exec/eval
    if token.context:
        features[33] = 1.0 if token.context.precedes_exec_or_eval else 0.0

    # [34] Context: is dunder
    if token.context:
        features[34] = 1.0 if token.context.is_dunder else 0.0

    # [35] Context: is builtin shadow
    if token.context:
        features[35] = 1.0 if token.context.is_builtin_shadow else 0.0

    # [36] Security score (rule-based)
    if token.security:
        features[36] = token.security.score

    # [37] Is suspicious (rule-based flag)
    if token.security:
        features[37] = 1.0 if token.security.is_suspicious else 0.0

    # [38] Shell pattern match
    if token.context:
        features[38] = 1.0 if token.context.matches_shell_pattern else 0.0

    # [39-41] Neighbor keyword density (tokens around this one)
    if neighbor_tokens:
        n_dangerous = sum(
            1 for t in neighbor_tokens
            if t.raw_value.lower() in DANGEROUS_APIS
            or t.raw_value.upper() in SQL_KEYWORDS
        )
        n_suspicious = sum(
            1 for t in neighbor_tokens
            if t.security and t.security.is_suspicious
        )
        n_high_entropy = sum(
            1 for t in neighbor_tokens
            if t.entropy and t.entropy.char_entropy > 3.5
        )
        total_neighbors = max(len(neighbor_tokens), 1)
        features[39] = min(n_dangerous / total_neighbors, 1.0)
        features[40] = min(n_suspicious / total_neighbors, 1.0)
        features[41] = min(n_high_entropy / total_neighbors, 1.0)

    # [42] Is IDENTIFIER token type
    try:
        from W5_6.token_models import TokenType
        features[42] = 1.0 if token.token_type == TokenType.IDENTIFIER else 0.0
        features[43] = 1.0 if token.token_type == TokenType.STRING else 0.0
        features[44] = 1.0 if token.token_type == TokenType.KEYWORD else 0.0
    except ImportError:
        # Fallback: use numeric token type value
        tv = token.token_type.value
        features[42] = 1.0 if tv == 7 else 0.0   # IDENTIFIER
        features[43] = 1.0 if tv == 3 else 0.0   # STRING
        features[44] = 1.0 if tv == 8 else 0.0   # KEYWORD

    return features


def extract_45_features_array(token, neighbor_tokens=None):
    """Returns numpy array version of extract_45_features."""
    import numpy as np
    return np.array(extract_45_features(token, neighbor_tokens), dtype=np.float32)
