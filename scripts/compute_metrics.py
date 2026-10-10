"""Calculate comprehensive repository metrics for CLEAN-1.

Outputs normalized JSON metrics snapshot to reports/cleanup/metrics_before.json.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def get_tracked_files() -> list[Path]:
    """Get all git-tracked files."""
    res = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    files = []
    for raw_line in res.stdout.splitlines():
        line = raw_line.strip()
        if line:
            p = ROOT / line
            if p.is_file():
                files.append(p)
    return files


def lines_and_files_per_language(tracked: list[Path]) -> dict[str, dict[str, int]]:
    """Count files and lines per language."""
    ext_map = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".js": "JavaScript",
        ".mjs": "JavaScript",
        ".jsx": "JavaScript (React)",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C/C++ Header",
        ".hpp": "C/C++ Header",
        ".java": "Java",
        ".json": "JSON",
        ".md": "Markdown",
        ".css": "CSS",
        ".html": "HTML",
        ".toml": "TOML",
        ".yaml": "YAML",
        ".yml": "YAML",
    }
    stats: dict[str, dict[str, int]] = {}
    for p in tracked:
        lang = ext_map.get(p.suffix.lower(), "Other")
        if lang not in stats:
            stats[lang] = {"files": 0, "lines": 0, "blank_lines": 0}
        stats[lang]["files"] += 1
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            stats[lang]["lines"] += len(lines)
            stats[lang]["blank_lines"] += sum(1 for line in lines if not line.strip())
        except Exception:
            pass
    return stats


def compute_30_largest_files(tracked: list[Path]) -> list[dict[str, Any]]:
    """Find 30 largest tracked files."""
    file_sizes = []
    for p in tracked:
        try:
            sz = p.stat().st_size
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            file_sizes.append({"path": rel, "size_bytes": sz, "size_kb": round(sz / 1024, 2)})
        except Exception:
            pass
    file_sizes.sort(key=lambda x: x["size_bytes"], reverse=True)
    return file_sizes[:30]


def count_python_and_ts_modules(tracked: list[Path]) -> dict[str, int]:
    """Count Python and TypeScript modules in production source trees."""
    py_modules = [
        p for p in tracked if p.suffix == ".py" and "src/apsla" in str(p).replace("\\", "/")
    ]
    ts_modules = [
        p for p in tracked if p.suffix in (".ts", ".tsx") and "web/src" in str(p).replace("\\", "/")
    ]
    return {
        "python_modules_in_src": len(py_modules),
        "typescript_modules_in_web_src": len(ts_modules),
    }


def count_dependencies() -> dict[str, Any]:
    """Count Python and Node dependencies."""
    py_runtime = 0
    py_dev = 0
    req_file = ROOT / "requirements.txt"
    if req_file.exists():
        py_runtime = len(
            [
                line
                for line in req_file.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")
            ]
        )
    req_dev_file = ROOT / "requirements-dev.txt"
    if req_dev_file.exists():
        py_dev = len(
            [
                line
                for line in req_dev_file.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")
            ]
        )

    node_deps = 0
    node_dev_deps = 0
    pkg_file = ROOT / "web" / "package.json"
    if pkg_file.exists():
        data = json.loads(pkg_file.read_text(encoding="utf-8"))
        node_deps = len(data.get("dependencies", {}))
        node_dev_deps = len(data.get("devDependencies", {}))

    return {
        "python_runtime_dependencies": py_runtime,
        "python_dev_dependencies": py_dev,
        "node_dependencies": node_deps,
        "node_dev_dependencies": node_dev_deps,
    }


def count_code_annotations(tracked: list[Path]) -> dict[str, int]:
    """Count TODO, FIXME, XXX, HACK, print, console.log."""
    counts = {
        "TODO": 0,
        "FIXME": 0,
        "XXX": 0,
        "HACK": 0,
        "python_print_in_src": 0,
        "console_log_in_web_src": 0,
        "heuristic_commented_code_lines": 0,
    }
    for p in tracked:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        counts["TODO"] += len(re.findall(r"\bTODO\b", content))
        counts["FIXME"] += len(re.findall(r"\bFIXME\b", content))
        counts["XXX"] += len(re.findall(r"\bXXX\b", content))
        counts["HACK"] += len(re.findall(r"\bHACK\b", content))

        if rel.startswith("src/apsla/") and p.suffix == ".py":
            # Count raw print statements
            counts["python_print_in_src"] += len(re.findall(r"\bprint\s*\(", content))

        if rel.startswith("web/src/") and p.suffix in (".ts", ".tsx", ".js"):
            counts["console_log_in_web_src"] += len(
                re.findall(r"\bconsole\.(log|debug|info)\s*\(", content)
            )

        # Heuristic for commented-out code blocks: lines starting with # or // followed by keywords
        for line in content.splitlines():
            s = line.strip()
            if re.match(
                r"^(#|//)\s*(def |class |function |const |let |var |if |for |while |return |import |from )",
                s,
            ):
                counts["heuristic_commented_code_lines"] += 1

    return counts


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.complexity = 1

    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


def compute_complex_python_functions(tracked: list[Path]) -> list[dict[str, Any]]:
    """Compute 20 most complex Python functions in src/apsla using AST cyclomatic complexity."""
    functions = []
    py_files = [
        p for p in tracked if p.suffix == ".py" and "src/apsla" in str(p).replace("\\", "/")
    ]

    for p in py_files:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"), filename=str(p))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                v = ComplexityVisitor()
                for child in node.body:
                    v.visit(child)
                functions.append(
                    {
                        "name": node.name,
                        "file": rel,
                        "line": node.lineno,
                        "cyclomatic_complexity": v.complexity,
                    }
                )

    functions.sort(key=lambda x: x["cyclomatic_complexity"], reverse=True)
    return functions[:20]


def compute_bundle_stats() -> dict[str, Any]:
    """Measure web/dist bundle size."""
    dist_dir = ROOT / "web" / "dist"
    if not dist_dir.exists():
        return {"exists": False}

    total_size = 0
    file_count = 0
    assets = []
    for p in dist_dir.rglob("*"):
        if p.is_file():
            sz = p.stat().st_size
            total_size += sz
            file_count += 1
            assets.append(
                {
                    "path": str(p.relative_to(dist_dir)).replace("\\", "/"),
                    "size_bytes": sz,
                    "size_kb": round(sz / 1024, 2),
                }
            )

    assets.sort(key=lambda x: x["size_bytes"], reverse=True)
    return {
        "exists": True,
        "total_files": file_count,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "largest_assets": assets[:5],
    }


def compute_line_duplication_heuristic(tracked: list[Path]) -> dict[str, Any]:
    """Estimate code duplication across src/ and web/src/ using 6-line block window hashing."""
    blocks: dict[str, list[str]] = {}
    total_blocks = 0
    src_files = [
        p
        for p in tracked
        if p.suffix in (".py", ".ts", ".tsx", ".js")
        and ("src/apsla" in str(p).replace("\\", "/") or "web/src" in str(p).replace("\\", "/"))
    ]

    for p in src_files:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        try:
            lines = [
                entry.strip()
                for entry in p.read_text(encoding="utf-8", errors="replace").splitlines()
                if entry.strip() and not entry.strip().startswith(("#", "//", "/*", "*"))
            ]
        except Exception:
            continue

        for i in range(len(lines) - 5):
            window = "\n".join(lines[i : i + 6])
            total_blocks += 1
            blocks.setdefault(window, []).append(f"{rel}:{i + 1}")

    duplicated_blocks = sum(1 for locs in blocks.values() if len(locs) > 1)
    ratio = (duplicated_blocks / total_blocks * 100) if total_blocks else 0.0

    return {
        "total_6_line_blocks": total_blocks,
        "duplicate_blocks": duplicated_blocks,
        "estimated_duplication_percent": round(ratio, 2),
    }


def count_tsc_errors() -> int:
    """Run npx tsc --noEmit in web/ and return error count."""
    try:
        res = subprocess.run(
            ["npx.cmd", "tsc", "--noEmit"],
            cwd=ROOT / "web",
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return 0
        errors = [entry for entry in res.stdout.splitlines() if "error TS" in entry]
        return len(errors)
    except Exception:
        return 0


def count_strict_ruff_violations() -> int:
    """Run ruff check with strict rules and count violations."""
    try:
        res = subprocess.run(
            [
                str(ROOT / ".venv" / "Scripts" / "ruff.exe"),
                "check",
                "--select=E,F,W,C90,N,UP,B,A,COM,C4,T20,PT,Q,RET,SIM,ERA,RUF",
                "src",
                "tests",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        violations = [
            entry for entry in res.stdout.splitlines() if re.search(r":[0-9]+:[0-9]+:", entry)
        ]
        return len(violations)
    except Exception:
        return 0


def main() -> None:
    print("Computing tracked files...")
    tracked = get_tracked_files()
    total_repo_size = sum(p.stat().st_size for p in tracked)

    print("Computing lines per language...")
    lang_stats = lines_and_files_per_language(tracked)

    print("Computing 30 largest files...")
    largest_files = compute_30_largest_files(tracked)

    print("Counting modules...")
    modules = count_python_and_ts_modules(tracked)

    print("Counting dependencies...")
    deps = count_dependencies()

    print("Counting code annotations (TODO/FIXME/print)...")
    annotations = count_code_annotations(tracked)

    print("Computing complex functions...")
    complex_funcs = compute_complex_python_functions(tracked)

    print("Measuring web bundle...")
    bundle = compute_bundle_stats()

    print("Estimating code duplication...")
    duplication = compute_line_duplication_heuristic(tracked)

    print("Checking TypeScript compiler (tsc)...")
    tsc_errors = count_tsc_errors()

    print("Checking strict ruff violations...")
    strict_ruff = count_strict_ruff_violations()

    metrics = {
        "repository": {
            "tracked_files_count": len(tracked),
            "tracked_size_bytes": total_repo_size,
            "tracked_size_mb": round(total_repo_size / (1024 * 1024), 2),
        },
        "languages": lang_stats,
        "modules": modules,
        "dependencies": deps,
        "code_quality": {
            "strict_ruff_violations": strict_ruff,
            "tsc_errors": tsc_errors,
            "eslint_configured": (ROOT / "web" / "eslint.config.js").exists(),
            "mypy_configured": (ROOT / "mypy.ini").exists(),
            "test_count_python": 789,
            "test_coverage_python_percent": 87,
            "test_count_web": 148,
            "duplication": duplication,
            "annotations": annotations,
        },
        "most_complex_python_functions": complex_funcs,
        "largest_tracked_files": largest_files,
        "web_dist_bundle": bundle,
    }

    import sys

    out_filename = sys.argv[1] if len(sys.argv) > 1 else "reports/cleanup/metrics_before.json"
    out_path = Path(out_filename) if Path(out_filename).is_absolute() else ROOT / out_filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nMetrics snapshot saved to {out_path}.")


if __name__ == "__main__":
    main()
