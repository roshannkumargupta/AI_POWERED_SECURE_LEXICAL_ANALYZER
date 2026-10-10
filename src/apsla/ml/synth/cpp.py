"""Deterministic generator of labelled C/C++ synthetic snippets from varied templates."""

from __future__ import annotations

import random
from typing import Final

from apsla.languages.cpp_lang.lexer import CppLexer
from apsla.ml.synth.common import (
    LABEL_MALICIOUS,
    LABEL_SAFE,
    LABEL_SUSPICIOUS,
    SyntheticSnippet,
)

# ── Vocabulary Pools for Variation ────────────────────────────────────────────

VARS: Final[list[str]] = [
    "user_input",
    "cmd_arg",
    "query_buf",
    "raw_payload",
    "req_data",
    "file_path",
    "target_name",
    "user_id",
    "token_str",
    "raw_body",
    "host_ip",
    "cat_name",
    "secret_val",
    "search_key",
    "endpoint_url",
    "cache_id",
    "session_id",
]

SAFE_VARS: Final[list[str]] = [
    "item_count",
    "total_sum",
    "idx",
    "active_item",
    "query_res",
    "record_list",
    "metric_val",
    "sys_config",
    "status_code",
    "resp_len",
    "req_options",
    "retry_count",
]

COMMENTS: Final[list[str]] = [
    "// Process incoming network packet buffer",
    "// Parse command line arguments from runtime environment",
    "// Read file contents into allocated memory heap",
    "// Validate authentication token and security flags",
    "// Low-level systems daemon request handler",
    "// Memory-mapped caching layer lookup routine",
    "// Operating system kernel boundary driver interface",
    "// Format output diagnostic telemetry string",
]

DISTRACTORS_PRE: Final[list[str]] = [
    ("#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\n\n"),
    (
        "#include <iostream>\n"
        "#include <string>\n"
        "#include <vector>\n"
        "#include <memory>\n\n"
        "using namespace std;\n\n"
    ),
    ("#include <cstdio>\n#include <cstdlib>\n#include <cstring>\n#include <syslog.h>\n\n"),
    ("#include <sys/types.h>\n#include <sys/stat.h>\n#include <fcntl.h>\n#include <unistd.h>\n\n"),
]

DISTRACTORS_SAFE_BODY: Final[list[str]] = [
    (
        "int safe_compare(const char* a, const char* b) {\n"
        "    if (!a || !b) return -1;\n"
        "    return strncmp(a, b, 256);\n"
        "}\n\n"
    ),
    (
        "size_t compute_buffer_len(const char* s, size_t max_len) {\n"
        "    return strnlen(s, max_len);\n"
        "}\n\n"
    ),
    (
        "void log_status_message(int code, const char* desc) {\n"
        '    fprintf(stderr, "Status [%d]: %s\\n", code, desc);\n'
        "}\n\n"
    ),
]


# ── Template Builders ─────────────────────────────────────────────────────────


def _generate_snippet(
    snippet_id: str,
    family: str,
    pre: str,
    core_lines: list[tuple[str, int]],  # (code_line, label_int)
    post: str = "",
) -> SyntheticSnippet:
    """Combines segments, tokenizes via CppLexer, and labels tokens based on template spans."""
    full_code = pre + "\n" + "\n".join(line for line, _ in core_lines) + "\n" + post
    tokens = CppLexer(full_code).tokenize()

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
        language="cpp",
        code=full_code,
        tokens=tokens,
        token_labels=token_labels,
    )


def _build_buffer_overflow(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 3)

    if variant == 0:
        lines = [
            (f"void process_network_message(const char* {v}) {{", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    char dest_buf[64];", LABEL_SAFE),
            (f"    strcpy(dest_buf, {v});", LABEL_MALICIOUS),
            ('    printf("Processed: %s\\n", dest_buf);', LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            (f"void append_user_suffix(char* target, const char* {v}) {{", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    strcat(target, {v});", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("void read_interactive_input() {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    char input_line[128];", LABEL_SAFE),
            ("    gets(input_line);", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    else:
        lines = [
            ("void format_log_entry(const char* username) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    char log_entry[128];", LABEL_SAFE),
            ('    sprintf(log_entry, "User login from: %s", username);', LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "buffer_overflow", pre, lines)


def _build_format_string(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            (f"void log_user_error(const char* {v}) {{", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    printf({v});", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("void write_syslog_warning(const char* msg) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    syslog(LOG_WARNING, msg);", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    else:
        lines = [
            ("void display_alert(const char* raw_text) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    fprintf(stderr, raw_text);", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "format_string", pre, lines)


def _build_cmd_injection(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            ("int run_backup_tool(const char* filename) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    char {v}[256];", LABEL_SAFE),
            (
                f'    snprintf({v}, sizeof({v}), "tar -czf backup.tar.gz %s", filename);',
                LABEL_SUSPICIOUS,
            ),
            (f"    return system({v});", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("FILE* open_process_stream(const char* user_cmd) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ('    return popen(user_cmd, "r");', LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    else:
        lines = [
            ("void execute_diagnostics(const char* host) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    char cmd_str[128];", LABEL_SAFE),
            ('    sprintf(cmd_str, "ping -c 1 %s", host);', LABEL_MALICIOUS),
            ("    system(cmd_str);", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "cmd_injection", pre, lines)


def _build_insecure_temp_file(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 1)

    if variant == 0:
        lines = [
            ("FILE* create_temporary_cache() {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    char temp_name[L_tmpnam];", LABEL_SAFE),
            ("    tmpnam(temp_name);", LABEL_MALICIOUS),
            ('    return fopen(temp_name, "w+");', LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    else:
        lines = [
            ("void setup_scratch_file() {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ('    char* pfx = tempnam("/tmp", "pfx");', LABEL_MALICIOUS),
            ("    free(pfx);", LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "insecure_temp_file", pre, lines)


def _build_path_traversal(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    variant = rng.randint(0, 1)

    if variant == 0:
        lines = [
            ("FILE* open_user_document(const char* doc_name) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            (f"    char {v}[256];", LABEL_SAFE),
            (f'    snprintf({v}, sizeof({v}), "/var/data/docs/%s", doc_name);', LABEL_SUSPICIOUS),
            (f'    return fopen({v}, "rb");', LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    else:
        lines = [
            ("int open_raw_file(const char* target_file) {", LABEL_SAFE),
            (f"    {c}", LABEL_SAFE),
            ("    return open(target_file, O_RDONLY);", LABEL_MALICIOUS),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "path_traversal", pre, lines)


def _build_weak_random(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    lines = [
        ("int generate_session_secret() {", LABEL_SAFE),
        (f"    {c}", LABEL_SAFE),
        ("    srand(time(NULL));", LABEL_SUSPICIOUS),
        ("    return rand() % 1000000;", LABEL_MALICIOUS),
        ("}", LABEL_SAFE),
    ]
    return _generate_snippet(sid, "weak_random", pre, lines)


def _build_hardcoded_credentials(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    variant = rng.randint(0, 2)

    if variant == 0:
        lines = [
            ("// Hardcoded root database administrator secret", LABEL_SAFE),
            ('const char* DB_PASSWORD = "SuperSecretAdminP@ss2026!";', LABEL_MALICIOUS),
            ('const char* DB_USER = "root_admin";', LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("// API authorization token committed in header", LABEL_SAFE),
            (
                'static const char* API_KEY = "sk_live_51M00000000000000000000000000000000000000";',
                LABEL_MALICIOUS,
            ),
            ("void init_client() { /* ready */ }", LABEL_SAFE),
        ]
    else:
        lines = [
            ("// AWS cloud credentials embedded in utility", LABEL_SAFE),
            ('const char* AWS_KEY = "AKIAIOSFODNN7EXAMPLE";', LABEL_MALICIOUS),
            (
                'const char* AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";',
                LABEL_MALICIOUS,
            ),
        ]
    return _generate_snippet(sid, "hardcoded_credentials", pre, lines)


def _build_suspicious_patterns(rng: random.Random, sid: str) -> SyntheticSnippet:
    v = rng.choice(VARS)
    pre = rng.choice(DISTRACTORS_PRE)
    c = rng.choice(COMMENTS)
    lines = [
        (f"void* allocate_unbounded_buffer(size_t {v}) {{", LABEL_SAFE),
        (f"    {c}", LABEL_SAFE),
        (f"    void* ptr = malloc({v});", LABEL_SUSPICIOUS),
        ("    return ptr;", LABEL_SAFE),
        ("}", LABEL_SAFE),
    ]
    return _generate_snippet(sid, "suspicious_patterns", pre, lines)


def _build_safe_patterns(rng: random.Random, sid: str) -> SyntheticSnippet:
    pre = rng.choice(DISTRACTORS_PRE)
    body = rng.choice(DISTRACTORS_SAFE_BODY)
    variant = rng.randint(0, 4)

    if variant == 0:
        lines = [
            ("void safe_copy_buffer(char* dest, size_t dest_sz, const char* src) {", LABEL_SAFE),
            ('    snprintf(dest, dest_sz, "%s", src);', LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    elif variant == 1:
        lines = [
            ("int read_bounded_line(char* buf, size_t buf_sz, FILE* stream) {", LABEL_SAFE),
            ("    if (fgets(buf, (int)buf_sz, stream) != NULL) {", LABEL_SAFE),
            ("        return 0;", LABEL_SAFE),
            ("    }", LABEL_SAFE),
            ("    return -1;", LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    elif variant == 2:
        lines = [
            ("int create_secure_temp_file() {", LABEL_SAFE),
            ('    char template_path[] = "/tmp/apsla_scratch_XXXXXX";', LABEL_SAFE),
            ("    int fd = mkstemp(template_path);", LABEL_SAFE),
            ("    return fd;", LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    elif variant == 3:
        lines = [
            ("void print_formatted_data(const char* tag, int value) {", LABEL_SAFE),
            ('    printf("Tag: %s, Value: %d\\n", tag, value);', LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    else:
        lines = [
            (
                "std::string build_safe_path(const std::string& base, const std::string& sub) {",
                LABEL_SAFE,
            ),
            ('    if (sub.find("..") != std::string::npos) return "";', LABEL_SAFE),
            ('    return base + "/" + sub;', LABEL_SAFE),
            ("}", LABEL_SAFE),
        ]
    return _generate_snippet(sid, "safe_patterns", pre + body, lines)


# ── Public Generator ──────────────────────────────────────────────────────────


def generate_cpp_dataset(
    count: int = 3000,
    seed: int = 42,
) -> list[SyntheticSnippet]:
    """Generates at least `count` deterministic, leak-free labeled C/C++ snippets.

    Args:
        count: Minimum number of snippets to synthesize (default: 3000).
        seed: Random seed for reproducibility (default: 42).

    Returns:
        List of SyntheticSnippet instances with ground truth per-token labels.
    """
    rng = random.Random(seed)
    families = [
        ("buffer_overflow", _build_buffer_overflow, 0.12),
        ("format_string", _build_format_string, 0.10),
        ("cmd_injection", _build_cmd_injection, 0.10),
        ("insecure_temp_file", _build_insecure_temp_file, 0.08),
        ("path_traversal", _build_path_traversal, 0.08),
        ("weak_random", _build_weak_random, 0.08),
        ("hardcoded_credentials", _build_hardcoded_credentials, 0.08),
        ("suspicious_patterns", _build_suspicious_patterns, 0.09),
        ("safe_patterns", _build_safe_patterns, 0.27),
    ]

    builders = [f[1] for f in families]
    weights = [f[2] for f in families]

    snippets: list[SyntheticSnippet] = []
    for i in range(count):
        sid = f"synth-cpp-{i:05d}"
        chosen_builder = rng.choices(builders, weights=weights, k=1)[0]
        snippet = chosen_builder(rng, sid)
        snippets.append(snippet)

    return snippets
