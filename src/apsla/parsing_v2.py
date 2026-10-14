"""Language parser adapters and bounded, navigable AST serialization."""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from apsla.lexing.common import OffsetMap
from apsla.models import Range
from apsla.models_v2 import DiagnosticV2, TokenV2, ToolStatus, token_type_for


class ASTNodeV2(BaseModel):
    id: str
    type: str
    field_name: str | None = None
    range: Range
    parent_id: str | None = None
    child_ids: list[str] = Field(default_factory=list)
    text_preview: str
    token_ids: list[str] = Field(default_factory=list)
    finding_ids: list[str] = Field(default_factory=list)


class ASTViewV2(BaseModel):
    root_id: str
    nodes: list[ASTNodeV2]
    truncated: bool
    node_limit: int
    depth_limit: int


@dataclass
class ParseOutcome:
    language: str
    parser_name: str
    tree_kind: str
    tree: Any | None
    source: str
    diagnostics: list[DiagnosticV2]
    tools: list[ToolStatus]
    status: str
    reason: str | None = None
    started: float = field(default_factory=time.perf_counter)


@dataclass
class _AstStore:
    outcome: ParseOutcome
    analysis_id: str
    tokens: list[TokenV2]
    diagnostics: list[DiagnosticV2]
    refs: dict[str, tuple[Any, str | None, str | None, str]] = field(default_factory=dict)


_AST_STORES: OrderedDict[str, _AstStore] = OrderedDict()
_AST_LOCK = threading.RLock()
_MAX_AST_STORES = 24
_GRAMMAR_MODULES = {
    "python": "tree_sitter_python",
    "java": "tree_sitter_java",
    "javascript": "tree_sitter_javascript",
    "cpp": "tree_sitter_cpp",
    "c": "tree_sitter_c",
}


def _byte_map(source: str) -> list[int]:
    offsets = [0]
    current = 0
    for char in source:
        current += len(char.encode("utf-8"))
        offsets.append(current)
    return offsets


def _byte_to_py(offsets: list[int], byte_offset: int) -> int:
    import bisect

    return min(bisect.bisect_right(offsets, byte_offset) - 1, len(offsets) - 1)


def _range_from_py(offset_map: OffsetMap, start: int, end: int) -> Range:
    start_line, start_col = offset_map.py_to_pos(start)
    end_line, end_col = offset_map.py_to_pos(end)
    return Range(start_line=start_line, start_col=start_col, end_line=end_line, end_col=end_col)


def _range_from_ts(source: str, offsets: OffsetMap, bytes_map: list[int], node: Any) -> Range:
    return _range_from_py(
        offsets,
        _byte_to_py(bytes_map, node.start_byte),
        _byte_to_py(bytes_map, node.end_byte),
    )


def _syntax_error_from_python(source: str, language: str, analysis_id: str, exc: SyntaxError) -> DiagnosticV2:
    offsets = OffsetMap(source)
    line = max(1, exc.lineno or 1)
    line_text = source.splitlines()[line - 1] if source.splitlines() and line <= len(source.splitlines()) else ""
    # CPython reports UTF-8 byte columns for AST nodes; SyntaxError.offset is a
    # human-oriented column. Convert its code-point prefix to editor UTF-16.
    column_cp = max(0, (exc.offset or 1) - 1)
    column_cp = min(column_cp, len(line_text))
    start_py = sum(len(part) for part in source.splitlines(keepends=True)[: line - 1]) + column_cp
    start_line, start_col = offsets.py_to_pos(start_py)
    end_line, end_col = offsets.py_to_pos(min(start_py + 1, len(source)))
    stable = hashlib.sha256(f"{analysis_id}:python-syntax:{line}:{column_cp}:{exc.msg}".encode()).hexdigest()[:20]
    return DiagnosticV2(
        id=f"syntax-{stable}", language=language,
        range=Range(start_line=start_line, start_col=start_col, end_line=end_line, end_col=end_col),
        category="syntax", severity="error", message=exc.msg,
        related_evidence=[f"{exc.__class__.__name__}: {exc.text.rstrip() if exc.text else line_text}"],
        produced_by="python.ast", certainty="definitive",
    )


def _tree_sitter_diagnostics(source: str, language: str, analysis_id: str, tree: Any) -> list[DiagnosticV2]:
    offsets = OffsetMap(source)
    byte_offsets = _byte_map(source)
    output: list[DiagnosticV2] = []
    stack = [tree.root_node]
    while stack and len(output) < 250:
        node = stack.pop()
        if getattr(node, "is_missing", False):
            expected = {
                ";": "expected ';'",
                ")": "missing ')'",
                "}": "missing '}'",
                "]": "missing ']'",
                "(": "missing '('",
            }.get(node.type, f"expected {node.type!r}")
            issue_type = "missing"
            message = expected
        elif getattr(node, "is_error", False) or node.type == "ERROR":
            raw = source[_byte_to_py(byte_offsets, node.start_byte):_byte_to_py(byte_offsets, node.end_byte)]
            printable = raw[:40].replace("\n", "\\n").replace("\r", "\\r")
            issue_type = "error"
            message = f"unexpected {printable!r}" if printable else "unexpected syntax"
        else:
            issue_type = ""
            message = ""
        if issue_type:
            rng = _range_from_ts(source, offsets, byte_offsets, node)
            parent_context = node.parent.type if node.parent is not None else node.type
            evidence = source[max(0, _byte_to_py(byte_offsets, node.start_byte) - 32): min(len(source), _byte_to_py(byte_offsets, node.end_byte) + 32)]
            stable = hashlib.sha256(
                f"{analysis_id}:{node.start_byte}:{node.end_byte}:{node.type}:{issue_type}".encode()
            ).hexdigest()[:20]
            output.append(DiagnosticV2(
                id=f"syntax-{stable}", language=language, range=rng,
                category="syntax", severity="error", message=message,
                related_evidence=[f"node={node.type}; parent={parent_context}; context={evidence!r}"],
                produced_by=f"tree-sitter-{language}", certainty="incomplete",
            ))
        stack.extend(reversed(node.children))
    return output


def _tree_sitter(language: str, source: str) -> tuple[Any | None, str | None]:
    module_name = _GRAMMAR_MODULES.get(language)
    if module_name is None:
        return None, f"No tree-sitter grammar is configured for {language}."
    try:
        from tree_sitter import Language, Parser

        grammar = importlib.import_module(module_name)
        parser = Parser(Language(grammar.language()))
        return parser.parse(source.encode("utf-8")), None
    except ImportError as exc:
        return None, f"Required parser package is unavailable: {exc.name or type(exc).__name__}."
    except Exception as exc:
        return None, f"Parser could not load or parse this source ({type(exc).__name__})."


def parser_capability(language: str) -> dict[str, object]:
    if language == "python":
        _, reason = _tree_sitter(language, "")
        return {
            "name": "python.ast",
            "available": True,
            "fallback": "tree-sitter-python",
            "fallback_available": reason is None,
            "reason": reason,
        }
    _, reason = _tree_sitter(language, "")
    return {
        "name": f"tree-sitter-{language}",
        "available": reason is None,
        "reason": reason,
    }


def parse_source(language: str, source: str, analysis_id: str) -> ParseOutcome:
    """Parse source with native Python AST plus recovery, or its tree-sitter grammar."""
    started = time.perf_counter()
    if language == "python":
        try:
            python_tree = ast.parse(source)
            elapsed = (time.perf_counter() - started) * 1000
            return ParseOutcome(
                language, "python.ast", "python_ast", python_tree, source, [],
                [ToolStatus(name="python.ast", kind="parser", available=True, executed=True, duration_ms=elapsed, status="ok")], "ok",
            )
        except (SyntaxError, IndentationError, TabError) as exc:
            diagnostic = _syntax_error_from_python(source, language, analysis_id, exc)
            partial_tree, reason = _tree_sitter(language, source)
            diagnostics: list[DiagnosticV2] = []
            elapsed = (time.perf_counter() - started) * 1000
            tools = [ToolStatus(name="python.ast", kind="parser", available=True, executed=True, duration_ms=elapsed, status="failed", reason=exc.__class__.__name__)]
            if partial_tree is not None:
                tools.append(ToolStatus(name="tree-sitter-python", kind="parser", available=True, executed=True, duration_ms=elapsed, status="ok" if not partial_tree.root_node.has_error else "failed"))
                diagnostics.extend(_tree_sitter_diagnostics(source, language, analysis_id, partial_tree))
                return ParseOutcome(language, "python.ast + tree-sitter-python", "tree_sitter", partial_tree, source, [diagnostic, *diagnostics], tools, "issues", "Python AST rejected the source; tree-sitter supplies a partial recovery tree.", started)
            tools.append(ToolStatus(name="tree-sitter-python", kind="parser", available=False, status="unavailable", reason=reason))
            return ParseOutcome(language, "python.ast", "none", None, source, [diagnostic], tools, "issues", reason, started)
    syntax_tree, reason = _tree_sitter(language, source)
    elapsed = (time.perf_counter() - started) * 1000
    if syntax_tree is None:
        return ParseOutcome(language, f"tree-sitter-{language}", "none", None, source, [], [ToolStatus(name=f"tree-sitter-{language}", kind="parser", available=False, status="unavailable", reason=reason)], "unavailable", reason, started)
    errors = _tree_sitter_diagnostics(source, language, analysis_id, syntax_tree)
    has_errors = bool(errors) or syntax_tree.root_node.has_error
    tool = ToolStatus(name=f"tree-sitter-{language}", kind="parser", available=True, executed=True, duration_ms=elapsed, status="failed" if has_errors else "ok")
    return ParseOutcome(language, f"tree-sitter-{language}", "tree_sitter", syntax_tree, source, errors, [tool], "issues" if has_errors else "ok", "Tree-sitter recovery is incomplete and does not establish semantic correctness." if has_errors else None, started)


_SEMANTIC_TOOLS = {
    "python": ("ruff", "pyflakes", "mypy"),
    "cpp": ("g++", "clang++"),
    "java": ("javac",),
    "javascript": ("node", "eslint"),
}


def _tool_range(source: str, line: int, column: int, end_line: int | None = None, end_column: int | None = None) -> Range:
    offsets = OffsetMap(source)
    lines = source.splitlines(keepends=True)
    start_line = min(max(line, 1), max(len(lines), 1))
    start_text = lines[start_line - 1] if lines else ""
    start_cp = _byte_to_py(_byte_map(start_text), max(column - 1, 0))
    start_py = sum(len(part) for part in lines[: start_line - 1]) + start_cp
    finish_line = min(max(end_line or line, 1), max(len(lines), 1))
    finish_text = lines[finish_line - 1] if lines else ""
    finish_cp = _byte_to_py(_byte_map(finish_text), max((end_column or column) - 1, 0))
    finish_py = sum(len(part) for part in lines[: finish_line - 1]) + finish_cp
    return _range_from_py(offsets, start_py, max(start_py, finish_py))


def _tool_diagnostics(name: str, language: str, source: str, payload: dict[str, object], analysis_id: str) -> list[DiagnosticV2]:
    raw = payload.get("parsed")
    if name in {"ruff", "eslint", "bandit"} and isinstance(raw, list):
        diagnostics: list[DiagnosticV2] = []
        items: list[dict[str, Any]] = []
        for entry in raw:
            if name == "eslint" and isinstance(entry, dict):
                for message in entry.get("messages", []):
                    if isinstance(message, dict):
                        items.append(message)
            elif isinstance(entry, dict):
                items.append(entry)
        for index, item in enumerate(items):
            location = item.get("location") or {}
            line = int(location.get("row") or item.get("line") or item.get("lineNumber") or 1)
            column = int(location.get("column") or item.get("column") or 1)
            end_location = item.get("end_location") or {}
            end_line = int(end_location.get("row") or item.get("endLine") or line)
            end_column = int(end_location.get("column") or item.get("endColumn") or column + 1)
            message = str(item.get("message") or item.get("description") or item.get("ruleId") or "Analyzer diagnostic")
            stable = hashlib.sha256(f"{analysis_id}:{name}:{line}:{column}:{index}:{message}".encode()).hexdigest()[:20]
            diagnostics.append(DiagnosticV2(
                id=f"semantic-{stable}", language=language,
                range=_tool_range(source, line, column, end_line, end_column),
                category="semantic", severity=str(item.get("severity", "warning")),
                message=message, related_evidence=[json.dumps(item, ensure_ascii=False)[:1000]],
                produced_by=name, certainty="heuristic" if name in {"ruff", "eslint", "bandit"} else "definitive",
            ))
        return diagnostics
    text = str(payload.get("stderr") or payload.get("stdout") or "")
    diagnostics = []
    pattern = re.compile(r"(?:^|\n).+?:(\d+):(?:(\d+):)?\s*(?:(error|warning|note):\s*)?(.*)")
    for index, match in enumerate(pattern.finditer(text)):
        line, column = int(match.group(1)), int(match.group(2) or 1)
        severity, message = match.group(3) or "error", match.group(4).strip()
        stable = hashlib.sha256(f"{analysis_id}:{name}:{line}:{column}:{index}:{message}".encode()).hexdigest()[:20]
        diagnostics.append(DiagnosticV2(
            id=f"semantic-{stable}", language=language,
            range=_tool_range(source, line, column), category="semantic",
            severity=severity, message=message,
            related_evidence=[match.group(0).strip()[:1000]], produced_by=name,
            certainty="heuristic" if name == "mypy" else "definitive",
        ))
    return diagnostics


def run_semantic_checks(language: str, source: str, analysis_id: str) -> tuple[list[DiagnosticV2], list[ToolStatus], list[str]]:
    """Attempt only allowlisted static tools; never execute submitted source."""
    from apsla.server.tool_runner import execute_static_tool
    from apsla.status_wording import CHECK_UNAVAILABLE

    diagnostics: list[DiagnosticV2] = []
    statuses: list[ToolStatus] = []
    warnings: list[str] = []
    for name in _SEMANTIC_TOOLS.get(language, ()):
        status, payload = execute_static_tool(name, source, language)
        statuses.append(status)
        diagnostics.extend(_tool_diagnostics(name, language, source, payload, analysis_id))
        if status.status in {"unavailable", "timeout"}:
            warnings.append(f"{CHECK_UNAVAILABLE} {name}: {status.reason or status.status}.")
    return diagnostics, statuses, warnings


def _ast_children(node: Any, tree_kind: str) -> list[tuple[Any, str | None]]:
    if tree_kind == "tree_sitter":
        return [
            (child, node.field_name_for_child(index))
            for index, child in enumerate(node.children)
        ]
    children: list[tuple[Any, str | None]] = []
    for field_name, value in ast.iter_fields(node):
        if isinstance(value, ast.AST):
            children.append((value, field_name))
        elif isinstance(value, list):
            children.extend((item, field_name) for item in value if isinstance(item, ast.AST))
    return children


def _node_span(store: _AstStore, node: Any) -> tuple[int, int, str]:
    source = store.outcome.source
    if store.outcome.tree_kind == "tree_sitter":
        if hasattr(node, "root_node"):
            node = node.root_node
        bmap = _byte_map(source)
        start = _byte_to_py(bmap, node.start_byte)
        end = _byte_to_py(bmap, node.end_byte)
    else:
        if isinstance(node, ast.Module):
            return 0, len(source), source
        lines = source.splitlines(keepends=True)
        start_line = max(1, getattr(node, "lineno", 1))
        end_line = max(start_line, getattr(node, "end_lineno", start_line))
        start_byte_col = getattr(node, "col_offset", 0)
        end_byte_col = getattr(node, "end_col_offset", start_byte_col)
        start_text = lines[start_line - 1] if start_line <= len(lines) else ""
        end_text = lines[end_line - 1] if end_line <= len(lines) else ""
        start_col = _byte_to_py(_byte_map(start_text), start_byte_col)
        end_col = _byte_to_py(_byte_map(end_text), end_byte_col)
        start = sum(len(line) for line in lines[: start_line - 1]) + start_col
        end = sum(len(line) for line in lines[: end_line - 1]) + end_col
    return start, end, source[start:end]


def _node_type(node: Any, tree_kind: str) -> str:
    return node.type if tree_kind == "tree_sitter" else type(node).__name__


def _id(store: _AstStore, parent_id: str | None, index: int, node: Any) -> str:
    start, end, _ = _node_span(store, node)
    material = f"{store.analysis_id}:{parent_id or 'root'}:{index}:{_node_type(node, store.outcome.tree_kind)}:{start}:{end}"
    return "ast-" + hashlib.sha256(material.encode()).hexdigest()[:20]


def _register(store: _AstStore, node: Any, node_id: str, parent_id: str | None, field_name: str | None) -> None:
    store.refs[node_id] = (node, parent_id, field_name, node_id)


def _serialize_node(store: _AstStore, node: Any, node_id: str, parent_id: str | None, field_name: str | None, tokens: list[TokenV2], diagnostics: list[DiagnosticV2]) -> ASTNodeV2:
    start, end, text = _node_span(store, node)
    offsets = OffsetMap(store.outcome.source)
    rng = _range_from_py(offsets, start, end)
    token_ids = [token.id for token in tokens if (token.start_offset_codepoint < end and token.end_offset_codepoint > start) or (start == end == token.start_offset_codepoint)]
    def intersects(item: DiagnosticV2) -> bool:
        return (item.range.start_line < rng.end_line or
                (item.range.start_line == rng.end_line and item.range.start_col < rng.end_col)) and (
                    item.range.end_line > rng.start_line or
                    (item.range.end_line == rng.start_line and item.range.end_col > rng.start_col)
                )

    finding_ids = [item.id for item in diagnostics if intersects(item)]
    child_ids: list[str] = []
    for index, (child, child_field) in enumerate(_ast_children(node, store.outcome.tree_kind)):
        child_id = _id(store, node_id, index, child)
        child_ids.append(child_id)
        if child_id not in store.refs:
            _register(store, child, child_id, node_id, child_field)
    preview = " ".join(text.split())[:160]
    return ASTNodeV2(id=node_id, type=_node_type(node, store.outcome.tree_kind), field_name=field_name, range=rng, parent_id=parent_id, child_ids=child_ids, text_preview=preview, token_ids=token_ids, finding_ids=finding_ids)


def build_ast_view(outcome: ParseOutcome, analysis_id: str, tokens: list[TokenV2], diagnostics: list[DiagnosticV2], *, max_depth: int = 8, max_nodes: int = 500, root_id: str | None = None) -> ASTViewV2 | None:
    if outcome.tree is None:
        return None
    store = _AST_STORES.get(analysis_id)
    if store is None:
        root = outcome.tree
        if outcome.tree_kind == "tree_sitter" and hasattr(root, "root_node"):
            root = root.root_node
        store = _AstStore(outcome, analysis_id, tokens, diagnostics)
        root_id_value = _id(store, None, 0, root)
        _register(store, root, root_id_value, None, None)
        with _AST_LOCK:
            _AST_STORES[analysis_id] = store
            _AST_STORES.move_to_end(analysis_id)
            while len(_AST_STORES) > _MAX_AST_STORES:
                _AST_STORES.popitem(last=False)
    if root_id is None:
        node, parent_id, field_name, node_id = next(iter(store.refs.values()))
    else:
        ref = store.refs.get(root_id)
        if ref is None:
            return None
        node, parent_id, field_name, node_id = ref
    serialized: list[ASTNodeV2] = []
    truncated = False

    def visit(current: Any, current_id: str, parent: str | None, field: str | None, depth: int) -> None:
        nonlocal truncated
        if len(serialized) >= max_nodes:
            truncated = True
            return
        item = _serialize_node(store, current, current_id, parent, field, tokens, diagnostics)
        serialized.append(item)
        if item.child_ids and depth >= max_depth:
            truncated = True
            return
        for index, (child, child_field) in enumerate(_ast_children(current, outcome.tree_kind)):
            if len(serialized) >= max_nodes:
                truncated = True
                break
            child_id = item.child_ids[index]
            visit(child, child_id, current_id, child_field, depth + 1)

    visit(node, node_id, parent_id, field_name, 0)
    return ASTViewV2(root_id=node_id, nodes=serialized, truncated=truncated, node_limit=max_nodes, depth_limit=max_depth)


def ast_store_contains(analysis_id: str, node_id: str) -> bool:
    store = _AST_STORES.get(analysis_id)
    return bool(store and node_id in store.refs)


def build_token_projection(plugin: Any, source: str, language: str, analysis_id: str) -> list[TokenV2]:
    offsets = OffsetMap(source)
    result: list[TokenV2] = []
    try:
        raw_tokens = plugin.lex(source)
    except Exception:
        return result
    public_index = 0
    for raw in raw_tokens:
        mapped = token_type_for(language, raw.kind, raw.text)
        if mapped is None:
            continue
        token_type, category = mapped
        digest = hashlib.sha256(
            f"{analysis_id}:{public_index}:{raw.start}:{raw.end}:{raw.text}".encode()
        ).hexdigest()[:24]
        result.append(TokenV2(
            id=digest, language=language, lexeme=raw.text, token_type=token_type,
            category=category, start_offset=raw.start, end_offset=raw.end,
            start_offset_codepoint=offsets.utf16_to_py(raw.start),
            end_offset_codepoint=offsets.utf16_to_py(raw.end), start_line=raw.line,
            start_column=raw.col, end_line=raw.end_line, end_column=raw.end_col,
            lexical_status="invalid" if token_type == "INVALID_TOKEN" else "valid",
        ))
        public_index += 1
    return result


def ast_node_view(analysis_id: str, node_id: str, *, max_depth: int = 3, max_nodes: int = 100) -> ASTViewV2 | None:
    store = _AST_STORES.get(analysis_id)
    if store is None or node_id not in store.refs:
        return None
    return build_ast_view(
        store.outcome, analysis_id, store.tokens, store.diagnostics,
        max_depth=max_depth, max_nodes=max_nodes, root_id=node_id,
    )
