# SL2-0 Environment Probe

Captured 2026-10-12 in the repository root. Each entry records the command that was actually issued and its observable output. `ABSENT` means command lookup failed; launch failures are reported separately.

| Area | Exact command | Result |
|---|---|---|
| Python | `python --version` | `Python 3.12.5` |
| pip | `pip --version` | `pip 26.1.2 from C:\Users\ROSHAN GUPTA\AppData\Local\Programs\Python\Python312\Lib\site-packages\pip (python 3.12)` |
| Node | `node --version` | `v24.11.1` |
| npm | `npm --version` | `11.6.2` |
| Git | `git --version` | `git version 2.46.2.windows.1` |
| g++ | `Get-Command g++` then `g++ --version` | Present at `C:\MinGW\bin\g++.exe`; failed to launch: `Illegal System DLL Relocation` / reserved system DLL address conflict. |
| gcc | `Get-Command gcc` then `gcc --version` | Present at `C:\MinGW\bin\gcc.exe`; same launch failure as g++. |
| clang | `Get-Command clang` | Absent from PATH. |
| clang++ | `Get-Command clang++` | Absent from PATH. |
| clang-tidy | `Get-Command clang-tidy` | Absent from PATH. |
| cppcheck | `Get-Command cppcheck` | Absent from PATH. |
| Java | `Get-Command java` then `java -version` | `java version "1.8.0_401"`; Java(TM) SE Runtime Environment build `1.8.0_401-b10`; 64-Bit Server VM build `25.401-b10`. The earlier `java --version` spelling is unsupported by this runtime. |
| javac | `Get-Command javac` | Absent from PATH. |
| semgrep | `Get-Command semgrep` | Absent from PATH. |
| bandit | `Get-Command bandit` | Absent from PATH. |
| Ruff | `ruff --version` | `ruff 0.16.8` |
| pyflakes | `Get-Command pyflakes` | Absent from PATH. |
| mypy | `Get-Command mypy`; `.\.venv\Scripts\mypy.exe --version` | Global command absent; project venv returns `mypy 2.4.0 (compiled: yes)`. |
| ESLint | `Get-Command eslint`; `node web/node_modules/eslint/bin/eslint.js --version` | Global command absent; project local version is `v9.39.5`. `npm.cmd run lint --prefix web` printed `> eslint src` but did not finish before interruption. |
| Ollama | `ollama --version` | Client `0.40.2`; `Warning: could not connect to a running Ollama instance`. Reachability: no. Models: not enumerable while service is unreachable. |
| Tree-sitter CLI | `Get-Command tree-sitter` | Absent from PATH. |
| Tree-sitter Python packages/grammars | `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -c "from tree_sitter import Language, Parser; import tree_sitter_cpp as cpp, tree_sitter_java as java, tree_sitter_javascript as js, tree_sitter_python as py; grammars=[('python',py.language(),'x=1\\n'),('java',java.language(),'class X { int f(){ return 1; } }'),('javascript',js.language(),'const x = 1;'),('cpp',cpp.language(),'int main(){return 0;}')]; [(lambda name, lang, src: (lambda tree: print(name, 'loaded', 'parse_error='+str(tree.root_node.has_error)))(Parser(Language(lang)).parse(src.encode())))(*g) for g in grammars]"` | All four grammar constructions and parses succeeded: `python loaded parse_error=False`, `java loaded parse_error=False`, `javascript loaded parse_error=False`, `cpp loaded parse_error=False`. Core and all four grammar modules were importable. |
| Playwright | `node -e "for (const p of ['playwright','playwright-core','puppeteer']) { try { console.log(p+': '+require.resolve(p,{paths:['./web']})) } catch { console.log(p+': ABSENT') } }"` | `playwright: ABSENT`, `playwright-core: ABSENT`, `puppeteer: ABSENT` from `web`. |
| Playwright browser cache | `Get-ChildItem web/node_modules/.cache/ms-playwright; Get-ChildItem $env:LOCALAPPDATA/ms-playwright` | No browser installation listed. |

## Exact Tree-sitter probe

The executed PowerShell command set `$env:PYTHONPATH='src'`, piped the following Python script through a PowerShell here-string to `\.venv\Scripts\python.exe -`, and printed a result for each grammar:

```python
from tree_sitter import Language, Parser
import tree_sitter_cpp as cpp
import tree_sitter_java as java
import tree_sitter_javascript as javascript
import tree_sitter_python as python
samples = [('python', python.language(), 'x=1'), ('java', java.language(), 'class X { int f(){ return 1; } }'), ('javascript', javascript.language(), 'const x = 1;'), ('cpp', cpp.language(), 'int main(){return 0;}')]
for name, grammar, source in samples:
    tree = Parser(Language(grammar)).parse(source.encode())
    print(f'{name} loaded parse_error={tree.root_node.has_error}')
```

The observed output was `python loaded parse_error=False`, `java loaded parse_error=False`, `javascript loaded parse_error=False`, `cpp loaded parse_error=False`.

## Verification commands

- `ruff check .` produced `Found 1 error`: unsorted imports in pre-existing untracked `run_tests.py` (I001). This file was not changed.
- Ruff output began `I001 [*] Import block is un-sorted or un-formatted` at `run_tests.py:1:1` and ended `Found 1 error. 1 fixable with the --fix option.`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q --basetemp=reports/sl2-pytest` was started. It produced no test summary/output before the process stopped responding; the process/session ended after interruption. Result: **incomplete, no pass count**. This is not a passing test run.
- `node web/node_modules/vitest/vitest.mjs --version` returned `vitest/2.1.9 win32-x64 node-v24.11.1`.
- `npm.cmd test --prefix web -- --reporter=dot` completed with exit code 0: `Test Files 22 passed (22); Tests 148 passed (148); Duration 49.10s` (Vitest 2.1.9, Node v24.11.1).
- An exploratory `node web/node_modules/vitest/vitest.mjs run` launched with the repository root as its working directory and failed with 26 tests; errors included `document is not defined` and paths resolved relative to the wrong root. It is not the project test result; the supported `web`-scoped command above passed.
- Screenshot attempt: `msedge.exe --headless --disable-gpu --no-first-run --user-data-dir=$env:TEMP/sl2-edge-profile2 --window-size=1536,1022 --screenshot=<absolute docs/ui_reference_v2/prototype.png> <file URI>` did not create the file. Browser-use later rejected the `file:` URL with its policy (only `http:`/`https:` permitted); the blocked URL was not retried or worked around. Screenshot is therefore unavailable; no image is claimed.

The attached prototype references Google Fonts and `https://cdn.tailwindcss.com`; no successful CDN browser load was observed. CDN reachability is **unverified**, and offline availability is not established. These dependencies are flagged for removal in the target implementation.
