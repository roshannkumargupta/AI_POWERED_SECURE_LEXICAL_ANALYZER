"""Markdown link validation script for SecureLex IDE.

Verifies that all local relative file links in README.md and docs/ resolve
to existing files on disk.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Match markdown links: [text](target)
LINK_PATTERN = re.compile(r"\[(?P<text>[^\]]*)\]\((?P<url>[^\)]+)\)")


def is_external_or_special(url: str) -> bool:
    """Check if the URL is external or an anchor/special link."""
    trimmed = url.strip()
    if not trimmed:
        return True
    return trimmed.startswith(("#", "http://", "https://", "mailto:", "ftp:", "data:"))


def validate_file_links(md_file: Path) -> list[tuple[int, str, str]]:
    """Scan a markdown file for broken relative links.

    Returns a list of (line_number, link_text, target_url) tuples for broken links.
    """
    broken: list[tuple[int, str, str]] = []
    try:
        content = md_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not read {md_file}: {e}")
        return broken

    lines = content.splitlines()
    for line_no, line in enumerate(lines, start=1):
        for match in LINK_PATTERN.finditer(line):
            target = match.group("url").strip()
            # Split off query parameters or anchor fragments
            target_clean = target.split("?")[0].split("#")[0]
            if not target_clean or is_external_or_special(target):
                continue

            # Check relative to document location
            candidate_1 = (md_file.parent / target_clean).resolve()
            # Check relative to repository root
            candidate_2 = (ROOT / target_clean.lstrip("/\\")).resolve()

            if not candidate_1.exists() and not candidate_2.exists():
                broken.append((line_no, match.group("text"), target))

    return broken


def main() -> int:
    search_files: list[Path] = []

    # 1. Root README.md
    root_readme = ROOT / "README.md"
    if root_readme.exists():
        search_files.append(root_readme)

    # 2. All markdown files in docs/
    docs_dir = ROOT / "docs"
    if docs_dir.exists():
        search_files.extend(sorted(docs_dir.rglob("*.md")))

    total_links = 0
    total_broken = 0

    print("Checking markdown link integrity...")
    for md_file in search_files:
        broken_links = validate_file_links(md_file)
        if broken_links:
            rel_file = md_file.relative_to(ROOT)
            print(f"\n[FAIL] {rel_file}:")
            for line_no, text, target in broken_links:
                total_broken += 1
                print(f"  Line {line_no}: [{text}]({target}) -> Target not found")
        else:
            total_links += 1

    if total_broken > 0:
        print(f"\nFound {total_broken} broken markdown link(s).")
        return 1

    print(f"\n[OK] All markdown links verified across {len(search_files)} documentation files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
