"""Allowlisted optional tool discovery and bounded static-analysis execution."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from apsla.models_v2 import ToolStatus


@dataclass(frozen=True)
class ToolDefinition:
    executable: str
    kind: str
    version_args: tuple[str, ...]
    languages: tuple[str, ...] = ()
    static_profile: str | None = None


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "g++": ToolDefinition("g++", "compiler", ("--version",), ("cpp",), "cpp"),
    "gcc": ToolDefinition("gcc", "compiler", ("--version",), ("c", "cpp"), "cpp"),
    "clang": ToolDefinition("clang", "compiler", ("--version",), ("c", "cpp"), "cpp"),
    "clang++": ToolDefinition("clang++", "compiler", ("--version",), ("cpp",), "cpp"),
    "clang-tidy": ToolDefinition("clang-tidy", "analyzer", ("--version",), ("cpp",), "clang-tidy"),
    "cppcheck": ToolDefinition("cppcheck", "analyzer", ("--version",), ("c", "cpp"), "cppcheck"),
    "javac": ToolDefinition("javac", "compiler", ("-version",), ("java",), "java"),
    "node": ToolDefinition("node", "runtime", ("--version",), ("javascript",), "node-check"),
    "ruff": ToolDefinition("ruff", "analyzer", ("--version",), ("python",), "ruff"),
    "pyflakes": ToolDefinition("pyflakes", "analyzer", ("--version",), ("python",), "pyflakes"),
    "mypy": ToolDefinition("mypy", "analyzer", ("--version",), ("python",), "mypy"),
    "eslint": ToolDefinition("eslint", "analyzer", ("--version",), ("javascript",), "eslint"),
    "bandit": ToolDefinition("bandit", "analyzer", ("--version",), ("python",), "bandit"),
    "semgrep": ToolDefinition("semgrep", "analyzer", ("--version",), (), "semgrep"),
    "clang-format": ToolDefinition("clang-format", "formatter", ("--version",), ("cpp",)),
    "black": ToolDefinition("black", "formatter", ("--version",), ("python",)),
    "prettier": ToolDefinition("prettier", "formatter", ("--version",), ("javascript",)),
    "google-java-format": ToolDefinition(
        "google-java-format", "formatter", ("--version",), ("java",)
    ),
}

VERSION_TIMEOUT_SECONDS = 2.0
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_OUTPUT_BYTES = 64 * 1024


def network_sandbox_available() -> bool:
    """Return whether this host has an OS-enforced offline subprocess sandbox.

    No portable Windows network namespace/job policy is configured by this app yet.
    Fail closed instead of treating proxy variables as network isolation.
    """
    return False


def _clean_env() -> dict[str, str]:
    """Keep only process basics and a PATH; remove secrets and provider config."""
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env["PYTHONNOUSERSITE"] = "1"
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    return env


def _bounded(text: str | bytes | None) -> str:
    if text is None:
        return ""
    data = text if isinstance(text, bytes) else text.encode("utf-8", errors="replace")
    return data[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")


def _parse_output(name: str, stdout: str, stderr: str) -> dict[str, object]:
    """Parse structured analyzer formats while retaining bounded raw evidence."""
    source = stdout.strip() or stderr.strip()
    if name == "cppcheck" and source:
        parsed = source
    elif name in {"ruff", "bandit", "eslint", "semgrep"} and source:
        try:
            parsed: object = json.loads(source)
        except json.JSONDecodeError:
            parsed = {"parse_error": "Tool output was not valid JSON."}
    else:
        parsed = [line for line in source.splitlines() if line.strip()]
    return {"parsed": parsed, "stdout": stdout, "stderr": stderr}


def _run_capped(
    argv: list[str], *, cwd: str | Path, env: dict[str, str], timeout: float
) -> tuple[int, bytes, bytes]:
    """Run without a shell and drain both pipes while retaining at most the cap."""
    proc = subprocess.Popen(
        argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False
    )
    captured = {"stdout": bytearray(), "stderr": bytearray()}

    def drain(key: str, stream: object) -> None:
        while True:
            chunk = stream.read(8192)  # type: ignore[attr-defined]
            if not chunk:
                break
            room = MAX_OUTPUT_BYTES - len(captured[key])
            if room > 0:
                captured[key].extend(chunk[:room])

    assert proc.stdout is not None and proc.stderr is not None
    readers = [
        threading.Thread(target=drain, args=("stdout", proc.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", proc.stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()
    try:
        returncode = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        for reader in readers:
            reader.join(timeout=1)
        proc.stdout.close()
        proc.stderr.close()
        raise subprocess.TimeoutExpired(
            argv,
            timeout,
            output=bytes(captured["stdout"]),
            stderr=bytes(captured["stderr"]),
        ) from None
    for reader in readers:
        reader.join()
    proc.stdout.close()
    proc.stderr.close()
    return returncode, bytes(captured["stdout"]), bytes(captured["stderr"])


def detect_tool(
    name: str, *, path: str | None = None, timeout: float = VERSION_TIMEOUT_SECONDS
) -> ToolStatus:
    definition = TOOL_REGISTRY.get(name)
    if definition is None:
        return ToolStatus(
            name=name,
            kind="unknown",
            available=False,
            status="unavailable",
            reason="Executable is not allowlisted.",
        )
    executable = shutil.which(definition.executable, path=path)
    if executable is None:
        return ToolStatus(
            name=name,
            kind=definition.kind,
            available=False,
            status="unavailable",
            reason="Install the tool and make it available on PATH.",
        )
    try:
        returncode, stdout, stderr = _run_capped(
            [executable, *definition.version_args],
            timeout=timeout,
            env=_clean_env(),
            cwd=tempfile.gettempdir(),
        )
        output = _bounded(stdout or stderr).strip().splitlines()
        version = output[0][:200] if output else None
        if returncode:
            return ToolStatus(
                name=name,
                kind=definition.kind,
                available=True,
                version=version,
                status="failed",
                reason=f"Version probe exited with status {returncode}; check the executable installation.",
            )
        return ToolStatus(
            name=name, kind=definition.kind, available=True, version=version, status="ok"
        )
    except subprocess.TimeoutExpired:
        return ToolStatus(
            name=name,
            kind=definition.kind,
            available=True,
            status="timeout",
            reason="Version probe exceeded its time limit.",
        )
    except OSError as exc:
        return ToolStatus(
            name=name,
            kind=definition.kind,
            available=False,
            status="unavailable",
            reason=f"Executable could not start ({type(exc).__name__}); check runtime libraries and PATH.",
        )


def detect_all_tools(*, path: str | None = None) -> list[ToolStatus]:
    return [detect_tool(name, path=path) for name in TOOL_REGISTRY]


def execute_static_tool(
    name: str,
    source: str,
    language: str,
    *,
    filename: str = "source",
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[ToolStatus, dict[str, object]]:
    """Run a fixed static-check profile in a disposable directory; never run source.

    The caller cannot choose an executable or arguments. Submitted filename and
    contents are placed in a random temp directory under a fixed safe basename.
    The display filename is deliberately never used as a path or argument.
    """
    definition = TOOL_REGISTRY.get(name)
    if definition is None or definition.static_profile is None:
        return (
            ToolStatus(
                name=name,
                kind="analyzer",
                available=False,
                status="unavailable",
                reason="No static-analysis execution profile is allowlisted.",
            ),
            {},
        )
    if definition.languages and language not in definition.languages:
        return (
            ToolStatus(
                name=name,
                kind=definition.kind,
                available=False,
                status="skipped",
                reason="Tool does not support the requested language.",
            ),
            {},
        )
    detected = detect_tool(name)
    if not detected.available or detected.status != "ok":
        return detected, {}
    if name == "semgrep" and not (Path(__file__).resolve().parents[3] / "rules" / "semgrep").is_dir():
        return (
            ToolStatus(name=name, kind=definition.kind, available=True, version=detected.version,
                       status="unavailable", reason="Create the repository-local rules/semgrep directory; registry rules are never downloaded."),
            {},
        )
    if not network_sandbox_available():
        return (
            ToolStatus(
                name=name,
                kind=definition.kind,
                available=True,
                version=detected.version,
                status="unavailable",
                reason="No OS-enforced network-isolated subprocess sandbox is configured; execution is disabled.",
            ),
            {},
        )
    executable = shutil.which(definition.executable)
    assert executable is not None
    suffix = {"python": ".py", "java": ".java", "javascript": ".js", "cpp": ".cpp", "c": ".c"}.get(
        language, ".txt"
    )
    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix="securelex-tool-") as temp:
            root = Path(temp)
            java_class = re.search(
                r"\bpublic\s+(?:(?:abstract|final|sealed|strictfp)\s+)*class\s+([A-Za-z_$][A-Za-z0-9_$]*)",
                source,
            ) if language == "java" else None
            java_basename = java_class.group(1) if java_class else "Input"
            src_path = root / (java_basename + suffix if language == "java" else "input" + suffix)
            src_path.write_text(source, encoding="utf-8")
            profile = definition.static_profile
            if profile == "cpp":
                standard = "-std=c17" if language == "c" else "-std=c++20"
                if name.startswith("clang"):
                    args = [standard, "-fsyntax-only", "-ferror-limit=10", "-fno-color-diagnostics", "-x", "c++" if language == "cpp" else "c", str(src_path)]
                else:
                    args = [standard, "-fsyntax-only", "-fmax-errors=10", "-fdiagnostics-color=never", "-x", "c++" if language == "cpp" else "c", str(src_path)]
            elif profile == "ruff":
                args = ["check", "--isolated", "--select", "F", "--output-format", "json", str(src_path)]
            elif profile == "pyflakes":
                args = [str(src_path)]
            elif profile == "mypy":
                args = ["--no-incremental", "--follow-imports", "skip", str(src_path)]
            elif profile == "bandit":
                args = ["-f", "json", str(src_path)]
            elif profile == "eslint":
                args = ["--no-config-lookup", "--no-ignore", "--rule", "no-undef:error", "--rule", "no-unused-vars:warn", "--format", "json", str(src_path)]
            elif profile == "node-check":
                args = ["--check", str(src_path)]
            elif profile == "cppcheck":
                args = [
                    "--enable=warning,style,performance,portability",
                    "--error-exitcode=0",
                    "--xml",
                    "--xml-version=2",
                    str(src_path),
                ]
            elif profile == "clang-tidy":
                args = [str(src_path), "--", "-std=c++20", "-fsyntax-only", "-fno-color-diagnostics"]
            elif profile == "semgrep":
                config = Path(__file__).resolve().parents[3] / "rules" / "semgrep"
                args = ["scan", "--metrics=off", "--disable-version-check", "--config", str(config), "--json", "--no-git-ignore", str(src_path)]
            elif profile == "java":
                args = ["-proc:none", "-d", str(root / "classes"), str(src_path)]
            else:
                return (
                    ToolStatus(
                        name=name,
                        kind=definition.kind,
                        available=False,
                        status="unavailable",
                        reason="No fixed execution arguments are defined.",
                    ),
                    {},
                )
            # This branch requires an OS-enforced network sandbox; also isolate cwd/env,
            # use fixed arguments, cap runtime/output and invoke without a shell.
            returncode, stdout, stderr = _run_capped(
                [executable, *args], cwd=root, env=_clean_env(), timeout=timeout
            )
            status = ToolStatus(
                name=name,
                kind=definition.kind,
                available=True,
                version=detected.version,
                executed=True,
                duration_ms=(time.perf_counter() - started) * 1000,
                status="ok" if returncode == 0 else "failed",
                reason=None if returncode == 0 else f"Tool exited with status {returncode}.",
            )
            return status, _parse_output(name, _bounded(stdout), _bounded(stderr))
    except subprocess.TimeoutExpired as exc:
        return (
            ToolStatus(
                name=name,
                kind=definition.kind,
                available=True,
                version=detected.version,
                executed=True,
                duration_ms=(time.perf_counter() - started) * 1000,
                status="timeout",
                reason="Tool execution exceeded its time limit.",
            ),
            _parse_output(name, _bounded(exc.stdout), _bounded(exc.stderr)),
        )
    except OSError as exc:
        return (
            ToolStatus(
                name=name,
                kind=definition.kind,
                available=False,
                version=detected.version,
                executed=True,
                duration_ms=(time.perf_counter() - started) * 1000,
                status="failed",
                reason=f"Tool could not complete: {type(exc).__name__}.",
            ),
            {},
        )
