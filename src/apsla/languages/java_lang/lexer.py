"""Hand-written, zero-crash, Unicode-aware lexical analyzer for Java."""

from __future__ import annotations

import unicodedata
from typing import Final

from apsla.lexing.base import LexerBase
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token

JAVA_STANDARD_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "abstract",
        "assert",
        "boolean",
        "break",
        "byte",
        "case",
        "catch",
        "char",
        "class",
        "const",
        "continue",
        "default",
        "do",
        "double",
        "else",
        "enum",
        "extends",
        "final",
        "finally",
        "float",
        "for",
        "goto",
        "if",
        "implements",
        "import",
        "instanceof",
        "int",
        "interface",
        "long",
        "native",
        "new",
        "package",
        "private",
        "protected",
        "public",
        "return",
        "short",
        "static",
        "strictfp",
        "super",
        "switch",
        "synchronized",
        "this",
        "throw",
        "throws",
        "transient",
        "try",
        "void",
        "volatile",
        "while",
        "true",
        "false",
        "null",
    }
)

JAVA_CONTEXTUAL_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "var",
        "record",
        "sealed",
        "permits",
        "yield",
        "non-sealed",
        "to",
        "with",
        "open",
        "opens",
        "provides",
        "uses",
        "module",
        "requires",
        "exports",
        "transitive",
    }
)

ALL_JAVA_KEYWORDS: Final[frozenset[str]] = JAVA_STANDARD_KEYWORDS | JAVA_CONTEXTUAL_KEYWORDS

OPERATORS_4: Final[tuple[str, ...]] = (">>>=",)
OPERATORS_3: Final[tuple[str, ...]] = (">>>", "<<=", ">>=", "...")
OPERATORS_2: Final[tuple[str, ...]] = (
    "==",
    "!=",
    "<=",
    ">=",
    "&&",
    "||",
    "++",
    "--",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "&=",
    "|=",
    "^=",
    "<<",
    ">>",
    "->",
    "::",
)
OPERATORS_1: Final[frozenset[str]] = frozenset(
    {
        "=",
        "+",
        "-",
        "*",
        "/",
        "%",
        "<",
        ">",
        "!",
        "~",
        "&",
        "|",
        "^",
        "?",
        ":",
        ".",
        ",",
        ";",
        "(",
        ")",
        "{",
        "}",
        "[",
        "]",
    }
)

BIDI_AND_CONTROL_CODEPOINTS: Final[frozenset[int]] = frozenset(
    {
        0x202A,  # LRE
        0x202B,  # RLE
        0x202C,  # PDF
        0x202D,  # LRO
        0x202E,  # RLO
        0x2066,  # LRI
        0x2067,  # RLI
        0x2068,  # FSI
        0x2069,  # PDI
        0x200E,  # LRM
        0x200F,  # RLM
        0x061C,  # ALM
        0x200B,  # ZWSP
        0x200C,  # ZWNJ
        0x200D,  # ZWJ
        0x2060,  # WJ
        0xFEFF,  # BOM / ZWNBSP
    }
)


class JavaLexer(LexerBase):
    """Hand-written, zero-crash, Unicode-aware state machine lexer for Java.

    Guarantees:
      - Never raises exceptions; unrecognized characters become ERROR tokens.
      - Lossless trivia preservation: "".join(t.text for t in tokens) == source.
      - Exact UTF-16 code unit offset synchronization.
      - Full Java 21 support: keywords, contextual keywords, annotations,
        text blocks, numeric literals with underscores, unicode escapes, etc.
    """

    def __init__(self, source: str, offset_map: OffsetMap | None = None) -> None:
        super().__init__(source, offset_map)
        self.unicode_escape_findings: list[dict[str, int | str]] = []

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

            # 2. Comments (Line // or Block /* ... */)
            if ch == "/" and self.peek(1) in ("/", "*"):
                self._lex_comment(tokens)
                continue

            # 3. Annotations (@Name or @Name(...))
            if ch == "@":
                self._lex_annotation(tokens)
                continue

            # 4. Strings: Text Blocks (""") or regular strings ("...")
            if ch == '"':
                if self.peek_slice(3) == '"""':
                    self._lex_text_block(tokens)
                else:
                    self._lex_string(tokens)
                continue

            # 5. Character literals ('...')
            if ch == "'":
                self._lex_char(tokens)
                continue

            # 6. Numbers (decimal, hex, binary, octal, floats)
            if ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self._lex_number(tokens)
                continue

            # 7. Unicode escapes that might start an identifier or keyword (\uXXXX)
            if ch == "\\" and self.peek(1) == "u":
                self._lex_unicode_escape_token(tokens)
                continue

            # 8. Identifiers and Keywords
            if self._is_java_identifier_start(ch):
                self._lex_identifier(tokens)
                continue

            # 9. Operators and Punctuation (longest match first)
            if self._lex_operator(tokens):
                continue

            # 10. Fallback: single character ERROR token
            self.advance()
            tokens.append(self.make_token("ERROR", start_pos, self.cursor))

        return tokens

    # ── Sub-Lexer Methods ────────────────────────────────────────────────────────

    def _lex_whitespace(self, tokens: list[Token]) -> None:
        start_pos = self.cursor
        while not self.is_eof and self.peek().isspace():
            self.advance()
        tokens.append(self.make_token("WHITESPACE", start_pos, self.cursor))

    def _lex_comment(self, tokens: list[Token]) -> None:
        start_pos = self.cursor
        if self.peek_slice(2) == "//":
            self.advance_by(2)
            while not self.is_eof and self.peek() not in ("\r", "\n"):
                self._check_unicode_escape_in_comment(self.cursor)
                self.advance()
            tokens.append(self.make_token("COMMENT", start_pos, self.cursor))
        elif self.peek_slice(2) == "/*":
            self.advance_by(2)
            while not self.is_eof:
                self._check_unicode_escape_in_comment(self.cursor)
                if self.peek_slice(2) == "*/":
                    self.advance_by(2)
                    break
                self.advance()
            tokens.append(self.make_token("COMMENT", start_pos, self.cursor))

    def _check_unicode_escape_in_comment(self, pos: int) -> None:
        """Inspect if current cursor in comment starts a dangerous \\uXXXX escape."""
        if pos + 5 < self.length and self.source[pos] == "\\" and self.source[pos + 1] == "u":
            idx = pos + 2
            while idx < self.length and self.source[idx] == "u":
                idx += 1
            if idx + 4 <= self.length:
                hex_str = self.source[idx : idx + 4]
                try:
                    cp = int(hex_str, 16)
                    if cp in BIDI_AND_CONTROL_CODEPOINTS or unicodedata.category(
                        chr(cp)
                    ).startswith("C"):
                        self.unicode_escape_findings.append(
                            {
                                "offset": pos,
                                "codepoint": cp,
                                "hex": hex_str,
                            }
                        )
                except ValueError:
                    pass

    def _lex_annotation(self, tokens: list[Token]) -> None:
        """Lex an annotation like @Override or @RequestMapping(value = "/api")."""
        start_pos = self.cursor
        self.advance()  # consume '@'

        # Consume identifier after @
        while not self.is_eof and (self.peek().isspace() or self.peek() == "\\"):
            if self.peek().isspace():
                break
            if self.peek_slice(2) == "\\u":
                self.advance_by(2)
                while not self.is_eof and self.peek() == "u":
                    self.advance()
                self.advance_by(4)
            else:
                break

        if not self.is_eof and self._is_java_identifier_start(self.peek()):
            while not self.is_eof and (
                self._is_java_identifier_part(self.peek()) or self.peek() == "."
            ):
                self.advance()

        # Optional arguments: @Annotation(...)
        if not self.is_eof and self.peek() == "(":
            depth = 1
            self.advance()  # consume '('
            in_str = False
            str_quote = ""
            while not self.is_eof and depth > 0:
                cur = self.peek()
                if in_str:
                    if cur == "\\":
                        self.advance_by(2)
                        continue
                    if cur == str_quote:
                        in_str = False
                    self.advance()
                    continue

                if cur in ('"', "'"):
                    in_str = True
                    str_quote = cur
                    self.advance()
                    continue

                if cur == "(":
                    depth += 1
                elif cur == ")":
                    depth -= 1
                elif cur in ("\n", "\r") and depth > 0:
                    # Unterminated annotation across too many lines safety
                    pass
                self.advance()

        tokens.append(self.make_token("ANNOTATION", start_pos, self.cursor))

    def _lex_text_block(self, tokens: list[Token]) -> None:
        """Lex Java 15+ text block: \"\"\" ... \"\"\"."""
        start_pos = self.cursor
        self.advance_by(3)  # consume initial '"""'

        while not self.is_eof:
            if self.peek() == "\\":
                self.advance_by(2)
                continue
            if self.peek_slice(3) == '"""':
                self.advance_by(3)
                tokens.append(self.make_token("STRING", start_pos, self.cursor))
                return
            self.advance()

        # Unterminated text block: emit ERROR token
        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_string(self, tokens: list[Token]) -> None:
        """Lex regular double-quoted string literal."""
        start_pos = self.cursor
        self.advance()  # consume initial '"'

        while not self.is_eof:
            ch = self.peek()
            if ch == "\\":
                self.advance_by(2)
                continue
            if ch == '"':
                self.advance()  # consume closing '"'
                tokens.append(self.make_token("STRING", start_pos, self.cursor))
                return
            if ch in ("\r", "\n"):
                # Java regular strings cannot span newlines unescaped
                break
            self.advance()

        # Unterminated string
        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_char(self, tokens: list[Token]) -> None:
        """Lex single-quoted character literal ('...')."""
        start_pos = self.cursor
        self.advance()  # consume initial "'"

        while not self.is_eof:
            ch = self.peek()
            if ch == "\\":
                self.advance_by(2)
                continue
            if ch == "'":
                self.advance()  # consume closing "'"
                tokens.append(self.make_token("CHAR", start_pos, self.cursor))
                return
            if ch in ("\r", "\n"):
                break
            self.advance()

        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_number(self, tokens: list[Token]) -> None:
        """Lex integer, hex, binary, octal, or floating-point literal."""
        start_pos = self.cursor

        # Hex or Binary
        if self.peek() == "0" and self.peek(1).lower() in ("x", "b"):
            is_hex = self.peek(1).lower() == "x"
            self.advance_by(2)
            valid_chars = "0123456789abcdefABCDEF_" if is_hex else "01_"
            while not self.is_eof and self.peek() in valid_chars:
                self.advance()

            # Hex float: 0x1.0p-3
            if is_hex and self.peek() == ".":
                self.advance()
                while not self.is_eof and self.peek() in "0123456789abcdefABCDEF_":
                    self.advance()
            if is_hex and self.peek().lower() == "p":
                self.advance()
                if not self.is_eof and self.peek() in ("+", "-"):
                    self.advance()
                while not self.is_eof and (self.peek().isdigit() or self.peek() == "_"):
                    self.advance()

            # Suffixes L, f, d
            if not self.is_eof and self.peek().lower() in ("l", "f", "d"):
                self.advance()

            tokens.append(self.make_token("NUMBER", start_pos, self.cursor))
            return

        # Decimal / Octal / Float
        while not self.is_eof and (self.peek().isdigit() or self.peek() == "_"):
            self.advance()

        # Fractional part
        if not self.is_eof and self.peek() == "." and self.peek(1) != ".":
            self.advance()
            while not self.is_eof and (self.peek().isdigit() or self.peek() == "_"):
                self.advance()

        # Exponent part
        if not self.is_eof and self.peek().lower() == "e":
            self.advance()
            if not self.is_eof and self.peek() in ("+", "-"):
                self.advance()
            while not self.is_eof and (self.peek().isdigit() or self.peek() == "_"):
                self.advance()

        # Suffixes L, l, f, F, d, D
        if not self.is_eof and self.peek().lower() in ("l", "f", "d"):
            self.advance()

        tokens.append(self.make_token("NUMBER", start_pos, self.cursor))

    def _lex_unicode_escape_token(self, tokens: list[Token]) -> None:
        """Handle \\uXXXX at top level and continue into identifier if applicable."""
        start_pos = self.cursor
        self.advance_by(2)  # consume '\\u'
        while not self.is_eof and self.peek() == "u":
            self.advance()
        hex_digits = self.advance_by(4)
        try:
            cp = int(hex_digits, 16)
            if cp in BIDI_AND_CONTROL_CODEPOINTS or unicodedata.category(chr(cp)).startswith("C"):
                self.unicode_escape_findings.append(
                    {
                        "offset": start_pos,
                        "codepoint": cp,
                        "hex": hex_digits,
                    }
                )
            decoded_char = chr(cp)
            if self._is_java_identifier_start(decoded_char):
                # Continue reading identifier
                while not self.is_eof and self._is_java_identifier_part(self.peek()):
                    self.advance()
                tokens.append(self.make_token("IDENTIFIER", start_pos, self.cursor))
                return
        except ValueError:
            pass

        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_identifier(self, tokens: list[Token]) -> None:
        """Lex Java identifier or keyword."""
        start_pos = self.cursor
        while not self.is_eof and self._is_java_identifier_part(self.peek()):
            self.advance()

        text = self.source[start_pos : self.cursor]
        kind = "KEYWORD" if text in ALL_JAVA_KEYWORDS else "IDENTIFIER"
        tokens.append(self.make_token(kind, start_pos, self.cursor))

    def _lex_operator(self, tokens: list[Token]) -> bool:
        """Attempt to match 4, 3, 2, or 1 character operators."""
        start_pos = self.cursor

        # 4-char
        for op in OPERATORS_4:
            if self.peek_slice(4) == op:
                self.advance_by(4)
                tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
                return True

        # 3-char
        for op in OPERATORS_3:
            if self.peek_slice(3) == op:
                self.advance_by(3)
                tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
                return True

        # 2-char
        for op in OPERATORS_2:
            if self.peek_slice(2) == op:
                self.advance_by(2)
                tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
                return True

        # 1-char
        ch = self.peek()
        if ch in OPERATORS_1:
            self.advance()
            kind = (
                "OPERATOR"
                if ch not in ("(", ")", "{", "}", "[", "]", ";", ",", ".")
                else "PUNCTUATION"
            )
            tokens.append(self.make_token(kind, start_pos, self.cursor))
            return True

        return False

    @staticmethod
    def _is_java_identifier_start(ch: str) -> bool:
        """Check if character can begin a Java identifier (JLS §3.8)."""
        if ch in ("_", "$"):
            return True
        if "a" <= ch <= "z" or "A" <= ch <= "Z":
            return True
        cat = unicodedata.category(ch)
        return cat in ("Lu", "Ll", "Lt", "Lm", "Lo", "Nl")

    @staticmethod
    def _is_java_identifier_part(ch: str) -> bool:
        """Check if character can continue a Java identifier (JLS §3.8)."""
        if ch in ("_", "$"):
            return True
        if "a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9":
            return True
        cat = unicodedata.category(ch)
        return cat in ("Lu", "Ll", "Lt", "Lm", "Lo", "Nl", "Nd", "Mc", "Mn", "Pc", "Cf")
