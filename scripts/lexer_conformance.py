"""Compare the Python product lexer against Python's standard tokenizer."""

from __future__ import annotations

import io
import json
import sysconfig
import tokenize
from pathlib import Path

from apsla.languages import registry

IGNORED = {tokenize.ENCODING, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}


def main() -> None:
    root = Path(sysconfig.get_paths()["stdlib"])
    files = sorted(path for path in root.rglob("*.py") if "site-packages" not in str(path))[:120]
    checked = 0
    mismatches = 0
    tokens_compared = 0
    details: list[str] = []
    lexer = registry.get("python")
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            reference = [item.string for item in tokenize.generate_tokens(io.StringIO(source).readline) if item.type not in IGNORED]
            actual = [item.text for item in lexer.lex(source) if item.kind not in {"WHITESPACE", "NEWLINE", "INDENT", "DEDENT"}]
        except (OSError, UnicodeError, tokenize.TokenError, IndentationError, SyntaxError):
            continue
        checked += 1
        tokens_compared += max(len(reference), len(actual))
        if reference != actual:
            mismatches += 1
            if len(details) < 8:
                details.append(f"{path.name}: tokenize={len(reference)}, securelex={len(actual)}")
    try:
        from tree_sitter_language_pack import get_parser

        grammars = {}
        for name in ("java", "javascript", "cpp"):
            try:
                get_parser(name)
                grammars[name] = "loaded"
            except Exception as exc:  # grammar/tool failures are recorded as unavailable
                grammars[name] = f"unavailable: {type(exc).__name__}"
    except ImportError:
        grammars = dict.fromkeys(("java", "javascript", "cpp"), "unavailable: package not installed")
    print(json.dumps({"reference": "python tokenize", "stdlib_files": checked, "files_with_mismatch": mismatches, "token_boundaries_compared": tokens_compared, "examples": details, "other_grammars": grammars}, indent=2))
    if checked < 100:
        raise SystemExit(f"Only {checked} Python stdlib files could be compared; minimum is 100")


if __name__ == "__main__":
    main()
