"""C and C++ taint profile and dangerous API taxonomy for SecureLex IDE.

Adapted from AI-Powered-Secure-Lexical-Analyzer (MIT).
"""

from __future__ import annotations

from typing import Final

from apsla.languages.base import TaintProfile

# ── Untrusted Sources ──────────────────────────────────────────────────────────

CPP_SOURCES: Final[frozenset[str]] = frozenset(
    {
        # Command-line arguments
        "argv",
        "argc",
        "argv[",
        "*argv",
        # Environment variables
        "getenv",
        "environ",
        # Standard console & terminal inputs
        "gets",
        "fgets",
        "scanf",
        "fscanf",
        "sscanf",
        "getline",
        "cin >>",
        "std::cin >>",
        "cin.get",
        "cin.getline",
        "std::getline",
        "getchar",
        "fgetc",
        # Low-level and socket I/O reads
        "read",
        "recv",
        "recvfrom",
        "recvmsg",
        "fread",
        # C++ stream reads
        "ifstream",
        "std::ifstream",
    }
)

# ── Sensitive Sinks ────────────────────────────────────────────────────────────

CPP_SINKS: Final[frozenset[str]] = frozenset(
    {
        # Unbounded memory copy / string formatting (CWE-120 / CWE-242)
        "strcpy",
        "strcat",
        "gets",
        "sprintf",
        "vsprintf",
        # Bounded copy with tainted / wrong length (CWE-787)
        "strncpy",
        "memcpy",
        "memmove",
        # Format string vulnerabilities (CWE-134)
        "printf",
        "fprintf",
        "syslog",
        "snprintf",
        "vsnprintf",
        # Command injection (CWE-78)
        "system",
        "popen",
        "execl",
        "execlp",
        "execv",
        "execvp",
        "execve",
        # Integer overflow in memory allocation (CWE-190)
        "malloc",
        "calloc",
        "realloc",
        # Use-after-free / Double free (CWE-416 / CWE-415)
        "free",
        # Path traversal (CWE-22)
        "fopen",
        "open",
        # Weak random numbers (CWE-338)
        "rand",
        "srand",
        # Insecure temporary files (CWE-377)
        "tmpnam",
        "mktemp",
        # Uncontrolled stack allocation (CWE-770)
        "alloca",
    }
)

# ── Sanitizers & Safe Practices ───────────────────────────────────────────────

CPP_SANITIZERS: Final[frozenset[str]] = frozenset(
    {
        # Explicit bounds checking
        "sizeof",
        "std::min",
        "min",
        # Safe standard library containers
        "std::string",
        "std::vector",
        "std::array",
        # Bounded numeric conversions
        "strtol",
        "strtoll",
        "strtoul",
        "strtoull",
        "strtof",
        "strtod",
    }
)

# ── Dangerous API Catalog ─────────────────────────────────────────────────────

CPP_DANGEROUS_APIS: Final[dict[str, str]] = {
    "strcpy": "Unbounded string copy into destination buffer without length checks (CWE-120).",
    "strcat": "Unbounded string concatenation can overflow destination buffer (CWE-120).",
    "gets": "Inherently dangerous unbounded buffer read from stdin; deprecated in C99, removed in C11 (CWE-242 / CWE-120).",
    "sprintf": "Unbounded string formatting into buffer without size limit; use snprintf (CWE-120).",
    "vsprintf": "Unbounded variable argument formatting into buffer; use vsnprintf (CWE-120).",
    "scanf": "Scanf '%s' conversion without explicit field width overflows destination buffer (CWE-120).",
    "system": "Executes shell commands from untrusted inputs without argument array isolation (CWE-78).",
    "popen": "Spawns command pipeline in system shell; susceptible to command injection (CWE-78).",
    "execl": "Executes command directly; vulnerable if binary path or arguments are tainted (CWE-78).",
    "execlp": "Executes command searching PATH; susceptible to binary substitution (CWE-78).",
    "execvp": "Executes command searching PATH with argument vector (CWE-78).",
    "rand": "Linear congruential pseudorandom generator unsuitable for cryptographic tokens (CWE-338).",
    "srand": "Seeds weak pseudorandom generator; easily predictable by attackers (CWE-338).",
    "tmpnam": "Creates predictable temporary file name prone to TOCTOU symlink races (CWE-377).",
    "mktemp": "Generates temporary file name without atomicity; use mkstemp (CWE-377).",
    "alloca": "Stack allocation without error detection or stack overflow protection (CWE-770).",
    "free": "Explicit memory deallocation; requires careful pointer nullification to prevent use-after-free (CWE-416).",
}

# ── Taint Profile Singleton ───────────────────────────────────────────────────

CPP_TAINT_PROFILE: Final[TaintProfile] = TaintProfile(
    language="cpp",
    sources=CPP_SOURCES,
    sinks=CPP_SINKS,
    sanitizers=CPP_SANITIZERS,
    dangerous_apis=CPP_DANGEROUS_APIS,
)
