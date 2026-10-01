"""Script to generate C and C++ fixtures and expect.json."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(r"c:\Users\ROSHAN GUPTA\OneDrive\Documents\Desktop\AIDS -Nitw\sem3\toc\securelex-ide")
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "cpp"
VULN_DIR = FIXTURES_DIR / "vulnerable"
SAFE_DIR = FIXTURES_DIR / "safe"
ADV_DIR = FIXTURES_DIR / "adversarial"

VULN_DIR.mkdir(parents=True, exist_ok=True)
SAFE_DIR.mkdir(parents=True, exist_ok=True)
ADV_DIR.mkdir(parents=True, exist_ok=True)

# ── Vulnerable Fixtures ────────────────────────────────────────────────────────

VULNERABLE_FILES = {
    "strcpy_argv.c": (
        "#include <stdio.h>\n"
        "#include <string.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32];\n"
        "    char *src = argv[1];\n"
        "    strcpy(dest, src);\n"
        "    return 0;\n"
        "}\n"
    ),
    "strcat_unbounded.c": (
        "#include <stdio.h>\n"
        "#include <string.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32] = \"Hello \";\n"
        "    char *src = argv[1];\n"
        "    strcat(dest, src);\n"
        "    return 0;\n"
        "}\n"
    ),
    "gets_stdin.c": (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char buf[64];\n"
        "    gets(buf);\n"
        "    return 0;\n"
        "}\n"
    ),
    "sprintf_unbounded.c": (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char buf[64];\n"
        "    sprintf(buf, \"User %s logged in\", argv[1]);\n"
        "    return 0;\n"
        "}\n"
    ),
    "vsprintf_unbounded.c": (
        "#include <stdio.h>\n"
        "#include <stdarg.h>\n\n"
        "void log_msg(const char *fmt, ...) {\n"
        "    char buf[128];\n"
        "    va_list args;\n"
        "    va_start(args, fmt);\n"
        "    vsprintf(buf, fmt, args);\n"
        "    va_end(args);\n"
        "}\n"
    ),
    "strncpy_wrong_sizeof.c": (
        "#include <stdio.h>\n"
        "#include <string.h>\n\n"
        "void copy_data(char *src) {\n"
        "    char dest[32];\n"
        "    strncpy(dest, src, sizeof(src));\n"
        "}\n"
    ),
    "memcpy_wrong_sizeof.c": (
        "#include <stdio.h>\n"
        "#include <string.h>\n\n"
        "void copy_data(char *src) {\n"
        "    char dest[32];\n"
        "    memcpy(dest, src, sizeof(src));\n"
        "}\n"
    ),
    "format_string_printf.c": (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char buf[64];\n"
        "    fgets(buf, sizeof(buf), stdin);\n"
        "    printf(buf);\n"
        "    return 0;\n"
        "}\n"
    ),
    "format_string_fprintf.c": (
        "#include <stdio.h>\n\n"
        "void report_err(const char *msg) {\n"
        "    fprintf(stderr, msg);\n"
        "}\n"
    ),
    "format_string_syslog.c": (
        "#include <syslog.h>\n\n"
        "void log_event(const char *event) {\n"
        "    syslog(LOG_INFO, event);\n"
        "}\n"
    ),
    "scanf_no_width.c": (
        "#include <stdio.h>\n\n"
        "int main() {\n"
        "    char buf[32];\n"
        "    scanf(\"%s\", buf);\n"
        "    return 0;\n"
        "}\n"
    ),
    "fscanf_no_width.c": (
        "#include <stdio.h>\n\n"
        "void read_file(FILE *fp) {\n"
        "    char buf[64];\n"
        "    fscanf(fp, \"%s\", buf);\n"
        "}\n"
    ),
    "sscanf_no_width.c": (
        "#include <stdio.h>\n\n"
        "void parse(const char *input) {\n"
        "    char buf[32];\n"
        "    sscanf(input, \"%s\", buf);\n"
        "}\n"
    ),
    "cmd_injection_system.c": (
        "#include <stdlib.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char *cmd = argv[1];\n"
        "    system(cmd);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cmd_injection_popen.c": (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char *cmd = argv[1];\n"
        "    FILE *fp = popen(cmd, \"r\");\n"
        "    return 0;\n"
        "}\n"
    ),
    "malloc_overflow.c": (
        "#include <stdlib.h>\n\n"
        "void alloc_grid(int width, int height) {\n"
        "    int *grid = (int *)malloc(width * height * sizeof(int));\n"
        "}\n"
    ),
    "use_after_free.c": (
        "#include <stdlib.h>\n"
        "#include <stdio.h>\n\n"
        "void process() {\n"
        "    char *p = (char *)malloc(32);\n"
        "    free(p);\n"
        "    printf(\"%s\\n\", p);\n"
        "}\n"
    ),
    "double_free.c": (
        "#include <stdlib.h>\n\n"
        "void cleanup() {\n"
        "    char *p = (char *)malloc(32);\n"
        "    free(p);\n"
        "    free(p);\n"
        "}\n"
    ),
    "path_traversal_fopen.c": (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char *path = argv[1];\n"
        "    FILE *fp = fopen(path, \"r\");\n"
        "    return 0;\n"
        "}\n"
    ),
    "insecure_rand.c": (
        "#include <stdlib.h>\n\n"
        "int generate_token() {\n"
        "    int token = rand();\n"
        "    return token;\n"
        "}\n"
    ),
    "hardcoded_password.c": (
        "#include <stdio.h>\n\n"
        "const char *db_password = \"SuperSecretP@ssword999\";\n"
    ),
    "insecure_tmpnam.c": (
        "#include <stdio.h>\n\n"
        "void make_temp() {\n"
        "    char name[L_tmpnam];\n"
        "    tmpnam(name);\n"
        "}\n"
    ),
    "alloca_variable.c": (
        "#include <alloca.h>\n\n"
        "void stack_alloc(int n) {\n"
        "    void *p = alloca(n);\n"
        "}\n"
    ),
}

# ── Safe Fixtures ─────────────────────────────────────────────────────────────

SAFE_FILES = {
    "safe_snprintf.c": (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32];\n"
        "    if (argc > 1) {\n"
        "        snprintf(dest, sizeof(dest), \"%s\", argv[1]);\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
    ),
    "safe_fgets.c": (
        "#include <stdio.h>\n\n"
        "int main() {\n"
        "    char buf[64];\n"
        "    fgets(buf, sizeof(buf), stdin);\n"
        "    return 0;\n"
        "}\n"
    ),
    "safe_strncpy_dest_size.c": (
        "#include <string.h>\n\n"
        "void safe_copy(const char *src) {\n"
        "    char dest[32];\n"
        "    strncpy(dest, src, sizeof(dest) - 1);\n"
        "    dest[sizeof(dest) - 1] = '\\0';\n"
        "}\n"
    ),
    "safe_printf_format.c": (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    if (argc > 1) {\n"
        "        printf(\"%s\\n\", argv[1]);\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
    ),
    "safe_fprintf_format.c": (
        "#include <stdio.h>\n\n"
        "void log_err(const char *msg) {\n"
        "    fprintf(stderr, \"%s\\n\", msg);\n"
        "}\n"
    ),
    "safe_syslog_format.c": (
        "#include <syslog.h>\n\n"
        "void log_info(const char *msg) {\n"
        "    syslog(LOG_INFO, \"%s\", msg);\n"
        "}\n"
    ),
    "safe_scanf_width.c": (
        "#include <stdio.h>\n\n"
        "int main() {\n"
        "    char buf[32];\n"
        "    scanf(\"%31s\", buf);\n"
        "    return 0;\n"
        "}\n"
    ),
    "safe_fscanf_width.c": (
        "#include <stdio.h>\n\n"
        "void read_safe(FILE *fp) {\n"
        "    char buf[64];\n"
        "    fscanf(fp, \"%63s\", buf);\n"
        "}\n"
    ),
    "safe_sscanf_width.c": (
        "#include <stdio.h>\n\n"
        "void parse_safe(const char *in) {\n"
        "    char buf[16];\n"
        "    sscanf(in, \"%15s\", buf);\n"
        "}\n"
    ),
    "safe_malloc_calloc.c": (
        "#include <stdlib.h>\n\n"
        "void alloc_safe(size_t n, size_t sz) {\n"
        "    void *p = calloc(n, sz);\n"
        "}\n"
    ),
    "safe_malloc_single.c": (
        "#include <stdlib.h>\n\n"
        "void alloc_buf() {\n"
        "    char *p = (char *)malloc(1024);\n"
        "    free(p);\n"
        "}\n"
    ),
    "safe_free_null.c": (
        "#include <stdlib.h>\n\n"
        "void safe_cleanup() {\n"
        "    char *p = (char *)malloc(64);\n"
        "    free(p);\n"
        "    p = NULL;\n"
        "}\n"
    ),
    "safe_system_constant.c": (
        "#include <stdlib.h>\n\n"
        "int main() {\n"
        "    system(\"echo Done\");\n"
        "    return 0;\n"
        "}\n"
    ),
    "safe_mkstemp.c": (
        "#include <stdlib.h>\n\n"
        "void make_file() {\n"
        "    char template_file[] = \"/tmp/tmpXXXXXX\";\n"
        "    int fd = mkstemp(template_file);\n"
        "}\n"
    ),
    "safe_alloca_constant.c": (
        "#include <alloca.h>\n\n"
        "void alloc_fast() {\n"
        "    void *p = alloca(64);\n"
        "}\n"
    ),
    "safe_cpp_string.cpp": (
        "#include <string>\n\n"
        "void test() {\n"
        "    std::string s = \"hello\";\n"
        "    s += \" world\";\n"
        "}\n"
    ),
    "safe_cpp_vector.cpp": (
        "#include <vector>\n\n"
        "void test() {\n"
        "    std::vector<int> v;\n"
        "    v.push_back(42);\n"
        "}\n"
    ),
    "safe_cpp_random.cpp": (
        "#include <random>\n\n"
        "int get_rand() {\n"
        "    std::random_device rd;\n"
        "    std::mt19937 gen(rd());\n"
        "    return gen();\n"
        "}\n"
    ),
    "safe_cpp_ifstream.cpp": (
        "#include <fstream>\n"
        "#include <string>\n\n"
        "void read_file() {\n"
        "    std::ifstream f(\"config.txt\");\n"
        "    std::string line;\n"
        "    if (f) {\n"
        "        std::getline(f, line);\n"
        "    }\n"
        "}\n"
    ),
    "safe_math_sin.c": (
        "#include <math.h>\n\n"
        "double compute(double x) {\n"
        "    return sin(x) + cos(x);\n"
        "}\n"
    ),
    "safe_strncat.c": (
        "#include <string.h>\n\n"
        "void append_data(char *dst, size_t dst_sz, const char *src) {\n"
        "    strncat(dst, src, dst_sz - strlen(dst) - 1);\n"
        "}\n"
    ),
    "safe_bounds_check.c": (
        "#include <string.h>\n\n"
        "void copy_checked(char *dst, size_t dst_sz, const char *src, size_t len) {\n"
        "    if (len < dst_sz) {\n"
        "        memcpy(dst, src, len);\n"
        "    }\n"
        "}\n"
    ),
}

# ── Adversarial Fixtures ──────────────────────────────────────────────────────

ADVERSARIAL_FILES = {
    "adv_comment_strcpy.c": (
        "#include <stdio.h>\n\n"
        "// Never use strcpy(dest, src) in modern code\n"
        "int main() {\n"
        "    return 0;\n"
        "}\n"
    ),
    "adv_comment_gets.c": (
        "#include <stdio.h>\n\n"
        "/*\n"
        " * gets(buf) was deprecated in C99 and removed in C11.\n"
        " */\n"
        "int main() {\n"
        "    return 0;\n"
        "}\n"
    ),
    "adv_string_sprintf.c": (
        "#include <stdio.h>\n\n"
        "const char *msg = \"Warning: sprintf and vsprintf can cause buffer overflows.\";\n"
        "int main() {\n"
        "    return 0;\n"
        "}\n"
    ),
    "adv_define_system.c": (
        "#include <stdio.h>\n\n"
        "#define SYSTEM_BANNER \"System initialized successfully\"\n"
        "#define STRCPY_SECURE 1\n\n"
        "int main() {\n"
        "    return 0;\n"
        "}\n"
    ),
    "adv_strncpy_constant_bound.c": (
        "#include <string.h>\n\n"
        "int main() {\n"
        "    char buf[64];\n"
        "    strncpy(buf, \"hello\", 5);\n"
        "    buf[5] = '\\0';\n"
        "    return 0;\n"
        "}\n"
    ),
    "adv_printf_format_literal.c": (
        "#include <stdio.h>\n\n"
        "int main(int argc, char *argv[]) {\n"
        "    char *user_input = argv[1];\n"
        "    printf(\"%s\\n\", user_input);\n"
        "    return 0;\n"
        "}\n"
    ),
    "adv_trojan_source_bidi.c": (
        "#include <stdio.h>\n"
        "#include <stdbool.h>\n\n"
        "int main() {\n"
        "    bool isAdmin = false;\n"
        "    /* \u202e } \u2066if (isAdmin)\u2066 \u202e */\n"
        "    return 0;\n"
        "}\n"
    ),
    "adv_zero_width_space.c": (
        "#include <stdio.h>\n\n"
        "int main() {\n"
        "    int sec\u200Bret = 42;\n"
        "    return 0;\n"
        "}\n"
    ),
    "adv_cyrillic_homoglyph.c": (
        "#include <stdio.h>\n\n"
        "int main() {\n"
        "    int p\u0430ssword = 123;\n"
        "    return 0;\n"
        "}\n"
    ),
}

# ── Write files ───────────────────────────────────────────────────────────────

for fname, content in VULNERABLE_FILES.items():
    (VULN_DIR / fname).write_text(content, encoding="utf-8")

for fname, content in SAFE_FILES.items():
    (SAFE_DIR / fname).write_text(content, encoding="utf-8")

for fname, content in ADVERSARIAL_FILES.items():
    (ADV_DIR / fname).write_text(content, encoding="utf-8")

print(f"Generated {len(VULNERABLE_FILES)} vulnerable, {len(SAFE_FILES)} safe, {len(ADVERSARIAL_FILES)} adversarial fixtures.")
