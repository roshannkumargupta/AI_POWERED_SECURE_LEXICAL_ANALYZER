"""Pre-bundled code samples for demonstration, security testing, and IDE presets."""

from __future__ import annotations

from apsla.server.schemas import SampleItem

PYTHON_SAMPLES: list[SampleItem] = [
    SampleItem(
        id="python-vuln-cmd-injection",
        title="Command Injection via Web Parameter",
        category="vulnerable",
        language="python",
        filename="vulnerable_ping.py",
        code=(
            "from flask import Flask, request\n"
            "import os\n\n"
            "app = Flask(__name__)\n\n"
            "@app.route('/ping')\n"
            "def ping():\n"
            "    # Untrusted user parameter flows directly into system shell\n"
            "    target = request.args.get('ip')\n"
            "    os.system('ping -c 1 ' + target)\n"
            "    return 'Ping dispatched'\n"
        ),
        description=(
            "Vulnerable endpoint where an HTTP request parameter enters via request.args.get "
            "and reaches the os.system() sink via dynamic string concatenation."
        ),
    ),
    SampleItem(
        id="python-adv-trojan-source",
        title="Trojan Source Bidi Override Attack",
        category="adversarial",
        language="python",
        filename="trojan_auth.py",
        code=(
            "# Trojan Source Bidirectional Override Attack (CVE-2021-42574)\n"
            "access_level = 'user'\n\n"
            "# Visual display appears benign, but bidi control reverses execution logic\n"
            "if access_level != 'user\u202e \u2066# check admin\u2069 \u2066':\n"
            "    print('Administrative privileges granted!')\n"
            "else:\n"
            "    print('Standard access only.')\n"
        ),
        description=(
            "Adversarial sample exploiting Right-to-Left Override (U+202E) control characters "
            "to reverse visual token order while preserving malicious execution semantics."
        ),
    ),
    SampleItem(
        id="python-adv-cyrillic-homoglyph",
        title="Cyrillic Homoglyph Execution",
        category="adversarial",
        language="python",
        filename="homoglyph_exec.py",
        code=(
            "# Confusable homoglyph: Latin 'e' replaced with Cyrillic 'е' (U+0435)\n"
            "payload = input('Enter expression: ')\n"
            "\u0435xec(payload)\n"
        ),
        description=(
            "Adversarial obfuscation substituting Latin characters with visually identical "
            "Cyrillic counterparts to evade simple keyword-based detection filters."
        ),
    ),
    SampleItem(
        id="python-safe-subprocess",
        title="Safe Parameterized Subprocess Execution",
        category="safe",
        language="python",
        filename="safe_ping.py",
        code=(
            "import subprocess\n"
            "import shlex\n\n"
            "def safe_ping(target_ip: str) -> None:\n"
            "    # Verified remediation: array argument vector without shell=True\n"
            "    clean_ip = shlex.quote(target_ip)\n"
            "    cmd = ['ping', '-c', '1', clean_ip]\n"
            "    subprocess.run(cmd, check=True)\n"
        ),
        description=(
            "Remediated safe implementation using subprocess.run with argument vector "
            "and shlex sanitization, immune to shell command injection."
        ),
    ),
]


def get_samples(language: str | None = None) -> list[SampleItem]:
    """Retrieve pre-bundled interactive code samples.

    Args:
        language: Optional language filter (e.g. 'python').

    Returns:
        List of matching SampleItem objects.
    """
    if language is None or language.lower() in ("python", "py"):
        return list(PYTHON_SAMPLES)
    return []
