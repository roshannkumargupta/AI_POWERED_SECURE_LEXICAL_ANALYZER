"""Build the deterministic Python demonstration sample catalogue."""

from __future__ import annotations

import argparse
import base64
import json
import zlib
from pathlib import Path
from typing import Any

from apsla.samples.schema import SampleMeta

ROOT = Path(__file__).resolve().parents[1] / "src" / "apsla" / "samples"
ORDER = {
    "py-i01": 1,
    "py-s02": 2,
    "py-u04": 3,
    "py-u01": 4,
    "py-b06": 5,
    "py-a06": 6,
    "jv-i01": 7,
    "jv-i06": 8,
    "js-b04": 9,
    "js-a01": 10,
    "cp-i01": 11,
    "cp-a06": 12,
    "py-a04": 13,
}
INTERMEDIATE_CONTEXT = """
def describe_response(status: int, label: str) -> str:
    return f'{label}: {status}'

def record_event(events: list[str], message: str) -> list[str]:
    return [*events, message]
"""
ADVANCED_CONTEXT = """
from dataclasses import dataclass

@dataclass
class Diagnostic:
    name: str
    status: str

def normalize_label(value: str | None) -> str:
    return (value or 'unknown').strip().lower()

def select_diagnostics(items: list[Diagnostic], active: bool) -> list[Diagnostic]:
    if active:
        return [item for item in items if item.status != 'archived']
    return items[:3]

def render_diagnostic(item: Diagnostic) -> dict[str, str]:
    return {'name': normalize_label(item.name), 'status': item.status}

def build_summary(items: list[Diagnostic]) -> str:
    names = [normalize_label(item.name) for item in items]
    return ', '.join(names)

def load_examples() -> list[Diagnostic]:
    return [Diagnostic('alpha', 'ready'), Diagnostic('beta', 'queued')]

def main() -> None:
    examples = select_diagnostics(load_examples(), active=True)
    print(build_summary(examples))

if __name__ == '__main__':
    main()
"""


def _row(
    sid: str,
    level: str | None,
    kind: str,
    topic: str,
    title: str,
    code: str,
    rules: list[tuple[str, int]] | None = None,
    *,
    fix: str = "none",
    notes: list[str] | None = None,
    approximate: bool = False,
    chars: list[str] | None = None,
    min_findings: int | None = None,
    taint: bool = False,
    clean: bool = False,
) -> tuple[dict[str, Any], str]:
    """Create one metadata row and source body with consistent expectations."""
    filename = f"{sid}_{title.lower().replace(' ', '_')[:28]}.py"
    section = "python"
    summary = f"Demonstrates {topic.lower()} in a small, inert Python example."
    rules = rules or []
    expected = {
        "findings": [{"rule_id": rule, "line": line} for rule, line in rules],
        "min_findings": len(rules) if min_findings is None else min_findings,
    }
    if clean:
        expected["clean_below"] = "medium"
    if taint:
        expected["taint"] = True
    if notes is None:
        rule_names = ", ".join(rule for rule, _ in rules) or "no medium-or-higher security rule"
        if kind == "vulnerable":
            attacker_inputs = {
                "Command Injection": "`127.0.0.1; echo demo` as the submitted host or task.",
                "SQL Injection": "`' OR '1'='1` as the search value.",
                "Path Traversal": "`../../notes.txt` as the requested file name.",
                "Deserialization": "a crafted serialized object or YAML tag in the input stream.",
                "Template Injection": "`{{ 8 * 8 }}` as the supplied display name.",
                "Dynamic Import": "`os` as the requested module name.",
                "Weak Cryptography": "repeated guesses against a predictable session value.",
                "Hard-Coded Secret": "a source checkout exposed to someone outside the service team.",
                "TLS Validation": "a proxy presenting an untrusted certificate for the requested host.",
                "Obfuscation": "the shown encoded bytes decode only to a harmless print call.",
                "Multiple Security Issues": "crafted request values at the example.invalid service routes.",
                "File Processing": "`../../notes.txt` as the upload name, plus crafted local input.",
            }
            fix_text = {
                "safe": "The proposed safe fix replaces the risky operation with a safer API.",
                "review": "Review the generated patch and preserve the route's intended behavior.",
                "manual": "The current engine requires a manual redesign for this operation.",
                "none": "No automatic fix is expected; constrain the input and API explicitly.",
            }[fix]
            notes = [
                summary,
                f"An attacker could supply {attacker_inputs.get(topic, 'crafted input')}",
                f"SecureLex checks for {rule_names}"
                + (" and traces its data flow." if taint else "."),
                fix_text,
            ]
        elif kind == "unicode":
            notes = [
                summary,
                f"Recorded source contains {', '.join(chars or [])}, which can disguise characters or identifiers.",
                f"The expected Unicode checks include {rule_names}.",
                "Inspect the code points and restore ordinary, readable source text.",
            ]
        else:
            notes = [
                summary,
                "The source uses ordinary Python structures in a security-relevant look-alike.",
                "SecureLex should report no medium-or-higher finding for this example.",
            ]
    row: dict[str, Any] = {
        "id": sid,
        "language": "python",
        "file": f"{section}/{filename}",
        "title": title[:50],
        "kind": kind,
        "level": level,
        "topic": topic,
        "summary": summary,
        "notes": notes,
        "expect": expected,
        "fix_expected": fix,
        "approximate": approximate,
        "special_chars": chars or [],
        "demo_order": ORDER.get(sid),
    }
    SampleMeta.model_validate(row)
    return row, code.rstrip() + "\n"


def catalogue() -> list[tuple[dict[str, Any], str]]:
    """Return the 41 ordered samples; encoded and Unicode source is built explicitly."""
    data: list[tuple[dict[str, Any], str]] = []

    def add(*args: Any, **kwargs: Any) -> None:
        values = list(args)
        if len(values) > 5 and values[1] == "advanced":
            values[5] = values[5].rstrip() + ADVANCED_CONTEXT
        elif len(values) > 5 and values[1] == "intermediate":
            values[5] = values[5].rstrip() + INTERMEDIATE_CONTEXT
        data.append(_row(*values, **kwargs))

    add(
        "py-b01",
        "basic",
        "vulnerable",
        "Code Execution",
        "Evaluate Console Expression",
        "expression = input('Expression: ')\nresult = eval(expression)\nprint(result)",
        [("APS-PY-INJ-001", 2)],
        fix="review",
    )
    add(
        "py-b02",
        "basic",
        "vulnerable",
        "Code Execution",
        "Execute Supplied Script",
        "code = input('Code: ')\nexec(code)\nprint('Completed')",
        [("APS-PY-INJ-001", 2)],
        fix="review",
    )
    add(
        "py-b03",
        "basic",
        "vulnerable",
        "Command Injection",
        "Ping a Supplied Host",
        "import os\nhost = input('Host: ')\nos.system('ping -c 1 ' + host)",
        [("APS-PY-INJ-002", 3)],
        fix="review",
    )
    add(
        "py-b04",
        "basic",
        "vulnerable",
        "SQL Injection",
        "Look Up a User",
        "import sqlite3\nname = input('Name: ')\nconn = sqlite3.connect(':memory:')\nconn.execute(\"SELECT * FROM users WHERE name='\" + name + \"'\")",
        [("APS-PY-INJ-004", 4)],
        fix="review",
    )
    add(
        "py-b05",
        "basic",
        "vulnerable",
        "Deserialization",
        "Restore a Socket Message",
        "import pickle\nimport socket\nsock = socket.socket()\ndata = sock.recv(4096)\nrecord = pickle.loads(data)",
        [("APS-PY-DES-001", 5)],
        fix="manual",
    )
    add(
        "py-b06",
        "basic",
        "vulnerable",
        "Deserialization",
        "Read a YAML Configuration",
        "import yaml\nwith open('config.yml', encoding='utf-8') as config:\n    settings = yaml.load(config)\nprint(settings)",
        [("APS-PY-DES-002", 3)],
        fix="safe",
    )
    add(
        "py-b07",
        "basic",
        "vulnerable",
        "Weak Cryptography",
        "Create a Password Digest",
        "import hashlib\npassword = input('Password: ')\ndigest = hashlib.md5(password.encode()).hexdigest()\nprint(digest)",
        [("APS-PY-CRY-001", 3)],
        fix="safe",
    )
    add(
        "py-b08",
        "basic",
        "vulnerable",
        "Hard-Coded Secret",
        "Configure Service Credentials",
        "API_KEY = 'AKIAIOSFODNN7EXAMPLE'\nDB_PASSWORD = 'example-only-password'\nprint('Service configured')",
        [("APS-PY-SEC-001", 1), ("APS-PY-SEC-001", 2)],
        fix="review",
        min_findings=2,
    )
    add(
        "py-b09",
        "basic",
        "vulnerable",
        "TLS Validation",
        "Fetch a Status Page",
        "import requests\nurl = 'https://example.invalid/status'\nresponse = requests.get(url, verify=False, timeout=2)\nprint(response.status_code)",
        [("APS-PY-NET-001", 3)],
        fix="safe",
    )
    add(
        "py-b10",
        "basic",
        "vulnerable",
        "Weak Cryptography",
        "Generate a Session Code",
        "import random\nsession_token = random.randint(100000, 999999)\nprint(session_token)",
        [("APS-PY-CRY-002", 2)],
        fix="safe",
    )
    add(
        "py-i01",
        "intermediate",
        "vulnerable",
        "Command Injection",
        "Flask Host Diagnostics",
        "from flask import Flask, request\nimport os\napp = Flask(__name__)\n\n@app.get('/ping')\ndef ping():\n    target = request.args.get('q')\n    command = 'echo ' + target\n    os.system('echo ' + target)\n    return 'queued'",
        [("APS-PY-INJ-002", 9)],
        fix="review",
        taint=True,
    )
    add(
        "py-i02",
        "intermediate",
        "vulnerable",
        "SQL Injection",
        "Flask Account Search",
        "from flask import Flask, request\nimport sqlite3\napp = Flask(__name__)\n\n@app.get('/search')\ndef search():\n    name = request.args.get('name', '')\n    query = f\"SELECT * FROM accounts WHERE name = '{name}'\"\n    db = sqlite3.connect(':memory:')\n    return str(db.execute(query).fetchall())",
        [("APS-PY-INJ-004", 10)],
        fix="review",
    )
    add(
        "py-i03",
        "intermediate",
        "vulnerable",
        "Command Injection",
        "Run a Host Check",
        "import subprocess\nhost = input('Host: ')\nargs = f'ping -c 1 {host}'\ncompleted = subprocess.run(args, shell=True, capture_output=True, text=True)\nprint(completed.stdout)",
        [("APS-PY-INJ-003", 4)],
        fix="review",
    )
    add(
        "py-i04",
        "intermediate",
        "vulnerable",
        "Path Traversal",
        "Open an Uploaded Report",
        "from flask import Flask, request\napp = Flask(__name__)\n\n@app.get('/download')\ndef download():\n    filename = request.args.get('file')\n    path = 'uploads/' + filename\n    with open(path, encoding='utf-8') as report:\n        return report.read()",
        [("APS-PY-IO-001", 8)],
        fix="review",
        taint=True,
        approximate=True,
    )
    add(
        "py-i05",
        "intermediate",
        "vulnerable",
        "Template Injection",
        "Render a Greeting",
        "from flask import Flask, request, render_template_string\napp = Flask(__name__)\n\n@app.get('/hello')\ndef hello():\n    name = request.args.get('name', 'guest')\n    template = name\n    return render_template_string(template)",
        [("APS-PY-XSS-001", 8)],
        fix="review",
    )
    add(
        "py-i06",
        "intermediate",
        "vulnerable",
        "Command Injection",
        "Django Maintenance View",
        "import subprocess\ndef maintenance(request):\n    command = request.GET.get('cmd', 'echo ready')\n    selected = str(command)\n    result = subprocess.call(selected, shell=True)\n    return str(result)",
        [("APS-PY-INJ-003", 5)],
        fix="review",
    )
    add(
        "py-i07",
        "intermediate",
        "vulnerable",
        "Dynamic Import",
        "Load a Requested Plugin",
        "import importlib\nfrom flask import Flask, request\napp = Flask(__name__)\n\n@app.get('/plugin')\ndef plugin():\n    module_name = request.args.get('module', '')\n    loaded = importlib.import_module(module_name)\n    return loaded.__name__",
        [("APS-PY-INJ-005", 8)],
        fix="none",
    )
    add(
        "py-i08",
        "intermediate",
        "vulnerable",
        "Deserialization",
        "Restore a Submitted Session",
        "import pickle\nfrom flask import Flask, request\napp = Flask(__name__)\n\n@app.post('/session')\ndef restore():\n    body = request.data\n    session = pickle.loads(body)\n    return str(type(session).__name__)",
        [("APS-PY-DES-001", 8)],
        fix="manual",
    )
    add(
        "py-i09",
        "intermediate",
        "vulnerable",
        "Weak Cryptography",
        "Issue a Session Identifier",
        "import hashlib\nimport random\n\ndef create_session():\n    session_token = random.random()\n    return hashlib.sha1(str(session_token).encode()).hexdigest()\n\nprint(create_session())",
        [("APS-PY-CRY-001", 7), ("APS-PY-CRY-002", 5)],
        fix="safe",
        min_findings=2,
    )
    add(
        "py-a01",
        "advanced",
        "vulnerable",
        "Command Injection",
        "Dispatch a Diagnostic Job",
        "from flask import Flask, request\nimport os\napp = Flask(__name__)\n\ndef run_job(command):\n    prefix = 'echo ' + command\n    os.system(prefix)\n\n@app.get('/job')\ndef job():\n    value = request.args.get('task', '')\n    run_job(value)\n    return 'accepted'",
        [("APS-PY-INJ-002", 7)],
        fix="review",
        taint=True,
    )
    add(
        "py-a02",
        "advanced",
        "vulnerable",
        "Command Injection",
        "Select a Diagnostic Target",
        "import os\nfrom flask import Flask, request\napp = Flask(__name__)\n\n@app.get('/diagnose')\ndef diagnose():\n    if request.args.get('remote'):\n        target = request.args.get('host', '')\n    else:\n        target = '127.0.0.1'\n    command = 'echo ' + target\n    os.system(command)\n    return 'done'",
        [("APS-PY-INJ-002", 12)],
        fix="review",
        taint=True,
    )
    add(
        "py-a03",
        "advanced",
        "vulnerable",
        "Command Injection",
        "Build a Multi-Stage Task",
        "import os\nfrom flask import request\n\ndef dispatch():\n    value = request.args.get('task', '')\n    first = f'{value}'\n    second = '%s' % first\n    third = '{}'.format(second)\n    fourth = 'run ' + third\n    words = [fourth, 'safe']\n    command = ' '.join(words)\n    os.system('echo ' + command)",
        [("APS-PY-INJ-002", 12)],
        fix="review",
        taint=True,
        approximate=True,
    )
    payload = base64.b64encode(b"print('sample only')").decode("ascii")
    add(
        "py-a04",
        "advanced",
        "vulnerable",
        "Obfuscation",
        "Decode a Harmless Message",
        f"import base64\npayload = {payload!r}\nexec(base64.b64decode(payload))",
        [("APS-PY-OBF-001", 3)],
        fix="manual",
    )
    layered = base64.b64encode(zlib.compress(b"print('sample only')")).decode("ascii")
    add(
        "py-a05",
        "advanced",
        "vulnerable",
        "Obfuscation",
        "Unpack a Harmless Notice",
        f"import base64\nimport zlib\npayload = {layered!r}\nraw = base64.b64decode(payload)\nexec(zlib.decompress(raw))",
        [("APS-PY-OBF-001", 5)],
        fix="manual",
    )
    mini = """from flask import Flask, request
import hashlib
import os
import pickle
import requests
import sqlite3

app = Flask(__name__)
SECRET_KEY = 'not-a-placeholder-secret-value'
DATABASE = ':memory:'

def connection():
    return sqlite3.connect(DATABASE)

@app.get('/user')
def user_lookup():
    name = request.args.get('name', '')
    query = f\"SELECT * FROM users WHERE name='{name}'\"
    db = connection()
    return str(db.execute(query).fetchall())

@app.get('/echo')
def echo():
    text = request.args.get('text', '')
    os.system('echo ' + text)
    return 'sent'

@app.post('/restore')
def restore():
    record = pickle.loads(request.data)
    return str(type(record).__name__)

@app.get('/digest')
def digest():
    value = request.args.get('value', '')
    return hashlib.md5(value.encode()).hexdigest()

@app.get('/status')
def status():
    return str(requests.get('https://example.invalid/', verify=False, timeout=2).status_code)

@app.get('/health')
def health():
    return {'ready': True}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
"""
    add(
        "py-a06",
        "advanced",
        "vulnerable",
        "Multiple Security Issues",
        "Small Flask Service Review",
        mini,
        [
            ("APS-PY-SEC-001", 9),
            ("APS-PY-INJ-004", 20),
            ("APS-PY-INJ-002", 24),
            ("APS-PY-DES-001", 29),
            ("APS-PY-CRY-001", 35),
            ("APS-PY-NET-001", 39),
        ],
        fix="review",
        min_findings=6,
    )
    add(
        "py-a07",
        "advanced",
        "vulnerable",
        "File Processing",
        "Process a Submitted Archive Name",
        "import subprocess\nimport yaml\nfrom flask import request\n\ndef process_upload():\n    filename = request.args.get('file', '')\n    with open('uploads/' + filename, encoding='utf-8') as stream:\n        settings = yaml.load(stream)\n    command = f'echo {filename}'\n    subprocess.run(command, shell=True)\n    return str(settings)",
        [("APS-PY-IO-001", 8), ("APS-PY-DES-002", 9), ("APS-PY-INJ-003", 11)],
        fix="review",
        min_findings=3,
    )
    add(
        "py-a08",
        "advanced",
        "vulnerable",
        "Command Injection",
        "Quote the Wrong Value",
        "import os\nfrom flask import request\nimport shlex\n\ndef run_report():\n    trusted = shlex.quote('weekly')\n    supplied = request.args.get('report', '')\n    command = 'echo ' + supplied\n    os.system(command)\n    return trusted",
        [("APS-PY-INJ-002", 9)],
        fix="review",
    )
    add(
        "py-s01",
        None,
        "safe",
        "Process Execution",
        "Run a Fixed Argument List",
        "import subprocess\n\ndef list_directory(path: str) -> str:\n    result = subprocess.run(['ls', '-l', path], check=True, capture_output=True, text=True)\n    return result.stdout\n",
        clean=True,
    )
    add(
        "py-s02",
        None,
        "safe",
        "Command Injection",
        "Quote a Search Term",
        "import os\nimport shlex\n\ndef show_term(user: str) -> None:\n    quoted = shlex.quote(user)\n    os.system('echo ' + quoted)\n",
        clean=True,
        fix="none",
    )
    add(
        "py-s03",
        None,
        "safe",
        "SQL Injection",
        "Search with a Bound Parameter",
        "import sqlite3\n\ndef find_user(conn: sqlite3.Connection, uid: int):\n    return conn.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchall()\n",
        clean=True,
    )
    add(
        "py-s04",
        None,
        "safe",
        "Secure Defaults",
        "Load Trusted Configuration",
        "import hashlib\nimport secrets\nimport requests\nimport yaml\n\ndef load_settings(stream):\n    return yaml.safe_load(stream)\n\ndef digest(data: bytes) -> str:\n    return hashlib.sha256(data).hexdigest()\n\ndef token() -> str:\n    return secrets.token_hex(24)\n\ndef fetch() -> int:\n    return requests.get('https://example.invalid/', timeout=2).status_code\n",
        clean=True,
    )
    add(
        "py-s05",
        None,
        "safe",
        "Input Validation",
        "Convert a Port to an Integer",
        "import subprocess\n\ndef check_port(value: str):\n    port = int(value)\n    return subprocess.run(['echo', str(port)], check=True, capture_output=True)\n",
        clean=True,
    )
    add(
        "py-s06",
        None,
        "safe",
        "Lexer Context",
        "Security Terms in Documentation",
        'def inspect_model(model):\n    """Words eval, exec and os.system describe APIs, not calls."""\n    # eval(user_text), exec(code), os.system(command)\n    note = \'eval and exec are documentation terms\'\n    return model.eval()\n',
        clean=True,
    )
    add(
        "py-s07",
        None,
        "safe",
        "Application Structure",
        "Clean Service Module",
        "from dataclasses import dataclass\nfrom typing import Iterable\nimport logging\n\nlogger = logging.getLogger(__name__)\n\n@dataclass\nclass Job:\n    name: str\n\ndef describe(jobs: Iterable[Job]) -> list[str]:\n    with open('README.md', encoding='utf-8') as guide:\n        prefix = guide.readline().strip()\n    return [f'{prefix}: {job.name}' for job in jobs]\n\nasync def ready() -> bool:\n    return True\n",
        clean=True,
    )
    bidi = chr(0x202E) + chr(0x2066) + chr(0x2069)
    add(
        "py-u01",
        None,
        "unicode",
        "Unicode Bidi Controls",
        "Review a Bidi-Controlled Comment",
        f"# displayed text {bidi} comment\nrole = 'reader'\nprint(role)\n",
        [("APS-ALL-UNI-001", 1)],
        fix="safe",
        chars=["U+202E", "U+2066", "U+2069"],
    )
    zwsp = chr(0x200B)
    add(
        "py-u02",
        None,
        "unicode",
        "Invisible Identifier",
        "Find an Invisible Name Character",
        f"account{zwsp}name = 'guest'\nprint(account{zwsp}name)\n",
        [("APS-ALL-UNI-002", 1)],
        fix="safe",
        chars=["U+200B"],
    )
    tag = "".join(chr(cp) for cp in range(0xE0061, 0xE0066)) + chr(0xE007F)
    add(
        "py-u03",
        None,
        "unicode",
        "Unicode Tag Characters",
        "Inspect Hidden Tag Text",
        f"# note {tag}\nstatus = 'ready'\nprint(status)\n",
        [("APS-ALL-UNI-003", 1)],
        fix="safe",
        chars=[f"U+{cp:04X}" for cp in list(range(0xE0061, 0xE0066)) + [0xE007F]],
    )
    cyr_exec = "".join(chr(cp) for cp in [0x0435, 0x0445, 0x0435, 0x0441])
    add(
        "py-u04",
        None,
        "unicode",
        "Confusable API Name",
        "Inspect a Disguised Exec Call",
        f"payload = input('Value: ')\n{cyr_exec}(payload)\n",
        [("APS-ALL-UNI-006", 2), ("APS-PY-INJ-001", 2)],
        fix="review",
        chars=["U+0435", "U+0445", "U+0441"],
        min_findings=2,
    )
    full_eval = "".join(chr(cp) for cp in [0xFF45, 0xFF56, 0xFF41, 0xFF4C])
    add(
        "py-u05",
        None,
        "unicode",
        "Confusable API Name",
        "Inspect a Fullwidth Eval Call",
        f"expression = input('Value: ')\n{full_eval}(expression)\n",
        [("APS-ALL-UNI-006", 2)],
        fix="safe",
        chars=[f"U+{cp:04X}" for cp in [0xFF45, 0xFF56, 0xFF41, 0xFF4C]],
    )
    mixed = "us" + chr(0x0435) + "r_name"
    add(
        "py-u06",
        None,
        "unicode",
        "Mixed-Script Identifier",
        "Review a Mixed-Script Name",
        f"{mixed} = 'guest'\nprint({mixed})\n",
        [("APS-ALL-UNI-004", 1)],
        fix="safe",
        chars=["U+0435"],
    )
    lexer = '''@decorate\ndef parse_record(raw: bytes):
    text = rf"value={raw!r}; nested={ {'key': f\"{len(raw)}\"} }"
    triple = """a triple string with 'quotes'"""
    blob = rb"\\x41"
    count = 1_000 + 0x1F + 0b101 + 1e3 + 2j
    matrix = [[(x := item * 2) for item in range(3)] for _ in range(2)]
    mapper = lambda value: value @ count
    return text, triple, blob, matrix, mapper

async def read_all(items):
    return [await item for item in items]
'''
    add(
        "py-l01",
        None,
        "lexer",
        "Lexer Coverage",
        "Exercise Python Lexer Forms",
        lexer,
        [],
        clean=True,
    )
    cyr_exec = "".join(chr(cp) for cp in [0x0435, 0x0445, 0x0435, 0x0441])
    add(
        "py-ui5-security",
        "basic",
        "vulnerable",
        "UI-5 Security Demo",
        "Target Demo - Security",
        f"import os\nname = request.args.get('q')\nos.system('ls ' + name)\npw = 'admin123'\n{cyr_exec}('safe_argument')\n",
        [],
        min_findings=0,
        chars=["U+0435", "U+0445", "U+0441"],
    )
    add(
        "py-ui5-lexical",
        "basic",
        "vulnerable",
        "UI-5 Lexical Demo",
        "Target Demo - Lexical Error",
        "import os\nname = request.args.get('q')\nos.system('ls ' + name)\npw = 'admin123'\nmsg = \"hello with no closing quote.\n",
        [],
        min_findings=0,
    )
    from sample_catalogue_s2 import catalogue_s2
    from sample_catalogue_s3 import catalogue_s3

    return data + catalogue_s2() + catalogue_s3()


def build() -> int:
    """Write every sample source and the validated, sorted manifest."""
    ROOT.mkdir(parents=True, exist_ok=True)
    for directory in ("python", "java", "javascript", "cpp", "pending"):
        (ROOT / directory).mkdir(exist_ok=True)
        init = ROOT / directory / "__init__.py"
        if directory != "pending":
            init.write_text('"""Bundled sample sources."""\n', encoding="utf-8")
    entries = catalogue()
    for row, _ in entries:
        row["demo_order"] = ORDER.get(row["id"])
    existing_manifest = ROOT / "manifest.json"
    pending = {}
    if existing_manifest.exists():
        current = json.loads(existing_manifest.read_text(encoding="utf-8"))
        if not isinstance(current, list):
            raise ValueError("existing manifest must be a JSON array")
        pending = {row["id"]: row for row in current if row.get("pending_reason")}
    rows = []
    ids = [row["id"] for row, _ in entries]
    expected_count = 41 + 35 + 34 + 34 + 2
    if len(ids) != len(set(ids)) or len(ids) != expected_count:
        raise RuntimeError(f"expected {expected_count} unique catalogue entries, found {len(ids)}")
    for row, code in entries:
        code = code.replace("__BIDI_SAMPLE__", chr(0x202E) + chr(0x2066) + chr(0x2069)).replace(
            "__CYRILLIC_A__", chr(0x0430)
        )
        prior = pending.get(row["id"])
        if prior:
            row["file"] = prior["file"]
            row["pending_reason"] = prior["pending_reason"]
        rows.append(row)
        path = ROOT / row["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code.rstrip() + "\n", encoding="utf-8", newline="\n")
    (ROOT / "manifest.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(rows)


def main() -> None:
    """Parse command-line options and generate sources deterministically."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(f"Built {build()} samples in {ROOT}")


if __name__ == "__main__":
    main()
