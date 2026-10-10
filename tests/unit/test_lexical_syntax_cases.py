"""Comprehensive test suite verifying all 80 benchmark lexical and syntax test cases."""

from __future__ import annotations

import pytest

from apsla.fixes.edits import apply_edits
from apsla.pipeline import Analyzer

TEST_CASES = [
    {
        "id": 1,
        "language": "python",
        "type": "lexical",
        "code": 'x = "hello',
        "answer": "Unterminated string literal",
    },
    {
        "id": 2,
        "language": "python",
        "type": "lexical",
        "code": "x = '''hello",
        "answer": "Unterminated triple-quoted string",
    },
    {
        "id": 3,
        "language": "python",
        "type": "lexical",
        "code": "x = 0b102",
        "answer": "Invalid binary literal",
    },
    {
        "id": 4,
        "language": "python",
        "type": "lexical",
        "code": "x = 0xG1",
        "answer": "Invalid hexadecimal literal",
    },
    {
        "id": 5,
        "language": "python",
        "type": "lexical",
        "code": "x = 1__2",
        "answer": "Invalid numeric literal",
    },
    {
        "id": 6,
        "language": "python",
        "type": "lexical",
        "code": "x = 12abc",
        "answer": "Invalid numeric literal",
    },
    {
        "id": 7,
        "language": "python",
        "type": "lexical",
        "code": "x = 1e+",
        "answer": "Invalid exponent",
    },
    {
        "id": 8,
        "language": "python",
        "type": "lexical",
        "code": "x = 5 § 2",
        "answer": "Invalid character/token",
    },
    {
        "id": 9,
        "language": "python",
        "type": "lexical",
        "code": 'x = "\\uZZZZ"',
        "answer": "Malformed Unicode escape",
    },
    {
        "id": 10,
        "language": "python",
        "type": "lexical",
        "code": "x = 'abc\\",
        "answer": "Unterminated string or invalid line continuation",
    },
    {
        "id": 11,
        "language": "python",
        "type": "syntax",
        "code": "if x > 5 print(x)",
        "answer": "Missing colon",
    },
    {
        "id": 12,
        "language": "python",
        "type": "syntax",
        "code": "print(10",
        "answer": "Missing closing parenthesis",
    },
    {
        "id": 13,
        "language": "python",
        "type": "syntax",
        "code": "if x > 5:\nprint(x)",
        "answer": "Indentation error",
    },
    {
        "id": 14,
        "language": "python",
        "type": "syntax",
        "code": "def add(a b):",
        "answer": "Missing comma between parameters",
    },
    {
        "id": 15,
        "language": "python",
        "type": "syntax",
        "code": "if x = 5:",
        "answer": "Assignment used instead of comparison",
    },
    {
        "id": 16,
        "language": "python",
        "type": "syntax",
        "code": "for i in range(5) print(i)",
        "answer": "Missing colon",
    },
    {
        "id": 17,
        "language": "python",
        "type": "syntax",
        "code": "else:",
        "answer": "Unexpected else",
    },
    {
        "id": 18,
        "language": "python",
        "type": "syntax",
        "code": "def f(a, a):",
        "answer": "Duplicate parameter name",
    },
    {
        "id": 19,
        "language": "python",
        "type": "syntax",
        "code": "return 5",
        "answer": "Return outside function",
    },
    {
        "id": 20,
        "language": "python",
        "type": "syntax",
        "code": "x = (1 + 2]",
        "answer": "Mismatched brackets",
    },
    {
        "id": 21,
        "language": "java",
        "type": "lexical",
        "code": 'String s = "hello;',
        "answer": "Unterminated string literal",
    },
    {
        "id": 22,
        "language": "java",
        "type": "lexical",
        "code": "char c = 'ab';",
        "answer": "Invalid character literal",
    },
    {
        "id": 23,
        "language": "java",
        "type": "lexical",
        "code": "int x = 5 § 2;",
        "answer": "Illegal character",
    },
    {
        "id": 24,
        "language": "java",
        "type": "lexical",
        "code": "int x = 0b102;",
        "answer": "Invalid binary literal",
    },
    {
        "id": 25,
        "language": "java",
        "type": "lexical",
        "code": "int x = 0xG1;",
        "answer": "Invalid hexadecimal literal",
    },
    {
        "id": 26,
        "language": "java",
        "type": "lexical",
        "code": 'String s = "abc\\q";',
        "answer": "Illegal escape character",
    },
    {
        "id": 27,
        "language": "java",
        "type": "lexical",
        "code": "int x = 12abc;",
        "answer": "Malformed numeric literal/token",
    },
    {
        "id": 28,
        "language": "java",
        "type": "lexical",
        "code": 'String s = "abc',
        "answer": "Unterminated string literal",
    },
    {
        "id": 29,
        "language": "java",
        "type": "lexical",
        "code": "char c = '\\x';",
        "answer": "Illegal escape in character literal",
    },
    {
        "id": 30,
        "language": "java",
        "type": "lexical",
        "code": "int x = 0x;",
        "answer": "Invalid hexadecimal literal",
    },
    {
        "id": 31,
        "language": "java",
        "type": "syntax",
        "code": "int x = 10",
        "answer": "Missing semicolon",
    },
    {
        "id": 32,
        "language": "java",
        "type": "syntax",
        "code": "if (x > 5 {}",
        "answer": "Missing closing parenthesis",
    },
    {
        "id": 33,
        "language": "java",
        "type": "syntax",
        "code": 'System.out.println("Hi"',
        "answer": "Missing closing parenthesis",
    },
    {
        "id": 34,
        "language": "java",
        "type": "syntax",
        "code": "int = 10;",
        "answer": "Missing variable name",
    },
    {
        "id": 35,
        "language": "java",
        "type": "syntax",
        "code": "for (int i = 0 i < 5; i++) {}",
        "answer": "Missing semicolon",
    },
    {
        "id": 36,
        "language": "java",
        "type": "syntax",
        "code": "if x > 5 {}",
        "answer": "Missing parentheses around condition",
    },
    {
        "id": 37,
        "language": "java",
        "type": "syntax",
        "code": "class Demo {",
        "answer": "Missing closing brace",
    },
    {
        "id": 38,
        "language": "java",
        "type": "syntax",
        "code": "public void test( {}",
        "answer": "Malformed parameter list",
    },
    {
        "id": 39,
        "language": "java",
        "type": "syntax",
        "code": "switch (x) { case 1 System.out.println(x); }",
        "answer": "Missing colon after case label",
    },
    {
        "id": 40,
        "language": "java",
        "type": "syntax",
        "code": "break;",
        "answer": "Illegal break outside loop or switch",
    },
    {
        "id": 41,
        "language": "javascript",
        "type": "lexical",
        "code": 'let s = "hello;',
        "answer": "Unterminated string literal",
    },
    {
        "id": 42,
        "language": "javascript",
        "type": "lexical",
        "code": "let x = @;",
        "answer": "Invalid token",
    },
    {
        "id": 43,
        "language": "javascript",
        "type": "lexical",
        "code": "let x = 0xG1;",
        "answer": "Invalid hexadecimal literal",
    },
    {
        "id": 44,
        "language": "javascript",
        "type": "lexical",
        "code": "let x = 0b102;",
        "answer": "Invalid binary literal",
    },
    {
        "id": 45,
        "language": "javascript",
        "type": "lexical",
        "code": "let x = 1e+;",
        "answer": "Invalid numeric exponent",
    },
    {
        "id": 46,
        "language": "javascript",
        "type": "lexical",
        "code": "let s = 'abc",
        "answer": "Unterminated string literal",
    },
    {
        "id": 47,
        "language": "javascript",
        "type": "lexical",
        "code": "let x = #;",
        "answer": "Unexpected hash character",
    },
    {
        "id": 48,
        "language": "javascript",
        "type": "lexical",
        "code": "let x = 12abc;",
        "answer": "Invalid numeric literal/token",
    },
    {
        "id": 49,
        "language": "javascript",
        "type": "lexical",
        "code": "let r = /[/;",
        "answer": "Invalid regular-expression literal",
    },
    {
        "id": 50,
        "language": "javascript",
        "type": "lexical",
        "code": "let x = `hello;",
        "answer": "Unterminated template literal",
    },
    {
        "id": 51,
        "language": "javascript",
        "type": "syntax",
        "code": "if (x > 5 { console.log(x); }",
        "answer": "Missing closing parenthesis",
    },
    {
        "id": 52,
        "language": "javascript",
        "type": "syntax",
        "code": "function add(a, b { return a+b; }",
        "answer": "Missing closing parenthesis",
    },
    {
        "id": 53,
        "language": "javascript",
        "type": "syntax",
        "code": "const = 10;",
        "answer": "Missing variable name",
    },
    {
        "id": 54,
        "language": "javascript",
        "type": "syntax",
        "code": "if (x > 5) else {}",
        "answer": "Invalid else placement",
    },
    {
        "id": 55,
        "language": "javascript",
        "type": "syntax",
        "code": "for (let i = 0 i < 5; i++) {}",
        "answer": "Missing semicolon",
    },
    {
        "id": 56,
        "language": "javascript",
        "type": "syntax",
        "code": "function () {}",
        "answer": "Function declaration requires a name",
    },
    {
        "id": 57,
        "language": "javascript",
        "type": "syntax",
        "code": "return 5;",
        "answer": "Illegal top-level return in a normal script",
    },
    {
        "id": 58,
        "language": "javascript",
        "type": "syntax",
        "code": "let x = (1 + 2;",
        "answer": "Missing closing parenthesis",
    },
    {
        "id": 59,
        "language": "javascript",
        "type": "syntax",
        "code": "switch (x) { case 1 console.log(x); }",
        "answer": "Missing colon after case label",
    },
    {
        "id": 60,
        "language": "javascript",
        "type": "syntax",
        "code": "const x;",
        "answer": "Constant declaration requires initializer",
    },
    {
        "id": 61,
        "language": "cpp",
        "type": "lexical",
        "code": "int x = @;",
        "answer": "Invalid token",
    },
    {
        "id": 62,
        "language": "cpp",
        "type": "lexical",
        "code": 'string s = "hello;',
        "answer": "Unterminated string literal",
    },
    {
        "id": 63,
        "language": "cpp",
        "type": "lexical",
        "code": "int x = 0b102;",
        "answer": "Invalid binary literal",
    },
    {
        "id": 64,
        "language": "cpp",
        "type": "lexical",
        "code": "int x = 0xG1;",
        "answer": "Invalid hexadecimal literal",
    },
    {
        "id": 65,
        "language": "cpp",
        "type": "lexical",
        "code": "int x = 12abc;",
        "answer": "Invalid numeric literal",
    },
    {
        "id": 66,
        "language": "cpp",
        "type": "lexical",
        "code": "char c = '\\x';",
        "answer": "Incomplete hexadecimal escape",
    },
    {
        "id": 67,
        "language": "cpp",
        "type": "lexical",
        "code": "int x = 5 § 2;",
        "answer": "Invalid character/token",
    },
    {
        "id": 68,
        "language": "cpp",
        "type": "lexical",
        "code": 'string s = "abc\\',
        "answer": "Unterminated string or invalid line splice",
    },
    {
        "id": 69,
        "language": "cpp",
        "type": "lexical",
        "code": "int x = 1.2.3;",
        "answer": "Malformed numeric literal",
    },
    {
        "id": 70,
        "language": "cpp",
        "type": "lexical",
        "code": "/* comment",
        "answer": "Unterminated block comment",
    },
    {
        "id": 71,
        "language": "cpp",
        "type": "syntax",
        "code": "int main(){ int x = 10 return 0; }",
        "answer": "Missing semicolon",
    },
    {
        "id": 72,
        "language": "cpp",
        "type": "syntax",
        "code": "int main(){ if (x > 5 { cout << x; } }",
        "answer": "Missing closing parenthesis",
    },
    {
        "id": 73,
        "language": "cpp",
        "type": "syntax",
        "code": 'int main(){ cout << "Hi" return 0; }',
        "answer": "Missing semicolon",
    },
    {
        "id": 74,
        "language": "cpp",
        "type": "syntax",
        "code": "int main(){ int = 10; return 0; }",
        "answer": "Missing variable name",
    },
    {
        "id": 75,
        "language": "cpp",
        "type": "syntax",
        "code": "int main(){ for (int i = 0 i < 5; i++) {} }",
        "answer": "Missing semicolon in for loop",
    },
    {
        "id": 76,
        "language": "cpp",
        "type": "syntax",
        "code": "int main(){ if x > 5 { cout << x; } }",
        "answer": "Missing parentheses around condition",
    },
    {
        "id": 77,
        "language": "cpp",
        "type": "syntax",
        "code": "int main(){ return 0;",
        "answer": "Missing closing brace",
    },
    {
        "id": 78,
        "language": "cpp",
        "type": "syntax",
        "code": "int add(int a, int b { return a+b; }",
        "answer": "Missing closing parenthesis",
    },
    {
        "id": 79,
        "language": "cpp",
        "type": "syntax",
        "code": "int main(){ switch (x) { case 1 cout << x; } }",
        "answer": "Missing colon after case label",
    },
    {
        "id": 80,
        "language": "cpp",
        "type": "syntax",
        "code": "int main(){ break; return 0; }",
        "answer": "Illegal break outside loop or switch",
    },
]


@pytest.fixture(scope="module")
def analyzer() -> Analyzer:
    return Analyzer({"ml": False})


@pytest.mark.parametrize(
    "tc", TEST_CASES, ids=[f"{tc['language']}_{tc['type']}_{tc['id']:02d}" for tc in TEST_CASES]
)
def test_user_benchmark_case(analyzer: Analyzer, tc: dict[str, str | int]) -> None:
    res = analyzer.analyze(source=str(tc["code"]), language=str(tc["language"]))
    matching = [f for f in res.findings if f.kind in ("lexical", "syntax")]
    assert len(matching) > 0, f"Case #{tc['id']} failed to detect error in {tc['code']!r}"

    first = matching[0]
    assert first.kind == tc["type"], (
        f"Case #{tc['id']} expected kind={tc['type']!r}, got {first.kind!r}"
    )
    assert len(first.fixes) > 0, f"Case #{tc['id']} has no fixes attached"

    # Verify fix removes all lexical and syntax errors
    fix = first.fixes[0]
    assert len(fix.edits) > 0, f"Case #{tc['id']} fix has no edits"
    fixed_code = apply_edits(str(tc["code"]), fix.edits)
    re_res = analyzer.analyze(source=fixed_code, language=str(tc["language"]))
    re_errs = [f for f in re_res.findings if f.kind in ("lexical", "syntax")]
    assert len(re_errs) == 0, (
        f"Case #{tc['id']} fix left errors: {[(e.kind, e.message) for e in re_errs]}, fixed_code={fixed_code!r}"
    )
