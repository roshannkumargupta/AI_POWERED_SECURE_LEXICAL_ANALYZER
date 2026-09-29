"""
Simplified web language grammar for testing
Supports: variables, strings, SQL-like queries, basic functions
"""

# Language keywords (web-focused)
KEYWORDS = {
    "abstract", "continue", "for", "new", "switch", "assert", "default", "goto", 
    "package", "synchronized", "boolean", "do", "if", "private", "this", "break", 
    "double", "implements", "protected", "throw", "byte", "else", "import", "public", 
    "throws", "case", "enum", "instanceof", "return", "transient", "catch", "extends", "int", 
    "short", "try", "char", "final", "interface", "static", "void", "class", "finally", "long", 
    "strictfp", "volatile", "const", "float", "native", "super", "while"
}

# Operators
OPERATORS = {
    '+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=',
    '&&', '||', '!', '&', '|'
}

# Delimiters
DELIMITERS = {
    ';', ',', '(', ')', '{', '}', '[', ']', '.', '"', "'"
}

# Token types
TOKEN_TYPES = {
    'KEYWORD': 'KEYWORD',
    'IDENTIFIER': 'IDENTIFIER',
    'STRING': 'STRING',
    'NUMBER': 'NUMBER',
    'OPERATOR': 'OPERATOR',
    'DELIMITER': 'DELIMITER',
    'COMMENT': 'COMMENT',
    'WHITESPACE': 'WHITESPACE'
}