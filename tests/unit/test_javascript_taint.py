"""Unit tests for JavaScript Taint-Lite engine and propagation mechanisms."""

from __future__ import annotations

from apsla.languages.javascript_lang.lexer import JavaScriptLexer
from apsla.languages.javascript_lang.profile import JS_TAINT_PROFILE
from apsla.lexing.common import OffsetMap
from apsla.pipeline import Analyzer
from apsla.taint.lite import TaintLiteEngine


def _run_js_taint(source: str):
    lexer = JavaScriptLexer(source)
    tokens = lexer.tokenize()
    omap = OffsetMap(source)
    engine = TaintLiteEngine(source, tokens, JS_TAINT_PROFILE, omap)
    return engine.analyze()


def test_template_literal_sqli_taint_path():
    """Verify that req.query.id -> template literal -> db.query gives a path."""
    source = """
    app.get('/users', async (req, res) => {
        const id = req.query.id;
        const query = `SELECT * FROM users WHERE id = '${id}'`;
        const result = await db.query(query);
        res.json(result);
    });
    """
    flows = _run_js_taint(source)
    assert len(flows) >= 1
    flow = flows[0]
    assert flow.rule_id == "APS-JS-INJ-003"

    # Must contain at least 3 steps: source -> propagate -> sink
    assert len(flow.path) >= 3
    assert flow.path[0].step.value == "source"
    assert flow.path[-1].step.value == "sink"
    steps = [s.step.value for s in flow.path]
    assert "propagate" in steps


def test_dom_xss_taint_path():
    """Verify location.hash -> intermediate -> innerHTML gives a DOM XSS taint path."""
    source = """
    function render() {
        const payload = location.hash.slice(1);
        const html = "<div>" + payload + "</div>";
        const container = document.getElementById('app');
        container.innerHTML = html;
    }
    """
    flows = _run_js_taint(source)
    assert len(flows) >= 1
    flow = flows[0]
    assert flow.rule_id == "APS-JS-XSS-001"
    assert len(flow.path) >= 3
    assert flow.path[0].step.value == "source"
    assert flow.path[-1].step.value == "sink"


def test_child_process_exec_taint_path():
    """Verify req.body.command -> exec gives a command injection taint path."""
    source = """
    const { exec } = require('child_process');
    app.post('/run', (req, res) => {
        const cmd = req.body.command;
        const full = "ping -c 1 " + cmd;
        exec(full, (err, stdout) => {
            res.send(stdout);
        });
    });
    """
    flows = _run_js_taint(source)
    assert len(flows) >= 1
    assert flows[0].rule_id == "APS-JS-INJ-002"
    assert len(flows[0].path) >= 3


def test_path_traversal_taint_path():
    """Verify req.params.file -> fs.readFile gives a path traversal taint path."""
    source = """
    const fs = require('fs');
    app.get('/download', (req, res) => {
        const filename = req.params.file;
        const targetPath = "/var/data/" + filename;
        fs.readFile(targetPath, 'utf8', (err, data) => {
            res.send(data);
        });
    });
    """
    flows = _run_js_taint(source)
    assert len(flows) >= 1
    assert flows[0].rule_id == "APS-JS-IO-001"
    assert len(flows[0].path) >= 3


def test_destructuring_source_taint():
    """Verify that destructuring assignment (const { id } = req.query) tracks taint."""
    source = """
    app.get('/profile', async (req, res) => {
        const { id } = req.query;
        const sql = "SELECT * FROM profiles WHERE user_id = '" + id + "'";
        const data = await db.query(sql);
        res.json(data);
    });
    """
    flows = _run_js_taint(source)
    assert len(flows) >= 1
    assert flows[0].rule_id == "APS-JS-INJ-003"


def test_sanitizer_dompurify():
    """Verify DOMPurify.sanitize clears taint for innerHTML sink."""
    source = """
    function renderUserContent() {
        const raw = location.search;
        const clean = DOMPurify.sanitize(raw);
        document.getElementById('content').innerHTML = clean;
    }
    """
    flows = _run_js_taint(source)
    assert len(flows) == 0


def test_sanitizer_parse_int():
    """Verify parseInt clears taint for SQL injection."""
    source = """
    app.get('/user', async (req, res) => {
        const rawId = req.query.id;
        const safeId = parseInt(rawId, 10);
        const query = "SELECT * FROM users WHERE id = " + safeId;
        const result = await db.query(query);
        res.json(result);
    });
    """
    flows = _run_js_taint(source)
    assert len(flows) == 0


def test_sanitizer_path_basename():
    """Verify path.basename clears taint for file read sink."""
    source = """
    const path = require('path');
    const fs = require('fs');
    app.get('/read', (req, res) => {
        const userPath = req.params.file;
        const safeName = path.basename(userPath);
        fs.readFile('/data/' + safeName, 'utf8', (err, data) => res.send(data));
    });
    """
    flows = _run_js_taint(source)
    assert len(flows) == 0


def test_analyzer_boosts_taint_confirmed_severity():
    """Verify analyzer flags taint confirmed findings as critical severity."""
    source = """
    app.get('/search', async (req, res) => {
        const term = req.query.q;
        const sql = `SELECT * FROM items WHERE name LIKE '%${term}%'`;
        const items = await db.query(sql);
        res.json(items);
    });
    """
    analyzer = Analyzer()
    result = analyzer.analyze(source, language="javascript", filename="search.js")
    sqli_findings = [f for f in result.findings if f.rule_id == "APS-JS-INJ-003"]
    assert len(sqli_findings) == 1
    f = sqli_findings[0]
    assert f.severity.value == "critical"
    assert f.evidence.get("taint_confirmed") is True
    assert len(f.taint_path) >= 3
