"""Script to generate all JavaScript test fixtures and expect.json with precise (rule_id, line) entries."""

import json
from pathlib import Path

BASE = Path("tests/fixtures/javascript")
VULN = BASE / "vulnerable"
SAFE = BASE / "safe"
ADV = BASE / "adversarial"

VULN.mkdir(parents=True, exist_ok=True)
SAFE.mkdir(parents=True, exist_ok=True)
ADV.mkdir(parents=True, exist_ok=True)

vulnerable_fixtures = {
    "code_injection_eval.js": (
        "function runDynamic(userInput) {\n"
        "    eval(userInput);\n"
        "}\n",
        [{"rule_id": "APS-JS-INJ-001", "line": 2}]
    ),
    "code_injection_settimeout.js": (
        "function scheduleTask(taskName) {\n"
        '    setTimeout("executeTask(" + taskName + ")", 1000);\n'
        "}\n",
        [{"rule_id": "APS-JS-INJ-001", "line": 2}]
    ),
    "code_injection_function.js": (
        "function makeHandler(codeStr) {\n"
        "    const fn = new Function('req', 'res', codeStr);\n"
        "    return fn;\n"
        "}\n",
        [{"rule_id": "APS-JS-INJ-001", "line": 2}]
    ),
    "cmd_injection_exec.js": (
        "const { exec } = require('child_process');\n"
        "function pingHost(host) {\n"
        '    exec("ping -c 1 " + host);\n'
        "}\n",
        [{"rule_id": "APS-JS-INJ-002", "line": 3}]
    ),
    "cmd_injection_spawn_shell.js": (
        "const { spawn } = require('child_process');\n"
        "function runShell(command) {\n"
        "    spawn(command, { shell: true });\n"
        "}\n",
        [{"rule_id": "APS-JS-INJ-002", "line": 3}]
    ),
    "dom_xss.js": (
        "const hash = location.hash.slice(1);\n"
        "const output = document.getElementById('output');\n"
        'output.innerHTML = "Welcome " + hash;\n',
        [{"rule_id": "APS-JS-XSS-001", "line": 3}]
    ),
    "dom_xss_doc_write.js": (
        "const name = new URLSearchParams(location.search).get('name');\n"
        'document.write("Hello " + name);\n',
        [{"rule_id": "APS-JS-XSS-001", "line": 2}]
    ),
    "dom_xss_outer_html.js": (
        "function updateWidget(userBio) {\n"
        "    const card = document.getElementById('card');\n"
        '    card.outerHTML = "<div class=\'card\'>" + userBio + "</div>";\n'
        "}\n",
        [{"rule_id": "APS-JS-XSS-001", "line": 3}]
    ),
    "react_xss_dangerously_set_inner_html.js": (
        "function UserCard({ bio }) {\n"
        "    return <div dangerouslySetInnerHTML={{ __html: bio }} />;\n"
        "}\n",
        [{"rule_id": "APS-JS-XSS-002", "line": 2}]
    ),
    "open_redirect_location.js": (
        "function redirectUser() {\n"
        "    const target = location.search.slice(1);\n"
        "    location.href = target;\n"
        "}\n",
        [{"rule_id": "APS-JS-NET-001", "line": 3}]
    ),
    "open_redirect_set_attribute.js": (
        "function bindEvent(elem, handlerCode) {\n"
        '    elem.setAttribute("onclick", handlerCode);\n'
        "}\n",
        [{"rule_id": "APS-JS-NET-001", "line": 2}]
    ),
    "sqli_concat.js": (
        "function getUser(id) {\n"
        '    db.query("SELECT * FROM users WHERE id = " + id);\n'
        "}\n",
        [{"rule_id": "APS-JS-INJ-003", "line": 2}]
    ),
    "sqli_template_literal.js": (
        "async function findItem(req) {\n"
        "    const id = req.query.id;\n"
        "    const query = `SELECT * FROM items WHERE id = ${id}`;\n"
        "    await db.query(query);\n"
        "}\n",
        [{"rule_id": "APS-JS-INJ-003", "line": 4}]
    ),
    "path_traversal_read_file.js": (
        "const fs = require('fs');\n"
        "function loadDoc(req, res) {\n"
        "    const file = req.params.file;\n"
        "    fs.readFile('/data/' + file, 'utf8', (err, data) => res.send(data));\n"
        "}\n",
        [{"rule_id": "APS-JS-IO-001", "line": 4}]
    ),
    "path_traversal_send_file.js": (
        "function serveUpload(req, res) {\n"
        "    const filename = req.query.name;\n"
        "    res.sendFile('/uploads/' + filename);\n"
        "}\n",
        [{"rule_id": "APS-JS-IO-001", "line": 3}]
    ),
    "ssrf_fetch.js": (
        "async function proxyFetch(req, res) {\n"
        "    const url = req.query.url;\n"
        "    const resp = await fetch(url);\n"
        "    res.send(await resp.text());\n"
        "}\n",
        [{"rule_id": "APS-JS-NET-002", "line": 3}]
    ),
    "ssrf_axios.js": (
        "const axios = require('axios');\n"
        "function fetchRemote(req, res) {\n"
        "    const target = req.query.target;\n"
        '    axios.get("http://" + target);\n'
        "}\n",
        [{"rule_id": "APS-JS-NET-002", "line": 4}]
    ),
    "insecure_random_token.js": (
        "function generateSessionToken() {\n"
        "    const sessionToken = Math.random().toString(36).substring(2);\n"
        "    return sessionToken;\n"
        "}\n",
        [{"rule_id": "APS-JS-CRY-001", "line": 2}]
    ),
    "crypto_md5.js": (
        "const crypto = require('crypto');\n"
        "function hashPassword(password) {\n"
        '    return crypto.createHash("md5").update(password).digest("hex");\n'
        "}\n",
        [{"rule_id": "APS-JS-CRY-002", "line": 3}]
    ),
    "crypto_sha1.js": (
        "const crypto = require('crypto');\n"
        "function hashData(data) {\n"
        '    return crypto.createHash("sha1").update(data).digest("hex");\n'
        "}\n",
        [{"rule_id": "APS-JS-CRY-002", "line": 3}]
    ),
    "hardcoded_api_key.js": (
        'const API_KEY = "AKIA1234567890ABCDEF12";\n',
        [{"rule_id": "APS-JS-SEC-001", "line": 1}]
    ),
    "hardcoded_jwt_secret.js": (
        'const jwtSecret = "super_duper_secret_key_998877";\n',
        [{"rule_id": "APS-JS-SEC-001", "line": 1}]
    ),
    "jwt_none_algorithm.js": (
        "const jwt = require('jsonwebtoken');\n"
        "function verifyToken(token) {\n"
        "    return jwt.verify(token, 'secret', { algorithms: ['none'] });\n"
        "}\n",
        [{"rule_id": "APS-JS-SEC-002", "line": 3}]
    ),
    "prototype_pollution_assign.js": (
        "function updateConfig(req, res) {\n"
        "    const config = {};\n"
        "    Object.assign(config, req.body);\n"
        "}\n",
        [{"rule_id": "APS-JS-INJ-004", "line": 3}]
    ),
    "redos_dynamic_regex.js": (
        "function matchUser(req) {\n"
        "    const pattern = req.query.pattern;\n"
        "    const re = new RegExp(pattern);\n"
        '    return re.test("sample");\n'
        "}\n",
        [{"rule_id": "APS-JS-INJ-005", "line": 3}]
    ),
    "obfuscation_eval_atob.js": (
        "function execPayload() {\n"
        '    eval(atob("YWxlcnQoMSk="));\n'
        "}\n",
        [{"rule_id": "APS-JS-OBF-001", "line": 2}]
    ),
    "disabled_tls_env.js": (
        'process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";\n',
        [{"rule_id": "APS-JS-NET-003", "line": 1}]
    ),
    "disabled_tls_reject_unauthorized.js": (
        "const https = require('https');\n"
        "const agent = new https.Agent({\n"
        "    rejectUnauthorized: false\n"
        "});\n",
        [{"rule_id": "APS-JS-NET-003", "line": 3}]
    ),
}

safe_fixtures = {
    "safe_eval_json_parse.js": (
        "function parseConfig(raw) {\n"
        "    return JSON.parse(raw);\n"
        "}\n"
    ),
    "safe_timer_callback.js": (
        "function schedule(item) {\n"
        "    setTimeout(() => alert(item), 1000);\n"
        "}\n"
    ),
    "safe_cmd_exec_file.js": (
        "const { execFile } = require('child_process');\n"
        "function pingHost(host) {\n"
        '    execFile("ping", ["-c", "1", host]);\n'
        "}\n"
    ),
    "safe_spawn_array.js": (
        "const { spawn } = require('child_process');\n"
        "function listFiles() {\n"
        '    spawn("ls", ["-la"]);\n'
        "}\n"
    ),
    "safe_dom_text_content.js": (
        "const hash = location.hash.slice(1);\n"
        "const output = document.getElementById('output');\n"
        'output.textContent = "Welcome " + hash;\n'
    ),
    "safe_dom_purify_inner_html.js": (
        "function renderBio(userBio) {\n"
        "    const div = document.getElementById('bio');\n"
        "    div.innerHTML = DOMPurify.sanitize(userBio);\n"
        "}\n"
    ),
    "safe_react_dom_purify.js": (
        "function UserCard({ bio }) {\n"
        "    return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(bio) }} />;\n"
        "}\n"
    ),
    "safe_open_redirect_whitelist.js": (
        "function redirect() {\n"
        "    const target = '/dashboard';\n"
        "    location.href = target;\n"
        "}\n"
    ),
    "safe_sqli_parameterized.js": (
        "function getUser(id) {\n"
        '    db.query("SELECT * FROM users WHERE id = ?", [id]);\n'
        "}\n"
    ),
    "safe_sqli_pg_parameterized.js": (
        "function getItem(id) {\n"
        '    pool.query("SELECT * FROM items WHERE id = $1", [id]);\n'
        "}\n"
    ),
    "safe_path_basename.js": (
        "const fs = require('fs');\n"
        "const path = require('path');\n"
        "function loadSafeDoc(req, res) {\n"
        "    const safeFile = path.basename(req.params.file);\n"
        "    fs.readFile(path.join('/data', safeFile), 'utf8', (err, data) => res.send(data));\n"
        "}\n"
    ),
    "safe_ssrf_whitelisted.js": (
        "function fetchInternal(endpoint) {\n"
        '    fetch("https://api.internal.corp/status");\n'
        "}\n"
    ),
    "safe_crypto_random_uuid.js": (
        "const crypto = require('crypto');\n"
        "function generateId() {\n"
        "    return crypto.randomUUID();\n"
        "}\n"
    ),
    "safe_crypto_random_bytes.js": (
        "const crypto = require('crypto');\n"
        "function generateKey() {\n"
        "    return crypto.randomBytes(32).toString('hex');\n"
        "}\n"
    ),
    "safe_math_random_dice.js": (
        "function rollDice() {\n"
        "    return Math.floor(Math.random() * 6) + 1;\n"
        "}\n"
    ),
    "safe_crypto_sha256.js": (
        "const crypto = require('crypto');\n"
        "function hashPassword(password) {\n"
        '    return crypto.createHash("sha256").update(password).digest("hex");\n'
        "}\n"
    ),
    "safe_crypto_sha512.js": (
        "const crypto = require('crypto');\n"
        "function hashData(data) {\n"
        '    return crypto.createHash("sha512").update(data).digest("hex");\n'
        "}\n"
    ),
    "safe_secret_env.js": (
        "const API_KEY = process.env.API_KEY || '';\n"
    ),
    "safe_secret_placeholder.js": (
        'const apiKey = "YOUR_API_KEY_HERE";\n'
    ),
    "safe_jwt_hs256.js": (
        "const jwt = require('jsonwebtoken');\n"
        "function verifyToken(token, secret) {\n"
        "    return jwt.verify(token, secret, { algorithms: ['HS256'] });\n"
        "}\n"
    ),
    "safe_object_assign_static.js": (
        "function mergeConfig(options) {\n"
        "    return Object.assign({}, { timeout: 5000 }, { retries: 3 });\n"
        "}\n"
    ),
    "safe_static_regex.js": (
        "function validateInput(str) {\n"
        "    const re = /^[a-zA-Z0-9_-]+$/;\n"
        "    return re.test(str);\n"
        "}\n"
    ),
    "safe_atob_decode_only.js": (
        "function decodeMessage(encoded) {\n"
        "    const decoded = atob(encoded);\n"
        "    console.log(decoded);\n"
        "}\n"
    ),
    "safe_tls_reject_unauthorized_true.js": (
        "const https = require('https');\n"
        "const agent = new https.Agent({\n"
        "    rejectUnauthorized: true\n"
        "});\n"
    ),
    "safe_tls_env_default.js": (
        "const https = require('https');\n"
        "// Normal TLS settings preserved\n"
        "https.get('https://example.com');\n"
    ),
}

adversarial_fixtures = {
    "adv_comment_exec.js": (
        "// child_process.exec('rm -rf ' + userInput);\n"
        "/* eval(untrustedData); */\n"
        "console.log('Secure application');\n"
    ),
    "adv_string_eval.js": (
        'const advice = "Never use eval(userInput) in your JavaScript source code.";\n'
        'const note = "Avoid setting innerHTML directly";\n'
        "console.log(advice, note);\n"
    ),
    "adv_regex_trap_division.js": (
        "const a = 100;\n"
        "const b = 20;\n"
        "const c = 2;\n"
        "const result = (a + b) / 2 / c;\n"
        "console.log(result);\n"
    ),
    "adv_division_trap_regex.js": (
        "function checkCode(code) {\n"
        "    return /^[A-Z0-9]+$/i.test(code);\n"
        "}\n"
    ),
    "adv_template_literal_constants.js": (
        "async function fetchRoles() {\n"
        "    const query = `SELECT * FROM roles WHERE status = ${'ACTIVE'}`;\n"
        "    return query;\n"
        "}\n"
    ),
    "adv_minified_safe.js": (
        "function a(b,c){var d=b+c;return d>10?d:0;}\n"
        "function f(x){return x*x;}\n"
        "console.log(a(2,3));\n"
    ),
    "adv_prototype_safe_assign.js": (
        "function createSafeDict() {\n"
        "    const target = Object.create(null);\n"
        "    return Object.assign(target, { safeKey: 1 });\n"
        "}\n"
    ),
    "adv_variable_name_traps.js": (
        "const options = {\n"
        "    eval: false,\n"
        "    exec: 'echo',\n"
        "    innerHTML: 'hello'\n"
        "};\n"
        "function getSetting(key) {\n"
        "    return options[key];\n"
        "}\n"
        "console.log(getSetting('exec'));\n"
    ),
}

expect_data = {
    "vulnerable": {},
    "safe": {},
    "adversarial": {}
}

for name, (code, exp) in vulnerable_fixtures.items():
    (VULN / name).write_text(code, encoding="utf-8")
    expect_data["vulnerable"][name] = exp

for name, code in safe_fixtures.items():
    (SAFE / name).write_text(code, encoding="utf-8")
    expect_data["safe"][name] = []

for name, code in adversarial_fixtures.items():
    (ADV / name).write_text(code, encoding="utf-8")
    expect_data["adversarial"][name] = []

(BASE / "expect.json").write_text(json.dumps(expect_data, indent=2), encoding="utf-8")
print(f"Generated {len(vulnerable_fixtures)} vulnerable, {len(safe_fixtures)} safe, {len(adversarial_fixtures)} adversarial fixtures.")
