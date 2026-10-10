"""Rule-specific automated remediation fix generators for Python source code."""

from __future__ import annotations

import ast
import re

from apsla.fixes.imports import ensure_import_python
from apsla.fixes.registry import FIX_REGISTRY, FixContext, FixGenerator
from apsla.models import Edit, Fix, VerificationResult
from apsla.unicode_defense.recovery import _CONFUSABLES_MAP


def _create_initial_verification() -> VerificationResult:
    return VerificationResult(
        syntax_ok=False,
        finding_gone=False,
        new_findings=[],
        verified=False,
        notes="Pending verification",
    )


class UnicodeBidiFixGenerator(FixGenerator):
    """Removes Trojan Source bidirectional override characters."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        line_num = finding.range.start_line
        line_start_py = context.offset_map.pos_to_py(line_num, 1)
        line_end_py = (
            context.offset_map.pos_to_py(line_num + 1, 1)
            if line_num < context.offset_map.line_count
            else context.offset_map.py_len
        )
        line_text = context.source[line_start_py:line_end_py]

        from apsla.unicode_defense.scanner import BIDI_CONTROLS

        edits: list[Edit] = []
        for offset, ch in enumerate(line_text):
            if ord(ch) in BIDI_CONTROLS:
                pos = context.offset_map.span_to_range(
                    line_start_py + offset, line_start_py + offset + 1
                )
                edits.append(Edit(range=pos, new_text=""))

        if not edits:
            edits = [Edit(range=finding.range, new_text="")]

        return [
            Fix(
                id=f"fix-{finding.id}-1",
                finding_id=finding.id,
                title="Remove bidirectional control character",
                description="Deletes Trojan Source bidirectional override character (CVE-2021-42574).",
                confidence="safe",
                kind="rule",
                edits=edits,
                verification=_create_initial_verification(),
            )
        ]


class UnicodeInvisibleFixGenerator(FixGenerator):
    """Removes zero-width and invisible characters."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        line_num = finding.range.start_line
        line_start_py = context.offset_map.pos_to_py(line_num, 1)
        line_end_py = (
            context.offset_map.pos_to_py(line_num + 1, 1)
            if line_num < context.offset_map.line_count
            else context.offset_map.py_len
        )
        line_text = context.source[line_start_py:line_end_py]

        from apsla.unicode_defense.scanner import ZERO_WIDTH_CHARS

        edits: list[Edit] = []
        for offset, ch in enumerate(line_text):
            if ord(ch) in ZERO_WIDTH_CHARS:
                pos = context.offset_map.span_to_range(
                    line_start_py + offset, line_start_py + offset + 1
                )
                edits.append(Edit(range=pos, new_text=""))

        if not edits:
            edits = [Edit(range=finding.range, new_text="")]

        return [
            Fix(
                id=f"fix-{finding.id}-1",
                finding_id=finding.id,
                title="Remove invisible character",
                description="Deletes hidden zero-width or non-rendering character.",
                confidence="safe",
                kind="rule",
                edits=edits,
                verification=_create_initial_verification(),
            )
        ]


class UnicodeTagFixGenerator(FixGenerator):
    """Removes deprecated Unicode tag characters."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        line_num = finding.range.start_line
        line_start_py = context.offset_map.pos_to_py(line_num, 1)
        line_end_py = (
            context.offset_map.pos_to_py(line_num + 1, 1)
            if line_num < context.offset_map.line_count
            else context.offset_map.py_len
        )
        line_text = context.source[line_start_py:line_end_py]

        edits: list[Edit] = []
        for offset, ch in enumerate(line_text):
            if 0xE0000 <= ord(ch) <= 0xE007F:
                pos = context.offset_map.span_to_range(
                    line_start_py + offset, line_start_py + offset + 1
                )
                edits.append(Edit(range=pos, new_text=""))

        if not edits:
            edits = [Edit(range=finding.range, new_text="")]

        return [
            Fix(
                id=f"fix-{finding.id}-1",
                finding_id=finding.id,
                title="Remove Unicode tag character",
                description="Deletes deprecated Unicode tag character used for payload smuggling.",
                confidence="safe",
                kind="rule",
                edits=edits,
                verification=_create_initial_verification(),
            )
        ]


class UnicodeConfusableFixGenerator(FixGenerator):
    """Replaces confusable homoglyphs with ASCII equivalents."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        # Check if an identifier token overlaps the finding range
        overlapping_tok = None
        for tok in context.tokens:
            tok_rng = tok.to_range()
            if (
                tok_rng.start_line == finding.range.start_line
                and tok_rng.start_col <= finding.range.start_col
                and finding.range.end_col <= tok_rng.end_col
            ):
                overlapping_tok = tok
                break

        if overlapping_tok is not None:
            raw_slice = overlapping_tok.text
            target_range = overlapping_tok.to_range()
        else:
            start_py = context.offset_map.pos_to_py(
                finding.range.start_line, finding.range.start_col
            )
            end_py = context.offset_map.pos_to_py(finding.range.end_line, finding.range.end_col)
            raw_slice = context.source[start_py:end_py]
            target_range = finding.range

        recovered = []
        for ch in raw_slice:
            recovered.append(_CONFUSABLES_MAP.get(ch, ch))
        new_text = "".join(recovered)
        if new_text == raw_slice:
            recovered_to = (
                finding.evidence.get("recovered_to") or finding.evidence.get("target") or ""
            )
            if recovered_to:
                new_text = recovered_to

        is_dangerous = new_text in ("exec", "eval", "system", "popen", "__import__")
        desc = (
            f"Replaces confusable homoglyphs with ASCII letters (recovers dangerous API: '{new_text}')."
            if is_dangerous
            else "Replaces confusable characters with standard ASCII letters."
        )

        edit = Edit(range=target_range, new_text=new_text)
        return [
            Fix(
                id=f"fix-{finding.id}-1",
                finding_id=finding.id,
                title="Replace confusable character with ASCII",
                description=desc,
                confidence="safe",
                kind="rule",
                edits=[edit],
                verification=_create_initial_verification(),
            )
        ]


class OsSystemFixGenerator(FixGenerator):
    """Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT).

    Replaces os.system(cmd) with subprocess.run([...args], check=True).
    """

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        # Find the os.system / os.popen call node near finding line
        target_call: ast.Call | None = None
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                func_name = ""
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    func_name = f"{node.func.value.id}.{node.func.attr}"
                if func_name in ("os.system", "os.popen"):
                    target_call = node
                    break

        if target_call is None or not target_call.args:
            return []

        arg = target_call.args[0]
        arg_text = ast.get_source_segment(context.source, arg) or ""

        # Determine safe subprocess argument list
        # Case 1: String concatenation: "echo " + name
        if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
            left_seg = (ast.get_source_segment(context.source, arg.left) or "").strip()
            right_seg = (ast.get_source_segment(context.source, arg.right) or "").strip()
            # If left is string literal: e.g. "echo "
            if isinstance(arg.left, ast.Constant) and isinstance(arg.left.value, str):
                parts = arg.left.value.strip().split()
                part_strs = [f'"{p}"' for p in parts]
                replacement_args = f"[{', '.join(part_strs)}, {right_seg}], check=True"
            else:
                replacement_args = f"[{left_seg}, {right_seg}], check=True"

        # Case 2: f-string: f"echo {name}"
        elif isinstance(arg, ast.JoinedStr):
            list_items = []
            for val in arg.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    for p in val.value.strip().split():
                        list_items.append(f'"{p}"')
                elif isinstance(val, ast.FormattedValue):
                    seg = ast.get_source_segment(context.source, val.value) or ""
                    list_items.append(seg)
            replacement_args = f"[{', '.join(list_items)}], check=True"

        # Case 3: Constant string literal: e.g. "ls -la"
        elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            parts = arg.value.strip().split()
            part_strs = [f'"{p}"' for p in parts]
            replacement_args = f"[{', '.join(part_strs)}], check=True"

        # Case 4: General variable or expression: shlex.split(var)
        else:
            replacement_args = f"shlex.split({arg_text}), check=True"

        call_start_py = context.offset_map.pos_to_py(target_call.lineno, target_call.col_offset + 1)
        call_end_py = context.offset_map.pos_to_py(
            target_call.end_lineno, target_call.end_col_offset + 1
        )
        call_range = context.offset_map.span_to_range(call_start_py, call_end_py)

        call_edit = Edit(range=call_range, new_text=f"subprocess.run({replacement_args})")
        import_edits = ensure_import_python(context.source, "import subprocess")
        if "shlex.split" in replacement_args:
            import_edits.extend(ensure_import_python(context.source, "import shlex"))

        all_edits = [*import_edits, call_edit]

        return [
            Fix(
                id=f"fix-{finding.id}-1",
                finding_id=finding.id,
                title="Replace os.system with safe subprocess.run",
                description="Replaces shell execution with parameterized subprocess.run([...], check=True).",
                confidence="review",
                kind="rule",
                edits=all_edits,
                verification=_create_initial_verification(),
            )
        ]


class SubprocessShellFixGenerator(FixGenerator):
    """Replaces shell=True in subprocess calls with shell=False and list arguments."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                has_shell_true = False
                kw_target: ast.keyword | None = None
                for kw in node.keywords:
                    if (
                        kw.arg == "shell"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True
                    ):
                        has_shell_true = True
                        kw_target = kw
                        break

                if has_shell_true and kw_target is not None and node.args:
                    kw_start = context.offset_map.pos_to_py(
                        kw_target.lineno, kw_target.col_offset + 1
                    )
                    kw_end = context.offset_map.pos_to_py(
                        kw_target.end_lineno, kw_target.end_col_offset + 1
                    )
                    kw_range = context.offset_map.span_to_range(kw_start, kw_end)
                    edits = [Edit(range=kw_range, new_text="shell=False")]

                    arg0 = node.args[0]
                    # If arg0 is not already a list or tuple, wrap it as a list
                    if not isinstance(arg0, (ast.List, ast.Tuple)):
                        arg0_start = context.offset_map.pos_to_py(arg0.lineno, arg0.col_offset + 1)
                        arg0_end = context.offset_map.pos_to_py(
                            arg0.end_lineno, arg0.end_col_offset + 1
                        )
                        arg0_range = context.offset_map.span_to_range(arg0_start, arg0_end)

                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            parts = [f'"{p}"' for p in arg0.value.strip().split()]
                            list_text = f"[{', '.join(parts)}]"
                        else:
                            seg = ast.get_source_segment(context.source, arg0) or ""
                            list_text = f"[{seg}]"

                        edits.append(Edit(range=arg0_range, new_text=list_text))

                    return [
                        Fix(
                            id=f"fix-{finding.id}-1",
                            finding_id=finding.id,
                            title="Disable shell=True with argument list in subprocess call",
                            description="Disables shell interpretation by setting shell=False with arguments separated into a list.",
                            confidence="review",
                            kind="rule",
                            edits=edits,
                            verification=_create_initial_verification(),
                        )
                    ]
        return []


class EvalFixGenerator(FixGenerator):
    """Replaces eval() with ast.literal_eval() for safe literal evaluation."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                if func_name == "eval" and node.args:
                    arg_seg = ast.get_source_segment(context.source, node.args[0]) or ""
                    # Check if argument looks like a literal or data expression
                    is_literal_candidate = any(
                        hint in arg_seg.lower()
                        for hint in (
                            "data",
                            "json",
                            "payload",
                            "literal",
                            "expr",
                            "val",
                            "dict",
                            "{",
                            "[",
                        )
                    ) or isinstance(node.args[0], (ast.Name, ast.Constant))

                    if is_literal_candidate:
                        call_start = context.offset_map.pos_to_py(node.lineno, node.col_offset + 1)
                        call_end = context.offset_map.pos_to_py(
                            node.end_lineno, node.end_col_offset + 1
                        )
                        call_range = context.offset_map.span_to_range(call_start, call_end)
                        call_edit = Edit(range=call_range, new_text=f"ast.literal_eval({arg_seg})")
                        import_edits = ensure_import_python(context.source, "import ast")
                        return [
                            Fix(
                                id=f"fix-{finding.id}-1",
                                finding_id=finding.id,
                                title="Use ast.literal_eval for safe literal evaluation",
                                description="Replaces dangerous eval() with ast.literal_eval().",
                                confidence="review",
                                kind="rule",
                                edits=[*import_edits, call_edit],
                                verification=_create_initial_verification(),
                            )
                        ]

        # Advice-only fix for general code execution
        return [
            Fix(
                id=f"fix-{finding.id}-1",
                finding_id=finding.id,
                title="Avoid dynamic code execution with eval/exec",
                description="Do not execute untrusted strings via eval() or exec(). Refactor logic to use safe static dispatch.",
                confidence="manual",
                kind="rule",
                edits=[],
                verification=_create_initial_verification(),
            )
        ]


def _extract_sql_and_params(source: str, node: ast.AST, placeholder: str) -> tuple[str, list[str]]:
    params: list[str] = []
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                parts.append(val.value)
            elif isinstance(val, ast.FormattedValue):
                if parts and (parts[-1].endswith("'") or parts[-1].endswith('"')):
                    parts[-1] = parts[-1][:-1]
                parts.append(placeholder)
                param_seg = ast.get_source_segment(source, val.value) or "param"
                params.append(param_seg)
        cleaned_parts: list[str] = []
        for i, part in enumerate(parts):
            cur_part = (
                part[1:]
                if (i > 0 and parts[i - 1] == placeholder and part.startswith(("'", '"')))
                else part
            )
            cleaned_parts.append(cur_part)
        return "".join(cleaned_parts).strip(), params

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):

        def _flatten(n: ast.AST) -> list[ast.AST]:
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                return _flatten(n.left) + _flatten(n.right)
            return [n]

        nodes = _flatten(node)
        parts = []
        for item in nodes:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                parts.append(item.value)
            else:
                if parts and (parts[-1].endswith("'") or parts[-1].endswith('"')):
                    parts[-1] = parts[-1][:-1]
                parts.append(placeholder)
                seg = ast.get_source_segment(source, item) or "param"
                params.append(seg)
        cleaned_parts = []
        for i, part in enumerate(parts):
            cur_part = (
                part[1:]
                if (i > 0 and parts[i - 1] == placeholder and part.startswith(("'", '"')))
                else part
            )
            cleaned_parts.append(cur_part)
        return "".join(cleaned_parts).strip(), params

    return "SELECT ...", params


class SqlInjectionFixGenerator(FixGenerator):
    """Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT).

    Replaces dynamic string SQL building with parameterized queries.
    """

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        placeholder = "?" if "sqlite" in context.source.lower() else "%s"

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name in ("execute", "executemany") and node.args:
                    sql_arg = node.args[0]
                    # Case 1: Direct dynamic argument (f-string or BinOp)
                    if isinstance(sql_arg, (ast.JoinedStr, ast.BinOp)):
                        clean_sql, params = _extract_sql_and_params(
                            context.source, sql_arg, placeholder
                        )
                        params_tuple = (
                            f"({', '.join(params)},)"
                            if len(params) == 1
                            else f"({', '.join(params)})"
                        )
                        new_call = f"{ast.get_source_segment(context.source, node.func)}({clean_sql!r}, {params_tuple})"
                        call_start = context.offset_map.pos_to_py(node.lineno, node.col_offset + 1)
                        call_end = context.offset_map.pos_to_py(
                            node.end_lineno, node.end_col_offset + 1
                        )
                        call_range = context.offset_map.span_to_range(call_start, call_end)
                        return [
                            Fix(
                                id=f"fix-{finding.id}-1",
                                finding_id=finding.id,
                                title="Use parameterized SQL query",
                                description=f"Replaces dynamic query with parameterized query using '{placeholder}' placeholders.",
                                confidence="review",
                                kind="rule",
                                edits=[Edit(range=call_range, new_text=new_call)],
                                verification=_create_initial_verification(),
                            )
                        ]
                    # Case 2: Variable name referencing preceding assignment
                    if isinstance(sql_arg, ast.Name):
                        var_name = sql_arg.id
                        target_assign: ast.Assign | None = None
                        for stmt in ast.walk(tree):
                            if (
                                isinstance(stmt, ast.Assign)
                                and getattr(stmt, "lineno", 0) < node.lineno
                            ):
                                for tgt in stmt.targets:
                                    if isinstance(tgt, ast.Name) and tgt.id == var_name:
                                        target_assign = stmt
                                        break

                        if target_assign is not None and isinstance(
                            target_assign.value, (ast.JoinedStr, ast.BinOp)
                        ):
                            clean_sql, params = _extract_sql_and_params(
                                context.source, target_assign.value, placeholder
                            )
                            assign_val_start = context.offset_map.pos_to_py(
                                target_assign.value.lineno, target_assign.value.col_offset + 1
                            )
                            assign_val_end = context.offset_map.pos_to_py(
                                target_assign.value.end_lineno,
                                target_assign.value.end_col_offset + 1,
                            )
                            assign_range = context.offset_map.span_to_range(
                                assign_val_start, assign_val_end
                            )
                            assign_edit = Edit(range=assign_range, new_text=repr(clean_sql))

                            params_tuple = (
                                f"({', '.join(params)},)"
                                if len(params) == 1
                                else f"({', '.join(params)})"
                            )
                            new_call = f"{ast.get_source_segment(context.source, node.func)}({var_name}, {params_tuple})"
                            call_start = context.offset_map.pos_to_py(
                                node.lineno, node.col_offset + 1
                            )
                            call_end = context.offset_map.pos_to_py(
                                node.end_lineno, node.end_col_offset + 1
                            )
                            call_range = context.offset_map.span_to_range(call_start, call_end)
                            call_edit = Edit(range=call_range, new_text=new_call)

                            return [
                                Fix(
                                    id=f"fix-{finding.id}-1",
                                    finding_id=finding.id,
                                    title="Use parameterized SQL query",
                                    description=f"Replaces concatenated query with parameterized query using '{placeholder}' placeholders.",
                                    confidence="review",
                                    kind="rule",
                                    edits=[assign_edit, call_edit],
                                    verification=_create_initial_verification(),
                                )
                            ]
        return []


class YamlLoadFixGenerator(FixGenerator):
    """Replaces unsafe yaml.load() with yaml.safe_load()."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                func_name = ""
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    func_name = f"{node.func.value.id}.{node.func.attr}"
                if func_name in ("yaml.load", "yaml.unsafe_load") and node.args:
                    arg_seg = ast.get_source_segment(context.source, node.args[0]) or ""
                    call_start = context.offset_map.pos_to_py(node.lineno, node.col_offset + 1)
                    call_end = context.offset_map.pos_to_py(
                        node.end_lineno, node.end_col_offset + 1
                    )
                    call_range = context.offset_map.span_to_range(call_start, call_end)
                    edit = Edit(range=call_range, new_text=f"yaml.safe_load({arg_seg})")
                    return [
                        Fix(
                            id=f"fix-{finding.id}-1",
                            finding_id=finding.id,
                            title="Replace yaml.load with yaml.safe_load",
                            description="Uses yaml.safe_load to prevent arbitrary code execution during deserialization.",
                            confidence="safe",
                            kind="rule",
                            edits=[edit],
                            verification=_create_initial_verification(),
                        )
                    ]
        return []


class PickleAdviceFixGenerator(FixGenerator):
    """Provides advice for insecure pickle deserialization."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        return [
            Fix(
                id=f"fix-{finding.id}-1",
                finding_id=finding.id,
                title="Replace pickle with safe serialization format",
                description="Do not deserialize untrusted data with pickle or marshal. Migrate to json.loads() or hmac-signed payloads.",
                confidence="manual",
                kind="rule",
                edits=[],
                verification=_create_initial_verification(),
            )
        ]


class HashlibFixGenerator(FixGenerator):
    """Upgrades weak hashlib.md5/sha1 to hashlib.sha256."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ) and isinstance(node.func, ast.Attribute) and node.func.attr in ("md5", "sha1"):
                # Check if compared to a literal hash in the line/statement
                line_start = context.offset_map.pos_to_py(node.lineno, 1)
                line_end = (
                    context.offset_map.pos_to_py(node.lineno + 1, 1)
                    if node.lineno < context.offset_map.line_count
                    else context.offset_map.py_len
                )
                line_text = context.source[line_start:line_end]
                has_literal_hash = bool(
                    re.search(r'==\s*["\'][a-fA-F0-9]{32,40}["\']', line_text)
                )

                attr_start = context.offset_map.pos_to_py(
                    node.func.lineno, node.func.col_offset + 1
                )
                attr_end = context.offset_map.pos_to_py(
                    node.func.end_lineno, node.func.end_col_offset + 1
                )
                func_seg = ast.get_source_segment(context.source, node.func) or ""
                new_func = func_seg.replace("md5", "sha256").replace("sha1", "sha256")
                attr_range = context.offset_map.span_to_range(attr_start, attr_end)
                edit = Edit(range=attr_range, new_text=new_func)

                confidence = "review" if has_literal_hash else "safe"
                return [
                    Fix(
                        id=f"fix-{finding.id}-1",
                        finding_id=finding.id,
                        title="Upgrade weak cryptographic hash to SHA-256",
                        description="Replaces broken MD5/SHA-1 hash with secure SHA-256.",
                        confidence=confidence,
                        kind="rule",
                        edits=[edit],
                        verification=_create_initial_verification(),
                    )
                ]
        return []


class RandomModuleFixGenerator(FixGenerator):
    """Replaces random module with secrets module for tokens."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                call_seg = ast.get_source_segment(context.source, node) or ""
                if "random." in call_seg:
                    new_call = (
                        call_seg.replace("random.randint", "secrets.randbelow")
                        .replace("random.choice", "secrets.choice")
                        .replace("random.", "secrets.")
                    )
                    call_start = context.offset_map.pos_to_py(node.lineno, node.col_offset + 1)
                    call_end = context.offset_map.pos_to_py(
                        node.end_lineno, node.end_col_offset + 1
                    )
                    call_range = context.offset_map.span_to_range(call_start, call_end)
                    call_edit = Edit(range=call_range, new_text=new_call)
                    import_edits = ensure_import_python(context.source, "import secrets")
                    return [
                        Fix(
                            id=f"fix-{finding.id}-1",
                            finding_id=finding.id,
                            title="Use secrets module for cryptographic tokens",
                            description="Replaces pseudorandom generator with cryptographically strong secrets module.",
                            confidence="review",
                            kind="rule",
                            edits=[*import_edits, call_edit],
                            verification=_create_initial_verification(),
                        )
                    ]
        return []


class HardcodedSecretFixGenerator(FixGenerator):
    """Extracts hardcoded secret into os.environ."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        # Find target assignment or constant at finding line
        var_name = "SECRET_KEY"
        target_const: ast.Constant | None = None
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                if node.targets and isinstance(node.targets[0], ast.Name):
                    var_name = node.targets[0].id.upper()
                if isinstance(node.value, ast.Constant):
                    target_const = node.value
                    break

        if target_const is not None:
            const_start = context.offset_map.pos_to_py(
                target_const.lineno, target_const.col_offset + 1
            )
            const_end = context.offset_map.pos_to_py(
                target_const.end_lineno, target_const.end_col_offset + 1
            )
            const_range = context.offset_map.span_to_range(const_start, const_end)
            edit = Edit(range=const_range, new_text=f'os.environ.get("{var_name}", "")')
            import_edits = ensure_import_python(context.source, "import os")
            return [
                Fix(
                    id=f"fix-{finding.id}-1",
                    finding_id=finding.id,
                    title="Load secret from environment variable",
                    description=f"Replaces hardcoded credential literal with os.environ.get('{var_name}', '').",
                    confidence="review",
                    kind="rule",
                    edits=[*import_edits, edit],
                    verification=_create_initial_verification(),
                )
            ]
        return []


class RequestsVerifyFixGenerator(FixGenerator):
    """Removes or sets verify=True for requests calls."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                for kw in node.keywords:
                    if (
                        kw.arg == "verify"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is False
                    ):
                        kw_start = context.offset_map.pos_to_py(kw.lineno, kw.col_offset + 1)
                        kw_end = context.offset_map.pos_to_py(kw.end_lineno, kw.end_col_offset + 1)
                        kw_range = context.offset_map.span_to_range(kw_start, kw_end)
                        edit = Edit(range=kw_range, new_text="verify=True")
                        return [
                            Fix(
                                id=f"fix-{finding.id}-1",
                                finding_id=finding.id,
                                title="Enable SSL verification in requests call",
                                description="Enables TLS certificate validation by setting verify=True.",
                                confidence="safe",
                                kind="rule",
                                edits=[edit],
                                verification=_create_initial_verification(),
                            )
                        ]
        return []


class PathTraversalFixGenerator(FixGenerator):
    """Wraps user-controlled path in os.path.basename."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name in ("open", "send_file") and node.args:
                    path_arg = node.args[0]
                    arg_seg = ast.get_source_segment(context.source, path_arg) or ""
                    arg_start = context.offset_map.pos_to_py(
                        path_arg.lineno, path_arg.col_offset + 1
                    )
                    arg_end = context.offset_map.pos_to_py(
                        path_arg.end_lineno, path_arg.end_col_offset + 1
                    )
                    arg_range = context.offset_map.span_to_range(arg_start, arg_end)
                    edit = Edit(range=arg_range, new_text=f"os.path.basename({arg_seg})")
                    import_edits = ensure_import_python(context.source, "import os")
                    return [
                        Fix(
                            id=f"fix-{finding.id}-1",
                            finding_id=finding.id,
                            title="Sanitize path with os.path.basename",
                            description="Wraps path parameter in os.path.basename() to prevent directory traversal.",
                            confidence="review",
                            kind="rule",
                            edits=[*import_edits, edit],
                            verification=_create_initial_verification(),
                        )
                    ]
        return []


class XssEscapeFixGenerator(FixGenerator):
    """Wraps user data in markupsafe.escape."""

    def generate(self, context: FixContext) -> list[Fix]:
        finding = context.finding
        tree = context.ast_tree
        if tree is None:
            return []

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node, "lineno", 0) == finding.range.start_line
            ):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name in ("Markup", "render_template_string") and node.args:
                    arg_node = node.args[0]
                    arg_seg = ast.get_source_segment(context.source, arg_node) or ""
                    arg_start = context.offset_map.pos_to_py(
                        arg_node.lineno, arg_node.col_offset + 1
                    )
                    arg_end = context.offset_map.pos_to_py(
                        arg_node.end_lineno, arg_node.end_col_offset + 1
                    )
                    arg_range = context.offset_map.span_to_range(arg_start, arg_end)
                    edit = Edit(range=arg_range, new_text=f"markupsafe.escape({arg_seg})")
                    import_edits = ensure_import_python(context.source, "import markupsafe")
                    return [
                        Fix(
                            id=f"fix-{finding.id}-1",
                            finding_id=finding.id,
                            title="Escape dynamic content with markupsafe.escape",
                            description="Escapes HTML metacharacters to prevent Cross-Site Scripting (XSS).",
                            confidence="review",
                            kind="rule",
                            edits=[*import_edits, edit],
                            verification=_create_initial_verification(),
                        )
                    ]
        return []


def register_python_fix_generators() -> None:
    """Register all Python fix generators into the global FIX_REGISTRY."""
    # Unicode fixes
    FIX_REGISTRY.register("APS-ALL-UNI-001", UnicodeBidiFixGenerator())
    FIX_REGISTRY.register("APS-ALL-UNI-002", UnicodeInvisibleFixGenerator())
    FIX_REGISTRY.register("APS-ALL-UNI-003", UnicodeTagFixGenerator())
    FIX_REGISTRY.register("APS-ALL-UNI-004", UnicodeConfusableFixGenerator())
    FIX_REGISTRY.register("APS-ALL-UNI-006", UnicodeConfusableFixGenerator())

    # Python security fixes
    FIX_REGISTRY.register("APS-PY-INJ-001", EvalFixGenerator())
    FIX_REGISTRY.register("APS-PY-INJ-002", OsSystemFixGenerator())
    FIX_REGISTRY.register("APS-PY-INJ-003", SubprocessShellFixGenerator())
    FIX_REGISTRY.register("APS-PY-INJ-004", SqlInjectionFixGenerator())
    FIX_REGISTRY.register("APS-PY-DES-001", PickleAdviceFixGenerator())
    FIX_REGISTRY.register("APS-PY-DES-002", YamlLoadFixGenerator())
    FIX_REGISTRY.register("APS-PY-CRY-001", HashlibFixGenerator())
    FIX_REGISTRY.register("APS-PY-CRY-002", RandomModuleFixGenerator())
    FIX_REGISTRY.register("APS-PY-SEC-001", HardcodedSecretFixGenerator())
    FIX_REGISTRY.register("APS-PY-NET-001", RequestsVerifyFixGenerator())
    FIX_REGISTRY.register("APS-PY-IO-001", PathTraversalFixGenerator())
    FIX_REGISTRY.register("APS-PY-XSS-001", XssEscapeFixGenerator())


# Register upon import
register_python_fix_generators()
