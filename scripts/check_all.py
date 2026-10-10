"""Unified repository verification and CI gate script for SecureLex IDE.

Executes all verification gates across Python backend and TypeScript frontend:
1. Rule fixture schema and coverage check (`scripts/check_rule_fixtures.py`)
2. Documentation markdown link integrity (`scripts/check_links.py`)
3. Python linting (`ruff check .`)
4. Python strict type checking (`mypy`)
5. Golden characterisation test suite (`scripts/golden.py --check`)
6. Frontend formatting check (`npm run format`)
7. Frontend linting (`npm run lint`)
8. Frontend strict type checking (`npm run typecheck`)
9. Frontend unit and contract tests (`npm test`)
10. Frontend production build (`npm run build`)
11. Python test suite (`pytest -q`)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"


def get_python_exe() -> str:
    """Find virtual environment python executable or fallback to sys.executable."""
    venv_py = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def get_npm_cmd() -> str:
    """Find npm executable."""
    return shutil.which("npm.cmd") or shutil.which("npm") or "npm"


def run_gate(name: str, cmd: list[str] | str, cwd: Path, env: dict[str, str] | None = None) -> tuple[bool, float, str]:
    """Execute a single gate command, returning (success, elapsed_seconds, output)."""
    print(f"\n[GATE] Running {name}...", flush=True)
    start_t = time.perf_counter()

    use_shell = isinstance(cmd, str) or os.name == "nt"
    run_env = os.environ.copy()
    run_env["PYTHONUTF8"] = "1"
    if env:
        run_env.update(env)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=run_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=use_shell,
            check=False,
        )
        elapsed = time.perf_counter() - start_t
        success = proc.returncode == 0
        if success:
            print(f"       -> PASS ({elapsed:.2f}s)", flush=True)
        else:
            print(f"       -> FAIL ({elapsed:.2f}s, exit code {proc.returncode})", flush=True)
            print(proc.stdout, flush=True)
        return success, elapsed, proc.stdout
    except Exception as exc:
        elapsed = time.perf_counter() - start_t
        print(f"       -> ERROR ({elapsed:.2f}s): {exc}", flush=True)
        return False, elapsed, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified verification gates runner.")
    parser.add_argument("--skip-pytest", action="store_true", help="Skip long Python pytest run.")
    parser.add_argument("--skip-build", action="store_true", help="Skip frontend production build.")
    parser.add_argument("--fast", action="store_true", help="Fast mode: skip pytest and production build.")
    args = parser.parse_args()

    skip_pytest = args.skip_pytest or args.fast
    skip_build = args.skip_build or args.fast

    py_exe = get_python_exe()
    npm_cmd = get_npm_cmd()

    print("=" * 70, flush=True)
    print("  SecureLex IDE (apsla) - Unified Verification Gate", flush=True)
    print("=" * 70, flush=True)

    results: list[tuple[str, bool, float]] = []

    # 1. Rule fixtures
    ok, el, _ = run_gate("Rule Fixtures Check", [py_exe, str(ROOT / "scripts" / "check_rule_fixtures.py")], ROOT)
    results.append(("Rule Fixtures Check", ok, el))

    # 2. Doc links
    ok, el, _ = run_gate("Documentation Links Check", [py_exe, str(ROOT / "scripts" / "check_links.py")], ROOT)
    results.append(("Documentation Links Check", ok, el))

    # 3. Ruff
    ruff_exe = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("ruff.exe" if os.name == "nt" else "ruff")
    ruff_cmd = [str(ruff_exe) if ruff_exe.exists() else "ruff", "check", "."]
    ok, el, _ = run_gate("Python Ruff Linter", ruff_cmd, ROOT)
    results.append(("Python Ruff Linter", ok, el))

    # 4. Mypy
    mypy_exe = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("mypy.exe" if os.name == "nt" else "mypy")
    mypy_cmd = [str(mypy_exe) if mypy_exe.exists() else "mypy"]
    ok, el, _ = run_gate("Python Mypy Typecheck", mypy_cmd, ROOT)
    results.append(("Python Mypy Typecheck", ok, el))

    # 5. Golden Tests
    ok, el, _ = run_gate("Golden Characterisation Tests", [py_exe, str(ROOT / "scripts" / "golden.py"), "--check"], ROOT)
    results.append(("Golden Characterisation Tests", ok, el))

    # 6. Frontend Format
    ok, el, _ = run_gate("Frontend Prettier Check", [npm_cmd, "run", "format"], WEB_DIR)
    results.append(("Frontend Prettier Check", ok, el))

    # 7. Frontend Lint
    ok, el, _ = run_gate("Frontend ESLint Check", [npm_cmd, "run", "lint"], WEB_DIR)
    results.append(("Frontend ESLint Check", ok, el))

    # 8. Frontend Typecheck
    ok, el, _ = run_gate("Frontend TypeScript Check", [npm_cmd, "run", "typecheck"], WEB_DIR)
    results.append(("Frontend TypeScript Check", ok, el))

    # 9. Frontend Vitest Tests
    ok, el, _ = run_gate("Frontend Vitest Tests", [npm_cmd, "test"], WEB_DIR)
    results.append(("Frontend Vitest Tests", ok, el))

    # 10. Frontend Build
    if not skip_build:
        ok, el, _ = run_gate("Frontend Production Build", [npm_cmd, "run", "build"], WEB_DIR)
        results.append(("Frontend Production Build", ok, el))

    # 11. Pytest
    if not skip_pytest:
        pytest_exe = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("pytest.exe" if os.name == "nt" else "pytest")
        pytest_cmd = [str(pytest_exe) if pytest_exe.exists() else "pytest", "-q"]
        ok, el, _ = run_gate("Python Pytest Suite", pytest_cmd, ROOT)
        results.append(("Python Pytest Suite", ok, el))
        # Revert any test-induced changes to reports/
        subprocess.run(["git", "checkout", "--", "reports/"], cwd=str(ROOT), capture_output=True, check=False)

    print("\n" + "=" * 70, flush=True)
    print("  VERIFICATION SUMMARY", flush=True)
    print("=" * 70, flush=True)
    all_passed = True
    for name, success, elapsed in results:
        status_str = "[PASS]" if success else "[FAIL]"
        if not success:
            all_passed = False
        print(f"  {status_str}  {name:<40} ({elapsed:.2f}s)", flush=True)
    print("=" * 70, flush=True)

    if all_passed:
        print("ALL VERIFICATION GATES PASSED! Repository is ready for merge/release.\n", flush=True)
        return 0

    print("ONE OR MORE VERIFICATION GATES FAILED. See details above.\n", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
