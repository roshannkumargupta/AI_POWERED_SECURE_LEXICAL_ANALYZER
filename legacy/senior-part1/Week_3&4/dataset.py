malicious_tokens = [
    "OR 1=1",
    "DROP TABLE",
    "UNION SELECT",
    "<script>",
    "eval(",
    "exec(",
    "rm -rf",
    "--",
    "shutdown",
    "reboot",
    "sudo",
    "chmod 777",
    "/etc/passwd",
    "C:\Windows\System32",
    "bash"
]

safe_tokens = [
    "int", "float", "return", "if", "else",
    "for", "while", "printf", "main","switch",
    "printf","scanf","struct",";","=","var", "let", "const", "function", "console", "log",
    "document", "window", "length", "true", "false", "null",
    "username", "password", "email", "count", "total",
    "index", "i", "j", "k", "sum", "list", "array"
]

X = malicious_tokens + safe_tokens
y = [1]*len(malicious_tokens) + [0]*len(safe_tokens)
