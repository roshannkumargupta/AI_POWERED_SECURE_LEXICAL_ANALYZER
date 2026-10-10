"""Lightweight recursive-descent structure parser for C/C++ with panic-mode recovery.

Produces a StructTree representation covering structs/classes, functions,
blocks, statements, assignments, call expressions, includes, and error recovery nodes.
Never raises; always returns a StructTree.
"""

from __future__ import annotations

from apsla.languages.cpp_lang.lexer import CppLexer
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


class CppStructParser:
    """Recursive-descent structure parser for C and C++."""

    def __init__(self, source: str, tokens: list[Token] | None = None) -> None:
        self.source = source
        self.raw_tokens = tokens if tokens is not None else CppLexer(source).tokenize()
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
        root = FileNode(range=file_range, language="cpp")

        while not self._is_at_end():
            start_pos = self.pos
            node = self._parse_top_level_or_statement()
            if node:
                root.children.append(node)
            if self.pos == start_pos:
                tok = self._advance()
                if tok.text == "}":
                    self.errors.append(
                        ErrorNode(
                            message=f"Unmatched closing delimiter '{tok.text}' at line {tok.line}",
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

        self._check_unmatched_brackets()

        return StructTree(
            root=root,
            language="cpp",
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

        while not self._is_at_end():
            nxt = self._peek()
            if nxt.text in sync_tokens:
                if nxt.text == ";":
                    self._advance()
                break
            self._advance()
        return err

    # ── Declarations & Statements ──────────────────────────────────────────────

    def _parse_top_level_or_statement() -> StructNode | None:
        pass

    def _parse_top_level_or_statement(self) -> StructNode | None:
        if self._is_at_end():
            return None

        tok = self._peek()

        # Preprocessor directive
        if tok.text.startswith("#") or tok.kind == "PREPROCESSOR":
            return self._parse_preprocessor_directive()

        # Namespace
        if tok.text == "namespace":
            return self._parse_namespace()

        # Class or Struct
        if tok.text in ("class", "struct"):
            return self._parse_class_or_struct()

        # Access specifiers: public:, private:, protected:
        if tok.text in ("public", "private", "protected") and self._peek(1).text == ":":
            self._advance()
            self._advance()
            return None

        return self._parse_function_or_statement()

    def _parse_preprocessor_directive(self) -> ImportNode | None:
        dir_tok = self._advance()
        text = dir_tok.text.strip()

        # Check for #include
        if "include" in text:
            # Header might be in token or next tokens
            header = text.replace("#include", "").strip()
            if not header and not self._is_at_end() and self._peek().line == dir_tok.line:
                header_tok = self._advance()
                header = header_tok.text
            imp_node = ImportNode(
                module=header.strip("<>\"'"),
                range=self._token_range(dir_tok, dir_tok),
                is_include=True,
            )
            self.imports.append(imp_node)
            return imp_node
        return None

    def _parse_namespace(self) -> StructNode:
        start_tok = self._advance()  # 'namespace'
        _ns_name = ""
        if self._peek().kind == "IDENTIFIER":
            _ns_name = self._advance().text

        children: list[StructNode] = []
        if self._match("{"):
            while not self._is_at_end() and self._peek().text != "}":
                child = self._parse_top_level_or_statement()
                if child:
                    children.append(child)
            self._match("}")
        return BlockNode(range=self._token_range(start_tok, self._peek(-1)), children=children)

    def _parse_class_or_struct(self) -> ClassNode:
        kind_tok = self._advance()  # 'class' or 'struct'
        is_struct = kind_tok.text == "struct"
        name = ""
        if self._peek().kind == "IDENTIFIER":
            name = self._advance().text

        # Skip template or inheritance
        while not self._is_at_end() and self._peek().text not in ("{", ";"):
            self._advance()

        class_node = ClassNode(
            name=name,
            range=self._token_range(kind_tok, self._peek(-1)),
            is_struct=is_struct,
        )

        if self._match("{"):
            body_nodes: list[StructNode] = []
            while not self._is_at_end() and self._peek().text != "}":
                member = self._parse_top_level_or_statement()
                if member:
                    body_nodes.append(member)
            self._match("}")
            self._match(";")  # optional trailing semicolon
            class_node.children.extend(body_nodes)
            class_node.range = self._token_range(kind_tok, self._peek(-1))
        elif self._match(";"):
            # Forward declaration
            pass
        else:
            self._panic_sync({"}"}, f"Expected '{{' or ';' in {kind_tok.text} '{name}'")

        self.classes.append(class_node)
        return class_node

    def _parse_function_or_statement(self) -> StructNode | None:
        start_tok = self._peek()

        if start_tok.text == "{":
            self._advance()
            return self._parse_block(start_brace_consumed=True)

        if start_tok.text == "return":
            return self._parse_return_statement()

        if start_tok.text in ("if", "for", "while", "switch", "try", "do"):
            return self._parse_control_statement()

        # Check for function signature: ReturnType FunctionName ( ParamList ) {
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
            name_idx = paren_pos - 1
            name_tok = self.tokens[self.pos + name_idx]
            # Verify name_tok is an identifier, not a keyword
            if name_tok.kind in ("IDENTIFIER", "KEYWORD") and name_tok.text not in (
                "if",
                "for",
                "while",
                "switch",
                "return",
            ):
                # Could be a function definition
                return_type = " ".join(t.text for t in self.tokens[self.pos : self.pos + name_idx])
                # Check if this has a body '{' after ')'
                has_body = False
                depth = 0
                check_idx = paren_pos
                while self.pos + check_idx < len(self.tokens):
                    ct = self.tokens[self.pos + check_idx]
                    if ct.text == "(":
                        depth += 1
                    elif ct.text == ")":
                        depth -= 1
                        if depth == 0:
                            # Look ahead for '{' or ';'
                            if self.pos + check_idx + 1 < len(self.tokens):
                                nxt = self.tokens[self.pos + check_idx + 1]
                                if nxt.text == "{":
                                    has_body = True
                            break
                    check_idx += 1

                if has_body:
                    for _ in range(paren_pos):
                        self._advance()
                    return self._parse_function_declaration(
                        name=name_tok.text,
                        return_type=return_type,
                        start_tok=start_tok,
                    )

        return self._parse_expression_or_assignment_statement()

    def _parse_function_declaration(
        self,
        name: str,
        return_type: str,
        start_tok: Token,
    ) -> FunctionNode:
        self._match("(")
        params: list[str] = []
        while not self._is_at_end() and self._peek().text != ")":
            pt = self._advance()
            if pt.kind == "IDENTIFIER" and pt.text not in (",", "*", "&", "[", "]"):
                if self._peek().text in (",", ")", "="):
                    params.append(pt.text)
            elif pt.text == ",":
                continue
        self._match(")")

        fn_node = FunctionNode(
            name=name,
            range=self._token_range(start_tok, self._peek(-1)),
            params=params,
            return_type=return_type,
            is_method=False,
        )

        if self._match("{"):
            block = self._parse_block(start_brace_consumed=True)
            fn_node.children.append(block)
            fn_node.range = self._token_range(start_tok, self._peek(-1))
        elif self._match(";"):
            pass
        else:
            self._panic_sync({";", "}"}, f"Expected '{{' in function '{name}'")

        self.functions.append(fn_node)
        return fn_node

    def _parse_block(self, start_brace_consumed: bool = False) -> BlockNode:
        start_tok = self._peek(-1) if start_brace_consumed else self._advance()
        children: list[StructNode] = []

        while not self._is_at_end() and self._peek().text != "}":
            start_pos = self.pos
            stmt = self._parse_function_or_statement()
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
        self._extract_calls_from_tokens(val_tokens)
        return ret_node

    def _parse_control_statement(self) -> StructNode:
        start_tok = self._advance()
        if self._match("("):
            cond_tokens = self._skip_matching("(", ")")
            self._extract_calls_from_tokens(cond_tokens)

        body_node: StructNode | None = None
        if self._peek().text == "{":
            self._advance()
            body_node = self._parse_block(start_brace_consumed=True)
        else:
            body_node = self._parse_function_or_statement()

        if start_tok.text == "if" and self._match("else"):
            if self._peek().text == "{":
                self._advance()
                self._parse_block(start_brace_consumed=True)
            else:
                self._parse_function_or_statement()

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

            # In C++, no ASI: statement keyword on a new line indicates missing semicolon
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
                    "bool",
                    "void",
                    "return",
                    "if",
                    "for",
                    "while",
                    "class",
                    "struct",
                    "namespace",
                    "public",
                    "private",
                    "protected",
                    "static",
                    "const",
                    "std",
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

        eq_idx = -1
        for i, t in enumerate(stmt_tokens):
            if t.text == "=" and i > 0:
                eq_idx = i
                break

        if eq_idx > 0:
            target_toks = stmt_tokens[:eq_idx]
            # Strip type modifiers/pointers from target name
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

        self._extract_calls_from_tokens(stmt_tokens)
        return StatementNode(range=stmt_range, text=stmt_text)

    # ── Call Extraction ────────────────────────────────────────────────────────

    def _extract_calls_from_tokens(self, tokens: list[Token]) -> list[CallNode]:
        calls: list[CallNode] = []
        i = 0
        while i < len(tokens):
            if tokens[i].text == "(" and i > 0:
                callee_parts: list[str] = []
                j = i - 1
                while j >= 0:
                    tok = tokens[j]
                    if tok.kind in ("IDENTIFIER", "KEYWORD") or tok.text in (".", "->", "::"):
                        callee_parts.insert(0, tok.text)
                        j -= 1
                    else:
                        break

                callee_name = "".join(callee_parts)
                if callee_name and callee_name not in (
                    "if",
                    "for",
                    "while",
                    "switch",
                    "catch",
                    "sizeof",
                ):
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


def parse_cpp_structure(source: str, tokens: list[Token] | None = None) -> StructTree:
    """Entry point for parsing C/C++ source code into a StructTree."""
    return CppStructParser(source, tokens).parse()
