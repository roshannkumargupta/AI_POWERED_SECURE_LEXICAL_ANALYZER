"""Deterministic generator of labelled Python synthetic snippets from varied templates."""

from __future__ import annotations

import random
from typing import Final

from apsla.languages.python_lang.lexer import PythonLexer
from apsla.ml.synth.common import (
    LABEL_MALICIOUS,
    LABEL_SAFE,
    LABEL_SUSPICIOUS,
    SyntheticSnippet,
)

# ── Vocabulary Pools for Variation ────────────────────────────────────────────

VARS: Final[list[str]] = [
    "user_input",
    "cmd",
    "query",
    "payload",
    "req_data",
    "filename",
    "buffer",
    "item_id",
    "token",
    "raw_arg",
    "user_id",
    "host_ip",
    "cat_name",
    "secret_val",
    "param",
    "endpoint",
    "cache_key",
    "session_id",
]

SAFE_VARS: Final[list[str]] = [
    "count",
    "total",
    "idx",
    "item",
    "result",
    "records",
    "metrics",
    "config",
    "logger",
    "status",
    "response",
    "options",
    "retries",
]

COMMENTS: Final[list[str]] = [
    "# Execute user requested action",
    "# Handle incoming API request payload",
    "# Process query parameters from client",
    "# Ensure data consistency across services",
    "# Audit log entry for security monitoring",
    "# Cache lookup for optimized performance",
    "# Parse incoming webhook request",
    "# Validate input parameters",
]

DISTRACTORS_PRE: Final[list[str]] = [
    "import os\nimport sys\nimport logging\nlogger = logging.getLogger(__name__)\n",
    "from typing import Any, Optional\nimport json\nimport time\n",
    "import os\nimport hashlib\nimport subprocess\n",
    "import sqlite3\nimport base64\n",
    "import secrets\nimport yaml\n",
    "import requests\nimport markupsafe\n",
]

DISTRACTORS_SAFE_BODY: Final[list[str]] = [
    "def calculate_checksum(data: str) -> str:\n    return hashlib.sha256(data.encode()).hexdigest()\n",
    "def sanitize_identifier(raw: str) -> str:\n    return ''.join(c for c in raw if c.isalnum())\n",
    "def format_response(status_code: int, msg: str) -> dict:\n    return {'status': status_code, 'message': msg}\n",
    "def safe_increment(val: int) -> int:\n    return val + 1 if val > 0 else 0\n",
]


# ── Template Builders ─────────────────────────────────────────────────────────


def _generate_snippet(
    snippet_id: str,
    family: str,
    pre: str,
    core_lines: list[tuple[str, int]],  # (code_line, label_int)
    post: str,
) -> SyntheticSnippet:
    """Combines segments, tokenizes, and labels tokens based on template spans."""
    full_code = pre + "\n" + "\n".join(line for line, _ in core_lines) + "\n" + post
    tokens = PythonLexer(full_code).tokenize()

    # Determine start/end character offsets of each core line
    offset_map: list[tuple[int, int, int]] = []  # (start_char, end_char, label)
    curr_char = len(pre) + 1  # accounts for '\n'
    for line, label in core_lines:
        line_len = len(line)
        offset_map.append((curr_char, curr_char + line_len, label))
        curr_char += line_len + 1  # line + '\n'

    # Compute character offset of each token in full_code
    token_labels: list[int] = []
    char_cursor = 0
    for tok in tokens:
        tok_start = char_cursor
        tok_end = tok_start + len(tok.text)
        char_cursor = tok_end

        # Check if token overlaps any labeled line
        tok_label = LABEL_SAFE
        for start_c, end_c, lbl in offset_map:
            # Overlap check
            if max(tok_start, start_c) < min(tok_end, end_c) and tok.kind not in (
                "WHITESPACE",
                "NEWLINE",
                "COMMENT",
            ):
                tok_label = max(tok_label, lbl)
        token_labels.append(tok_label)

    return SyntheticSnippet(
        snippet_id=snippet_id,
        template_family=family,
        language="python",
        code=full_code,
        tokens=tokens,
        token_labels=token_labels,
    )


# ── Family Generators ─────────────────────────────────────────────────────────


def _build_cmd_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 3)

    if variant == 0:
        lines = [
            (c, LABEL_SAFE),
            (f"{v} = request.args.get('target', '')", LABEL_SUSPICIOUS),
            (f"os.system('ping -c 1 ' + {v})", LABEL_MALICIOUS),
        ]
    elif variant == 1:
        lines = [
            (c, LABEL_SAFE),
            (f"{v} = input('Enter command: ')", LABEL_SUSPICIOUS),
            (f"subprocess.run({v}, shell=True, check=True)", LABEL_MALICIOUS),
        ]
    elif variant == 2:
        lines = [
            (c, LABEL_SAFE),
            (f"{v} = os.getenv('USER_ACTION', '')", LABEL_SUSPICIOUS),
            (f"stream = os.popen(f'echo {{{v}}}')", LABEL_MALICIOUS),
        ]
    else:
        lines = [
            (c, LABEL_SAFE),
            (f"{v} = sys.argv[1]", LABEL_SUSPICIOUS),
            (f"subprocess.Popen('cat ' + {v}, shell=True)", LABEL_MALICIOUS),
        ]
    return _generate_snippet(sid, "cmd_injection", pre, lines, "")


def _build_sql_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            (c, LABEL_SAFE),
            (f"{v} = request.form['user_id']", LABEL_SUSPICIOUS),
            (f"sql = 'SELECT * FROM users WHERE id = \\'' + {v} + '\\''", LABEL_MALICIOUS),
            ("cursor.execute(sql)", LABEL_MALICIOUS),
        ]
    elif variant == 1:
        lines = [
            (c, LABEL_SAFE),
            (f"{v} = input('Filter: ')", LABEL_SUSPICIOUS),
            (
                f"cursor.execute(f'SELECT balance FROM accounts WHERE owner = {{{v}}}')",
                LABEL_MALICIOUS,
            ),
        ]
    else:
        lines = [
            (c, LABEL_SAFE),
            (f"{v} = request.json.get('name', '')", LABEL_SUSPICIOUS),
            (
                f"cursor.execute('UPDATE profile SET bio = %s WHERE id = %s' % ({v}, 1))",
                LABEL_MALICIOUS,
            ),
        ]
    return _generate_snippet(sid, "sql_injection", pre, lines, "")


def _build_code_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            (f"{v} = request.args.get('expr', '1+1')", LABEL_SUSPICIOUS),
            (f"res = eval({v})", LABEL_MALICIOUS),
        ]
    elif variant == 1:
        lines = [
            (f"{v} = input('Script: ')", LABEL_SUSPICIOUS),
            (f"exec({v})", LABEL_MALICIOUS),
        ]
    else:
        lines = [
            (f"{v} = request.headers.get('X-Handler', 'main')", LABEL_SUSPICIOUS),
            (f"mod = __import__({v})", LABEL_MALICIOUS),
        ]
    return _generate_snippet(sid, "code_injection", pre, lines, "")


def _build_unsafe_deserialization(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            (f"{v} = request.get_data()", LABEL_SUSPICIOUS),
            (f"obj = pickle.loads({v})", LABEL_MALICIOUS),
        ]
    elif variant == 1:
        lines = [
            (f"{v} = request.files['config'].read()", LABEL_SUSPICIOUS),
            (f"cfg = yaml.load({v}, Loader=yaml.Loader)", LABEL_MALICIOUS),
        ]
    else:
        lines = [
            (f"{v} = request.get_data()", LABEL_SUSPICIOUS),
            (f"res = marshal.loads({v})", LABEL_MALICIOUS),
        ]
    return _generate_snippet(sid, "unsafe_deserialization", pre, lines, "")


def _build_weak_crypto(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            (f"{v} = request.form.get('password', '')", LABEL_SUSPICIOUS),
            (f"hashed_pw = hashlib.md5({v}.encode()).hexdigest()", LABEL_MALICIOUS),
        ]
    elif variant == 1:
        lines = [
            (f"{v} = request.json.get('token', '')", LABEL_SUSPICIOUS),
            (f"sig = hashlib.sha1({v}.encode()).digest()", LABEL_MALICIOUS),
        ]
    else:
        lines = [
            ("import random", LABEL_SAFE),
            ("alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'", LABEL_SAFE),
            ("api_token = ''.join(random.choice(alphabet) for _ in range(32))", LABEL_MALICIOUS),
        ]
    return _generate_snippet(sid, "weak_crypto", pre, lines, "")


def _build_hardcoded_secrets(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 2)

    if variant == 0:
        secret = "sk-live-" + "".join(rng.choices("0123456789abcdef", k=32))
        lines = [
            (f'API_KEY = "{secret}"', LABEL_MALICIOUS),
            ("client = SomeServiceClient(api_key=API_KEY)", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ('DB_PASSWORD = "SuperSecretPassword123!"', LABEL_MALICIOUS),
            ("db = connect(user='admin', password=DB_PASSWORD)", LABEL_SAFE),
        ]
    else:
        lines = [
            ('JWT_SECRET_KEY = "shhhhh_this_is_a_very_secret_signing_token_99"', LABEL_MALICIOUS),
            ("token = encode_jwt({'user': 'admin'}, JWT_SECRET_KEY)", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "hardcoded_secrets", pre, lines, "")


def _build_path_traversal(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 1)

    if variant == 0:
        lines = [
            (f"{v} = request.args.get('path', 'default.txt')", LABEL_SUSPICIOUS),
            (f"with open({v}, 'r') as f:", LABEL_MALICIOUS),
            ("    content = f.read()", LABEL_SAFE),
        ]
    else:
        lines = [
            (f"{v} = request.args.get('doc', 'readme.pdf')", LABEL_SUSPICIOUS),
            (f"return send_file({v})", LABEL_MALICIOUS),
        ]
    return _generate_snippet(sid, "path_traversal", pre, lines, "")


def _build_obfuscated_payload(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 1)

    if variant == 0:
        encoded = "ZWNobyAnaGFja2VkJw=="
        lines = [
            (f'payload = "{encoded}"', LABEL_SUSPICIOUS),
            ("decoded = base64.b64decode(payload)", LABEL_SUSPICIOUS),
            ("exec(decoded)", LABEL_MALICIOUS),
        ]
    else:
        hex_data = "6578656328227072696e742831292229"
        lines = [
            (f'hex_bytes = bytes.fromhex("{hex_data}")', LABEL_SUSPICIOUS),
            ("eval(hex_bytes.decode('utf-8'))", LABEL_MALICIOUS),
        ]
    return _generate_snippet(sid, "obfuscated_payload", pre, lines, "")


def _build_unicode_attacks(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 2)

    if variant == 0:
        # Trojan source bidi override
        lines = [
            ('access_level = "user\u202e\u202dadmin"', LABEL_MALICIOUS),
            ('if access_level == "admin":', LABEL_SAFE),
            ('    print("Authorized")', LABEL_SAFE),
        ]
    elif variant == 1:
        # Cyrillic homoglyph for exec
        lines = [
            ("# Execute command securely", LABEL_SAFE),
            ('\u0435\u0445\u0435\u0441("echo 1")', LABEL_MALICIOUS),
        ]
    else:
        # Zero width space in variable
        lines = [
            ('user_\u200btoken = "secret123"', LABEL_MALICIOUS),
            ("print(user_\u200btoken)", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "unicode_attacks", pre, lines, "")


def _build_suspicious_patterns(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            (f"{v} = 'https://api.internal.network/data'", LABEL_SAFE),
            (f"resp = requests.get({v}, verify=False)", LABEL_SUSPICIOUS),
        ]
    elif variant == 1:
        lines = [
            (f"{v} = request.args.get('html_content', '')", LABEL_SUSPICIOUS),
            (f"safe_html = Markup({v})", LABEL_SUSPICIOUS),
        ]
    else:
        lines = [
            (f"{v} = request.args.get('template', 'Hello {{ name }}')", LABEL_SUSPICIOUS),
            (f"return render_template_string({v}, name='Guest')", LABEL_SUSPICIOUS),
        ]
    return _generate_snippet(sid, "suspicious_patterns", pre, lines, "")


def _build_safe_patterns(rng: random.Random, sid: str) -> SyntheticSnippet:
    sv = rng.choice(SAFE_VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    body = rng.choice(DISTRACTORS_SAFE_BODY)
    variant = rng.randint(0, 4)

    if variant == 0:
        lines = [
            (f"{sv} = [x * 2 for x in range(10) if x % 2 == 0]", LABEL_SAFE),
            (f"logger.info('Computed items: %d', len({sv}))", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("user_id = int(request.args.get('id', 0))", LABEL_SAFE),
            ("cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))", LABEL_SAFE),
            ("records = cursor.fetchall()", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("target_file = os.path.basename(request.args.get('f', 'default.txt'))", LABEL_SAFE),
            ("with open(os.path.join('/safe/dir', target_file), 'r') as f:", LABEL_SAFE),
            ("    content = f.read()", LABEL_SAFE),
        ]
    elif variant == 3:
        lines = [
            ("token_val = secrets.token_hex(32)", LABEL_SAFE),
            ("cfg = yaml.safe_load('setting: true\\nretries: 3')", LABEL_SAFE),
        ]
    else:
        lines = [
            ("subprocess.run(['ls', '-la'], check=True)", LABEL_SAFE),
            ('parsed = json.loads(\'{"status": "ok", "code": 200}\')', LABEL_SAFE),
        ]
    return _generate_snippet(sid, "safe_patterns", pre + body, lines, "")


# ── Public Generator ──────────────────────────────────────────────────────────


def generate_python_dataset(
    count: int = 3000,
    seed: int = 42,
) -> list[SyntheticSnippet]:
    """Generates at least `count` deterministic, leak-free labeled Python snippets.

    Args:
        count: Minimum number of snippets to synthesize (default: 3000).
        seed: Random seed for reproducibility (default: 42).

    Returns:
        List of SyntheticSnippet instances with ground truth per-token labels.
    """
    rng = random.Random(seed)
    families = [
        ("cmd_injection", _build_cmd_injection, 0.10),
        ("sql_injection", _build_sql_injection, 0.10),
        ("code_injection", _build_code_injection, 0.08),
        ("unsafe_deserialization", _build_unsafe_deserialization, 0.08),
        ("weak_crypto", _build_weak_crypto, 0.08),
        ("hardcoded_secrets", _build_hardcoded_secrets, 0.08),
        ("path_traversal", _build_path_traversal, 0.08),
        ("obfuscated_payload", _build_obfuscated_payload, 0.05),
        ("unicode_attacks", _build_unicode_attacks, 0.05),
        ("suspicious_patterns", _build_suspicious_patterns, 0.10),
        ("safe_patterns", _build_safe_patterns, 0.20),
    ]

    builders = [f[1] for f in families]
    weights = [f[2] for f in families]

    snippets: list[SyntheticSnippet] = []
    for i in range(count):
        sid = f"synth-py-{i:05d}"
        chosen_builder = rng.choices(builders, weights=weights, k=1)[0]
        snippet = chosen_builder(rng, sid)
        snippets.append(snippet)

    return snippets
