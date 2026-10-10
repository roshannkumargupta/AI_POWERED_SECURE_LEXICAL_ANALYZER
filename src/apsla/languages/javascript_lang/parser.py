"""Lightweight recursive-descent structure parser for JavaScript with panic-mode recovery.

Produces a StructTree representation covering classes, functions, arrow functions,
blocks, statements, assignments, call expressions, and error recovery nodes.
Never raises; always returns a StructTree.
"""

from __future__ import annotations

from apsla.languages.javascript_lang.lexer import JavaScriptLexer
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


class JavaScriptStructParser:
    """Recursive-descent structure parser for JavaScript / TypeScript / Node."""

    def __init__(self, source: str, tokens: list[Token] | None = None) -> None:
        self.source = source
        self.raw_tokens = tokens if tokens is not None else JavaScriptLexer(source).tokenize()
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
        root = FileNode(range=file_range, language="javascript")

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

        self._check_unmatched_brackets()

        return StructTree(
            root=root,
            language="javascript",
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

    def _parse_top_level_or_statement(self) -> StructNode | None:
        tok = self._peek()

        # Handle 'export' keyword
        if tok.text == "export":
            self._advance()
            tok = self._peek()

        if tok.text == "import":
            return self._parse_import_statement()

        if tok.text == "class":
            return self._parse_class_declaration()

        if tok.text in ("function", "async"):
            if tok.text == "async" and self._peek(1).text == "function":
                self._advance()  # 'async'
            if self._peek().text == "function":
                return self._parse_function_declaration()

        return self._parse_statement()

    def _parse_import_statement(self) -> ImportNode:
        start_tok = self._advance()  # 'import'
        names: list[str] = []
        module_name = ""

        # Collect imported identifiers
        while not self._is_at_end() and self._peek().text not in ("from", ";"):
            t = self._advance()
            if t.kind == "IDENTIFIER":
                names.append(t.text)

        if self._match("from"):
            mod_tok = self._advance()
            module_name = mod_tok.text.strip("\"'")

        if self._match(";"):
            pass

        imp_node = ImportNode(
            module=module_name,
            range=self._token_range(start_tok, self._peek(-1)),
            names=names,
            is_include=False,
        )
        self.imports.append(imp_node)
        return imp_node

    def _parse_class_declaration(self) -> ClassNode:
        start_tok = self._advance()  # 'class'
        class_name = ""
        if self._peek().kind == "IDENTIFIER":
            class_name = self._advance().text

        # Extends
        if self._match("extends"):
            while not self._is_at_end() and self._peek().text != "{":
                self._advance()

        class_node = ClassNode(
            name=class_name,
            range=self._token_range(start_tok, self._peek(-1)),
            is_struct=False,
        )

        if self._match("{"):
            body_nodes = self._parse_class_body()
            class_node.children.extend(body_nodes)
            class_node.range = self._token_range(start_tok, self._peek(-1))
        else:
            self._panic_sync({"}"}, f"Expected '{{' in class declaration of '{class_name}'")

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
        _is_async = False
        is_static = False

        if start_tok.text == "static":
            self._advance()
            is_static = True
        if self._peek().text == "async":
            self._advance()
            _is_async = True

        name_tok = self._peek()
        if name_tok.text == "}":
            return None

        # Method or property
        if self._peek(1).text == "(":
            method_name = self._advance().text
            self._match("(")
            params = self._parse_param_list()
            self._match(")")
            fn_node = FunctionNode(
                name=method_name,
                range=self._token_range(start_tok, self._peek(-1)),
                params=params,
                is_method=True,
                modifiers=["static"] if is_static else [],
            )
            if self._match("{"):
                block = self._parse_block(start_brace_consumed=True)
                fn_node.children.append(block)
                fn_node.range = self._token_range(start_tok, self._peek(-1))
            self.functions.append(fn_node)
            return fn_node

        return self._parse_statement()

    def _parse_function_declaration(self) -> FunctionNode:
        start_tok = self._advance()  # 'function'
        name = ""
        if self._peek().kind == "IDENTIFIER":
            name = self._advance().text

        self._match("(")
        params = self._parse_param_list()
        self._match(")")

        fn_node = FunctionNode(
            name=name,
            range=self._token_range(start_tok, self._peek(-1)),
            params=params,
            is_method=False,
        )

        if self._match("{"):
            block = self._parse_block(start_brace_consumed=True)
            fn_node.children.append(block)
            fn_node.range = self._token_range(start_tok, self._peek(-1))
        else:
            self._panic_sync({";", "}"}, f"Expected '{{' in function '{name}'")

        self.functions.append(fn_node)
        return fn_node

    def _parse_param_list(self) -> list[str]:
        params: list[str] = []
        while not self._is_at_end() and self._peek().text != ")":
            t = self._advance()
            if t.kind == "IDENTIFIER" and t.text not in (",", "{", "}"):
                params.append(t.text)
            elif t.text == ",":
                continue
        return params

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

        if tok.text == "{":
            self._advance()
            return self._parse_block(start_brace_consumed=True)

        if tok.text == "return":
            return self._parse_return_statement()

        if tok.text in ("if", "for", "while", "switch", "try", "do"):
            return self._parse_control_statement()

        return self._parse_expression_or_assignment_statement()

    def _parse_return_statement(self) -> ReturnNode:
        ret_tok = self._advance()  # 'return'
        val_tokens: list[Token] = []
        paren_depth = 0
        bracket_depth = 0
        brace_depth = 0
        while not self._is_at_end():
            curr = self._peek()
            if curr.text == "(":
                paren_depth += 1
            elif curr.text == ")":
                if paren_depth > 0:
                    paren_depth -= 1
            elif curr.text == "[":
                bracket_depth += 1
            elif curr.text == "]":
                if bracket_depth > 0:
                    bracket_depth -= 1
            elif curr.text == "{":
                brace_depth += 1
            elif curr.text == "}":
                if brace_depth > 0:
                    brace_depth -= 1
                elif curr.kind != "TEMPLATE":
                    break
            elif curr.text == ";":
                if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                    break
            # Check for newline ASI (if next token is on subsequent line and not an operator)
            if (
                paren_depth == 0
                and bracket_depth == 0
                and brace_depth == 0
                and val_tokens
                and curr.line > val_tokens[-1].line
            ):
                break
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
            body_node = self._parse_statement()

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

        _is_var_decl = False
        if start_tok.text in ("const", "let", "var"):
            _is_var_decl = True

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

            # ASI line break heuristic: if current token starts a new statement keyword on a new line
            if (
                paren_depth == 0
                and bracket_depth == 0
                and brace_depth == 0
                and stmt_tokens
                and t.line > stmt_tokens[-1].line
                and t.text
                in (
                    "const",
                    "let",
                    "var",
                    "function",
                    "return",
                    "if",
                    "for",
                    "while",
                    "class",
                    "export",
                    "import",
                )
            ):
                break
            stmt_tokens.append(self._advance())

        if not stmt_tokens:
            return StatementNode(range=self._token_range(start_tok, start_tok), text="")

        stmt_range = self._token_range(stmt_tokens[0], stmt_tokens[-1])
        stmt_text = " ".join(t.text for t in stmt_tokens)

        # Check for assignment '='
        eq_idx = -1
        for i, t in enumerate(stmt_tokens):
            if t.text == "=" and i > 0:
                eq_idx = i
                break

        if eq_idx > 0:
            target_toks = stmt_tokens[:eq_idx]
            target_name = target_toks[-1].text if target_toks else ""
            val_toks = stmt_tokens[eq_idx + 1 :]
            val_text = " ".join(t.text for t in val_toks)
            val_range = self._token_range(val_toks[0], val_toks[-1]) if val_toks else None

            # Detect require('module') as Import
            if "require" in val_text:
                for k, vt in enumerate(val_toks):
                    if (
                        vt.text == "require"
                        and k + 2 < len(val_toks)
                        and val_toks[k + 1].text == "("
                    ):
                        mod_str = val_toks[k + 2].text.strip("\"'")
                        imp_node = ImportNode(
                            module=mod_str,
                            range=stmt_range,
                            names=[target_name],
                            is_include=False,
                        )
                        self.imports.append(imp_node)

            # Check if value is an arrow function: (x, y) => { ... } or x => { ... }
            is_arrow = any(t.text == "=>" for t in val_toks)
            if is_arrow:
                arrow_fn = FunctionNode(
                    name=target_name,
                    range=stmt_range,
                    params=[t.text for t in target_toks if t.kind == "IDENTIFIER"],
                    is_method=False,
                )
                self.functions.append(arrow_fn)

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
                    if tok.kind in ("IDENTIFIER", "KEYWORD") or tok.text == ".":
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
                    "function",
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
                else:
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
            if t.kind in ("COMMENT", "STRING", "TEMPLATE", "REGEX"):
                continue
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


def parse_javascript_structure(source: str, tokens: list[Token] | None = None) -> StructTree:
    """Entry point for parsing JavaScript source code into a StructTree."""
    return JavaScriptStructParser(source, tokens).parse()
