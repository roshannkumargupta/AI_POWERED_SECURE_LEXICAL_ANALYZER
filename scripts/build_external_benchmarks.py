"""Builder script to populate realistic external benchmark datasets for Java, JavaScript, and C++."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_DIR = ROOT / "data" / "external"


def build_java_benchmarks() -> None:
    target_dir = EXTERNAL_DIR / "java"
    target_dir.mkdir(parents=True, exist_ok=True)

    benchmarks: dict[str, dict[str, str]] = {
        "ext_01_user_report_servlet.java": {
            "label": "MALICIOUS",
            "note": "File opened directly with user parameter without path canonicalization",
            "code": (
                "package com.app.servlet;\n\n"
                "import java.io.*;\n"
                "import javax.servlet.http.*;\n\n"
                "public class ReportServlet extends HttpServlet {\n"
                "    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {\n"
                '        String fileName = req.getParameter("report");\n'
                '        File reportFile = new File("/var/reports/" + fileName);\n'
                "        try (FileInputStream fis = new FileInputStream(reportFile)) {\n"
                "            fis.transferTo(resp.getOutputStream());\n"
                "        }\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_02_safe_path_resolve.java": {
            "label": "SAFE",
            "note": "Path traversal prevented using normalize and startsWith verification",
            "code": (
                "package com.app.util;\n\n"
                "import java.nio.file.*;\n\n"
                "public class SafePathResolver {\n"
                "    public static Path resolveSafe(String baseDir, String userPath) {\n"
                "        Path base = Paths.get(baseDir).toAbsolutePath().normalize();\n"
                "        Path target = base.resolve(userPath).normalize();\n"
                "        if (!target.startsWith(base)) {\n"
                '            throw new SecurityException("Access denied: Path traversal detected");\n'
                "        }\n"
                "        return target;\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_03_payment_gateway_md5.java": {
            "label": "MALICIOUS",
            "note": "MD5 weak cryptographic hash used for payment verification signature",
            "code": (
                "package com.bank.crypto;\n\n"
                "import java.security.MessageDigest;\n\n"
                "public class PaymentSigner {\n"
                "    public static byte[] computePaymentSignature(String txData) throws Exception {\n"
                '        MessageDigest md = MessageDigest.getInstance("MD5");\n'
                "        return md.digest(txData.getBytes());\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_04_token_generator_secure_random.java": {
            "label": "SAFE",
            "note": "SecureRandom and Base64 url encoding for session token generation",
            "code": (
                "package com.bank.security;\n\n"
                "import java.security.SecureRandom;\n"
                "import java.util.Base64;\n\n"
                "public class SecureTokenGenerator {\n"
                "    private static final SecureRandom rng = new SecureRandom();\n\n"
                "    public static String generateSessionToken() {\n"
                "        byte[] buf = new byte[32];\n"
                "        rng.nextBytes(buf);\n"
                "        return Base64.getUrlEncoder().withoutPadding().encodeToString(buf);\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_05_backup_db_runtime_exec.java": {
            "label": "MALICIOUS",
            "note": "Runtime.getRuntime().exec command injection via concatenated table name",
            "code": (
                "package com.app.admin;\n\n"
                "public class DatabaseBackup {\n"
                "    public void exportTable(String tableName) throws Exception {\n"
                '        String cmd = "mysqldump -u root -psecret mydb " + tableName;\n'
                "        Runtime.getRuntime().exec(cmd);\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_06_docker_process_builder.java": {
            "label": "SAFE",
            "note": "ProcessBuilder with safe explicit argument array",
            "code": (
                "package com.app.ops;\n\n"
                "import java.util.*;\n\n"
                "public class ContainerManager {\n"
                "    public static Process listContainers() throws Exception {\n"
                '        List<String> args = Arrays.asList("docker", "ps", "--format", "json");\n'
                "        return new ProcessBuilder(args).start();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_07_hibernate_sqli_search.java": {
            "label": "MALICIOUS",
            "note": "Hibernate HQL string concatenation leading to SQL injection",
            "code": (
                "package com.app.dao;\n\n"
                "import javax.persistence.EntityManager;\n\n"
                "public class UserDao {\n"
                "    public Object findByUsername(EntityManager em, String username) {\n"
                '        String hql = "FROM User WHERE username = \'" + username + "\'";\n'
                "        return em.createQuery(hql).getSingleResult();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_08_prepared_statement_user.java": {
            "label": "SAFE",
            "note": "Parameterized JDBC query preventing SQL injection",
            "code": (
                "package com.app.dao;\n\n"
                "import java.sql.*;\n\n"
                "public class SafeUserDao {\n"
                "    public ResultSet getUser(Connection conn, long userId) throws SQLException {\n"
                '        String sql = "SELECT id, email FROM users WHERE id = ?";\n'
                "        PreparedStatement ps = conn.prepareStatement(sql);\n"
                "        ps.setLong(1, userId);\n"
                "        return ps.executeQuery();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_09_session_deserialize_ois.java": {
            "label": "MALICIOUS",
            "note": "Unsafe ObjectInputStream readObject on arbitrary incoming stream",
            "code": (
                "package com.app.auth;\n\n"
                "import java.io.*;\n\n"
                "public class SessionDeserializer {\n"
                "    public static Object loadSession(InputStream in) throws Exception {\n"
                "        ObjectInputStream ois = new ObjectInputStream(in);\n"
                "        return ois.readObject();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_10_json_jackson_deserialize.java": {
            "label": "SAFE",
            "note": "Safe Jackson JSON parsing with strict DTO typing",
            "code": (
                "package com.app.auth;\n\n"
                "import com.fasterxml.jackson.databind.ObjectMapper;\n\n"
                "public class SafeSessionLoader {\n"
                "    private static final ObjectMapper mapper = new ObjectMapper();\n\n"
                "    public static UserProfile parseProfile(String json) throws Exception {\n"
                "        return mapper.readValue(json, UserProfile.class);\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_11_xxe_document_builder.java": {
            "label": "MALICIOUS",
            "note": "XML DocumentBuilderFactory vulnerable to XXE external entity resolution",
            "code": (
                "package com.app.xml;\n\n"
                "import java.io.InputStream;\n"
                "import javax.xml.parsers.DocumentBuilderFactory;\n\n"
                "public class XmlParserService {\n"
                "    public void parseFeed(InputStream stream) throws Exception {\n"
                "        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();\n"
                "        dbf.newDocumentBuilder().parse(stream);\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_12_safe_xxe_configured.java": {
            "label": "SAFE",
            "note": "DocumentBuilderFactory hardened with disallow-doctype-decl feature",
            "code": (
                "package com.app.xml;\n\n"
                "import javax.xml.parsers.DocumentBuilderFactory;\n\n"
                "public class SafeXmlParser {\n"
                "    public static DocumentBuilderFactory createSecureFactory() throws Exception {\n"
                "        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();\n"
                '        dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);\n'
                "        return dbf;\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_13_ssrf_url_openstream.java": {
            "label": "MALICIOUS",
            "note": "Direct URL openStream on user-controlled endpoint parameter (SSRF)",
            "code": (
                "package com.app.net;\n\n"
                "import java.io.InputStream;\n"
                "import java.net.URL;\n\n"
                "public class WebhookFetcher {\n"
                "    public InputStream fetchHook(String remoteUrl) throws Exception {\n"
                "        URL url = new URL(remoteUrl);\n"
                "        return url.openStream();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_14_safe_http_client_allowed_hosts.java": {
            "label": "SAFE",
            "note": "Host validation against trusted domain whitelist before HTTP dispatch",
            "code": (
                "package com.app.net;\n\n"
                "import java.net.URI;\n"
                "import java.util.Set;\n\n"
                "public class SafeHttpClient {\n"
                '    private static final Set<String> ALLOWED = Set.of("api.trusted.com", "auth.trusted.com");\n\n'
                "    public static boolean isUrlAllowed(String urlStr) {\n"
                "        URI uri = URI.create(urlStr);\n"
                '        return "https".equalsIgnoreCase(uri.getScheme()) && ALLOWED.contains(uri.getHost());\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_15_hardcoded_aws_credentials.java": {
            "label": "MALICIOUS",
            "note": "Embedded static AWS production access key and secret token",
            "code": (
                "package com.app.cloud;\n\n"
                "public class AwsClientConfig {\n"
                '    public static final String ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE";\n'
                '    public static final String SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";\n'
                "}\n"
            ),
        },
        "ext_16_env_secret_retrieval.java": {
            "label": "SAFE",
            "note": "Retrieval of cloud credentials from environment variables",
            "code": (
                "package com.app.cloud;\n\n"
                "public class SafeAwsConfig {\n"
                "    public static String getSecretKey() {\n"
                '        return System.getenv("AWS_SECRET_ACCESS_KEY");\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_17_crypto_des_ecb_cipher.java": {
            "label": "MALICIOUS",
            "note": "Legacy DES encryption in insecure ECB mode",
            "code": (
                "package com.app.crypto;\n\n"
                "import javax.crypto.Cipher;\n"
                "import javax.crypto.SecretKey;\n\n"
                "public class LegacyEncryption {\n"
                "    public static Cipher getDesCipher(SecretKey key) throws Exception {\n"
                '        Cipher c = Cipher.getInstance("DES/ECB/PKCS5Padding");\n'
                "        c.init(Cipher.ENCRYPT_MODE, key);\n"
                "        return c;\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_18_crypto_aes_gcm_safe.java": {
            "label": "SAFE",
            "note": "Authenticated AES-GCM encryption with 128-bit authentication tag",
            "code": (
                "package com.app.crypto;\n\n"
                "import javax.crypto.Cipher;\n"
                "import javax.crypto.SecretKey;\n"
                "import javax.crypto.spec.GCMParameterSpec;\n\n"
                "public class ModernEncryption {\n"
                "    public static Cipher getGcmCipher(SecretKey key, byte[] iv) throws Exception {\n"
                '        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");\n'
                "        c.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(128, iv));\n"
                "        return c;\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_19_bidi_override_auth.java": {
            "label": "MALICIOUS",
            "note": "CVE-2021-42574 Trojan Source bidirectional override in role check",
            "code": (
                "package com.app.auth;\n\n"
                "public class RoleChecker {\n"
                "    public static boolean checkAccess(String role) {\n"
                "        boolean isAdmin = false;\n"
                "        /* \u202e } \u2066if (isAdmin)\u2069 \u2026 */ return true;\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_20_cyrillic_homoglyph_admin.java": {
            "label": "MALICIOUS",
            "note": "Cyrillic homoglyph character shadowing administrative identifier",
            "code": (
                "package com.app.auth;\n\n"
                "public class HomoglyphAdmin {\n"
                "    public static boolean isPrivileged(String adm\u0456n) {\n"
                '        return adm\u0456n != null && adm\u0456n.equals("root");\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_21_zero_width_auth_bypass.java": {
            "label": "MALICIOUS",
            "note": "Invisible zero-width space characters embedded in secret token string",
            "code": (
                "package com.app.auth;\n\n"
                "public class InvisibleToken {\n"
                '    public static final String SECRET_PIN = "adm\u200bin_secret";\n'
                "}\n"
            ),
        },
        "ext_22_process_builder_shell_injection.java": {
            "label": "MALICIOUS",
            "note": "Invoking /bin/sh -c with arbitrary parameter concatenation",
            "code": (
                "package com.app.ops;\n\n"
                "public class ShellRunner {\n"
                "    public static void runScript(String userCommand) throws Exception {\n"
                '        new ProcessBuilder("sh", "-c", "echo " + userCommand).start();\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_23_base64_hidden_class_load.java": {
            "label": "MALICIOUS",
            "note": "Base64 decoded class name passed directly to reflective Class.forName",
            "code": (
                "package com.app.dynamic;\n\n"
                "import java.util.Base64;\n\n"
                "public class ObfuscatedLoader {\n"
                "    public static void executePayload(String b64Name) throws Exception {\n"
                "        String cls = new String(Base64.getDecoder().decode(b64Name));\n"
                "        Class.forName(cls).getDeclaredConstructor().newInstance();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_24_ldap_unencoded_search.java": {
            "label": "MALICIOUS",
            "note": "Unescaped user input inside JNDI LDAP search filter",
            "code": (
                "package com.app.ldap;\n\n"
                "import javax.naming.directory.DirContext;\n"
                "import javax.naming.directory.SearchControls;\n\n"
                "public class LdapSearchService {\n"
                "    public void searchUser(DirContext ctx, String username) throws Exception {\n"
                '        String filter = "(&(objectClass=user)(uid=" + username + "))";\n'
                '        ctx.search("ou=people,dc=example,dc=com", filter, new SearchControls());\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_25_ldap_safe_filter.java": {
            "label": "SAFE",
            "note": "LDAP filter characters sanitized using RFC 4515 escaping rules",
            "code": (
                "package com.app.ldap;\n\n"
                "public class SafeLdapFilter {\n"
                "    public static String escapeLdapFilter(String input) {\n"
                '        return input.replace("\\\\", "\\\\5c").replace("*", "\\\\2a").replace("(", "\\\\28").replace(")", "\\\\29");\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_26_insecure_random_seed.java": {
            "label": "SUSPICIOUS",
            "note": "java.util.Random PRNG used for security-critical password reset token",
            "code": (
                "package com.app.auth;\n\n"
                "import java.util.Random;\n\n"
                "public class WeakResetToken {\n"
                "    public static int createResetCode() {\n"
                "        Random r = new Random();\n"
                "        return r.nextInt(900000) + 100000;\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_27_secure_random_otp.java": {
            "label": "SAFE",
            "note": "CSPRNG SecureRandom used for one-time passcode generation",
            "code": (
                "package com.app.auth;\n\n"
                "import java.security.SecureRandom;\n\n"
                "public class StrongResetToken {\n"
                "    public static int createOtp() throws Exception {\n"
                "        return SecureRandom.getInstanceStrong().nextInt(900000) + 100000;\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_28_reflection_class_for_name.java": {
            "label": "SUSPICIOUS",
            "note": "Dynamic unconstrained reflective class instantiation",
            "code": (
                "package com.app.plugin;\n\n"
                "public class PluginFactory {\n"
                "    public static Object instantiate(String className) throws Exception {\n"
                "        return Class.forName(className).getDeclaredConstructor().newInstance();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_29_static_handler_registry.java": {
            "label": "SAFE",
            "note": "Safe immutable map lookup mapping string tokens to known supplier types",
            "code": (
                "package com.app.plugin;\n\n"
                "import java.util.Map;\n"
                "import java.util.function.Supplier;\n\n"
                "public class SafePluginRegistry {\n"
                "    private static final Map<String, Supplier<Object>> REG = Map.of(\n"
                '        "xml", Object::new,\n'
                '        "json", Object::new\n'
                "    );\n"
                "    public static Object create(String key) {\n"
                "        return REG.getOrDefault(key, Object::new).get();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_30_zip_slip_traversal.java": {
            "label": "MALICIOUS",
            "note": "Zip Slip vulnerability extracting zip entry path without canonical check",
            "code": (
                "package com.app.archive;\n\n"
                "import java.io.*;\n"
                "import java.util.zip.ZipEntry;\n\n"
                "public class ZipExtractor {\n"
                "    public static void extractEntry(File targetDir, ZipEntry entry, InputStream in) throws IOException {\n"
                "        File dest = new File(targetDir, entry.getName());\n"
                "        new FileOutputStream(dest).write(in.readAllBytes());\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_31_safe_zip_extract.java": {
            "label": "SAFE",
            "note": "Zip Slip defense checking getCanonicalPath startsWith destination directory",
            "code": (
                "package com.app.archive;\n\n"
                "import java.io.*;\n"
                "import java.util.zip.ZipEntry;\n\n"
                "public class SafeZipExtractor {\n"
                "    public static File safeExtract(File destDir, ZipEntry entry) throws IOException {\n"
                "        File destFile = new File(destDir, entry.getName());\n"
                "        String canonicalDest = destDir.getCanonicalPath();\n"
                "        String canonicalFile = destFile.getCanonicalPath();\n"
                "        if (!canonicalFile.startsWith(canonicalDest + File.separator)) {\n"
                '            throw new SecurityException("Zip Slip traversal attempt");\n'
                "        }\n"
                "        return destFile;\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_32_jwt_hardcoded_hmac.java": {
            "label": "MALICIOUS",
            "note": "Hardcoded symmetric HMAC signing secret for JWT tokens",
            "code": (
                "package com.app.jwt;\n\n"
                "public class JwtConfig {\n"
                '    public static final String HMAC_SECRET = "my_super_secret_jwt_hmac_key_2026!";\n'
                "}\n"
            ),
        },
        "ext_33_jwt_vault_secret.java": {
            "label": "SAFE",
            "note": "JWT secret retrieved securely from environment or external secret vault",
            "code": (
                "package com.app.jwt;\n\n"
                "public class SafeJwtConfig {\n"
                "    public static String getSecret() {\n"
                '        return System.getenv("JWT_SIGNING_SECRET");\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_34_spring_sql_native_query.java": {
            "label": "MALICIOUS",
            "note": "JPA createNativeQuery with raw input concatenation",
            "code": (
                "package com.app.dao;\n\n"
                "import javax.persistence.EntityManager;\n\n"
                "public class ItemRepository {\n"
                "    public Object searchItem(EntityManager em, String keyword) {\n"
                '        return em.createNativeQuery("SELECT * FROM items WHERE title = \'" + keyword + "\'").getResultList();\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_35_spring_jpa_named_param.java": {
            "label": "SAFE",
            "note": "Spring Data JPA query with named parameter binding",
            "code": (
                "package com.app.dao;\n\n"
                "import javax.persistence.EntityManager;\n\n"
                "public class SafeItemRepository {\n"
                "    public Object searchItem(EntityManager em, String keyword) {\n"
                '        return em.createQuery("SELECT i FROM Item i WHERE i.title = :kw")\n'
                '                 .setParameter("kw", keyword)\n'
                "                 .getResultList();\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_36_runtime_grep_exec.java": {
            "label": "MALICIOUS",
            "note": "Runtime.getRuntime().exec grep command with unchecked user search expression",
            "code": (
                "package com.app.logs;\n\n"
                "public class LogFilter {\n"
                "    public static void filterLogs(String pattern) throws Exception {\n"
                '        Runtime.getRuntime().exec("grep " + pattern + " /var/log/server.log");\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_37_bounded_log_reader.java": {
            "label": "SAFE",
            "note": "In-memory Java stream log filtering without shell invocation",
            "code": (
                "package com.app.logs;\n\n"
                "import java.nio.file.*;\n"
                "import java.util.List;\n"
                "import java.util.stream.Collectors;\n\n"
                "public class SafeLogFilter {\n"
                "    public static List<String> grep(Path logPath, String term) throws Exception {\n"
                "        return Files.lines(logPath).filter(line -> line.contains(term)).limit(100).collect(Collectors.toList());\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_38_xss_servlet_writer.java": {
            "label": "MALICIOUS",
            "note": "Reflected XSS writing unsanitized request parameter directly into HTML response",
            "code": (
                "package com.app.web;\n\n"
                "import javax.servlet.http.*;\n\n"
                "public class UserGreetingServlet extends HttpServlet {\n"
                "    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws Exception {\n"
                '        String name = req.getParameter("name");\n'
                '        resp.getWriter().println("<h1>Welcome " + name + "</h1>");\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_39_xss_escaped_html.java": {
            "label": "SAFE",
            "note": "HTML entity escaping on dynamic input string before response emission",
            "code": (
                "package com.app.web;\n\n"
                "import org.apache.commons.text.StringEscapeUtils;\n\n"
                "public class SafeGreetingFormatter {\n"
                "    public static String formatGreeting(String rawName) {\n"
                '        return "<h1>Welcome " + StringEscapeUtils.escapeHtml4(rawName) + "</h1>";\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_40_sha1_certificate_fingerprint.java": {
            "label": "MALICIOUS",
            "note": "SHA-1 digest used for cryptographic identity verification",
            "code": (
                "package com.app.cert;\n\n"
                "import java.security.MessageDigest;\n\n"
                "public class CertFingerprint {\n"
                "    public static byte[] getFingerprint(byte[] certDer) throws Exception {\n"
                '        return MessageDigest.getInstance("SHA-1").digest(certDer);\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_41_sha256_hash_service.java": {
            "label": "SAFE",
            "note": "SHA-256 secure hash calculation with standard Java Security API",
            "code": (
                "package com.app.cert;\n\n"
                "import java.security.MessageDigest;\n\n"
                "public class SafeCertFingerprint {\n"
                "    public static byte[] getFingerprint(byte[] certDer) throws Exception {\n"
                '        return MessageDigest.getInstance("SHA-256").digest(certDer);\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_42_spring_greeting_controller.java": {
            "label": "SAFE",
            "note": "Modern Spring REST controller producing serialized JSON response",
            "code": (
                "package com.app.controller;\n\n"
                "import java.util.Map;\n\n"
                "public class HealthController {\n"
                "    public Map<String, Object> checkHealth() {\n"
                '        return Map.of("status", "UP", "timestamp", System.currentTimeMillis());\n'
                "    }\n"
                "}\n"
            ),
        },
    }

    index: dict[str, dict[str, Any]] = {}
    for filename, item in benchmarks.items():
        file_path = target_dir / filename
        file_path.write_text(item["code"], encoding="utf-8")
        index[filename] = {
            "label": item["label"],
            "note": item["note"],
            "length": len(item["code"]),
        }

    with open(target_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"Java benchmarks created: {len(benchmarks)} files.")


def build_javascript_benchmarks() -> None:
    target_dir = EXTERNAL_DIR / "javascript"
    target_dir.mkdir(parents=True, exist_ok=True)

    benchmarks: dict[str, dict[str, str]] = {
        "ext_01_user_report_open.js": {
            "label": "MALICIOUS",
            "note": "fs.readFile path traversal via direct query string concatenation",
            "code": (
                "const fs = require('fs');\n"
                "function readReport(req, res) {\n"
                "    const target = '/var/reports/' + req.query.file;\n"
                "    fs.readFile(target, 'utf-8', (err, data) => {\n"
                "        res.send(data);\n"
                "    });\n"
                "}\n"
            ),
        },
        "ext_02_safe_path_resolve.js": {
            "label": "SAFE",
            "note": "path.basename sanitization preventing directory escape",
            "code": (
                "const path = require('path');\n"
                "const fs = require('fs');\n"
                "function safeReadReport(req, res) {\n"
                "    const safeFile = path.basename(req.query.file || 'default.txt');\n"
                "    const fullPath = path.join('/var/reports', safeFile);\n"
                "    return fs.readFileSync(fullPath, 'utf-8');\n"
                "}\n"
            ),
        },
        "ext_03_payment_gateway_md5.js": {
            "label": "MALICIOUS",
            "note": "crypto.createHash with insecure MD5 for payment signature verification",
            "code": (
                "const crypto = require('crypto');\n"
                "function verifyPayment(txId, amount) {\n"
                "    return crypto.createHash('md5').update(txId + ':' + amount).digest('hex');\n"
                "}\n"
            ),
        },
        "ext_04_token_generator_crypto.js": {
            "label": "SAFE",
            "note": "CSPRNG crypto.randomBytes generating session authorization token",
            "code": (
                "const crypto = require('crypto');\n"
                "function generateSessionToken() {\n"
                "    return crypto.randomBytes(32).toString('hex');\n"
                "}\n"
            ),
        },
        "ext_05_backup_db_system.js": {
            "label": "MALICIOUS",
            "note": "child_process.exec command injection via unsanitized table name",
            "code": (
                "const { exec } = require('child_process');\n"
                "function dumpTable(tableName) {\n"
                "    exec('mysqldump mydb ' + tableName, (err, stdout) => {\n"
                "        console.log(stdout);\n"
                "    });\n"
                "}\n"
            ),
        },
        "ext_06_docker_exec_spawn.js": {
            "label": "SAFE",
            "note": "child_process.spawn with safe explicit argument array without shell",
            "code": (
                "const { spawn } = require('child_process');\n"
                "function listContainers() {\n"
                "    return spawn('docker', ['ps', '--format', 'json'], { shell: false });\n"
                "}\n"
            ),
        },
        "ext_07_eval_math_calc.js": {
            "label": "MALICIOUS",
            "note": "eval on arbitrary user formula string leading to code execution",
            "code": (
                "function computeFormula(req, res) {\n"
                "    const expr = req.query.expr;\n"
                "    const result = eval(expr);\n"
                "    res.json({ result });\n"
                "}\n"
            ),
        },
        "ext_08_safe_math_parser.js": {
            "label": "SAFE",
            "note": "Safe numeric evaluation using Math.pow and Number coercion",
            "code": (
                "function safeAdd(a, b) {\n"
                "    const numA = Number(a);\n"
                "    const numB = Number(b);\n"
                "    if (Number.isNaN(numA) || Number.isNaN(numB)) throw new Error('Invalid numbers');\n"
                "    return numA + numB;\n"
                "}\n"
            ),
        },
        "ext_09_sql_search_users.js": {
            "label": "MALICIOUS",
            "note": "Raw SQL query concatenation with user username input",
            "code": (
                "async function findUser(db, username) {\n"
                '    const query = "SELECT * FROM users WHERE username = \'" + username + "\'";\n'
                "    return await db.query(query);\n"
                "}\n"
            ),
        },
        "ext_10_sql_parameterized.js": {
            "label": "SAFE",
            "note": "Parameterized database query using SQL placeholders",
            "code": (
                "async function findUserSafe(db, username) {\n"
                "    const query = 'SELECT id, email FROM users WHERE username = $1';\n"
                "    return await db.query(query, [username]);\n"
                "}\n"
            ),
        },
        "ext_11_dom_xss_innerhtml.js": {
            "label": "MALICIOUS",
            "note": "DOM XSS assigning document.location.search to innerHTML",
            "code": (
                "function renderGreeting() {\n"
                "    const param = new URLSearchParams(window.location.search).get('user');\n"
                "    document.getElementById('greeting').innerHTML = 'Hello ' + param;\n"
                "}\n"
            ),
        },
        "ext_12_safe_dom_textcontent.js": {
            "label": "SAFE",
            "note": "Safe DOM insertion via textContent property preventing script execution",
            "code": (
                "function renderGreetingSafe() {\n"
                "    const param = new URLSearchParams(window.location.search).get('user') || 'Guest';\n"
                "    document.getElementById('greeting').textContent = 'Hello ' + param;\n"
                "}\n"
            ),
        },
        "ext_13_xss_dangerously_set.js": {
            "label": "MALICIOUS",
            "note": "React dangerouslySetInnerHTML with unvalidated user profile bio",
            "code": (
                "function ProfileBio({ rawBio }) {\n"
                "    return <div dangerouslySetInnerHTML={{ __html: rawBio }} />;\n"
                "}\n"
            ),
        },
        "ext_14_dom_purify_react.js": {
            "label": "SAFE",
            "note": "DOMPurify sanitization before dangerouslySetInnerHTML binding",
            "code": (
                "import DOMPurify from 'dompurify';\n"
                "function SafeProfileBio({ rawBio }) {\n"
                "    const clean = DOMPurify.sanitize(rawBio);\n"
                "    return <div dangerouslySetInnerHTML={{ __html: clean }} />;\n"
                "}\n"
            ),
        },
        "ext_15_hardcoded_jwt_secret.js": {
            "label": "MALICIOUS",
            "note": "Hardcoded symmetric JWT authorization signing key in module scope",
            "code": (
                "const jwt = require('jsonwebtoken');\n"
                "const JWT_SECRET = 'my_static_production_secret_token_2026';\n"
                "function signSession(user) {\n"
                "    return jwt.sign(user, JWT_SECRET, { expiresIn: '1h' });\n"
                "}\n"
            ),
        },
        "ext_16_env_jwt_secret.js": {
            "label": "SAFE",
            "note": "JWT secret loaded from process.env with runtime presence check",
            "code": (
                "const jwt = require('jsonwebtoken');\n"
                "function signSessionSafe(user) {\n"
                "    const secret = process.env.JWT_SECRET;\n"
                "    if (!secret) throw new Error('JWT_SECRET missing');\n"
                "    return jwt.sign(user, secret, { expiresIn: '1h' });\n"
                "}\n"
            ),
        },
        "ext_17_prototype_pollution_assign.js": {
            "label": "MALICIOUS",
            "note": "Object.assign on parsed JSON body allowing prototype pollution",
            "code": (
                "function updateSettings(targetObj, jsonBody) {\n"
                "    const payload = JSON.parse(jsonBody);\n"
                "    return Object.assign(targetObj, payload);\n"
                "}\n"
            ),
        },
        "ext_18_safe_shallow_clone.js": {
            "label": "SAFE",
            "note": "Safe property copying verifying own properties and key whitelist",
            "code": (
                "function safeMergeSettings(allowedKeys, source) {\n"
                "    const out = {};\n"
                "    for (const k of allowedKeys) {\n"
                "        if (Object.prototype.hasOwnProperty.call(source, k)) {\n"
                "            out[k] = source[k];\n"
                "        }\n"
                "    }\n"
                "    return out;\n"
                "}\n"
            ),
        },
        "ext_19_bidi_override_check.js": {
            "label": "MALICIOUS",
            "note": "Trojan Source bidirectional control characters spoofing security check",
            "code": (
                "function isUserAdmin(role) {\n"
                "    const isAdmin = false;\n"
                "    /* \u202e } \u2066if (isAdmin)\u2069 \u2026 */ return true;\n"
                "}\n"
            ),
        },
        "ext_20_cyrillic_homoglyph_var.js": {
            "label": "MALICIOUS",
            "note": "Cyrillic homoglyph variable shadowing legitimate auth identifier",
            "code": (
                "function verifyToken(tok\u0435n) {\n"
                "    return tok\u0435n === 'trusted_admin';\n"
                "}\n"
            ),
        },
        "ext_21_zero_width_auth.js": {
            "label": "MALICIOUS",
            "note": "Zero width spaces hidden inside authentication secret literal",
            "code": ("const MASTER_PIN = 'adm\u200bin_secret_pass';\n"),
        },
        "ext_22_exec_sync_shell.js": {
            "label": "MALICIOUS",
            "note": "execSync executing shell string containing user archive parameter",
            "code": (
                "const { execSync } = require('child_process');\n"
                "function extractArchive(tarName) {\n"
                "    execSync('tar -xzf ' + tarName);\n"
                "}\n"
            ),
        },
        "ext_23_base64_payload_eval.js": {
            "label": "MALICIOUS",
            "note": "Decoding Base64 string from client and executing directly via eval",
            "code": (
                "function runEncoded(req) {\n"
                "    const raw = Buffer.from(req.body.b64, 'base64').toString('utf-8');\n"
                "    eval(raw);\n"
                "}\n"
            ),
        },
        "ext_24_ssrf_axios_get.js": {
            "label": "MALICIOUS",
            "note": "SSRF vulnerability making HTTP requests to arbitrary unvalidated URLs",
            "code": (
                "const axios = require('axios');\n"
                "async function fetchProxy(req, res) {\n"
                "    const url = req.query.target;\n"
                "    const resp = await axios.get(url);\n"
                "    res.send(resp.data);\n"
                "}\n"
            ),
        },
        "ext_25_safe_url_fetch.js": {
            "label": "SAFE",
            "note": "URL protocol and hostname validation against trusted whitelist",
            "code": (
                "const axios = require('axios');\n"
                "async function safeFetch(urlStr) {\n"
                "    const u = new URL(urlStr);\n"
                "    if (u.protocol !== 'https:' || u.hostname !== 'api.example.com') {\n"
                "        throw new Error('Blocked SSRF target');\n"
                "    }\n"
                "    return await axios.get(u.href);\n"
                "}\n"
            ),
        },
        "ext_26_math_random_password.js": {
            "label": "SUSPICIOUS",
            "note": "Insecure Math.random used for OTP password reset token",
            "code": (
                "function generateResetCode() {\n"
                "    return Math.floor(100000 + Math.random() * 900000).toString();\n"
                "}\n"
            ),
        },
        "ext_27_crypto_random_reset.js": {
            "label": "SAFE",
            "note": "crypto.randomInt for cryptographically secure OTP generation",
            "code": (
                "const crypto = require('crypto');\n"
                "function generateSecureOtp() {\n"
                "    return crypto.randomInt(100000, 1000000).toString();\n"
                "}\n"
            ),
        },
        "ext_28_dynamic_require_plugin.js": {
            "label": "SUSPICIOUS",
            "note": "Dynamic unconstrained module require from user parameter",
            "code": (
                "function loadPlugin(req) {\n"
                "    const name = req.params.name;\n"
                "    return require('./plugins/' + name);\n"
                "}\n"
            ),
        },
        "ext_29_static_require_map.js": {
            "label": "SAFE",
            "note": "Dictionary map for loading authorized plugin modules",
            "code": (
                "const PLUGINS = {\n"
                "    auth: require('./plugins/auth'),\n"
                "    cache: require('./plugins/cache')\n"
                "};\n"
                "function getPlugin(name) {\n"
                "    return PLUGINS[name] || null;\n"
                "}\n"
            ),
        },
        "ext_30_document_write_sink.js": {
            "label": "MALICIOUS",
            "note": "document.write with user location search parameter",
            "code": (
                "function emitBanner() {\n"
                "    const banner = new URLSearchParams(location.search).get('banner');\n"
                "    document.write('<div>' + banner + '</div>');\n"
                "}\n"
            ),
        },
        "ext_31_safe_element_append.js": {
            "label": "SAFE",
            "note": "Creating DOM elements and assigning textContent securely",
            "code": (
                "function emitBannerSafe(bannerText) {\n"
                "    const div = document.createElement('div');\n"
                "    div.textContent = bannerText;\n"
                "    document.body.appendChild(div);\n"
                "}\n"
            ),
        },
        "ext_32_weak_sha1_hash.js": {
            "label": "MALICIOUS",
            "note": "Deprecated SHA-1 hashing algorithm for user checksums",
            "code": (
                "const crypto = require('crypto');\n"
                "function hashSha1(data) {\n"
                "    return crypto.createHash('sha1').update(data).digest('hex');\n"
                "}\n"
            ),
        },
        "ext_33_safe_sha256_hash.js": {
            "label": "SAFE",
            "note": "SHA-256 secure hash calculation via standard crypto module",
            "code": (
                "const crypto = require('crypto');\n"
                "function hashSha256(data) {\n"
                "    return crypto.createHash('sha256').update(data).digest('hex');\n"
                "}\n"
            ),
        },
        "ext_34_express_sql_login.js": {
            "label": "MALICIOUS",
            "note": "Direct SQL injection in authentication query",
            "code": (
                "async function loginUser(client, req) {\n"
                "    const { user, pass } = req.body;\n"
                "    const sql = `SELECT * FROM accounts WHERE user = '${user}' AND pass = '${pass}'`;\n"
                "    return await client.query(sql);\n"
                "}\n"
            ),
        },
        "ext_35_pg_client_login.js": {
            "label": "SAFE",
            "note": "Parameterized login verification preventing credential bypass",
            "code": (
                "async function loginUserSafe(client, req) {\n"
                "    const { user, pass } = req.body;\n"
                "    const sql = 'SELECT id, pass_hash FROM accounts WHERE user = $1';\n"
                "    return await client.query(sql, [user]);\n"
                "}\n"
            ),
        },
        "ext_36_popen_grep_logs.js": {
            "label": "MALICIOUS",
            "note": "exec executing grep with user filter",
            "code": (
                "const { exec } = require('child_process');\n"
                "function searchLogs(filter) {\n"
                "    exec('grep ' + filter + ' /var/log/app.log', (err, stdout) => {\n"
                "        console.log(stdout);\n"
                "    });\n"
                "}\n"
            ),
        },
        "ext_37_safe_log_search.js": {
            "label": "SAFE",
            "note": "Streams-based text file search without spawning subprocesses",
            "code": (
                "const fs = require('fs');\n"
                "const readline = require('readline');\n"
                "async function safeSearchLogs(keyword) {\n"
                "    const rl = readline.createInterface({ input: fs.createReadStream('/var/log/app.log') });\n"
                "    const matches = [];\n"
                "    for await (const line of rl) {\n"
                "        if (line.includes(keyword)) matches.push(line);\n"
                "    }\n"
                "    return matches;\n"
                "}\n"
            ),
        },
        "ext_38_new_function_calc.js": {
            "label": "MALICIOUS",
            "note": "Dynamic code injection using new Function constructor",
            "code": (
                "function evaluateCode(raw) {\n"
                "    const fn = new Function('return ' + raw);\n"
                "    return fn();\n"
                "}\n"
            ),
        },
        "ext_39_safe_json_calc.js": {
            "label": "SAFE",
            "note": "JSON.parse for safe data structures instead of dynamic code execution",
            "code": (
                "function parseCalculationPayload(rawJson) {\n"
                "    const data = JSON.parse(rawJson);\n"
                "    return Number(data.operandA) + Number(data.operandB);\n"
                "}\n"
            ),
        },
        "ext_40_cors_wildcard_credentials.js": {
            "label": "SUSPICIOUS",
            "note": "Insecure CORS header with wildcard reflection",
            "code": (
                "function setCors(req, res) {\n"
                "    res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*');\n"
                "    res.setHeader('Access-Control-Allow-Credentials', 'true');\n"
                "}\n"
            ),
        },
        "ext_41_safe_cors_origin.js": {
            "label": "SAFE",
            "note": "Strict origin matching for CORS response headers",
            "code": (
                "function setSafeCors(req, res) {\n"
                "    const origin = req.headers.origin;\n"
                "    if (origin === 'https://app.example.com') {\n"
                "        res.setHeader('Access-Control-Allow-Origin', origin);\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_42_express_health_route.js": {
            "label": "SAFE",
            "note": "Standard Express JSON telemetry status handler",
            "code": (
                "function healthHandler(req, res) {\n"
                "    res.json({ status: 'ok', uptime: process.uptime() });\n"
                "}\n"
            ),
        },
    }

    index: dict[str, dict[str, Any]] = {}
    for filename, item in benchmarks.items():
        file_path = target_dir / filename
        file_path.write_text(item["code"], encoding="utf-8")
        index[filename] = {
            "label": item["label"],
            "note": item["note"],
            "length": len(item["code"]),
        }

    with open(target_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"JavaScript benchmarks created: {len(benchmarks)} files.")


def build_cpp_benchmarks() -> None:
    target_dir = EXTERNAL_DIR / "cpp"
    target_dir.mkdir(parents=True, exist_ok=True)

    benchmarks: dict[str, dict[str, str]] = {
        "ext_01_user_report_open.c": {
            "label": "MALICIOUS",
            "note": "Unbounded sprintf constructing file path with potential buffer overflow and traversal",
            "code": (
                "#include <stdio.h>\n"
                "FILE* open_report(const char* filename) {\n"
                "    char path[128];\n"
                '    sprintf(path, "/var/reports/%s", filename);\n'
                '    return fopen(path, "r");\n'
                "}\n"
            ),
        },
        "ext_02_safe_path_resolve.c": {
            "label": "SAFE",
            "note": "Bounded snprintf and directory prefix validation",
            "code": (
                "#include <stdio.h>\n"
                "#include <string.h>\n"
                "FILE* safe_open_report(const char* base, const char* filename) {\n"
                '    if (strstr(filename, "..") != NULL) return NULL;\n'
                "    char path[256];\n"
                '    snprintf(path, sizeof(path), "%s/%s", base, filename);\n'
                '    return fopen(path, "r");\n'
                "}\n"
            ),
        },
        "ext_03_payment_gateway_hash.c": {
            "label": "MALICIOUS",
            "note": "Weak MD5 hash algorithm used for transaction validation",
            "code": (
                "#include <string.h>\n"
                "void hash_tx_md5(const char* tx_data, unsigned char* out) {\n"
                "    // Insecure MD5 implementation\n"
                "    extern void MD5(const unsigned char*, size_t, unsigned char*);\n"
                "    MD5((const unsigned char*)tx_data, strlen(tx_data), out);\n"
                "}\n"
            ),
        },
        "ext_04_token_generator_urandom.c": {
            "label": "SAFE",
            "note": "Reading random bytes from /dev/urandom for cryptographic token",
            "code": (
                "#include <stdio.h>\n"
                "int generate_token(unsigned char* buf, size_t len) {\n"
                '    FILE* f = fopen("/dev/urandom", "rb");\n'
                "    if (!f) return -1;\n"
                "    size_t r = fread(buf, 1, len, f);\n"
                "    fclose(f);\n"
                "    return (r == len) ? 0 : -1;\n"
                "}\n"
            ),
        },
        "ext_05_backup_db_system.c": {
            "label": "MALICIOUS",
            "note": "system() command injection via dynamic table parameter",
            "code": (
                "#include <stdlib.h>\n"
                "#include <stdio.h>\n"
                "int backup_table(const char* table_name) {\n"
                "    char cmd[256];\n"
                '    snprintf(cmd, sizeof(cmd), "mysqldump mydb %s", table_name);\n'
                "    return system(cmd);\n"
                "}\n"
            ),
        },
        "ext_06_docker_exec_fork.c": {
            "label": "SAFE",
            "note": "fork and execve with argument vector avoiding shell expansion",
            "code": (
                "#include <unistd.h>\n"
                "#include <sys/wait.h>\n"
                "int run_docker_ps() {\n"
                "    pid_t pid = fork();\n"
                "    if (pid == 0) {\n"
                '        char* const args[] = {"docker", "ps", NULL};\n'
                '        execvp("docker", args);\n'
                "        _exit(1);\n"
                "    }\n"
                "    int status;\n"
                "    waitpid(pid, &status, 0);\n"
                "    return status;\n"
                "}\n"
            ),
        },
        "ext_07_strcpy_packet_copy.c": {
            "label": "MALICIOUS",
            "note": "Unbounded strcpy buffer overflow copying network packet data",
            "code": (
                "#include <string.h>\n"
                "void process_packet(const char* raw_packet) {\n"
                "    char local_buf[64];\n"
                "    strcpy(local_buf, raw_packet);\n"
                "}\n"
            ),
        },
        "ext_08_safe_snprintf_copy.c": {
            "label": "SAFE",
            "note": "snprintf bounded buffer copy ensuring null termination",
            "code": (
                "#include <stdio.h>\n"
                "void safe_process_packet(const char* raw_packet) {\n"
                "    char local_buf[64];\n"
                '    snprintf(local_buf, sizeof(local_buf), "%s", raw_packet);\n'
                "}\n"
            ),
        },
        "ext_09_printf_format_string.c": {
            "label": "MALICIOUS",
            "note": "Format string vulnerability passing user buffer directly to printf",
            "code": (
                "#include <stdio.h>\n"
                "void log_user_message(const char* user_msg) {\n"
                "    printf(user_msg);\n"
                "}\n"
            ),
        },
        "ext_10_safe_printf_format.c": {
            "label": "SAFE",
            "note": "printf with explicit format specifier string",
            "code": (
                "#include <stdio.h>\n"
                "void safe_log_user_message(const char* user_msg) {\n"
                '    printf("%s\\n", user_msg);\n'
                "}\n"
            ),
        },
        "ext_11_gets_user_input.c": {
            "label": "MALICIOUS",
            "note": "Dangerous gets function leading to stack buffer overflow",
            "code": (
                "#include <stdio.h>\n"
                "void read_username() {\n"
                "    char name_buf[32];\n"
                "    gets(name_buf);\n"
                "}\n"
            ),
        },
        "ext_12_safe_fgets_input.c": {
            "label": "SAFE",
            "note": "Bounded fgets reading user input with size limit",
            "code": (
                "#include <stdio.h>\n"
                "void safe_read_username() {\n"
                "    char name_buf[32];\n"
                "    if (fgets(name_buf, sizeof(name_buf), stdin) != NULL) {\n"
                "        // Process safely\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_13_tmpnam_race_condition.c": {
            "label": "MALICIOUS",
            "note": "Insecure tmpnam race condition vulnerability",
            "code": (
                "#include <stdio.h>\n"
                "FILE* get_scratch_file() {\n"
                "    char name[L_tmpnam];\n"
                "    tmpnam(name);\n"
                '    return fopen(name, "w+");\n'
                "}\n"
            ),
        },
        "ext_14_safe_mkstemp.c": {
            "label": "SAFE",
            "note": "Secure atomic temporary file creation via mkstemp",
            "code": (
                "#include <stdlib.h>\n"
                "#include <unistd.h>\n"
                "int get_safe_scratch_fd() {\n"
                '    char template_str[] = "/tmp/app_XXXXXX";\n'
                "    return mkstemp(template_str);\n"
                "}\n"
            ),
        },
        "ext_15_hardcoded_admin_pass.c": {
            "label": "MALICIOUS",
            "note": "Hardcoded administrator password string literal",
            "code": (
                'const char* ADMIN_PASSWORD = "SuperSecretMasterPass2026!";\n'
                "int verify_pass(const char* p) {\n"
                "    extern int strcmp(const char*, const char*);\n"
                "    return strcmp(p, ADMIN_PASSWORD) == 0;\n"
                "}\n"
            ),
        },
        "ext_16_getenv_secret.c": {
            "label": "SAFE",
            "note": "Administrator password retrieved from environment",
            "code": (
                "#include <stdlib.h>\n"
                "#include <string.h>\n"
                "int safe_verify_pass(const char* p) {\n"
                '    const char* env_pass = getenv("ADMIN_PASSWORD");\n'
                "    if (!env_pass) return 0;\n"
                "    return strcmp(p, env_pass) == 0;\n"
                "}\n"
            ),
        },
        "ext_17_strcat_buffer_overflow.c": {
            "label": "MALICIOUS",
            "note": "Unbounded strcat buffer overflow concatenating user argument",
            "code": (
                "#include <string.h>\n"
                "void append_path(char* dest, const char* component) {\n"
                "    strcat(dest, component);\n"
                "}\n"
            ),
        },
        "ext_18_safe_strncat_copy.c": {
            "label": "SAFE",
            "note": "Bounded strncat accounting for existing buffer length",
            "code": (
                "#include <string.h>\n"
                "void safe_append_path(char* dest, size_t dest_sz, const char* component) {\n"
                "    size_t cur_len = strlen(dest);\n"
                "    if (cur_len + 1 < dest_sz) {\n"
                "        strncat(dest, component, dest_sz - cur_len - 1);\n"
                "    }\n"
                "}\n"
            ),
        },
        "ext_19_bidi_override_auth.c": {
            "label": "MALICIOUS",
            "note": "Trojan Source bidirectional control characters spoofing security logic",
            "code": (
                "#include <stdbool.h>\n"
                "bool check_admin_rights() {\n"
                "    bool is_admin = false;\n"
                "    /* \u202e } \u2066if (is_admin)\u2069 \u2026 */ return true;\n"
                "}\n"
            ),
        },
        "ext_20_cyrillic_homoglyph_id.c": {
            "label": "MALICIOUS",
            "note": "Cyrillic homoglyph shadowing legitimate administrative variable",
            "code": (
                "#include <string.h>\n"
                "int check_token(const char* tok\u0435n) {\n"
                '    return strcmp(tok\u0435n, "trusted_root") == 0;\n'
                "}\n"
            ),
        },
        "ext_21_zero_width_auth.c": {
            "label": "MALICIOUS",
            "note": "Zero-width spaces embedded in cryptographic secret literal",
            "code": ('const char* MASTER_KEY = "adm\u200bin_secret_2026";\n'),
        },
        "ext_22_popen_user_command.c": {
            "label": "MALICIOUS",
            "note": "popen command execution with user-controlled string",
            "code": (
                "#include <stdio.h>\n"
                "FILE* run_filter(const char* filter) {\n"
                "    char cmd[128];\n"
                '    snprintf(cmd, sizeof(cmd), "sort %s", filter);\n'
                '    return popen(cmd, "r");\n'
                "}\n"
            ),
        },
        "ext_23_base64_payload_run.c": {
            "label": "MALICIOUS",
            "note": "Base64 payload decoded and executed via system",
            "code": (
                "#include <stdlib.h>\n"
                "void execute_b64(const char* b64_cmd) {\n"
                "    char script[256];\n"
                "    extern void decode_base64(const char*, char*);\n"
                "    decode_base64(b64_cmd, script);\n"
                "    system(script);\n"
                "}\n"
            ),
        },
        "ext_24_syslog_format_string.c": {
            "label": "MALICIOUS",
            "note": "syslog format string vulnerability with direct message argument",
            "code": (
                "#include <syslog.h>\n"
                "void report_incident(const char* alert_msg) {\n"
                "    syslog(LOG_ERR, alert_msg);\n"
                "}\n"
            ),
        },
        "ext_25_safe_syslog_format.c": {
            "label": "SAFE",
            "note": "syslog with constant format specifier",
            "code": (
                "#include <syslog.h>\n"
                "void safe_report_incident(const char* alert_msg) {\n"
                '    syslog(LOG_ERR, "%s", alert_msg);\n'
                "}\n"
            ),
        },
        "ext_26_rand_session_cookie.c": {
            "label": "SUSPICIOUS",
            "note": "Insecure rand() function used for session cookie identifier",
            "code": ("#include <stdlib.h>\nint make_cookie() {\n    return rand() % 1000000;\n}\n"),
        },
        "ext_27_safe_getrandom_cookie.c": {
            "label": "SAFE",
            "note": "Cryptographically secure random generation via getentropy or /dev/urandom",
            "code": (
                "#include <stdio.h>\n"
                "int make_safe_cookie(unsigned int* out) {\n"
                '    FILE* f = fopen("/dev/urandom", "rb");\n'
                "    if (!f) return -1;\n"
                "    fread(out, sizeof(*out), 1, f);\n"
                "    fclose(f);\n"
                "    return 0;\n"
                "}\n"
            ),
        },
        "ext_28_unchecked_malloc_size.c": {
            "label": "SUSPICIOUS",
            "note": "malloc with unchecked user input size potential integer overflow",
            "code": (
                "#include <stdlib.h>\n"
                "void* allocate_buffer(size_t count, size_t elem_size) {\n"
                "    return malloc(count * elem_size);\n"
                "}\n"
            ),
        },
        "ext_29_safe_calloc_checked.c": {
            "label": "SAFE",
            "note": "calloc with automatic multiplication overflow protection",
            "code": (
                "#include <stdlib.h>\n"
                "void* safe_allocate_buffer(size_t count, size_t elem_size) {\n"
                "    return calloc(count, elem_size);\n"
                "}\n"
            ),
        },
        "ext_30_sprintf_buffer_overflow.c": {
            "label": "MALICIOUS",
            "note": "sprintf buffer overflow into fixed stack buffer",
            "code": (
                "#include <stdio.h>\n"
                "void make_log_entry(char* out, const char* user, const char* ip) {\n"
                '    sprintf(out, "LOGIN: %s from %s", user, ip);\n'
                "}\n"
            ),
        },
        "ext_31_safe_snprintf_buffer.c": {
            "label": "SAFE",
            "note": "snprintf with explicit output buffer capacity bounds",
            "code": (
                "#include <stdio.h>\n"
                "void safe_make_log_entry(char* out, size_t out_sz, const char* user, const char* ip) {\n"
                '    snprintf(out, out_sz, "LOGIN: %s from %s", user, ip);\n'
                "}\n"
            ),
        },
        "ext_32_hardcoded_api_key.cpp": {
            "label": "MALICIOUS",
            "note": "Hardcoded API secret token in C++ string constant",
            "code": (
                "#include <string>\n"
                "namespace Config {\n"
                '    const std::string STRIPE_SECRET = "sk_live_51M00000000000000000000000000000000000000";\n'
                "}\n"
            ),
        },
        "ext_33_safe_config_api_key.cpp": {
            "label": "SAFE",
            "note": "API key read safely from configuration file or environment variable",
            "code": (
                "#include <string>\n"
                "#include <cstdlib>\n"
                "namespace Config {\n"
                "    std::string getSecret() {\n"
                '        const char* val = std::getenv("API_SECRET_KEY");\n'
                '        return val ? std::string(val) : "";\n'
                "    }\n"
                "}\n"
            ),
        },
        "ext_34_double_free_pointer.c": {
            "label": "MALICIOUS",
            "note": "Double free memory corruption vulnerability",
            "code": (
                "#include <stdlib.h>\n"
                "void process_and_cleanup(char* ptr, int error_code) {\n"
                "    if (error_code != 0) {\n"
                "        free(ptr);\n"
                "    }\n"
                "    free(ptr);\n"
                "}\n"
            ),
        },
        "ext_35_raii_unique_ptr.cpp": {
            "label": "SAFE",
            "note": "Modern C++ std::unique_ptr RAII memory management avoiding double free",
            "code": (
                "#include <memory>\n"
                "#include <string>\n"
                "std::unique_ptr<std::string> createManagedString(const std::string& input) {\n"
                "    return std::make_unique<std::string>(input);\n"
                "}\n"
            ),
        },
        "ext_36_popen_grep_filter.c": {
            "label": "MALICIOUS",
            "note": "popen executing grep with unquoted user pattern",
            "code": (
                "#include <stdio.h>\n"
                "FILE* search_sys_log(const char* pattern) {\n"
                "    char cmd[128];\n"
                '    sprintf(cmd, "grep %s /var/log/syslog", pattern);\n'
                '    return popen(cmd, "r");\n'
                "}\n"
            ),
        },
        "ext_37_safe_file_stream.cpp": {
            "label": "SAFE",
            "note": "std::ifstream reading file safely without child processes",
            "code": (
                "#include <fstream>\n"
                "#include <string>\n"
                "#include <vector>\n"
                "std::vector<std::string> safeGrep(const std::string& path, const std::string& term) {\n"
                "    std::ifstream file(path);\n"
                "    std::vector<std::string> matches;\n"
                "    std::string line;\n"
                "    while (std::getline(file, line)) {\n"
                "        if (line.find(term) != std::string::npos) matches.push_back(line);\n"
                "    }\n"
                "    return matches;\n"
                "}\n"
            ),
        },
        "ext_38_tempnam_insecure.c": {
            "label": "MALICIOUS",
            "note": "Deprecated tempnam function vulnerable to symlink race condition",
            "code": (
                "#include <stdio.h>\n"
                "char* make_temp_name() {\n"
                '    return tempnam("/tmp", "pfx");\n'
                "}\n"
            ),
        },
        "ext_39_safe_std_string_concat.cpp": {
            "label": "SAFE",
            "note": "Safe C++ std::string concatenation avoiding buffer overflows",
            "code": (
                "#include <string>\n"
                "std::string formatUserGreeting(const std::string& name) {\n"
                '    return "Welcome, " + name + "!";\n'
                "}\n"
            ),
        },
        "ext_40_raw_crypto_sha1.c": {
            "label": "MALICIOUS",
            "note": "Deprecated SHA-1 hashing algorithm for security token verification",
            "code": (
                "#include <string.h>\n"
                "void hash_token_sha1(const char* token, unsigned char* out) {\n"
                "    extern void SHA1(const unsigned char*, size_t, unsigned char*);\n"
                "    SHA1((const unsigned char*)token, strlen(token), out);\n"
                "}\n"
            ),
        },
        "ext_41_safe_sha256_openssl.c": {
            "label": "SAFE",
            "note": "Modern SHA-256 cryptographic hash function",
            "code": (
                "#include <string.h>\n"
                "void safe_hash_token(const char* token, unsigned char* out) {\n"
                "    extern void SHA256(const unsigned char*, size_t, unsigned char*);\n"
                "    SHA256((const unsigned char*)token, strlen(token), out);\n"
                "}\n"
            ),
        },
        "ext_42_cpp_json_telemetry.cpp": {
            "label": "SAFE",
            "note": "Safe C++ struct telemetry record construction",
            "code": (
                "#include <string>\n"
                "struct MetricRecord {\n"
                "    std::string serviceName;\n"
                "    int statusCode;\n"
                "    double latencyMs;\n"
                "};\n"
                "MetricRecord createRecord(int code, double lat) {\n"
                '    return {"AuthService", code, lat};\n'
                "}\n"
            ),
        },
    }

    index: dict[str, dict[str, Any]] = {}
    for filename, item in benchmarks.items():
        file_path = target_dir / filename
        file_path.write_text(item["code"], encoding="utf-8")
        index[filename] = {
            "label": item["label"],
            "note": item["note"],
            "length": len(item["code"]),
        }

    with open(target_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"C/C++ benchmarks created: {len(benchmarks)} files.")


def main() -> None:
    build_java_benchmarks()
    build_javascript_benchmarks()
    build_cpp_benchmarks()
    print("All external benchmarks generated successfully.")


if __name__ == "__main__":
    main()
