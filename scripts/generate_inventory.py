"""Generate comprehensive repository inventory for CLEAN-1.

Produces docs/cleanup/inventory.md.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FOLDER_PURPOSES = {
    ".": "Repository root workspace",
    "benchmarks": "Throughput, latency, and carbon benchmarks placeholder",
    "data": "Benchmark and training datasets (raw, provenance, external)",
    "data/external": "Realistic multi-language external evaluation test snippets",
    "data/external/cpp": "External C/C++ evaluation snippets",
    "data/external/java": "External Java Spring/JPA evaluation snippets",
    "data/external/javascript": "External JavaScript Node/Express evaluation snippets",
    "data/external/python": "External Python Flask/Django evaluation snippets",
    "data/feedback": "Append-only user false positive feedback records",
    "data/raw": "Raw token and homoglyph CSV attack corpora",
    "data/sources": "Unicode consortium lookalike/confusables source datasets",
    "docs": "Architecture documentation, developer guides, and viva materials",
    "docs/api_samples": "Saved raw JSON API response payloads across 4 languages",
    "docs/cleanup": "CLEAN-1 repository hygiene and dead-code documentation",
    "docs/explained": "Plain-English phase guides and 5 viva questions per phase",
    "docs/grammar": "Grammar references and syntax specifications",
    "docs/plan": "Preserved 16-week improvement plan documents",
    "docs/screenshots": "Visual UI evidence captures across phases",
    "legacy": "Strictly read-only historical senior prototype projects",
    "legacy/senior-part1": "Senior Python analyzer prototype (W5_6, ML_model)",
    "legacy/senior-part2": "Senior Java analyzer codebase (MIT licensed)",
    "reports": "Automated verification evidence, matrices, and metrics reports",
    "reports/cleanup": "CLEAN-1 safety baselines, metrics snapshots, and diffs",
    "reports/cleanup/screens_before": "UI baseline screenshots captured at clean-0",
    "reports/ui7": "UI-7 responsive frame screenshots and QA matrix",
    "reports/ui9": "UI-9 fix coverage and full E2E evaluation matrices",
    "scratch": "Scratch investigation and helper test generation scripts",
    "scripts": "Maintenance, build, verification, and evaluation automation scripts",
    "src": "Production Python source code root",
    "src/apsla": "AI-Powered Secure Lexical Analyzer (APSLA) core package",
    "src/apsla/agents": "Phase 15 modular compiler stage agents and orchestrator",
    "src/apsla/diagnostics": "Addictive lexical and syntax diagnostic engine",
    "src/apsla/feedback": "Append-only false positive feedback store and loader",
    "src/apsla/fixes": "Atomic text remediation, import injection, and verification engine",
    "src/apsla/languages": "Language plugins and runtime checkable protocols",
    "src/apsla/languages/cpp_lang": "C/C++ resilient lexer, parser, rules, and fixes",
    "src/apsla/languages/java_lang": "Java resilient lexer, parser, rules, and fixes",
    "src/apsla/languages/javascript_lang": "JavaScript resilient lexer, parser, rules, and fixes",
    "src/apsla/languages/python_lang": "Python lexer, AST parser, taint, rules, and fixes",
    "src/apsla/lexing": "Token definitions and bidirectional UTF-16 offset maps",
    "src/apsla/llm": "Guarded local Ollama provider and optional LLM interfaces",
    "src/apsla/ml": "45-dim feature extractor, synthetic dataset engine, and models",
    "src/apsla/ml/artifacts": "Trained ML model weights, temperature calibration, and schemas",
    "src/apsla/ml/synth": "Multi-language synthetic grammar snippet generators",
    "src/apsla/rules": "Language-agnostic rules, base classes, and explanations",
    "src/apsla/samples": "Bundled 146-entry 4-language sample snippets and loader",
    "src/apsla/samples/cpp": "C/C++ sample snippets",
    "src/apsla/samples/java": "Java sample snippets",
    "src/apsla/samples/javascript": "JavaScript sample snippets",
    "src/apsla/samples/pending": "Catalogued samples with documented engine gaps",
    "src/apsla/samples/python": "Python sample snippets",
    "src/apsla/server": "FastAPI HTTP REST service, LRU caching, and SPA mounting",
    "src/apsla/taint": "Data-flow taint analysis engines (AST and taint-lite)",
    "src/apsla/unicode_defense": "Confusable mappings, bidi detection, and text recovery",
    "tests": "Hermetic pytest and vitest test suites and fixtures",
    "tests/e2e": "End-to-end catalogue and server test cases",
    "tests/fixtures": "Test fixtures across languages and categories",
    "tests/fixtures/cpp": "C/C++ vulnerable, safe, and parser fixtures",
    "tests/fixtures/java": "Java vulnerable, safe, and parser fixtures",
    "tests/fixtures/javascript": "JavaScript vulnerable, safe, and parser fixtures",
    "tests/fixtures/python": "Python vulnerable, safe, and adversarial fixtures",
    "tests/golden": "Normalized golden characterisation baseline JSON files",
    "tests/security": "Security regression tests (agent tools allowlist, prompt injection)",
    "tests/unit": "Unit test modules for lexers, parsers, rules, ML, fixes, and server",
    "third_party": "Third-party licences and vendor attribution files",
    "web": "React 18 + TypeScript + Monaco Editor SPA IDE frontend",
    "web/e2e": "Frontend edge-case fixtures and Playwright/CDP runners",
    "web/public": "Static web assets and pre-paint theme initializer script",
    "web/qa": "Browser diagnostics and reference frame metrics readers",
    "web/src": "Frontend React components, state, Monaco hooks, and theme system",
    "web/src/api": "Typed HTTP API client and backend serializers",
    "web/src/components": "Modular UI components (TopBar, Editor, Problems, Flyouts)",
    "web/src/editor": "Monaco editor navigation and action controllers",
    "web/src/model": "Frontend finding and token adaptation data models",
    "web/src/monaco": "Monaco markers, decorations, code actions, and themes",
    "web/src/samples": "Bundled fallback sample snippets",
    "web/src/state": "Global state reducer, actions, and multi-file workspace store",
    "web/src/test": "Vitest frontend component, guard, and utility unit tests",
    "web/src/theme": "Semantic CSS variable tokens and dynamic Monaco themes",
    "web/src/tokens": "Pure token security classification derivation engine",
    "web/src/utils": "Diff computation, breadcrumbs, and UI scale utilities",
}


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_tracked_files() -> list[Path]:
    res = subprocess.run(
        ["git", "ls-files", "-s"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    files = []
    for line in res.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 4:
            mode, rel_path = parts[0], " ".join(parts[3:])
            p = ROOT / rel_path
            if p.is_file():
                files.append((p, mode, rel_path))
    return files


def main() -> None:
    print("Collecting files...")
    tracked_entries = get_tracked_files()

    # 1. Tracked artifacts that shouldn't be tracked
    junk_patterns = [
        re.compile(r"__pycache__"),
        re.compile(r"\.pyc$"),
        re.compile(r"^\.venv/"),
        re.compile(r"^node_modules/"),
        re.compile(r"^dist/"),
        re.compile(r"\.coverage$"),
        re.compile(r"^logs/.*\.log$"),
        re.compile(r"\.DS_Store$"),
        re.compile(r"\.log$"),
        re.compile(r"\.tmp$"),
        re.compile(r"\.bak$"),
        re.compile(r"\.orig$"),
        re.compile(r"\.swp$"),
    ]
    tracked_junk = []
    for _p, _mode, rel in tracked_entries:
        rel_posix = rel.replace("\\", "/")
        for pat in junk_patterns:
            if pat.search(rel_posix):
                tracked_junk.append(rel_posix)
                break

    # 2. Duplicate files by SHA-256 hash (excluding legacy/)
    print("Checking duplicate files...")
    hashes: dict[str, list[str]] = {}
    for p, _mode, rel in tracked_entries:
        rel_posix = rel.replace("\\", "/")
        if rel_posix.startswith("legacy/"):
            continue
        try:
            h = compute_sha256(p)
            hashes.setdefault(h, []).append(rel_posix)
        except Exception:
            pass
    duplicates = {h: locs for h, locs in hashes.items() if len(locs) > 1}

    # 3. Empty files and empty directories
    print("Checking empty files and empty directories...")
    empty_files = []
    for p, _mode, rel in tracked_entries:
        try:
            if p.stat().st_size == 0:
                empty_files.append(rel.replace("\\", "/"))
        except Exception:
            pass

    empty_dirs = []
    for root, dirs, files in os.walk(ROOT):
        rel_root = str(Path(root).relative_to(ROOT)).replace("\\", "/")
        if any(
            rel_root.startswith(ignored) for ignored in (".git", ".venv", "node_modules", "legacy")
        ):
            continue
        if not dirs and not files:
            empty_dirs.append(rel_root)

    # 4. Files over 1 MB
    print("Checking large files...")
    large_files = []
    for p, _mode, rel in tracked_entries:
        try:
            sz = p.stat().st_size
            if sz > 1024 * 1024:
                large_files.append((rel.replace("\\", "/"), round(sz / (1024 * 1024), 2)))
        except Exception:
            pass
    large_files.sort(key=lambda x: x[1], reverse=True)

    # 5. Line endings (CRLF / Mixed / LF) and UTF-8 validity
    print("Checking line endings and UTF-8 encodings...")
    crlf_files = []
    mixed_files = []
    non_utf8_files = []
    executable_files = []

    for p, mode, rel in tracked_entries:
        rel_posix = rel.replace("\\", "/")
        if mode == "100755":
            executable_files.append(rel_posix)

        try:
            raw = p.read_bytes()
        except Exception:
            continue

        try:
            text = raw.decode("utf-8")
            has_crlf = "\r\n" in text
            has_lone_lf = bool(re.search(r"(?<!\r)\n", text))
            if has_crlf and has_lone_lf:
                mixed_files.append(rel_posix)
            elif has_crlf:
                crlf_files.append(rel_posix)
        except UnicodeDecodeError:
            non_utf8_files.append(rel_posix)

    # 6. Secret-like strings
    print("Scanning for secret-like strings...")
    secret_findings = []
    secret_patterns = [
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
        (re.compile(r"ghp_[0-9a-zA-Z]{36}"), "GitHub Personal Access Token"),
        (re.compile(r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"), "Private Key"),
        (
            re.compile(
                r"(api[_-]?key|secret[_-]?key|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
                re.IGNORECASE,
            ),
            "Generic Hardcoded Secret",
        ),
    ]
    for p, _mode, rel in tracked_entries:
        rel_posix = rel.replace("\\", "/")
        if (
            rel_posix.startswith("legacy/")
            or "tests/fixtures" in rel_posix
            or "samples" in rel_posix
            or "tests/golden" in rel_posix
        ):
            continue  # Security test fixtures intentionally contain synthetic sample secrets
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            for pat, desc in secret_patterns:
                for m in pat.finditer(content):
                    secret_findings.append(
                        {
                            "file": rel_posix,
                            "description": desc,
                            "snippet": m.group(0)[:40] + "...",
                        }
                    )
        except Exception:
            pass

    # 7. Large generated outputs in reports/
    print("Checking reports directory...")
    report_files = []
    reports_dir = ROOT / "reports"
    for p in reports_dir.rglob("*"):
        if p.is_file():
            sz = p.stat().st_size
            rel_rep = str(p.relative_to(ROOT)).replace("\\", "/")
            report_files.append((rel_rep, sz))
    report_files.sort(key=lambda x: x[1], reverse=True)

    # Write Markdown
    print("Formatting docs/cleanup/inventory.md...")
    lines = [
        "# Repository Inventory — CLEAN-1",
        "",
        "**Generated:** October 10, 2026  ",
        "**Scope:** Full repository audit excluding read-only `legacy/` modifications.  ",
        "",
        "---",
        "",
        "## 1. Folder Tree (Depth 3) & Purpose",
        "",
        "| Directory | Purpose |",
        "|---|---|",
    ]
    for folder, purpose in sorted(FOLDER_PURPOSES.items()):
        if folder == ".":
            lines.append(f"| `.` (root) | {purpose} |")
        else:
            lines.append(f"| `{folder}/` | {purpose} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 2. Tracked Artefacts & Stray Cache Files",
            "",
            f"**Total stray tracked artefacts found:** {len(tracked_junk)}",
            "",
        ]
    )
    if tracked_junk:
        for f in tracked_junk:
            lines.append(f"- `{f}`")
    else:
        lines.append(
            "*None. All build outputs, logs, and environments are properly excluded by git.*"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Duplicate Files by SHA-256 Hash",
            "",
            f"**Duplicate file clusters (outside `legacy/`):** {len(duplicates)}",
            "",
        ]
    )
    for h, locs in duplicates.items():
        lines.append(f"- **SHA-256:** `{h[:12]}...` ({len(locs)} copies):")
        for loc in locs:
            lines.append(f"  - `{loc}`")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. Empty Files and Directories",
            "",
            f"**Empty (0-byte) tracked files:** {len(empty_files)}",
            "",
        ]
    )
    for ef in empty_files:
        lines.append(f"- `{ef}` (intentional package or git anchor if `__init__.py` or `.gitkeep`)")

    lines.extend(
        [
            "",
            f"**Empty directories:** {len(empty_dirs)}",
            "",
        ]
    )
    if empty_dirs:
        for ed in empty_dirs:
            lines.append(f"- `{ed}/`")
    else:
        lines.append("*None.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 5. Large Files (> 1 MB)",
            "",
            f"**Total files > 1 MB:** {len(large_files)}",
            "",
            "| Path | Size (MB) | Category | Action |",
            "|---|---|---|---|",
        ]
    )
    for lf, sz in large_files:
        category = (
            "Model weights"
            if "ml/artifacts" in lf
            else ("Web bundle" if "web/dist" in lf else "Dataset/Doc")
        )
        action = (
            "Preserve (Required runtime artifact)"
            if "artifacts" in lf or "dist" in lf
            else "Review"
        )
        lines.append(f"| `{lf}` | {sz} MB | {category} | {action} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 6. Line Endings & Encodings",
            "",
            f"- **Files with CRLF line endings:** {len(crlf_files)}",
            f"- **Files with Mixed line endings:** {len(mixed_files)}",
            f"- **Non-UTF-8 / Binary files:** {len(non_utf8_files)} (images, model weights, binaries)",
            f"- **Executable tracked files (mode 100755):** {len(executable_files)}",
            "",
        ]
    )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 7. Secret-Like Strings Audit",
            "",
            f"**Suspicious string patterns outside test fixtures/samples:** {len(secret_findings)}",
            "",
        ]
    )
    if secret_findings:
        for sf in secret_findings:
            lines.append(f"- `{sf['file']}`: {sf['description']} (`{sf['snippet']}`)")
    else:
        lines.append("*None found in production source or configuration files.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 8. Large Generated Outputs in `reports/`",
            "",
            "| Report File | Size |",
            "|---|---|",
        ]
    )
    for rf, sz in report_files[:15]:
        lines.append(f"| `{rf}` | {round(sz / 1024, 2)} KB |")

    out_file = ROOT / "docs" / "cleanup" / "inventory.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Inventory written to {out_file}.")


if __name__ == "__main__":
    main()
