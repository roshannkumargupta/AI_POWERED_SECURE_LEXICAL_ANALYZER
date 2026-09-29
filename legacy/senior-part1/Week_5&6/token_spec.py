import re

TOKEN_SPECIFICATION = [
    ('NUMBER',      r'\d+'),
    ('IDENTIFIER',  r'[A-Za-z_][A-Za-z0-9_]*'),
    ('STRING',      r'"[^"\n]*"'),
    ('OPERATOR',    r'[+\-*/=]'),
    ('DELIMITER',   r'[;,(){}]'),
    ('WHITESPACE',  r'\s+'),
    ('UNKNOWN',     r'.'),
]

master_pattern = re.compile('|'.join(
    f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION
))
