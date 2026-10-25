"""
Script to safely clean up obsolete, temporary residue, ephemeral caches,
redundant model checkpoints, and bloated logs from the workspace.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ACTIVE_ML_MODELS = {
    "separate_cpp_hist_gradient_boosting_20261021_162559",
    "separate_java_hist_gradient_boosting_20261021_162559",
    "separate_javascript_random_forest_20261021_162559",
    "separate_python_hist_gradient_boosting_20261021_162559",
}


def get_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def remove_path(path: Path) -> int:
    sz = get_size(path)
    if not path.exists():
        return 0
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    except Exception as e:
        print(f"Error removing {path}: {e}")
        return 0
    return sz


def main() -> None:
    print("=" * 65)
    print("SecureLex IDE Workspace Cleanup")
    print("=" * 65)

    bytes_freed = 0
    items_deleted = 0

    # 1. Leftover pytest temp directories in ROOT
    print("\n[1/6] Cleaning leftover pytest temporary directories...")
    for item in ROOT.iterdir():
        if item.is_dir() and item.name.startswith(".pytest"):
            sz = remove_path(item)
            bytes_freed += sz
            items_deleted += 1
            print(f"  - Deleted: {item.name} ({sz / 1024:.1f} KB)")

    # 2. Root logs
    print("\n[2/6] Cleaning root log files...")
    for fname in ["api-run.err.log", "api-run.log", "web-run.err.log", "web-run.log"]:
        fpath = ROOT / fname
        if fpath.exists():
            sz = remove_path(fpath)
            bytes_freed += sz
            items_deleted += 1
            print(f"  - Deleted: {fname} ({sz / 1024:.1f} KB)")

    # 3. Caches & build artifacts
    print("\n[3/6] Cleaning heavy caches and build directories...")
    cache_dirs = [
        ROOT / ".mypy_cache",
        ROOT / ".ruff_cache",
        ROOT / ".hypothesis",
        ROOT / ".vite",
        ROOT / "test-results",
        ROOT / "web" / "dist",
        ROOT / "web" / ".vite",
        ROOT / "web" / "test-results",
    ]
    for cdir in cache_dirs:
        if cdir.exists():
            sz = remove_path(cdir)
            bytes_freed += sz
            items_deleted += 1
            print(f"  - Deleted: {cdir.relative_to(ROOT)} ({sz / (1024*1024):.2f} MB)")

    # 4. Obsolete ML model checkpoints
    print("\n[4/6] Cleaning obsolete historical ML model checkpoints...")
    artifacts_dir = ROOT / "src" / "apsla" / "ml" / "artifacts"
    ml_freed = 0
    ml_count = 0
    if artifacts_dir.exists():
        for model_dir in artifacts_dir.iterdir():
            if model_dir.is_dir() and model_dir.name not in ACTIVE_ML_MODELS:
                sz = remove_path(model_dir)
                ml_freed += sz
                ml_count += 1
    bytes_freed += ml_freed
    items_deleted += ml_count
    print(f"  - Deleted {ml_count} older model checkpoints ({ml_freed / (1024*1024):.2f} MB freed)")
    print(f"  - Retained active production models: {len(ACTIVE_ML_MODELS)}")

    # 5. Heavy terminal logs & redundant screenshots
    print("\n[5/6] Cleaning bloated terminal logs & baseline screens...")
    heavy_logs = [
        ROOT / "reports" / "prelaunch" / "logs" / "ruff_format.log",
        ROOT / "reports" / "prelaunch" / "logs" / "ruff_format_src.log",
        ROOT / "reports" / "cleanup" / "screens_before",
        ROOT / "reports" / "sl2_1_pytest_basetemp",
    ]
    for rdir in (ROOT / "reports").iterdir():
        if rdir.is_dir() and rdir.name.startswith(".pytest"):
            heavy_logs.append(rdir)

    for h in heavy_logs:
        if h.exists():
            sz = remove_path(h)
            bytes_freed += sz
            items_deleted += 1
            print(f"  - Deleted: {h.relative_to(ROOT)} ({sz / (1024*1024):.2f} MB)")

    # 6. Stray binary files & scratch debug scripts
    print("\n[6/6] Cleaning stray binaries and scratch test scripts...")
    stray_files = [
        ROOT / "web" / "Appendix_D_Raw_Experimental_Data.docx",
        ROOT / "web" / "files.zip",
    ]
    for sf in stray_files:
        if sf.exists():
            sz = remove_path(sf)
            bytes_freed += sz
            items_deleted += 1
            print(f"  - Deleted: {sf.relative_to(ROOT)} ({sz / (1024*1024):.2f} MB)")

    scratch_dir = ROOT / "scratch"
    scratch_count = 0
    scratch_freed = 0
    if scratch_dir.exists():
        for sf in scratch_dir.iterdir():
            if sf.is_file() and sf.name not in {"cleanup_workspace.py"}:
                sz = remove_path(sf)
                scratch_freed += sz
                scratch_count += 1
    bytes_freed += scratch_freed
    items_deleted += scratch_count
    print(f"  - Deleted {scratch_count} scratch debug scripts ({scratch_freed / 1024:.1f} KB)")

    print("\n" + "=" * 65)
    print("Cleanup Completed Successfully!")
    print("=" * 65)
    print(f"Total items removed: {items_deleted}")
    print(f"Total disk space freed: {bytes_freed / (1024*1024):.2f} MB")
    print("=" * 65)


if __name__ == "__main__":
    main()
