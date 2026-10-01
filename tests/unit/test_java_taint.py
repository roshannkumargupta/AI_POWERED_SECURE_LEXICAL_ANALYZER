"""Unit tests for Java Taint-Lite engine and propagation mechanisms."""

from __future__ import annotations

from apsla.languages.java_lang.lexer import JavaLexer
from apsla.languages.java_lang.profile import JAVA_TAINT_PROFILE
from apsla.lexing.common import OffsetMap
from apsla.taint.lite import TaintLiteEngine


def _run_java_taint(source: str):
    lexer = JavaLexer(source)
    tokens = lexer.tokenize()
    omap = OffsetMap(source)
    engine = TaintLiteEngine(source, tokens, JAVA_TAINT_PROFILE, omap)
    return engine.analyze()


def test_three_step_taint_path_sqli():
    """Verify that getParameter -> concatenation -> executeQuery gives a 3-step path."""
    source = """
    package com.example;
    import java.sql.Statement;
    import jakarta.servlet.http.HttpServletRequest;

    public class SqliTest {
        public void handle(HttpServletRequest request, Statement stmt) throws Exception {
            String user = request.getParameter("user");
            String query = "SELECT * FROM accounts WHERE user = '" + user + "'";
            stmt.executeQuery(query);
        }
    }
    """
    flows = _run_java_taint(source)
    assert len(flows) >= 1
    flow = flows[0]
    assert flow.rule_id == "APS-JV-INJ-002"

    # Must contain at least 3 steps: source -> propagate -> sink
    assert len(flow.path) >= 3
    assert flow.path[0].step.value == "source"
    assert flow.path[-1].step.value == "sink"
    steps = [s.step.value for s in flow.path]
    assert "propagate" in steps


def test_stringbuilder_propagation():
    """Verify taint propagation through StringBuilder append method chain."""
    source = """
    import java.sql.Statement;
    import jakarta.servlet.http.HttpServletRequest;

    public class StringBuilderTest {
        public void handle(HttpServletRequest req, Statement stmt) throws Exception {
            String name = req.getParameter("name");
            StringBuilder sb = new StringBuilder();
            sb.append("SELECT * FROM users WHERE name = '");
            sb.append(name);
            sb.append("'");
            stmt.execute(sb.toString());
        }
    }
    """
    flows = _run_java_taint(source)
    assert len(flows) >= 1
    assert flows[0].rule_id == "APS-JV-INJ-002"
    assert len(flows[0].path) >= 3


def test_sanitizer_integer_parse_int():
    """Verify that Integer.parseInt clears taint for SQL injection."""
    source = """
    import java.sql.Statement;
    import jakarta.servlet.http.HttpServletRequest;

    public class SafeSql {
        public void handle(HttpServletRequest req, Statement stmt) throws Exception {
            String rawId = req.getParameter("id");
            int safeId = Integer.parseInt(rawId);
            String sql = "SELECT * FROM users WHERE id = " + safeId;
            stmt.executeQuery(sql);
        }
    }
    """
    flows = _run_java_taint(source)
    # TaintLiteEngine does not flag flows where the variable was sanitized
    assert len(flows) == 0


def test_sanitizer_escape_html():
    """Verify that StringEscapeUtils.escapeHtml4 sanitizes XSS."""
    source = """
    import jakarta.servlet.http.HttpServletRequest;
    import jakarta.servlet.http.HttpServletResponse;
    import org.apache.commons.text.StringEscapeUtils;

    public class SafeXss {
        public void handle(HttpServletRequest req, HttpServletResponse res) throws Exception {
            String raw = req.getParameter("comment");
            String safe = StringEscapeUtils.escapeHtml4(raw);
            res.getWriter().println(safe);
        }
    }
    """
    flows = _run_java_taint(source)
    assert len(flows) == 0


def test_sanitizer_paths_normalize():
    """Verify that Paths.normalize sanitizes path traversal."""
    source = """
    import java.io.File;
    import java.nio.file.Paths;
    import jakarta.servlet.http.HttpServletRequest;

    public class SafePath {
        public void handle(HttpServletRequest req) {
            String filename = req.getParameter("file");
            String clean = Paths.normalize(filename);
            new File("/safe/dir/" + clean);
        }
    }
    """
    flows = _run_java_taint(source)
    assert len(flows) == 0


def test_scope_isolation():
    """Verify variable assignments inside inner block don't leak outside."""
    source = """
    import java.sql.Statement;
    import jakarta.servlet.http.HttpServletRequest;

    public class ScopeTest {
        public void handle(HttpServletRequest req, Statement stmt) throws Exception {
            String cleanQuery = "SELECT 1";
            {
                String tainted = req.getParameter("user");
                cleanQuery = "SELECT 2";
            }
            stmt.executeQuery(cleanQuery);
        }
    }
    """
    flows = _run_java_taint(source)
    assert len(flows) == 0
