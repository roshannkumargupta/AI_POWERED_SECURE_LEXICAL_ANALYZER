"""Common Weakness Enumeration (CWE) definitions and metadata mappings."""

from __future__ import annotations

from typing import Final

# IMPORTANT: These CWE mappings are heuristic defaults and must be double-checked by a human.
# Automated categorizations should always undergo verification by a qualified security analyst.
HUMAN_REVIEW_DISCLAIMER: Final[str] = (
    "These CWE mappings are heuristic defaults and must be double-checked by a human."
)

CATEGORY_TO_CWE: Final[dict[str, str]] = {
    # Injection categories
    "COMMAND_INJECTION": "CWE-78",
    "INJ-CMD": "CWE-78",  # Improper Neutralization of Special Elements in an OS Command
    "CMD": "CWE-78",
    "SQL_INJECTION": "CWE-89",
    "INJ-SQL": "CWE-89",  # SQL Injection
    "SQL": "CWE-89",
    "XSS": "CWE-79",
    "INJ-XSS": "CWE-79",  # Cross-site Scripting
    "CODE_INJECTION": "CWE-94",
    "INJ-CODE": "CWE-94",  # Improper Control of Generation of Code ('Code Injection')
    "CODE": "CWE-94",
    "EVAL_INJECTION": "CWE-95",
    "INJ-EVAL": "CWE-95",  # Improper Neutralization of Directives in Dynamically Evaluated Code
    "EVAL": "CWE-95",
    # Deserialization & Memory
    "DESERIALIZATION": "CWE-502",
    "UNSAFE_DESERIALIZATION": "CWE-502",
    "DESER": "CWE-502",  # Deserialization of Untrusted Data
    "BUFFER_OVERFLOW": "CWE-120",
    "MEM": "CWE-120",  # Buffer Copy without Checking Size of Input
    "OUT_OF_BOUNDS_WRITE": "CWE-787",
    "BUF-OVERFLOW": "CWE-787",  # Out-of-bounds Write
    "FORMAT_STRING": "CWE-134",
    "FORMAT": "CWE-134",  # Use of Externally-Controlled Format String
    # Cryptography & Secrets
    "WEAK_CRYPTO": "CWE-327",
    "CRYPTO": "CWE-327",  # Use of a Broken or Risky Cryptographic Algorithm
    "HARDCODED_SECRET": "CWE-798",
    "SECRET": "CWE-798",  # Use of Hard-coded Credentials
    "CRED": "CWE-798",
    # Path & Network
    "PATH_TRAVERSAL": "CWE-22",
    "PATH": "CWE-22",  # Improper Limitation of a Pathname to a Restricted Directory
    "SSRF": "CWE-918",  # Server-Side Request Forgery
    "XXE": "CWE-611",  # Improper Restriction of XML External Entity Reference
    # Unicode & Obfuscation
    "UNI-CONFUSABLE": "CWE-1007",  # Insufficient Visual Distinction of Homoglyphs
    "CONFUSABLE": "CWE-1007",
    "HOMOGLYPH": "CWE-1007",
    "VISUALLY_SIMILAR": "CWE-1007",
    "IMPROPER_ENCODING": "CWE-116",
    "ENCODING": "CWE-116",  # Improper Encoding or Escaping of Output
    "MALICIOUS_CODE": "CWE-506",
    "EMBEDDED_MALICIOUS_CODE": "CWE-506",
    "TROJAN": "CWE-506",  # Embedded Malicious Code (Trojan Source, bidi overrides)
    "MALICIOUS": "CWE-506",
    # Fallback / General
    "GENERIC": "CWE-20",  # Improper Input Validation
    "ML-ANOMALY": "CWE-1007",
}

RULE_CATEGORY_TO_CWE: Final[dict[str, str]] = CATEGORY_TO_CWE

CWE_METADATA: Final[dict[str, dict[str, str]]] = {
    "CWE-78": {
        "title": "OS Command Injection",
        "description": "The software constructs an OS command using externally-influenced input without proper neutralization.",
    },
    "CWE-89": {
        "title": "SQL Injection",
        "description": "The software constructs a SQL command using untrusted input that can alter the intended SQL logic.",
    },
    "CWE-79": {
        "title": "Cross-Site Scripting (XSS)",
        "description": "The software does not neutralize or incorrectly neutralizes user-controllable input before placing it in web output.",
    },
    "CWE-94": {
        "title": "Code Injection",
        "description": "The software constructs all or part of a code segment using externally-influenced input.",
    },
    "CWE-95": {
        "title": "Eval Injection",
        "description": "The software receives input from an upstream component and uses it in dynamically evaluated statements.",
    },
    "CWE-502": {
        "title": "Deserialization of Untrusted Data",
        "description": "The application deserializes untrusted data without sufficiently verifying that the resulting data will be valid.",
    },
    "CWE-327": {
        "title": "Use of Broken Cryptographic Algorithm",
        "description": "The use of a broken or risky cryptographic algorithm will compromise message confidentiality or integrity.",
    },
    "CWE-798": {
        "title": "Use of Hard-coded Credentials",
        "description": "The software contains hard-coded credentials such as passwords or cryptographic keys.",
    },
    "CWE-22": {
        "title": "Path Traversal",
        "description": "The software uses external input to construct a pathname intended to identify a file or directory located under a restricted directory.",
    },
    "CWE-918": {
        "title": "Server-Side Request Forgery (SSRF)",
        "description": "The web server receives a URL or request parameter from an upstream client and makes a network request to this target.",
    },
    "CWE-120": {
        "title": "Buffer Copy without Checking Size of Input",
        "description": "The program copies an input buffer to an output buffer without verifying that the size of the input buffer is less than the size of the output buffer.",
    },
    "CWE-787": {
        "title": "Out-of-bounds Write",
        "description": "The software writes data past the end, or before the beginning, of the intended buffer.",
    },
    "CWE-134": {
        "title": "Use of Externally-Controlled Format String",
        "description": "The software uses a function that accepts a format string as an argument, but the format string originates from an external source.",
    },
    "CWE-611": {
        "title": "Improper Restriction of XML External Entity Reference (XXE)",
        "description": "The software processes an XML document that can contain XML entities with URIs that resolve to documents outside of the intended sphere of control.",
    },
    "CWE-1007": {
        "title": "Insufficient Visual Distinction of Homoglyphs",
        "description": "The product relies on visual distinction between characters from different scripts or fonts, creating security ambiguities.",
    },
    "CWE-116": {
        "title": "Improper Encoding or Escaping of Output",
        "description": "The software prepares data for a specific context without appropriately encoding or escaping characters.",
    },
    "CWE-506": {
        "title": "Embedded Malicious Code",
        "description": "The software contains code that is not part of the intended product logic, including Trojan Source bidi tricks.",
    },
    "CWE-20": {
        "title": "Improper Input Validation",
        "description": "The product receives input or data, but it does not validate or incorrectly validates that the input has the expected properties.",
    },
}


def get_cwe_for_category(category: str) -> str:
    """Retrieve the standard CWE identifier for a given rule category.

    Note: These mappings are heuristic defaults and must be double-checked by a human.

    Args:
        category: The category identifier or rule prefix (e.g. 'INJ-CMD', 'CONFUSABLE').

    Returns:
        str: Corresponding CWE identifier (e.g. 'CWE-78'), or 'CWE-20' as fallback.
    """
    cleaned = category.strip().upper()
    return CATEGORY_TO_CWE.get(cleaned, "CWE-20")
