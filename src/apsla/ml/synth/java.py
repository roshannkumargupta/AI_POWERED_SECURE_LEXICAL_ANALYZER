"""Deterministic generator of labelled Java synthetic snippets from varied templates."""

from __future__ import annotations

import random
from typing import Final

from apsla.languages.java_lang.lexer import JavaLexer
from apsla.ml.synth.common import (
    LABEL_MALICIOUS,
    LABEL_SAFE,
    LABEL_SUSPICIOUS,
    SyntheticSnippet,
)

# ── Vocabulary Pools for Variation ────────────────────────────────────────────

VARS: Final[list[str]] = [
    "userInput",
    "cmdParam",
    "queryStr",
    "rawPayload",
    "reqData",
    "fileName",
    "targetPath",
    "itemId",
    "authToken",
    "rawArg",
    "userId",
    "hostIp",
    "categoryName",
    "secretKey",
    "searchQuery",
    "remoteEndpoint",
    "cacheKey",
    "sessionToken",
]

SAFE_VARS: Final[list[str]] = [
    "itemCount",
    "totalSum",
    "loopIndex",
    "activeItem",
    "queryResult",
    "userRecords",
    "metricValue",
    "appConfig",
    "logger",
    "respStatus",
    "httpResponse",
    "requestOptions",
    "retryCount",
]

COMMENTS: Final[list[str]] = [
    "// Process client request data safely",
    "// Handle incoming parameter from HTTP servlet",
    "// Query database for matching entity records",
    "// Validate input format and authorization tokens",
    "// Internal audit log for enterprise monitoring",
    "// Service layer business logic execution",
    "// High-performance caching layer resolution",
    "// Microservice boundary dispatch routine",
]

DISTRACTORS_PRE: Final[list[str]] = [
    (
        "package com.example.service;\n\n"
        "import java.io.*;\n"
        "import java.util.*;\n"
        "import java.util.logging.Logger;\n\n"
        "public class DataProcessor {\n"
        "    private static final Logger log = Logger.getLogger(DataProcessor.class.getName());\n"
    ),
    (
        "package com.enterprise.security;\n\n"
        "import java.nio.file.*;\n"
        "import java.security.*;\n"
        "import java.sql.*;\n\n"
        "public class SecurityManagerService {\n"
    ),
    (
        "package org.securelex.controller;\n\n"
        "import java.net.*;\n"
        "import javax.servlet.http.*;\n"
        "import java.util.concurrent.ConcurrentHashMap;\n\n"
        "public class GatewayHandler {\n"
    ),
    (
        "package com.bank.payment;\n\n"
        "import javax.crypto.*;\n"
        "import java.math.BigDecimal;\n"
        "import java.util.stream.Collectors;\n\n"
        "public class TransactionEngine {\n"
    ),
]

DISTRACTORS_SAFE_BODY: Final[list[str]] = [
    (
        "    public static String computeChecksum(String input) throws Exception {\n"
        '        MessageDigest md = MessageDigest.getInstance("SHA-256");\n'
        "        byte[] digest = md.digest(input.getBytes());\n"
        "        return HexFormat.of().formatHex(digest);\n"
        "    }\n"
    ),
    (
        "    public static String sanitizeString(String raw) {\n"
        '        if (raw == null) return "";\n'
        '        return raw.replaceAll("[^a-zA-Z0-9_-]", "");\n'
        "    }\n"
    ),
    (
        "    public static int calculateTotal(List<Integer> values) {\n"
        "        return values.stream().mapToInt(Integer::intValue).sum();\n"
        "    }\n"
    ),
]


# ── Template Builders ─────────────────────────────────────────────────────────


def _generate_snippet(
    snippet_id: str,
    family: str,
    pre: str,
    core_lines: list[tuple[str, int]],  # (code_line, label_int)
    post: str = "}\n",
) -> SyntheticSnippet:
    """Combines segments, tokenizes via JavaLexer, and labels tokens based on template spans."""
    full_code = pre + "\n" + "\n".join(line for line, _ in core_lines) + "\n" + post
    tokens = JavaLexer(full_code).tokenize()

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
        language="java",
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
            (
                "    public void runDiagnostic(HttpServletRequest req) throws Exception {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            (f'        String {v} = req.getParameter("host");', LABEL_SUSPICIOUS),
            (f'        Runtime.getRuntime().exec("ping -c 1 " + {v});', LABEL_MALICIOUS),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("    public void executeScript(String rawInput) throws Exception {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            (f'        String {v} = rawInput != null ? rawInput : "";', LABEL_SUSPICIOUS),
            (f'        ProcessBuilder pb = new ProcessBuilder("sh", "-c", {v});', LABEL_MALICIOUS),
            ("        pb.start();", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            (
                "    public void backupDatabase(HttpServletRequest req) throws Exception {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            (f'        String {v} = req.getHeader("X-Target-Table");', LABEL_SUSPICIOUS),
            (
                f'        Runtime.getRuntime().exec(new String[]{{"/bin/sh", "-c", "mysqldump " + {v}}});',
                LABEL_MALICIOUS,
            ),
            ("    }", LABEL_SAFE),
        ]
    else:
        lines = [
            ("    public void convertDoc(String fileName) throws Exception {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            (f'        String {v} = System.getenv("CLI_TOOL") + " " + fileName;', LABEL_SUSPICIOUS),
            (f"        Runtime.getRuntime().exec({v});", LABEL_MALICIOUS),
            ("    }", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "cmd_injection", pre, lines)


def _build_sql_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 3)

    if variant == 0:
        lines = [
            (
                "    public ResultSet findUser(Connection conn, String query) throws SQLException {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            (
                f'        String {v} = "SELECT * FROM users WHERE username = \'" + query + "\'";',
                LABEL_SUSPICIOUS,
            ),
            ("        Statement stmt = conn.createStatement();", LABEL_SAFE),
            (f"        return stmt.executeQuery({v});", LABEL_MALICIOUS),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            (
                "    public int deleteOrder(Statement statement, String orderId) throws SQLException {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            ('        String sql = "DELETE FROM orders WHERE id = " + orderId;', LABEL_SUSPICIOUS),
            ("        return statement.executeUpdate(sql);", LABEL_MALICIOUS),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            (
                "    public List<Object> searchCatalog(Statement stmt, HttpServletRequest req) throws SQLException {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            (f'        String {v} = req.getParameter("category");', LABEL_SUSPICIOUS),
            (
                f'        stmt.execute("SELECT * FROM items WHERE category = \'" + {v} + "\' ORDER BY price");',
                LABEL_MALICIOUS,
            ),
            ("        return new ArrayList<>();", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    else:
        lines = [
            (
                "    public void batchUpdate(Connection conn, String[] ids) throws SQLException {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            ("        Statement st = conn.createStatement();", LABEL_SAFE),
            ("        for (String id : ids) {", LABEL_SAFE),
            (
                '            st.addBatch("UPDATE inventory SET stock = 0 WHERE item_id = \'" + id + "\'");',
                LABEL_MALICIOUS,
            ),
            ("        }", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "sql_injection", pre, lines)


def _build_path_traversal(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            (
                "    public byte[] downloadFile(HttpServletRequest req) throws IOException {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            (f'        String {v} = req.getParameter("path");', LABEL_SUSPICIOUS),
            (f'        File target = new File("/var/app/data/" + {v});', LABEL_MALICIOUS),
            ("        return Files.readAllBytes(target.toPath());", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            (
                "    public FileInputStream openAttachment(String fileName) throws FileNotFoundException {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            ('        String fullPath = "/mnt/storage/" + fileName;', LABEL_SUSPICIOUS),
            ("        return new FileInputStream(fullPath);", LABEL_MALICIOUS),
            ("    }", LABEL_SAFE),
        ]
    else:
        lines = [
            (
                "    public void writeReport(String reportName, String data) throws IOException {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            ('        Path path = Paths.get("/opt/reports/" + reportName);', LABEL_MALICIOUS),
            ("        Files.writeString(path, data);", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "path_traversal", pre, lines)


def _build_unsafe_deserialization(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    lines = [
        ("    public Object deserializeSession(byte[] rawBytes) throws Exception {", LABEL_SAFE),
        (f"        {c}", LABEL_SAFE),
        ("        ByteArrayInputStream bais = new ByteArrayInputStream(rawBytes);", LABEL_SAFE),
        ("        ObjectInputStream ois = new ObjectInputStream(bais);", LABEL_SUSPICIOUS),
        (f"        Object {v} = ois.readObject();", LABEL_MALICIOUS),
        ("        ois.close();", LABEL_SAFE),
        (f"        return {v};", LABEL_SAFE),
        ("    }", LABEL_SAFE),
    ]
    return _generate_snippet(sid, "unsafe_deserialization", pre, lines)


def _build_weak_crypto(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 3)

    if variant == 0:
        lines = [
            ("    public byte[] hashPassword(String password) throws Exception {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            ('        MessageDigest md = MessageDigest.getInstance("MD5");', LABEL_MALICIOUS),
            ("        return md.digest(password.getBytes());", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("    public byte[] generateFingerprint(byte[] data) throws Exception {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            ('        MessageDigest md = MessageDigest.getInstance("SHA-1");', LABEL_MALICIOUS),
            ("        return md.digest(data);", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("    public Cipher createCipher(SecretKey key) throws Exception {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            (
                '        Cipher cipher = Cipher.getInstance("DES/ECB/PKCS5Padding");',
                LABEL_MALICIOUS,
            ),
            ("        cipher.init(Cipher.ENCRYPT_MODE, key);", LABEL_SAFE),
            ("        return cipher;", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    else:
        lines = [
            ("    public Cipher initAesEcb(SecretKey key) throws Exception {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            ('        Cipher c = Cipher.getInstance("AES/ECB/NoPadding");', LABEL_MALICIOUS),
            ("        c.init(Cipher.DECRYPT_MODE, key);", LABEL_SAFE),
            ("        return c;", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "weak_crypto", pre, lines)


def _build_hardcoded_secrets(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 3)

    if variant == 0:
        lines = [
            ("    // AWS credentials hardcoded in production bean", LABEL_SAFE),
            (
                '    private static final String AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE";',
                LABEL_MALICIOUS,
            ),
            (
                '    private static final String AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";',
                LABEL_MALICIOUS,
            ),
            ('    public String getRegion() { return "us-east-1"; }', LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("    // Database administrator password credentials", LABEL_SAFE),
            (
                '    public static final String DB_PASSWORD = "SuperSecretP@ssw0rd2026!";',
                LABEL_MALICIOUS,
            ),
            ('    public static final String DB_USER = "sa_admin";', LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("    // Stripe production API secret key", LABEL_SAFE),
            (
                '    private String stripeSecret = "sk_live_51M00000000000000000000000000000000000000";',
                LABEL_MALICIOUS,
            ),
            ('    public void init() { System.out.println("Stripe ready"); }', LABEL_SAFE),
        ]
    else:
        lines = [
            ("    // Private token for signing JWT sessions", LABEL_SAFE),
            (
                '    protected final String jwtSigningKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9";',
                LABEL_MALICIOUS,
            ),
            ("    public int getTimeout() { return 3600; }", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "hardcoded_secrets", pre, lines)


def _build_xxe_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    lines = [
        (
            f"    public org.w3c.dom.Document parseXml(InputStream {v}) throws Exception {{",
            LABEL_SAFE,
        ),
        (f"        {c}", LABEL_SAFE),
        (
            "        javax.xml.parsers.DocumentBuilderFactory dbf = javax.xml.parsers.DocumentBuilderFactory.newInstance();",
            LABEL_SUSPICIOUS,
        ),
        ("        javax.xml.parsers.DocumentBuilder db = dbf.newDocumentBuilder();", LABEL_SAFE),
        (f"        return db.parse({v});", LABEL_MALICIOUS),
        ("    }", LABEL_SAFE),
    ]
    return _generate_snippet(sid, "xxe_injection", pre, lines)


def _build_ssrf_networking(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 1)

    if variant == 0:
        lines = [
            (
                "    public String fetchRemoteData(HttpServletRequest req) throws IOException {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            (f'        String {v} = req.getParameter("targetUrl");', LABEL_SUSPICIOUS),
            (f"        URL url = new URL({v});", LABEL_SUSPICIOUS),
            ("        InputStream stream = url.openStream();", LABEL_MALICIOUS),
            ("        return new String(stream.readAllBytes());", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    else:
        lines = [
            ("    public void sendWebhook(String endpoint) throws Exception {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            (
                "        HttpURLConnection conn = (HttpURLConnection) new URL(endpoint).openConnection();",
                LABEL_MALICIOUS,
            ),
            ('        conn.setRequestMethod("POST");', LABEL_SAFE),
            ("        conn.getResponseCode();", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "ssrf_networking", pre, lines)


def _build_suspicious_patterns(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            (
                "    public Object loadDynamicPlugin(String className) throws Exception {",
                LABEL_SAFE,
            ),
            (f"        {c}", LABEL_SAFE),
            ("        Class<?> clazz = Class.forName(className);", LABEL_SUSPICIOUS),
            ("        return clazz.getDeclaredConstructor().newInstance();", LABEL_SUSPICIOUS),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("    public void loadNativeHelper(String libName) {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            ("        System.loadLibrary(libName);", LABEL_SUSPICIOUS),
            ("    }", LABEL_SAFE),
        ]
    else:
        lines = [
            ("    public int generateToken() {", LABEL_SAFE),
            (f"        {c}", LABEL_SAFE),
            ("        Random rand = new Random();", LABEL_SUSPICIOUS),
            ("        return rand.nextInt(1000000);", LABEL_SUSPICIOUS),
            ("    }", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "suspicious_patterns", pre, lines)


def _build_safe_patterns(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    body = rng.choice(DISTRACTORS_SAFE_BODY)
    variant = rng.randint(0, 4)

    if variant == 0:
        lines = [
            (
                "    public User findUserById(Connection conn, long id) throws SQLException {",
                LABEL_SAFE,
            ),
            ('        String sql = "SELECT id, name, email FROM users WHERE id = ?";', LABEL_SAFE),
            ("        try (PreparedStatement ps = conn.prepareStatement(sql)) {", LABEL_SAFE),
            ("            ps.setLong(1, id);", LABEL_SAFE),
            ("            try (ResultSet rs = ps.executeQuery()) {", LABEL_SAFE),
            (
                '                if (rs.next()) return new User(rs.getLong("id"), rs.getString("name"));',
                LABEL_SAFE,
            ),
            ("            }", LABEL_SAFE),
            ("        }", LABEL_SAFE),
            ("        return null;", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("    public byte[] readSafeDocument(String docId) throws IOException {", LABEL_SAFE),
            ("        String cleanId = sanitizeString(docId);", LABEL_SAFE),
            (
                '        Path targetPath = Paths.get("/var/safe/docs", cleanId).normalize();',
                LABEL_SAFE,
            ),
            (
                '        if (!targetPath.startsWith("/var/safe/docs")) throw new SecurityException("Invalid path");',
                LABEL_SAFE,
            ),
            ("        return Files.readAllBytes(targetPath);", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("    public String generateSecureSessionToken() {", LABEL_SAFE),
            ("        byte[] randomBytes = new byte[32];", LABEL_SAFE),
            ("        new SecureRandom().nextBytes(randomBytes);", LABEL_SAFE),
            (
                "        return Base64.getUrlEncoder().withoutPadding().encodeToString(randomBytes);",
                LABEL_SAFE,
            ),
            ("    }", LABEL_SAFE),
        ]
    elif variant == 3:
        lines = [
            ("    public void runCommandSafely(String argument) throws Exception {", LABEL_SAFE),
            (
                '        List<String> cmd = Arrays.asList("/usr/bin/ls", "-l", "--", argument);',
                LABEL_SAFE,
            ),
            ("        ProcessBuilder pb = new ProcessBuilder(cmd);", LABEL_SAFE),
            ("        Process p = pb.start();", LABEL_SAFE),
            ("        p.waitFor();", LABEL_SAFE),
            ("    }", LABEL_SAFE),
        ]
    else:
        lines = [
            ("    public int countActiveSessions(Map<String, Long> activeMap) {", LABEL_SAFE),
            ("        long threshold = System.currentTimeMillis() - 3600000;", LABEL_SAFE),
            (
                "        return (int) activeMap.values().stream().filter(t -> t > threshold).count();",
                LABEL_SAFE,
            ),
            ("    }", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "safe_patterns", pre + body, lines)


# ── Public Generator ──────────────────────────────────────────────────────────


def generate_java_dataset(
    count: int = 3000,
    seed: int = 42,
) -> list[SyntheticSnippet]:
    """Generates at least `count` deterministic, leak-free labeled Java snippets.

    Args:
        count: Minimum number of snippets to synthesize (default: 3000).
        seed: Random seed for reproducibility (default: 42).

    Returns:
        List of SyntheticSnippet instances with ground truth per-token labels.
    """
    rng = random.Random(seed)
    families = [
        ("cmd_injection", _build_cmd_injection, 0.10),
        ("sql_injection", _build_sql_injection, 0.10),
        ("path_traversal", _build_path_traversal, 0.09),
        ("unsafe_deserialization", _build_unsafe_deserialization, 0.08),
        ("weak_crypto", _build_weak_crypto, 0.08),
        ("hardcoded_secrets", _build_hardcoded_secrets, 0.08),
        ("xxe_injection", _build_xxe_injection, 0.07),
        ("ssrf_networking", _build_ssrf_networking, 0.07),
        ("suspicious_patterns", _build_suspicious_patterns, 0.08),
        ("safe_patterns", _build_safe_patterns, 0.25),
    ]

    builders = [f[1] for f in families]
    weights = [f[2] for f in families]

    snippets: list[SyntheticSnippet] = []
    for i in range(count):
        sid = f"synth-java-{i:05d}"
        chosen_builder = rng.choices(builders, weights=weights, k=1)[0]
        snippet = chosen_builder(rng, sid)
        snippets.append(snippet)

    return snippets
