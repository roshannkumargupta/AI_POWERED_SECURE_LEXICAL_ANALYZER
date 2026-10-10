#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# ruff: noqa: E402, F841, I001
from apsla.languages.python_lang import PythonPlugin
from apsla.languages.java_lang import JavaPlugin
from apsla.languages.javascript_lang import JavaScriptPlugin
from apsla.languages.cpp_lang import CppPlugin


def debug():
    py = PythonPlugin()
    jv = JavaPlugin()
    js = JavaScriptPlugin()
    cp = CppPlugin()

    # Python case 19: return 5
    print("--- Python case 19: return 5 ---")
    import ast

    try:
        ast.parse("return 5")
        print("ast.parse('return 5') SUCCEEDED!")
    except Exception as e:
        print("ast.parse('return 5') RAISED:", type(e), e)

    # Java case 22: char c = 'ab';
    print("\n--- Java case 22: char c = 'ab'; ---")
    tokens = jv.lex("char c = 'ab';")
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", jv.syntax_check("char c = 'ab';"))

    # Java case 26: String s = "abc\q";
    print('\n--- Java case 26: String s = "abc\\q"; ---')
    tokens = jv.lex('String s = "abc\\q";')
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", jv.syntax_check('String s = "abc\\q";'))

    # Java case 29: char c = '\x';
    print("\n--- Java case 29: char c = '\\x'; ---")
    tokens = jv.lex("char c = '\\x';")
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", jv.syntax_check("char c = '\\x';"))

    # Java case 40: break;
    print("\n--- Java case 40: break; ---")
    tokens = jv.lex("break;")
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", jv.syntax_check("break;"))

    # JS case 57: return 5;
    print("\n--- JS case 57: return 5; ---")
    tokens = js.lex("return 5;")
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", js.syntax_check("return 5;"))

    # C++ case 64: int x = 0xG1;
    print("\n--- C++ case 64: int x = 0xG1; ---")
    tokens = cp.lex("int x = 0xG1;")
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", cp.syntax_check("int x = 0xG1;"))

    # C++ case 65: int x = 12abc;
    print("\n--- C++ case 65: int x = 12abc; ---")
    tokens = cp.lex("int x = 12abc;")
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", cp.syntax_check("int x = 12abc;"))

    # C++ case 66: char c = '\x';
    print("\n--- C++ case 66: char c = '\\x'; ---")
    tokens = cp.lex("char c = '\\x';")
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", cp.syntax_check("char c = '\\x';"))

    # C++ case 80: int main(){ break; return 0; }
    print("\n--- C++ case 80: int main(){ break; return 0; } ---")
    tokens = cp.lex("int main(){ break; return 0; }")
    print("Tokens:", [(t.kind, t.text) for t in tokens])
    print("Syntax check:", cp.syntax_check("int main(){ break; return 0; }"))


if __name__ == "__main__":
    debug()
