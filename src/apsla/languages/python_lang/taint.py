"""AST-based flow-sensitive data-flow taint analysis engine for Python."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

from apsla.models import Range, TaintPathStep, TaintStepKind
from apsla.rules.base import RuleContext

COMMAND_SINKS = frozenset({"os.system", "os.popen"})
CODE_SINKS = frozenset({"eval", "exec", "__import__", "importlib.import_module"})
SQL_SINKS = frozenset({"execute", "executemany"})
PATH_SINKS = frozenset({"open", "send_file", "flask.send_file"})
XSS_SINKS = frozenset({"render_template_string", "Markup", "markupsafe.Markup"})
DESER_SINKS = frozenset({"pickle.loads", "pickle.load", "yaml.load", "yaml.unsafe_load"})


@dataclass(slots=True)
class TaintFlow:
    """A detected or sanitized taint flow path from source to sink."""

    rule_id: str
    sink_range: Range
    path: list[TaintPathStep] = field(default_factory=list)
    sanitized: bool = False
    message: str = ""


@dataclass(slots=True)
class TaintResult:
    """Result of AST data-flow taint analysis containing all detected flows."""

    flows: list[TaintFlow] = field(default_factory=list)

    def __iter__(self):
        return iter(self.flows)

    def __len__(self) -> int:
        return len(self.flows)


@dataclass
class TaintValue:
    """Taint state for a variable or expression."""

    is_tainted: bool
    categories: set[str] = field(default_factory=lambda: {"ALL"})
    path: list[TaintPathStep] = field(default_factory=list)
    sanitized: bool = False


class PythonTaintAnalyzer:
    """Flow-sensitive intra-file AST data-flow taint analysis engine."""

    def __init__(self, context: RuleContext) -> None:
        self.context = context
        self.flows: list[TaintFlow] = []
        # Intra-file function summaries: func_name -> {param_name: TaintValue}
        self.function_summaries: dict[str, dict[str, bool]] = {}

    def _create_step(
        self,
        kind: TaintStepKind,
        rng: Range,
        node: ast.AST | None = None,
        note: str = "",
    ) -> TaintPathStep:
        """Construct a validated TaintPathStep instance."""
        text = ""
        if node is not None:
            try:
                text = ast.get_source_segment(self.context.raw_source, node) or ""
            except Exception:
                text = ""
        if not text:
            text = note or kind.value
        return TaintPathStep(
            step=kind,
            range=rng,
            text=text,
            note=note,
        )

    def analyze(self) -> TaintResult:
        """Execute full AST taint analysis and return detected flows."""
        tree = self.context.ast_tree
        if tree is None:
            return TaintResult()

        # Phase 1: Build function summaries for intra-file calls
        self._build_function_summaries(tree)

        # Phase 2: Flow-sensitive analysis of module-level statements and functions
        env: dict[str, TaintValue] = {}
        for stmt in tree.body:
            self._analyze_statement(stmt, env)

        return TaintResult(flows=self.flows)

    def _build_function_summaries(self, tree: ast.AST) -> None:
        """Analyze function definitions to determine which arguments flow to return values."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_names = [arg.arg for arg in node.args.args]
                param_taint: dict[str, bool] = {}

                # Simulated taint tracking over function body assuming each parameter is tainted
                for p in param_names:
                    local_env = {p: TaintValue(is_tainted=True, categories={"ALL"})}
                    returns_taint = False
                    for stmt in node.body:
                        self._analyze_statement(stmt, local_env, record_sinks=False)
                        if isinstance(stmt, ast.Return) and stmt.value is not None:
                            val = self._evaluate_expression(stmt.value, local_env)
                            if val.is_tainted:
                                returns_taint = True
                    param_taint[p] = returns_taint

                self.function_summaries[node.name] = param_taint

    def _analyze_statement(
        self,
        stmt: ast.AST,
        env: dict[str, TaintValue],
        record_sinks: bool = True,
    ) -> None:
        """Flow-sensitively process a single Python statement."""
        # 1. Variable Assignment: v = expr
        if isinstance(stmt, ast.Assign):
            val = self._evaluate_expression(stmt.value, env, record_sinks=record_sinks)
            for target in stmt.targets:
                self._assign_target(target, val, env, stmt)

        # 2. Augmented Assignment: v += expr
        elif isinstance(stmt, ast.AugAssign):
            val = self._evaluate_expression(stmt.value, env, record_sinks=record_sinks)
            if isinstance(stmt.target, ast.Name):
                orig = env.get(stmt.target.id, TaintValue(is_tainted=False))
                combined = self._merge_taint(
                    orig, val, stmt, f"Augmented assignment to '{stmt.target.id}'"
                )
                env[stmt.target.id] = combined

        # 3. Expression Statements: func(...)
        elif isinstance(stmt, ast.Expr):
            self._evaluate_expression(stmt.value, env, record_sinks=record_sinks)

        # 4. Conditional Branches: if / else
        elif isinstance(stmt, ast.If):
            self._evaluate_expression(stmt.test, env, record_sinks=record_sinks)

            env_then = {k: self._clone_taint(v) for k, v in env.items()}
            env_else = {k: self._clone_taint(v) for k, v in env.items()}

            for s in stmt.body:
                self._analyze_statement(s, env_then, record_sinks=record_sinks)
            for s in stmt.orelse:
                self._analyze_statement(s, env_else, record_sinks=record_sinks)

            # Union of both branches
            all_keys = set(env_then.keys()) | set(env_else.keys())
            for k in all_keys:
                t1 = env_then.get(k, TaintValue(is_tainted=False))
                t2 = env_else.get(k, TaintValue(is_tainted=False))
                if t1.is_tainted:
                    env[k] = t1
                elif t2.is_tainted:
                    env[k] = t2

        # 5. Loops: while / for (Fixed-point iteration, max 3 rounds)
        elif isinstance(stmt, (ast.While, ast.For)):
            if isinstance(stmt, ast.For):
                # Target in for loop is tainted if iterable is tainted
                iter_val = self._evaluate_expression(stmt.iter, env, record_sinks=record_sinks)
                self._assign_target(stmt.target, iter_val, env, stmt)

            for _ in range(3):
                prev_tainted = {k: v.is_tainted for k, v in env.items()}
                for s in stmt.body:
                    self._analyze_statement(s, env, record_sinks=record_sinks)
                new_tainted = {k: v.is_tainted for k, v in env.items()}
                if prev_tainted == new_tainted:
                    break

        # 6. Function Definitions
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check for FastAPI / Flask route parameters
            is_route = False
            for dec in stmt.decorator_list:
                dec_name = self._get_attr_name(dec)
                if any(kw in dec_name for kw in ("route", "get", "post", "put", "delete", "api")):
                    is_route = True
                    break

            func_env = {k: self._clone_taint(v) for k, v in env.items()}
            if is_route:
                for arg in stmt.args.args:
                    rng = self.context.node_to_range(arg)
                    step = self._create_step(
                        kind=TaintStepKind.SOURCE,
                        rng=rng,
                        node=arg,
                        note=f"Route parameter '{arg.arg}' receives untrusted user input",
                    )
                    func_env[arg.arg] = TaintValue(
                        is_tainted=True,
                        categories={"ALL"},
                        path=[step],
                    )

            for s in stmt.body:
                self._analyze_statement(s, func_env, record_sinks=record_sinks)

    def _assign_target(
        self,
        target: ast.AST,
        val: TaintValue,
        env: dict[str, TaintValue],
        stmt: ast.AST,
    ) -> None:
        """Assign a evaluated taint value to target variables (supporting tuple unpacking)."""
        # Single variable: x = val
        if isinstance(target, ast.Name):
            if val.is_tainted:
                # Add propagation step
                rng = self.context.node_to_range(stmt)
                prop_step = self._create_step(
                    kind=TaintStepKind.PROPAGATE,
                    rng=rng,
                    node=stmt,
                    note=f"Taint propagated via assignment to '{target.id}'",
                )
                env[target.id] = TaintValue(
                    is_tainted=True,
                    categories=set(val.categories),
                    path=val.path + [prop_step],
                    sanitized=val.sanitized,
                )
            else:
                # Variable reassigned to constant becomes clean! (Flow-sensitive)
                env[target.id] = TaintValue(
                    is_tainted=False, sanitized=val.sanitized, path=val.path
                )

        # Tuple unpacking: a, b = val
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._assign_target(elt, val, env, stmt)

        # Subscript: d['k'] = val
        elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
            var_name = target.value.id
            if val.is_tainted:
                rng = self.context.node_to_range(stmt)
                prop_step = self._create_step(
                    kind=TaintStepKind.PROPAGATE,
                    rng=rng,
                    node=stmt,
                    note=f"Tainted item assigned into container '{var_name}'",
                )
                orig = env.get(var_name, TaintValue(is_tainted=False))
                env[var_name] = TaintValue(
                    is_tainted=True,
                    categories=set(val.categories),
                    path=(orig.path or val.path) + [prop_step],
                )

    def _evaluate_expression(
        self,
        expr: ast.AST,
        env: dict[str, TaintValue],
        record_sinks: bool = True,
    ) -> TaintValue:
        """Evaluate an AST expression and determine its taint status and provenance."""
        # Constants are clean
        if isinstance(expr, ast.Constant):
            return TaintValue(is_tainted=False)

        # Variables: look up in environment
        if isinstance(expr, ast.Name):
            return env.get(expr.id, TaintValue(is_tainted=False))

        # Binary operations: left + right, format % arg
        if isinstance(expr, ast.BinOp):
            l_val = self._evaluate_expression(expr.left, env, record_sinks=record_sinks)
            r_val = self._evaluate_expression(expr.right, env, record_sinks=record_sinks)
            return self._merge_taint(l_val, r_val, expr, "Tainted concatenation / formatting")

        # JoinedStr (f-strings)
        if isinstance(expr, ast.JoinedStr):
            tainted_parts: list[TaintValue] = []
            sanitized_parts: list[TaintValue] = []
            for part in expr.values:
                p_val = self._evaluate_expression(part, env, record_sinks=record_sinks)
                if p_val.is_tainted:
                    tainted_parts.append(p_val)
                elif p_val.sanitized:
                    sanitized_parts.append(p_val)
            if tainted_parts:
                first = tainted_parts[0]
                rng = self.context.node_to_range(expr)
                prop_step = self._create_step(
                    kind=TaintStepKind.PROPAGATE,
                    rng=rng,
                    node=expr,
                    note="Tainted variable formatted inside f-string",
                )
                return TaintValue(
                    is_tainted=True,
                    categories=set(first.categories),
                    path=first.path + [prop_step],
                )
            if sanitized_parts:
                return TaintValue(is_tainted=False, sanitized=True, path=sanitized_parts[0].path)
            return TaintValue(is_tainted=False)

        # FormattedValue inside f-string
        if isinstance(expr, ast.FormattedValue):
            return self._evaluate_expression(expr.value, env, record_sinks=record_sinks)

        # Subscripts & Slices: val[0], val['key']
        if isinstance(expr, ast.Subscript):
            # Check if this subscript is an untrusted source: e.g. request.args['q'], os.environ['VAR']
            source_check = self._check_untrusted_source(expr)
            if source_check is not None:
                return source_check

            v_val = self._evaluate_expression(expr.value, env, record_sinks=record_sinks)
            if v_val.is_tainted:
                rng = self.context.node_to_range(expr)
                prop_step = self._create_step(
                    kind=TaintStepKind.PROPAGATE,
                    rng=rng,
                    node=expr,
                    note="Subscript access on tainted container",
                )
                return TaintValue(
                    is_tainted=True,
                    categories=set(v_val.categories),
                    path=v_val.path + [prop_step],
                )
            return TaintValue(is_tainted=False)

        # Attribute access: val.attr
        if isinstance(expr, ast.Attribute):
            source_check = self._check_untrusted_source(expr)
            if source_check is not None:
                return source_check

            v_val = self._evaluate_expression(expr.value, env, record_sinks=record_sinks)
            if v_val.is_tainted:
                return v_val
            return TaintValue(is_tainted=False)

        # Function / Method Calls
        if isinstance(expr, ast.Call):
            # 1. Check if the call is an untrusted input SOURCE
            source_val = self._check_untrusted_source(expr)
            if source_val is not None:
                return source_val

            # 2. Check if the call is a SANITIZER
            sanitized_val = self._check_sanitizer(expr, env, record_sinks=record_sinks)
            if sanitized_val is not None:
                return sanitized_val

            # 3. Check if the call is a SINK
            call_name = self._get_attr_name(expr.func)
            if record_sinks:
                self._check_sink(expr, call_name, env)

            # 4. Check standard propagation functions: e.g. .format(), .join()
            if call_name.endswith(".format"):
                args_val = [
                    self._evaluate_expression(a, env, record_sinks=record_sinks) for a in expr.args
                ]
                for a_val in args_val:
                    if a_val.is_tainted:
                        rng = self.context.node_to_range(expr)
                        prop_step = self._create_step(
                            kind=TaintStepKind.PROPAGATE,
                            rng=rng,
                            node=expr,
                            note="Taint propagated via str.format()",
                        )
                        return TaintValue(
                            is_tainted=True,
                            categories=set(a_val.categories),
                            path=a_val.path + [prop_step],
                        )

            if call_name.endswith(".join") and expr.args:
                arg_val = self._evaluate_expression(expr.args[0], env, record_sinks=record_sinks)
                if arg_val.is_tainted:
                    return arg_val

            # 5. Check intra-file function summary
            if call_name in self.function_summaries and expr.args:
                summary = self.function_summaries[call_name]
                for (param_name, returns_taint), arg_expr in zip(summary.items(), expr.args):
                    if returns_taint:
                        arg_val = self._evaluate_expression(
                            arg_expr, env, record_sinks=record_sinks
                        )
                        if arg_val.is_tainted:
                            rng = self.context.node_to_range(expr)
                            prop_step = self._create_step(
                                kind=TaintStepKind.PROPAGATE,
                                rng=rng,
                                node=expr,
                                note=f"Tainted argument flows through function '{call_name}()'",
                            )
                            return TaintValue(
                                is_tainted=True,
                                categories=set(arg_val.categories),
                                path=arg_val.path + [prop_step],
                            )

            return TaintValue(is_tainted=False)

        # Lists, Sets, Tuples, Dicts
        if isinstance(expr, (ast.List, ast.Set, ast.Tuple)):
            for elt in expr.elts:
                val = self._evaluate_expression(elt, env, record_sinks=record_sinks)
                if val.is_tainted:
                    return val
            return TaintValue(is_tainted=False)

        if isinstance(expr, ast.Dict):
            for v in expr.values:
                val = self._evaluate_expression(v, env, record_sinks=record_sinks)
                if val.is_tainted:
                    return val
            return TaintValue(is_tainted=False)

        return TaintValue(is_tainted=False)

    def _check_untrusted_source(self, node: ast.AST) -> TaintValue | None:
        """Check if an AST node corresponds to an untrusted external input source."""
        node_name = self._get_attr_name(node)

        # 1. input() call
        if isinstance(node, ast.Call) and node_name == "input":
            rng = self.context.node_to_range(node)
            step = self._create_step(
                kind=TaintStepKind.SOURCE,
                rng=rng,
                node=node,
                note="User input enters via standard input()",
            )
            return TaintValue(is_tainted=True, categories={"ALL"}, path=[step])

        # 2. sys.argv / sys.stdin.read
        if "sys.argv" in node_name or "sys.stdin" in node_name:
            rng = self.context.node_to_range(node)
            step = self._create_step(
                kind=TaintStepKind.SOURCE,
                rng=rng,
                node=node,
                note=f"Command-line / stream input enters via '{node_name}'",
            )
            return TaintValue(is_tainted=True, categories={"ALL"}, path=[step])

        # 3. os.environ / os.getenv
        if "os.environ" in node_name or "os.getenv" in node_name:
            rng = self.context.node_to_range(node)
            step = self._create_step(
                kind=TaintStepKind.SOURCE,
                rng=rng,
                node=node,
                note=f"Environment variable input enters via '{node_name}'",
            )
            return TaintValue(is_tainted=True, categories={"ALL"}, path=[step])

        # 4. Flask request: request.args, request.form, request.values, request.json, request.headers, etc.
        flask_patterns = (
            "request.args",
            "request.form",
            "request.values",
            "request.json",
            "request.data",
            "request.cookies",
            "request.headers",
            "request.get_json",
        )
        if any(p in node_name for p in flask_patterns):
            rng = self.context.node_to_range(node)
            step = self._create_step(
                kind=TaintStepKind.SOURCE,
                rng=rng,
                node=node,
                note=f"HTTP request parameter enters via '{node_name}'",
            )
            return TaintValue(is_tainted=True, categories={"ALL"}, path=[step])

        # 5. Django: request.GET, request.POST
        if "request.GET" in node_name or "request.POST" in node_name:
            rng = self.context.node_to_range(node)
            step = self._create_step(
                kind=TaintStepKind.SOURCE,
                rng=rng,
                node=node,
                note=f"Django request data enters via '{node_name}'",
            )
            return TaintValue(is_tainted=True, categories={"ALL"}, path=[step])

        # 6. socket.recv
        if "socket.recv" in node_name or ".recv" in node_name:
            rng = self.context.node_to_range(node)
            step = self._create_step(
                kind=TaintStepKind.SOURCE,
                rng=rng,
                node=node,
                note="Network socket data received",
            )
            return TaintValue(is_tainted=True, categories={"ALL"}, path=[step])

        return None

    def _check_sanitizer(
        self,
        call_node: ast.Call,
        env: dict[str, TaintValue],
        record_sinks: bool = True,
    ) -> TaintValue | None:
        """Check if call is a known sanitizer function that clears or neutralizes taint."""
        call_name = self._get_attr_name(call_node.func)
        if not call_node.args:
            return None

        arg_val = self._evaluate_expression(call_node.args[0], env, record_sinks=False)
        is_san = False

        # 1. shlex.quote() -> clears command injection taint
        if call_name in ("shlex.quote", "quote"):
            is_san = True
        # 2. int() / float() casts -> clears all injection taint
        elif call_name in ("int", "float"):
            is_san = True
        # 3. html.escape / markupsafe.escape -> clears XSS taint
        elif call_name in ("html.escape", "markupsafe.escape", "escape", "Markup.escape"):
            is_san = True
        # 4. os.path.basename / secure_filename -> clears path traversal taint
        elif call_name in (
            "os.path.basename",
            "basename",
            "secure_filename",
            "werkzeug.utils.secure_filename",
        ):
            is_san = True

        if is_san:
            san_step = self._create_step(
                kind=TaintStepKind.SANITIZER,
                rng=self.context.node_to_range(call_node),
                node=call_node,
                note=f"Taint sanitized via '{call_name}()'",
            )
            return TaintValue(
                is_tainted=False,
                sanitized=True,
                path=arg_val.path + [san_step] if arg_val.path else [san_step],
            )

        return None

    def _check_sink(
        self,
        call_node: ast.Call,
        call_name: str,
        env: dict[str, TaintValue],
    ) -> None:
        """Inspect if call target is a sensitive security sink receiving tainted data."""
        if not call_node.args:
            return

        arg_val = self._evaluate_expression(call_node.args[0], env, record_sinks=False)

        # (a) Command Injection Sinks
        has_shell_true = any(
            kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in call_node.keywords
        )
        is_cmd_sink = False
        rule_id = "APS-PY-INJ-002"
        if call_name in COMMAND_SINKS:
            is_cmd_sink = True
            rule_id = "APS-PY-INJ-002"
        elif call_name.startswith("subprocess."):
            if has_shell_true:
                is_cmd_sink = True
                rule_id = "APS-PY-INJ-003"
            elif not isinstance(call_node.args[0], (ast.List, ast.Tuple)):
                is_cmd_sink = True
                rule_id = "APS-PY-INJ-003"

        if is_cmd_sink:
            rng = self.context.node_to_range(call_node)
            if arg_val.sanitized:
                self.flows.append(
                    TaintFlow(
                        rule_id=rule_id,
                        sink_range=rng,
                        path=arg_val.path,
                        sanitized=True,
                        message=f"Command parameter sanitized before reaching {call_name}()",
                    )
                )
            elif arg_val.is_tainted:
                sink_step = self._create_step(
                    kind=TaintStepKind.SINK,
                    rng=rng,
                    node=call_node,
                    note=f"Tainted command reaches shell execution sink '{call_name}()'",
                )
                self.flows.append(
                    TaintFlow(
                        rule_id=rule_id,
                        sink_range=rng,
                        path=arg_val.path + [sink_step],
                        sanitized=False,
                        message=f"Command injection confirmed: untrusted data flows into {call_name}()",
                    )
                )

        # (b) Code Execution Sinks: eval, exec
        elif call_name in CODE_SINKS:
            if arg_val.is_tainted and not arg_val.sanitized:
                rng = self.context.node_to_range(call_node)
                sink_step = self._create_step(
                    kind=TaintStepKind.SINK,
                    rng=rng,
                    node=call_node,
                    note=f"Tainted expression reaches dynamic code evaluation sink '{call_name}()'",
                )
                self.flows.append(
                    TaintFlow(
                        rule_id="APS-PY-INJ-001",
                        sink_range=rng,
                        path=arg_val.path + [sink_step],
                        sanitized=False,
                        message=f"Arbitrary code execution confirmed: untrusted data reaches {call_name}()",
                    )
                )

        # (c) SQL Injection Sinks: cursor.execute(query)
        elif any(call_name.endswith(f".{s}") for s in SQL_SINKS) or call_name in SQL_SINKS:
            rng = self.context.node_to_range(call_node)
            is_parameterized = len(call_node.args) >= 2 or any(
                kw.arg == "params" for kw in call_node.keywords
            )
            if is_parameterized or arg_val.sanitized:
                self.flows.append(
                    TaintFlow(
                        rule_id="APS-PY-INJ-004",
                        sink_range=rng,
                        path=arg_val.path,
                        sanitized=True,
                        message="SQL query parameterized or sanitized",
                    )
                )
            elif arg_val.is_tainted:
                sink_step = self._create_step(
                    kind=TaintStepKind.SINK,
                    rng=rng,
                    node=call_node,
                    note="Tainted SQL query reaches database execution sink",
                )
                self.flows.append(
                    TaintFlow(
                        rule_id="APS-PY-INJ-004",
                        sink_range=rng,
                        path=arg_val.path + [sink_step],
                        sanitized=False,
                        message="SQL injection confirmed: dynamic untrusted query executed without parameterization",
                    )
                )

        # (d) Path Traversal Sinks: open, send_file
        elif call_name in PATH_SINKS:
            rng = self.context.node_to_range(call_node)
            if arg_val.sanitized:
                self.flows.append(
                    TaintFlow(
                        rule_id="APS-PY-IO-001",
                        sink_range=rng,
                        path=arg_val.path,
                        sanitized=True,
                        message=f"Path parameter sanitized before reaching {call_name}()",
                    )
                )
            elif arg_val.is_tainted:
                sink_step = self._create_step(
                    kind=TaintStepKind.SINK,
                    rng=rng,
                    node=call_node,
                    note=f"Untrusted path reaches filesystem sink '{call_name}()'",
                )
                self.flows.append(
                    TaintFlow(
                        rule_id="APS-PY-IO-001",
                        sink_range=rng,
                        path=arg_val.path + [sink_step],
                        sanitized=False,
                        message=f"Path traversal confirmed: user input flows into {call_name}() without sanitization",
                    )
                )

        # (e) XSS / SSTI Sinks: render_template_string, Markup
        elif call_name in XSS_SINKS:
            rng = self.context.node_to_range(call_node)
            if arg_val.sanitized:
                self.flows.append(
                    TaintFlow(
                        rule_id="APS-PY-XSS-001",
                        sink_range=rng,
                        path=arg_val.path,
                        sanitized=True,
                        message=f"Template parameter sanitized before reaching {call_name}()",
                    )
                )
            elif arg_val.is_tainted:
                sink_step = self._create_step(
                    kind=TaintStepKind.SINK,
                    rng=rng,
                    node=call_node,
                    note=f"Untrusted string reaches HTML rendering sink '{call_name}()'",
                )
                self.flows.append(
                    TaintFlow(
                        rule_id="APS-PY-XSS-001",
                        sink_range=rng,
                        path=arg_val.path + [sink_step],
                        sanitized=False,
                        message=f"Cross-site scripting / SSTI confirmed: user data flows into {call_name}()",
                    )
                )

        # (f) Insecure Deserialization Sinks: pickle.loads, yaml.load
        elif call_name in DESER_SINKS:
            if arg_val.is_tainted and not arg_val.sanitized:
                rng = self.context.node_to_range(call_node)
                sink_step = self._create_step(
                    kind=TaintStepKind.SINK,
                    rng=rng,
                    node=call_node,
                    note=f"Tainted payload reaches deserialization sink '{call_name}()'",
                )
                rule_id = "APS-PY-DES-002" if "yaml" in call_name else "APS-PY-DES-001"
                self.flows.append(
                    TaintFlow(
                        rule_id=rule_id,
                        sink_range=rng,
                        path=arg_val.path + [sink_step],
                        sanitized=False,
                        message=f"Insecure deserialization confirmed: untrusted data flows into {call_name}()",
                    )
                )

    def _merge_taint(
        self,
        val1: TaintValue,
        val2: TaintValue,
        node: ast.AST,
        note: str,
    ) -> TaintValue:
        """Merge two taint values, preserving propagation history."""
        if not val1.is_tainted and not val2.is_tainted:
            return TaintValue(is_tainted=False, sanitized=val1.sanitized or val2.sanitized)

        source_val = val1 if val1.is_tainted else val2
        rng = self.context.node_to_range(node)
        prop_step = self._create_step(
            kind=TaintStepKind.PROPAGATE,
            rng=rng,
            node=node,
            note=note,
        )
        return TaintValue(
            is_tainted=True,
            categories=set(val1.categories) | set(val2.categories),
            path=source_val.path + [prop_step],
            sanitized=val1.sanitized or val2.sanitized,
        )

    def _clone_taint(self, val: TaintValue) -> TaintValue:
        """Create a deep copy of a TaintValue for branch analysis."""
        return TaintValue(
            is_tainted=val.is_tainted,
            categories=set(val.categories),
            path=list(val.path),
            sanitized=val.sanitized,
        )

    def _get_attr_name(self, node: ast.AST) -> str:
        """Extract full dotted name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            val_name = self._get_attr_name(node.value)
            return f"{val_name}.{node.attr}" if val_name else node.attr
        if isinstance(node, ast.Call):
            return self._get_attr_name(node.func)
        if isinstance(node, ast.Subscript):
            return self._get_attr_name(node.value)
        return ""


def analyze_python_taint(context: RuleContext) -> TaintResult:
    """Entrypoint function for Python AST data-flow taint tracking."""
    analyzer = PythonTaintAnalyzer(context)
    return analyzer.analyze()
