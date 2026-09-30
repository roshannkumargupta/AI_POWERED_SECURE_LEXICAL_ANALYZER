"""Generate comprehensive test fixtures for Phase 2 Python security analysis."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "python"
VULN_DIR = FIXTURES_DIR / "vulnerable"
SAFE_DIR = FIXTURES_DIR / "safe"
ADV_DIR = FIXTURES_DIR / "adversarial"

VULNERABLE_FIXTURES: dict[str, tuple[str, list[dict[str, str | int]]]] = {
    # Senior Probe 1: Flask request taint to os.system sink
    "cmd_injection_flask.py": (
        'name = request.args.get("q")\nos.system("echo " + name)\n',
        [{"rule_id": "APS-PY-INJ-002", "line": 2}],
    ),
    # Senior Probe 2: Sequential input() taint propagation to os.system
    "cmd_injection_input_seq.py": (
        "u = input()\nv = u\nos.system(v)\n",
        [{"rule_id": "APS-PY-INJ-002", "line": 3}],
    ),
    "cmd_injection_os_popen.py": (
        'cmd = "cat " + input()\nos.popen(cmd)\n',
        [{"rule_id": "APS-PY-INJ-002", "line": 2}],
    ),
    "cmd_injection_fstring.py": (
        'target = input()\nos.system(f"ping {target}")\n',
        [{"rule_id": "APS-PY-INJ-002", "line": 2}],
    ),
    "eval_dynamic_input.py": (
        "expr = input()\neval(expr)\n",
        [{"rule_id": "APS-PY-INJ-001", "line": 2}],
    ),
    "exec_dynamic_script.py": (
        "code = input()\nexec(code)\n",
        [{"rule_id": "APS-PY-INJ-001", "line": 2}],
    ),
    "subprocess_shell_true.py": (
        "cmd = input()\nsubprocess.run(cmd, shell=True)\n",
        [{"rule_id": "APS-PY-INJ-003", "line": 2}],
    ),
    "subprocess_popen_shell.py": (
        'cmd = "ls " + input()\nsubprocess.Popen(cmd, shell=True)\n',
        [{"rule_id": "APS-PY-INJ-003", "line": 2}],
    ),
    "sql_injection_concat.py": (
        'query = "SELECT * FROM users WHERE id = \'" + user_id + "\'"\ncursor.execute(query)\n',
        [{"rule_id": "APS-PY-INJ-004", "line": 2}],
    ),
    "sql_injection_fstring.py": (
        "user = input()\ncursor.execute(f\"SELECT * FROM accounts WHERE name = '{user}'\")\n",
        [{"rule_id": "APS-PY-INJ-004", "line": 2}],
    ),
    "sql_injection_percent.py": (
        'category = input()\ncursor.execute("SELECT * FROM items WHERE cat = %s" % category)\n',
        [{"rule_id": "APS-PY-INJ-004", "line": 2}],
    ),
    "pickle_loads_untrusted.py": (
        "payload = input()\npickle.loads(payload)\n",
        [{"rule_id": "APS-PY-DES-001", "line": 2}],
    ),
    "marshal_loads_untrusted.py": (
        "data = input()\nmarshal.loads(data)\n",
        [{"rule_id": "APS-PY-DES-001", "line": 2}],
    ),
    "shelve_open_untrusted.py": (
        "name = input()\nshelve.open(name)\n",
        [{"rule_id": "APS-PY-DES-001", "line": 2}],
    ),
    "yaml_load_unsafe.py": (
        "stream = input()\nyaml.load(stream)\n",
        [{"rule_id": "APS-PY-DES-002", "line": 2}],
    ),
    "yaml_unsafe_load_call.py": (
        "data = input()\nyaml.unsafe_load(data)\n",
        [{"rule_id": "APS-PY-DES-002", "line": 2}],
    ),
    "crypto_md5_hash.py": (
        'pwd = "secret"\nhashlib.md5(pwd.encode())\n',
        [{"rule_id": "APS-PY-CRY-001", "line": 2}],
    ),
    "crypto_sha1_hash.py": (
        'data = b"confidential"\nhashlib.sha1(data)\n',
        [{"rule_id": "APS-PY-CRY-001", "line": 2}],
    ),
    "weak_random_token.py": (
        "auth_token = random.randint(1000, 9999)\n",
        [{"rule_id": "APS-PY-CRY-002", "line": 1}],
    ),
    "weak_random_secret.py": (
        "session_secret = random.random()\n",
        [{"rule_id": "APS-PY-CRY-002", "line": 1}],
    ),
    "hardcoded_api_key.py": (
        'api_key = "ak_live_8f3a9e1b2c4d5e6f7a8b9c0d1e2f3a4b"\n',
        [{"rule_id": "APS-PY-SEC-001", "line": 1}],
    ),
    "hardcoded_password.py": (
        'admin_password = "P@ssw0rd98765!XYZ"\n',
        [{"rule_id": "APS-PY-SEC-001", "line": 1}],
    ),
    "requests_verify_false.py": (
        'requests.get("https://insecure.internal", verify=False)\n',
        [{"rule_id": "APS-PY-NET-001", "line": 1}],
    ),
    "requests_post_verify_false.py": (
        'requests.post("https://api.internal/login", verify=False)\n',
        [{"rule_id": "APS-PY-NET-001", "line": 1}],
    ),
    "path_traversal_open.py": (
        'user_file = input()\nopen(user_file, "r")\n',
        [{"rule_id": "APS-PY-IO-001", "line": 2}],
    ),
    "path_traversal_send_file.py": (
        'doc = request.args.get("doc")\nsend_file(doc)\n',
        [{"rule_id": "APS-PY-IO-001", "line": 2}],
    ),
    "dynamic_import_call.py": (
        "mod_name = input()\n__import__(mod_name)\n",
        [{"rule_id": "APS-PY-INJ-005", "line": 2}],
    ),
    "dynamic_importlib_module.py": (
        "mod = input()\nimportlib.import_module(mod)\n",
        [{"rule_id": "APS-PY-INJ-005", "line": 2}],
    ),
    "obfuscated_exec_b64.py": (
        "exec(base64.b64decode(payload))\n",
        [{"rule_id": "APS-PY-OBF-001", "line": 1}, {"rule_id": "APS-PY-INJ-001", "line": 1}],
    ),
    "template_injection_render.py": (
        'user = input()\nrender_template_string("Hello " + user)\n',
        [{"rule_id": "APS-PY-XSS-001", "line": 2}],
    ),
    "xss_raw_markup.py": (
        'user_content = input()\nMarkup("<p>" + user_content + "</p>")\n',
        [{"rule_id": "APS-PY-XSS-001", "line": 2}],
    ),
}

SAFE_FIXTURES: dict[str, tuple[str, list[dict[str, str | int]]]] = {
    # Senior Probe 3: Sanitized input via shlex.quote()
    "cmd_sanitized_shlex.py": (
        'import shlex\nimport os\nu = "test"\nc = shlex.quote(u)\nos.system("echo " + c)\n',
        [],
    ),
    # Senior Probe 4: Safe list-form subprocess execution
    "subprocess_list_safe.py": (
        'import subprocess\nsubprocess.run(["ls", "-l"])\n',
        [],
    ),
    # Senior Bug fix: Wrong-variable bug is gone
    "cmd_wrong_variable_safe.py": (
        'import os\nuser_input = "malicious; rm -rf /"\nsafe_cmd = "echo static_hello"\nos.system(safe_cmd)\n',
        [],
    ),
    "cmd_constant_os_system.py": (
        'import os\nos.system("ls -la")\n',
        [],
    ),
    "eval_literal_eval_safe.py": (
        'import ast\nuser_data = "{}"\nast.literal_eval(user_data)\n',
        [],
    ),
    "eval_constant_math_safe.py": (
        'eval("1 + 1")\n',
        [],
    ),
    "subprocess_shell_false.py": (
        'import subprocess\nsubprocess.run(["echo", "hello"], shell=False)\n',
        [],
    ),
    "sql_parameterized_query.py": (
        'user_id = 42\ncursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))\n',
        [],
    ),
    "sql_parameterized_executemany.py": (
        'records = [(1,), (2,)]\ncursor.executemany("INSERT INTO t VALUES (%s)", records)\n',
        [],
    ),
    "pickle_safe_json_loads.py": (
        'import json\nuser_payload = "{}"\njson.loads(user_payload)\n',
        [],
    ),
    "yaml_safe_load.py": (
        'import yaml\nstream = "a: 1"\nyaml.safe_load(stream)\n',
        [],
    ),
    "yaml_load_with_safeloader.py": (
        'import yaml\nstream = "a: 1"\nyaml.load(stream, Loader=yaml.SafeLoader)\n',
        [],
    ),
    "crypto_sha256_safe.py": (
        'import hashlib\ndata = b"clean"\nhashlib.sha256(data)\n',
        [],
    ),
    "crypto_sha512_safe.py": (
        'import hashlib\ndata = b"clean"\nhashlib.sha512(data)\n',
        [],
    ),
    "crypto_md5_usedforsecurity_false.py": (
        'import hashlib\ndata = b"checksum"\nhashlib.md5(data, usedforsecurity=False)\n',
        [],
    ),
    "random_secrets_token_safe.py": (
        "import secrets\nauth_token = secrets.token_hex(32)\n",
        [],
    ),
    "random_non_sensitive_var.py": (
        "import random\ndie_roll = random.randint(1, 6)\n",
        [],
    ),
    "secret_env_variable_safe.py": (
        'import os\napi_key = os.environ.get("API_KEY")\n',
        [],
    ),
    "secret_placeholder_safe.py": (
        'password = "changeme"\n',
        [],
    ),
    "requests_verify_true_safe.py": (
        'import requests\nrequests.get("https://example.com", verify=True)\n',
        [],
    ),
    "requests_default_verify_safe.py": (
        'import requests\nrequests.get("https://example.com")\n',
        [],
    ),
    "path_static_open_safe.py": (
        'open("config.json", "r")\n',
        [],
    ),
    "path_basename_sanitized_safe.py": (
        'import os\nuser_path = "uploads/report.pdf"\nopen(os.path.basename(user_path), "r")\n',
        [],
    ),
    "path_secure_filename_safe.py": (
        'user_path = "uploads/report.pdf"\nopen(secure_filename(user_path), "r")\n',
        [],
    ),
    "importlib_constant_module_safe.py": (
        'import importlib\nimportlib.import_module("json")\n',
        [],
    ),
    "static_import_statement_safe.py": (
        "import math\nx = math.sqrt(16)\n",
        [],
    ),
    "template_render_static_safe.py": (
        'render_template("home.html", name="Alice")\n',
        [],
    ),
    "xss_markup_escape_safe.py": (
        'from markupsafe import Markup\nuser_comment = "Hello"\nMarkup.escape(user_comment)\n',
        [],
    ),
}

ADVERSARIAL_FIXTURES: dict[str, tuple[str, list[dict[str, str | int]]]] = {
    # Senior Probe 5: Trojan Source Bidi Override (U+202E)
    "trojan_source_bidi.py": (
        's = "ADM\u202e\u202dMIN"\n',
        [{"rule_id": "APS-ALL-UNI-001", "line": 1}],
    ),
    # Senior Probe 6: Cyrillic homoglyph look-alike 'exec'
    "cyrillic_homoglyph_exec.py": (
        '\u0435\u0445\u0435\u0441("echo 1")\n',
        [
            {"rule_id": "APS-ALL-UNI-004", "line": 1},
            {"rule_id": "APS-ALL-UNI-006", "line": 1},
            {"rule_id": "APS-PY-INJ-001", "line": 1},
        ],
    ),
    "zero_width_space_ident.py": (
        "adm\u200bin = 1\n",
        [{"rule_id": "APS-ALL-UNI-002", "line": 1}],
    ),
    "bidi_comment_spoof.py": (
        "# \u202e return; \u202d access_granted = True\n",
        [{"rule_id": "APS-ALL-UNI-001", "line": 1}],
    ),
    "mixed_script_func.py": (
        "def p\u0430yload(): pass\n",
        [
            {"rule_id": "APS-ALL-UNI-004", "line": 1},
            {"rule_id": "APS-ALL-UNI-005", "line": 1},
        ],
    ),
    "confusable_eval_homoglyph.py": (
        "\u0435val(payload)\n",
        [
            {"rule_id": "APS-ALL-UNI-004", "line": 1},
            {"rule_id": "APS-ALL-UNI-005", "line": 1},
            {"rule_id": "APS-ALL-UNI-006", "line": 1},
            {"rule_id": "APS-PY-INJ-001", "line": 1},
        ],
    ),
    "invisible_tag_chars.py": (
        f'x = "{chr(0xE0001)}{chr(0xE0020)}hidden"\n',
        [{"rule_id": "APS-ALL-UNI-003", "line": 1}],
    ),
    "soft_hyphen_split.py": (
        "ex\u00adecutable = True\n",
        [{"rule_id": "APS-ALL-UNI-002", "line": 1}],
    ),
    "bidi_string_literal.py": (
        'role = "user\u202eguest\u202d"\n',
        [{"rule_id": "APS-ALL-UNI-001", "line": 1}],
    ),
    "confusable_import_homoglyph.py": (
        "__\u0456mport__(mod_name)\n",
        [
            {"rule_id": "APS-ALL-UNI-004", "line": 1},
            {"rule_id": "APS-ALL-UNI-005", "line": 1},
            {"rule_id": "APS-ALL-UNI-006", "line": 1},
            {"rule_id": "APS-PY-INJ-005", "line": 1},
        ],
    ),
    "zero_width_joiner_ident.py": (
        'tok\u200den = "val"\n',
        [{"rule_id": "APS-ALL-UNI-002", "line": 1}],
    ),
}


def write_fixtures(
    target_dir: Path,
    fixtures: dict[str, tuple[str, list[dict[str, str | int]]]],
) -> dict[str, list[dict[str, str | int]]]:
    """Write source files and return expectations mapping."""
    target_dir.mkdir(parents=True, exist_ok=True)
    expect_map: dict[str, list[dict[str, str | int]]] = {}

    for fname, (code, expected) in fixtures.items():
        src_path = target_dir / fname
        src_path.write_text(code, encoding="utf-8")

        expect_path = target_dir / f"{src_path.stem}.expect.json"
        expect_path.write_text(json.dumps(expected, indent=2), encoding="utf-8")

        expect_map[fname] = expected

    # Also write a combined expect.json in target_dir
    combined_expect = target_dir / "expect.json"
    combined_expect.write_text(json.dumps(expect_map, indent=2), encoding="utf-8")
    return expect_map


def main() -> None:
    """Generate all fixture files and expectation JSON records."""
    vuln_expect = write_fixtures(VULN_DIR, VULNERABLE_FIXTURES)
    safe_expect = write_fixtures(SAFE_DIR, SAFE_FIXTURES)
    adv_expect = write_fixtures(ADV_DIR, ADVERSARIAL_FIXTURES)

    # Master expect.json in tests/fixtures/python/
    master_expect = {
        "vulnerable": vuln_expect,
        "safe": safe_expect,
        "adversarial": adv_expect,
    }
    (FIXTURES_DIR / "expect.json").write_text(json.dumps(master_expect, indent=2), encoding="utf-8")

    print(
        f"Generated {len(vuln_expect)} vulnerable, {len(safe_expect)} safe, "
        f"and {len(adv_expect)} adversarial fixtures in {FIXTURES_DIR}"
    )


if __name__ == "__main__":
    main()
