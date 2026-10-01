"""Hand-written, zero-crash, Unicode-aware lexical analyzer for C and C++.

Supports:
  - C (C89, C99, C11, C23) and C++ (C++98 up to C++20/C++23) keywords
  - Preprocessor directives as a single PREPROCESSOR token, including backslash
    line continuations and #include <header.h> syntax
  - C++11 Raw string literals: R"delim(...)delim" with any delimiter and multi-line support
  - Prefixed string and character literals: L, u8, u, U
  - Numbers: hex (0x), binary (0b), octal (0), digit separators (1'000'000),
    float suffixes (f, l), hex floats (0x1.fp3), and user-defined literal suffixes (10s, 1.5km)
  - All C and C++ operators: ->*, .*, <=>, ::, <<=, >>=, ..., and standard operators
  - Line comments (//) and block comments (/* */)
  - Identifiers including Unicode (XID_Start, XID_Continue)
  - Lossless source reconstruction: "".join(t.text for t in tokens) == source
  - Zero-crash guarantee: unrecognized characters emit ERROR tokens
"""

from __future__ import annotations

import unicodedata
from typing import Final

from apsla.lexing.base import LexerBase
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token

# ── Keywords ──────────────────────────────────────────────────────────────────

C_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "auto",
        "break",
        "case",
        "char",
        "const",
        "continue",
        "default",
        "do",
        "double",
        "else",
        "enum",
        "extern",
        "float",
        "for",
        "goto",
        "if",
        "inline",
        "int",
        "long",
        "register",
        "restrict",
        "return",
        "short",
        "signed",
        "sizeof",
        "static",
        "struct",
        "switch",
        "typedef",
        "union",
        "unsigned",
        "void",
        "volatile",
        "while",
        # C99 / C11 / C23 keywords
        "_Alignas",
        "_Alignof",
        "_Atomic",
        "_Bool",
        "_Complex",
        "_Generic",
        "_Imaginary",
        "_Noreturn",
        "_Static_assert",
        "_Thread_local",
        "typeof",
        "typeof_unqual",
    }
)

CPP_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "alignas",
        "alignof",
        "and",
        "and_eq",
        "asm",
        "atomic_cancel",
        "atomic_commit",
        "atomic_noexcept",
        "bitand",
        "bitor",
        "bool",
        "catch",
        "char8_t",
        "char16_t",
        "char32_t",
        "class",
        "compl",
        "concept",
        "consteval",
        "constexpr",
        "constinit",
        "const_cast",
        "co_await",
        "co_return",
        "co_yield",
        "decltype",
        "delete",
        "dynamic_cast",
        "explicit",
        "export",
        "false",
        "friend",
        "mutable",
        "namespace",
        "new",
        "noexcept",
        "not",
        "not_eq",
        "nullptr",
        "operator",
        "or",
        "or_eq",
        "private",
        "protected",
        "public",
        "reinterpret_cast",
        "requires",
        "static_assert",
        "static_cast",
        "template",
        "this",
        "thread_local",
        "throw",
        "true",
        "try",
        "typeid",
        "typename",
        "using",
        "virtual",
        "wchar_t",
        "xor",
        "xor_eq",
        # Contextual keywords / special identifiers
        "override",
        "final",
        "import",
        "module",
    }
)

ALL_CPP_KEYWORDS: Final[frozenset[str]] = C_KEYWORDS | CPP_KEYWORDS

# ── Operators ─────────────────────────────────────────────────────────────────

OPERATORS_3: Final[frozenset[str]] = frozenset(
    {
        "<=>",
        "->*",
        "<<=",
        ">>=",
        "...",
    }
)

OPERATORS_2: Final[frozenset[str]] = frozenset(
    {
        "::",
        "->",
        ".*",
        "++",
        "--",
        "<<",
        ">>",
        "<=",
        ">=",
        "==",
        "!=",
        "&&",
        "||",
        "+=",
        "-=",
        "*=",
        "/=",
        "%=",
        "&=",
        "|=",
        "^=",
    }
)

OPERATORS_1: Final[frozenset[str]] = frozenset(
    {
        "+",
        "-",
        "*",
        "/",
        "%",
        "^",
        "&",
        "|",
        "~",
        "!",
        "=",
        "<",
        ">",
        "?",
        ":",
        ",",
        ";",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        ".",
    }
)


class CppLexer(LexerBase):
    """Hand-written, zero-crash, Unicode-aware state machine lexer for C and C++.

    Guarantees:
      - Never raises exceptions; unrecognized characters become ERROR tokens.
      - Lossless trivia preservation: "".join(t.text for t in tokens) == source.
      - Exact UTF-16 code unit offset synchronization.
      - C and C++20 keywords, preprocessor directives with line continuations,
        raw string literals (R"delim(...)delim"), prefixed strings (L, u8, u, U),
        digit separators (1'000), hex floats, and user-defined literal suffixes.
    """

    def __init__(self, source: str, offset_map: OffsetMap | None = None) -> None:
        super().__init__(source, offset_map)

    def tokenize(self) -> list[Token]:
        """Perform full lexical analysis, returning complete token sequence."""
        tokens: list[Token] = []

        while not self.is_eof:
            start_pos = self.cursor
            ch = self.peek()

            # 1. Whitespace
            if ch.isspace():
                self._lex_whitespace(tokens)
                continue

            # 2. Preprocessor directive (# at line start or preceded only by whitespace on line)
            if ch == "#" and self._is_at_preprocessor_start(tokens):
                self._lex_preprocessor(tokens)
                continue

            # 3. Comments (// or /* */)
            if ch == "/" and self.peek(1) in ("/", "*"):
                self._lex_comment(tokens)
                continue

            # 4. Raw string literals: R"...", u8R"...", LR"...", uR"...", UR"..."
            if (ch == "R" and self.peek(1) == '"') or (
                ch in ("L", "u", "U") and self._looks_like_raw_string()
            ):
                self._lex_raw_string(tokens)
                continue

            # 5. String or char literals with prefixes: L"...", u8"...", u"...", U"...", L'...', etc.
            if ch in ("L", "u", "U") and self._looks_like_prefixed_literal():
                self._lex_prefixed_literal(tokens)
                continue

            # 6. Standard string literal: "..."
            if ch == '"':
                self._lex_string(tokens)
                continue

            # 7. Character literal: '...'
            if ch == "'":
                self._lex_char(tokens)
                continue

            # 8. Numbers: digits or leading decimal dot (.5)
            if ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self._lex_number(tokens)
                continue

            # 9. Identifiers and keywords
            if self._is_cpp_identifier_start(ch):
                self._lex_identifier(tokens)
                continue

            # 10. Operators & Delimiters
            if self._lex_operator(tokens):
                continue

            # 11. Unrecognized character -> ERROR token
            self.advance()
            tokens.append(self.make_token("ERROR", start_pos, self.cursor))

        return tokens

    # ── Internal Lexing Methods ──────────────────────────────────────────────

    def _is_at_preprocessor_start(self, tokens: list[Token]) -> bool:
        """Check if '#' begins a preprocessor directive (first non-whitespace on line)."""
        if not tokens:
            return True
        last = tokens[-1]
        if "\n" in last.text or "\r" in last.text:
            return True
        # Check backwards in tokens to ensure all prior tokens on this line are whitespace
        for t in reversed(tokens):
            if "\n" in t.text or "\r" in t.text:
                return True
            if t.kind != "WHITESPACE":
                return False
        return True

    def _lex_whitespace(self, tokens: list[Token]) -> None:
        """Accumulate contiguous whitespace characters."""
        start_pos = self.cursor
        while not self.is_eof and self.peek().isspace():
            self.advance()
        tokens.append(self.make_token("WHITESPACE", start_pos, self.cursor))

    def _lex_preprocessor(self, tokens: list[Token]) -> None:
        """Lex a preprocessor directive as a single PREPROCESSOR token.

        Supports backslash line continuations (\\ followed by newline) and
        keeps header names like <stdio.h> or "header.h" inside the token.
        """
        start_pos = self.cursor
        self.advance()  # consume '#'

        while not self.is_eof:
            ch = self.peek()

            # Backslash line continuation
            if ch == "\\":
                next_ch = self.peek(1)
                if next_ch == "\n":
                    self.advance_by(2)
                    continue
                if next_ch == "\r":
                    if self.peek(2) == "\n":
                        self.advance_by(3)
                    else:
                        self.advance_by(2)
                    continue

            # End of directive: unescaped newline
            if ch in ("\n", "\r"):
                break

            # Block comment inside preprocessor directive
            if ch == "/" and self.peek(1) == "*":
                self.advance_by(2)
                while not self.is_eof:
                    if self.peek() == "*" and self.peek(1) == "/":
                        self.advance_by(2)
                        break
                    self.advance()
                continue

            # Line comment inside preprocessor directive: terminates directive
            if ch == "/" and self.peek(1) == "/":
                break

            # Angle-bracket header name in #include <...>
            if ch == "<":
                # Check if this line contains 'include'
                line_so_far = self.source[start_pos : self.cursor]
                if "include" in line_so_far:
                    # Consume up to matching '>'
                    self.advance()
                    while not self.is_eof and self.peek() not in (">", "\n", "\r"):
                        self.advance()
                    if not self.is_eof and self.peek() == ">":
                        self.advance()
                    continue

            # String literal in preprocessor directive (e.g. #include "file.h")
            if ch == '"':
                self.advance()
                while not self.is_eof and self.peek() not in ('"', "\n", "\r"):
                    if self.peek() == "\\" and self.peek(1) in ('"', "\\"):
                        self.advance_by(2)
                    else:
                        self.advance()
                if not self.is_eof and self.peek() == '"':
                    self.advance()
                continue

            self.advance()

        tokens.append(self.make_token("PREPROCESSOR", start_pos, self.cursor))

    def _lex_comment(self, tokens: list[Token]) -> None:
        """Lex single-line (//) or multi-line (/* */) comment."""
        start_pos = self.cursor
        self.advance()  # consume first '/'
        ch = self.peek()
        self.advance()  # consume second '/' or '*'

        if ch == "/":
            # Line comment: runs to newline, respecting backslash line continuation
            while not self.is_eof:
                if self.peek() == "\\":
                    if self.peek(1) == "\n":
                        self.advance_by(2)
                        continue
                    if self.peek(1) == "\r":
                        if self.peek(2) == "\n":
                            self.advance_by(3)
                        else:
                            self.advance_by(2)
                        continue
                if self.peek() in ("\n", "\r"):
                    break
                self.advance()
            tokens.append(self.make_token("COMMENT", start_pos, self.cursor))
        else:
            # Block comment: runs to '*/'
            closed = False
            while not self.is_eof:
                if self.peek() == "*" and self.peek(1) == "/":
                    self.advance_by(2)
                    closed = True
                    break
                self.advance()

            if closed:
                tokens.append(self.make_token("COMMENT", start_pos, self.cursor))
            else:
                tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _looks_like_raw_string(self) -> bool:
        """Check if cursor points to a raw string prefix like R", u8R", LR", uR", UR"."""
        ch = self.peek()
        if ch == "R" and self.peek(1) == '"':
            return True
        if ch in ("L", "u", "U"):
            if self.peek(1) == "R" and self.peek(2) == '"':
                return True
        if ch == "u" and self.peek(1) == "8" and self.peek(2) == "R" and self.peek(3) == '"':
            return True
        return False

    def _lex_raw_string(self, tokens: list[Token]) -> None:
        """Lex a C++11 raw string literal R"delimiter(content)delimiter".

        Can be multi-line and contain arbitrary characters.
        """
        start_pos = self.cursor

        # Consume prefix: R, LR, uR, UR, or u8R
        if self.peek() == "u" and self.peek(1) == "8" and self.peek(2) == "R":
            self.advance_by(3)
        elif self.peek() in ("L", "u", "U") and self.peek(1) == "R":
            self.advance_by(2)
        elif self.peek() == "R":
            self.advance()

        # Consume opening quote
        if self.peek() == '"':
            self.advance()

        # Delimiter extraction: up to 16 chars before '('
        delim_start = self.cursor
        while not self.is_eof and self.peek() != "(" and self.peek() not in ('"', "\n", " "):
            self.advance()

        if self.peek() != "(":
            # Malformed raw string
            tokens.append(self.make_token("ERROR", start_pos, self.cursor))
            return

        delimiter = self.source[delim_start : self.cursor]
        self.advance()  # consume '('

        target_closing = f"){delimiter}\""

        # Scan for closing sequence
        while not self.is_eof:
            if self.peek_slice(len(target_closing)) == target_closing:
                self.advance_by(len(target_closing))
                tokens.append(self.make_token("STRING", start_pos, self.cursor))
                return
            self.advance()

        # Unterminated raw string literal
        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _looks_like_prefixed_literal(self) -> bool:
        """Check if cursor points to a prefixed string or char literal."""
        ch = self.peek()
        if ch in ("L", "u", "U"):
            if self.peek(1) in ('"', "'"):
                return True
        if ch == "u" and self.peek(1) == "8":
            if self.peek(2) in ('"', "'"):
                return True
        return False

    def _lex_prefixed_literal(self, tokens: list[Token]) -> None:
        """Lex string or char literal with prefix L, u8, u, or U."""
        start_pos = self.cursor

        if self.peek() == "u" and self.peek(1) == "8":
            self.advance_by(2)
        else:
            self.advance()

        quote = self.peek()
        if quote == '"':
            self._lex_string_with_start(tokens, start_pos)
        elif quote == "'":
            self._lex_char_with_start(tokens, start_pos)
        else:
            tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_string(self, tokens: list[Token]) -> None:
        """Lex standard double-quoted string literal."""
        start_pos = self.cursor
        self._lex_string_with_start(tokens, start_pos)

    def _lex_string_with_start(self, tokens: list[Token], start_pos: int) -> None:
        """Scan string literal starting at quote until matching unescaped quote."""
        self.advance()  # consume opening '"'

        while not self.is_eof:
            ch = self.peek()
            if ch == "\\":
                # Escape sequence or backslash newline
                next_ch = self.peek(1)
                if next_ch in ("\n", "\r"):
                    if next_ch == "\r" and self.peek(2) == "\n":
                        self.advance_by(3)
                    else:
                        self.advance_by(2)
                    continue
                self.advance_by(2)
                continue

            if ch == '"':
                self.advance()
                # Optional user-defined literal suffix, e.g. "hello"s or "query"_sql
                if not self.is_eof and (self.peek() == "_" or self.peek().isalpha()):
                    while not self.is_eof and (self.peek() == "_" or self.peek().isalnum()):
                        self.advance()
                tokens.append(self.make_token("STRING", start_pos, self.cursor))
                return

            if ch in ("\n", "\r"):
                # Unescaped newline terminates string in C/C++
                break

            self.advance()

        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_char(self, tokens: list[Token]) -> None:
        """Lex standard single-quoted character literal."""
        start_pos = self.cursor
        self._lex_char_with_start(tokens, start_pos)

    def _lex_char_with_start(self, tokens: list[Token], start_pos: int) -> None:
        """Scan character literal starting at quote until matching unescaped quote."""
        self.advance()  # consume opening "'"

        while not self.is_eof:
            ch = self.peek()
            if ch == "\\":
                self.advance_by(2)
                continue
            if ch == "'":
                self.advance()
                # Optional user-defined literal suffix, e.g. 'c'_val
                if not self.is_eof and (self.peek() == "_" or self.peek().isalpha()):
                    while not self.is_eof and (self.peek() == "_" or self.peek().isalnum()):
                        self.advance()
                tokens.append(self.make_token("STRING", start_pos, self.cursor))
                return
            if ch in ("\n", "\r"):
                break
            self.advance()

        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_number(self, tokens: list[Token]) -> None:
        """Lex integer, float, hex, binary, or octal literal.

        Supports:
          - Digit separators: 1'000'000, 0xdead'beef, 0b1010'0101
          - Hex floats: 0x1.fp3, 0x1.0p-4
          - Float suffixes: f, F, l, L
          - Integer suffixes: u, U, l, L, ll, LL, z, Z
          - User-defined literal suffixes: 10s, 1.5km, 42_ns
        """
        start_pos = self.cursor

        # Hex or Binary
        if self.peek() == "0" and self.peek(1).lower() in ("x", "b"):
            is_hex = self.peek(1).lower() == "x"
            self.advance_by(2)
            valid = "0123456789abcdefABCDEF" if is_hex else "01"

            while not self.is_eof:
                ch = self.peek()
                if ch in valid:
                    self.advance()
                elif ch == "'" and self.peek(1) in valid:
                    # Digit separator
                    self.advance_by(2)
                else:
                    break

            # Hex float fractional part (0x1.ff...)
            if is_hex and not self.is_eof and self.peek() == "." and self.peek(1) in valid:
                self.advance()  # consume '.'
                while not self.is_eof:
                    ch = self.peek()
                    if ch in valid:
                        self.advance()
                    elif ch == "'" and self.peek(1) in valid:
                        self.advance_by(2)
                    else:
                        break

            # Hex float binary exponent (p or P)
            if is_hex and not self.is_eof and self.peek().lower() == "p":
                self.advance()  # consume 'p'
                if not self.is_eof and self.peek() in ("+", "-"):
                    self.advance()
                while not self.is_eof and (self.peek().isdigit() or self.peek() == "'"):
                    self.advance()

            self._consume_numeric_suffixes()
            tokens.append(self.make_token("NUMBER", start_pos, self.cursor))
            return

        # Decimal or Octal or Float
        while not self.is_eof:
            ch = self.peek()
            if ch.isdigit():
                self.advance()
            elif ch == "'" and self.peek(1).isdigit():
                # Digit separator (e.g. 1'000)
                self.advance_by(2)
            else:
                break

        # Fractional part (.123)
        if not self.is_eof and self.peek() == "." and self.peek(1) != ".":
            self.advance()  # consume '.'
            while not self.is_eof:
                ch = self.peek()
                if ch.isdigit():
                    self.advance()
                elif ch == "'" and self.peek(1).isdigit():
                    self.advance_by(2)
                else:
                    break

        # Decimal exponent (e or E)
        if not self.is_eof and self.peek().lower() == "e":
            self.advance()  # consume 'e'
            if not self.is_eof and self.peek() in ("+", "-"):
                self.advance()
            while not self.is_eof and (self.peek().isdigit() or self.peek() == "'"):
                self.advance()

        self._consume_numeric_suffixes()
        tokens.append(self.make_token("NUMBER", start_pos, self.cursor))

    def _consume_numeric_suffixes(self) -> None:
        """Consume standard integer/float suffixes or user-defined literal suffix."""
        if self.is_eof:
            return

        # User-defined literal suffix starts with '_' or letters
        ch = self.peek()
        if ch == "_" or ch.isalpha():
            while not self.is_eof and (self.peek() == "_" or self.peek().isalnum()):
                self.advance()

    def _lex_identifier(self, tokens: list[Token]) -> None:
        """Lex identifier or keyword."""
        start_pos = self.cursor
        while not self.is_eof and self._is_cpp_identifier_part(self.peek()):
            self.advance()

        text = self.source[start_pos : self.cursor]
        kind = "KEYWORD" if text in ALL_CPP_KEYWORDS else "IDENTIFIER"
        tokens.append(self.make_token(kind, start_pos, self.cursor))

    def _lex_operator(self, tokens: list[Token]) -> bool:
        """Attempt to match 3, 2, or 1 character operator."""
        start_pos = self.cursor

        # Try 3-character operator
        slice_3 = self.peek_slice(3)
        if slice_3 in OPERATORS_3:
            self.advance_by(3)
            tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
            return True

        # Try 2-character operator
        slice_2 = self.peek_slice(2)
        if slice_2 in OPERATORS_2:
            self.advance_by(2)
            tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
            return True

        # Try 1-character operator
        slice_1 = self.peek()
        if slice_1 in OPERATORS_1:
            self.advance()
            tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
            return True

        return False

    @staticmethod
    def _is_cpp_identifier_start(ch: str) -> bool:
        """Check if character can start a C/C++ identifier."""
        if not ch:
            return False
        if ch.isascii():
            return ch.isalpha() or ch == "_"
        cat = unicodedata.category(ch)
        return cat in ("Lu", "Ll", "Lt", "Lm", "Lo", "Nl")

    @staticmethod
    def _is_cpp_identifier_part(ch: str) -> bool:
        """Check if character can continue a C/C++ identifier."""
        if not ch:
            return False
        if ch.isascii():
            return ch.isalnum() or ch == "_"
        cat = unicodedata.category(ch)
        return cat in ("Lu", "Ll", "Lt", "Lm", "Lo", "Nl", "Nd", "Mn", "Mc", "Pc")
