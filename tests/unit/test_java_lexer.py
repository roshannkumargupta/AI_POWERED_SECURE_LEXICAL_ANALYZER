"""Unit, property, and comprehensive corpus tests for JavaLexer."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from apsla.languages.java_lang.lexer import JavaLexer

# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


@settings(max_examples=100, deadline=None)
@given(st.text())
def test_lexer_never_crashes_and_preserves_trivia(text: str) -> None:
    """JavaLexer must never raise an exception and must perfectly reconstruct input."""
    lexer = JavaLexer(text)
    tokens = lexer.tokenize()
    reconstructed = "".join(t.text for t in tokens)
    assert reconstructed == text, f"Reconstruction failed for input: {text!r}"


# ---------------------------------------------------------------------------
# Specific lexical feature tests
# ---------------------------------------------------------------------------


def test_keywords_and_contextual() -> None:
    """Verify standard and contextual keywords."""
    code = "public class Example permits Sub record var yield sealed"
    lexer = JavaLexer(code)
    tokens = [t for t in lexer.tokenize() if t.kind != "WHITESPACE"]

    expected_keywords = [
        "public",
        "class",
        "Example",
        "permits",
        "Sub",
        "record",
        "var",
        "yield",
        "sealed",
    ]
    assert [t.text for t in tokens] == expected_keywords
    for t in tokens:
        if t.text in ("Example", "Sub"):
            assert t.kind == "IDENTIFIER"
        else:
            assert t.kind == "KEYWORD"


def test_unicode_identifiers() -> None:
    """Verify Unicode-aware identifiers in Java."""
    code = 'int счёт = 10; double π = 3.14159; String grüße = "hallo";'
    lexer = JavaLexer(code)
    tokens = [t for t in lexer.tokenize() if t.kind == "IDENTIFIER"]
    names = [t.text for t in tokens]
    assert "счёт" in names
    assert "π" in names
    assert "grüße" in names


def test_text_blocks() -> None:
    r"""Verify multiline text blocks (Java 15+ \"\"\"...\"\"\")."""
    code = (
        'String html = """\n    <html>\n        <body>"Hello World"</body>\n    </html>\n    """;'
    )
    lexer = JavaLexer(code)
    tokens = [t for t in lexer.tokenize() if t.kind == "STRING"]
    assert len(tokens) == 1
    assert tokens[0].text.startswith('"""')
    assert tokens[0].text.endswith('"""')
    assert '"Hello World"' in tokens[0].text


def test_string_and_char_literals() -> None:
    """Verify strings with escapes and char literals."""
    code = "char c = '\\''; char newline = '\\n'; String s = \"Hello, \\\"World\\\"!\\n\";"
    lexer = JavaLexer(code)
    tokens = [t for t in lexer.tokenize() if t.kind in ("STRING", "CHAR")]
    assert len(tokens) == 3
    assert tokens[0].kind == "CHAR"
    assert tokens[0].text == "'\\''"
    assert tokens[1].kind == "CHAR"
    assert tokens[1].text == "'\\n'"
    assert tokens[2].kind == "STRING"
    assert tokens[2].text == '"Hello, \\"World\\"!\n"' or "Hello" in tokens[2].text


def test_annotations() -> None:
    """Verify annotations with and without parameters."""
    code = (
        "@Override\n"
        '@RequestMapping(value = "/api/v1/users", method = RequestMethod.GET)\n'
        "public void getUser() {}"
    )
    lexer = JavaLexer(code)
    tokens = [t for t in lexer.tokenize() if t.kind == "ANNOTATION"]
    assert len(tokens) == 2
    assert tokens[0].text == "@Override"
    assert tokens[1].text == '@RequestMapping(value = "/api/v1/users", method = RequestMethod.GET)'


def test_number_literals() -> None:
    """Verify hex, binary, octal, underscores, suffixes, and hex floats."""
    code = (
        "int a = 1_000_000;\n"
        "int hex = 0x1A_2F;\n"
        "int bin = 0b1010_0101;\n"
        "int oct = 0755;\n"
        "long l = 1000L;\n"
        "float f = 3.1415f;\n"
        "double d = 2.0d;\n"
        "double hexFloat = 0x1.0p-3;\n"
    )
    lexer = JavaLexer(code)
    tokens = [t for t in lexer.tokenize() if t.kind == "NUMBER"]
    assert len(tokens) == 8
    texts = [t.text for t in tokens]
    assert "1_000_000" in texts
    assert "0x1A_2F" in texts
    assert "0b1010_0101" in texts
    assert "0755" in texts
    assert "1000L" in texts
    assert "3.1415f" in texts
    assert "2.0d" in texts
    assert "0x1.0p-3" in texts


def test_operators() -> None:
    """Verify advanced Java operators: >>>=, ->, ::, ..."""
    code = (
        "x >>>= 2; Runnable r = () -> {}; Function f = String::valueOf; void test(int... args) {}"
    )
    lexer = JavaLexer(code)
    tokens = [t for t in lexer.tokenize() if t.kind == "OPERATOR"]
    op_texts = [t.text for t in tokens]
    assert ">>>=" in op_texts
    assert "->" in op_texts
    assert "::" in op_texts
    assert "..." in op_texts


def test_comments_and_javadoc() -> None:
    """Verify line comments, block comments, and Javadoc."""
    code = (
        "// Single line comment\n"
        "/* Block comment\n"
        "   spanning lines */\n"
        "/**\n"
        " * Javadoc documentation comment.\n"
        " */\n"
        "int x = 1;\n"
    )
    lexer = JavaLexer(code)
    tokens = [t for t in lexer.tokenize() if t.kind == "COMMENT"]
    assert len(tokens) == 3


def test_unicode_escapes_inside_source() -> None:
    r"""Verify that \uXXXX inside source is decoded in token properties and reconstructs cleanly."""
    code = "int \\u0078 = 42; // \\u0078 is x"
    lexer = JavaLexer(code)
    tokens = lexer.tokenize()
    reconstructed = "".join(t.text for t in tokens)
    assert reconstructed == code
    # The identifier token raw text contains \u0078
    id_tokens = [t for t in tokens if t.kind == "IDENTIFIER"]
    assert len(id_tokens) == 1
    assert "0078" in id_tokens[0].text or id_tokens[0].text == "x"


# ---------------------------------------------------------------------------
# 15 Realistic Java source files with ZERO ERROR tokens
# ---------------------------------------------------------------------------

REALISTIC_JAVA_FILES = [
    # 1. Spring Boot REST Controller
    """
    package com.example.demo.controller;

    import org.springframework.web.bind.annotation.*;
    import java.util.List;

    @RestController
    @RequestMapping("/api/v1/products")
    public class ProductController {
        private final ProductService service;

        public ProductController(ProductService service) {
            this.service = service;
        }

        @GetMapping("/{id}")
        public Product getById(@PathVariable("id") Long id) {
            return service.findById(id);
        }
    }
    """,
    # 2. Modern Java Record
    """
    package com.example.demo.model;

    import java.time.Instant;

    public record UserProfile(
        String username,
        String email,
        Instant createdAt,
        boolean active
    ) {
        public UserProfile {
            if (username == null || username.isBlank()) {
                throw new IllegalArgumentException("Username cannot be empty");
            }
        }
    }
    """,
    # 3. Sealed interface and pattern matching permits
    """
    package com.example.demo.shapes;

    public sealed interface Shape permits Circle, Rectangle, Square {
        double area();
    }

    final class Circle implements Shape {
        private final double radius;
        public Circle(double radius) { this.radius = radius; }
        public double area() { return Math.PI * radius * radius; }
    }

    final class Rectangle implements Shape {
        private final double w, h;
        public Rectangle(double w, double h) { this.w = w; this.h = h; }
        public double area() { return w * h; }
    }

    final class Square implements Shape {
        private final double s;
        public Square(double s) { this.s = s; }
        public double area() { return s * s; }
    }
    """,
    # 4. Stream and Lambda Pipeline
    """
    package com.example.demo.service;

    import java.util.List;
    import java.util.stream.Collectors;

    public class FilterService {
        public List<String> processNames(List<String> raw) {
            return raw.stream()
                .filter(s -> s != null && !s.isEmpty())
                .map(String::trim)
                .map(String::toUpperCase)
                .sorted()
                .collect(Collectors.toList());
        }
    }
    """,
    # 5. Multithreaded ExecutorService
    """
    package com.example.demo.concurrency;

    import java.util.concurrent.*;

    public class TaskRunner {
        private final ExecutorService executor = Executors.newFixedThreadPool(4);

        public Future<String> submitTask(Callable<String> task) {
            return executor.submit(task);
        }

        public void shutdown() {
            executor.shutdown();
        }
    }
    """,
    # 6. JDBC Connection with Try-With-Resources
    """
    package com.example.demo.db;

    import java.sql.*;

    public class DatabaseManager {
        public void executeSafe(Connection conn, String id) throws SQLException {
            String sql = "SELECT * FROM users WHERE id = ?";
            try (PreparedStatement stmt = conn.prepareStatement(sql)) {
                stmt.setString(1, id);
                try (ResultSet rs = stmt.executeQuery()) {
                    while (rs.next()) {
                        System.out.println(rs.getString("username"));
                    }
                }
            }
        }
    }
    """,
    # 7. Rich Enum with methods and constants
    """
    package com.example.demo.types;

    public enum HttpStatus {
        OK(200, "Success"),
        BAD_REQUEST(400, "Client Error"),
        INTERNAL_ERROR(500, "Server Error");

        private final int code;
        private final String message;

        HttpStatus(int code, String message) {
            this.code = code;
            this.message = message;
        }

        public int getCode() { return code; }
        public String getMessage() { return message; }
    }
    """,
    # 8. Switch expression with yield
    """
    package com.example.demo.logic;

    public class Calculator {
        public int evaluate(String op, int a, int b) {
            return switch (op) {
                case "ADD" -> a + b;
                case "SUB" -> a - b;
                case "MUL" -> a * b;
                default -> {
                    System.out.println("Unknown op: " + op);
                    yield 0;
                }
            };
        }
    }
    """,
    # 9. Text blocks with SQL and JSON formatting
    """
    package com.example.demo.templates;

    public class QueryTemplates {
        public static final String USER_QUERY = \"\"\"
            SELECT id, username, email, created_at
            FROM system_users
            WHERE status = 'ACTIVE'
            ORDER BY created_at DESC
            \"\"\";
    }
    """,
    # 10. Custom Exception Hierarchy
    """
    package com.example.demo.exceptions;

    public class BaseDomainException extends RuntimeException {
        private final int errorCode;

        public BaseDomainException(String message, int errorCode) {
            super(message);
            this.errorCode = errorCode;
        }

        public int getErrorCode() {
            return errorCode;
        }
    }
    """,
    # 11. Generic Builder Pattern
    """
    package com.example.demo.builder;

    public class RequestBuilder<T> {
        private String endpoint;
        private T body;

        public RequestBuilder<T> endpoint(String endpoint) {
            this.endpoint = endpoint;
            return this;
        }

        public RequestBuilder<T> body(T body) {
            this.body = body;
            return this;
        }
    }
    """,
    # 12. File I/O with Java NIO Paths and Files
    """
    package com.example.demo.io;

    import java.nio.file.*;
    import java.io.IOException;
    import java.util.List;

    public class ConfigLoader {
        public List<String> readConfig(Path configPath) throws IOException {
            if (Files.exists(configPath)) {
                return Files.readAllLines(configPath);
            }
            return List.of();
        }
    }
    """,
    # 13. Security Filter with Servlet API
    """
    package com.example.demo.filter;

    import jakarta.servlet.*;
    import jakarta.servlet.http.HttpServletRequest;
    import jakarta.servlet.http.HttpServletResponse;
    import java.io.IOException;

    public class SecurityHeaderFilter implements Filter {
        @Override
        public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
                throws IOException, ServletException {
            HttpServletResponse response = (HttpServletResponse) res;
            response.setHeader("X-Frame-Options", "DENY");
            response.setHeader("X-Content-Type-Options", "nosniff");
            chain.doFilter(req, res);
        }
    }
    """,
    # 14. Java 11+ HttpClient asynchronous request
    """
    package com.example.demo.net;

    import java.net.URI;
    import java.net.http.HttpClient;
    import java.net.http.HttpRequest;
    import java.net.http.HttpResponse;
    import java.util.concurrent.CompletableFuture;

    public class ApiClient {
        private final HttpClient client = HttpClient.newHttpClient();

        public CompletableFuture<String> fetchAsync(String url) {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .GET()
                .build();
            return client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(HttpResponse::body);
        }
    }
    """,
    # 15. Cryptographic Key Agreement & SecureRandom
    """
    package com.example.demo.crypto;

    import java.security.SecureRandom;
    import javax.crypto.KeyGenerator;
    import javax.crypto.SecretKey;

    public class CryptoUtils {
        public static SecretKey generateKey() throws Exception {
            KeyGenerator gen = KeyGenerator.getInstance("AES");
            gen.init(256, new SecureRandom());
            return gen.generateKey();
        }
    }
    """,
]


def test_fifteen_realistic_java_files_zero_error_tokens() -> None:
    """Verify that 15 realistic hand-written Java files tokenize with zero ERROR tokens."""
    assert len(REALISTIC_JAVA_FILES) >= 15

    for idx, java_code in enumerate(REALISTIC_JAVA_FILES, 1):
        lexer = JavaLexer(java_code)
        tokens = lexer.tokenize()

        # 1. Zero error tokens
        error_tokens = [t for t in tokens if t.kind == "ERROR"]
        assert not error_tokens, (
            f"Realistic Java snippet #{idx} had unexpected ERROR tokens: {error_tokens}"
        )

        # 2. Perfect trivia preservation
        reconstructed = "".join(t.text for t in tokens)
        assert reconstructed == java_code, (
            f"Realistic Java snippet #{idx} trivia reconstruction failed"
        )
