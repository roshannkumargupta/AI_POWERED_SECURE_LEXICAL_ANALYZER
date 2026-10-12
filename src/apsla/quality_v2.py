"""Measured syntax-tree quality observations; no runtime claims are made."""

from __future__ import annotations

import ast
import hashlib
from typing import Any

from apsla.lexing.common import OffsetMap
from apsla.models import Range
from apsla.models_v2 import QualityObservationV2

_DECISIONS = {"if_statement", "if_expression", "conditional_expression", "for_statement", "for_in_statement", "while_statement", "catch_clause", "case_clause", "elif_clause", "conditional", "boolean_operator"}


def _py_range(source: str, node: ast.AST) -> Range:
    offsets = OffsetMap(source)
    lines = source.splitlines(keepends=True)
    start_line = max(1, getattr(node, "lineno", 1))
    end_line = max(1, getattr(node, "end_lineno", start_line))
    start = sum(len(line) for line in lines[: start_line - 1]) + len(lines[start_line - 1].encode("utf-8")[: getattr(node, "col_offset", 0)].decode("utf-8", "ignore"))
    end = sum(len(line) for line in lines[: end_line - 1]) + len(lines[end_line - 1].encode("utf-8")[: getattr(node, "end_col_offset", 0)].decode("utf-8", "ignore"))
    sl, sc = offsets.py_to_pos(start)
    el, ec = offsets.py_to_pos(end)
    return Range(start_line=sl, start_col=sc, end_line=el, end_col=ec)


def _ts_range(source: str, node: Any) -> Range:
    offsets = OffsetMap(source)
    starts = source.splitlines(keepends=True)
    sr, sb = node.start_point
    er, eb = node.end_point
    start_py = sum(len(x) for x in starts[:sr]) + len(starts[sr].encode("utf-8")[:sb].decode("utf-8", "ignore"))
    end_py = sum(len(x) for x in starts[:er]) + len(starts[er].encode("utf-8")[:eb].decode("utf-8", "ignore"))
    sl, sc = offsets.py_to_pos(min(start_py, len(source)))
    el, ec = offsets.py_to_pos(min(end_py, len(source)))
    return Range(start_line=sl, start_col=sc, end_line=el, end_col=ec)


def measure_quality(language: str, source: str, tree: Any | None) -> list[QualityObservationV2]:
    """Measure function complexity, line length, nesting and parameters from parser trees."""
    if tree is None:
        return []
    functions: list[tuple[Any, str, list[Any]]] = []
    if isinstance(tree, ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                functions.append((node, getattr(node, "name", "<lambda>"), list(ast.walk(node))))
    else:
        root = tree.root_node if hasattr(tree, "root_node") else tree
        stack = [root]
        while stack:
            node = stack.pop()
            if "function" in node.type or node.type in {"method_declaration", "constructor_declaration", "arrow_function", "method_definition"}:
                descendants = []
                todo = [node]
                while todo:
                    child = todo.pop()
                    descendants.append(child)
                    todo.extend(child.children)
                functions.append((node, node.type, descendants))
            stack.extend(node.children)
    observations: list[QualityObservationV2] = []
    for index, (node, name, descendants) in enumerate(functions):
        is_python = isinstance(node, ast.AST)
        rng = _py_range(source, node) if is_python else _ts_range(source, node)
        def counts_decision(child: Any, py_tree: bool = is_python) -> bool:
            if py_tree:
                return isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp, ast.BoolOp))
            if child.type in _DECISIONS:
                return True
            return child.type == "binary_expression" and any(
                part.type in {"&&", "||", "and", "or"} for part in child.children
            )

        decision_count = sum(
            max(1, len(child.values) - 1)
            if is_python and isinstance(child, ast.BoolOp)
            else int(counts_decision(child))
            for child in descendants
        )
        complexity = 1 + decision_count
        if is_python:
            fn = node
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = len(fn.args.posonlyargs) + len(fn.args.args) + len(fn.args.kwonlyargs) + int(fn.args.vararg is not None) + int(fn.args.kwarg is not None)
            else:
                params = len(fn.args.args)
        else:
            params_node = next((child for child in node.children if "parameter" in child.type), None)
            params = len(params_node.named_children) if params_node is not None else 0
        span = max(1, rng.end_line - rng.start_line + 1)
        depths: list[int] = []
        def visit(
            cur: Any, depth: int, py_tree: bool = is_python, depth_values: list[int] = depths
        ) -> None:
            depth_values.append(depth)
            children = list(ast.iter_child_nodes(cur)) if py_tree else cur.children
            for child in children:
                decision = isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try)) if py_tree else counts_decision(child)
                visit(child, depth + (1 if decision else 0), py_tree)
        visit(node, 0)
        nesting = max(depths, default=0)
        ident = hashlib.sha256(f"{language}:{name}:{rng.start_line}:{rng.start_col}:{index}".encode()).hexdigest()[:18]
        for kind, value, evidence in (
            ("cyclomatic_complexity", complexity, ["base complexity 1 plus counted decision nodes"]),
            ("function_length", span, ["inclusive source line span"]),
            ("nesting_depth", nesting, ["maximum nested decision depth"]),
            ("parameter_count", params, ["declared parameter nodes"]),
        ):
            observations.append(QualityObservationV2(id=f"quality-{ident}-{kind}", kind=kind, range=rng, value=value, evidence=[name, *evidence], measured=True))
    return observations
