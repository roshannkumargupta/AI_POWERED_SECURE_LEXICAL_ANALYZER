"""Unit tests for the hand-written C and C++ lexical analyzer."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from apsla.languages.cpp_lang.lexer import CppLexer

# ── Property-Based Tests (Hypothesis) ─────────────────────────────────────────


@given(st.text())
@settings(max_examples=100)
def test_cpp_lexer_lossless_reconstruction_property(source: str) -> None:
    """Invariant: token stream text exactly equals input source byte-for-byte."""
    lexer = CppLexer(source)
    tokens = lexer.tokenize()
    reconstructed = "".join(t.text for t in tokens)
    assert reconstructed == source, f"Mismatch on input: {source!r}"


@given(st.text())
@settings(max_examples=100)
def test_cpp_lexer_never_raises_on_arbitrary_fuzz(source: str) -> None:
    """Invariant: lexer never raises any exception on arbitrary string inputs."""
    lexer = CppLexer(source)
    tokens = lexer.tokenize()
    assert isinstance(tokens, list)


# ── Raw String Literals ───────────────────────────────────────────────────────


def test_raw_string_basic():
    source = 'const char* s = R"(Hello "World"!)";'
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind not in ("WHITESPACE",)]
    str_tok = next(t for t in tokens if t.kind == "STRING")
    assert str_tok.text == 'R"(Hello "World"!)"'


def test_raw_string_custom_delimiter():
    source = 'const char* xml = R"xyz(<tag id="42">hello</tag>)xyz";'
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "STRING"]
    assert len(tokens) == 1
    assert tokens[0].text == 'R"xyz(<tag id="42">hello</tag>)xyz"'


def test_raw_string_multiline():
    source = 'const char* q = R"sql(\nSELECT *\nFROM users\nWHERE id = 1;\n)sql";'
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "STRING"]
    assert len(tokens) == 1
    assert "SELECT *" in tokens[0].text


def test_raw_string_with_prefix():
    source = 'auto s1 = u8R"(utf8)"; auto s2 = LR"(wide)"; auto s3 = uR"(utf16)"; auto s4 = UR"(utf32)";'
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "STRING"]
    assert len(tokens) == 4
    assert tokens[0].text == 'u8R"(utf8)"'
    assert tokens[1].text == 'LR"(wide)"'
    assert tokens[2].text == 'uR"(utf16)"'
    assert tokens[3].text == 'UR"(utf32)"'


# ── Digit Separators (C++14 / C23) ───────────────────────────────────────────


def test_digit_separators_decimal():
    source = "int val = 1'000'000;"
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "NUMBER"]
    assert len(tokens) == 1
    assert tokens[0].text == "1'000'000"


def test_digit_separators_hex():
    source = "unsigned hex = 0xdead'beef'cafe;"
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "NUMBER"]
    assert len(tokens) == 1
    assert tokens[0].text == "0xdead'beef'cafe"


def test_digit_separators_binary():
    source = "int b = 0b1010'0101'1100;"
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "NUMBER"]
    assert len(tokens) == 1
    assert tokens[0].text == "0b1010'0101'1100"


def test_digit_separators_float():
    source = "double pi = 3.14159'26535'89793;"
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "NUMBER"]
    assert len(tokens) == 1
    assert tokens[0].text == "3.14159'26535'89793"


# ── Preprocessor Directives ───────────────────────────────────────────────────


def test_preprocessor_include_angle_brackets():
    source = "#include <stdio.h>\n#include <vector>\n"
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "PREPROCESSOR"]
    assert len(tokens) == 2
    assert tokens[0].text == "#include <stdio.h>"
    assert tokens[1].text == "#include <vector>"


def test_preprocessor_include_quotes():
    source = '#include "my_header.h"\n'
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "PREPROCESSOR"]
    assert len(tokens) == 1
    assert tokens[0].text == '#include "my_header.h"'


def test_preprocessor_backslash_continuation():
    source = "#define MAX(a, b) \\\n    ((a) > (b) ? (a) : (b))\n"
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "PREPROCESSOR"]
    assert len(tokens) == 1
    assert "(a) > (b)" in tokens[0].text


# ── Prefixed Literals & User-Defined Literals ─────────────────────────────────


def test_prefixed_strings_and_chars():
    source = 'L"wide string"; u8"utf-8 string"; u"utf-16"; U"utf-32"; L\'w\'; u8\'u\';'
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "STRING"]
    assert len(tokens) == 6
    assert tokens[0].text == 'L"wide string"'
    assert tokens[1].text == 'u8"utf-8 string"'
    assert tokens[4].text == "L'w'"


def test_user_defined_literals():
    source = 'auto timeout = 10s; auto dist = 2.5km; auto name = "hello"s;'
    lexer = CppLexer(source)
    tokens = lexer.tokenize()
    numbers = [t for t in tokens if t.kind == "NUMBER"]
    strings = [t for t in tokens if t.kind == "STRING"]
    assert any(t.text == "10s" for t in numbers)
    assert any(t.text == "2.5km" for t in numbers)
    assert any(t.text == '"hello"s' for t in strings)


# ── All Operators ─────────────────────────────────────────────────────────────


def test_all_cpp_operators():
    source = "<=> ->* .* :: <<= >>= ... ++ -- -> && || == != <= >= += -= *= /= %= &= |= ^="
    lexer = CppLexer(source)
    tokens = [t for t in lexer.tokenize() if t.kind == "OPERATOR"]
    expected_ops = [
        "<=>",
        "->*",
        ".*",
        "::",
        "<<=",
        ">>=",
        "...",
        "++",
        "--",
        "->",
        "&&",
        "||",
        "==",
        "!=",
        "<=",
        ">=",
        "+=",
        "-=",
        "*=",
        "/=",
        "%=",
        "&=",
        "|=",
        "^=",
    ]
    actual_ops = [t.text for t in tokens]
    assert actual_ops == expected_ops


# ── 15 Realistic Hand-Written C and C++ Files (0 ERROR Tokens) ────────────────


REALISTIC_CPP_SNIPPETS = [
    # 1. Standard C Hello World with main
    """#include <stdio.h>

int main(int argc, char* argv[]) {
    printf("Hello, World!\\n");
    return 0;
}
""",
    # 2. Command-Line Argument Parser in C
    """#include <stdio.h>
#include <stdlib.h>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <name>\\n", argv[0]);
        return 1;
    }
    printf("Arg: %s\\n", argv[1]);
    return 0;
}
""",
    # 3. Socket Server in C with sockaddr_in
    """#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

void start_server(int port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    bind(fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(fd, 5);
}
""",
    # 4. Modern C++ RAII Vector & Unique Pointer
    """#include <vector>
#include <memory>
#include <string>

class UserSession {
public:
    explicit UserSession(std::string name) : username_(std::move(name)) {}
    const std::string& name() const { return username_; }
private:
    std::string username_;
};

void run() {
    auto session = std::make_unique<UserSession>("Alice");
    std::vector<int> numbers = {1, 2, 3, 4, 5};
}
""",
    # 5. C++ Template Class with typename
    """template <typename T, typename Alloc = std::allocator<T>>
class SimpleBuffer {
public:
    SimpleBuffer(size_t cap) : capacity_(cap), data_(new T[cap]) {}
    ~SimpleBuffer() { delete[] data_; }
    T& operator[](size_t idx) { return data_[idx]; }
private:
    size_t capacity_;
    T* data_;
};
""",
    # 6. C++20 Concepts and Requires Clause
    """#include <concepts>

template <typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template <Numeric T>
T add(T a, T b) requires true {
    return a + b;
}
""",
    # 7. Raw String SQL and Multi-line Queries
    """#include <string>

std::string getQuery(int id) {
    const char* sql = R"sql(
        SELECT user_id, email, created_at
        FROM accounts
        WHERE status = 'ACTIVE'
    )sql";
    return std::string(sql);
}
""",
    # 8. Multi-line Macro with Backslash Continuations
    """#define SAFE_FREE(ptr) \\
    do { \\
        if ((ptr) != NULL) { \\
            free(ptr); \\
            (ptr) = NULL; \\
        } \\
    } while (0)
""",
    # 9. Hex Floats and Digit Separators
    """void math_constants() {
    double hex_pi = 0x1.921fb54442d18p+1;
    long long million = 1'000'000LL;
    unsigned int mask = 0b1111'0000'1010'0101;
    float rate = 0.05f;
}
""",
    # 10. Safe String Formatting with snprintf
    """#include <stdio.h>

void formatLog(const char* tag, const char* msg) {
    char buffer[256];
    snprintf(buffer, sizeof(buffer), "[%s] %s", tag, msg);
    puts(buffer);
}
""",
    # 11. C++ File IO with std::ifstream and std::getline
    """#include <fstream>
#include <string>
#include <iostream>

void readConfig(const std::string& path) {
    std::ifstream file(path);
    std::string line;
    while (std::getline(file, line)) {
        std::cout << line << "\\n";
    }
}
""",
    # 12. Multithreading with std::mutex and std::lock_guard
    """#include <mutex>
#include <thread>

std::mutex g_mutex;
int g_counter = 0;

void increment() {
    std::lock_guard<std::mutex> lock(g_mutex);
    ++g_counter;
}
""",
    # 13. C Struct with Bitfields and Typedef Enum
    """typedef enum {
    STATUS_OK = 0,
    STATUS_ERROR = 1,
    STATUS_PENDING = 2
} Status;

typedef struct {
    unsigned int is_admin : 1;
    unsigned int is_active : 1;
    unsigned int role_id : 6;
} UserFlags;
""",
    # 14. Unicode UTF-8 and Wide String Literals
    """#include <wchar.h>

void showMessages() {
    const char* utf8_text = u8"Authentication: 🛡️ Security Check";
    const wchar_t* wide_text = L"Unicode Wide String: Здравствуйте";
    char32_t code_point = U'🌟';
}
""",
    # 15. Pointer to Member and Spaceship Operator
    """struct Point {
    int x;
    int y;
    auto operator<=>(const Point&) const = default;
};

void memberPointerDemo() {
    int Point::*ptr = &Point::x;
    Point p{10, 20};
    int val = p.*ptr;
}
""",
]


@pytest.mark.parametrize("idx,code", list(enumerate(REALISTIC_CPP_SNIPPETS)))
def test_cpp_realistic_snippets_zero_error_tokens(idx: int, code: str) -> None:
    """Verify that 15 realistic C and C++ snippets produce 0 ERROR tokens."""
    lexer = CppLexer(code)
    tokens = lexer.tokenize()

    error_tokens = [t for t in tokens if t.kind == "ERROR"]
    assert not error_tokens, (
        f"Snippet #{idx + 1} produced ERROR tokens: {[t.text for t in error_tokens]}\n"
        f"Code:\n{code}"
    )

    # Lossless verification
    reconstructed = "".join(t.text for t in tokens)
    assert reconstructed == code, f"Snippet #{idx + 1} failed lossless reconstruction"
