"""Unit tests for Python data-flow taint analysis and PythonPlugin."""

import ast

from apsla.languages.python_lang import PythonPlugin
from apsla.languages.python_lang.taint import PythonTaintAnalyzer
from apsla.lexing.common import OffsetMap
from apsla.rules.base import RuleContext
from apsla.unicode_defense.recovery import recover_text


def _run_taint(code: str):
    tree = ast.parse(code)
    omap = OffsetMap(code)
    rec = recover_text(code)
    ctx = RuleContext(
        raw_source=code,
        recovered_source=code,
        tokens=[],
        ast_tree=tree,
        offset_map=omap,
        recovery=rec,
    )
    analyzer = PythonTaintAnalyzer(ctx)
    return analyzer.analyze()


def test_taint_sources():
    # input()
    flows = _run_taint("x = input()\nos.system(x)").flows
    assert len(flows) == 1
    assert flows[0].rule_id == "APS-PY-INJ-002"
    assert not flows[0].sanitized

    # sys.argv
    flows = _run_taint("import sys\ncmd = sys.argv[1]\nos.system(cmd)").flows
    assert len(flows) == 1
    assert flows[0].rule_id == "APS-PY-INJ-002"

    # os.environ
    flows = _run_taint("import os\nu = os.getenv('USER')\nos.system(u)").flows
    assert len(flows) == 1

    # sys.stdin.read
    flows = _run_taint("import sys\ndata = sys.stdin.read()\neval(data)").flows
    assert len(flows) == 1
    assert flows[0].rule_id == "APS-PY-INJ-001"

    # socket recv
    flows = _run_taint(
        "import socket\ns = socket.socket()\nbuf = s.recv(1024)\nos.system(buf)"
    ).flows
    assert len(flows) == 1

    # django request.GET
    flows = _run_taint("def view(request):\n    q = request.GET.get('q')\n    os.system(q)").flows
    assert len(flows) == 1

    # fastapi parameter
    flows = _run_taint(
        "@app.get('/items')\ndef endpoint(user_id: str):\n    os.system(user_id)"
    ).flows
    assert len(flows) == 1


def test_taint_propagation_features():
    # Augmented assignment
    code_aug = "cmd = 'ls '\ncmd += input()\nos.system(cmd)"
    flows = _run_taint(code_aug).flows
    assert len(flows) == 1
    assert len(flows[0].path) >= 3

    # Tuple unpacking
    code_unpack = "a, b = ('safe', input())\nos.system(b)"
    flows = _run_taint(code_unpack).flows
    assert len(flows) == 1

    # Reassignment clears taint
    code_clean = "x = input()\nx = 'echo safe'\nos.system(x)"
    flows = _run_taint(code_clean).flows
    assert len(flows) == 0

    # Branch union: taint flows if either branch is tainted
    code_branch = "if True:\n    x = input()\nelse:\n    x = 'clean'\nos.system(x)"
    flows = _run_taint(code_branch).flows
    assert len(flows) == 1


def test_taint_loop_fixed_point():
    # Loop propagating taint across iterations
    code_loop = "x = 'init'\nfor i in range(3):\n    x = x + input()\nos.system(x)"
    flows = _run_taint(code_loop).flows
    assert len(flows) == 1

    code_while = "x = 'init'\nwhile True:\n    x = x + input()\n    break\nos.system(x)"
    flows = _run_taint(code_while).flows
    assert len(flows) == 1


def test_taint_intra_file_function_summary():
    # Helper returns tainted input
    code = (
        "def sanitize_wrapper(val):\n"
        "    return val + ' extra'\n"
        "u = input()\n"
        "cmd = sanitize_wrapper(u)\n"
        "os.system(cmd)"
    )
    flows = _run_taint(code).flows
    assert len(flows) == 1


def test_taint_sanitizers():
    # shlex.quote
    code_shlex = "import shlex\nu = input()\nsafe_u = shlex.quote(u)\nos.system('echo ' + safe_u)"
    flows = _run_taint(code_shlex).flows
    assert len(flows) == 1
    assert flows[0].sanitized

    # int cast
    code_int = "u = input()\nsafe_id = int(u)\nos.system(f'echo {safe_id}')"
    flows = _run_taint(code_int).flows
    assert len(flows) == 1
    assert flows[0].sanitized

    # html.escape for XSS
    code_xss = (
        "import html\nu = input()\nsafe_html = html.escape(u)\nrender_template_string(safe_html)"
    )
    flows = _run_taint(code_xss).flows
    assert len(flows) == 1
    assert flows[0].sanitized

    # secure_filename for path traversal
    code_path = (
        "from werkzeug.utils import secure_filename\n"
        "f = input()\n"
        "clean_f = secure_filename(f)\n"
        "open(clean_f, 'r')"
    )
    flows = _run_taint(code_path).flows
    assert len(flows) == 1
    assert flows[0].sanitized

    # Parameterized SQL query
    code_sql = "u = input()\ncursor.execute('SELECT * FROM users WHERE id = %s', (u,))"
    flows = _run_taint(code_sql).flows
    # Parameterized query should be marked sanitized
    assert len(flows) == 1
    assert flows[0].sanitized


def test_python_plugin_interface():
    plugin = PythonPlugin()
    assert plugin.id == "python"
    assert ".py" in plugin.extensions

    tokens = plugin.lex("x = 42\n")
    assert len(tokens) > 0

    valid_ast, _ = plugin.syntax_check("x = 42\n")
    assert valid_ast is True

    invalid_ast, err = plugin.syntax_check("def (:\n")
    assert invalid_ast is False
    assert err is not None
    assert len(plugin.dangerous_apis()) > 0

    rules = plugin.rules()
    assert len(rules) >= 14

    code = "x = input()\nos.system(x)"
    omap = OffsetMap(code)
    res = plugin.analyze_taint(code, omap)
    assert len(res) == 1
