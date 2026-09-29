"""
Week 5 – Secure Token and Model Design
"""

from __future__ import annotations

import math
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

# 1. TOKEN TYPE TAXONOMY

class TokenType(Enum):
    """Exhaustive set of token categories for a Python lexer."""
    # Literals
    INTEGER      = auto()
    FLOAT        = auto()
    STRING       = auto()
    BYTES        = auto()
    BOOL         = auto()
    NONE         = auto()

    # Identifiers & keywords
    IDENTIFIER   = auto()
    KEYWORD      = auto()

    # Operators
    ARITHMETIC   = auto()
    COMPARISON   = auto()
    LOGICAL      = auto()
    BITWISE      = auto()
    ASSIGNMENT   = auto()

    # Delimiters
    LPAREN       = auto()
    RPAREN       = auto()
    LBRACKET     = auto()
    RBRACKET     = auto()
    LBRACE       = auto()
    RBRACE       = auto()
    COMMA        = auto()
    COLON        = auto()
    SEMICOLON    = auto()
    DOT          = auto()

    # Structural
    NEWLINE      = auto()
    INDENT       = auto()
    DEDENT       = auto()
    COMMENT      = auto()
    WHITESPACE   = auto()

    # Special / error
    UNKNOWN      = auto()
    ERROR        = auto()


# 2. UNICODE PROPERTIES

@dataclass
class UnicodeProperties:
    """
    Unicode metadata for a token string.
    Captures suspicious patterns used in obfuscation attacks.
    """
    # Category distribution e.g. {"Ll": 3, "Lu": 1, "Nd": 2}
    category_distribution: Dict[str, int] = field(default_factory=dict)

    # Counts
    ascii_count:        int = 0
    non_ascii_count:    int = 0
    zero_width_count:   int = 0   # ​ (U+200B), ⁠ (U+2060), etc.
    control_char_count: int = 0
    rtl_char_count:     int = 0   # Arabic, Hebrew chars used in homograph attacks
    homoglyph_count:    int = 0   # Cyrillic/Greek look-alikes for Latin chars

    # Derived flags
    has_mixed_scripts:  bool = False
    has_invisible_chars:bool = False
    is_pure_ascii:      bool = True

    # Script names present (e.g. {"Latin", "Cyrillic"})
    scripts_present: List[str] = field(default_factory=list)

    @classmethod
    def from_string(cls, text: str) -> "UnicodeProperties":
        """Analyse a raw token string and return its UnicodeProperties."""
        props = cls()

        # Known homoglyph code-points (Cyrillic ↔ Latin, Greek ↔ Latin)
        HOMOGLYPHS = {
            0x0430, 0x0435, 0x043E, 0x043F, 0x0441, 0x0445, 0x0443, 0x04CF, 0x0455,  # Cyrillic
            0x03B1, 0x03B2, 0x03B3, 0x03B4, 0x03B5,0x03C1,0x03BF,                   # Greek
        }
        ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}
        RTL_RANGES = [(0x0590, 0x08FF), (0xFB00, 0xFDFF)]

        scripts: Dict[str, int] = {}

        for ch in text:
            cp = ord(ch)
            cat = unicodedata.category(ch)
            props.category_distribution[cat] = props.category_distribution.get(cat, 0) + 1

            # ASCII / Non-ASCII
            if cp < 128:
                props.ascii_count += 1
            else:
                props.non_ascii_count += 1

            # Zero-width
            if cp in ZERO_WIDTH:
                props.zero_width_count += 1

            # Control chars (Cc) excluding tab/newline
            if cat == "Cc" and ch not in ("\t", "\n", "\r"):
                props.control_char_count += 1

            # RTL chars
            for start, end in RTL_RANGES:
                if start <= cp <= end:
                    props.rtl_char_count += 1
                    break

            # Homoglyphs
            if cp in HOMOGLYPHS:
                props.homoglyph_count += 1

            # Script detection via name prefix
            try:
                uname = unicodedata.name(ch, "")
                script = uname.split()[0] if uname else "UNKNOWN"
                SCRIPT_WHITELIST = {"LATIN", "CYRILLIC", "GREEK", "ARABIC", "HEBREW"}
                if script in SCRIPT_WHITELIST:
                    scripts[script] = scripts.get(script, 0) + 1
            except Exception:
                pass

        props.scripts_present = list(scripts.keys())
        props.is_pure_ascii = props.non_ascii_count == 0
        props.has_invisible_chars = (props.zero_width_count + props.control_char_count) > 0
        props.has_mixed_scripts = len(scripts) > 1

        return props
    
    def risk_level(self) -> str:
        """
        Compute security risk level based on Unicode features.
        """

        if self.zero_width_count > 0:
            return "HIGH"

        if self.homoglyph_count > 0 and self.has_mixed_scripts:
            return "HIGH"

        if self.control_char_count > 0:
            return "HIGH"

        if self.rtl_char_count > 0:
            return "MEDIUM"

        if not self.is_pure_ascii:
            return "MEDIUM"

        return "LOW"


# 3. ENTROPY METRICS

@dataclass
class EntropyMetrics:
    """
    Shannon-entropy based features for a token string.
    High entropy → potential obfuscation / randomised identifier.
    """
    char_entropy:      float = 0.0   # Shannon entropy over individual chars
    bigram_entropy:    float = 0.0   # Shannon entropy over char bigrams
    trigram_entropy:   float = 0.0   # Shannon entropy over char trigrams
    normalised_entropy:float = 0.0   # char_entropy / log2(unique_chars)
    is_high_entropy:   bool  = False  # True when char_entropy > threshold

    ENTROPY_THRESHOLD: float = 3.5   # Typical for natural identifiers < 3.5

    @staticmethod
    def _shannon(counts: Counter) -> float:
        """Compute Shannon entropy H = -Σ p·log₂(p)."""
        total = sum(counts.values())
        if total == 0:
            return 0.0
        return -sum(
            (c / total) * math.log2(c / total)
            for c in counts.values() if c > 0
        )

    @classmethod
    def from_string(cls, text: str) -> "EntropyMetrics":
        """Compute entropy metrics for a given string."""
        em = cls()
        if not text:
            return em

        # Character entropy
        em.char_entropy = cls._shannon(Counter(text))

        # Bigram entropy
        bigrams = [text[i:i+2] for i in range(len(text) - 1)]
        em.bigram_entropy = cls._shannon(Counter(bigrams)) if bigrams else 0.0

        # Trigram entropy
        trigrams = [text[i:i+3] for i in range(len(text) - 2)]
        em.trigram_entropy = cls._shannon(Counter(trigrams)) if trigrams else 0.0

        # Normalised entropy
        unique = len(set(text))
        if unique > 1:
            em.normalised_entropy = em.char_entropy / math.log2(unique)

        em.is_high_entropy = em.char_entropy > cls.ENTROPY_THRESHOLD

        return em


# ─────────────────────────────────────────────
# 4. CONTEXTUAL PATTERNS
# ─────────────────────────────────────────────

@dataclass
class ContextualPatterns:
    """
    Structural / contextual features of a token within a token stream.
    Captures patterns that are suspicious regardless of content.
    """
    position_in_stream:     int   = 0      # Absolute index in token list
    previous_token_type:    Optional[TokenType] = None
    next_token_type:        Optional[TokenType] = None

    # Depth / nesting
    nesting_depth:          int   = 0      # Bracket / paren depth at this token
    is_inside_string:       bool  = False
    is_inside_comment:      bool  = False

    # Structural flags
    follows_import:         bool  = False
    precedes_exec_or_eval:  bool  = False  # exec/eval are high-risk
    is_dunder:              bool  = False  # __name__, __import__, etc.
    is_builtin_shadow:      bool  = False  # Re-defines a Python builtin

    # Pattern matches
    matches_sql_pattern:    bool  = False  # SELECT, DROP, INSERT keywords
    matches_shell_pattern:  bool  = False  # os.system, subprocess, shell=True
    has_base64_pattern:     bool  = False  # long alphanum strings ending in ==

    PYTHON_BUILTINS = frozenset({
        "print", "input", "len", "range", "open", "type", "id",
        "eval", "exec", "compile", "__import__", "getattr", "setattr",
        "hasattr", "delattr", "vars", "dir", "globals", "locals",
    })

    SQL_KEYWORDS = frozenset({
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
        "ALTER", "TRUNCATE", "UNION", "EXEC",
    })

    SHELL_PATTERNS = frozenset({
        "os.system", "subprocess", "shell=True",
        "popen", "check_call", "check_output",
    })

    @classmethod
    def from_token_stream(
        cls,
        token_value: str,
        index: int,
        stream: List["SecureToken"],
        nesting_depth: int = 0,
    ) -> "ContextualPatterns":
        """Derive contextual features from surrounding token stream."""
        cp = cls()
        cp.position_in_stream = index
        cp.nesting_depth = nesting_depth

        if index > 0:
            cp.previous_token_type = stream[index - 1].token_type
        if index < len(stream) - 1:
            cp.next_token_type = stream[index + 1].token_type

        val_upper = token_value.upper()
        cp.matches_sql_pattern    = val_upper in cls.SQL_KEYWORDS
        window = " ".join(t.raw_value for t in stream[max(0, index-2): index+3])
        cp.matches_shell_pattern  = any(p in window for p in cls.SHELL_PATTERNS)
        cp.is_dunder              = token_value.startswith("__") and token_value.endswith("__")
        cp.is_builtin_shadow      = token_value in cls.PYTHON_BUILTINS

        # Simple base64 heuristic: long alphanum string ending with ==
        import re
        cp.has_base64_pattern = bool(
            re.fullmatch(r"[A-Za-z0-9+/]{20,}={0,2}", token_value)
        )

        # Predecessor context
        for j in range(max(0, index - 3), index):
            prev_val = stream[j].raw_value.lower()
            if prev_val == "import":
                cp.follows_import = True
            if prev_val in ("exec", "eval"):
                cp.precedes_exec_or_eval = True

        return cp


# ─────────────────────────────────────────────
# 5. SECURITY SCORE
# ─────────────────────────────────────────────

@dataclass
class SecurityScore:
    """
    Aggregated security risk score for one token.
    Score ∈ [0.0, 1.0].  Above threshold → flag for review.
    """
    score:           float = 0.0
    threshold:       float = 0.5
    is_suspicious:   bool  = False
    reasons:         List[str] = field(default_factory=list)

    WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "non_ascii":          0.15,
        "zero_width":         0.30,
        "high_entropy":       0.20,
        "homoglyph":          0.25,
        "mixed_scripts":      0.20,
        "exec_eval_context":  0.30,
        "sql_keyword":        0.15,
        "shell_pattern":      0.30,
        "base64_pattern":     0.10,
        "builtin_shadow":     0.20,
    })

    @classmethod
    def compute(
        cls,
        unicode_props: UnicodeProperties,
        entropy: EntropyMetrics,
        context: ContextualPatterns,
    ) -> "SecurityScore":
        ss = cls()
        w = ss.WEIGHTS

        total = 0.0
        reasons = []

        if unicode_props.non_ascii_count > 0:
            total += w["non_ascii"]
            reasons.append(f"non-ASCII chars: {unicode_props.non_ascii_count}")

        if unicode_props.zero_width_count > 0:
            total += w["zero_width"]
            reasons.append(f"zero-width chars: {unicode_props.zero_width_count}")

        if entropy.is_high_entropy:
            total += w["high_entropy"]
            reasons.append(f"high entropy: {entropy.char_entropy:.3f}")

        if unicode_props.homoglyph_count > 0:
            total += w["homoglyph"]
            reasons.append(f"homoglyph chars: {unicode_props.homoglyph_count}")

        if unicode_props.has_mixed_scripts:
            total += w["mixed_scripts"]
            reasons.append(f"mixed scripts: {unicode_props.scripts_present}")

        if context.precedes_exec_or_eval:
            total += w["exec_eval_context"]
            reasons.append("used near exec/eval")

        if context.matches_sql_pattern:
            total += w["sql_keyword"]
            reasons.append("matches SQL keyword")

        if context.matches_shell_pattern:
            total += w["shell_pattern"]
            reasons.append("matches shell pattern")

        if context.has_base64_pattern:
            total += w["base64_pattern"]
            reasons.append("possible base64 payload")

        if context.is_builtin_shadow:
            total += w["builtin_shadow"]
            reasons.append(f"shadows Python builtin")

        ss.score = min(total, 1.0)
        ss.reasons = reasons
        ss.is_suspicious = ss.score >= ss.threshold
        return ss


# ─────────────────────────────────────────────
# 6. MAIN SECURE TOKEN DATA MODEL
# ─────────────────────────────────────────────

@dataclass
class SecureToken:
    """
    Complete, enriched token model.
    Combines raw lexical data with security metadata.
    """
    # Core
    raw_value:    str
    token_type:   TokenType
    line:         int
    column:       int

    # Metadata (populated by enrich())
    length:       int                      = field(init=False)
    unicode:      Optional[UnicodeProperties]  = None
    entropy:      Optional[EntropyMetrics]     = None
    context:      Optional[ContextualPatterns] = None
    security:     Optional[SecurityScore]      = None

    def __post_init__(self):
        self.length = len(self.raw_value)

    def enrich(
        self,
        stream: Optional[List["SecureToken"]] = None,
        index: int = 0,
        nesting_depth: int = 0,
    ) -> "SecureToken":
        """
        Populate all metadata fields.
        Call this after the full token stream is available.
        """
        self.unicode  = UnicodeProperties.from_string(self.raw_value)
        self.entropy  = EntropyMetrics.from_string(self.raw_value)
        self.context  = ContextualPatterns.from_token_stream(
            self.raw_value, index, stream or [], nesting_depth
        )
        self.security = SecurityScore.compute(self.unicode, self.entropy, self.context)
        return self

    def to_dict(self) -> dict:
        """Serialise token to a plain dict (JSON-friendly)."""
        return {
            "raw_value":   self.raw_value,
            "token_type":  self.token_type.name,
            "line":        self.line,
            "column":      self.column,
            "length":      self.length,
            "unicode": {
                "is_pure_ascii":      self.unicode.is_pure_ascii if self.unicode else None,
                "non_ascii_count":    self.unicode.non_ascii_count if self.unicode else 0,
                "zero_width_count":   self.unicode.zero_width_count if self.unicode else 0,
                "homoglyph_count":    self.unicode.homoglyph_count if self.unicode else 0,
                "has_mixed_scripts":  self.unicode.has_mixed_scripts if self.unicode else False,
                "scripts":            self.unicode.scripts_present if self.unicode else [],
            },
            "entropy": {
                "char_entropy":       round(self.entropy.char_entropy, 4) if self.entropy else 0,
                "bigram_entropy":     round(self.entropy.bigram_entropy, 4) if self.entropy else 0,
                "normalised_entropy": round(self.entropy.normalised_entropy, 4) if self.entropy else 0,
                "is_high_entropy":    self.entropy.is_high_entropy if self.entropy else False,
            },
            "context": {
                "position":             self.context.position_in_stream if self.context else 0,
                "nesting_depth":        self.context.nesting_depth if self.context else 0,
                "is_dunder":            self.context.is_dunder if self.context else False,
                "is_builtin_shadow":    self.context.is_builtin_shadow if self.context else False,
                "follows_import":       self.context.follows_import if self.context else False,
                "near_exec_eval":       self.context.precedes_exec_or_eval if self.context else False,
                "sql_pattern":          self.context.matches_sql_pattern if self.context else False,
                "shell_pattern":        self.context.matches_shell_pattern if self.context else False,
                "base64_pattern":       self.context.has_base64_pattern if self.context else False,
            },
            "security": {
                "score":        round(self.security.score, 4) if self.security else 0,
                "is_suspicious": self.security.is_suspicious if self.security else False,
                "reasons":      self.security.reasons if self.security else [],
            },
        }
