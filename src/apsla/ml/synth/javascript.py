"""Deterministic generator of labelled JavaScript synthetic snippets from varied templates."""

from __future__ import annotations

import random
from typing import Final

from apsla.languages.javascript_lang.lexer import JavaScriptLexer
from apsla.ml.synth.common import (
    LABEL_MALICIOUS,
    LABEL_SAFE,
    LABEL_SUSPICIOUS,
    SyntheticSnippet,
)

# ── Vocabulary Pools for Variation ────────────────────────────────────────────

VARS: Final[list[str]] = [
    "userInput",
    "cmdArg",
    "queryParam",
    "rawPayload",
    "reqData",
    "filePath",
    "targetDir",
    "userId",
    "tokenStr",
    "rawBody",
    "hostUrl",
    "catName",
    "secretToken",
    "searchKey",
    "endpointUri",
    "cacheId",
    "sessionId",
]

SAFE_VARS: Final[list[str]] = [
    "itemCount",
    "totalSum",
    "idx",
    "itemObj",
    "queryResult",
    "dataList",
    "metricVal",
    "appConfig",
    "loggerInstance",
    "statusCode",
    "respData",
    "reqOptions",
    "retryAttempts",
]

COMMENTS: Final[list[str]] = [
    "// Process incoming Express API request",
    "// Validate authentication token and request headers",
    "// Query persistent database for client records",
    "// Handle client-side browser DOM manipulation",
    "// High-throughput Redis caching resolution",
    "// Microservice communication event dispatcher",
    "// Render dynamic view template component",
    "// Sanitize input payload before persistence",
]

DISTRACTORS_PRE: Final[list[str]] = [
    (
        "const express = require('express');\n"
        "const router = express.Router();\n"
        "const path = require('path');\n"
        "const fs = require('fs');\n"
        "const logger = console;\n"
    ),
    (
        "import crypto from 'crypto';\n"
        "import axios from 'axios';\n"
        "import DOMPurify from 'isomorphic-dompurify';\n"
    ),
    (
        "const { exec, spawn } = require('child_process');\n"
        "const { Client } = require('pg');\n"
        "const dbClient = new Client();\n"
    ),
    ("import { useState, useEffect } from 'react';\nimport escapeHtml from 'escape-html';\n"),
]

DISTRACTORS_SAFE_BODY: Final[list[str]] = [
    (
        "function computeDigest(data) {\n"
        "    return crypto.createHash('sha256').update(data).digest('hex');\n"
        "}\n"
    ),
    (
        "const sanitizeFilename = (name) => {\n"
        "    return path.basename(name).replace(/[^a-zA-Z0-9._-]/g, '');\n"
        "};\n"
    ),
    (
        "function formatResponse(code, message, payload = null) {\n"
        "    return { status: code, message, data: payload, timestamp: Date.now() };\n"
        "}\n"
    ),
]


# ── Template Builders ─────────────────────────────────────────────────────────


def _generate_snippet(
    snippet_id: str,
    family: str,
    pre: str,
    core_lines: list[tuple[str, int]],  # (code_line, label_int)
    post: str = "\nmodule.exports = router;\n",
) -> SyntheticSnippet:
    """Combines segments, tokenizes via JavaScriptLexer, and labels tokens based on template spans."""
    full_code = pre + "\n" + "\n".join(line for line, _ in core_lines) + "\n" + post
    tokens = JavaScriptLexer(full_code).tokenize()

    offset_map: list[tuple[int, int, int]] = []
    curr_char = len(pre) + 1
    for line, label in core_lines:
        line_len = len(line)
        offset_map.append((curr_char, curr_char + line_len, label))
        curr_char += line_len + 1

    token_labels: list[int] = []
    char_cursor = 0
    for tok in tokens:
        tok_start = char_cursor
        tok_end = tok_start + len(tok.text)
        char_cursor = tok_end

        tok_label = LABEL_SAFE
        for start_c, end_c, lbl in offset_map:
            if max(tok_start, start_c) < min(tok_end, end_c):
                if tok.kind not in ("WHITESPACE", "NEWLINE", "COMMENT"):
                    tok_label = max(tok_label, lbl)
        token_labels.append(tok_label)

    return SyntheticSnippet(
        snippet_id=snippet_id,
        template_family=family,
        language="javascript",
        code=full_code,
        tokens=tokens,
        token_labels=token_labels,
    )


def _build_cmd_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 3)

    if variant == 0:
        lines = [
            ("router.get('/ping', (req, res) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    const {v} = req.query.host;", LABEL_SUSPICIOUS),
            (f"    exec('ping -c 1 ' + {v}, (err, stdout) => {{", LABEL_MALICIOUS),
            ("        res.send(stdout);", LABEL_SAFE),
            ("    });", LABEL_SAFE),
            ("});", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("function runUserScript(req, res) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    const {v} = req.body.command;", LABEL_SUSPICIOUS),
            (f'    const child = exec(`sh -c "${{{v}}}"`);', LABEL_MALICIOUS),
            ("    child.stdout.pipe(res);", LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("const executeBackup = (tableName) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    const cmd = 'mysqldump ' + tableName;", LABEL_SUSPICIOUS),
            ("    require('child_process').execSync(cmd);", LABEL_MALICIOUS),
            ("    return true;", LABEL_SAFE),
            ("};", LABEL_SAFE),
        ]
    else:
        lines = [
            ("router.post('/convert', (req, res) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    const {v} = req.body.format || 'pdf';", LABEL_SUSPICIOUS),
            (f"    exec('pandoc input.md -o output.' + {v});", LABEL_MALICIOUS),
            ("    res.json({ done: true });", LABEL_SAFE),
            ("});", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "cmd_injection", pre, lines)


def _build_code_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            ("function evaluateExpression(req, res) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    const {v} = req.query.expr;", LABEL_SUSPICIOUS),
            (f"    const result = eval({v});", LABEL_MALICIOUS),
            ("    res.json({ result });", LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("const createDynamicCalculator = (formulaStr) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    const fn = new Function('x', 'return ' + formulaStr);", LABEL_MALICIOUS),
            ("    return fn(42);", LABEL_SAFE),
            ("};", LABEL_SAFE),
        ]
    else:
        lines = [
            ("router.post('/timer', (req, res) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    const {v} = req.body.callbackCode;", LABEL_SUSPICIOUS),
            (f"    setTimeout({v}, 1000);", LABEL_MALICIOUS),
            ("    res.send('Scheduled');", LABEL_SAFE),
            ("});", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "code_injection", pre, lines)


def _build_dom_xss(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 3)

    if variant == 0:
        lines = [
            ("function renderUserProfile() {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    const params = new URLSearchParams(window.location.search);", LABEL_SAFE),
            (f"    const {v} = params.get('name');", LABEL_SUSPICIOUS),
            (f"    document.getElementById('header').innerHTML = 'Hello ' + {v};", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("const injectWidget = () => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    const payload = location.hash.substring(1);", LABEL_SUSPICIOUS),
            ("    document.write('<div>Welcome ' + payload + '</div>');", LABEL_MALICIOUS),
            ("};", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("function DynamicBanner({ bannerHtml }) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (
                "    return <div dangerouslySetInnerHTML={{ __html: bannerHtml }} />;",
                LABEL_MALICIOUS,
            ),
            ("}", LABEL_SAFE),
        ]
    else:
        lines = [
            ("function updateStatusMessage() {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    const ref = document.referrer;", LABEL_SUSPICIOUS),
            (
                "    document.querySelector('.notification').outerHTML = `<span>From: ${ref}</span>`;",
                LABEL_MALICIOUS,
            ),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "dom_xss", pre, lines)


def _build_sql_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            ("router.get('/user/:id', async (req, res) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    const {v} = req.params.id;", LABEL_SUSPICIOUS),
            (f"    const query = 'SELECT * FROM users WHERE id = ' + {v};", LABEL_SUSPICIOUS),
            ("    const results = await dbClient.query(query);", LABEL_MALICIOUS),
            ("    res.json(results.rows);", LABEL_SAFE),
            ("});", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("async function searchProducts(searchTerm) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (
                "    const sql = `SELECT * FROM items WHERE name LIKE '%${searchTerm}%'`;",
                LABEL_SUSPICIOUS,
            ),
            ("    return await dbClient.query(sql);", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    else:
        lines = [
            ("router.delete('/orders', async (req, res) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    const orderId = req.query.orderId;", LABEL_SUSPICIOUS),
            (
                "    await dbClient.query('DELETE FROM orders WHERE id = ' + orderId);",
                LABEL_MALICIOUS,
            ),
            ("    res.sendStatus(204);", LABEL_SAFE),
            ("});", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "sql_injection", pre, lines)


def _build_path_traversal(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 1)

    if variant == 0:
        lines = [
            ("router.get('/file', (req, res) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    const {v} = req.query.path;", LABEL_SUSPICIOUS),
            (f"    const fullPath = '/var/www/uploads/' + {v};", LABEL_SUSPICIOUS),
            ("    fs.readFile(fullPath, (err, data) => {", LABEL_MALICIOUS),
            ("        res.send(data);", LABEL_SAFE),
            ("    });", LABEL_SAFE),
            ("});", LABEL_SAFE),
        ]
    else:
        lines = [
            ("function loadConfigSync(fileName) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    const target = path.join('./config', fileName);", LABEL_SUSPICIOUS),
            ("    return fs.readFileSync(target, 'utf-8');", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "path_traversal", pre, lines)


def _build_weak_crypto(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            ("function hashUserPassword(password) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (
                "    return crypto.createHash('md5').update(password).digest('hex');",
                LABEL_MALICIOUS,
            ),
            ("}", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("const generateSignature = (payload) => {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (
                "    return crypto.createHash('sha1').update(payload).digest('hex');",
                LABEL_MALICIOUS,
            ),
            ("};", LABEL_SAFE),
        ]
    else:
        lines = [
            ("function generateResetCode() {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    const token = Math.random().toString(36).substring(2);", LABEL_MALICIOUS),
            ("    return token;", LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "weak_crypto", pre, lines)


def _build_hardcoded_secrets(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 3)

    if variant == 0:
        lines = [
            ("// Hardcoded Stripe live API token", LABEL_SAFE),
            (
                "const STRIPE_SECRET = 'sk_live_51M00000000000000000000000000000000000000';",
                LABEL_MALICIOUS,
            ),
            ("function getClient() { return { secret: STRIPE_SECRET }; }", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("// JWT authorization signing secret", LABEL_SAFE),
            ("const JWT_SECRET_KEY = 'super_secret_production_key_dont_share!';", LABEL_MALICIOUS),
            ("module.exports.signToken = (user) => jwt.sign(user, JWT_SECRET_KEY);", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("// AWS access keys committed to repository", LABEL_SAFE),
            ("const AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE';", LABEL_MALICIOUS),
            (
                "const AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';",
                LABEL_MALICIOUS,
            ),
        ]
    else:
        lines = [
            ("// OAuth client client credentials", LABEL_SAFE),
            ("const CLIENT_SECRET = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890';", LABEL_MALICIOUS),
            (
                "function getHeaders() { return { 'Authorization': `Bearer ${CLIENT_SECRET}` }; }",
                LABEL_SAFE,
            ),
        ]
    return _generate_snippet(sid, "hardcoded_secrets", pre, lines)


def _build_prototype_pollution(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    lines = [
        ("router.post('/settings', (req, res) => {", LABEL_SAFE),
        (f"    {c}", LABEL_SAFE),
        (f"    const {v} = req.body.config;", LABEL_SUSPICIOUS),
        (f"    const merged = Object.assign({{}}, JSON.parse({v}));", LABEL_MALICIOUS),
        ("    res.json(merged);", LABEL_SAFE),
        ("});", LABEL_SAFE),
    ]
    return _generate_snippet(sid, "prototype_pollution", pre, lines)


def _build_ssrf_networking(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    lines = [
        ("router.get('/proxy', async (req, res) => {", LABEL_SAFE),
        (f"    {c}", LABEL_SAFE),
        (f"    const {v} = req.query.url;", LABEL_SUSPICIOUS),
        (f"    const response = await axios.get({v});", LABEL_MALICIOUS),
        ("    res.send(response.data);", LABEL_SAFE),
        ("});", LABEL_SAFE),
    ]
    return _generate_snippet(sid, "ssrf_networking", pre, lines)


def _build_suspicious_patterns(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    lines = [
        ("function loadModule(pluginName) {", LABEL_SAFE),
        (f"    {c}", LABEL_SAFE),
        (f"    const {v} = './plugins/' + pluginName;", LABEL_SUSPICIOUS),
        (f"    return require({v});", LABEL_SUSPICIOUS),
        ("}", LABEL_SAFE),
    ]
    return _generate_snippet(sid, "suspicious_patterns", pre, lines)


def _build_safe_patterns(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    body = rng.choice(DISTRACTORS_SAFE_BODY)
    variant = rng.randint(0, 4)

    if variant == 0:
        lines = [
            ("router.get('/user/:id', async (req, res) => {", LABEL_SAFE),
            ("    const userId = parseInt(req.params.id, 10);", LABEL_SAFE),
            (
                "    if (Number.isNaN(userId)) return res.status(400).send('Invalid id');",
                LABEL_SAFE,
            ),
            (
                "    const result = await dbClient.query('SELECT * FROM users WHERE id = $1', [userId]);",
                LABEL_SAFE,
            ),
            ("    res.json(result.rows[0] || null);", LABEL_SAFE),
            ("});", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("function renderComment(rawComment) {", LABEL_SAFE),
            ("    const cleanHtml = DOMPurify.sanitize(rawComment);", LABEL_SAFE),
            ("    document.getElementById('comment-box').innerHTML = cleanHtml;", LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("const generateCryptoToken = () => {", LABEL_SAFE),
            ("    return crypto.randomBytes(32).toString('hex');", LABEL_SAFE),
            ("};", LABEL_SAFE),
        ]
    elif variant == 3:
        lines = [
            ("router.get('/download', (req, res) => {", LABEL_SAFE),
            (
                "    const safeFile = sanitizeFilename(req.query.filename || 'report.pdf');",
                LABEL_SAFE,
            ),
            ("    const resolvedPath = path.join(__dirname, 'public', safeFile);", LABEL_SAFE),
            ("    res.sendFile(resolvedPath);", LABEL_SAFE),
            ("});", LABEL_SAFE),
        ]
    else:
        lines = [
            ("function runBoundedSubprocess(argList) {", LABEL_SAFE),
            (
                "    return spawn('ls', ['-lh', '--', ...argList], { stdio: 'inherit' });",
                LABEL_SAFE,
            ),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "safe_patterns", pre + body, lines)


# ── Public Generator ──────────────────────────────────────────────────────────


def generate_javascript_dataset(
    count: int = 3000,
    seed: int = 42,
) -> list[SyntheticSnippet]:
    """Generates at least `count` deterministic, leak-free labeled JavaScript snippets.

    Args:
        count: Minimum number of snippets to synthesize (default: 3000).
        seed: Random seed for reproducibility (default: 42).

    Returns:
        List of SyntheticSnippet instances with ground truth per-token labels.
    """
    rng = random.Random(seed)
    families = [
        ("cmd_injection", _build_cmd_injection, 0.10),
        ("code_injection", _build_code_injection, 0.08),
        ("dom_xss", _build_dom_xss, 0.10),
        ("sql_injection", _build_sql_injection, 0.09),
        ("path_traversal", _build_path_traversal, 0.08),
        ("weak_crypto", _build_weak_crypto, 0.08),
        ("hardcoded_secrets", _build_hardcoded_secrets, 0.08),
        ("prototype_pollution", _build_prototype_pollution, 0.07),
        ("ssrf_networking", _build_ssrf_networking, 0.07),
        ("suspicious_patterns", _build_suspicious_patterns, 0.08),
        ("safe_patterns", _build_safe_patterns, 0.25),
    ]

    builders = [f[1] for f in families]
    weights = [f[2] for f in families]

    snippets: list[SyntheticSnippet] = []
    for i in range(count):
        sid = f"synth-js-{i:05d}"
        chosen_builder = rng.choices(builders, weights=weights, k=1)[0]
        snippet = chosen_builder(rng, sid)
        snippets.append(snippet)

    return snippets
