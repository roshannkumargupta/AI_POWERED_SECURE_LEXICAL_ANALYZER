"""Populates data/external/python with 42 realistic, hand-written benchmark snippets."""

from __future__ import annotations

import json
from pathlib import Path

EXTERNAL_DIR = Path(__file__).resolve().parent.parent / "data" / "external" / "python"
EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

SNIPPETS = [
    # 1. Path traversal open
    (
        "ext_01_user_report_open.py",
        """import os
def get_report(user_filename: str) -> str:
    path = "/var/reports/" + user_filename
    with open(path, "r") as f:
        return f.read()
""",
        "MALICIOUS",
        "open(path, ...) on concatenated user input",
    ),
    # 2. Safe path resolve
    (
        "ext_02_safe_path_resolve.py",
        """import os
def get_safe_report(user_filename: str) -> str:
    safe_name = os.path.basename(user_filename)
    path = os.path.join("/var/reports", safe_name)
    with open(path, "r") as f:
        return f.read()
""",
        "SAFE",
        "path sanitized with os.path.basename",
    ),
    # 3. MD5 payment hash
    (
        "ext_03_payment_gateway_hash.py",
        """import hashlib
def verify_payment_signature(tx_id: str, secret: str) -> str:
    raw = f"{tx_id}:{secret}"
    return hashlib.md5(raw.encode()).hexdigest()
""",
        "MALICIOUS",
        "MD5 weak crypto for payment signature",
    ),
    # 4. Secrets token generator
    (
        "ext_04_token_generator_secrets.py",
        """import secrets
def create_session_token() -> str:
    return secrets.token_urlsafe(32)
""",
        "SAFE",
        "cryptographically strong token generation",
    ),
    # 5. OS system command injection
    (
        "ext_05_backup_db_system.py",
        """import os
def backup_table(table_name: str) -> None:
    cmd = f"pg_dump -t {table_name} my_database > backup.sql"
    os.system(cmd)
""",
        "MALICIOUS",
        "os.system with dynamic table_name",
    ),
    # 6. Safe subprocess list
    (
        "ext_06_docker_exec_subprocess.py",
        """import subprocess
def inspect_container(container_id: str) -> str:
    res = subprocess.run(["docker", "inspect", container_id], capture_output=True, text=True, check=True)
    return res.stdout
""",
        "SAFE",
        "subprocess.run with argument list and shell=False",
    ),
    # 7. Eval calculator
    (
        "ext_07_eval_math_calculator.py",
        """def calculate_metric(user_formula: str) -> float:
    return float(eval(user_formula))
""",
        "MALICIOUS",
        "eval on dynamic input string",
    ),
    # 8. Literal eval config
    (
        "ext_08_literal_eval_config.py",
        """import ast
def parse_literal_config(raw_text: str) -> dict:
    return ast.literal_eval(raw_text)
""",
        "SAFE",
        "ast.literal_eval for safe literal data",
    ),
    # 9. SQL search injection
    (
        "ext_09_sql_search_users.py",
        """def find_users_by_role(cursor, role: str) -> list:
    query = "SELECT id, name FROM users WHERE role = '" + role + "'"
    cursor.execute(query)
    return cursor.fetchall()
""",
        "MALICIOUS",
        "SQL concatenated query execution",
    ),
    # 10. Parameterized SQL
    (
        "ext_10_sql_parameterized_query.py",
        """def find_users_by_role_safe(cursor, role: str) -> list:
    cursor.execute("SELECT id, name FROM users WHERE role = ?", (role,))
    return cursor.fetchall()
""",
        "SAFE",
        "parameterized SQL query execution",
    ),
    # 11. Pickle deserialization
    (
        "ext_11_session_deserialize_pickle.py",
        """import pickle
def load_session_cookie(raw_cookie_bytes: bytes) -> dict:
    return pickle.loads(raw_cookie_bytes)
""",
        "MALICIOUS",
        "pickle.loads on untrusted cookie",
    ),
    # 12. JSON deserialization
    (
        "ext_12_json_api_response.py",
        """import json
def parse_api_payload(body: str) -> dict:
    return json.loads(body)
""",
        "SAFE",
        "safe json.loads",
    ),
    # 13. SSL verify false
    (
        "ext_13_webhook_ssl_verify_false.py",
        """import requests
def dispatch_webhook(url: str, data: dict) -> int:
    resp = requests.post(url, json=data, verify=False)
    return resp.status_code
""",
        "MALICIOUS",
        "requests verify=False disables TLS certificate validation",
    ),
    # 14. SSL verify true
    (
        "ext_14_api_client_verify_true.py",
        """import requests
def fetch_status(endpoint: str) -> dict:
    resp = requests.get(endpoint, timeout=10, verify=True)
    return resp.json()
""",
        "SAFE",
        "requests with verify=True",
    ),
    # 15. Hardcoded AWS key
    (
        "ext_15_hardcoded_aws_key.py",
        """AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE12"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
def init_aws():
    return {"key": AWS_ACCESS_KEY_ID}
""",
        "MALICIOUS",
        "hardcoded AWS credential constants",
    ),
    # 16. Env secret retrieval
    (
        "ext_16_env_secret_retrieval.py",
        """import os
def get_database_password() -> str:
    return os.environ.get("DB_PASSWORD", "")
""",
        "SAFE",
        "secrets loaded from environment variables",
    ),
    # 17. XSS Markup
    (
        "ext_17_xss_render_template.py",
        """import markupsafe
def build_welcome_banner(user_name: str) -> markupsafe.Markup:
    return markupsafe.Markup("<h1>Welcome, " + user_name + "</h1>")
""",
        "MALICIOUS",
        "Markup wrapper around unescaped user string",
    ),
    # 18. Escaped HTML output
    (
        "ext_18_escaped_html_output.py",
        """import markupsafe
def build_safe_welcome(user_name: str) -> str:
    escaped = markupsafe.escape(user_name)
    return f"<h1>Welcome, {escaped}</h1>"
""",
        "SAFE",
        "markupsafe.escape protects against XSS",
    ),
    # 19. Trojan Source bidi
    (
        "ext_19_bidi_spoofed_check.py",
        """def check_admin(user_role: str) -> bool:
    role = "user\u202e\u202dadmin"
    return user_role == role
""",
        "MALICIOUS",
        "Trojan Source bidirectional control characters",
    ),
    # 20. Cyrillic homoglyph exec
    (
        "ext_20_cyrillic_homoglyph_exec.py",
        """def run_task(cmd: str):
    \u0435\u0445\u0435\u0441(cmd)
""",
        "MALICIOUS",
        "confusable Cyrillic homoglyph concealing exec",
    ),
    # 21. Zero width auth
    (
        "ext_21_zero_width_auth.py",
        """auth_\u200btoken = "secret99"
def verify(t):
    return t == auth_\u200btoken
""",
        "MALICIOUS",
        "invisible zero-width space in identifier",
    ),
    # 22. Subprocess shell true
    (
        "ext_22_subprocess_shell_true.py",
        """import subprocess
def list_user_files(subfolder: str):
    subprocess.Popen("ls " + subfolder, shell=True)
""",
        "MALICIOUS",
        "subprocess shell=True command injection",
    ),
    # 23. Obfuscated payload
    (
        "ext_23_base64_hidden_payload.py",
        """import base64
def run_bootstrap():
    encoded = "cHJpbnQoJ2hlbGxvIHdvcmxkJyk="
    exec(base64.b64decode(encoded))
""",
        "MALICIOUS",
        "base64 decoded payload passed to exec",
    ),
    # 24. YAML unsafe load
    (
        "ext_24_yaml_load_unsafe.py",
        """import yaml
def read_pipeline(spec: str):
    return yaml.load(spec, Loader=yaml.Loader)
""",
        "MALICIOUS",
        "unsafe yaml.load deserialization",
    ),
    # 25. YAML safe load
    (
        "ext_25_yaml_safe_load.py",
        """import yaml
def read_pipeline_safe(spec: str):
    return yaml.safe_load(spec)
""",
        "SAFE",
        "safe yaml.safe_load",
    ),
    # 26. Random password reset
    (
        "ext_26_random_password_reset.py",
        """import random
def generate_pin() -> str:
    return str(random.randint(100000, 999999))
""",
        "SUSPICIOUS",
        "pseudo-random generator for authentication pin",
    ),
    # 27. Secrets password reset
    (
        "ext_27_secrets_password_reset.py",
        """import secrets
def generate_safe_pin() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))
""",
        "SAFE",
        "cryptographically strong pin generation",
    ),
    # 28. Dynamic import plugin
    (
        "ext_28_dynamic_import_plugin.py",
        """def load_extension(extension_name: str):
    return __import__(extension_name)
""",
        "MALICIOUS",
        "dynamic __import__ on user string",
    ),
    # 29. Static import map
    (
        "ext_29_static_import_map.py",
        """from handlers import auth_handler, data_handler
HANDLERS = {"auth": auth_handler, "data": data_handler}
def get_handler(name: str):
    return HANDLERS.get(name)
""",
        "SAFE",
        "static dictionary dispatch",
    ),
    # 30. Tarfile extract traversal
    (
        "ext_30_tar_extract_traversal.py",
        """import tarfile
def unpack_archive(archive_path: str, dest_dir: str):
    with tarfile.open(archive_path) as tar:
        tar.extractall(dest_dir)
""",
        "SUSPICIOUS",
        "tarfile extractall without path traversal check",
    ),
    # 31. Safe tar extract
    (
        "ext_31_safe_tar_extract.py",
        """import tarfile, os
def unpack_safe(archive_path: str, dest_dir: str):
    with tarfile.open(archive_path) as tar:
        for member in tar.getmembers():
            if not os.path.abspath(os.path.join(dest_dir, member.name)).startswith(dest_dir):
                raise ValueError("Path traversal attempt")
        tar.extractall(dest_dir)
""",
        "SAFE",
        "validated tar member extraction",
    ),
    # 32. Weak JWT secret
    (
        "ext_32_jwt_weak_secret.py",
        """def sign_jwt(claims: dict) -> str:
    secret = "secret"
    return f"{claims}.{secret}"
""",
        "MALICIOUS",
        "hardcoded trivial secret",
    ),
    # 33. Env JWT secret
    (
        "ext_33_jwt_env_secret.py",
        """import os
def sign_jwt_safe(claims: dict) -> str:
    secret = os.environ.get("JWT_SECRET")
    return f"{claims}.{secret}"
""",
        "SAFE",
        "secret loaded from env",
    ),
    # 34. Flask login SQL
    (
        "ext_34_flask_login_sql.py",
        """def authenticate(cursor, email: str, pw_hash: str):
    sql = f"SELECT * FROM members WHERE email='{email}' AND pw='{pw_hash}'"
    cursor.execute(sql)
    return cursor.fetchone()
""",
        "MALICIOUS",
        "f-string SQL query execution",
    ),
    # 35. SQLite param query
    (
        "ext_35_sqlite_param_query.py",
        """def authenticate_safe(cursor, email: str, pw_hash: str):
    sql = "SELECT * FROM members WHERE email=? AND pw=?"
    cursor.execute(sql, (email, pw_hash))
    return cursor.fetchone()
""",
        "SAFE",
        "parameterized SQLite query",
    ),
    # 36. OS popen grep
    (
        "ext_36_os_popen_grep.py",
        """import os
def search_system_logs(pattern: str) -> str:
    pipe = os.popen("grep " + pattern + " /var/log/syslog")
    return pipe.read()
""",
        "MALICIOUS",
        "os.popen with concatenated command",
    ),
    # 37. Subprocess check output
    (
        "ext_37_subprocess_check_output.py",
        """import subprocess
def search_system_logs_safe(pattern: str) -> str:
    out = subprocess.check_output(["grep", pattern, "/var/log/syslog"], text=True)
    return out
""",
        "SAFE",
        "subprocess.check_output with argument list",
    ),
    # 38. Jinja raw template
    (
        "ext_38_jinja_raw_template.py",
        """from jinja2 import Template
def render_profile(template_str: str, ctx: dict) -> str:
    return Template(template_str).render(**ctx)
""",
        "MALICIOUS",
        "dynamic Template construction allows SSTI",
    ),
    # 39. Jinja sandboxed env
    (
        "ext_39_jinja_sandboxed_env.py",
        """from jinja2.sandbox import SandboxedEnvironment
def render_safe_profile(template_str: str, ctx: dict) -> str:
    env = SandboxedEnvironment()
    return env.from_string(template_str).render(**ctx)
""",
        "SAFE",
        "SandboxedEnvironment mitigates SSTI",
    ),
    # 40. Crypto SHA1 sign
    (
        "ext_40_crypto_sha1_sign.py",
        """import hashlib
def sign_firmware(binary_data: bytes) -> str:
    return hashlib.sha1(binary_data).hexdigest()
""",
        "MALICIOUS",
        "SHA-1 deprecated broken digest for signature",
    ),
    # 41. Crypto SHA256 sign
    (
        "ext_41_crypto_sha256_sign.py",
        """import hashlib
def sign_firmware_safe(binary_data: bytes) -> str:
    return hashlib.sha256(binary_data).hexdigest()
""",
        "SAFE",
        "SHA-256 secure hash for signature",
    ),
    # 42. Flask echo service
    (
        "ext_42_flask_echo_service.py",
        """import os
def handle_echo(msg: str):
    os.system("echo " + msg)
""",
        "MALICIOUS",
        "os.system command injection",
    ),
]


def create_dataset():
    index = {}
    for filename, code, label, note in SNIPPETS:
        file_path = EXTERNAL_DIR / filename
        file_path.write_text(code, encoding="utf-8")
        index[filename] = {
            "label": label,
            "note": note,
            "length": len(code),
        }
    with open(EXTERNAL_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"Created {len(SNIPPETS)} external benchmark snippets in {EXTERNAL_DIR}")


if __name__ == "__main__":
    create_dataset()
