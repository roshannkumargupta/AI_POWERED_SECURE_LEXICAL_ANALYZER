"""
Week 5 – Token Grammar Specification & I/O Formats
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Tuple

try:
    from W5_6.token_models import TokenType
except ImportError:
    from token_models import TokenType

MAX_IDENTIFIER_LENGTH = 64

# 1. TOKEN GRAMMAR SPECIFICATION

@dataclass
class GrammarRule:
    """One regex-based grammar rule for a token type."""
    token_type:  TokenType
    pattern:     str           # Raw regex string
    compiled:    Pattern = field(init=False, repr=False)
    description: str = ""
    examples:    List[str] = field(default_factory=list)
    counter_ex:  List[str] = field(default_factory=list)  # invalid examples

    def __post_init__(self):
        self.compiled = re.compile(self.pattern)

    def matches(self, text: str) -> bool:
        return bool(self.compiled.fullmatch(text))


class TokenGrammar:
    """
    Complete grammar specification for the AI-Secure Lexer.

    Grammar philosophy:
      - Be strict about identifiers (no invisible chars, no homoglyphs)
      - Accept full Python numeric literal syntax
      - Reject anything that does not match a known rule → ERROR token
    """

    PYTHON_KEYWORDS: frozenset = frozenset({
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
        "try", "while", "with", "yield",
    })

    def __init__(self):
        self.rules: List[GrammarRule] = self._build_rules()

    def _build_rules(self) -> List[GrammarRule]:
        return [
            # ── Whitespace / structural ──────────────────────────────
            GrammarRule(
                TokenType.NEWLINE, r"\n|\r\n|\r",
                description="Line terminator",
                examples=["\n", "\r\n"],
            ),
            GrammarRule(
                TokenType.WHITESPACE, r"[ \t]+",
                description="Horizontal whitespace (spaces and tabs)",
                examples=["   ", "\t"],
            ),
            GrammarRule(
                TokenType.INDENT, r"\t+",
                description="Indentation block",
                examples=["\t", "\t\t"],
            ),
            GrammarRule(
                TokenType.COMMENT, r"#[^\n]*",
                description="Single-line comment starting with #",
                examples=["# hello", "# x = 5"],
            ),

            # ── Numeric literals ─────────────────────────────────────
            GrammarRule(
                TokenType.FLOAT,
                r"(?:\d+\.\d*|\.\d+|\d+[eE][+-]?\d+)(?:[eE][+-]?\d+)?[jJ]?",
                description="Floating-point literal (with optional complex suffix)",
                examples=["3.14", ".5", "1e10", "2.0j"],
                counter_ex=["3.", "1e", "abc"],
            ),
            GrammarRule(
                TokenType.INTEGER,
                r"(0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+|\d+)[jJ]?",
                description="Integer literal (decimal, hex, octal, binary, complex)",
                examples=["42", "0xFF", "0b101", "0o17", "5j"],
                counter_ex=["0x", "0b", "09"],
            ),

            # ── String literals ──────────────────────────────────────
            GrammarRule(
                TokenType.STRING,
                r'(r|u|f|b|rb|br|rf|fr)?'
                r'("""[\s\S]*?"""|' r"'''[\s\S]*?'''|"
                r'"[^"\n]*"|' r"'[^'\n]*')",
                description="String literal with optional prefix (r, u, f, b, rb, rf)",
                examples=['"hello"', "'world'", 'f"x={x}"', r'r"\d+"', '"""multi"""'],
                counter_ex=['"unclosed', "'''unclosed"],
            ),
            GrammarRule(
                TokenType.BYTES,
                r'(b|B)("""[\s\S]*?"""|' r"'''[\s\S]*?'''|"
                r'"[^"\n]*"|' r"'[^'\n]*')",
                description="Bytes literal",
                examples=['b"data"', 'B"\\xff"'],
            ),

            # ── Identifiers & keywords ───────────────────────────────
            GrammarRule(
                TokenType.IDENTIFIER,
                r"[a-zA-Z_][a-zA-Z0-9_]*",
                description=(
                    "Identifier: starts with letter/underscore, "
                    "followed by letters/digits/underscores. ASCII-only."
                ),
                examples=["my_var", "_private", "CamelCase", "x1"],
                counter_ex=["123abc", "", "my-var", "аbc"],  # аbc uses Cyrillic а
            ),

            # ── Operators ────────────────────────────────────────────
            GrammarRule(
                TokenType.COMPARISON,
                r"==|!=|<=|>=|<|>",
                description="Comparison operators",
                examples=["==", "!=", "<=", ">=", "<", ">"],
            ),
            GrammarRule(
                TokenType.LOGICAL,
                r"and|or|not",
                description="Logical operators (keyword form)",
                examples=["and", "or", "not"],
            ),
            GrammarRule(
                TokenType.ASSIGNMENT,
                r"=|\+=|-=|\*=|/=|//=|%=|\*\*=|&=|\|=|\^=|>>=|<<=",
                description="Assignment and augmented assignment",
                examples=["=", "+=", "-=", "**="],
            ),
            GrammarRule(
                TokenType.ARITHMETIC,
                r"\+|-|\*\*|\*|//|/|%|@",
                description="Arithmetic operators",
                examples=["+", "-", "*", "**", "//", "/", "%"],
            ),
            GrammarRule(
                TokenType.BITWISE,
                r"&|\||\^|~|<<|>>",
                description="Bitwise operators",
                examples=["&", "|", "^", "~", "<<", ">>"],
            ),

            # ── Delimiters ───────────────────────────────────────────
            GrammarRule(TokenType.LPAREN,    r"\(", description="Left parenthesis"),
            GrammarRule(TokenType.RPAREN,    r"\)", description="Right parenthesis"),
            GrammarRule(TokenType.LBRACKET,  r"\[", description="Left square bracket"),
            GrammarRule(TokenType.RBRACKET,  r"\]", description="Right square bracket"),
            GrammarRule(TokenType.LBRACE,    r"\{", description="Left curly brace"),
            GrammarRule(TokenType.RBRACE,    r"\}", description="Right curly brace"),
            GrammarRule(TokenType.COMMA,     r",",  description="Comma separator"),
            GrammarRule(TokenType.COLON,     r":",  description="Colon"),
            GrammarRule(TokenType.SEMICOLON, r";",  description="Semicolon"),
            GrammarRule(TokenType.DOT,       r"\.", description="Attribute access / dot"),
        ]

    def classify(self, text: str) -> TokenType:
        """Return the TokenType for a given raw string, or ERROR."""
        # Fast path: Python keywords
        if text in self.PYTHON_KEYWORDS:
            return TokenType.KEYWORD

        for rule in self.rules:
            if rule.matches(text):
                return rule.token_type

        return TokenType.ERROR

    def validate(self, text: str, expected_type: TokenType) -> Tuple[bool, str]:
        """
        Validate that `text` conforms to the grammar rule for `expected_type`.
        Returns (valid, reason_if_invalid).
        """
        for rule in self.rules:
            if rule.token_type == expected_type:
                if rule.compiled.fullmatch(text):
                    return True, ""
                return False, (
                    f"Token '{text!r}' does not match pattern for "
                    f"{expected_type.name}: /{rule.pattern}/"
                )
        return False, f"No grammar rule defined for {expected_type.name}"

    def to_dict(self) -> List[Dict[str, Any]]:
        """Export grammar as a JSON-serialisable list."""
        out = []
        for rule in self.rules:
            out.append({
                "token_type":  rule.token_type.name,
                "pattern":     rule.pattern,
                "description": rule.description,
                "examples":    rule.examples,
                "counter_examples": rule.counter_ex,
            })
        return out


# ─────────────────────────────────────────────
# 2. INPUT FORMAT SPECIFICATION
# ─────────────────────────────────────────────

@dataclass
class LexerInput:
    """
    Validated input container for the secure lexer.

    Accepted sources:
      - raw source code string
      - path to a .py file
      - list of pre-split lines
    """
    source_code:  str
    filename:     str = "<string>"
    encoding:     str = "utf-8"
    language:     str = "python"
    max_file_size_bytes: int = 1_048_576   # 1 MB hard limit

    @classmethod
    def from_string(cls, code: str, filename: str = "<string>") -> "LexerInput":
        return cls(source_code=code, filename=filename)

    @classmethod
    def from_file(cls, path: str) -> "LexerInput":
        import os
        size = os.path.getsize(path)
        if size > 1_048_576:  # 1 MB hard limit
            raise ValueError(f"File too large: {size} bytes (limit 1 MB)")
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            code = fh.read()
        return cls(source_code=code, filename=path)

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Pre-flight validation of input before lexing.
        Returns (ok, list_of_warnings).
        """
        warnings: List[str] = []

        if not self.source_code:
            return False, ["Source code is empty"]

        if len(self.source_code.encode("utf-8")) > self.max_file_size_bytes:
            warnings.append("Source exceeds 1 MB — performance may degrade")

        # Detect embedded null bytes (common in binary injection)
        if "\x00" in self.source_code:
            warnings.append("Null bytes detected in source — possible binary injection")

        # Detect non-standard line endings
        if "\r\n" in self.source_code:
            warnings.append("Windows CRLF line endings detected")
        if "\r" in self.source_code and "\r\n" not in self.source_code:
            warnings.append("Old Mac CR line endings detected")

        return True, warnings

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "encoding": self.encoding,
            "language": self.language,
            "size_bytes": len(self.source_code.encode("utf-8")),
            "line_count": self.source_code.count("\n") + 1,
        }


# 3. OUTPUT FORMAT SPECIFICATION

@dataclass
class LexerOutput:
    """
    Full output of the secure lexer.
    Includes the enriched token list plus summary statistics.
    """
    filename:        str
    tokens:          List[Any]         # List[SecureToken]
    errors:          List[Dict]        # Parse / validation errors
    warnings:        List[str]
    suspicious_tokens: List[Any]       # Tokens flagged by security scorer
    metadata:        Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialise full output to a JSON-friendly dict."""
        return {
            "filename":   self.filename,
            "summary": {
                "total_tokens":      len(self.tokens),
                "error_tokens":      sum(1 for t in self.tokens if t.token_type == TokenType.ERROR),
                "suspicious_tokens": len(self.suspicious_tokens),
                "total_errors":      len(self.errors),
                "total_warnings":    len(self.warnings),
            },
            "tokens":    [t.to_dict() for t in self.tokens],
            "errors":    self.errors,
            "warnings":  self.warnings,
            "suspicious": [t.to_dict() for t in self.suspicious_tokens],
            "metadata":  self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_json())
        print(f"[LexerOutput] Saved to {path}")


# 4. SAMPLE INPUTS AND OUTPUTS  (Week 5 spec)

SAMPLE_INPUTS = {
    "clean_code": """\
def add(a, b):
    \"\"\"Return the sum of a and b.\"\"\"
    return a + b

result = add(3, 7)
print(result)
""",

    "syntax_error_code": """\
def broken(x
    return x * 2
""",

    "obfuscated_code": """\
# Cyrillic homoglyph attack: 'а' (U+0430) looks like 'a'
аdd = lambda х, у: х + у          # Cyrillic identifiers
exec("__import__('os').system('id')")  # Shell injection via exec
""",

    "high_entropy_code": """\
secret = "aGVsbG8gd29ybGQ="        # base64 payload
key    = "x7Kp!mQ@zR#nY$vW"        # random-looking string
""",

    "sql_injection_code": """\
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)
""",
}

SAMPLE_OUTPUTS = {
    "token_summary": {
        "filename": "example.py",
        "summary": {
            "total_tokens": 18,
            "error_tokens": 0,
            "suspicious_tokens": 0,
            "total_errors": 0,
            "total_warnings": 0,
        },
        "tokens": [
            {
                "raw_value": "def",
                "token_type": "KEYWORD",
                "line": 1, "column": 0, "length": 3,
                "unicode": {"is_pure_ascii": True, "non_ascii_count": 0,
                            "zero_width_count": 0, "homoglyph_count": 0,
                            "has_mixed_scripts": False, "scripts": ["LATIN"]},
                "entropy": {"char_entropy": 1.585, "bigram_entropy": 0.0,
                            "normalised_entropy": 1.0, "is_high_entropy": False},
                "context": {"position": 0, "nesting_depth": 0,
                            "is_dunder": False, "is_builtin_shadow": False,
                            "follows_import": False, "near_exec_eval": False,
                            "sql_pattern": False, "shell_pattern": False,
                            "base64_pattern": False},
                "security": {"score": 0.0, "is_suspicious": False, "reasons": []},
            },
        ],
        "errors": [],
        "warnings": [],
        "suspicious": [],
    },
    "suspicious_token_example": {
        "raw_value": "аdd",              # Cyrillic а
        "token_type": "IDENTIFIER",
        "line": 2, "column": 0, "length": 3,
        "unicode": {"is_pure_ascii": False, "non_ascii_count": 1,
                    "zero_width_count": 0, "homoglyph_count": 1,
                    "has_mixed_scripts": True,
                    "scripts": ["LATIN", "CYRILLIC"]},
        "entropy": {"char_entropy": 1.585, "bigram_entropy": 1.0,
                    "normalised_entropy": 1.0, "is_high_entropy": False},
        "context": {"position": 5, "nesting_depth": 0,
                    "is_dunder": False, "is_builtin_shadow": False,
                    "follows_import": False, "near_exec_eval": False,
                    "sql_pattern": False, "shell_pattern": False,
                    "base64_pattern": False},
        "security": {
            "score": 0.6,
            "is_suspicious": True,
            "reasons": [
                "non-ASCII chars: 1",
                "homoglyph chars: 1",
                "mixed scripts: ['LATIN', 'CYRILLIC']",
            ],
        },
    },
}
