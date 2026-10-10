"""C/C++ catalogue sources for phase S-3."""

from __future__ import annotations

from typing import Any


def catalogue_s3() -> list[tuple[dict[str, Any], str]]:
    rows: list[tuple[dict[str, Any], str]] = []

    def add(
        sid: str,
        level: str | None,
        kind: str,
        title: str,
        topic: str,
        code: str,
        rules: list[tuple[str, int]] | None = None,
        *,
        chars: list[str] | None = None,
        demo: int | None = None,
    ) -> None:
        if rules is None:
            rules = []
        expected: dict[str, Any] = {
            "findings": [{"rule_id": rule, "line": line} for rule, line in rules],
            "min_findings": len(rules),
        }
        if kind in {"safe", "lexer"}:
            expected["clean_below"] = "medium"
        if kind == "unicode":
            expected["findings"] = [{"rule_id": rule, "line": line} for rule, line in rules]
        summary = f"{topic} example for C/C++ sample review."
        rule_names = ", ".join(rule for rule, _ in rules) or "no medium-or-higher security rule"
        notes = [
            summary,
            "Use inert example input only; no network or destructive payload is included.",
            f"SecureLex checks for {rule_names}.",
            "Review the highlighted source and compare it with the bounded or safer alternative.",
        ]
        ext = (
            ".c"
            if sid
            in {
                "cp-b01",
                "cp-b02",
                "cp-b03",
                "cp-b04",
                "cp-b05",
                "cp-b06",
                "cp-b07",
                "cp-b08",
                "cp-b09",
                "cp-i01",
                "cp-i02",
                "cp-i03",
                "cp-i04",
                "cp-i05",
                "cp-i06",
                "cp-i07",
                "cp-i08",
                "cp-a01",
                "cp-a02",
                "cp-a03",
                "cp-a04",
                "cp-a05",
                "cp-a06",
                "cp-s01",
                "cp-s02",
                "cp-s04",
                "cp-u01",
                "cp-u02",
            }
            else ".cpp"
        )
        row = {
            "id": sid,
            "language": "cpp",
            "file": f"cpp/{sid}_{title.lower().replace(' ', '_')[:28]}{ext}",
            "title": title,
            "kind": kind,
            "level": level,
            "topic": topic,
            "summary": summary,
            "notes": notes,
            "expect": expected,
            "fix_expected": "none",
            "approximate": False,
            "special_chars": chars or [],
            "demo_order": demo,
        }
        rows.append((row, code.rstrip() + "\n"))

    add(
        "cp-b01",
        "basic",
        "vulnerable",
        "Read a Line with gets",
        "Memory Safety",
        "#include <stdio.h>\nint main(void) { char buf[32]; gets(buf); puts(buf); return 0; }",
        [("APS-CP-MEM-001", 3)],
    )
    add(
        "cp-b02",
        "basic",
        "vulnerable",
        "Copy a Name with strcpy",
        "Memory Safety",
        '#include <string.h>\nint main(void) { char dst[16]; const char *name = "guest"; strcpy(dst, name); return dst[0]; }',
        [("APS-CP-MEM-001", 3)],
    )
    add(
        "cp-b03",
        "basic",
        "vulnerable",
        "Format into a Fixed Buffer",
        "Memory Safety",
        '#include <stdio.h>\nint main(void) { char buf[16]; const char *a="service", *b="status"; sprintf(buf, "%s-%s", a, b); puts(buf); }',
        [("APS-CP-MEM-001", 3)],
    )
    add(
        "cp-b04",
        "basic",
        "vulnerable",
        "Scan a Name without Width",
        "Memory Safety",
        '#include <stdio.h>\nint main(void) { char name[20]; scanf("%s", name); return name[0]; }',
        [("APS-CP-MEM-003", 3)],
    )
    add(
        "cp-b05",
        "basic",
        "vulnerable",
        "Print a Variable Format",
        "Format String",
        '#include <stdio.h>\nint main(void) { char message[] = "status"; printf(message); return 0; }',
        [("APS-CP-FMT-001", 3)],
    )
    add(
        "cp-b06",
        "basic",
        "vulnerable",
        "Build a Command with system",
        "Command Injection",
        '#include <stdio.h>\n#include <stdlib.h>\nint main(void) { char cmd[128]; const char *dir="sample"; sprintf(cmd, "ls %s", dir); system(cmd); return 0; }',
        [("APS-CP-INJ-001", 3)],
    )
    add(
        "cp-b07",
        "basic",
        "vulnerable",
        "Generate a Predictable Token",
        "Weak Cryptography",
        "#include <stdlib.h>\n#include <time.h>\nint main(void) { srand((unsigned)time(0)); int token = rand(); return token == 0; }",
        [("APS-CP-CRY-001", 3)],
    )
    add(
        "cp-b08",
        "basic",
        "vulnerable",
        "Compare a Hard-Coded Password",
        "Hard-Coded Secret",
        '#include <string.h>\nint main(void) { const char *password="example-only"; char input[32]="guest"; return strcmp(password, input); }',
        [("APS-CP-SEC-001", 3)],
    )
    add(
        "cp-b09",
        "basic",
        "vulnerable",
        "Create a Temporary Name",
        "Temporary File",
        "#include <stdio.h>\nint main(void) { char name[L_tmpnam]; if (tmpnam(name)) puts(name); return 0; }",
        [("APS-CP-IO-002", 3)],
    )
    add(
        "cp-i01",
        "intermediate",
        "vulnerable",
        "Copy an Argument into a Buffer",
        "Tainted Memory Copy",
        "#include <string.h>\nint main(int argc, char **argv) { char buf[32]; if (argc > 1) strcpy(buf, argv[1]); return 0; }",
        [("APS-CP-MEM-001", 3)],
        demo=11,
    )
    add(
        "cp-i02",
        "intermediate",
        "vulnerable",
        "Format an Argument",
        "Format String",
        "#include <stdio.h>\nint main(int argc, char **argv) { if (argc > 1) { printf(argv[1]); fprintf(stderr, argv[1]); } return 0; }",
        [("APS-CP-FMT-001", 2)],
    )
    add(
        "cp-i03",
        "intermediate",
        "vulnerable",
        "Build a Command from Environment",
        "Command Injection",
        '#include <stdlib.h>\n#include <stdio.h>\nint main(void) { char cmd[128]; const char *user=getenv("USER"); sprintf(cmd, "echo %s", user); system(cmd); }',
        [("APS-CP-INJ-001", 3)],
    )
    add(
        "cp-i04",
        "intermediate",
        "vulnerable",
        "Copy a Tainted Length",
        "Memory Safety",
        "#include <stdlib.h>\n#include <string.h>\nint main(int argc, char **argv) { char buf[32]; int n=argc>2 ? atoi(argv[2]) : 0; if (argc>1) memcpy(buf, argv[1], n); return 0; }",
        [("APS-CP-MEM-002", 3)],
    )
    add(
        "cp-i05",
        "intermediate",
        "vulnerable",
        "Allocate with an Overflowing Size",
        "Integer Overflow",
        "#include <stdlib.h>\nint main(int argc, char **argv) { int n=argc>1 ? atoi(argv[1]) : 1; int *items=malloc(n * sizeof(int)); free(items); return 0; }",
        [("APS-CP-MEM-004", 3)],
    )
    add(
        "cp-i06",
        "intermediate",
        "vulnerable",
        "Open a Path from argv",
        "Path Handling",
        '#include <stdio.h>\nint main(int argc, char **argv) { if (argc>1) { FILE *f=fopen(argv[1], "r"); if (f) fclose(f); } return 0; }',
        [("APS-CP-IO-001", 3)],
    )
    add(
        "cp-i07",
        "intermediate",
        "vulnerable",
        "Copy Using Pointer Sizeof",
        "Memory Safety",
        '#include <string.h>\nvoid copy_name(char *dst, const char *src) { strncpy(dst, src, sizeof(dst)); }\nint main(void) { char buf[16]; copy_name(buf, "guest"); }',
        [("APS-CP-MEM-002", 2)],
    )
    add(
        "cp-i08",
        "intermediate",
        "vulnerable",
        "Allocate a Stack Buffer from Input",
        "Memory Safety",
        "#include <alloca.h>\n#include <stdlib.h>\nint main(int argc, char **argv) { int n=argc>1 ? atoi(argv[1]) : 8; char *buf=alloca(n); return buf[0]; }",
        [("APS-CP-MEM-007", 3)],
    )
    add(
        "cp-i09",
        "intermediate",
        "vulnerable",
        "Ping a Supplied Host",
        "Command Injection",
        '#include <cstdlib>\n#include <iostream>\n#include <string>\nint main() { std::string host; std::getline(std::cin, host); std::system(("ping " + host).c_str()); }',
        [("APS-CP-INJ-001", 4)],
    )
    add(
        "cp-a01",
        "advanced",
        "vulnerable",
        "Read Memory after free",
        "Use After Free",
        "#include <cstdlib>\nint main(void) { int *p=(int*)malloc(sizeof(int)); *p=7; free(p); return *p; }",
        [("APS-CP-MEM-005", 3)],
    )
    add(
        "cp-a02",
        "advanced",
        "vulnerable",
        "Free a Pointer Twice",
        "Double Free",
        "#include <cstdlib>\nint main(void) { int *p=(int*)malloc(sizeof(int)); free(p); free(p); return 0; }",
        [("APS-CP-MEM-006", 3)],
    )
    add(
        "cp-a03",
        "advanced",
        "vulnerable",
        "Copy Data across Functions",
        "Interprocedural Memory Safety",
        '#include <cstring>\nchar *read_input() { static char value[]="sample"; return value; }\nvoid process(const char *src) { char buf[8]; strcpy(buf, src); }\nint main() { process(read_input()); }',
        [("APS-CP-MEM-001", 4)],
    )
    add(
        "cp-a04",
        "advanced",
        "vulnerable",
        "Review a Small Utility",
        "Multiple Security Issues",
        """#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
int main(void) {
    char input[64], message[32], command[96], password[24];
    printf("Input: ");
    gets(input);
    sprintf(message, "hello %s", input);
    sprintf(command, "echo %s", input);
    system(command);
    srand((unsigned)time(0));
    int token = rand();
    strcpy(password, "demo-password");
    printf("token=%d password=%s\\n", token, password);
    return 0;
}""".replace("\n+", "\n")
        + "\n/*\n"
        + "\n".join(f" * Utility review note {index}" for index in range(1, 47))
        + "\n */",
        [
            ("APS-CP-MEM-001", 9),
            ("APS-CP-MEM-001", 10),
            ("APS-CP-INJ-001", 11),
            ("APS-CP-CRY-001", 13),
            ("APS-CP-SEC-001", 14),
        ],
    )
    add(
        "cp-a05",
        "advanced",
        "vulnerable",
        "Review a TCP Echo Buffer",
        "Memory and Format Strings",
        "#include <stdio.h>\n#include <string.h>\nint main(void) { char incoming[64], buffer[16]; int received=0; recv(0, incoming, sizeof incoming, 0); strcpy(buffer, incoming); printf(buffer); return received; }",
        [("APS-CP-MEM-001", 4), ("APS-CP-FMT-001", 4)],
    )
    add(
        "cp-a06",
        "advanced",
        "vulnerable",
        "Compare Checked and Unchecked Copies",
        "Bounds Checking",
        '#include <string.h>\nvoid checked(const char *src, size_t len) { char buf[16]; if (len >= sizeof buf) return; memcpy(buf, src, len); }\nvoid unchecked(const char *src) { char buf[16]; strcpy(buf, src); }\nint main(void) { checked("ok", 2); unchecked("sample"); }',
        [("APS-CP-MEM-001", 3)],
        demo=12,
    )
    add(
        "cp-s01",
        None,
        "safe",
        "Read Input with Bounds",
        "Bounded Input",
        '#include <stdio.h>\n#include <stdlib.h>\nint main(void) { char buf[32]; if (fgets(buf, sizeof buf, stdin)) { char *end; long n=strtol(buf, &end, 10); if (end != buf && n >= 0 && n <= 100) printf("%ld\\n", n); } }',
    )
    add(
        "cp-s02",
        None,
        "safe",
        "Use Constant Format Strings",
        "Format Safety",
        '#include <stdio.h>\nint main(void) { const char *s="status"; printf("%s", s); puts(""); fputs(s, stdout); }',
    )
    add(
        "cp-s03",
        None,
        "safe",
        "Use Modern C++ Containers",
        "Safe C++",
        '#include <memory>\n#include <string>\n#include <vector>\nint main() { std::vector<std::unique_ptr<std::string>> items; items.push_back(std::make_unique<std::string>("ready")); for (const auto &item : items) (void)*item; }',
    )
    add(
        "cp-s04",
        None,
        "safe",
        "Copy after a Length Check",
        "Bounded Copies",
        "#include <cstring>\nvoid copy_text(char *dst, size_t cap, const char *src, size_t len) { if (len >= cap) return; memcpy(dst, src, len); dst[len] = '\\0'; }\nint main() { char buf[16]; copy_text(buf, sizeof buf, \"hello\", 5); }",
    )
    add(
        "cp-s05",
        None,
        "safe",
        "Open a File with RAII",
        "RAII File Handling",
        '#include <filesystem>\n#include <fstream>\n#include <string>\nint main() { const std::filesystem::path path{"README.md"}; if (std::filesystem::exists(path)) { std::ifstream file(path); std::string line; std::getline(file, line); } }',
    )
    add(
        "cp-u01",
        None,
        "unicode",
        "Review a Bidi Comment",
        "Trojan Source",
        "#include <iostream>\nint main() { // review note __BIDI_SAMPLE__\n    int ready = 1;\n    std::cout << ready;\n}",
        [("APS-ALL-UNI-001", 2)],
        chars=["U+202E", "U+2066", "U+2069"],
    )
    add(
        "cp-u02",
        None,
        "unicode",
        "Inspect a Look-Alike Identifier",
        "Unicode Identifier",
        "#include <iostream>\nint main() { int p__CYRILLIC_A__th = 1; std::cout << p__CYRILLIC_A__th; }",
        [("APS-ALL-UNI-004", 2)],
        chars=["U+0430"],
    )
    add(
        "cp-l01",
        None,
        "lexer",
        "Exercise C++ Literals",
        "Lexer Showcase",
        "#include <string_view>\nusing namespace std::literals;\nint main() { auto raw = R\"x(first line\\nsecond line)x\"; auto count=1'000'000; auto hex=0x1.8p+2; auto suffix=\"sample\"sv; char8_t a=u8'a'; char16_t b=u'b'; char32_t c=U'c'; wchar_t d=L'd'; return int(count + int(hex) + int(raw.size()+suffix.size()+a+b+c+d)); }",
    )
    add(
        "cp-l02",
        None,
        "lexer",
        "Exercise Preprocessor Forms",
        "Lexer Showcase",
        '#ifndef SAMPLE_HEADER\n#define SAMPLE_HEADER\n#define SAMPLE_VALUE(x) \\\n+    ((x) + 1)\n#if defined(__cplusplus)\n#include <iostream>\n#elif defined(SAMPLE_C)\n#include "sample.h"\n#else\n#pragma once\n#endif\nint main() { return SAMPLE_VALUE(1); }'.replace(
            "\n+", "\n"
        ),
    )
    add(
        "cp-l03",
        None,
        "lexer",
        "Exercise C++20 Syntax",
        "Lexer Showcase",
        "#include <compare>\n#include <concepts>\nnamespace demo { template<class T> concept Number = std::integral<T>; struct Box { int value; auto operator<=>(const Box&) const = default; }; int Box::* member = &Box::value; template<Number T> auto twice(T x) { auto fn = [x] { return x + x; }; return fn(); } }\nint main() { demo::Box b{2}; return (b.*demo::member) + int(demo::twice(1)); }",
    )
    return rows
