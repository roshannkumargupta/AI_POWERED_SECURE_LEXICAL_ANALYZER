"""Hand-written, zero-crash, Unicode-aware lexical analyzer for Python."""

from __future__ import annotations

import unicodedata
from typing import Final

from apsla.lexing.base import LexerBase
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Range

PYTHON_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    }
)

# Operators ordered by descending length so multi-character operators match first
OPERATORS_3: Final[tuple[str, ...]] = ("**=", "//=", "<<=", ">>=", "...")
OPERATORS_2: Final[tuple[str, ...]] = (
    ":=",
    "->",
    "**",
    "//",
    "<<",
    ">>",
    "<=",
    ">=",
    "==",
    "!=",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "&=",
    "|=",
    "^=",
    "@=",
)
OPERATORS_1: Final[frozenset[str]] = frozenset(
    {
        "+",
        "-",
        "*",
        "/",
        "%",
        "@",
        "&",
        "|",
        "^",
        "~",
        "<",
        ">",
        "=",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        ",",
        ":",
        ".",
        ";",
    }
)

STRING_PREFIXES_2: Final[frozenset[str]] = frozenset(
    {
        "rf",
        "fr",
        "rb",
        "br",
    }
)
STRING_PREFIXES_1: Final[frozenset[str]] = frozenset({"r", "u", "b", "f"})


def is_python_ident_start(ch: str) -> bool:
    """Check if character can start a Python identifier (Unicode PEP 3131)."""
    if not ch:
        return False
    if "a" <= ch <= "z" or "A" <= ch <= "Z" or ch == "_":
        return True
    if ord(ch) < 128:
        return False
    cat = unicodedata.category(ch)
    return cat in ("Lu", "Ll", "Lt", "Lm", "Lo", "Nl")


def is_python_ident_continue(ch: str) -> bool:
    """Check if character can continue a Python identifier (Unicode PEP 3131)."""
    if not ch:
        return False
    if "a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9" or ch == "_":
        return True
    if ord(ch) < 128:
        return False
    cat = unicodedata.category(ch)
    return cat in ("Lu", "Ll", "Lt", "Lm", "Lo", "Nl", "Mn", "Mc", "Nd", "Pc")


class PythonLexer(LexerBase):
    """Hand-written state-machine lexer for Python source code.

    Invariants:
      1. Never raises exceptions: malformed syntax is captured as ERROR tokens.
      2. Full trivia preservation: "".join(t.text for t in tokens) == source exactly.
      3. UTF-16 code unit offset and coordinate tracking on all tokens.
      4. f-strings emitted as ONE STRING token with embedded expression Ranges in 'parts'.
    """

    def __init__(self, source: str, offset_map: OffsetMap | None = None) -> None:
        super().__init__(source, offset_map)
        self.paren_depth = 0
        self.indent_stack: list[int] = [0]
        self.at_line_start = True

    def tokenize(self) -> list[Token]:
        """Execute full tokenization over input source."""
        tokens: list[Token] = []

        while not self.is_eof:
            # Handle indentation check at the start of a logical line
            if self.at_line_start and self.paren_depth == 0:
                indent_tokens = self._handle_indentation()
                if indent_tokens:
                    tokens.extend(indent_tokens)
                    if self.is_eof:
                        break

            start_pos = self.cursor
            ch = self.peek()

            # 1. Newlines
            if ch in ("\r", "\n"):
                tokens.append(self._lex_newline())
                continue

            # 2. Whitespace (spaces and tabs)
            if ch in (" ", "\t"):
                tokens.append(self._lex_whitespace())
                continue

            # 3. Line continuation: backslash followed by newline
            if ch == "\\" and self.peek(1) in ("\r", "\n"):
                start_p = self.cursor
                self.advance()  # consume \
                if self.peek() == "\r" and self.peek(1) == "\n":
                    self.advance_by(2)
                else:
                    self.advance()
                tokens.append(self.make_token("WHITESPACE", start_p, self.cursor))
                continue

            # 4. Comments
            if ch == "#":
                tokens.append(self._lex_comment())
                continue

            # 5. String literals (with optional prefixes r, u, b, f, etc.)
            string_token = self._try_lex_string()
            if string_token is not None:
                tokens.append(string_token)
                continue

            # 6. Numbers
            if ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                tokens.append(self._lex_number())
                continue

            # 7. Identifiers and Keywords
            if is_python_ident_start(ch):
                tokens.append(self._lex_identifier_or_keyword())
                continue

            # 8. Multi-character operators
            op3 = self.peek_slice(3)
            if op3 in OPERATORS_3:
                self.advance_by(3)
                tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
                continue

            op2 = self.peek_slice(2)
            if op2 in OPERATORS_2:
                self.advance_by(2)
                tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
                continue

            # 9. Single-character operators & delimiters
            if ch in OPERATORS_1:
                self.advance()
                if ch in ("(", "[", "{"):
                    self.paren_depth += 1
                elif ch in (")", "]", "}"):
                    self.paren_depth = max(0, self.paren_depth - 1)
                tokens.append(self.make_token("OPERATOR", start_pos, self.cursor))
                continue

            # 10. Fallback: unrecognized character -> emit ERROR token without crashing
            self.advance()
            tokens.append(self.make_token("ERROR", start_pos, self.cursor))

        # At EOF: close remaining indentation levels
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(self.make_token("DEDENT", self.length, self.length, text=""))

        return tokens

    def _handle_indentation(self) -> list[Token]:
        """Check and update indentation level at line start.

        Returns list of INDENT / DEDENT / WHITESPACE tokens.
        """
        start_p = self.cursor

        # Peek ahead to see how many spaces/tabs exist
        p = self.cursor
        col = 0
        while p < self.length and self.source[p] in (" ", "\t"):
            if self.source[p] == " ":
                col += 1
            elif self.source[p] == "\t":
                col = (col // 8 + 1) * 8
            p += 1

        # Check if the line is blank or only a comment
        if p >= self.length or self.source[p] in ("\r", "\n", "#"):
            # Do not change indentation on blank or comment-only lines
            return []

        # Advance cursor past leading indentation spaces
        indent_text = self.source[start_p:p]
        self.cursor = p
        self.at_line_start = False

        tokens: list[Token] = []
        current_level = self.indent_stack[-1]

        if col > current_level:
            self.indent_stack.append(col)
            tokens.append(self.make_token("INDENT", start_p, self.cursor, text=indent_text))
        elif col < current_level:
            # Emit one or more DEDENTs
            first = True
            while len(self.indent_stack) > 1 and col < self.indent_stack[-1]:
                self.indent_stack.pop()
                # Only the first DEDENT or a preceding WHITESPACE holds the text
                t_text = indent_text if first else ""
                tokens.append(self.make_token("DEDENT", start_p, self.cursor, text=t_text))
                first = False

            if col != self.indent_stack[-1]:
                # Inconsistent dedent
                tokens.append(self.make_token("ERROR", start_p, self.cursor, text=""))
        else:
            # Same indentation level: emit plain WHITESPACE if any spaces were consumed
            if indent_text:
                tokens.append(self.make_token("WHITESPACE", start_p, self.cursor, text=indent_text))

        return tokens

    def _lex_newline(self) -> Token:
        """Lex a CRLF, LF, or CR newline."""
        start_p = self.cursor
        if self.peek() == "\r" and self.peek(1) == "\n":
            self.advance_by(2)
        else:
            self.advance()

        if self.paren_depth == 0:
            self.at_line_start = True
            return self.make_token("NEWLINE", start_p, self.cursor)
        return self.make_token("WHITESPACE", start_p, self.cursor)

    def _lex_whitespace(self) -> Token:
        """Consume consecutive spaces and tabs."""
        start_p = self.cursor
        while not self.is_eof and self.peek() in (" ", "\t"):
            self.advance()
        return self.make_token("WHITESPACE", start_p, self.cursor)

    def _lex_comment(self) -> Token:
        """Consume comment until newline or EOF."""
        start_p = self.cursor
        while not self.is_eof and self.peek() not in ("\r", "\n"):
            self.advance()
        return self.make_token("COMMENT", start_p, self.cursor)

    def _try_lex_string(self) -> Token | None:
        """Attempt to lex a string literal with optional prefixes and quote styles."""
        start_p = self.cursor
        prefix_len = 0
        is_fstring = False

        # Check 2-character prefixes (rf, fr, rb, br)
        two_chars = self.peek_slice(2).lower()
        if two_chars in STRING_PREFIXES_2:
            next_ch = self.peek(2)
            if next_ch in ("'", '"'):
                prefix_len = 2
                is_fstring = "f" in two_chars

        # Check 1-character prefixes (r, u, b, f)
        if prefix_len == 0:
            one_char = self.peek(0).lower()
            if one_char in STRING_PREFIXES_1:
                next_ch = self.peek(1)
                if next_ch in ("'", '"'):
                    prefix_len = 1
                    is_fstring = one_char == "f"

        # Check raw quote without prefix
        if prefix_len == 0 and self.peek(0) not in ("'", '"'):
            return None

        quote_start = start_p + prefix_len
        quote_char = self.source[quote_start]

        # Check if triple quote
        if (
            quote_start + 2 < self.length
            and self.source[quote_start + 1] == quote_char
            and self.source[quote_start + 2] == quote_char
        ):
            quote_delim = quote_char * 3
        else:
            quote_delim = quote_char

        delim_len = len(quote_delim)
        self.cursor = quote_start + delim_len

        # Now scan string body
        parts: list[Range] = []

        if is_fstring:
            parts = self._scan_fstring_body(quote_delim)
        else:
            self._scan_standard_string_body(quote_delim)

        return self.make_token("STRING", start_p, self.cursor, parts=parts)

    def _scan_standard_string_body(self, quote_delim: str) -> None:
        """Scan standard non-fstring body until matching delimiter or EOF."""
        is_triple = len(quote_delim) == 3

        while not self.is_eof:
            if self.match(quote_delim):
                return

            ch = self.peek()

            # Escaped character
            if ch == "\\":
                self.advance()
                if not self.is_eof:
                    self.advance()
                continue

            # Non-triple-quoted strings cannot span newlines unless escaped
            if not is_triple and ch in ("\r", "\n"):
                return

            self.advance()

    def _scan_fstring_body(self, quote_delim: str) -> list[Range]:
        """Scan f-string body and extract embedded expression ranges."""
        is_triple = len(quote_delim) == 3
        parts: list[Range] = []

        while not self.is_eof:
            if self.match(quote_delim):
                return parts

            ch = self.peek()

            # Escaped braces: {{ or }}
            if ch == "{" and self.peek(1) == "{":
                self.advance_by(2)
                continue
            if ch == "}" and self.peek(1) == "}":
                self.advance_by(2)
                continue

            # Embedded expression start: {
            if ch == "{":
                self.advance()  # consume {
                expr_start = self.cursor
                self._scan_fstring_expression(quote_delim)
                expr_end = self.cursor
                if self.peek() == "}":
                    self.advance()  # consume }
                elif self.peek_slice(len(quote_delim)) == quote_delim:
                    # Unterminated expression before end of string
                    pass

                # Record the range of the embedded expression
                if expr_end > expr_start:
                    parts.append(self.offset_map.span_to_range(expr_start, expr_end))
                continue

            # Escaped character
            if ch == "\\":
                self.advance()
                if not self.is_eof:
                    self.advance()
                continue

            if not is_triple and ch in ("\r", "\n"):
                return parts

            self.advance()

        return parts

    def _scan_fstring_expression(self, outer_delim: str) -> None:
        """Scan inside an f-string embedded expression { ... } until matching closing brace."""
        brace_depth = 1
        paren_depth = 0

        while not self.is_eof and brace_depth > 0:
            ch = self.peek()

            # Stop if outer quote closing delimiter is met
            if self.peek_slice(len(outer_delim)) == outer_delim:
                return

            # Nested quotes inside expression
            if ch in ("'", '"'):
                # Nested string inside expression
                q = ch
                if self.peek_slice(3) in ("'''", '"""'):
                    q = self.peek_slice(3)
                self.advance_by(len(q))
                while not self.is_eof and not self.match(q):
                    if self.peek() == "\\":
                        self.advance_by(2)
                    else:
                        self.advance()
                continue

            if ch in ("(", "["):
                paren_depth += 1
                self.advance()
                continue
            if ch in (")", "]"):
                paren_depth = max(0, paren_depth - 1)
                self.advance()
                continue

            if ch == "{" and paren_depth == 0:
                brace_depth += 1
                self.advance()
                continue

            if ch == "}" and paren_depth == 0:
                brace_depth -= 1
                if brace_depth == 0:
                    # Do not advance here; caller consumes closing }
                    return
                self.advance()
                continue

            self.advance()

    def _lex_number(self) -> Token:
        """Lex integer, float, binary, hex, octal, exponent, or complex number."""
        start_p = self.cursor

        # 1. Hex, Binary, Octal: 0x..., 0b..., 0o...
        if self.peek() == "0" and self.peek(1).lower() in ("x", "b", "o"):
            self.advance_by(2)
            while not self.is_eof and (self.peek().isalnum() or self.peek() == "_"):
                self.advance()
            return self.make_token("NUMBER", start_p, self.cursor)

        # 2. Decimal digits with underscores
        has_digits = False
        while not self.is_eof and (self.peek().isdigit() or self.peek() == "_"):
            self.advance()
            has_digits = True

        # Decimal point: e.g. 123.456 or .456
        if (
            self.peek() == "."
            and (self.peek(1).isdigit() or has_digits)
            and self.peek_slice(3) != "..."
        ):
            self.advance()  # consume .
            while not self.is_eof and (self.peek().isdigit() or self.peek() == "_"):
                self.advance()

        # Exponent: e.g. 1e10, 2.5E-3
        if self.peek().lower() == "e":
            self.advance()  # consume e
            if self.peek() in ("+", "-"):
                self.advance()
            while not self.is_eof and (self.peek().isdigit() or self.peek() == "_"):
                self.advance()

        # Complex / imaginary suffix: j or J
        if self.peek().lower() == "j":
            self.advance()

        return self.make_token("NUMBER", start_p, self.cursor)

    def _lex_identifier_or_keyword(self) -> Token:
        """Lex a Python keyword or Unicode identifier."""
        start_p = self.cursor
        while not self.is_eof and is_python_ident_continue(self.peek()):
            self.advance()

        text = self.source[start_p : self.cursor]
        kind = "KEYWORD" if text in PYTHON_KEYWORDS else "IDENTIFIER"
        return self.make_token(kind, start_p, self.cursor, text=text)
