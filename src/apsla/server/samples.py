"""Pre-bundled code samples for demonstration, security testing, and IDE presets."""

from __future__ import annotations

import json
from pathlib import Path

from apsla.samples.loader import load_sample, load_samples
from apsla.server.schemas import SampleItem

_SENIOR_PATH = Path(__file__).resolve().parents[1] / "samples" / "senior_results.json"


def _senior_results() -> dict[str, dict[str, object]]:
    try:
        data = json.loads(_SENIOR_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


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


JAVA_SAMPLES: list[SampleItem] = [
    SampleItem(
        id="java-vuln-sqli-servlet",
        title="SQL Injection via Servlet Parameter",
        category="vulnerable",
        language="java",
        filename="sqli_servlet.java",
        code=(
            "import java.io.IOException;\n"
            "import java.sql.Connection;\n"
            "import java.sql.ResultSet;\n"
            "import java.sql.Statement;\n"
            "import javax.servlet.http.HttpServlet;\n"
            "import javax.servlet.http.HttpServletRequest;\n"
            "import javax.servlet.http.HttpServletResponse;\n\n"
            "public class UserServlet extends HttpServlet {\n"
            "    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws IOException {\n"
            '        String id = request.getParameter("id");\n'
            "        try {\n"
            "            Connection conn = Database.getConnection();\n"
            "            Statement stmt = conn.createStatement();\n"
            '            String query = "SELECT * FROM users WHERE id = \'" + id + "\'";\n'
            "            ResultSet rs = stmt.executeQuery(query);\n"
            "        } catch (Exception e) {\n"
            "            e.printStackTrace();\n"
            "        }\n"
            "    }\n"
            "}\n"
        ),
        description=(
            "Vulnerable servlet endpoint where user input flows from request.getParameter "
            "into a dynamic SQL query string via concatenation, executed by Statement.executeQuery."
        ),
    ),
    SampleItem(
        id="java-vuln-deserialization",
        title="Insecure ObjectInputStream Deserialization",
        category="vulnerable",
        language="java",
        filename="deser_handler.java",
        code=(
            "import java.io.InputStream;\n"
            "import java.io.ObjectInputStream;\n"
            "import javax.servlet.http.HttpServletRequest;\n\n"
            "public class SessionHandler {\n"
            "    public Object restoreSession(HttpServletRequest req) throws Exception {\n"
            "        InputStream in = req.getInputStream();\n"
            "        ObjectInputStream ois = new ObjectInputStream(in);\n"
            "        // Deserializing untrusted object stream triggers gadget chains\n"
            "        return ois.readObject();\n"
            "    }\n"
            "}\n"
        ),
        description=(
            "Insecure Java object deserialization reading arbitrary serialized classes from an HTTP request "
            "stream without an ObjectInputFilter whitelist."
        ),
    ),
    SampleItem(
        id="java-adv-trojan-source",
        title="Trojan Source Bidi Override in Java",
        category="adversarial",
        language="java",
        filename="trojan_auth.java",
        code=(
            "public class AccessControl {\n"
            "    public static boolean checkAccess(String role) {\n"
            "        boolean isAdmin = false;\n"
            "        /* \u202e } \u2066if (isAdmin)\u2069 \u2066 begin admin check */\n"
            '        if ("admin".equals(role)) {\n'
            "            isAdmin = true;\n"
            "        }\n"
            "        return isAdmin;\n"
            "    }\n"
            "}\n"
        ),
        description=(
            "Adversarial Java sample using Trojan Source bidirectional override characters inside a comment "
            "to visually manipulate the apparent control-flow structure (CVE-2021-42574)."
        ),
    ),
    SampleItem(
        id="java-safe-prepared-statement",
        title="Safe PreparedStatement Parameterization",
        category="safe",
        language="java",
        filename="safe_prepared_stmt.java",
        code=(
            "import java.sql.Connection;\n"
            "import java.sql.PreparedStatement;\n"
            "import java.sql.ResultSet;\n"
            "import javax.servlet.http.HttpServletRequest;\n\n"
            "public class SafeUserQuery {\n"
            "    public void queryUser(HttpServletRequest request, Connection conn) throws Exception {\n"
            '        String id = request.getParameter("id");\n'
            '        String sql = "SELECT * FROM users WHERE id = ?";\n'
            "        try (PreparedStatement pstmt = conn.prepareStatement(sql)) {\n"
            "            pstmt.setString(1, id);\n"
            "            try (ResultSet rs = pstmt.executeQuery()) {\n"
            "                // Safe parameterized execution\n"
            "            }\n"
            "        }\n"
            "    }\n"
            "}\n"
        ),
        description=(
            "Remediated Java query using java.sql.PreparedStatement with '?' parameter placeholder "
            "and typed parameter binding, immune to SQL injection."
        ),
    ),
]


JAVASCRIPT_SAMPLES: list[SampleItem] = [
    SampleItem(
        id="js-vuln-dom-xss",
        title="DOM Cross-Site Scripting via location.hash",
        category="vulnerable",
        language="javascript",
        filename="dom_xss.js",
        code=(
            "// Client-side DOM XSS via unvalidated location.hash\n"
            "const hash = location.hash.slice(1);\n"
            "const output = document.getElementById('output');\n"
            "output.innerHTML = 'Welcome ' + hash;\n"
        ),
        description=(
            "Unsanitized location.hash reaches innerHTML sink via string concatenation, "
            "allowing arbitrary script execution in the user's browser context."
        ),
    ),
    SampleItem(
        id="js-vuln-express-cmd-injection",
        title="Express Command Injection via Web Parameter",
        category="vulnerable",
        language="javascript",
        filename="express_cmd_injection.js",
        code=(
            "const express = require('express');\n"
            "const { exec } = require('child_process');\n"
            "const app = express();\n\n"
            "app.get('/ping', (req, res) => {\n"
            "    const host = req.query.host;\n"
            "    exec('ping -c 1 ' + host, (err, stdout) => {\n"
            "        res.send(stdout);\n"
            "    });\n"
            "});\n"
        ),
        description=(
            "Untrusted query parameter enters via req.query.host and flows into "
            "child_process.exec without argument escaping, permitting shell command injection."
        ),
    ),
    SampleItem(
        id="js-adv-trojan-source",
        title="Trojan Source Bidi Override in JavaScript",
        category="adversarial",
        language="javascript",
        filename="trojan_source.js",
        code=(
            "// Trojan Source Bidirectional Override Attack (CVE-2021-42574)\n"
            "const accessLevel = 'user';\n\n"
            "/* \u202e } \u2066if (accessLevel === 'admin')\u2066 \u202e */\n"
            "if (accessLevel === 'user') {\n"
            "    console.log('Standard user access');\n"
            "}\n"
        ),
        description=(
            "Adversarial sample exploiting Right-to-Left Override (U+202E) control characters "
            "to reverse visual display order while hiding critical conditional checks."
        ),
    ),
    SampleItem(
        id="js-safe-text-content",
        title="Safe DOM Rendering with textContent",
        category="safe",
        language="javascript",
        filename="safe_text_content.js",
        code=(
            "// Safe DOM text rendering via textContent\n"
            "const hash = location.hash.slice(1);\n"
            "const output = document.getElementById('output');\n"
            "output.textContent = 'Welcome ' + hash;\n"
        ),
        description=(
            "Remediated safe implementation using textContent, which treats input strictly "
            "as plain text without HTML parsing, immune to DOM XSS."
        ),
    ),
]


CPP_SAMPLES: list[SampleItem] = [
    SampleItem(
        id="cpp-vuln-strcpy-argv",
        title="Buffer Overflow via strcpy(argv[1])",
        category="vulnerable",
        language="cpp",
        filename="strcpy_argv.c",
        code=(
            "#include <stdio.h>\n"
            "#include <string.h>\n\n"
            "int main(int argc, char *argv[]) {\n"
            "    char dest[32];\n"
            "    char *src = argv[1];\n"
            "    strcpy(dest, src);\n"
            '    printf("Processed input: %s\\n", dest);\n'
            "    return 0;\n"
            "}\n"
        ),
        description=(
            "Untrusted command-line argument argv[1] flows directly into a fixed-size buffer "
            "using unbounded strcpy(), leading to stack buffer overflow (CWE-120)."
        ),
    ),
    SampleItem(
        id="cpp-vuln-format-string",
        title="Format String Vulnerability via printf(user_buf)",
        category="vulnerable",
        language="cpp",
        filename="format_string.c",
        code=(
            "#include <stdio.h>\n\n"
            "int main(int argc, char *argv[]) {\n"
            "    char user_buf[64];\n"
            "    fgets(user_buf, sizeof(user_buf), stdin);\n"
            "    // Non-literal format string allows arbitrary stack reads and %n memory overwrites\n"
            "    printf(user_buf);\n"
            "    return 0;\n"
            "}\n"
        ),
        description=(
            "User-controlled input passed directly as the format string argument to printf() (CWE-134)."
        ),
    ),
    SampleItem(
        id="cpp-vuln-cmd-injection",
        title="Command Injection via system() and getenv()",
        category="vulnerable",
        language="cpp",
        filename="command_injection.c",
        code=(
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n\n"
            "int main(int argc, char *argv[]) {\n"
            '    char *user_path = getenv("USER_PATH");\n'
            "    char cmd[128];\n"
            '    sprintf(cmd, "ls -la %s", user_path);\n'
            "    system(cmd);\n"
            "    return 0;\n"
            "}\n"
        ),
        description=(
            "Untrusted environment variable concatenated into shell command string and executed via system() (CWE-78)."
        ),
    ),
    SampleItem(
        id="cpp-adv-trojan-source",
        title="Trojan Source Bidi Override in C",
        category="adversarial",
        language="cpp",
        filename="trojan_source.c",
        code=(
            "#include <stdio.h>\n"
            "#include <stdbool.h>\n\n"
            "int main(int argc, char *argv[]) {\n"
            "    bool is_admin = false;\n"
            "    /* \u202e } \u2066if (is_admin)\u2066 \u202e */\n"
            "    if (is_admin) {\n"
            '        printf("Administrative access granted.\\n");\n'
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        description=(
            "Adversarial sample exploiting Right-to-Left Override (U+202E) control characters "
            "in C comment to disguise control flow."
        ),
    ),
    SampleItem(
        id="cpp-safe-snprintf",
        title="Safe Bounded Buffer Copy with snprintf",
        category="safe",
        language="cpp",
        filename="safe_snprintf.c",
        code=(
            "#include <stdio.h>\n\n"
            "int main(int argc, char *argv[]) {\n"
            "    char dest[32];\n"
            "    if (argc > 1) {\n"
            '        snprintf(dest, sizeof(dest), "%s", argv[1]);\n'
            '        printf("%s\\n", dest);\n'
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        description=(
            "Remediated safe implementation using snprintf with sizeof(dest) and an explicit format specifier, "
            "preventing buffer overflow."
        ),
    ),
]


def get_samples(language: str | None = None) -> list[SampleItem]:
    """Retrieve pre-bundled interactive code samples.

    Args:
        language: Optional language filter (e.g. 'python', 'java', 'javascript', 'cpp').

    Returns:
        List of matching SampleItem objects.
    """
    if language is None:
        legacy = (
            list(PYTHON_SAMPLES) + list(JAVA_SAMPLES) + list(JAVASCRIPT_SAMPLES) + list(CPP_SAMPLES)
        )
        language_key = None
    else:
        aliases = {"py": "python", "js": "javascript", "c": "cpp", "c++": "cpp"}
        language_key = aliases.get(language.lower(), language.lower())
        legacy = [sample for sample in get_legacy_samples() if sample.language == language_key]

    senior = _senior_results()
    items = list(legacy)
    legacy_ids = {sample.id for sample in items}
    for meta, code in load_samples():
        if (language_key is None or meta.language == language_key) and meta.id not in legacy_ids:
            items.append(
                SampleItem(
                    id=meta.id,
                    title=meta.title,
                    category="adversarial" if meta.kind == "unicode" else meta.kind,
                    language=meta.language,
                    filename=meta.file.rsplit("/", 1)[-1],
                    code=code,
                    description=meta.summary,
                    group=meta.language,
                    kind=meta.kind,
                    level=meta.level,
                    topic=meta.topic,
                    summary=meta.summary,
                    notes=meta.notes,
                    expect=meta.expect.model_dump(),
                    fix_expected=meta.fix_expected,
                    approximate=meta.approximate,
                    special_chars=meta.special_chars,
                    demo_order=meta.demo_order,
                    senior=senior.get(meta.id),
                )
            )
    items = [_with_metadata_defaults(item) for item in items]
    language_rank = {"python": 0, "java": 1, "javascript": 2, "cpp": 3}
    kind_rank = {"basic": 0, "intermediate": 1, "advanced": 2, "safe": 3, "unicode": 4, "lexer": 5}
    items.sort(
        key=lambda item: (
            language_rank.get(item.language, 4),
            kind_rank.get(item.level or item.kind or item.category, 6),
            item.id,
        )
    )
    return items


def get_legacy_samples() -> list[SampleItem]:
    """Return the original sample records for backward-compatible UI presets."""
    return list(PYTHON_SAMPLES) + list(JAVA_SAMPLES) + list(JAVASCRIPT_SAMPLES) + list(CPP_SAMPLES)


def _with_metadata_defaults(sample: SampleItem) -> SampleItem:
    """Add stable metadata fields to a legacy sample without changing its open behavior."""
    kind = {"adversarial": "unicode"}.get(sample.category, sample.category)
    return sample.model_copy(
        update={
            "group": sample.language,
            "kind": kind,
            "level": "basic" if kind == "vulnerable" else None,
            "topic": sample.title,
            "summary": sample.description,
            "notes": [],
            "expect": {},
            "fix_expected": "none",
            "approximate": False,
            "special_chars": [],
            "demo_order": None,
        }
    )


def get_sample(sample_id: str) -> SampleItem | None:
    """Get a sample by ID, including retained pre-catalogue sample IDs."""
    found = load_sample(sample_id)
    if found:
        meta, code = found
        return SampleItem(
            id=meta.id,
            title=meta.title,
            category="adversarial" if meta.kind == "unicode" else meta.kind,
            language=meta.language,
            filename=meta.file.rsplit("/", 1)[-1],
            code=code,
            description=meta.summary,
            group=meta.language,
            kind=meta.kind,
            level=meta.level,
            topic=meta.topic,
            summary=meta.summary,
            notes=meta.notes,
            expect=meta.expect.model_dump(),
            fix_expected=meta.fix_expected,
            approximate=meta.approximate,
            special_chars=meta.special_chars,
            demo_order=meta.demo_order,
            senior=_senior_results().get(meta.id),
        )
    return next(
        (
            _with_metadata_defaults(sample)
            for sample in get_legacy_samples()
            if sample.id == sample_id
        ),
        None,
    )
