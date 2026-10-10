"""Lightweight Structure Tree (StructTree) representation for SecureLex IDE.

Provides concrete AST-like structural nodes across Java, JavaScript, and C++
without requiring heavy compiler frontends or external grammar tools.
Coordinates are strictly 1-indexed line/column in UTF-16 code units for
seamless editor and Monaco compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from apsla.models import Range


class NodeKind(StrEnum):
    """Categorical node kinds for lightweight program structure trees."""

    FILE = "File"
    CLASS = "Class"
    STRUCT = "Struct"
    FUNCTION = "Function"
    METHOD = "Method"
    BLOCK = "Block"
    STATEMENT = "Statement"
    ASSIGNMENT = "Assignment"
    CALL = "Call"
    RETURN = "Return"
    IMPORT = "Import"
    INCLUDE = "Include"
    ERROR = "Error"


@dataclass
class StructNode:
    """Base class for all lightweight structural syntax nodes."""

    kind: NodeKind
    range: Range
    text: str = ""
    name: str = ""
    children: list[StructNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert node and descendants to JSON-serializable dictionary."""
        data: dict[str, Any] = {
            "kind": self.kind.value,
            "range": {
                "start_line": self.range.start_line,
                "start_col": self.range.start_col,
                "end_line": self.range.end_line,
                "end_col": self.range.end_col,
            },
        }
        if self.name:
            data["name"] = self.name
        if self.text:
            data["text"] = self.text
        if self.children:
            data["children"] = [child.to_dict() for child in self.children]
        return data


@dataclass
class FileNode(StructNode):
    """Top-level translation unit node."""

    language: str = ""

    def __init__(
        self, range: Range, language: str = "", children: list[StructNode] | None = None
    ) -> None:
        super().__init__(kind=NodeKind.FILE, range=range, children=children or [])
        self.language = language


@dataclass
class ClassNode(StructNode):
    """Class or struct definition container."""

    is_struct: bool = False
    modifiers: list[str] = field(default_factory=list)

    def __init__(
        self,
        name: str,
        range: Range,
        is_struct: bool = False,
        modifiers: list[str] | None = None,
        children: list[StructNode] | None = None,
    ) -> None:
        kind = NodeKind.STRUCT if is_struct else NodeKind.CLASS
        super().__init__(kind=kind, range=range, name=name, children=children or [])
        self.is_struct = is_struct
        self.modifiers = modifiers or []


@dataclass
class FunctionNode(StructNode):
    """Function, method, or constructor declaration."""

    params: list[str] = field(default_factory=list)
    return_type: str = ""
    is_method: bool = False
    modifiers: list[str] = field(default_factory=list)

    def __init__(
        self,
        name: str,
        range: Range,
        params: list[str] | None = None,
        return_type: str = "",
        is_method: bool = False,
        modifiers: list[str] | None = None,
        children: list[StructNode] | None = None,
    ) -> None:
        kind = NodeKind.METHOD if is_method else NodeKind.FUNCTION
        super().__init__(kind=kind, range=range, name=name, children=children or [])
        self.params = params or []
        self.return_type = return_type
        self.is_method = is_method
        self.modifiers = modifiers or []

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["params"] = self.params
        if self.return_type:
            data["return_type"] = self.return_type
        return data


@dataclass
class BlockNode(StructNode):
    """Brace-delimited code block { ... }."""

    def __init__(self, range: Range, children: list[StructNode] | None = None) -> None:
        super().__init__(kind=NodeKind.BLOCK, range=range, children=children or [])


@dataclass
class StatementNode(StructNode):
    """General statement bounded by semicolon or block delimiter."""

    def __init__(
        self, range: Range, text: str = "", children: list[StructNode] | None = None
    ) -> None:
        super().__init__(kind=NodeKind.STATEMENT, range=range, text=text, children=children or [])


@dataclass
class AssignmentNode(StructNode):
    """Variable declaration or assignment statement."""

    target: str = ""
    value_text: str = ""
    value_range: Range | None = None

    def __init__(
        self,
        target: str,
        range: Range,
        value_text: str = "",
        value_range: Range | None = None,
        children: list[StructNode] | None = None,
    ) -> None:
        super().__init__(
            kind=NodeKind.ASSIGNMENT,
            range=range,
            name=target,
            text=value_text,
            children=children or [],
        )
        self.target = target
        self.value_text = value_text
        self.value_range = value_range

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["target"] = self.target
        data["value_text"] = self.value_text
        return data


@dataclass
class CallNode(StructNode):
    """Function, method, or system call expression."""

    callee: str = ""
    args: list[Range] = field(default_factory=list)
    arg_texts: list[str] = field(default_factory=list)

    def __init__(
        self,
        callee: str,
        range: Range,
        args: list[Range] | None = None,
        arg_texts: list[str] | None = None,
        children: list[StructNode] | None = None,
    ) -> None:
        super().__init__(kind=NodeKind.CALL, range=range, name=callee, children=children or [])
        self.callee = callee
        self.args = args or []
        self.arg_texts = arg_texts or []

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["callee"] = self.callee
        data["args"] = [
            {
                "start_line": a.start_line,
                "start_col": a.start_col,
                "end_line": a.end_line,
                "end_col": a.end_col,
            }
            for a in self.args
        ]
        data["arg_texts"] = self.arg_texts
        return data


@dataclass
class ReturnNode(StructNode):
    """Return statement."""

    value_text: str = ""
    value_range: Range | None = None

    def __init__(
        self,
        range: Range,
        value_text: str = "",
        value_range: Range | None = None,
        children: list[StructNode] | None = None,
    ) -> None:
        super().__init__(
            kind=NodeKind.RETURN, range=range, text=value_text, children=children or []
        )
        self.value_text = value_text
        self.value_range = value_range


@dataclass
class ImportNode(StructNode):
    """Module import or header include directive."""

    module: str = ""
    names: list[str] = field(default_factory=list)
    is_include: bool = False

    def __init__(
        self,
        module: str,
        range: Range,
        names: list[str] | None = None,
        is_include: bool = False,
        children: list[StructNode] | None = None,
    ) -> None:
        kind = NodeKind.INCLUDE if is_include else NodeKind.IMPORT
        super().__init__(kind=kind, range=range, name=module, children=children or [])
        self.module = module
        self.names = names or []
        self.is_include = is_include

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["module"] = self.module
        if self.names:
            data["names"] = self.names
        return data


@dataclass
class ErrorNode(StructNode):
    """Syntactic breakdown recorded during panic-mode recovery."""

    message: str = ""
    unexpected_token: str = ""

    def __init__(
        self,
        message: str,
        range: Range,
        unexpected_token: str = "",
    ) -> None:
        super().__init__(kind=NodeKind.ERROR, range=range, name=unexpected_token, text=message)
        self.message = message
        self.unexpected_token = unexpected_token

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["message"] = self.message
        data["unexpected_token"] = self.unexpected_token
        return data


@dataclass
class StructTree:
    """Complete structural tree with query indices and quality score."""

    root: FileNode
    language: str
    errors: list[ErrorNode] = field(default_factory=list)
    calls: list[CallNode] = field(default_factory=list)
    functions: list[FunctionNode] = field(default_factory=list)
    classes: list[ClassNode] = field(default_factory=list)
    assignments: list[AssignmentNode] = field(default_factory=list)
    imports: list[ImportNode] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if the tree contains zero error nodes."""
        return len(self.errors) == 0

    @property
    def quality_score(self) -> float:
        """Structure quality score in [0.0, 1.0]."""
        if not self.errors:
            return 1.0
        return max(0.0, 1.0 - (0.2 * len(self.errors)))

    def find_function_at(self, line: int, col: int) -> FunctionNode | None:
        """Find the innermost function containing the given coordinate."""
        for fn in reversed(self.functions):
            r = fn.range
            if r.start_line <= line <= r.end_line:
                if (line == r.start_line and col < r.start_col) or (
                    line == r.end_line and col > r.end_col
                ):
                    continue
                return fn
        return None

    def find_enclosing_scope(self, line: int, col: int) -> StructNode:
        """Find the most specific enclosing structural node."""
        fn = self.find_function_at(line, col)
        if fn:
            return fn
        for cls in reversed(self.classes):
            r = cls.range
            if r.start_line <= line <= r.end_line:
                return cls
        return self.root

    def to_dict(self) -> dict[str, Any]:
        """Serialize tree to nested dictionary."""
        return {
            "language": self.language,
            "is_valid": self.is_valid,
            "quality_score": round(self.quality_score, 3),
            "errors_count": len(self.errors),
            "calls_count": len(self.calls),
            "functions_count": len(self.functions),
            "classes_count": len(self.classes),
            "root": self.root.to_dict(),
        }
