"""Unit tests for the hand-written JavaScript lexical analyzer."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from apsla.languages.javascript_lang.lexer import JavaScriptLexer

# ── Property-Based Tests (Hypothesis) ─────────────────────────────────────────


@given(st.text())
@settings(max_examples=100)
def test_lexer_never_crashes_and_is_lossless(source: str) -> None:
    """Hypothesis property test: lexer never raises and always reconstructs source."""
    lexer = JavaScriptLexer(source)
    tokens = lexer.tokenize()
    reconstructed = "".join(t.text for t in tokens)
    assert reconstructed == source, "Token reconstruction must exactly match source"


# ── Regex vs Division Disambiguation Table Test (35+ cases) ───────────────────


REGEX_VS_DIVISION_CASES = [
    # Division cases (after operand / identifier / number / ) / ] / template / etc.)
    ("a / b", False),
    ("x / y / z", False),
    ("(x + y) / 2", False),
    ("arr[0] / 5", False),
    ("100 / 10", False),
    ("3.14 / 2", False),
    ("0x10 / 2", False),
    ("10n / 2n", False),
    ('"hello" / 2', False),
    ("'world' / 2", False),
    ("`template` / 2", False),
    ("this / 2", False),
    ("super / 2", False),
    ("true / 2", False),
    ("false / 2", False),
    ("null / 2", False),
    ("undefined / 2", False),
    ("x++ / 2", False),
    ("x-- / 2", False),
    ("foo() / 2", False),
    # Regex cases (after operator / keyword / delimiter / start of file)
    ("/abc/", True),
    ("return /abc/", True),
    ("return /abc/g", True),
    ("typeof /abc/", True),
    ("x = /abc/", True),
    ("x == /abc/", True),
    ("x === /abc/", True),
    ("x != /abc/", True),
    ("x !== /abc/", True),
    ("x += /abc/", True),
    ("x && /abc/.test(s)", True),
    ("x || /abc/.test(s)", True),
    ("x ?? /abc/", True),
    ("!/abc/.test(s)", True),
    ("x ? /abc/ : /def/", True),
    ("(/abc/)", True),
    ("[/abc/]", True),
    ("{ key: /abc/ }", True),
    ("; /abc/.test(s)", True),
    ("foo(/abc/)", True),
    ("foo(a, /abc/)", True),
    ("=> /abc/", True),
    (".../abc/", True),
    ("yield /abc/", True),
    ("await /abc/", True),
    ("throw /abc/", True),
    ("delete /abc/", True),
    ("case /abc/:", True),
    ("+ /abc/", True),
    ("- /abc/", True),
    ("~ /abc/", True),
]


@pytest.mark.parametrize("expr,is_regex", REGEX_VS_DIVISION_CASES)
def test_regex_vs_division_table(expr: str, is_regex: bool) -> None:
    """Verify that '/' is correctly disambiguated between regex literal and division."""
    lexer = JavaScriptLexer(expr)
    tokens = lexer.tokenize()
    reconstructed = "".join(t.text for t in tokens)
    assert reconstructed == expr

    has_regex_tok = any(t.kind == "REGEX" for t in tokens)
    if is_regex:
        assert has_regex_tok, f"Expected REGEX in '{expr}', got {[t.kind for t in tokens]}"
    else:
        assert not has_regex_tok, f"Expected DIVISION in '{expr}', got REGEX token"


# ── Nested Template Literals Test (3 levels) ──────────────────────────────────


def test_nested_template_literals_3_levels() -> None:
    """Verify arbitrary nesting of template literals with expressions to 3 levels."""
    code = "`L1 pre ${`L2 pre ${`L3 ${1 + 2} L3 post`} L2 post`} L1 post`"
    lexer = JavaScriptLexer(code)
    tokens = lexer.tokenize()

    assert "".join(t.text for t in tokens) == code
    assert all(t.kind != "ERROR" for t in tokens)

    # Check that inner expressions are tokenized properly
    num_tokens = [t for t in tokens if t.kind == "NUMBER"]
    assert len(num_tokens) == 2
    assert num_tokens[0].text == "1"
    assert num_tokens[1].text == "2"

    op_tokens = [t for t in tokens if t.kind == "OPERATOR" and t.text == "+"]
    assert len(op_tokens) == 1


def test_template_literal_with_object_braces() -> None:
    """Verify template expressions containing object literal braces do not exit early."""
    code = "const msg = `Data: ${{ a: 1, b: 2 }}`;"
    lexer = JavaScriptLexer(code)
    tokens = lexer.tokenize()

    assert "".join(t.text for t in tokens) == code
    assert all(t.kind != "ERROR" for t in tokens)


# ── 15 Realistic Hand-Written Files (Zero ERROR Tokens) ─────────────────────────


REALISTIC_JS_FILES = [
    # 1. Express REST API with async handlers
    (
        "express_api",
        """
        const express = require('express');
        const router = express.Router();

        router.get('/users/:id', async (req, res, next) => {
            try {
                const userId = parseInt(req.params.id, 10);
                if (Number.isNaN(userId)) {
                    return res.status(400).json({ error: 'Invalid ID' });
                }
                const user = await db.findUser(userId);
                return res.json({ data: user });
            } catch (err) {
                return next(err);
            }
        });

        module.exports = router;
        """,
    ),
    # 2. React JSX Component with hooks
    (
        "react_jsx",
        """
        import React, { useState, useEffect } from 'react';

        export function UserProfile({ userId, onUpdate }) {
            const [user, setUser] = useState(null);
            const [loading, setLoading] = useState(true);

            useEffect(() => {
                let mounted = true;
                fetch(`/api/users/${userId}`)
                    .then(res => res.json())
                    .then(data => {
                        if (mounted) {
                            setUser(data);
                            setLoading(false);
                        }
                    });
                return () => { mounted = false; };
            }, [userId]);

            if (loading) return <div className="spinner">Loading...</div>;

            return (
                <section className="profile-card">
                    <header>
                        <h2>{user?.name ?? 'Anonymous'}</h2>
                        <span className="badge">{user?.role}</span>
                    </header>
                    <p>{user?.bio}</p>
                    <button type="button" onClick={() => onUpdate?.(user)}>Edit</button>
                    <>
                        <hr />
                        <small>Profile loaded successfully</small>
                    </>
                </section>
            );
        }
        """,
    ),
    # 3. Node.js HTTP Server with Event Emitters
    (
        "http_server",
        """
        const http = require('http');
        const EventEmitter = require('events');

        class ServerEvents extends EventEmitter {}
        const serverBus = new ServerEvents();

        const server = http.createServer((req, res) => {
            serverBus.emit('request', req.method, req.url);
            res.writeHead(200, { 'Content-Type': 'text/plain' });
            res.end('OK\\n');
        });

        serverBus.on('request', (method, url) => {
            console.log(`[HTTP] ${method} ${url}`);
        });

        server.listen(3000, '127.0.0.1');
        """,
    ),
    # 4. Modern ES2024 Class with private fields and static block
    (
        "modern_class",
        """
        class BankAccount {
            #balance = 0n;
            #accountHolder;
            static #totalAccounts = 0;

            static {
                console.log('Initializing BankAccount class registry');
            }

            constructor(holder, initialDeposit = 0n) {
                this.#accountHolder = holder;
                this.#balance = BigInt(initialDeposit);
                BankAccount.#totalAccounts++;
            }

            get balance() {
                return this.#balance;
            }

            deposit(amount) {
                if (amount <= 0n) throw new RangeError('Deposit must be positive');
                this.#balance += BigInt(amount);
                return this.#balance;
            }

            static get totalAccounts() {
                return BankAccount.#totalAccounts;
            }
        }
        """,
    ),
    # 5. Generator and Async Generator functions
    (
        "generators",
        """
        function* fibonacci(limit) {
            let [prev, curr] = [0, 1];
            while (curr < limit) {
                yield curr;
                [prev, curr] = [curr, prev + curr];
            }
        }

        async function* fetchPages(baseUrl) {
            let page = 1;
            while (true) {
                const res = await fetch(`${baseUrl}?page=${page}`);
                const data = await res.json();
                if (!data.items?.length) break;
                yield* data.items;
                page++;
            }
        }
        """,
    ),
    # 6. Number literals: hex, binary, octal, bigints, separators
    (
        "numbers_comprehensive",
        """
        const hex = 0xDeadBeef;
        const bin = 0b1010_0101;
        const oct = 0o755;
        const big = 1_000_000_000_000_000n;
        const float1 = 1_234.567_89e-4;
        const float2 = .95;
        const legacyOctal = 0777;
        const result = hex + bin + oct + Number(big);
        """,
    ),
    # 7. Obfuscated patterns: base64, char codes, escapes
    (
        "obfuscation_patterns",
        """
        const encoded = "SGVsbG8gV29ybGQ=";
        const decoded = atob(encoded);
        const chars = String.fromCharCode(72, 101, 108, 108, 111);
        const hexString = "\\x48\\x65\\x6c\\x6c\\x6f";
        const unicodeStr = "\\u0048\\u0065\\u006c\\u006c\\u006f";
        const codePoint = "\\u{1F600}";
        """,
    ),
    # 8. Complex Regex with flags and character classes
    (
        "regex_complex",
        """
        const emailRe = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$/iu;
        const urlRe = /https?:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b([-a-zA-Z0-9()@:%_\\+.~#?&//=]*)/d;
        const multilineSlash = /foo\\/bar\\/[0-9]+/gims;
        """,
    ),
    # 9. Modern operators: ??, ?., &&=, ||=, ??=, **=
    (
        "modern_operators",
        """
        let config = { timeout: null, retries: 0 };
        config.timeout ??= 5000;
        config.retries ||= 3;
        config.verbose &&= false;

        const port = config?.server?.port ?? 8080;
        let pow = 2;
        pow **= 8;
        const isReady = (pow > 100) ? true : false;
        """,
    ),
    # 10. CommonJS module with exports and require
    (
        "commonjs_module",
        """
        'use strict';
        const path = require('path');
        const fs = require('fs');

        function readConfig(filepath) {
            const resolved = path.resolve(filepath);
            return JSON.parse(fs.readFileSync(resolved, 'utf-8'));
        }

        module.exports = {
            readConfig,
            version: '1.0.0',
        };
        """,
    ),
    # 11. ESM Module with import and export varieties
    (
        "esm_module",
        """
        import { readFile, writeFile } from 'node:fs/promises';
        import * as path from 'node:path';
        import DefaultClient from './client.js';

        export const VERSION = '2.4.0';
        export default class Service extends DefaultClient {
            async load(name) {
                return await readFile(path.join('./data', name));
            }
        }
        export { DefaultClient as Client };
        """,
    ),
    # 12. DOM manipulation and events
    (
        "dom_events",
        """
        document.addEventListener('DOMContentLoaded', () => {
            const form = document.querySelector('#contact-form');
            form?.addEventListener('submit', (event) => {
                event.preventDefault();
                const formData = new FormData(form);
                const payload = Object.fromEntries(formData.entries());
                console.log('Submitted', payload);
            });
        });
        """,
    ),
    # 13. Async / Await with Promise combinators and try/finally
    (
        "async_flow",
        """
        async function fetchAllResources(urls) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);

            try {
                const requests = urls.map(u => fetch(u, { signal: controller.signal }));
                const results = await Promise.allSettled(requests);
                return results.filter(r => r.status === 'fulfilled').map(r => r.value);
            } finally {
                clearTimeout(timeoutId);
            }
        }
        """,
    ),
    # 14. Web Worker and MessageChannel
    (
        "web_worker",
        """
        self.addEventListener('message', (event) => {
            const { type, data } = event.data;
            if (type === 'COMPUTE') {
                const result = data.reduce((acc, val) => acc + val, 0);
                self.postMessage({ type: 'RESULT', result });
            }
        });
        """,
    ),
    # 15. Shebang, comments, HTML comments, Unicode identifiers
    (
        "shebang_and_comments",
        """#!/usr/bin/env node
        // Single-line comment
        /* Multi-line
           comment block */
        <!-- HTML style line comment
        const π = 3.1415926535;
        const 日本語 = "Japanese identifier";
        const $element = { id: 42 };
        const _private = true;
        console.log(π, 日本語, $element, _private);
        --> End HTML comment line
        """,
    ),
]


@pytest.mark.parametrize("name,code", REALISTIC_JS_FILES)
def test_realistic_js_files_have_zero_errors(name: str, code: str) -> None:
    """Verify that realistic JavaScript files lex cleanly with zero ERROR tokens."""
    lexer = JavaScriptLexer(code)
    tokens = lexer.tokenize()

    assert "".join(t.text for t in tokens) == code
    errors = [t for t in tokens if t.kind == "ERROR"]
    assert not errors, f"File '{name}' produced ERROR tokens: {errors}"
