"""Script to generate confusables.json from Unicode confusables.txt data source."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = REPO_ROOT / "data" / "sources" / "confusables.txt"
OUTPUT_DIR = REPO_ROOT / "src" / "apsla" / "unicode_defense" / "data"
OUTPUT_PATH = OUTPUT_DIR / "confusables.json"
REMOTE_URL = "https://www.unicode.org/Public/security/latest/confusables.txt"


def ensure_confusables_file() -> Path:
    """Ensure confusables.txt exists, downloading if necessary."""
    if SOURCES_PATH.exists() and SOURCES_PATH.stat().st_size > 0:
        return SOURCES_PATH

    print(f"Confusables file not found locally. Downloading from {REMOTE_URL}...")
    SOURCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(REMOTE_URL, SOURCES_PATH)
        print("Download complete.")
        return SOURCES_PATH
    except Exception as e:
        print(f"Failed to download confusables: {e}")
        return SOURCES_PATH


def build_confusables_json() -> int:
    """Parse confusables.txt and extract mappings that resolve to pure ASCII.

    Returns:
        int: Total number of confusable mappings saved.
    """
    file_path = ensure_confusables_file()
    if not file_path.exists():
        print(f"[ERROR] Could not find or download {file_path}")
        sys.exit(1)

    mapping: dict[str, str] = {}

    with open(file_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Format: <src_hex> ; <target_hex_seq> ; <type> # comment
            parts = line.split("#")[0].split(";")
            if len(parts) < 2:
                continue

            src_hex = parts[0].strip()
            target_hexs = parts[1].strip().split()

            try:
                src_char = chr(int(src_hex, 16))
                target_str = "".join(chr(int(h, 16)) for h in target_hexs)

                # Keep only mappings where target resolves strictly to ASCII
                if all(ord(c) < 128 for c in target_str) and src_char != target_str:
                    mapping[src_char] = target_str
            except (ValueError, OverflowError):
                continue

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"Generated {OUTPUT_PATH} with {len(mapping)} ASCII-resolving confusable mappings.")
    return len(mapping)


if __name__ == "__main__":
    build_confusables_json()
