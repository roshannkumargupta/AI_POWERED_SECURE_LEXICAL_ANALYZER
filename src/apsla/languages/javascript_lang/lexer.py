"""Hand-written, zero-crash, Unicode-aware lexical analyzer for JavaScript.

Supports:
  - Keywords (including contextual: async, await, of, get, set, static, let)
  - Identifiers with $, _, and Unicode (XID_Start, XID_Continue)
  - Numbers: hex (0x), octal (0o/traditional), binary (0b), BigInt (10n),
    numeric separators (1_000), exponents (1e5, 1.5e-3), decimals (.5)
  - Strings with escapes (single and double quoted)
  - Template literals with nested ${...} to arbitrary depth (mode stack)
  - Regex literals vs division disambiguation by previous significant token
  - Operators: ?. ?? ??= ||= &&= **= => ... >>>= </ and all standard operators
  - Comments: //, /* */, and HTML-style <!-- and --> line comments
  - Shebang line (#!/usr/bin/env node) on line 1
  - JSX syntax tolerated without ERROR tokens (tokenized as operators, identifiers, strings)
"""

from __future__ import annotations

import unicodedata
from typing import Final

from apsla.lexing.base import LexerBase
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token

# ── Keyword sets ──────────────────────────────────────────────────────────────

JS_STANDARD_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "else",
        "export",
        "extends",
        "finally",
        "for",
        "function",
        "if",
        "import",
        "in",
        "instanceof",
        "new",
        "return",
        "super",
        "switch",
        "this",
        "throw",
        "try",
        "typeof",
        "var",
        "void",
        "while",
        "with",
        "yield",
        "true",
        "false",
        "null",
        "undefined",
        "enum",
    }
)

JS_CONTEXTUAL_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "async",
        "await",
        "of",
        "get",
        "set",
        "static",
        "let",
        "from",
        "as",
        "implements",
        "interface",
        "package",
        "private",
        "protected",
        "public",
        "target",
        "meta",
    }
)

ALL_JS_KEYWORDS: Final[frozenset[str]] = JS_STANDARD_KEYWORDS | JS_CONTEXTUAL_KEYWORDS

# Value keywords acting like expressions / operands before division
_JS_VALUE_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "this",
        "super",
        "true",
        "false",
        "null",
        "undefined",
    }
)

# Keywords after which an expression can begin -> '/' is a REGEX
_REGEX_PREV_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "return",
        "typeof",
        "delete",
        "void",
        "throw",
        "new",
        "in",
        "instanceof",
        "case",
        "yield",
        "await",
        "else",
        "do",
        "default",
    }
)

# Punctuation / delimiters after which '/' is a REGEX
_REGEX_PREV_DELIMS: Final[frozenset[str]] = frozenset(
    {
        "(",
        ",",
        "=",
        ":",
        "[",
        "!",
        "&",
        "|",
        "?",
        "{",
        "}",
        ";",
    }
)

# ── Operators (longest match first) ──────────────────────────────────────────

OPERATORS_4: Final[tuple[str, ...]] = (">>>=",)
OPERATORS_3: Final[tuple[str, ...]] = (
    ">>>",
    "<<=",
    ">>=",
    "===",
    "!==",
    "**=",
    "||=",
    "&&=",
    "??=",
    "...",
)
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
    "**",
    "=>",
    "?.",
    "??",
    "</",  # JSX closing tag open
    "/>",  # JSX self-closing tag
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

# ── Lexer mode enum ──────────────────────────────────────────────────────────

_MODE_NORMAL = 0
_MODE_TEMPLATE = 1  # inside template literal scanning for ` or ${
_MODE_TEMPLATE_EXPR = 2  # inside ${...} expression within template literal


class JavaScriptLexer(LexerBase):
    """Hand-written, zero-crash, Unicode-aware state machine lexer for JavaScript.

    Guarantees:
      - Never raises exceptions; unrecognized characters become ERROR tokens.
      - Lossless trivia preservation: "".join(t.text for t in tokens) == source.
      - Exact UTF-16 code unit offset synchronization.
      - Full ES2024 support: keywords, contextual keywords, template literals
        with arbitrary nesting, regex vs division disambiguation, BigInt, JSX.
    """

    def __init__(self, source: str, offset_map: OffsetMap | None = None) -> None:
        super().__init__(source, offset_map)
        # Mode stack for template literal nesting
        self._mode_stack: list[int] = [_MODE_NORMAL]
        # Brace depth tracking per template expression
        self._template_brace_depth: list[int] = []

    @property
    def _mode(self) -> int:
        return self._mode_stack[-1] if self._mode_stack else _MODE_NORMAL

    def tokenize(self) -> list[Token]:
        """Perform full lexical analysis, returning complete token sequence."""
        tokens: list[Token] = []

        # Handle shebang line (#!/usr/bin/env node) on line 1
        if self.source.startswith("#!"):
            self._lex_shebang(tokens)

        while not self.is_eof:
            start_pos = self.cursor
            ch = self.peek()

            # In template literal body mode, scan for ` or ${
            if self._mode == _MODE_TEMPLATE:
                self._lex_template_body(tokens)
                continue

            # Whitespace
            if ch.isspace():
                self._lex_whitespace(tokens)
                continue

            # Comments (// or /* */ or <!-- or -->)
            if ch == "/" and self.peek(1) in ("/", "*"):
                self._lex_comment(tokens)
                continue
            if ch == "<" and self.peek_slice(4) == "<!--":
                self._lex_html_comment(tokens)
                continue
            if ch == "-" and self.peek_slice(3) == "-->":
                self._lex_html_comment(tokens)
                continue

            # Decorator / annotation (@Name)
            if ch == "@":
                self._lex_annotation(tokens)
                continue

            # Template literal start
            if ch == "`":
                self._lex_template_start(tokens)
                continue

            # String literals (single or double quoted)
            if ch in ('"', "'"):
                self._lex_string(tokens)
                continue

            # Numbers: digits or leading decimal dot (.5)
            if ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self._lex_number(tokens)
                continue

            # Identifiers, keywords, and private identifiers (#field)
            if self._is_js_identifier_start(ch) or (
                ch == "#" and self._is_js_identifier_start(self.peek(1))
            ):
                self._lex_identifier(tokens)
                continue

            # Regex vs division: '/' that isn't '//' or '/*'
            if ch == "/":
                if self.peek(1) == ">":
                    # JSX self-closing tag '/>'
                    self._lex_operator(tokens)
                elif self._should_lex_regex(tokens):
                    self._lex_regex(tokens)
                else:
                    # Division operator or compound /=
                    self._lex_operator(tokens)
                continue

            # Closing brace may end a template expression
            if ch == "}" and self._mode == _MODE_TEMPLATE_EXPR:
                self._template_brace_depth[-1] -= 1
                if self._template_brace_depth[-1] < 0:
                    # Exiting template expression -> return to template body
                    self.advance()
                    tokens.append(self.make_token("TEMPLATE", start_pos, self.cursor))
                    self._template_brace_depth.pop()
                    self._mode_stack.pop()
                    continue

            # Opening brace inside template expression increases depth
            if ch == "{" and self._mode == _MODE_TEMPLATE_EXPR:
                self._template_brace_depth[-1] += 1

            # Operators and punctuation (longest match first)
            if self._lex_operator(tokens):
                continue

            # Fallback: single character ERROR token
            self.advance()
            tokens.append(self.make_token("ERROR", start_pos, self.cursor))

        return tokens

    # ── Sub-Lexer Methods ────────────────────────────────────────────────────

    def _lex_shebang(self, tokens: list[Token]) -> None:
        """Lex #!/usr/bin/env node shebang line."""
        start_pos = self.cursor
        while not self.is_eof and self.peek() not in ("\r", "\n"):
            self.advance()
        tokens.append(self.make_token("COMMENT", start_pos, self.cursor))

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
                self.advance()
            tokens.append(self.make_token("COMMENT", start_pos, self.cursor))
        elif self.peek_slice(2) == "/*":
            self.advance_by(2)
            while not self.is_eof:
                if self.peek_slice(2) == "*/":
                    self.advance_by(2)
                    break
                self.advance()
            tokens.append(self.make_token("COMMENT", start_pos, self.cursor))

    def _lex_html_comment(self, tokens: list[Token]) -> None:
        """Lex <!-- or --> as a line comment (HTML-style, standard in JS)."""
        start_pos = self.cursor
        if self.peek_slice(4) == "<!--":
            self.advance_by(4)
        elif self.peek_slice(3) == "-->":
            self.advance_by(3)
        while not self.is_eof and self.peek() not in ("\r", "\n"):
            self.advance()
        tokens.append(self.make_token("COMMENT", start_pos, self.cursor))

    def _lex_annotation(self, tokens: list[Token]) -> None:
        """Lex a decorator/annotation like @decorator."""
        start_pos = self.cursor
        self.advance()  # consume '@'

        if not self.is_eof and self._is_js_identifier_start(self.peek()):
            while not self.is_eof and (
                self._is_js_identifier_part(self.peek()) or self.peek() == "."
            ):
                self.advance()

        # Optional arguments: @decorator(...)
        if not self.is_eof and self.peek() == "(":
            depth = 1
            self.advance()
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
                if cur in ('"', "'", "`"):
                    in_str = True
                    str_quote = cur
                    self.advance()
                    continue
                if cur == "(":
                    depth += 1
                elif cur == ")":
                    depth -= 1
                self.advance()

        tokens.append(self.make_token("ANNOTATION", start_pos, self.cursor))

    def _lex_template_start(self, tokens: list[Token]) -> None:
        """Start lexing a template literal after encountering an opening backtick."""
        start_pos = self.cursor
        self.advance()  # consume opening `
        tokens.append(self.make_token("TEMPLATE", start_pos, self.cursor))
        self._mode_stack.append(_MODE_TEMPLATE)

    def _lex_template_body(self, tokens: list[Token]) -> None:
        """Lex the body of a template literal, handling ${ and closing `."""
        start_pos = self.cursor

        while not self.is_eof:
            ch = self.peek()

            if ch == "\\":
                # Escape sequence in template literal
                self.advance_by(2)
                continue

            if ch == "$" and self.peek(1) == "{":
                # Emit accumulated template body text
                if self.cursor > start_pos:
                    tokens.append(self.make_token("TEMPLATE", start_pos, self.cursor))
                # Emit ${ as TEMPLATE token
                expr_start = self.cursor
                self.advance_by(2)
                tokens.append(self.make_token("TEMPLATE", expr_start, self.cursor))
                # Enter expression mode
                self._mode_stack.append(_MODE_TEMPLATE_EXPR)
                self._template_brace_depth.append(0)
                return

            if ch == "`":
                # Emit accumulated template body text if any
                if self.cursor > start_pos:
                    tokens.append(self.make_token("TEMPLATE", start_pos, self.cursor))
                # Emit closing `
                tick_start = self.cursor
                self.advance()
                tokens.append(self.make_token("TEMPLATE", tick_start, self.cursor))
                self._mode_stack.pop()  # leave _MODE_TEMPLATE
                return

            self.advance()

        # Unterminated template literal
        if self.cursor > start_pos:
            tokens.append(self.make_token("ERROR", start_pos, self.cursor))
        if self._mode_stack and self._mode_stack[-1] == _MODE_TEMPLATE:
            self._mode_stack.pop()

    def _lex_string(self, tokens: list[Token]) -> None:
        """Lex single or double quoted string literal."""
        start_pos = self.cursor
        quote = self.peek()
        self.advance()  # consume opening quote

        while not self.is_eof:
            ch = self.peek()
            if ch == "\\":
                self.advance_by(2)
                continue
            if ch == quote:
                self.advance()
                tokens.append(self.make_token("STRING", start_pos, self.cursor))
                return
            if ch in ("\r", "\n"):
                # Standard JS strings cannot span unescaped newlines
                break
            self.advance()

        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_number(self, tokens: list[Token]) -> None:
        """Lex integer, hex, binary, octal, or float literal including BigInt and separators."""
        start_pos = self.cursor

        # Hex, Binary, Octal prefixes
        if self.peek() == "0" and self.peek(1).lower() in ("x", "b", "o"):
            prefix = self.peek(1).lower()
            self.advance_by(2)
            if prefix == "x":
                valid = "0123456789abcdefABCDEF_"
            elif prefix == "b":
                valid = "01_"
            else:  # octal (0o)
                valid = "01234567_"
            while not self.is_eof and self.peek() in valid:
                self.advance()
            # BigInt suffix
            if not self.is_eof and self.peek() == "n":
                self.advance()
            tokens.append(self.make_token("NUMBER", start_pos, self.cursor))
            return

        # Decimal / traditional octal / float
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

        # BigInt suffix
        if not self.is_eof and self.peek() == "n":
            self.advance()

        tokens.append(self.make_token("NUMBER", start_pos, self.cursor))

    def _should_lex_regex(self, tokens: list[Token]) -> bool:
        """Determine if '/' starts a regex literal based on previous significant token."""
        # Find last non-whitespace, non-comment token
        sig_idx = -1
        for i in range(len(tokens) - 1, -1, -1):
            tok = tokens[i]
            if tok.kind not in ("WHITESPACE", "COMMENT"):
                sig_idx = i
                break

        if sig_idx == -1:
            # Start of file -> regex is allowed
            return True

        tok = tokens[sig_idx]

        # After identifier, number, ), ] -> division
        if tok.kind in ("NUMBER", "STRING", "IDENTIFIER"):
            return False
        if tok.kind == "TEMPLATE":
            # After a completed template literal (`...`), '/' is division
            return False
        if tok.kind == "REGEX":
            # After a regex literal (/abc/), '/' is division
            return False
        if tok.text in (")", "]"):
            return False

        # Keyword values (this, super, true, false, null, undefined) act like operands -> division
        if tok.kind == "KEYWORD" and tok.text in _JS_VALUE_KEYWORDS:
            return False

        # Postfix ++ or -- after operand -> division (e.g. x++ / y)
        if tok.text in ("++", "--"):
            # Check what preceded ++ / --
            for j in range(sig_idx - 1, -1, -1):
                prev_tok = tokens[j]
                if prev_tok.kind not in ("WHITESPACE", "COMMENT"):
                    if prev_tok.kind in ("IDENTIFIER", "NUMBER") or prev_tok.text in (")", "]"):
                        return False
                    break

        # After return, typeof, and other expression keywords -> regex
        if tok.kind == "KEYWORD" and tok.text in _REGEX_PREV_KEYWORDS:
            return True

        # After delimiters: ( , = : [ ! & | ? { } ; -> regex
        if tok.text in _REGEX_PREV_DELIMS:
            return True

        # After any other operator -> regex (e.g. +, -, *, /, %, ==, ===, !=, !==, <, >, <=, >=, &&, ||, ??, =>, ...)
        if tok.kind == "OPERATOR":
            return True

        # Other keywords: by default assume regex if expression can follow
        if tok.kind == "KEYWORD":
            return True

        # Default fallback: regex
        return True

    def _lex_regex(self, tokens: list[Token]) -> None:
        """Lex a regular expression literal /pattern/flags."""
        start_pos = self.cursor
        self.advance()  # consume opening /

        in_class = False  # inside character class [...]
        while not self.is_eof:
            ch = self.peek()

            if ch == "\\":
                self.advance_by(2)
                continue

            if ch == "[":
                in_class = True
                self.advance()
                continue

            if ch == "]" and in_class:
                in_class = False
                self.advance()
                continue

            if ch == "/" and not in_class:
                self.advance()  # consume closing /
                # Consume flags (g, i, m, s, u, v, y, d)
                while not self.is_eof and self.peek().isalpha():
                    self.advance()
                tokens.append(self.make_token("REGEX", start_pos, self.cursor))
                return

            if ch in ("\r", "\n"):
                # Regex literals cannot span newlines
                break

            self.advance()

        # Unterminated regex
        tokens.append(self.make_token("ERROR", start_pos, self.cursor))

    def _lex_identifier(self, tokens: list[Token]) -> None:
        """Lex JavaScript identifier (including private #field) or keyword."""
        start_pos = self.cursor
        if self.peek() == "#":
            self.advance()
        while not self.is_eof and self._is_js_identifier_part(self.peek()):
            self.advance()

        text = self.source[start_pos : self.cursor]
        kind = "KEYWORD" if text in ALL_JS_KEYWORDS else "IDENTIFIER"
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
                if ch not in ("(", ")", "{", "}", "[", "]", ";", ",", ".", ":")
                else "PUNCTUATION"
            )
            tokens.append(self.make_token(kind, start_pos, self.cursor))
            return True

        return False

    @staticmethod
    def _is_js_identifier_start(ch: str) -> bool:
        """Check if character can begin a JavaScript identifier."""
        if not ch:
            return False
        if ch in ("_", "$"):
            return True
        if "a" <= ch <= "z" or "A" <= ch <= "Z":
            return True
        cat = unicodedata.category(ch)
        return cat in ("Lu", "Ll", "Lt", "Lm", "Lo", "Nl")

    @staticmethod
    def _is_js_identifier_part(ch: str) -> bool:
        """Check if character can continue a JavaScript identifier."""
        if not ch:
            return False
        if ch in ("_", "$"):
            return True
        if "a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9":
            return True
        cat = unicodedata.category(ch)
        return cat in ("Lu", "Ll", "Lt", "Lm", "Lo", "Nl", "Nd", "Mc", "Mn", "Pc", "Cf")
