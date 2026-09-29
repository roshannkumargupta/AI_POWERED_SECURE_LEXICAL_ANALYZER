"""
Baseline Lexer and Secure Ingestion Pipeline (regex engine)
"""
from __future__ import annotations
import json, logging, os, re, time,unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple
try:
    from W5_6.symbol_table import SymbolTable
except ImportError:
    from symbol_table import SymbolTable

try:
    from W5_6.token_models import (
        SecureToken, TokenType,
        UnicodeProperties, EntropyMetrics, ContextualPatterns, SecurityScore,
    )
except ImportError:
    from token_models import (
        SecureToken, TokenType,
        UnicodeProperties, EntropyMetrics, ContextualPatterns, SecurityScore,
    )

try:
    from W5_6.token_grammar import TokenGrammar, LexerInput
except ImportError:
    from token_grammar import TokenGrammar, LexerInput

def _make_logger(name, log_file=None):
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    lg = logging.getLogger(name)
    lg.setLevel(logging.DEBUG)
    if not lg.handlers:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt); sh.setLevel(logging.INFO)
        lg.addHandler(sh)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(fmt); fh.setLevel(logging.DEBUG)
            lg.addHandler(fh)
    return lg

PYTHON_KEYWORDS = frozenset({
    "False","None","True","and","as","assert","async","await","break","class",
    "continue","def","del","elif","else","except","finally","for","from",
    "global","if","import","in","is","lambda","nonlocal","not","or","pass",
    "raise","return","try","while","with","yield",
})

_TOKEN_SPEC = [
    (TokenType.COMMENT,    r"#[^\n]*"),
    (TokenType.STRING,
     r'(?:r|u|f|b|rb|br|rf|fr)?(?:"""[\s\S]*?"""|'
     r"'''[\s\S]*?'''|"
     r'"[^"\n\\]*(?:\\.[^"\n\\]*)*"|'
     r"'[^'\n\\]*(?:\\.[^'\n\\]*)*')"),
    (TokenType.FLOAT,      r"(?:\d+\.\d*|\.\d+|\d+[eE])[eE]?[+-]?\d*[jJ]?|(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?[jJ]?|\d+[eE][+-]?\d+[jJ]?"),
    (TokenType.INTEGER,    r"(?:0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+|\d+)[jJ]?"),
    (TokenType.IDENTIFIER, r"[a-zA-Z_\u00C0-\uFFFF][a-zA-Z0-9_\u00C0-\uFFFF]*"),
    (TokenType.ASSIGNMENT, r"//=|\*\*=|>>=|<<=|[+\-*/%&|^]=|="),
    (TokenType.COMPARISON, r"==|!=|<=|>=|<|>"),
    (TokenType.BITWISE,    r"<<|>>|[&|^~]"),
    (TokenType.ARITHMETIC, r"\*\*|//|[+\-*/%@]"),
    (TokenType.LPAREN,     r"\("), (TokenType.RPAREN,    r"\)"),
    (TokenType.LBRACKET,   r"\["), (TokenType.RBRACKET,   r"\]"),
    (TokenType.LBRACE,     r"\{"), (TokenType.RBRACE,     r"\}"),
    (TokenType.COMMA,      r","),  (TokenType.COLON,      r":"),
    (TokenType.SEMICOLON,  r";"),  (TokenType.DOT,        r"\."),
    (TokenType.NEWLINE,    r"\n"), (TokenType.WHITESPACE, r"[ \t]+"),
    (TokenType.ERROR,      r"."),
]

_MASTER = re.compile(
    "|".join(f"(?P<T{i}_{tt.name}>{pat})" for i,(tt,pat) in enumerate(_TOKEN_SPEC)),
    re.DOTALL | re.UNICODE,
)

def _regex_tokenise(source):
    line, line_start = 0, 0
    for m in _MASTER.finditer(source):
        raw = m.group(); col = m.start() - line_start
        ttype = TokenType.ERROR
        for key, val in m.groupdict().items():
            if val is not None:
                tname = "_".join(key.split("_")[1:])
                try: ttype = TokenType[tname]
                except KeyError: pass
                break
        if ttype == TokenType.IDENTIFIER and raw in PYTHON_KEYWORDS:
            ttype = TokenType.KEYWORD
        yield ttype, raw, line, col
        nl = raw.count("\n")
        if nl:
            line += nl
            line_start = m.start() + raw.rfind("\n") + 1

class BaselineLexer:
    _SKIP = {TokenType.WHITESPACE}

    def __init__(self, log_file="logs/lexer.log"):
        self.log = _make_logger("BaselineLexer", log_file)
        self.grammar = TokenGrammar()
        self.log.info("BaselineLexer ready (regex engine)")

    def tokenise(self, source, filename="<string>"):
        self.log.debug(f"Tokenising '{filename}' ({len(source)} chars)")
        t0 = time.perf_counter()
        tokens = []
        for ttype, raw, line, col in _regex_tokenise(source):
            if ttype in self._SKIP: continue
            tokens.append(SecureToken(raw_value=raw, token_type=ttype,
                                       line=line, column=col))
        elapsed = time.perf_counter() - t0
        self.log.info(f"'{filename}': {len(tokens)} tokens in {elapsed*1000:.1f} ms")
        return tokens

    def enrich(self, tokens):
        OPENERS = {TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE}
        CLOSERS = {TokenType.RPAREN, TokenType.RBRACKET, TokenType.RBRACE}
        depth, depths = 0, []
        for tok in tokens:
            if tok.token_type in OPENERS:
                depths.append(depth); depth += 1
            elif tok.token_type in CLOSERS:
                depth = max(0, depth-1); depths.append(depth)
            else:
                depths.append(depth)
        for i, tok in enumerate(tokens):
            tok.enrich(stream=tokens, index=i, nesting_depth=depths[i])
        return tokens

@dataclass
class ValidationError:
    error_type: str; token_value: str; line: int; column: int
    message: str; severity: str = "ERROR"
    def to_dict(self):
        return {"error_type":self.error_type,"value":self.token_value,
                "line":self.line,"column":self.column,
                "message":self.message,"severity":self.severity}

class LexerValidator:
    MAX_DEPTH = 10
    MAX_IDENTIFIER_LENGTH=64
    def __init__(self, log_file="logs/validator.log"):
        self.log = _make_logger("LexerValidator", log_file)

    def validate(self, tokens):
        errs = []
        if not tokens:
            errs.append(ValidationError("EMPTY_STREAM","",0,0,
                "Token stream empty — source blank or unparseable"))
            return False, errs
        errs += self._error_tokens(tokens)
        errs += self._detect_number_identifier(tokens)
        errs += self._bracket_balance(tokens)
        errs += self._nesting_depth(tokens)
        errs += self._identifiers(tokens)
        errs += self._security_flags(tokens)
        errs += self._duplicate_identifiers(tokens)
        hard = [e for e in errs if e.severity=="ERROR"]
        return len(hard)==0, errs

    def _error_tokens(self, tokens):
        return [ValidationError("PARSE_ERROR",t.raw_value,t.line,t.column,
                f"Unrecognised token: {t.raw_value!r}")
                for t in tokens if t.token_type in (TokenType.ERROR, TokenType.UNKNOWN)]

    def _detect_number_identifier(self,tokens):
        errors = []
        for i in range(len(tokens)-1):
            if tokens[i].token_type == TokenType.INTEGER and \
                tokens[i+1].token_type == TokenType.IDENTIFIER:
            
                if tokens[i+1].column == tokens[i].column + len(tokens[i].raw_value):
                    errors.append(ValidationError(
                        "INVALID_IDENTIFIER",
                        tokens[i].raw_value + tokens[i+1].raw_value,
                        tokens[i].line,
                        tokens[i].column,
                        "Identifier cannot start with a digit"
                    ))  
        return errors

    def _bracket_balance(self, tokens):
        out, stack = [], []
        PAIRS = {TokenType.RPAREN:TokenType.LPAREN,
                 TokenType.RBRACKET:TokenType.LBRACKET,
                 TokenType.RBRACE:TokenType.LBRACE}
        OPENERS = set(PAIRS.values())
        for tok in tokens:
            if tok.token_type in OPENERS: stack.append(tok)
            elif tok.token_type in PAIRS:
                if not stack or stack[-1].token_type != PAIRS[tok.token_type]:
                    out.append(ValidationError("UNMATCHED_BRACKET",tok.raw_value,
                        tok.line,tok.column,f"Unexpected '{tok.raw_value}'"))
                else: stack.pop()
        for tok in stack:
            out.append(ValidationError("UNCLOSED_BRACKET",tok.raw_value,
                tok.line,tok.column,f"Unclosed '{tok.raw_value}'"))
        return out

    def detect_mixed_script(self,identifier):
        scripts = set()

        for ch in identifier:
            name = unicodedata.name(ch, "")
            if "LATIN" in name:
                scripts.add("LATIN")
            elif "CYRILLIC" in name:
                scripts.add("CYRILLIC")
            elif "GREEK" in name:
                scripts.add("GREEK")

        return len(scripts) > 1

    def _nesting_depth(self, tokens):
        return [ValidationError("DEEP_NESTING",t.raw_value,t.line,t.column,
                f"Depth {t.context.nesting_depth} > max {self.MAX_DEPTH}",severity="WARNING")
                for t in tokens if t.context and t.context.nesting_depth > self.MAX_DEPTH]

    def _identifiers(self, tokens):
        errors = []

        for t in tokens:
            if t.token_type != TokenType.IDENTIFIER:
                continue

            # Identifier length limit
            if len(t.raw_value) > self.MAX_IDENTIFIER_LENGTH:
                errors.append(
                    ValidationError(
                        "IDENTIFIER_TOO_LONG",
                        t.raw_value,
                        t.line,
                        t.column,
                        "Identifier exceeds maximum allowed length"
                    )
                )

        # Non ASCII identifier
            if t.unicode and not t.unicode.is_pure_ascii:
                errors.append(
                    ValidationError(
                        "NON_ASCII_IDENTIFIER",
                        t.raw_value,
                        t.line,
                        t.column,
                        f"Non-ASCII identifier '{t.raw_value!r}' — possible homoglyph"
                    )
                )

        # Mixed script detection
            if self.detect_mixed_script(t.raw_value):
                errors.append(
                    ValidationError(
                        "MIXED_SCRIPT_IDENTIFIER",
                        t.raw_value,
                        t.line,
                        t.column,
                        "Identifier contains mixed Unicode scripts"
                    )
                )

        return errors

    def _security_flags(self, tokens):
        out = []
        for t in tokens:
            if t.security and t.security.is_suspicious:
                sev = "ERROR" if t.security.score>=0.7 else "WARNING"
                out.append(ValidationError("SECURITY_FLAG",t.raw_value,t.line,t.column,
                    f"Score {t.security.score:.2f}: "+", ".join(t.security.reasons),
                    severity=sev))
        return out
    
    def _duplicate_identifiers(self, tokens):
        """Warn when the same name is declared more than once in the same scope."""
        from collections import Counter
        names = [t.raw_value for t in tokens if t.token_type == TokenType.IDENTIFIER]
        counts = Counter(names)
        errors = []
        seen = set()
        for t in tokens:
            if (t.token_type == TokenType.IDENTIFIER
                    and counts[t.raw_value] > 5       # threshold: tweak as needed
                    and t.raw_value not in seen):
                seen.add(t.raw_value)
                errors.append(ValidationError(
                    "HIGH_FREQUENCY_IDENTIFIER",
                    t.raw_value, t.line, t.column,
                    f"Identifier '{t.raw_value}' appears {counts[t.raw_value]}x — possible token stuffing",
                    severity="WARNING"
                ))
        return errors

@dataclass
class IngestionResult:
    filename:str; success:bool
    tokens:List[SecureToken]
    validation_errors:List[ValidationError]
    warnings:List[str]; suspicious_tokens:List[SecureToken]
    metrics:Dict=field(default_factory=dict)
    timestamp:str=field(default_factory=lambda:datetime.utcnow().isoformat())

    def to_dict(self):
        return {"filename":self.filename,"success":self.success,
                "timestamp":self.timestamp,"metrics":self.metrics,
                "summary":{"total_tokens":len(self.tokens),
                           "suspicious_tokens":len(self.suspicious_tokens),
                           "validation_errors":len(self.validation_errors),
                           "warnings":len(self.warnings)},
                "tokens":[t.to_dict() for t in self.tokens],
                "validation_errors":[e.to_dict() for e in self.validation_errors],
                "warnings":self.warnings,
                "suspicious":[t.to_dict() for t in self.suspicious_tokens]}

    def to_json(self,indent=2):
        return json.dumps(self.to_dict(),indent=indent,ensure_ascii=False)

    def save(self,path):
        with open(path,"w",encoding="utf-8") as f: f.write(self.to_json())

class SecureIngestionPipeline:
    def __init__(self, output_dir="results", log_file="logs/pipeline.log"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log       = _make_logger("Pipeline", log_file)
        self.lexer     = BaselineLexer(log_file=log_file)
        self.validator = LexerValidator(log_file=log_file)
        self.log.info(f"Pipeline ready -> {self.output_dir}")
        self.symbol_table = SymbolTable()

    def process_string(self, source, filename="<string>"):
        return self._run(LexerInput.from_string(source, filename))

    def process_file(self, path):
        try: li = LexerInput.from_file(path)
        except (FileNotFoundError, ValueError) as e:
            return self._err(path, str(e))
        return self._run(li)

    def process_directory(self, directory):
        results = [self.process_file(str(f)) for f in Path(directory).rglob("*.py")]
        self.log.info(f"Directory scan: {len(results)} files")
        return results

    def _run(self, li):
        t0 = time.perf_counter(); warnings = []
        self.symbol_table = SymbolTable()
        ok, iw = li.validate()
        warnings.extend(iw)
        if not ok: return self._err(li.filename,"Input validation failed")
        #try : tokens = self.lexer.tokenise(li.source_code, li.filename)
        try :
            tokens = self.lexer.tokenise(li.source_code, li.filename)
            self.symbol_table.build_from_tokens(tokens) #build symbol table

        except Exception as e: return self._err(li.filename, str(e))

        tokens  = self.lexer.enrich(tokens)
        passed, val_errors = self.validator.validate(tokens)

        suspicious = [t for t in tokens if t.security and t.security.is_suspicious]

        elapsed = time.perf_counter() - t0
        metrics = self._metrics(tokens, elapsed, li)

        r = IngestionResult(li.filename, passed, tokens, val_errors,
                            warnings, suspicious, metrics)
        
        out = self.output_dir / (Path(li.filename).stem + "_lexer_output.json")
        r.save(str(out))

        # save symbol table
        sym_path = self.output_dir / (Path(li.filename).stem + "_symbols.txt")
        self.symbol_table.save(str(sym_path))
        return r

    def _metrics(self, tokens, elapsed, li):
        dist = {}
        for t in tokens: dist[t.token_type.name] = dist.get(t.token_type.name,0)+1
        entr = sum(t.entropy.char_entropy for t in tokens if t.entropy) / max(len(tokens),1)
        return {"total_tokens":len(tokens),"token_type_dist":dist,
                "source_lines":li.source_code.count("\n")+1,
                "source_bytes":len(li.source_code.encode()),
                "elapsed_ms":round(elapsed*1000,2),
                "tokens_per_second":round(len(tokens)/max(elapsed,1e-9)),
                "avg_char_entropy":round(entr,4),
                "suspicious_count":sum(1 for t in tokens if t.security and t.security.is_suspicious),
                "error_token_count":dist.get("ERROR",0)}

    def _err(self, filename, msg):
        return IngestionResult(filename, False, [],
            [ValidationError("PIPELINE_ERROR","",0,0,msg)], [], [], {})


# ═══════════════════════════════════════════════════════════════
# SIMPLE OUTPUT FORMAT EXTENSION (ADD TO END OF lexer.py)
# ═══════════════════════════════════════════════════════════════

class SimpleLexerOutput:
    """
    Provides simple text-based output format.
    Format: ERROR at {position}: {type}: {value} (Entropy={entropy}, Valid={valid})
    
    This class wraps the comprehensive IngestionResult and produces
    a simplified output format for easier reading and compatibility
    with basic text processing tools.
    """

    BASE64_PATTERN = re.compile(r'^[A-Za-z0-9+/]+={0,2}$')

    SQLI_PATTERN = re.compile(
        r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|FROM|WHERE)\b",
        re.IGNORECASE
    )

    CMD_INJECTION_PATTERN = re.compile(
        r"\b(rm\s+-rf|wget|curl|chmod|chown|bash|sh|nc|netcat|powershell)\b",
        re.IGNORECASE
    )
    
    def __init__(self, ingestion_result: IngestionResult):
        """
        Initialize with an IngestionResult from the pipeline.
        
        Args:
            ingestion_result: Result from SecureIngestionPipeline
        """
        self.result = ingestion_result
        self.log = _make_logger("SimpleOutput", log_file=None)
    
    def to_simple_format(self, show_all: bool = False) -> str:
        """
        Generate simple text output.
        """
        lines = []
        reported = set()

    # validator errors (e.g. 9abc)
        for err in self.result.validation_errors:
            key = (err.column, err.token_value)

            if key not in reported:
                lines.append(
                    f"ERROR at {err.column}: {err.error_type}: {err.token_value} ({err.message})"
                )
                reported.add(key)

    # token validation errors
        for token in self.result.tokens:

            is_valid = self._is_token_valid(token)

            if not is_valid or show_all:

                key = (token.column, token.raw_value)

                if key not in reported:

                    entropy = (
                        f"{token.entropy.char_entropy:.3f}"
                        if token.entropy else "None"
                    )
                    token_value=token.raw_value.encode("unicode_escape").decode()
                    lines.append(
                        f"ERROR at {token.column}: {token.token_type.name}: "
                        f"{token_value} (Entropy={entropy}, Valid={is_valid})"
                    )

                    reported.add(key)

        return "\n".join(lines) if lines else "(No errors detected)"
   
    def _looks_like_base64(self, value: str) -> bool:
        """
        Heuristic detection for Base64-encoded payloads.
        """
        if len(value) < 20:     # avoid flagging small normal strings
            return False

        if not self.BASE64_PATTERN.match(value):
            return False

        return True
    
    def _looks_like_sql_injection(self, value: str) -> bool:
        """
        Detect possible SQL injection payloads.
        """
        if self.SQLI_PATTERN.search(value):
            return True
        return False
    
    def _looks_like_command_injection(self, value: str) -> bool:
        """
        Detect possible command injection payloads.
        """
        if self.CMD_INJECTION_PATTERN.search(value):
            return True
        return False
    
    def _is_token_valid(self, token: SecureToken) -> bool:

        if token.token_type not in (
            TokenType.IDENTIFIER,
            TokenType.STRING,
            TokenType.COMMENT
        ):  
            return True

    # IDENTIFIER RULES
        if token.token_type == TokenType.IDENTIFIER:
            if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', token.raw_value):
                return False

            if token.unicode and not token.unicode.is_pure_ascii:
                return False
            
        if token.token_type == TokenType.IDENTIFIER:
            value = token.raw_value
            if len(value) > 15:
                digit_ratio = sum(c.isdigit() for c in value) / len(value)
                if digit_ratio > 0.2:
                    return False

    # STRING RULES
        if token.token_type == TokenType.STRING:

        # control characters
            if re.search(r'\\x[0-1][0-9A-Fa-f]', token.raw_value):
                    return False
            
            for char in token.raw_value:
                if ord(char) < 32 and char not in ('\t','\n','\r'):
                    return False

        # detect actual filesystem paths
            if re.search(r"(\/[A-Za-z0-9_\-\.]+)+", token.raw_value):
                return False
            
            value = token.raw_value.strip('"\'')
            if self._looks_like_base64(value):
                return False
            
            if self._looks_like_sql_injection(value):
                return False
            
            if self._looks_like_command_injection(value):
                return False

    # ENTROPY CHECK (only for long identifiers)
        if token.entropy and token.entropy.char_entropy > 4.2:
            if token.token_type == TokenType.IDENTIFIER and len(token.raw_value) > 20:
                return False

    # SECURITY SCORE
        if token.security and token.security.score > 0.8:
            return False

        return True


    def _format_token_line(self, token: SecureToken, entropy: float, is_valid: bool) -> str:
        """
        Format a single token line.
        
        Format: ERROR at {position}: {type}: {value} (Entropy={entropy}, Valid={valid})
        
        Args:
            token: SecureToken to format
            entropy: Calculated entropy value
            is_valid: Whether token passed validation
        
        Returns:
            Formatted string
        """
        position = token.column
        token_type = token.token_type.name
        value = repr(token.raw_value) #to print raw control chars
        
        # Use "ERROR" prefix for invalid tokens, "TOKEN" for valid ones
        prefix = "TOKEN" if is_valid else "ERROR"
        
        return f"{prefix} at {position}: {token_type}: {value} (Entropy={entropy:.3f}, Valid={is_valid})"
    
    def save_simple_format(self, path: str, show_all: bool = False):
        """
        Save simple format to a text file.
        
        Args:
            path: Output file path
            show_all: If True, save all tokens. If False, only invalid tokens.
        """
        output = self.to_simple_format(show_all=show_all)
        with open(path, "w", encoding="utf-8") as f:
            f.write(output)
        self.log.info(f"Simple output saved to {path}")
    
    def print_summary(self):
        """Print a summary of validation results."""
        total_tokens = len(self.result.tokens)
        reported=set()
        
        for err in self.result.validation_errors:
            reported.add((err.column,err.token_value))

        for token in self.result.tokens:
            if not self._is_token_valid(token):
                reported.add((token.column,token.raw_value))

        invalid_count = len(reported)

        
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total tokens:     {total_tokens}")
        print(f"Invalid tokens:   {invalid_count}")
        print(f"Valid tokens:     {total_tokens - invalid_count}")
        print(f"Success:          {'Yes' if invalid_count == 0 else 'No'}")
        print(f"{'='*60}\n")


# Add convenience method to SecureIngestionPipeline
def _add_simple_output_method():
    """Monkey-patch to add simple output method to pipeline."""
    
    def get_simple_output(self, result: IngestionResult) -> SimpleLexerOutput:
        """
        Get SimpleLexerOutput wrapper for an IngestionResult.
        
        Args:
            result: IngestionResult from process_string/process_file
        
        Returns:
            SimpleLexerOutput instance
        """
        return SimpleLexerOutput(result)
    
    SecureIngestionPipeline.get_simple_output = get_simple_output

_add_simple_output_method()