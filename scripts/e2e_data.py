#!/usr/bin/env python3
"""
scripts/e2e_data.py
Generates special test fixture files in web/e2e/fixtures/ for UI-9 testing.
"""

from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "web" / "e2e" / "fixtures"


def generate_fixtures() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. UTF-8 with BOM
    (FIXTURES_DIR / "utf8_bom.py").write_bytes(
        b"\xef\xbb\xbf# UTF-8 with BOM\ndef hello():\n    print('Hello with BOM')\n"
    )

    # 2. CRLF newlines
    (FIXTURES_DIR / "crlf.py").write_bytes(
        b'def add(a, b):\r\n    """Add two numbers."""\r\n    return a + b\r\n'
    )

    # 3. Mixed newlines
    (FIXTURES_DIR / "mixed_newlines.py").write_bytes(
        b"line1 = 1\r\nline2 = 2\nline3 = 3\rline4 = 4\n"
    )

    # 4. Emoji and CJK characters
    (FIXTURES_DIR / "emoji_cjk.py").write_text(
        "# Emojis: 🛡️ 🔥 🚀 💻\n"
        "# CJK characters: 你好世界 (Chinese), こんにちは (Japanese), 안녕하세요 (Korean)\n"
        "greeting = '🛡️ 安全分析 / セキュリティ / 보안'\n"
        "status = '🔥 Critical finding'\n",
        encoding="utf-8",
    )

    # 5. 300-line file
    lines_300 = ["# 300-line test file"]
    for i in range(1, 300):
        lines_300.append(f"def func_{i}():\n    return {i}")
    (FIXTURES_DIR / "lines_300.py").write_text("\n".join(lines_300) + "\n", encoding="utf-8")

    # 6. File with 5,000+ tokens
    # E.g. array with 2,500 numbers => [num, comma] = 5,000 tokens
    tokens_content = ["# 5000+ tokens test file", "numbers = ["]
    for i in range(2500):
        tokens_content.append(f"    {i},")
    tokens_content.append("]")
    (FIXTURES_DIR / "tokens_5000.py").write_text("\n".join(tokens_content) + "\n", encoding="utf-8")

    # 7. Near 500 KB file (~490 KB)
    chunk = "var_item_data = 'A' * 100\n" * 10
    repeats = (490 * 1024) // len(chunk)
    near_500k = "# Near 500KB test file\n" + (chunk * repeats)
    (FIXTURES_DIR / "near_500kb.py").write_text(near_500k, encoding="utf-8")

    # 8. Over 512 KB file (~525 KB)
    repeats_over = (525 * 1024) // len(chunk)
    over_512k = "# Over 512KB test file\n" + (chunk * repeats_over)
    (FIXTURES_DIR / "over_512kb.py").write_text(over_512k, encoding="utf-8")

    # 9. Invalid UTF-8 bytes
    (FIXTURES_DIR / "invalid_utf8.py").write_bytes(
        b"# Invalid UTF-8 bytes\nmsg = '\xff\xfe\x80\x81 bad bytes'\n"
    )

    # 10. Empty file
    (FIXTURES_DIR / "empty.py").write_bytes(b"")

    # 11. Whitespace only
    (FIXTURES_DIR / "whitespace_only.py").write_text("   \n\t\t\n   \r\n\t\n", encoding="utf-8")

    # 12. Binary file with .py extension
    (FIXTURES_DIR / "binary_as_py.py").write_bytes(
        b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00>\x00\x01\x00\x00\x00\x00\x00\x00"
    )

    # 13. Very long single line (50,000 characters)
    (FIXTURES_DIR / "long_single_line.py").write_text(
        "long_array = [" + ",".join(str(i) for i in range(10000)) + "]\n",
        encoding="utf-8",
    )

    # 14. Lexical error files per language
    # Python: unterminated string
    (FIXTURES_DIR / "lexical_error_py.py").write_text(
        "message = \"unterminated string literal\nprint('done')\n",
        encoding="utf-8",
    )

    # Java: unterminated char literal / illegal character
    (FIXTURES_DIR / "lexical_error_java.java").write_text(
        "public class BadLex {\n    char c = 'ab;\n    int x = 1;\n}\n",
        encoding="utf-8",
    )

    # JavaScript: unterminated template literal / illegal character
    (FIXTURES_DIR / "lexical_error_js.js").write_text(
        "const str = `unterminated template literal\nconsole.log(str);\n",
        encoding="utf-8",
    )

    # C/C++: unterminated string literal
    (FIXTURES_DIR / "lexical_error_cpp.cpp").write_text(
        '#include <stdio.h>\nint main() {\n    const char* s = "unterminated;\n    return 0;\n}\n',
        encoding="utf-8",
    )

    print(f"Generated {len(list(FIXTURES_DIR.glob('*')))} fixtures in {FIXTURES_DIR}")


if __name__ == "__main__":
    generate_fixtures()
