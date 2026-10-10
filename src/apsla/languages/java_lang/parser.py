"""Lightweight recursive-descent structure parser for Java with panic-mode recovery.

Produces a StructTree representation covering classes, methods, blocks,
statements, assignments, call expressions, and error recovery nodes.
Never raises; always returns a StructTree.
"""

from __future__ import annotations

from typing import Final

from apsla.languages.java_lang.lexer import JavaLexer
from apsla.languages.struct_tree import (
    AssignmentNode,
    BlockNode,
    CallNode,
    ClassNode,
    ErrorNode,
    FileNode,
    FunctionNode,
    ImportNode,
    ReturnNode,
    StatementNode,
    StructNode,
    StructTree,
)
from apsla.lexing.token import Token
from apsla.models import Range

JAVA_MODIFIERS: Final[frozenset[str]] = frozenset(
    {
        "public",
        "protected",
        "private",
        "static",
        "final",
        "abstract",
        "synchronized",
        "volatile",
        "transient",
        "native",
        "strictfp",
        "default",
    }
)


class JavaStructParser:
    """Recursive-descent structure parser for Java with panic recovery."""

    def __init__(self, source: str, tokens: list[Token] | None = None) -> None:
        self.source = source
        self.raw_tokens = tokens if tokens is not None else JavaLexer(source).tokenize()
        # Filter out comments and whitespace for parsing, but preserve range mapping
        self.tokens: list[Token] = [
            t for t in self.raw_tokens if t.kind not in ("WHITESPACE", "COMMENT")
        ]
        self.pos = 0
        self.errors: list[ErrorNode] = []
        self.calls: list[CallNode] = []
        self.functions: list[FunctionNode] = []
        self.classes: list[ClassNode] = []
        self.assignments: list[AssignmentNode] = []
        self.imports: list[ImportNode] = []

    def parse(self) -> StructTree:
        """Parse source tokens into a StructTree."""
        file_range = self._get_file_range()
        root = FileNode(range=file_range, language="java")

        # Parse package and imports
        while not self._is_at_end():
            token = self._peek()
            if token.text == "package":
                self._parse_package()
            elif token.text == "import":
                imp = self._parse_import()
                if imp:
                    root.children.append(imp)
                    self.imports.append(imp)
            else:
                break

        # Parse top-level type declarations
        while not self._is_at_end():
            start_pos = self.pos
            node = self._parse_type_declaration_or_statement()
            if node:
                root.children.append(node)
            if self.pos == start_pos:
                tok = self._advance()
                if tok.text == "}":
                    self.errors.append(
                        ErrorNode(
                            message="Unmatched closing brace '}'",
                            range=self._token_range(tok, tok),
                            unexpected_token=tok.text,
                        )
                    )
                elif tok.kind != "EOF":
                    self.errors.append(
                        ErrorNode(
                            message=f"Unexpected token '{tok.text}'",
                            range=self._token_range(tok, tok),
                            unexpected_token=tok.text,
                        )
                    )

        # Collect any unmatched brackets as error nodes
        self._check_unmatched_brackets()

        return StructTree(
            root=root,
            language="java",
            errors=self.errors,
            calls=self.calls,
            functions=self.functions,
            classes=self.classes,
            assignments=self.assignments,
            imports=self.imports,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        if self.tokens:
            last = self.tokens[-1]
            return Token(
                kind="EOF",
                text="",
                start=last.end,
                end=last.end,
                line=last.line,
                col=last.col + len(last.text),
                end_line=last.line,
                end_col=last.col + len(last.text),
            )
        return Token(kind="EOF", text="", start=0, end=0, line=1, col=1, end_line=1, end_col=1)

    def _is_at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def _advance(self) -> Token:
        tok = self._peek()
        self.pos += 1
        return tok

    def _match(self, text: str) -> bool:
        if self._peek().text == text:
            self._advance()
            return True
        return False

    def _token_range(self, start_tok: Token, end_tok: Token) -> Range:
        return Range(
            start_line=start_tok.line,
            start_col=start_tok.col,
            end_line=end_tok.line,
            end_col=end_tok.col + max(0, len(end_tok.text)),
        )

    def _get_file_range(self) -> Range:
        if not self.tokens:
            return Range(start_line=1, start_col=1, end_line=1, end_col=1)
        first = self.tokens[0]
        last = self.tokens[-1]
        return Range(
            start_line=first.line,
            start_col=first.col,
            end_line=last.line,
            end_col=last.col + len(last.text),
        )

    # ── Panic-Mode Recovery ────────────────────────────────────────────────────

    def _panic_sync(
        self, sync_tokens: set[str], error_msg: str, at_tok: Token | None = None
    ) -> ErrorNode:
        err_tok = at_tok or self._peek()
        err = ErrorNode(
            message=error_msg,
            range=Range(
                start_line=err_tok.line,
                start_col=err_tok.col,
                end_line=err_tok.line,
                end_col=err_tok.col + max(1, len(err_tok.text)),
            ),
            unexpected_token=err_tok.text,
        )
        self.errors.append(err)

        # Synchronize: advance until a sync token is seen
        while not self._is_at_end():
            nxt = self._peek()
            if nxt.text in sync_tokens:
                if nxt.text == ";":
                    self._advance()  # consume semicolon
                break
            self._advance()
        return err

    # ── Declarations ──────────────────────────────────────────────────────────

    def _parse_package(self) -> None:
        self._advance()  # 'package'
        while not self._is_at_end() and self._peek().text != ";":
            self._advance()
        self._match(";")

    def _parse_import(self) -> ImportNode | None:
        start_tok = self._advance()  # 'import'
        is_static = False
        if self._peek().text == "static":
            is_static = True
            self._advance()

        module_parts: list[str] = []
        end_tok = start_tok
        while not self._is_at_end() and self._peek().text != ";":
            if self._peek().text in ("public", "class", "interface", "enum", "{", "}"):
                self.errors.append(
                    ErrorNode(
                        message=f"Missing semicolon in import before '{self._peek().text}'",
                        range=self._token_range(end_tok, end_tok),
                        unexpected_token=self._peek().text,
                    )
                )
                break
            t = self._advance()
            module_parts.append(t.text)
            end_tok = t

        if not self._match(";"):
            if not self.errors or self.errors[-1].unexpected_token != self._peek().text:
                self.errors.append(
                    ErrorNode(
                        message="Expected ';' after import",
                        range=self._token_range(end_tok, end_tok),
                        unexpected_token=end_tok.text,
                    )
                )

        module_name = "".join(module_parts)
        imp = ImportNode(
            module=module_name,
            range=self._token_range(start_tok, end_tok),
            names=["static"] if is_static else [],
            is_include=False,
        )
        return imp

    def _parse_type_declaration_or_statement(self) -> StructNode | None:
        # Collect modifiers and annotations
        start_tok = self._peek()
        modifiers: list[str] = []

        while not self._is_at_end():
            tok = self._peek()
            if tok.text.startswith("@"):
                self._advance()
                if self._match("("):
                    self._skip_matching("(", ")")
            elif tok.text in JAVA_MODIFIERS:
                modifiers.append(self._advance().text)
            else:
                break

        tok = self._peek()
        if tok.text in ("class", "interface", "enum", "record"):
            return self._parse_class_declaration(modifiers, start_tok)

        # Otherwise could be a statement or field/method outside class (if top-level script/scratch)
        return self._parse_statement()

    def _parse_class_declaration(self, modifiers: list[str], start_tok: Token) -> ClassNode:
        kind_tok = self._advance()  # 'class', 'interface', 'enum', 'record'
        class_name = ""
        if not self._is_at_end() and self._peek().kind == "IDENTIFIER":
            class_name = self._advance().text

        # Skip generic parameters <T, ...>
        if self._match("<"):
            self._skip_matching("<", ">")

        # Skip extends / implements
        while not self._is_at_end() and self._peek().text != "{" and self._peek().text != ";":
            self._advance()

        class_node = ClassNode(
            name=class_name,
            range=self._token_range(start_tok, kind_tok),
            is_struct=False,
            modifiers=modifiers,
        )

        if self._match("{"):
            body_nodes = self._parse_class_body()
            class_node.children.extend(body_nodes)
            close_tok = self._peek(-1) if self.pos > 0 else start_tok
            class_node.range = self._token_range(start_tok, close_tok)
        elif self._peek().text == ";":
            self._advance()
        else:
            self._panic_sync({"}", ";"}, f"Expected '{{' in class declaration of '{class_name}'")

        self.classes.append(class_node)
        return class_node

    def _parse_class_body(self) -> list[StructNode]:
        nodes: list[StructNode] = []
        while not self._is_at_end() and self._peek().text != "}":
            member = self._parse_class_member()
            if member:
                nodes.append(member)
        self._match("}")
        return nodes

    def _parse_class_member(self) -> StructNode | None:
        start_tok = self._peek()
        modifiers: list[str] = []

        while not self._is_at_end():
            tok = self._peek()
            if tok.text.startswith("@"):
                self._advance()
                if self._match("("):
                    self._skip_matching("(", ")")
            elif tok.text in JAVA_MODIFIERS:
                modifiers.append(self._advance().text)
            else:
                break

        tok = self._peek()
        if tok.text in ("class", "interface", "enum", "record"):
            return self._parse_class_declaration(modifiers, start_tok)

        # Method or Field: read type and name
        if self._is_at_end() or tok.text == "}":
            return None

        # Lookahead for method: Type identifier ( ... ) {
        # Or Constructor: ClassName ( ... ) {
        _is_method = False
        name_tok = None
        return_type = ""

        # Scan ahead to see if there is a '(' before ';' or '=' or '{'
        scan_idx = 0
        has_paren = False
        paren_pos = -1
        while self.pos + scan_idx < len(self.tokens):
            st = self.tokens[self.pos + scan_idx]
            if st.text == "(":
                has_paren = True
                paren_pos = scan_idx
                break
            if st.text in (";", "=", "{", "}"):
                break
            scan_idx += 1

        if has_paren and paren_pos > 0:
            # Check if this is an enum constant entry e.g. ADMIN("Administrator"), USER("Standard User");
            if paren_pos == 1:
                scan_ahead = self.pos + paren_pos
                depth = 0
                is_enum_entry = False
                while scan_ahead < len(self.tokens):
                    st = self.tokens[scan_ahead]
                    if st.text == "(":
                        depth += 1
                    elif st.text == ")":
                        depth -= 1
                        if depth == 0:
                            if scan_ahead + 1 < len(self.tokens) and self.tokens[
                                scan_ahead + 1
                            ].text in (",", ";"):
                                is_enum_entry = True
                            break
                    scan_ahead += 1
                if is_enum_entry:
                    start_c = self._advance()
                    while not self._is_at_end() and self._peek().text not in (";", "}"):
                        self._advance()
                    self._match(";")
                    return StatementNode(
                        range=self._token_range(start_c, self._peek(-1)), text="enum_constants"
                    )

            # We have a method or constructor
            _is_method = True
            name_idx = paren_pos - 1
            name_tok = self.tokens[self.pos + name_idx]
            if name_idx > 0:
                return_type = " ".join(t.text for t in self.tokens[self.pos : self.pos + name_idx])

            # Advance up to '('
            for _ in range(paren_pos):
                self._advance()
            return self._parse_method_declaration(
                name=name_tok.text,
                return_type=return_type,
                modifiers=modifiers,
                start_tok=start_tok,
            )

        # Otherwise field declaration or statement
        return self._parse_statement()

    def _parse_method_declaration(
        self,
        name: str,
        return_type: str,
        modifiers: list[str],
        start_tok: Token,
    ) -> FunctionNode:
        # We are at '('
        self._match("(")
        params: list[str] = []
        while not self._is_at_end() and self._peek().text != ")":
            pt = self._advance()
            if pt.kind == "IDENTIFIER" and pt.text not in (",", "[", "]"):
                # Collect parameter name
                if self._peek().text in (",", ")"):
                    params.append(pt.text)
            elif pt.text == ",":
                continue
        self._match(")")

        # Skip throws clause
        if self._match("throws"):
            while not self._is_at_end() and self._peek().text not in ("{", ";"):
                self._advance()

        fn_node = FunctionNode(
            name=name,
            range=self._token_range(start_tok, self._peek(-1)),
            params=params,
            return_type=return_type,
            is_method=True,
            modifiers=modifiers,
        )

        if self._match("{"):
            block = self._parse_block(start_brace_consumed=True)
            fn_node.children.append(block)
            fn_node.range = self._token_range(start_tok, self._peek(-1))
        elif self._match(";"):
            # Abstract or interface method
            fn_node.range = self._token_range(start_tok, self._peek(-1))
        else:
            self._panic_sync({";", "}"}, f"Expected '{{' or ';' after method signature '{name}'")

        self.functions.append(fn_node)
        return fn_node

    # ── Statements & Expressions ───────────────────────────────────────────────

    def _parse_block(self, start_brace_consumed: bool = False) -> BlockNode:
        start_tok = self._peek(-1) if start_brace_consumed else self._advance()
        children: list[StructNode] = []

        while not self._is_at_end() and self._peek().text != "}":
            start_pos = self.pos
            stmt = self._parse_statement()
            if stmt:
                children.append(stmt)
            if self.pos == start_pos:
                tok = self._advance()
                if tok.text == "}":
                    break
                if tok.kind != "EOF":
                    self.errors.append(
                        ErrorNode(
                            message=f"Unexpected token '{tok.text}' in block",
                            range=self._token_range(tok, tok),
                            unexpected_token=tok.text,
                        )
                    )

        end_tok = (
            self._advance()
            if not self._is_at_end() and self._peek().text == "}"
            else self._peek(-1)
        )
        return BlockNode(range=self._token_range(start_tok, end_tok), children=children)

    def _parse_statement(self) -> StructNode | None:
        if self._is_at_end() or self._peek().text == "}":
            return None

        tok = self._peek()

        # Block statement
        if tok.text == "{":
            self._advance()
            return self._parse_block(start_brace_consumed=True)

        # Return statement
        if tok.text == "return":
            return self._parse_return_statement()

        # Control flow blocks: if, for, while, switch, try, do
        if tok.text in ("if", "for", "while", "switch", "try", "do"):
            return self._parse_control_statement()

        # Regular statement or assignment or call
        return self._parse_expression_or_assignment_statement()

    def _parse_return_statement(self) -> ReturnNode:
        ret_tok = self._advance()  # 'return'
        val_tokens: list[Token] = []
        while not self._is_at_end() and self._peek().text != ";":
            val_tokens.append(self._advance())
        self._match(";")

        val_text = " ".join(t.text for t in val_tokens)
        val_range = self._token_range(val_tokens[0], val_tokens[-1]) if val_tokens else None
        end_tok = val_tokens[-1] if val_tokens else ret_tok
        ret_node = ReturnNode(
            range=self._token_range(ret_tok, end_tok),
            value_text=val_text,
            value_range=val_range,
        )

        # Inspect return value for nested calls
        self._extract_calls_from_tokens(val_tokens)
        return ret_node

    def _parse_control_statement(self) -> StructNode:
        start_tok = self._advance()  # 'if', 'while', etc.
        if self._match("("):
            cond_tokens = self._skip_matching("(", ")")
            self._extract_calls_from_tokens(cond_tokens)

        # Body: could be block or single statement
        body_node: StructNode | None = None
        if self._peek().text == "{":
            self._advance()
            body_node = self._parse_block(start_brace_consumed=True)
        else:
            body_node = self._parse_statement()

        # Check for else clause if 'if'
        if start_tok.text == "if" and self._match("else"):
            if self._peek().text == "{":
                self._advance()
                self._parse_block(start_brace_consumed=True)
            else:
                self._parse_statement()

        end_tok = self._peek(-1) if self.pos > 0 else start_tok
        return StatementNode(
            range=self._token_range(start_tok, end_tok),
            text=start_tok.text,
            children=[body_node] if body_node else [],
        )

    def _parse_expression_or_assignment_statement(self) -> StructNode:
        start_tok = self._peek()
        stmt_tokens: list[Token] = []

        paren_depth = 0
        bracket_depth = 0
        brace_depth = 0

        # Read tokens until ';' or unclosed block '}'
        while not self._is_at_end():
            t = self._peek()
            if t.text == "(":
                paren_depth += 1
            elif t.text == ")":
                if paren_depth > 0:
                    paren_depth -= 1
            elif t.text == "[":
                bracket_depth += 1
            elif t.text == "]":
                if bracket_depth > 0:
                    bracket_depth -= 1
            elif t.text == "{":
                brace_depth += 1
            elif t.text == "}":
                if brace_depth > 0:
                    brace_depth -= 1
                else:
                    break

            if t.text == ";" and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                self._advance()
                break

            # In Java, no ASI: statement keyword on a new line indicates missing semicolon
            if (
                paren_depth == 0
                and bracket_depth == 0
                and brace_depth == 0
                and stmt_tokens
                and t.line > stmt_tokens[-1].line
                and t.text
                in (
                    "int",
                    "double",
                    "float",
                    "char",
                    "boolean",
                    "void",
                    "return",
                    "if",
                    "for",
                    "while",
                    "class",
                    "public",
                    "private",
                    "protected",
                    "static",
                    "final",
                    "String",
                )
            ):
                self.errors.append(
                    ErrorNode(
                        message=f"Missing semicolon before '{t.text}' at line {t.line}",
                        range=self._token_range(stmt_tokens[-1], stmt_tokens[-1]),
                        unexpected_token=t.text,
                    )
                )
                break

            stmt_tokens.append(self._advance())

        if not stmt_tokens:
            return StatementNode(range=self._token_range(start_tok, start_tok), text="")

        stmt_range = self._token_range(stmt_tokens[0], stmt_tokens[-1])
        stmt_text = " ".join(t.text for t in stmt_tokens)

        # Check for assignment '=' (not '==', '!=', '<=', '>=')
        eq_idx = -1
        for i, t in enumerate(stmt_tokens):
            if t.text == "=" and i > 0:
                eq_idx = i
                break

        if eq_idx > 0:
            # Assignment
            target_toks = stmt_tokens[:eq_idx]
            # Target is the last identifier in target_toks
            target_name = target_toks[-1].text if target_toks else ""
            val_toks = stmt_tokens[eq_idx + 1 :]
            val_text = " ".join(t.text for t in val_toks)
            val_range = self._token_range(val_toks[0], val_toks[-1]) if val_toks else None

            assign_node = AssignmentNode(
                target=target_name,
                range=stmt_range,
                value_text=val_text,
                value_range=val_range,
            )
            self.assignments.append(assign_node)
            self._extract_calls_from_tokens(val_toks)
            return assign_node

        # Regular statement (e.g. function call: obj.method(arg);)
        self._extract_calls_from_tokens(stmt_tokens)
        return StatementNode(range=stmt_range, text=stmt_text)

    # ── Call Extraction ────────────────────────────────────────────────────────

    def _extract_calls_from_tokens(self, tokens: list[Token]) -> list[CallNode]:
        calls: list[CallNode] = []
        i = 0
        while i < len(tokens):
            if tokens[i].text == "(" and i > 0:
                # Find callee
                callee_parts: list[str] = []
                j = i - 1
                while j >= 0:
                    tok = tokens[j]
                    if tok.kind in ("IDENTIFIER", "KEYWORD") or tok.text in (".", "::"):
                        callee_parts.insert(0, tok.text)
                        j -= 1
                    else:
                        break

                callee_name = "".join(callee_parts)
                # Ignore control flow words
                if callee_name and callee_name not in (
                    "if",
                    "for",
                    "while",
                    "switch",
                    "catch",
                    "synchronized",
                ):
                    # Extract argument ranges
                    _open_paren_tok = tokens[i]
                    arg_ranges, arg_texts, close_paren_tok = self._extract_call_args(tokens, i)
                    call_range = self._token_range(
                        tokens[i - len(callee_parts) if callee_parts else i - 1],
                        close_paren_tok,
                    )
                    c_node = CallNode(
                        callee=callee_name,
                        range=call_range,
                        args=arg_ranges,
                        arg_texts=arg_texts,
                    )
                    calls.append(c_node)
                    self.calls.append(c_node)
            i += 1
        return calls

    def _extract_call_args(
        self, tokens: list[Token], open_paren_idx: int
    ) -> tuple[list[Range], list[str], Token]:
        arg_ranges: list[Range] = []
        arg_texts: list[str] = []
        depth = 0
        current_arg: list[Token] = []
        close_tok = tokens[open_paren_idx]

        for k in range(open_paren_idx, len(tokens)):
            t = tokens[k]
            if t.text == "(":
                depth += 1
                if depth > 1:
                    current_arg.append(t)
            elif t.text == ")":
                depth -= 1
                if depth == 0:
                    close_tok = t
                    if current_arg:
                        arg_ranges.append(self._token_range(current_arg[0], current_arg[-1]))
                        arg_texts.append(" ".join(x.text for x in current_arg))
                    break
                current_arg.append(t)
            elif t.text == "," and depth == 1:
                if current_arg:
                    arg_ranges.append(self._token_range(current_arg[0], current_arg[-1]))
                    arg_texts.append(" ".join(x.text for x in current_arg))
                    current_arg = []
            else:
                current_arg.append(t)

        return arg_ranges, arg_texts, close_tok

    def _skip_matching(self, open_ch: str, close_ch: str) -> list[Token]:
        depth = 1
        toks: list[Token] = []
        while not self._is_at_end():
            t = self._advance()
            if t.text == open_ch:
                depth += 1
            elif t.text == close_ch:
                depth -= 1
                if depth == 0:
                    break
            toks.append(t)
        return toks

    def _check_unmatched_brackets(self) -> None:
        delim_pairs = {")": "(", "}": "{", "]": "["}
        stack: list[Token] = []
        for t in self.tokens:
            if t.text in ("(", "{", "["):
                stack.append(t)
            elif t.text in (")", "}", "]"):
                expected = delim_pairs[t.text]
                if not stack:
                    self.errors.append(
                        ErrorNode(
                            message=f"Unmatched closing delimiter '{t.text}'",
                            range=self._token_range(t, t),
                            unexpected_token=t.text,
                        )
                    )
                else:
                    top = stack.pop()
                    if top.text != expected:
                        self.errors.append(
                            ErrorNode(
                                message=f"Mismatched delimiter: opened '{top.text}' at line {top.line}, closed with '{t.text}'",
                                range=self._token_range(t, t),
                                unexpected_token=t.text,
                            )
                        )
        for unclosed in stack:
            self.errors.append(
                ErrorNode(
                    message=f"Unclosed delimiter '{unclosed.text}'",
                    range=self._token_range(unclosed, unclosed),
                    unexpected_token=unclosed.text,
                )
            )


def parse_java_structure(source: str, tokens: list[Token] | None = None) -> StructTree:
    """Entry point for parsing Java source code into a StructTree."""
    return JavaStructParser(source, tokens).parse()
