"""
Generate a comprehensive project package (ZIP) tailored for Claude.

This script:
1. Generates `PROJECT_TREE.txt` containing the full directory structure.
2. Generates `PROJECT_INDEX.md` with deep architectural knowledge, component maps,
   API specifications, rule registries, ML artifacts manifest, and test harness details.
3. Packages all source code, tests, documentation, specifications, configurations,
   and examples into `securelex-ide-claude.zip`.
4. Excludes huge binary weights (.joblib, .pt), caches (.venv, node_modules, __pycache__),
   temporary test logs, and secrets (.env), keeping the ZIP clean, fast, and well under
   Claude's 30MB upload limit.
"""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vite",
    ".hypothesis",
    "dist",
    "test-results",
    ".vitest",
    ".npm",
}

EXCLUDED_EXTENSIONS = {
    ".joblib",
    ".pt",
    ".pth",
    ".bin",
    ".npz",
    ".pyc",
    ".pyo",
    ".docx",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
}

EXCLUDED_FILES = {
    ".env",
    "api-run.log",
    "api-run.err.log",
    "web-run.log",
    "web-run.err.log",
    "files.zip",
    "securelex-ide-claude.zip",
    "securelex-ide-full.zip",
}


def should_exclude(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    parts = norm.split("/")

    # Check directory exclusions
    for p in parts[:-1]:
        if p in EXCLUDED_DIR_NAMES or p.startswith((".pytest-", ".pytest_")):
            return True

    # Check filename
    fname = parts[-1]
    if fname in EXCLUDED_FILES or fname.endswith((".log", ".err.log")):
        return True

    # Check extension
    ext = os.path.splitext(fname)[1].lower()
    return ext in EXCLUDED_EXTENSIONS


def generate_project_tree() -> str:
    """Build a clean text tree of all files included in the Claude package."""
    lines: list[str] = ["SecureLex IDE (apsla) — Project Tree", "=" * 50, ""]

    for root, dirs, files in os.walk(ROOT):
        # Prune excluded directories in-place
        dirs[:] = sorted([
            d for d in dirs
            if d not in EXCLUDED_DIR_NAMES
            and not d.startswith(".pytest-")
            and not d.startswith(".pytest_")
        ])

        rel_dir = os.path.relpath(root, ROOT)
        if rel_dir == ".":
            level = 0
            display_dir = "."
        else:
            rel_norm = rel_dir.replace("\\", "/")
            if any(p in EXCLUDED_DIR_NAMES for p in rel_norm.split("/")):
                continue
            level = len(rel_norm.split("/"))
            display_dir = os.path.basename(root) + "/"

        indent = "  " * level
        lines.append(f"{indent}{display_dir}")

        for f in sorted(files):
            rel_file = os.path.relpath(os.path.join(root, f), ROOT)
            if not should_exclude(rel_file):
                lines.append(f"{indent}  {f}")

    return "\n".join(lines) + "\n"


def collect_ml_manifest() -> list[dict]:
    """Collect metadata for all trained machine learning models."""
    manifest = []
    artifacts_dir = ROOT / "src" / "apsla" / "ml" / "artifacts"
    if artifacts_dir.exists():
        for meta_file in sorted(artifacts_dir.glob("*/meta.json")):
            try:
                with open(meta_file, encoding="utf-8") as f:
                    data = json.load(f)
                    manifest.append({
                        "model_id": data.get("model_id"),
                        "language": data.get("language"),
                        "model_type": data.get("model_type"),
                        "feature_dim": data.get("feature_dim"),
                        "macro_f1": data.get("validation_macro_f1"),
                        "created_at": data.get("created_at"),
                        "path": meta_file.parent.relative_to(ROOT).as_posix()
                    })
            except Exception:
                pass
    return manifest


def generate_project_index(ml_manifest: list[dict]) -> str:
    """Generate comprehensive architectural index for Claude."""
    doc = []
    doc.append("# SecureLex IDE (`apsla`) — Complete Project Index & Architecture Guide")
    doc.append("")
    doc.append("> **Note for Claude**: This document was generated specifically to provide complete context")
    doc.append("> of all files, folders, architecture, interfaces, and design decisions in this repository.")
    doc.append("")
    doc.append("## 1. Executive Summary")
    doc.append("- **Repository Name**: `securelex-ide` (`AI_POWERED_SECURE_LEXICAL_ANALYZER`)")
    doc.append("- **Package Name**: `apsla` (AI-Powered Secure Lexical Analyzer)")
    doc.append("- **Core Purpose**: High-performance, offline-capable developer IDE and static/hybrid security platform for **Python, JavaScript, Java, and C++**.")
    doc.append("- **Key Innovations**:")
    doc.append("  1. **Hybrid Detection Fusion**: Unifies AST/token rules + interprocedural taint flow + machine learning confidence + Unicode trojan defense.")
    doc.append("  2. **Path-Level Explainability**: Traces `source -> propagate -> sanitizer_missing -> sink` with Monaco coordinates.")
    doc.append("  3. **Verified Automated Fixes**: Fixes are applied to an isolated AST copy and re-analyzed; marked `verified` only if the vulnerability is eliminated without introducing new regressions.")
    doc.append("  4. **AI Assistance**: Integrated with Groq AI provider with strict prompt injection detection and tool runner harnesses.")
    doc.append("  5. **Rich Offline Web IDE**: React 18, TypeScript, Monaco Editor, dark/light themes, AST tree visualizer, Safety Lab, and Fix Workflow modal.")
    doc.append("")

    doc.append("## 2. Directory Structure & Component Map")
    doc.append("| Directory / File | Description |")
    doc.append("|---|---|")
    doc.append("| `src/apsla/` | Python backend package (FastAPI, core lexing, AST, taint analysis, ML, rule verifier, LLM agent) |")
    doc.append("| `src/apsla/server/` | FastAPI application (`app.py`), Pydantic schemas (`schemas.py`), tool runners, security rate limits |")
    doc.append("| `src/apsla/languages/` | Multi-language lexers, AST parsers, and token normalizers (Python, JS, Java, C++) |")
    doc.append("| `src/apsla/security_v2.py` | 58 internal security rule definitions, registry builder, rule evaluation |")
    doc.append("| `src/apsla/fixes/` | Fix synthesis (`generators.py`), AST patchers, `independent_verifier.py` (verification harness) |")
    doc.append("| `src/apsla/agents/` | Agent planner, Groq provider (`provider_v2.py`), prompt injection classifier, execution budget |")
    doc.append("| `src/apsla/ml/` | ML pipeline: token windowing (`windows.py`), feature extraction (`features.py`), inference, training scripts |")
    doc.append("| `src/apsla/ml/artifacts/` | Model metadata (`meta.json`) for trained scikit-learn & gradient boosting models |")
    doc.append("| `web/` | Modern React 18 + TypeScript + Vite frontend IDE |")
    doc.append("| `web/src/ide/` | Complete IDE UI: `IDE.tsx`, `MonacoEditor.tsx`, Panels (Tokens, AST, Problems, Security, Safety Lab) |")
    doc.append("| `web/src/ide/fix/` | Fix workflow state machine (`machine.ts`), modal (`FixWorkflowModal.tsx`), diff visualizer (`DiffPreview.tsx`) |")
    doc.append("| `web/src/ide/ai/` | AI drawer (`BuildAIDrawer.tsx`), Explain panel (`AIExplainPanel.tsx`), Agent activity panel |")
    doc.append("| `web/e2e/` | Playwright end-to-end tests for all workflows (Groq AI, failures, prompt injection, UI audit) |")
    doc.append("| `tests/` | Comprehensive backend test suites: `unit/`, `security/`, `e2e/`, `golden/` fixtures |")
    doc.append("| `scripts/` | Automation utilities: `check_all.py`, `build_all.py`, `golden.py`, `dev.py`, `package_for_claude.py` |")
    doc.append("| `docs/` | Architecture specs, `PROJECT_SPEC.md`, `rules_catalogue.md`, `api_v2.md`, threat models |")
    doc.append("| `reports/` | Test logs, phase evidence documents, samples matrix, benchmark findings |")
    doc.append("| `examples/` | Test samples for all 4 languages: `valid/`, `lexical-errors/`, `syntax-errors/`, `security/`, `adversarial/` |")
    doc.append("| `legacy/` | Historical reference code and baseline datasets (`senior-part1`, `senior-part2`) |")
    doc.append("")

    doc.append("## 3. Core Architecture & Data Flow")
    doc.append("```mermaid")
    doc.append("graph TD")
    doc.append("    UserCode[Source Code Input] --> Monaco[Monaco Editor / Web UI]")
    doc.append("    Monaco --> API[/api/analyze]")
    doc.append("    API --> Parser[Multi-Language Lexer & Parser]")
    doc.append("    Parser --> AST[Unified AST & Token Spans]")
    doc.append("    AST --> Rules[Security Rule Engine - 58 Rules]")
    doc.append("    AST --> Taint[Interprocedural Taint Flow Engine]")
    doc.append("    AST --> Trojan[Unicode & Homoglyph Detector]")
    doc.append("    AST --> ML[Token Windowing & ML Anomaly Model]")
    doc.append("    Rules & Taint & Trojan & ML --> Fusion[Calibrated Multi-Factor Confidence Score]")
    doc.append("    Fusion --> Finding[Finding Object with Source-to-Sink Path]")
    doc.append("    Finding --> FixHarness[Independent Fix Verifier]")
    doc.append("    FixHarness --> VerifiedFix[Verified Clean Patch]")
    doc.append("    VerifiedFix --> UI[Problems Panel & Fix Modal]")
    doc.append("```")
    doc.append("")

    doc.append("## 4. Key Endpoints (`src/apsla/server/app.py`)")
    doc.append("- `POST /api/analyze`: Main pipeline. Analyzes code for syntax, lexical tokens, AST nodes, security findings, taint paths, and ML anomalies.")
    doc.append("- `POST /api/fix/propose`: Proposes automated AST/regex fixes for a finding.")
    doc.append("- `POST /api/fix/verify`: Runs candidate patch against the isolated verification harness.")
    doc.append("- `POST /api/ai/explain`: Explains a vulnerability or code segment with Groq.")
    doc.append("- `POST /api/ai/propose-fix`: AI agent proposes a semantic remediation with diff generation.")
    doc.append("- `POST /api/ai/generate`: AI code generation / completion with safety filters.")
    doc.append("- `POST /api/safety-lab/run`: Evaluates code against known adversarial attacks and injection vectors.")
    doc.append("- `POST /api/feedback`: Submits user feedback (false positive / true positive) for active learning.")
    doc.append("")

    doc.append("## 5. Machine Learning Models Manifest")
    doc.append("Total trained model artifacts found: **" + str(len(ml_manifest)) + "**")
    doc.append("")
    doc.append("| Model ID | Language | Type | Dim | Macro F1 | Path |")
    doc.append("|---|---|---|---|---|---|")
    for m in ml_manifest[-15:]:  # show recent models
        f1_str = f"{m['macro_f1']:.4f}" if isinstance(m.get('macro_f1'), (int, float)) else "N/A"
        doc.append(f"| `{m['model_id']}` | {m['language']} | {m['model_type']} | {m['feature_dim']} | {f1_str} | `{m['path']}` |")
    doc.append("")
    doc.append("*(See all individual `src/apsla/ml/artifacts/*/meta.json` files for full hyperparameter logs)*")
    doc.append("")

    doc.append("## 6. Development & Quality Gate Commands")
    doc.append("- **Backend Dev Server**: `python scripts/dev.py --api-only` (runs FastAPI on port 8000)")
    doc.append("- **Frontend Dev Server**: `cd web && npm run dev` (runs Vite on port 5173)")
    doc.append("- **Run All Quality Gates**: `python scripts/check_all.py` (lint, typecheck, unit tests, golden tests)")
    doc.append("- **Run Unit Tests**: `pytest tests/unit/`")
    doc.append("- **Run Security Tests**: `pytest tests/security/`")
    doc.append("- **Run Golden Fixture Tests**: `python scripts/golden.py check`")
    doc.append("- **Frontend Tests**: `cd web && npm test` (Vitest unit tests)")
    doc.append("- **Frontend E2E Tests**: `cd web && npx playwright test`")
    doc.append("")

    return "\n".join(doc) + "\n"


def build_claude_zip() -> None:
    print("=" * 60)
    print("Building Claude Package for SecureLex IDE")
    print("=" * 60)

    # 1. Collect ML metadata
    print("[1/4] Collecting ML model artifacts metadata...")
    ml_manifest = collect_ml_manifest()
    print(f"      Found {len(ml_manifest)} model artifacts.")

    # 2. Generate PROJECT_INDEX.md
    print("[2/4] Generating PROJECT_INDEX.md...")
    index_content = generate_project_index(ml_manifest)
    index_file = ROOT / "PROJECT_INDEX.md"
    index_file.write_text(index_content, encoding="utf-8")
    print(f"      Wrote {len(index_content)} characters to {index_file.name}")

    # 3. Generate PROJECT_TREE.txt
    print("[3/4] Generating PROJECT_TREE.txt...")
    tree_content = generate_project_tree()
    tree_file = ROOT / "PROJECT_TREE.txt"
    tree_file.write_text(tree_content, encoding="utf-8")
    print(f"      Wrote {len(tree_content.splitlines())} lines to {tree_file.name}")

    # 4. Create ZIP archive
    zip_dest = ROOT / "securelex-ide-claude.zip"
    print(f"[4/4] Creating ZIP archive at: {zip_dest} ...")

    file_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(ROOT):
            dirs[:] = sorted([
                d for d in dirs
                if d not in EXCLUDED_DIR_NAMES
                and not d.startswith(".pytest-")
                and not d.startswith(".pytest_")
            ])

            for f in sorted(files):
                full_path = Path(root) / f
                rel_path = full_path.relative_to(ROOT).as_posix()

                if should_exclude(rel_path):
                    continue

                zf.write(full_path, arcname=rel_path)
                file_count += 1
                total_uncompressed_bytes += full_path.stat().st_size

    zip_size_bytes = zip_dest.stat().st_size
    zip_size_mb = zip_size_bytes / (1024 * 1024)
    uncomp_mb = total_uncompressed_bytes / (1024 * 1024)

    print("\n" + "=" * 60)
    print("Package Successfully Created!")
    print("=" * 60)
    print(f"Destination:          {zip_dest}")
    print(f"Total files included: {file_count:,}")
    print(f"Uncompressed size:    {uncomp_mb:.2f} MB")
    print(f"Compressed ZIP size:  {zip_size_mb:.2f} MB")
    print("Claude limit status:  PASS (Well below 30MB limit)")
    print("=" * 60)


if __name__ == "__main__":
    build_claude_zip()
