"""Profile-driven taint-lite engine for multi-language source-to-sink tracking.

Operates at statement-level on token streams, providing lightweight data-flow
reachability analysis across Java, JavaScript, and C++ without requiring
full compiler AST frontends.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from apsla.languages.base import TaintProfile, TaintResult
from apsla.lexing.common import OffsetMap
from apsla.lexing.token import Token
from apsla.models import Range, Severity, TaintPathStep, TaintStepKind
from apsla.taint.paths import assemble_taint_path, create_taint_step


@dataclass
class TaintState:
    """Tracks taint provenance and steps for a variable in scope."""

    var_name: str
    categories: set[str] = field(default_factory=lambda: {"ALL"})
    path: list[TaintPathStep] = field(default_factory=list)
    sanitized: bool = False
    sanitizer_name: str = ""


@dataclass
class Statement:
    """A statement or block header bounded by delimiters."""

    tokens: list[Token]
    text: str
    start_line: int
    start_col: int
    end_line: int
    end_col: int

    @property
    def range(self) -> Range:
        return Range(
            start_line=self.start_line,
            start_col=self.start_col,
            end_line=self.end_line,
            end_col=self.end_col,
        )


class TaintLiteEngine:
    """Statement-level data-flow taint analysis engine for C-family languages.

    Configured entirely through a language-specific TaintProfile defining
    sources, sinks, sanitizers, and propagators.
    """

    def __init__(
        self,
        source: str,
        tokens: list[Token],
        profile: TaintProfile,
        offset_map: OffsetMap | None = None,
        struct_tree: Any | None = None,
    ) -> None:
        self.source = source
        self.tokens = tokens
        self.profile = profile
        self.offset_map = offset_map or OffsetMap(source)
        self.struct_tree = struct_tree

        # Precompile lookup patterns for fast matching
        self._sources = profile.sources
        self._sinks = profile.sinks
        self._sanitizers = profile.sanitizers

    def analyze(self) -> list[TaintResult]:
        """Execute statement-level taint tracking and return detected flows."""
        statements = self._split_statements(self.tokens)
        detected_flows: list[TaintResult] = []

        # Scope stack: list of dict[var_name -> TaintState]
        scope_stack: list[dict[str, TaintState]] = [{}]
        current_fn_range: Range | None = None

        for stmt in statements:
            # Handle block delimiter braces in statement
            stmt_text = stmt.text.strip()
            if not stmt_text:
                continue

            # Scope isolation using StructTree function boundaries if available
            if self.struct_tree and getattr(self.struct_tree, "functions", None):
                fn = self.struct_tree.find_function_at(stmt.start_line, stmt.start_col)
                fn_range = fn.range if fn else None
                if fn_range != current_fn_range:
                    current_fn_range = fn_range
                    if fn_range is not None:
                        # Enter new function: isolate locals while keeping process globals (like argv)
                        global_scope = {
                            k: v for k, v in scope_stack[0].items() if k in ("argv", "argc")
                        }
                        scope_stack = [global_scope, {}]

            # Scope entry/exit based on block start and end
            if stmt.tokens and stmt.tokens[0].text == "}" and stmt.tokens[0].kind != "TEMPLATE":
                if len(scope_stack) > 1:
                    scope_stack.pop()

            if stmt.tokens and stmt.tokens[-1].text == "{" and stmt.tokens[-1].kind != "TEMPLATE":
                new_scope = {k: v for k, v in scope_stack[-1].items()}
                scope_stack.append(new_scope)

            current_scope = scope_stack[-1]

            # In C/C++, seed argv/argc if encountered or in main signature
            if ("argv" in stmt_text or "argc" in stmt_text) and "argv" not in current_scope:
                if re.search(r"\bargv\b", stmt_text):
                    source_step = create_taint_step(
                        kind=TaintStepKind.SOURCE,
                        range=stmt.range,
                        text=stmt_text,
                        note="Command-line argument 'argv' retrieved from process entry",
                    )
                    current_scope["argv"] = TaintState(
                        var_name="argv",
                        path=[source_step],
                        categories={"ALL", "COMMAND", "IO", "MEM"},
                    )

            # 1. Check for Sanitizers & Sources in statement
            sanitizer_found, sanitized_var = self._check_sanitizer(stmt, current_scope)
            source_matched, source_name = self._find_source(stmt)
            assigned_var = self._extract_assigned_var(stmt)

            if source_matched and assigned_var:
                if sanitizer_found:
                    # Input was immediately sanitized upon assignment (e.g. Integer.parseInt(req.getParameter("x")))
                    current_scope[assigned_var] = TaintState(
                        var_name=assigned_var,
                        sanitized=True,
                        sanitizer_name=sanitizer_found,
                    )
                else:
                    source_step = create_taint_step(
                        kind=TaintStepKind.SOURCE,
                        range=stmt.range,
                        text=stmt_text,
                        note=f"Untrusted input retrieved via {source_name}",
                    )
                    current_scope[assigned_var] = TaintState(
                        var_name=assigned_var,
                        path=[source_step],
                        categories=self._categorize_source(source_name),
                    )
                continue

            # 2. Check for Sanitizers on existing variables
            if sanitizer_found:
                if sanitized_var and sanitized_var in current_scope:
                    current_scope[sanitized_var].sanitized = True
                    current_scope[sanitized_var].sanitizer_name = sanitizer_found
                if assigned_var:
                    # e.g., int cleanId = Integer.parseInt(id);
                    # cleanId is safe / sanitized
                    current_scope[assigned_var] = TaintState(
                        var_name=assigned_var,
                        sanitized=True,
                        sanitizer_name=sanitizer_found,
                    )
                continue

            # 3. Check for Propagation
            propagated_var = self._check_propagation(stmt, current_scope, assigned_var)
            if propagated_var and assigned_var and assigned_var != propagated_var:
                source_state = current_scope[propagated_var]
                if not source_state.sanitized:
                    prop_step = create_taint_step(
                        kind=TaintStepKind.PROPAGATE,
                        range=stmt.range,
                        text=stmt_text,
                        note=f"Tainted value propagated to variable '{assigned_var}'",
                    )
                    current_scope[assigned_var] = TaintState(
                        var_name=assigned_var,
                        categories=set(source_state.categories),
                        path=list(source_state.path) + [prop_step],
                        sanitized=False,
                    )

            # Check StringBuilder / StringBuffer mutation
            # e.g. sb.append(input);
            sb_mutation = self._check_string_builder_mutation(stmt, current_scope)
            if sb_mutation:
                sb_var, input_var = sb_mutation
                source_state = current_scope[input_var]
                if not source_state.sanitized:
                    prop_step = create_taint_step(
                        kind=TaintStepKind.PROPAGATE,
                        range=stmt.range,
                        text=stmt_text,
                        note=f"Tainted data appended to StringBuilder '{sb_var}'",
                    )
                    current_scope[sb_var] = TaintState(
                        var_name=sb_var,
                        categories=set(source_state.categories),
                        path=list(source_state.path) + [prop_step],
                        sanitized=False,
                    )

            # 4. Check for Sinks
            sink_match = self._find_sink(stmt, current_scope)
            if sink_match:
                tainted_var, rule_id, title, cwe, sev = sink_match
                t_state = current_scope.get(tainted_var)
                if t_state and not t_state.sanitized:
                    sink_range = stmt.range
                    if self.struct_tree and getattr(self.struct_tree, "calls", None):
                        for c in self.struct_tree.calls:
                            if c.range.start_line == stmt.range.start_line:
                                for arg_range, arg_text in zip(c.args, c.arg_texts):
                                    if re.search(rf"\b{re.escape(tainted_var)}\b", arg_text):
                                        sink_range = arg_range
                                        break
                                if sink_range != stmt.range:
                                    break

                    sink_step = create_taint_step(
                        kind=TaintStepKind.SINK,
                        range=sink_range,
                        text=stmt_text,
                        note=f"Tainted data consumed by security-sensitive sink ({title})",
                    )
                    full_path = assemble_taint_path(
                        source_step=t_state.path[0],
                        propagate_steps=t_state.path[1:],
                        sink_step=sink_step,
                    )
                    detected_flows.append(
                        TaintResult(
                            rule_id=rule_id,
                            title=title,
                            cwe=cwe,
                            severity=sev,
                            range=stmt.range,
                            source_text=t_state.path[0].text,
                            sink_text=stmt_text,
                            path=full_path,
                            message=f"{title}: Untrusted data from line {t_state.path[0].range.start_line} reaches sink at line {stmt.range.start_line}.",
                        )
                    )

        return detected_flows

    # ── Internal Helper Methods ──────────────────────────────────────────────────

    def _split_statements(self, tokens: list[Token]) -> list[Statement]:
        """Segment token stream into individual statement chunks."""
        statements: list[Statement] = []
        current: list[Token] = []
        brace_stack: list[str] = []

        for tok in tokens:
            if tok.kind in ("WHITESPACE", "COMMENT"):
                continue

            if tok.kind == "TEMPLATE":
                current.append(tok)
                continue

            if tok.text == "{":
                # Determine if this '{' is a block opener or an expression (object/destructuring)
                is_obj = False
                if current:
                    prev = current[-1]
                    if prev.text in (
                        "const",
                        "let",
                        "var",
                        "import",
                        "export",
                        "=",
                        "+=",
                        "-=",
                        "*=",
                        "/=",
                        ":",
                        ",",
                        "return",
                    ):
                        is_obj = True
                    elif len(current) >= 2 and current[-2].text in ("const", "let", "var"):
                        is_obj = True
                if is_obj:
                    brace_stack.append("OBJECT")
                    current.append(tok)
                else:
                    brace_stack.append("BLOCK")
                    current.append(tok)
                    first = current[0]
                    last = current[-1]
                    raw_text = self.source[
                        self.offset_map.utf16_to_py(first.start) : self.offset_map.utf16_to_py(
                            last.end
                        )
                    ]
                    statements.append(
                        Statement(
                            tokens=list(current),
                            text=raw_text,
                            start_line=first.line,
                            start_col=first.col,
                            end_line=last.end_line,
                            end_col=last.end_col,
                        )
                    )
                    current.clear()
            elif tok.text == "}":
                if brace_stack and brace_stack[-1] == "OBJECT":
                    brace_stack.pop()
                    current.append(tok)
                else:
                    if brace_stack:
                        brace_stack.pop()
                    current.append(tok)
                    first = current[0]
                    last = current[-1]
                    raw_text = self.source[
                        self.offset_map.utf16_to_py(first.start) : self.offset_map.utf16_to_py(
                            last.end
                        )
                    ]
                    statements.append(
                        Statement(
                            tokens=list(current),
                            text=raw_text,
                            start_line=first.line,
                            start_col=first.col,
                            end_line=last.end_line,
                            end_col=last.end_col,
                        )
                    )
                    current.clear()
            elif tok.text == ";":
                current.append(tok)
                first = current[0]
                last = current[-1]
                raw_text = self.source[
                    self.offset_map.utf16_to_py(first.start) : self.offset_map.utf16_to_py(last.end)
                ]
                statements.append(
                    Statement(
                        tokens=list(current),
                        text=raw_text,
                        start_line=first.line,
                        start_col=first.col,
                        end_line=last.end_line,
                        end_col=last.end_col,
                    )
                )
                current.clear()
            else:
                current.append(tok)

        if current:
            first = current[0]
            last = current[-1]
            raw_text = self.source[
                self.offset_map.utf16_to_py(first.start) : self.offset_map.utf16_to_py(last.end)
            ]
            statements.append(
                Statement(
                    tokens=current,
                    text=raw_text,
                    start_line=first.line,
                    start_col=first.col,
                    end_line=last.end_line,
                    end_col=last.end_col,
                )
            )

        return statements

    def _find_source(self, stmt: Statement) -> tuple[bool, str]:
        """Determine if statement consumes an untrusted input source."""
        text = stmt.text
        for src in self._sources:
            if src in text:
                return True, src

        # Also support method parameter annotations: @RequestParam, @PathVariable, @RequestBody
        if any(annot in text for annot in ("@RequestParam", "@PathVariable", "@RequestBody")):
            return True, "Spring MVC Request Annotation"

        # main(String[] args) or args[0]
        if "args[" in text or "args." in text:
            return True, "Command-Line Arguments"

        # C/C++ command-line arguments: argv[1], *argv, argc
        if re.search(r"\b(?:argv\[|\*argv\b|argc\b)", text):
            return True, "Command-Line Arguments"

        # C++ cin >>
        if re.search(r"\b(?:std::)?cin\s*>>", text):
            return True, "Standard Console Input"

        # C getenv
        if re.search(r"\bgetenv\s*\(", text):
            return True, "Environment Variable"

        # C buffer reads: gets, fgets, fread, read, recv, getline, scanf
        if re.search(
            r"\b(?:gets|fgets|read|recv|recvfrom|fread|(?:std::)?getline|scanf|fscanf|sscanf)\s*\(",
            text,
        ):
            return True, "Buffer Read Input"

        return False, ""

    def _categorize_source(self, source_name: str) -> set[str]:
        """Categorize vulnerability vectors associated with this source."""
        return {"ALL", "SQL", "COMMAND", "IO", "XSS", "NET", "CODE", "MEM"}

    def _extract_assigned_var(self, stmt: Statement) -> str | None:
        """Extract the variable identifier receiving an assignment."""
        tokens = stmt.tokens
        for i, tok in enumerate(tokens):
            if tok.text == "=" and i > 0:
                # The token immediately preceding '=' (ignoring type keywords or annotations)
                target = tokens[i - 1]
                if target.kind == "IDENTIFIER":
                    return target.text
            elif tok.text in ("+=",) and i > 0:
                target = tokens[i - 1]
                if target.kind == "IDENTIFIER":
                    return target.text

        # Support destructuring: const { id } = req.query;
        m_destruct = re.search(r"\{\s*([A-Za-z0-9_$]+)", stmt.text)
        if m_destruct and "=" in stmt.text:
            eq_idx = stmt.text.find("=")
            brace_idx = stmt.text.find("{")
            if brace_idx < eq_idx:
                return m_destruct.group(1)

        # Pattern match Spring method parameter: @RequestParam String varName
        m = re.search(
            r"@(?:RequestParam|PathVariable|RequestBody)\s*(?:\([^)]*\))?\s*(?:[A-Za-z0-9_<>]+)\s+([A-Za-z0-9_]+)",
            stmt.text,
        )
        if m:
            return m.group(1)

        # C++ stream extraction: cin >> var or file >> var
        m_cin = re.search(r">>\s*([A-Za-z0-9_]+)", stmt.text)
        if m_cin:
            return m_cin.group(1)

        # C buffer reads with buffer as first argument: gets(buf), fgets(buf, ...), fread(buf, ...)
        m_buf1 = re.search(r"\b(?:gets|fgets|fread)\s*\(\s*&?([A-Za-z0-9_]+)", stmt.text)
        if m_buf1:
            return m_buf1.group(1)

        # C buffer reads with buffer as second argument: read(fd, buf, ...), recv(sock, buf, ...)
        m_buf2 = re.search(r"\b(?:read|recv|recvfrom)\s*\(\s*[^,]+,\s*&?([A-Za-z0-9_]+)", stmt.text)
        if m_buf2:
            return m_buf2.group(1)

        # getline(stream, var) or std::getline(stream, var)
        m_getline = re.search(r"\b(?:std::)?getline\s*\(\s*[^,]+,\s*&?([A-Za-z0-9_]+)", stmt.text)
        if m_getline:
            return m_getline.group(1)

        # scanf("%s", buf) or scanf("%d", &x)
        m_scanf = re.search(r"\b(?:scanf|fscanf|sscanf)\s*\([^,]+,\s*&?([A-Za-z0-9_]+)", stmt.text)
        if m_scanf:
            return m_scanf.group(1)

        return None

    def _check_sanitizer(
        self, stmt: Statement, current_scope: dict[str, TaintState]
    ) -> tuple[str | None, str | None]:
        """Check if statement applies a sanitizer to any tainted variable."""
        text = stmt.text
        for san in self._sanitizers:
            if san in text:
                # Find which variable is being sanitized
                for var_name in current_scope:
                    if re.search(rf"\b{re.escape(var_name)}\b", text):
                        return san, var_name
                return san, None
        return None, None

    def _check_propagation(
        self,
        stmt: Statement,
        current_scope: dict[str, TaintState],
        assigned_var: str | None,
    ) -> str | None:
        """Check if an assignment statement propagates tainted data to target variable."""
        tokens = stmt.tokens
        eq_idx = -1
        for i, tok in enumerate(tokens):
            if tok.text in ("=", "+="):
                eq_idx = i
                break

        if eq_idx == -1:
            return None

        # Check the right-hand side of '=' for any known tainted variable
        rhs_tokens = tokens[eq_idx + 1 :]
        for tok in rhs_tokens:
            if tok.kind == "IDENTIFIER" and tok.text in current_scope:
                state = current_scope[tok.text]
                if not state.sanitized:
                    return tok.text

        return None

    def _check_string_builder_mutation(
        self, stmt: Statement, current_scope: dict[str, TaintState]
    ) -> tuple[str, str] | None:
        """Detect sb.append(taintedVar) or sb.append(x + taintedVar)."""
        text = stmt.text
        m = re.search(r"([A-Za-z0-9_]+)\s*\.\s*append\s*\((.*?)\)", text)
        if m:
            sb_var = m.group(1)
            arg_str = m.group(2)
            for var_name, state in current_scope.items():
                if not state.sanitized and re.search(rf"\b{re.escape(var_name)}\b", arg_str):
                    return sb_var, var_name
        return None

    def _find_sink(
        self, stmt: Statement, current_scope: dict[str, TaintState]
    ) -> tuple[str, str, str, str, Severity] | None:
        """Identify if any tainted variable in scope reaches a dangerous sink."""
        text = stmt.text
        lang = getattr(self.profile, "language", "").lower()

        if lang == "javascript":
            sink_table: list[tuple[str, str, str, str, Severity]] = [
                (
                    r"(?:child_process\.(?:exec|execSync|spawn)|exec|execSync|spawn)\s*\(",
                    "APS-JS-INJ-002",
                    "Command Injection via Subprocess Execution",
                    "CWE-78",
                    Severity.CRITICAL,
                ),
                (
                    r"(?:(?:db|connection|pool|client|sequelize|knex)\.(?:query|execute|raw)|\.query|\.execute|\.raw)\s*\(",
                    "APS-JS-INJ-003",
                    "SQL Injection via Dynamic Query Construction",
                    "CWE-89",
                    Severity.CRITICAL,
                ),
                (
                    r"(?:eval|new\s+Function|Function|setTimeout|setInterval)\s*\(",
                    "APS-JS-INJ-001",
                    "Code Injection via Dynamic Evaluation",
                    "CWE-95",
                    Severity.CRITICAL,
                ),
                (
                    r"(?:\.innerHTML\s*=|\.outerHTML\s*=|\.insertAdjacentHTML\s*\(|document\.write\s*\(|document\.writeln\s*\()",
                    "APS-JS-XSS-001",
                    "DOM Cross-Site Scripting (XSS)",
                    "CWE-79",
                    Severity.HIGH,
                ),
                (
                    r"dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:",
                    "APS-JS-XSS-002",
                    "Cross-Site Scripting via dangerouslySetInnerHTML",
                    "CWE-79",
                    Severity.HIGH,
                ),
                (
                    r"(?:(?:window\.)?location(?:\.href)?\s*=|(?:\.setAttribute\s*\(\s*['\"]on))",
                    "APS-JS-NET-001",
                    "Open Redirect or Event Attribute Injection",
                    "CWE-601",
                    Severity.MEDIUM,
                ),
                (
                    r"(?:fs\.(?:readFile|readFileSync|createReadStream)|(?:res|response)\.sendFile)\s*\(",
                    "APS-JS-IO-001",
                    "Path Traversal via Tainted File Path",
                    "CWE-22",
                    Severity.HIGH,
                ),
                (
                    r"(?:axios(?:\.get|\.post)?|fetch|http\.(?:get|request)|https\.(?:get|request))\s*\(",
                    "APS-JS-NET-002",
                    "Server-Side Request Forgery (SSRF) via Tainted URL",
                    "CWE-918",
                    Severity.HIGH,
                ),
                (
                    r"(?:Object\.assign|_\.(?:merge|set)|lodash\.(?:merge|set))\s*\(",
                    "APS-JS-INJ-004",
                    "Prototype Pollution via Untrusted Object Modification",
                    "CWE-1321",
                    Severity.HIGH,
                ),
                (
                    r"(?:new\s+RegExp|RegExp)\s*\(",
                    "APS-JS-INJ-005",
                    "Regular Expression Denial of Service (ReDoS)",
                    "CWE-1333",
                    Severity.MEDIUM,
                ),
            ]
        elif lang in ("cpp", "c"):
            sink_table = [
                (
                    r"\b(?:system|popen|execl|execlp|execv|execvp|execve)\s*\(",
                    "APS-CP-INJ-001",
                    "Command Injection via Untrusted Input",
                    "CWE-78",
                    Severity.CRITICAL,
                ),
                (
                    r"\b(?:strcpy|strcat|sprintf|vsprintf)\s*\(",
                    "APS-CP-MEM-001",
                    "Buffer Overflow via Unbounded String Copy",
                    "CWE-120",
                    Severity.CRITICAL,
                ),
                (
                    r"\bgets\s*\(",
                    "APS-CP-MEM-001",
                    "Inherently Dangerous Function gets() Call",
                    "CWE-242",
                    Severity.CRITICAL,
                ),
                (
                    r"\b(?:strncpy|memcpy|memmove)\s*\(",
                    "APS-CP-MEM-002",
                    "Out-of-Bounds Memory Access via Tainted Length",
                    "CWE-787",
                    Severity.HIGH,
                ),
                (
                    r"\b(?:printf|fprintf|syslog|snprintf|vsnprintf)\s*\(",
                    "APS-CP-FMT-001",
                    "Format String Vulnerability via Non-Literal Format",
                    "CWE-134",
                    Severity.CRITICAL,
                ),
                (
                    r"\b(?:scanf|fscanf|sscanf)\s*\(",
                    "APS-CP-MEM-003",
                    "Buffer Overflow via Unbounded scanf '%s'",
                    "CWE-120",
                    Severity.HIGH,
                ),
                (
                    r"\b(?:malloc|calloc|realloc)\s*\(|new\s+[A-Za-z0-9_]+\[",
                    "APS-CP-MEM-004",
                    "Integer Overflow in Memory Allocation Size",
                    "CWE-190",
                    Severity.HIGH,
                ),
                (
                    r"\b(?:fopen|open)\s*\(|ifstream\s+[A-Za-z0-9_]+\s*\(",
                    "APS-CP-IO-001",
                    "Path Traversal via Tainted File Path",
                    "CWE-22",
                    Severity.HIGH,
                ),
                (
                    r"\balloca\s*\(",
                    "APS-CP-MEM-007",
                    "Uncontrolled Stack Allocation via alloca",
                    "CWE-770",
                    Severity.HIGH,
                ),
            ]
        else:
            sink_table = [
                (
                    r"(?:Runtime\.getRuntime\(\)\.exec|Runtime\.exec|ProcessBuilder)\s*\(",
                    "APS-JV-INJ-001",
                    "Command Injection via Untrusted Input",
                    "CWE-78",
                    Severity.CRITICAL,
                ),
                (
                    r"(?:\.executeQuery|\.executeUpdate|\.execute|\.createQuery|\.createNativeQuery)\s*\(",
                    "APS-JV-INJ-002",
                    "SQL Injection via Dynamic Query Construction",
                    "CWE-89",
                    Severity.CRITICAL,
                ),
                (
                    r"(?:ObjectInputStream\.readObject|\.readObject\(\)|XMLDecoder\.readObject|XStream\.fromXML)",
                    "APS-JV-DES-001",
                    "Insecure Deserialization via Untrusted Object Stream",
                    "CWE-502",
                    Severity.CRITICAL,
                ),
                (
                    r"(?:new\s+File|Paths\.get|new\s+FileInputStream|new\s+FileReader)\s*\(",
                    "APS-JV-IO-001",
                    "Path Traversal via Tainted File Path",
                    "CWE-22",
                    Severity.HIGH,
                ),
                (
                    r"(?:\.getWriter\(\)\.println|\.getWriter\(\)\.print|\.getOutputStream\(\)\.write)\s*\(",
                    "APS-JV-XSS-001",
                    "Reflected Cross-Site Scripting (XSS)",
                    "CWE-79",
                    Severity.HIGH,
                ),
                (
                    r"(?:new\s+URL|HttpClient\.send|HttpURLConnection)\s*\(",
                    "APS-JV-NET-001",
                    "Server-Side Request Forgery (SSRF) via Tainted URL",
                    "CWE-918",
                    Severity.HIGH,
                ),
                (
                    r"(?:Class\.forName|ClassLoader\.loadClass)\s*\(",
                    "APS-JV-INJ-003",
                    "Unsafe Reflection via Tainted Class Name",
                    "CWE-470",
                    Severity.MEDIUM,
                ),
                (
                    r"(?:ScriptEngine\.eval|\.eval)\s*\(",
                    "APS-JV-INJ-004",
                    "Code Injection via Script Engine Evaluation",
                    "CWE-94",
                    Severity.CRITICAL,
                ),
            ]

        for pattern, rule_id, title, cwe, sev in sink_table:
            m = re.search(pattern, text)
            if m:
                # Check which tainted variable is used in the sink call or statement
                for var_name, state in current_scope.items():
                    if not state.sanitized and re.search(rf"\b{re.escape(var_name)}\b", text):
                        # SQL Injection safety check: if PreparedStatement or parameterized placeholders used
                        if rule_id in ("APS-JV-INJ-002", "APS-JS-INJ-003"):
                            if "prepareStatement(" in text or "PreparedStatement" in text:
                                if "?" in text and "+" not in text:
                                    continue
                            # JS parameterized queries with placeholders and parameters array
                            if ("?" in text or "$1" in text) and "[" in text and "+" not in text:
                                continue

                        # Command Injection safety check: ProcessBuilder with discrete args (no shell, no concat) is safe
                        if rule_id == "APS-JV-INJ-001" and "ProcessBuilder" in text:
                            has_shell = bool(
                                re.search(
                                    r'"(?:(?:/[a-zA-Z0-9_/]+/)?(?:sh|bash)|cmd(?:\.exe)?)"\s*,\s*"[/-][cC]"',
                                    text,
                                )
                            )
                            has_concat = "+" in text
                            if not has_shell and not has_concat:
                                continue

                        # JS Command Injection safety: execFile or spawn with argument array and no shell:true is safe
                        if rule_id == "APS-JS-INJ-002":
                            if "execFile" in text or (
                                "spawn(" in text and "shell: true" not in text
                            ):
                                if "[" in text and "shell: true" not in text and "+" not in text:
                                    continue

                        # JS XSS safety: DOMPurify.sanitize or escapeHtml is safe
                        if rule_id in ("APS-JS-XSS-001", "APS-JS-XSS-002"):
                            if (
                                "DOMPurify.sanitize" in text
                                or "escapeHtml" in text
                                or "textContent" in text
                            ):
                                continue

                        # JS Path Traversal safety: path.basename is safe
                        if rule_id == "APS-JS-IO-001":
                            if "path.basename" in text:
                                continue

                        # JS setTimeout / setInterval: safe if first arg is arrow fn or function callback
                        if rule_id == "APS-JS-INJ-001" and (
                            "setTimeout" in text or "setInterval" in text
                        ):
                            if re.search(
                                r"set(?:Timeout|Interval)\s*\(\s*(?:\(\s*\)\s*=>|function\b|[A-Za-z0-9_]+\s*,)",
                                text,
                            ):
                                if "+" not in text and not re.search(
                                    rf"[`\"'].*\b{re.escape(var_name)}\b.*[`\"']", text
                                ):
                                    continue

                        # C/C++ format string: safe if format argument is a string literal starting with '"'
                        if rule_id == "APS-CP-FMT-001":
                            fn_m = re.search(
                                r"\b(printf|fprintf|syslog|snprintf|vsnprintf)\b", text
                            )
                            fn_name = fn_m.group(1) if fn_m else "printf"
                            fmt_idx = 0
                            if fn_name in ("fprintf", "syslog"):
                                fmt_idx = 1
                            elif fn_name in ("snprintf", "vsnprintf"):
                                fmt_idx = 2
                            inside_m = re.search(
                                r"\b(?:printf|fprintf|syslog|snprintf|vsnprintf)\s*\((.*)\)",
                                text,
                                re.DOTALL,
                            )
                            if inside_m:
                                parts = [p.strip() for p in inside_m.group(1).split(",")]
                                if len(parts) > fmt_idx:
                                    fmt_arg = parts[fmt_idx]
                                    if fmt_arg.startswith('"'):
                                        continue

                        # C/C++ strncpy / memcpy / memmove: safe if length is not tainted
                        if rule_id == "APS-CP-MEM-002":
                            inside_m = re.search(
                                r"\b(?:strncpy|memcpy|memmove)\s*\((.*)\)", text, re.DOTALL
                            )
                            if inside_m:
                                parts = [p.strip() for p in inside_m.group(1).split(",")]
                                if len(parts) >= 3:
                                    len_arg = parts[2]
                                    if not re.search(rf"\b{re.escape(var_name)}\b", len_arg):
                                        continue

                        # C/C++ scanf: safe if %s has an explicit width specifier e.g. %31s
                        if rule_id == "APS-CP-MEM-003":
                            if re.search(r'"[^"]*%\d+s[^"]*"', text):
                                continue
                            if not re.search(r'"[^"]*%s[^"]*"', text):
                                continue

                        return var_name, rule_id, title, cwe, sev

        return None
