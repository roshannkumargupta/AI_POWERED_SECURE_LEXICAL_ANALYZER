"""Java and JavaScript demonstration catalogue data catalogue data."""

from __future__ import annotations

from typing import Any

from apsla.samples.schema import SampleMeta

JAVA = {
    "INJ-001": 'String host = "example.invalid";\nRuntime.getRuntime().exec("ping " + host);',
    "INJ-002": 'String name = request.getParameter("name");\nStatement stmt = connection.createStatement();\nstmt.executeQuery("SELECT * FROM users WHERE name=\'" + name + "\'");',
    "CRY-001": 'MessageDigest digest = MessageDigest.getInstance("MD5");',
    "CRY-002": 'Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");',
    "CRY-003": "int token = new java.util.Random().nextInt();",
    "SEC-001": 'String password = "demo-credential-value-2026";\nDriverManager.getConnection("jdbc:example:mem", "demo", password);',
    "DES-001": 'ObjectInputStream input = new ObjectInputStream(new FileInputStream("sample.bin"));\nObject value = input.readObject();',
    "XSS-001": 'response.getWriter().println(request.getParameter("q"));',
    "IO-001": 'String name = request.getParameter("file");\nnew FileInputStream(baseDir + name);',
    "NET-001": 'String target = request.getParameter("url");\nnew URL(target).openStream();',
    "XML-001": "DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();\nfactory.newDocumentBuilder().parse(request.getInputStream());",
    "INJ-003": 'String className = request.getParameter("class");\nClass.forName(className).getDeclaredConstructor().newInstance();',
    "INJ-004": 'String expression = request.getParameter("expr");\nnew ScriptEngineManager().getEngineByName("javascript").eval(expression);',
    "NET-002": "TrustManager[] managers = { new X509TrustManager() { public void checkClientTrusted(X509Certificate[] c, String a) {} public void checkServerTrusted(X509Certificate[] c, String a) {} public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; } } };\nHostnameVerifier verifier = (host, session) -> true;",
}

JS = {
    "INJ-001": "const userInput = process.argv[2];\neval(userInput);",
    "INJ-002": 'const host = req.query.host;\nexec("ping " + host);',
    "INJ-003": "const id = req.query.id;\ndb.query(`SELECT * FROM users WHERE id=${id}`);",
    "INJ-004": "const body = JSON.parse(req.body);\nObject.assign(config, body);",
    "INJ-005": "const pattern = req.query.pattern;\nconst matcher = new RegExp(pattern);",
    "XSS-001": "element.innerHTML = location.hash;",
    "XSS-002": "return <div dangerouslySetInnerHTML={{ __html: value }} />;",
    "IO-001": "fs.readFile(req.query.file, callback);",
    "NET-001": 'window.location.href = new URLSearchParams(location.search).get("next");',
    "NET-002": "axios.get(req.query.url);",
    "NET-003": "const agent = new https.Agent({ rejectUnauthorized: false });",
    "CRY-001": "const token = Math.random().toString(36);",
    "CRY-002": 'const digest = crypto.createHash("md5").update(value).digest("hex");',
    "SEC-001": 'const api_key = "A7kQ9mP2xR5vT8wY3zB6";\nconst jwt_secret = "gH4jK7mN2pQ5sV8xY1cD";',
    "SEC-002": "const claims = jwt.decode(token);\nif (claims.admin) grantAccess();",
    "OBF-001": 'eval(atob("Y29uc29sZS5sb2coJ2RlbW8nKQ=="));',
}


JAVA_SPECS = [
    ("b01", "basic", "SQL by Concatenation", "SQL Injection", "INJ-002"),
    ("b02", "basic", "Runtime Command from Host", "Command Injection", "INJ-001"),
    ("b03", "basic", "MD5 Password Digest", "Weak Cryptography", "CRY-001"),
    ("b04", "basic", "SHA-1 Password Digest", "Weak Cryptography", "CRY-001"),
    ("b05", "basic", "DES Encryption", "Weak Cryptography", "CRY-002"),
    ("b06", "basic", "AES ECB Encryption", "Weak Cryptography", "CRY-002"),
    ("b07", "basic", "Predictable Random Token", "Weak Cryptography", "CRY-003"),
    ("b08", "basic", "Hard-Coded Database Password", "Hard-Coded Secret", "SEC-001"),
    ("b09", "basic", "Deserialize a Local File", "Deserialization", "DES-001"),
    ("i01", "intermediate", "Servlet SQL Injection", "SQL Injection", "INJ-002"),
    ("i02", "intermediate", "Servlet Command Injection", "Command Injection", "INJ-001"),
    ("i03", "intermediate", "Reflected Servlet Output", "Cross-Site Scripting", "XSS-001"),
    ("i04", "intermediate", "Read a Requested File", "Path Traversal", "IO-001"),
    ("i05", "intermediate", "Fetch a Requested URL", "Server-Side Request Forgery", "NET-001"),
    ("i06", "intermediate", "Parse Request XML", "XML External Entity", "XML-001"),
    ("i07", "intermediate", "Spring Native Query", "SQL Injection", "INJ-002"),
    ("i08", "intermediate", "Reflect a Requested Class", "Unsafe Reflection", "INJ-003"),
    ("i09", "intermediate", "Evaluate a Script Expression", "Dynamic Evaluation", "INJ-004"),
    ("i10", "intermediate", "Trust Every TLS Certificate", "TLS Validation", "NET-002"),
    ("a01", "advanced", "Deserialize a Network Stream", "Deserialization", "DES-001"),
    ("a02", "advanced", "Build SQL in a Helper", "SQL Injection", "INJ-002"),
    ("a03", "advanced", "Validation on One Branch", "SQL Injection", "INJ-002"),
    ("a04", "advanced", "Servlet Security Review", "Multiple Security Issues", "INJ-002"),
    ("a05", "advanced", "Decode an XML Object", "Deserialization", "DES-001"),
    ("a06", "advanced", "Trust-All HTTPS Client", "TLS Validation", "NET-002"),
]
JAVA_SAFE = [
    "Use a PreparedStatement",
    "Parse an Integer Before Query",
    "Use Safe Crypto and Process APIs",
    "Disable XML External Entities",
    "Normalize and Check a Path",
    "Clean Service Class",
]
JAVA_UNICODE = ["Bidi-Controlled Comment", "Escaped Bidi Character", "Mixed-Script Identifier"]

JS_SPECS = [
    ("b01", "basic", "Evaluate User Input", "Dynamic Evaluation", "INJ-001"),
    ("b02", "basic", "Construct a Function", "Dynamic Evaluation", "INJ-001"),
    ("b03", "basic", "Schedule a String", "Dynamic Evaluation", "INJ-001"),
    ("b04", "basic", "DOM XSS from URL Hash", "Cross-Site Scripting", "XSS-001"),
    ("b05", "basic", "Write the Query String", "Cross-Site Scripting", "XSS-001"),
    ("b06", "basic", "Predictable Session Token", "Weak Cryptography", "CRY-001"),
    ("b07", "basic", "Create an MD5 Digest", "Weak Cryptography", "CRY-002"),
    ("b08", "basic", "Hard-Coded API and JWT Secrets", "Hard-Coded Secret", "SEC-001"),
    ("b09", "basic", "Disable TLS Verification", "TLS Validation", "NET-003"),
    ("i01", "intermediate", "Express Command Injection", "Command Injection", "INJ-002"),
    ("i02", "intermediate", "Express SQL Injection", "SQL Injection", "INJ-003"),
    ("i03", "intermediate", "Read a Requested Path", "Path Traversal", "IO-001"),
    ("i04", "intermediate", "Redirect to a Query URL", "Open Redirect", "NET-001"),
    ("i05", "intermediate", "Fetch a Requested URL", "Server-Side Request Forgery", "NET-002"),
    ("i06", "intermediate", "Render Raw React HTML", "Cross-Site Scripting", "XSS-002"),
    ("i07", "intermediate", "Use an Unverified JWT", "JWT Verification", "SEC-002"),
    ("i08", "intermediate", "Build a User Regular Expression", "Regular Expression DoS", "INJ-005"),
    ("i09", "intermediate", "Write a Message into HTML", "Cross-Site Scripting", "XSS-001"),
    ("a01", "advanced", "Merge Untrusted Configuration", "Prototype Pollution", "INJ-004"),
    ("a02", "advanced", "Evaluate an Inert Encoded Notice", "Obfuscation", "OBF-001"),
    ("a03", "advanced", "Evaluate Harmless Character Codes", "Obfuscation", "OBF-001"),
    ("a04", "advanced", "Express Security Review", "Multiple Security Issues", "INJ-002"),
    ("a05", "advanced", "Pass Host Through a Helper", "Command Injection", "INJ-002"),
    ("a06", "advanced", "Destructure a Requested Host", "Command Injection", "INJ-002"),
]
JS_SAFE = [
    "Pass Arguments to execFile",
    "Use Safe DOM APIs",
    "Bind Database Parameters",
    "Reduce a Path to its Basename",
    "Use Modern Crypto and TLS",
    "Clean Modern Module",
]
JS_UNICODE = ["Bidi-Controlled Comment", "Cyrillic Eval Look-Alike"]


def _entry(
    language: str,
    sid: str,
    level: str | None,
    kind: str,
    title: str,
    topic: str,
    code: str,
    rules: list[tuple[str, int]] | None = None,
    *,
    taint: bool = False,
    approximate: bool = False,
    chars: list[str] | None = None,
    clean: bool = False,
    demo_order: int | None = None,
    fix_expected: str | None = None,
) -> tuple[dict[str, Any], str]:
    ext = ".java" if language == "java" else ".js"
    folder = language
    expected = {
        "findings": [{"rule_id": r, "line": n} for r, n in rules or []],
        "min_findings": len(rules or []),
    }
    if clean:
        expected["clean_below"] = "medium"
    if taint:
        expected["taint"] = True
    notes = [
        f"Demonstrates {topic.lower()} in a small, inert {language.title()} example.",
        "The source uses a fake host or local-only data and is never executed by the catalogue.",
        "Review the marked API and the expected analyzer behavior.",
    ]
    row: dict[str, Any] = {
        "id": sid,
        "language": language,
        "file": f"{folder}/{sid}_{title.lower().replace(' ', '_')[:28]}{ext}",
        "title": title[:50],
        "kind": kind,
        "level": level,
        "topic": topic,
        "summary": notes[0],
        "notes": notes,
        "expect": expected,
        "fix_expected": fix_expected or ("none" if clean else "review"),
        "approximate": approximate,
        "special_chars": chars or [],
        "demo_order": demo_order,
    }
    SampleMeta.model_validate(row)
    return row, code.rstrip() + "\n"


def catalogue_s2() -> list[tuple[dict[str, Any], str]]:
    """Create 35 Java and 34 JavaScript rows; all metadata is schema-validated."""
    result = []
    for suffix, level, title, topic, rule in JAVA_SPECS:
        sid = f"jv-{suffix}"
        code = JAVA[rule]
        if suffix in {"i01", "i07"}:
            code = (
                'String raw = request.getParameter("name");\nString name = raw;\n'
                "Statement stmt = connection.createStatement();\n"
                'stmt.executeQuery("SELECT * FROM users WHERE name=\'" + name + "\'");'
            )
        if suffix == "b04":
            code = 'MessageDigest digest = MessageDigest.getInstance("SHA-1");'
        elif suffix == "b05":
            code = 'Cipher cipher = Cipher.getInstance("DES");'
        elif suffix == "i02":
            code = 'String raw = request.getParameter("cmd");\nString cmd = raw;\nString command = "echo " + cmd;\nRuntime.getRuntime().exec(command);'
        elif suffix == "a01":
            code = "Object value = new ObjectInputStream(socket.getInputStream()).readObject();"
        elif suffix == "a02":
            code = 'String name = request.getParameter("name");\nreturn query(name);\nvoid query(String name) {\n Statement stmt = connection.createStatement();\n stmt.executeQuery("SELECT * FROM users WHERE name=" + name);\n}'
        elif suffix == "a03":
            code = 'String name = request.getParameter("name");\nif (name.matches("[0-9]+")) { return name; }\nStatement stmt = connection.createStatement();\nstmt.executeQuery("SELECT * FROM users WHERE name=" + name);'
        elif suffix == "a04":
            code = """String name = request.getParameter("name");
Statement stmt = connection.createStatement();
stmt.executeQuery("SELECT * FROM users WHERE name=" + name);
response.getWriter().println(request.getParameter("q"));
String file = request.getParameter("file");
new FileInputStream(baseDir + file);
MessageDigest.getInstance("MD5");
String password = "demo-credential-value-2026";
DriverManager.getConnection("jdbc:example:mem", "demo", password);
DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(request.getInputStream());
"""
            code += "// inert review context\n" * 60
        elif suffix == "a05":
            code = "Object value = new XMLDecoder(request.getInputStream()).readObject();"
        elif suffix == "b09":
            code = 'Object value = new ObjectInputStream(new FileInputStream("sample.bin")).readObject();'
        elif suffix == "a06":
            code += '\nString password = "demo-credential-value-2026";'
        imports = (
            "package demo;\nimport java.io.*;\nimport java.net.*;\nimport java.security.*;\n"
            "import java.security.cert.*;\nimport java.sql.*;\nimport java.util.*;\n"
            "import javax.crypto.*;\nimport javax.net.ssl.*;\nimport javax.script.*;\n"
            "import javax.servlet.http.*;\nimport javax.xml.parsers.*;\nimport java.beans.*;\n"
        )
        header = (
            imports
            + "class "
            + "Sample"
            + suffix.upper()
            + " {\n  void handle(HttpServletRequest request, HttpServletResponse response) throws Exception {\n"
        )
        body = "\n".join("    " + line if line else "" for line in code.splitlines())
        source = (
            header
            + '    String baseDir = "data/";\n    Connection connection = null;\n    Socket socket = new Socket();\n'
            + body
            + "\n  }\n}\n"
        )
        if suffix == "a02":
            source = imports + (
                "class SampleA02 {\n  Connection connection;\n"
                '  void handle(HttpServletRequest request) {\n    String name = request.getParameter("name");\n    query(name);\n  }\n'
                "  void query(String name) throws Exception {\n    Statement stmt = connection.createStatement();\n"
                '    stmt.executeQuery("SELECT * FROM users WHERE name=" + name);\n  }\n}\n'
            )
        if suffix == "a03":
            source = source.replace(
                'if (name.matches("[0-9]+")) { return name; }',
                'if (name.matches("[0-9]+")) { System.out.println(name); }',
            )
        ids = {
            "INJ-001": "APS-JV-INJ-001",
            "INJ-002": "APS-JV-INJ-002",
            "CRY-001": "APS-JV-CRY-001",
            "CRY-002": "APS-JV-CRY-002",
            "CRY-003": "APS-JV-CRY-003",
            "SEC-001": "APS-JV-SEC-001",
            "DES-001": "APS-JV-DES-001",
            "XSS-001": "APS-JV-XSS-001",
            "IO-001": "APS-JV-IO-001",
            "NET-001": "APS-JV-NET-001",
            "XML-001": "APS-JV-XML-001",
            "INJ-003": "APS-JV-INJ-003",
            "INJ-004": "APS-JV-INJ-004",
            "NET-002": "APS-JV-NET-002",
        }
        expected_rule = ids[rule]
        target_line = next(
            (
                n
                for n, line in enumerate(source.splitlines(), 1)
                if (
                    "getInstance(" in line
                    or "executeQuery(" in line
                    or "exec(" in line
                    or "readObject(" in line
                    or "getWriter()" in line
                    or "new URL(" in line
                    or "new FileInputStream(" in line
                    or "getDeclaredConstructor" in line
                    or ".eval(" in line
                    or "HostnameVerifier" in line
                    or "password =" in line
                    or "DocumentBuilderFactory.newInstance" in line
                )
            ),
            1,
        )
        taint = suffix in {"i01", "i02"}
        if suffix == "b07":
            target_line = next(
                n for n, line in enumerate(source.splitlines(), 1) if "new java.util.Random" in line
            )
        if suffix in {"u01", "u02", "u03"}:
            cp = [0x202E, 0x202E, 0x0435][int(suffix[-1]) - 1]
            character = chr(cp)
            java = f'package demo;\nimport java.util.*;\nclass Sample{suffix.upper()} {{\n  void note() {{\n    // visible note {character}\n    String e{character}mail = "reader";\n  }}\n}}'
            rr = "APS-JV-UNI-001" if suffix != "u03" else "APS-ALL-UNI-004"
            result.append(
                _entry(
                    "java",
                    sid,
                    None,
                    "unicode",
                    title,
                    "Unicode Review",
                    java,
                    [(rr, 4)],
                    chars=[f"U+{cp:04X}"],
                )
            )
        elif suffix == "a04":
            result.append(
                _entry(
                    "java",
                    sid,
                    level,
                    "vulnerable",
                    title,
                    topic,
                    source,
                    [
                        ("APS-JV-INJ-002", 21),
                        ("APS-JV-XSS-001", 22),
                        ("APS-JV-IO-001", 24),
                        ("APS-JV-CRY-001", 25),
                        ("APS-JV-SEC-001", 26),
                        ("APS-JV-XML-001", 28),
                    ],
                    fix_expected="review",
                    demo_order=13,
                )
            )
        else:
            result.append(
                _entry(
                    "java",
                    sid,
                    level,
                    "vulnerable",
                    title,
                    topic,
                    source,
                    [(expected_rule, target_line)],
                    taint=taint,
                    approximate=suffix in {"a02", "a03"},
                    demo_order={"i01": 7, "i06": 8, "a04": 13}.get(suffix),
                    fix_expected={
                        "b02": "review",
                        "b03": "safe",
                        "b04": "safe",
                        "b05": "manual",
                        "b06": "manual",
                        "b07": "review",
                        "b08": "review",
                        "i02": "review",
                        "i06": "review",
                        "a02": "manual",
                        "a03": "review",
                        "a04": "review",
                        "a06": "none",
                    }.get(suffix, "none"),
                )
            )
    for index, title in enumerate(JAVA_SAFE, 1):
        sid = f"jv-s{index:02}"
        safe_bodies = {
            1: 'PreparedStatement stmt = connection.prepareStatement("SELECT * FROM users WHERE name=?");\nstmt.setString(1, name);\nstmt.executeQuery();',
            2: 'int id = Integer.parseInt(request.getParameter("id"));\nStatement stmt = connection.createStatement();\nstmt.executeQuery("SELECT * FROM users WHERE id=" + id);',
            3: 'MessageDigest.getInstance("SHA-256");\nnew SecureRandom().nextBytes(new byte[16]);\nCipher.getInstance("AES/GCM/NoPadding");\nnew ProcessBuilder("echo", "ready").start();',
            4: 'DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();\nfactory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);\nfactory.setFeature("http://xml.org/sax/features/external-general-entities", false);',
            5: "Path root = Paths.get(base).toAbsolutePath().normalize();\nPath target = root.resolve(name).normalize();\nif (target.startsWith(root)) { return target.toString(); }",
            6: '@Deprecated\nrecord Entry<T>(T value) {}\nOptional<Entry<String>> result = Stream.of(new Entry<>("ready")).findFirst();',
        }
        source = f"package demo;\nimport java.io.*;\nimport java.nio.file.*;\nimport java.security.*;\nimport java.sql.*;\nimport java.util.*;\nimport java.util.stream.*;\nimport javax.crypto.*;\nimport javax.xml.parsers.*;\nclass Safe{index} {{\n  String read(String id) throws Exception {{\n    {safe_bodies[index]}\n    return id;\n  }}\n}}"
        result.append(_entry("java", sid, None, "safe", title, "Safe Java API", source, clean=True))
    for index, title in enumerate(JAVA_UNICODE, 1):
        sid = f"jv-u{index:02}"
        if index == 1:
            cp = 0x202E
            source = f"package demo;\nimport java.util.*;\nclass UnicodeOne {{\n  void note() {{\n    // display {chr(cp)} comment\n  }}\n}}"
            rule = "APS-ALL-UNI-001"
        elif index == 2:
            cp = 0x202E
            source = 'package demo;\nimport java.util.*;\nclass UnicodeTwo {\n  String note() { return "\\u202E"; }\n}'
            rule = "APS-ALL-UNI-001"
        else:
            cp = 0x0435
            source = f"package demo;\nimport java.util.*;\nclass UnicodeThree {{\n  void note() {{\n    int l{chr(cp)}vel = 1;\n  }}\n}}"
            rule = "APS-ALL-UNI-004"
        result.append(
            _entry(
                "java",
                sid,
                None,
                "unicode",
                title,
                "Unicode Review",
                source,
                [(rule, {1: 5, 2: 4, 3: 5}[index])],
                chars=["U+005C"] if index == 2 else [f"U+{cp:04X}"],
                fix_expected="none" if index == 2 else None,
            )
        )
    # Java lexer showcase.
    result.append(
        _entry(
            "java",
            "jv-l01",
            None,
            "lexer",
            "Java Lexer Showcase",
            "Lexer Coverage",
            'package demo;\nimport java.util.*;\n@interface Mark { String value(); }\nrecord Item<T>(T value) {}\nclass LexerShowcase {\n  String text = "quotes \\" and // not comment";\n  long count = 1_000L + 0x1F + 0b101;\n  float ratio = 1e3f;\n  java.util.function.Function<String, String> fn = value -> switch (value) { case "x" -> "/* text */"; default -> "ok"; };\n  String block = """\n    text block\n    """;\n}',
            clean=True,
        )
    )

    for suffix, level, title, topic, rule in JS_SPECS:
        sid = f"js-{suffix}"
        code = JS[rule]
        if suffix in {"b02", "b03", "b05", "i09"}:
            code = {
                "b02": "new Function(code)();",
                "b03": 'setTimeout("doWork()", 100);',
                "b05": "document.write(location.search);",
                "i09": "window.addEventListener('message', event => { element.innerHTML = event.data; });",
            }[suffix]
        elif suffix == "a03":
            code = "eval(String.fromCharCode(99,111,110,115,111,108,101,46,108,111,103,40,49,41));"
        elif suffix == "a05":
            code = (
                "const host = req.query.host;\nrunCmd(host);\nfunction runCmd(cmd) { exec(cmd); }"
            )
        elif suffix == "a06":
            code = "const { host } = req.query;\nexec(`ping ${host}`);"
        elif suffix == "i01":
            code = 'const raw = req.query.host;\nconst host = raw;\nconst command = "ping " + host;\nexec(command);'
        elif suffix == "i02":
            code = "const raw = req.query.id;\nconst id = raw;\ndb.query(`SELECT * FROM users WHERE id=${id}`);"
        elif suffix == "i03":
            code = 'fs.readFile("uploads/" + req.query.file, callback);'
        elif suffix == "a04":
            code = (
                """app.get("/review", (req, res) => {
  exec("ping " + req.query.host);
  db.query(`SELECT * FROM users WHERE id=${req.query.id}`);
  fs.readFile("uploads/" + req.query.file, () => {});
  element.innerHTML = location.hash;
  const token = Math.random().toString(36);
  const api_key = "A7kQ9mP2xR5vT8wY3zB6";
  res.send(page + token + api_key);
});
"""
                + "// inert route notes\n" * 65
            )
        prefix = "import { exec } from 'node:child_process';\n"
        source = (
            prefix
            + "function sample(req, res) {\n"
            + "\n".join("  " + ln for ln in code.splitlines())
            + "\n}\n"
        )
        maprule = {
            "INJ-001": "APS-JS-INJ-001",
            "INJ-002": "APS-JS-INJ-002",
            "INJ-003": "APS-JS-INJ-003",
            "INJ-004": "APS-JS-INJ-004",
            "INJ-005": "APS-JS-INJ-005",
            "XSS-001": "APS-JS-XSS-001",
            "XSS-002": "APS-JS-XSS-002",
            "IO-001": "APS-JS-IO-001",
            "NET-001": "APS-JS-NET-001",
            "NET-002": "APS-JS-NET-002",
            "NET-003": "APS-JS-NET-003",
            "CRY-001": "APS-JS-CRY-001",
            "CRY-002": "APS-JS-CRY-002",
            "SEC-001": "APS-JS-SEC-001",
            "SEC-002": "APS-JS-SEC-002",
            "OBF-001": "APS-JS-OBF-001",
        }
        # Rules identify the relevant call/assignment on its containing line.
        target_line = next(
            (
                n
                for n, line in enumerate(source.splitlines(), 1)
                if any(
                    term in line
                    for term in (
                        "eval(",
                        "new Function",
                        "setTimeout(",
                        "innerHTML",
                        "document.write",
                        "Math.random",
                        "createHash",
                        "api_key",
                        "rejectUnauthorized",
                        "exec(",
                        "db.query",
                        "readFile(",
                        "location.href",
                        "axios.get",
                        "dangerouslySetInnerHTML",
                        "jwt.decode",
                        "new RegExp",
                        "Object.assign",
                        "atob(",
                        "fromCharCode",
                        "exec(`",
                    )
                )
            ),
            1,
        )
        taint = suffix in {"i01", "i02", "a05"}
        if suffix == "a04":
            result.append(
                _entry(
                    "javascript",
                    sid,
                    level,
                    "vulnerable",
                    title,
                    topic,
                    source,
                    [
                        ("APS-JS-INJ-002", 4),
                        ("APS-JS-INJ-003", 5),
                        ("APS-JS-IO-001", 6),
                        ("APS-JS-XSS-001", 7),
                        ("APS-JS-CRY-001", 8),
                        ("APS-JS-SEC-001", 9),
                    ],
                    demo_order=10,
                    fix_expected="review",
                )
            )
        else:
            result.append(
                _entry(
                    "javascript",
                    sid,
                    level,
                    "vulnerable",
                    title,
                    topic,
                    source,
                    [(maprule[rule], target_line)],
                    taint=taint,
                    approximate=suffix == "a06",
                    demo_order={"b04": 9, "a01": 10}.get(suffix),
                    fix_expected={
                        "b01": "review",
                        "b04": "review",
                        "b05": "manual",
                        "b06": "review",
                        "b07": "review",
                        "b08": "manual",
                        "b09": "safe",
                        "i01": "review",
                        "i02": "review",
                        "i06": "review",
                        "i09": "review",
                        "a05": "review",
                    }.get(suffix, "none"),
                )
            )
    for index, title in enumerate(JS_SAFE, 1):
        sid = f"js-s{index:02}"
        safe_sources = {
            1: 'import { execFile } from "node:child_process";\nexecFile("ls", ["-l", dir], callback);',
            2: "element.textContent = value;\nelement.innerHTML = DOMPurify.sanitize(html);",
            3: 'db.query("SELECT * FROM users WHERE id = $1", [id]);',
            4: "fs.readFile(path.join(base, path.basename(req.query.file)), callback);",
            5: 'const token = crypto.randomUUID();\ncrypto.createHash("sha256").update(value);\nconst agent = new https.Agent({ rejectUnauthorized: true });',
            6: 'class Service { #ready = true; async read(item) { return item?.name ?? "ready"; } *items() { yield this.#ready; } }',
        }
        source = safe_sources[index]
        result.append(
            _entry(
                "javascript", sid, None, "safe", title, "Safe JavaScript API", source, clean=True
            )
        )
    for index, title in enumerate(JS_UNICODE, 1):
        sid = f"js-u{index:02}"
        cp = 0x202E if index == 1 else 0x0435
        source = (
            f"const message = 'review'; // note {chr(cp)}\nconsole.log(message);"
            if index == 1
            else f"const input = location.hash;\nconst {chr(0x0435)}val = input;\n{chr(0x0435)}val(input);"
        )
        rr = "APS-ALL-UNI-001" if index == 1 else "APS-ALL-UNI-006"
        result.append(
            _entry(
                "javascript",
                sid,
                None,
                "unicode",
                title,
                "Unicode Review",
                source,
                [(rr, 1)],
                chars=[f"U+{cp:04X}"],
            )
        )
    lexer_nested = r"""const nested = `outer ${`middle ${`inner ${value}`}`}`;
const quotient = numerator / denominator;
const pattern = /a\/b+/giu;
function getValue() { return /x/.test(value); }
// regex after return and slash-like comment text: /a\/b/
"""
    lexer_modern = r"""const huge = 10n;
const count = 1_000;
settings.timeout ??= 20;
class LexerCase { #secret = 1_000; get value() { return this.#secret ??= 2; } set value(next) { this.#secret = next; } }
try { throw new Error("demo"); } catch { /* optional binding */ }
const tagged = String.raw`line\\n${value}`;
"""
    result.append(
        _entry(
            "javascript",
            "js-l01",
            None,
            "lexer",
            "Templates and Slash Ambiguity",
            "Lexer Coverage",
            lexer_nested,
            clean=True,
        )
    )
    result.append(
        _entry(
            "javascript",
            "js-l02",
            None,
            "lexer",
            "Modern JavaScript Syntax",
            "Lexer Coverage",
            lexer_modern,
            clean=True,
        )
    )
    return result
