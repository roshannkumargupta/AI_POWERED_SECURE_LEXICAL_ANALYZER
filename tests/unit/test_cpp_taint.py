"""Unit tests for C/C++ taint-lite data-flow reachability analysis."""

from __future__ import annotations

from apsla.languages.cpp_lang.lexer import CppLexer
from apsla.languages.cpp_lang.profile import CPP_TAINT_PROFILE
from apsla.lexing.common import OffsetMap
from apsla.models import TaintStepKind
from apsla.taint.lite import TaintLiteEngine


def _run_cpp_taint(source: str):
    omap = OffsetMap(source)
    tokens = CppLexer(source).tokenize()
    engine = TaintLiteEngine(source, tokens, CPP_TAINT_PROFILE, omap)
    return engine.analyze()


def test_taint_path_argv_to_strcpy():
    """Verify end-to-end taint path from argv[1] source to strcpy sink."""
    source = (
        "#include <string.h>\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32];\n"
        "    char *src = argv[1];\n"
        "    strcpy(dest, src);\n"
        "    return 0;\n"
        "}\n"
    )
    flows = _run_cpp_taint(source)
    assert len(flows) >= 1
    flow = next(f for f in flows if f.rule_id == "APS-CP-MEM-001")
    assert flow.range.start_line == 5
    assert len(flow.path) == 2
    assert flow.path[0].step == TaintStepKind.SOURCE
    assert "argv" in flow.path[0].text
    assert flow.path[1].step == TaintStepKind.SINK
    assert "strcpy" in flow.path[1].text


def test_taint_path_direct_argv_to_strcpy():
    """Verify taint path when argv[1] is passed directly to strcpy."""
    source = (
        "#include <string.h>\n"
        "int main(int argc, char *argv[]) {\n"
        "    char dest[32];\n"
        "    strcpy(dest, argv[1]);\n"
        "    return 0;\n"
        "}\n"
    )
    flows = _run_cpp_taint(source)
    assert len(flows) >= 1
    flow = next(f for f in flows if f.rule_id == "APS-CP-MEM-001")
    assert flow.range.start_line == 4
    assert len(flow.path) == 2
    assert flow.path[0].step == TaintStepKind.SOURCE
    assert flow.path[1].step == TaintStepKind.SINK


def test_taint_path_cin_to_system():
    """Verify taint path from C++ std::cin >> var to system()."""
    source = (
        "#include <iostream>\n"
        "#include <cstdlib>\n"
        "int main() {\n"
        "    std::string cmd;\n"
        "    std::cin >> cmd;\n"
        "    system(cmd.c_str());\n"
        "    return 0;\n"
        "}\n"
    )
    flows = _run_cpp_taint(source)
    assert len(flows) >= 1
    flow = next(f for f in flows if f.rule_id == "APS-CP-INJ-001")
    assert flow.range.start_line == 6
    assert flow.path[0].step == TaintStepKind.SOURCE


def test_taint_path_getenv_to_popen():
    """Verify taint propagation from getenv through buffer to popen."""
    source = (
        "#include <stdlib.h>\n"
        "#include <stdio.h>\n"
        "int main() {\n"
        '    char *env_val = getenv("USER_CMD");\n'
        '    FILE *fp = popen(env_val, "r");\n'
        "    return 0;\n"
        "}\n"
    )
    flows = _run_cpp_taint(source)
    assert len(flows) >= 1
    flow = next(f for f in flows if f.rule_id == "APS-CP-INJ-001")
    assert flow.range.start_line == 5


def test_taint_path_sanitized_via_sizeof():
    """Verify that a bounds check with sizeof marks variable sanitized."""
    source = (
        "#include <string.h>\n"
        "void copy_data(char *src, size_t len) {\n"
        "    char dest[64];\n"
        "    if (len > sizeof(dest)) return;\n"
        "    memcpy(dest, src, len);\n"
        "}\n"
    )
    flows = _run_cpp_taint(source)
    # The bounds check with sizeof sanitizes the copy
    assert not any(f.rule_id == "APS-CP-MEM-002" for f in flows)
