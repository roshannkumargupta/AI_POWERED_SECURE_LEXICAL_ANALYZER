"""Java taint profile and dangerous API taxonomy."""

from __future__ import annotations

from typing import Final

from apsla.languages.base import TaintProfile

JAVA_SOURCES: Final[frozenset[str]] = frozenset(
    {
        "getParameter",
        "getHeader",
        "getCookies",
        "getQueryString",
        "getInputStream",
        "getReader",
        "HttpServletRequest",
        "ServletRequest",
        "@RequestParam",
        "@PathVariable",
        "@RequestBody",
        "Scanner",
        "readLine",
        "BufferedReader",
        "System.getenv",
        "getenv",
        "args[",
        "args.",
    }
)

JAVA_SINKS: Final[frozenset[str]] = frozenset(
    {
        "Runtime.exec",
        "Runtime.getRuntime().exec",
        "ProcessBuilder",
        "Statement.execute",
        "Statement.executeQuery",
        "Statement.executeUpdate",
        "executeQuery",
        "executeUpdate",
        "execute",
        "createQuery",
        "createNativeQuery",
        "ObjectInputStream.readObject",
        "XMLDecoder.readObject",
        "XStream.fromXML",
        "MessageDigest.getInstance",
        "Cipher.getInstance",
        "Random",
        "DocumentBuilderFactory",
        "SAXParserFactory",
        "XMLInputFactory",
        "new File",
        "Paths.get",
        "FileInputStream",
        "FileReader",
        "response.getWriter().println",
        "response.getWriter().print",
        "new URL",
        "HttpClient.send",
        "TrustManager",
        "HostnameVerifier",
        "Class.forName",
        "ClassLoader.loadClass",
        "ScriptEngine.eval",
    }
)

JAVA_SANITIZERS: Final[frozenset[str]] = frozenset(
    {
        "Integer.parseInt",
        "Long.parseLong",
        "Double.parseDouble",
        "Float.parseFloat",
        "Short.parseShort",
        "Byte.parseByte",
        "StringEscapeUtils.escapeHtml4",
        "StringEscapeUtils.escapeHtml3",
        "HtmlUtils.htmlEscape",
        "ESAPI.encoder",
        "encodeForHTML",
        "encodeForSQL",
        "Paths.normalize",
        "startsWith",
        "getCanonicalPath",
        "PreparedStatement",
        "prepareStatement",
        "setString",
        "setInt",
        "setLong",
    }
)

JAVA_DANGEROUS_APIS: Final[dict[str, str]] = {
    "Runtime.getRuntime().exec": "Command execution via Runtime.exec (CWE-78)",
    "Runtime.exec": "Command execution via Runtime.exec (CWE-78)",
    "ProcessBuilder": "Subprocess execution via ProcessBuilder (CWE-78)",
    "Statement.executeQuery": "SQL query execution on Statement (CWE-89)",
    "Statement.executeUpdate": "SQL statement modification on Statement (CWE-89)",
    "Statement.execute": "SQL execution on Statement (CWE-89)",
    "ObjectInputStream.readObject": "Unsafe Java object deserialization (CWE-502)",
    "XMLDecoder.readObject": "Unsafe XMLDecoder deserialization (CWE-502)",
    "XStream.fromXML": "Unsafe XStream XML deserialization (CWE-502)",
    "MessageDigest.getInstance": "Cryptographic message digest algorithm selection (CWE-327)",
    "Cipher.getInstance": "Cryptographic cipher algorithm selection (CWE-327)",
    "java.util.Random": "Insecure pseudo-random number generator (CWE-338)",
    "DocumentBuilderFactory.newInstance": "XML DocumentBuilder creation (XXE risk, CWE-611)",
    "SAXParserFactory.newInstance": "SAX parser creation (XXE risk, CWE-611)",
    "XMLInputFactory.newInstance": "StAX XML reader creation (XXE risk, CWE-611)",
    "java.io.File": "File path access (Path Traversal risk, CWE-22)",
    "java.nio.file.Paths.get": "File path retrieval (Path Traversal risk, CWE-22)",
    "java.io.FileInputStream": "File input stream access (Path Traversal risk, CWE-22)",
    "response.getWriter().println": "Servlet response output (Reflected XSS risk, CWE-79)",
    "response.getWriter().print": "Servlet response output (Reflected XSS risk, CWE-79)",
    "java.net.URL": "Network connection to URL (SSRF risk, CWE-918)",
    "Class.forName": "Dynamic class loading via reflection (CWE-470)",
    "ScriptEngine.eval": "Dynamic script evaluation (CWE-94)",
}

JAVA_TAINT_PROFILE: Final[TaintProfile] = TaintProfile(
    language="java",
    sources=JAVA_SOURCES,
    sinks=JAVA_SINKS,
    sanitizers=JAVA_SANITIZERS,
    dangerous_apis=JAVA_DANGEROUS_APIS,
)
