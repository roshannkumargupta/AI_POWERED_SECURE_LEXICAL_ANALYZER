"""Full build script for SecureLex IDE web frontend.

Runs 'npm ci', 'npm run build' in web/, checks web/dist, and outputs
a detailed size and bundle telemetry report.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def format_bytes(size: int) -> str:
    """Format byte count into human-readable unit."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    repo_root = Path(__file__).resolve().parent.parent
    web_dir = repo_root / "web"
    dist_dir = web_dir / "dist"

    print("=" * 65, flush=True)
    print("  SecureLex IDE (APSLA) - Production Frontend Build", flush=True)
    print("=" * 65, flush=True)
    print(f"Working directory: {web_dir}", flush=True)

    is_windows = sys.platform.startswith("win")
    npm_bin = shutil.which("npm.cmd") or shutil.which("npm") or "npm"

    # 1. Run npm ci
    print("\n[1/3] Installing dependencies with 'npm ci'...", flush=True)
    ci_cmd = [npm_bin, "ci"] if not is_windows else f'"{npm_bin}" ci'
    try:
        subprocess.run(
            ci_cmd,
            cwd=web_dir,
            check=True,
            shell=is_windows,
        )
        print("      Dependencies verified cleanly.", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during 'npm ci': {e}", flush=True)
        print("Falling back to 'npm install'...", flush=True)
        install_cmd = [npm_bin, "install"] if not is_windows else f'"{npm_bin}" install'
        subprocess.run(install_cmd, cwd=web_dir, check=True, shell=is_windows)

    # 2. Run npm run build
    print("\n[2/3] Building production bundle with 'npm run build'...", flush=True)
    build_cmd = [npm_bin, "run", "build"] if not is_windows else f'"{npm_bin}" run build'
    subprocess.run(
        build_cmd,
        cwd=web_dir,
        check=True,
        shell=is_windows,
    )
    print("      Build completed successfully.", flush=True)

    # 3. Report sizes
    print("\n[3/3] Inspecting production artifacts in web/dist/...", flush=True)
    if not dist_dir.exists():
        print(f"ERROR: Build directory not found at {dist_dir}", flush=True)
        return 1

    total_bytes = 0
    file_stats: list[tuple[str, int]] = []

    for root, _, files in os.walk(dist_dir):
        for f in files:
            full_path = Path(root) / f
            rel_path = full_path.relative_to(dist_dir)
            size = full_path.stat().st_size
            total_bytes += size
            file_stats.append((str(rel_path).replace("\\", "/"), size))

    file_stats.sort(key=lambda x: x[1], reverse=True)

    print("\n" + "-" * 65, flush=True)
    print(f"{'Artifact Path':<45} {'Size':>18}", flush=True)
    print("-" * 65, flush=True)
    top_files = file_stats[:15]
    index_html_size = dist_dir.joinpath("index.html").stat().st_size
    if ("index.html", index_html_size) not in top_files:
        top_files.append(("index.html", index_html_size))

    for path_str, size in top_files:
        print(f"{path_str:<45} {format_bytes(size):>18}", flush=True)

    if len(file_stats) > len(top_files):
        remaining_count = len(file_stats) - len(top_files)
        print(f"... and {remaining_count} other chunk / worker assets", flush=True)

    print("-" * 65, flush=True)
    print(
        f"{'Total Production Bundle Size (' + str(len(file_stats)) + ' files):':<45} {format_bytes(total_bytes):>18}",
        flush=True,
    )
    print("=" * 65, flush=True)
    print("[OK] Production build ready for offline distribution and FastAPI serving.", flush=True)
    print("=" * 65, flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
