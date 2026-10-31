"""Workspace File Management API for SecureLex IDE.

Provides safe, sandboxed file tree, read, write, create, rename, and delete operations
restricted to the project's workspace directory.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Define workspace root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"

workspace_router = APIRouter(prefix="/workspace", tags=["workspace"])

LANGUAGE_EXTENSIONS = {
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".py": "python",
    ".pyw": "python",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".json": "json",
    ".md": "markdown",
    ".txt": "text",
}

DEFAULT_FILES = {
    "src/main.cpp": (
        "#include <iostream>\n"
        "using namespace std;\n\n"
        "int main() {\n"
        "    int n = 5;\n"
        "    for (int i = 0; i \ufeff<= n; i++) {\n"
        '        cout << i << " ";\n'
        "    }\n"
        "    cout << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "src/utils.cpp": (
        '#include "utils.h"\n'
        "#include <string>\n\n"
        "std::string stripBOM(const std::string& src) {\n"
        '    if (src.rfind("\\xEF\\xBB\\xBF", 0) == 0) {\n'
        "        return src.substr(3);\n"
        "    }\n"
        "    return src;\n"
        "}\n"
    ),
    "src/utils.h": (
        "#pragma once\n"
        "#include <string>\n\n"
        "std::string stripBOM(const std::string& src);\n"
    ),
    "sample.py": (
        "import unicodedata\n\n"
        "def validate_stream(code_str):\n"
        "    for ch in code_str:\n"
        "        if ord(ch) == 0xFEFF:\n"
        '            raise ValueError("Invisible Trojan sequence detected")\n'
        "    return True\n"
    ),
    "App.java": (
        "package com.securelex.analyzer;\n\n"
        "public class App {\n"
        "    public static void main(String[] args) {\n"
        '        System.out.println("SecureLex Java Agent initialized");\n'
        "    }\n"
        "}\n"
    ),
    "app.js": (
        "export function lexBuffer(input) {\n"
        "    const hasTrojan = /\\uFEFF/.test(input);\n"
        "    if (hasTrojan) {\n"
        '        console.warn("Security vulnerability flag: U+FEFF");\n'
        "    }\n"
        "    return !hasTrojan;\n"
        "}\n"
    ),
    "README.md": (
        "# SecureLex IDE\n"
        "AI-Powered Secure Lexical Analyzer and Compiler Pipeline.\n\n"
        "## Features\n"
        "- Trojan Source Detection (CVE-2021-42574)\n"
        "- ISO C++20 Lexer Verification\n"
    ),
}


def ensure_workspace_initialized() -> None:
    """Ensure the workspace directory exists and has initial project files."""
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    for rel_path, content in DEFAULT_FILES.items():
        file_path = WORKSPACE_ROOT / rel_path
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")


def resolve_safe_path(rel_path: str) -> Path:
    """Resolve and validate that the relative path strictly resides inside WORKSPACE_ROOT."""
    if not rel_path or "\x00" in rel_path:
        raise HTTPException(status_code=400, detail="Invalid path.")

    # Normalize slashes and strip leading/trailing whitespace
    clean = rel_path.replace("\\", "/").strip("/ ")
    parts = clean.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise HTTPException(status_code=403, detail="Path traversal is prohibited.")

    resolved = (WORKSPACE_ROOT / clean).resolve()
    try:
        resolved.relative_to(WORKSPACE_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Path falls outside workspace boundary.")

    return resolved


def detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    return LANGUAGE_EXTENSIONS.get(ext, "text")


class FileCreateRequest(BaseModel):
    path: str = Field(..., min_length=1)
    content: str = ""


class FileSaveRequest(BaseModel):
    path: str = Field(..., min_length=1)
    content: str


class RenameRequest(BaseModel):
    old_path: str = Field(..., min_length=1)
    new_path: str = Field(..., min_length=1)


class FolderCreateRequest(BaseModel):
    path: str = Field(..., min_length=1)


class FileItemResponse(BaseModel):
    name: str
    path: str
    type: str  # "file" | "directory"
    size: int | None = None
    language: str | None = None
    children: list[FileItemResponse] | None = None


class WorkspaceTreeResponse(BaseModel):
    root: str
    tree: list[FileItemResponse]


class FileDetailResponse(BaseModel):
    path: str
    name: str
    content: str
    language: str
    size: int
    last_modified: float


IGNORED_NAMES = {
    "__pycache__", "node_modules", ".git", ".idea", ".vscode", "dist", "build", "coverage", ".pytest_cache"
}
IGNORED_EXTS = {".pyc", ".pyo", ".pyd", ".tmp", ".swp", ".swo", ".bak"}


def is_ignored_item(path: Path | str) -> bool:
    p = Path(path) if isinstance(path, str) else path
    name = p.name
    if name.startswith(".") or name in IGNORED_NAMES:
        return True
    if any(name.endswith(ext) for ext in IGNORED_EXTS):
        return True
    return False


def build_tree_node(item_path: Path) -> FileItemResponse:
    rel_path = item_path.relative_to(WORKSPACE_ROOT).as_posix()
    if item_path.is_dir():
        children: list[FileItemResponse] = []
        for child in sorted(item_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if is_ignored_item(child):
                continue
            children.append(build_tree_node(child))
        return FileItemResponse(
            name=item_path.name,
            path=rel_path,
            type="directory",
            children=children,
        )
    else:
        stat = item_path.stat()
        return FileItemResponse(
            name=item_path.name,
            path=rel_path,
            type="file",
            size=stat.st_size,
            language=detect_language(item_path),
        )


@workspace_router.get("/tree", response_model=WorkspaceTreeResponse)
async def get_workspace_tree() -> WorkspaceTreeResponse:
    """Return the hierarchical tree of all files in the workspace."""
    ensure_workspace_initialized()
    items: list[FileItemResponse] = []
    for entry in sorted(WORKSPACE_ROOT.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if is_ignored_item(entry):
            continue
        items.append(build_tree_node(entry))
    return WorkspaceTreeResponse(root="SECURELEX-PROJECT", tree=items)


@workspace_router.get("/file", response_model=FileDetailResponse)
async def get_workspace_file(path: str = Query(..., description="Relative file path")) -> FileDetailResponse:
    """Read and return content of a file from workspace."""
    ensure_workspace_initialized()
    target = resolve_safe_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    stat = target.stat()
    if stat.st_size > 524288:  # 512 KB limit
        raise HTTPException(status_code=413, detail="File exceeds maximum size limit (512 KB).")

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = target.read_text(encoding="latin-1")

    rel_path = target.relative_to(WORKSPACE_ROOT).as_posix()
    return FileDetailResponse(
        path=rel_path,
        name=target.name,
        content=content,
        language=detect_language(target),
        size=stat.st_size,
        last_modified=stat.st_mtime,
    )


@workspace_router.post("/file")
async def create_workspace_file(req: FileCreateRequest) -> dict[str, Any]:
    """Create a new file in the workspace."""
    ensure_workspace_initialized()
    target = resolve_safe_path(req.path)
    if target.exists():
        raise HTTPException(status_code=409, detail="File already exists.")

    if len(req.content.encode("utf-8")) > 524288:
        raise HTTPException(status_code=413, detail="File content exceeds size limit.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    stat = target.stat()
    rel_path = target.relative_to(WORKSPACE_ROOT).as_posix()
    return {"success": True, "path": rel_path, "size": stat.st_size}


@workspace_router.post("/folder")
async def create_workspace_folder(req: FolderCreateRequest) -> dict[str, Any]:
    """Create a new folder in the workspace."""
    ensure_workspace_initialized()
    target = resolve_safe_path(req.path)
    if target.exists():
        raise HTTPException(status_code=409, detail="Folder already exists.")
    target.mkdir(parents=True, exist_ok=True)
    rel_path = target.relative_to(WORKSPACE_ROOT).as_posix()
    return {"success": True, "path": rel_path}


@workspace_router.put("/file")
async def save_workspace_file(req: FileSaveRequest) -> dict[str, Any]:
    """Save/update content of a file in the workspace."""
    ensure_workspace_initialized()
    target = resolve_safe_path(req.path)

    if len(req.content.encode("utf-8")) > 524288:
        raise HTTPException(status_code=413, detail="File content exceeds size limit.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    stat = target.stat()
    rel_path = target.relative_to(WORKSPACE_ROOT).as_posix()
    return {
        "success": True,
        "path": rel_path,
        "size": stat.st_size,
        "last_modified": stat.st_mtime,
    }


@workspace_router.delete("/file")
async def delete_workspace_file(path: str = Query(..., description="Relative path")) -> dict[str, Any]:
    """Delete a file or directory from the workspace."""
    ensure_workspace_initialized()
    target = resolve_safe_path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    if target.resolve() == WORKSPACE_ROOT.resolve():
        raise HTTPException(status_code=403, detail="Cannot delete root workspace directory.")

    if target.is_dir():
        import shutil
        shutil.rmtree(target)
    else:
        target.unlink()

    return {"success": True, "path": path}


@workspace_router.post("/rename")
async def rename_workspace_file(req: RenameRequest) -> dict[str, Any]:
    """Rename or move a file within the workspace."""
    ensure_workspace_initialized()
    source = resolve_safe_path(req.old_path)
    dest = resolve_safe_path(req.new_path)

    if not source.exists():
        raise HTTPException(status_code=404, detail="Source file not found.")
    if dest.exists():
        raise HTTPException(status_code=409, detail="Destination path already exists.")

    dest.parent.mkdir(parents=True, exist_ok=True)
    source.rename(dest)
    return {
        "success": True,
        "old_path": source.relative_to(WORKSPACE_ROOT).as_posix(),
        "new_path": dest.relative_to(WORKSPACE_ROOT).as_posix(),
    }


# ==============================================================================
# Project-Wide Search & Replace
# ==============================================================================

class SearchMatch(BaseModel):
    line: int
    col: int
    length: int
    line_text: str
    match_text: str


class FileSearchResult(BaseModel):
    file: str
    matches: list[SearchMatch]


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    file_count: int
    results: list[FileSearchResult]


@workspace_router.get("/search", response_model=SearchResponse)
async def search_workspace(
    query: str = Query(..., description="Search term or regex"),
    is_regex: bool = Query(False, description="Whether to treat query as regex"),
    match_case: bool = Query(False, description="Case-sensitive search"),
    match_whole_word: bool = Query(False, description="Whole word match"),
) -> SearchResponse:
    """Project-wide safe search across all workspace files."""
    ensure_workspace_initialized()
    if not query:
        return SearchResponse(query="", total_matches=0, file_count=0, results=[])

    # Convert Unicode codepoint notations like U+FEFF to actual characters if needed
    effective_queries: list[str] = [query]
    unicode_match = re.fullmatch(r"U\+([0-9A-Fa-f]{4,6})", query.strip())
    if unicode_match:
        try:
            char_repr = chr(int(unicode_match.group(1), 16))
            effective_queries.append(char_repr)
        except Exception:
            pass

    # Regex search patterns (tuple of pattern string and flags)
    flags = 0 if match_case else re.IGNORECASE
    compiled_patterns: list[tuple[str, int]] = []
    for q in effective_queries:
        try:
            if is_regex:
                pat_str = q
            else:
                pat_str = re.escape(q)
            if match_whole_word and not is_regex:
                pat_str = rf"\b{pat_str}\b"
            re.search(pat_str, "", flags)
            compiled_patterns.append((pat_str, flags))
        except re.error:
            # Fallback to literal search
            compiled_patterns.append((re.escape(q), flags))

    results: list[FileSearchResult] = []
    total_matches = 0

    # Walk through workspace files
    for root, _, files in os.walk(WORKSPACE_ROOT):
        for f in sorted(files):
            file_path = Path(root) / f
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            rel_path = file_path.relative_to(WORKSPACE_ROOT).as_posix()
            file_matches: list[SearchMatch] = []

            for line_idx, line_text in enumerate(content.splitlines(), start=1):
                seen_spans = set()
                for pat_str, pat_flags in compiled_patterns:
                    for m in re.finditer(pat_str, line_text, pat_flags):
                        span = m.span()
                        if span in seen_spans:
                            continue
                        seen_spans.add(span)
                        start_col = span[0] + 1
                        m_len = max(1, span[1] - span[0])
                        file_matches.append(
                            SearchMatch(
                                line=line_idx,
                                col=start_col,
                                length=m_len,
                                line_text=line_text,
                                match_text=m.group(0),
                            )
                        )

            if file_matches:
                # Sort matches by line and col
                file_matches.sort(key=lambda m: (m.line, m.col))
                results.append(FileSearchResult(file=rel_path, matches=file_matches))
                total_matches += len(file_matches)

    return SearchResponse(
        query=query,
        total_matches=total_matches,
        file_count=len(results),
        results=results,
    )


class ReplaceRequest(BaseModel):
    query: str
    replace: str
    files: list[str] | None = None
    is_regex: bool = False
    match_case: bool = False


@workspace_router.post("/replace")
async def replace_workspace(req: ReplaceRequest) -> dict[str, Any]:
    """Project-wide replace across workspace files."""
    ensure_workspace_initialized()
    if not req.query:
        return {"success": False, "error": "Empty query", "updated_files": [], "replacements": 0}

    flags = 0 if req.match_case else re.IGNORECASE
    # Decode U+XXXX if needed
    unicode_match = re.fullmatch(r"U\+([0-9A-Fa-f]{4,6})", req.query.strip())
    search_term = chr(int(unicode_match.group(1), 16)) if unicode_match else req.query
    pat_str = search_term if req.is_regex else re.escape(search_term)

    target_files: list[Path] = []
    if req.files:
        for f in req.files:
            p = resolve_safe_path(f)
            if p.exists() and p.is_file():
                target_files.append(p)
    else:
        for root, _, files in os.walk(WORKSPACE_ROOT):
            for f in files:
                target_files.append(Path(root) / f)

    updated_files = []
    total_replacements = 0

    for file_path in target_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        new_content, count = re.subn(pat_str, req.replace, content, flags=flags)
        if count > 0:
            file_path.write_text(new_content, encoding="utf-8")
            total_replacements += count
            updated_files.append(file_path.relative_to(WORKSPACE_ROOT).as_posix())

    return {
        "success": True,
        "updated_files": updated_files,
        "replacements": total_replacements,
    }


# ==============================================================================
# Source Control (Git Integration)
# ==============================================================================

class GitFileStatus(BaseModel):
    path: str
    status: str
    staged: bool = False


class GitStatusResponse(BaseModel):
    available: bool
    branch: str = ""
    clean: bool = True
    files: list[GitFileStatus] = Field(default_factory=list)
    reason: str | None = None


@workspace_router.get("/git/status", response_model=GitStatusResponse)
async def get_git_status() -> GitStatusResponse:
    """Check actual Git repository status."""
    try:
        status_proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "-uall"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if status_proc.returncode != 0:
            return GitStatusResponse(
                available=False,
                reason=status_proc.stderr.strip() or "Git command failed.",
            )

        branch_proc = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3,
        )
        branch = branch_proc.stdout.strip() or "main"

        file_list: list[GitFileStatus] = []
        for line in status_proc.stdout.splitlines():
            line = line.rstrip()
            if len(line) < 4:
                continue
            x = line[0]
            y = line[1]
            file_path = line[3:].strip()
            # Normalize status code
            code = "M"
            staged = False
            if x != " " and x != "?":
                staged = True
                code = x
            elif y != " ":
                code = y
            if code == "?":
                code = "U"

            file_list.append(GitFileStatus(path=file_path, status=code, staged=staged))

        return GitStatusResponse(
            available=True,
            branch=branch,
            clean=len(file_list) == 0,
            files=file_list,
        )
    except Exception as e:
        return GitStatusResponse(
            available=False,
            reason=f"Git unavailable: {e}",
        )


@workspace_router.get("/git/diff")
async def get_git_diff(path: str = Query("", description="Relative path")) -> dict[str, Any]:
    """Retrieve actual Git diff for a file or repo."""
    try:
        cmd = ["git", "diff", "HEAD"]
        if path:
            cmd.extend(["--", path])
        diff_proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        diff_text = diff_proc.stdout
        if not diff_text and path:
            # Check untracked diff fallback
            target = PROJECT_ROOT / path
            if target.exists() and target.is_file():
                try:
                    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
                    diff_text = f"--- /dev/null\n+++ b/{path}\n@@ -0,0 +1,{len(lines)} @@\n" + "\n".join(f"+{l}" for l in lines)
                except Exception:
                    pass

        return {
            "available": True,
            "path": path,
            "diff": diff_text or "No changes detected.",
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "diff": "",
        }


class GitCommitRequest(BaseModel):
    message: str
    files: list[str] | None = None


@workspace_router.post("/git/commit")
async def git_commit(req: GitCommitRequest) -> dict[str, Any]:
    """Perform actual Git commit. Confirms execution before reporting success."""
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Commit message cannot be empty.")

    try:
        # 1. Stage requested files or all changes
        if req.files and len(req.files) > 0:
            add_proc = subprocess.run(
                ["git", "add"] + req.files,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=5,
            )
        else:
            add_proc = subprocess.run(
                ["git", "add", "-A"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=5,
            )

        if add_proc.returncode != 0:
            return {
                "success": False,
                "error": f"Failed to stage files: {add_proc.stderr.strip()}",
            }

        # 2. Commit changes
        commit_proc = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )

        if commit_proc.returncode != 0:
            return {
                "success": False,
                "error": commit_proc.stderr.strip() or commit_proc.stdout.strip() or "Nothing to commit.",
            }

        # 3. Retrieve confirmed commit hash
        hash_proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3,
        )
        commit_hash = hash_proc.stdout.strip() if hash_proc.returncode == 0 else "unknown"

        return {
            "success": True,
            "commit_hash": commit_hash,
            "message": msg,
            "output": commit_proc.stdout.strip(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Git commit failed: {e}",
        }


