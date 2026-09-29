import re
from collections import namedtuple
from .grammar import KEYWORDS, OPERATORS, DELIMITERS, TOKEN_TYPES

Token = namedtuple('Token', ['type', 'value', 'line', 'column'])

class SimpleTokenizer:
    """Basic tokenizer without ML integration"""
    
    def __init__(self):
        # Define token patterns (simplified)
        self.patterns = [
            (TOKEN_TYPES['COMMENT'], r'//.*'),       # Java comments
            (TOKEN_TYPES['COMMENT'], r'/\*[\s\S]*?\*/'),     # Java multiline comments
            (TOKEN_TYPES['STRING'], r'"[^"]*"'),    # Double quoted strings
            (TOKEN_TYPES['STRING'], r"'[^']*'"),    # Single quoted strings   
            (TOKEN_TYPES['NUMBER'], r'\d+\.?\d*'),  # Numbers
            (TOKEN_TYPES['OPERATOR'], r'[+\-*/=<>!&|]+'),  # Operators
            (TOKEN_TYPES['DELIMITER'], r'[();{},.]'),     # Delimiters
            (TOKEN_TYPES['WHITESPACE'], r'\s+'),          # Whitespace
            (TOKEN_TYPES['IDENTIFIER'], r'[a-zA-Z_][a-zA-Z0-9_]*'),  # Identifiers
        ]
        
        # Compile regex patterns
        self.regex_patterns = [(name, re.compile(pattern)) 
                              for name, pattern in self.patterns]
    
    def tokenize(self, code):
        """Convert code string into tokens"""
        tokens = []
        line_num = 1
        line_start = 0
        
        i = 0
        while i < len(code):
            # Track position
            line = line_num
            column = i - line_start + 1
            
            # Try each pattern
            matched = False
            for token_type, regex in self.regex_patterns:
                match = regex.match(code, i)
                if match:
                    value = match.group(0)      # Returns the part which matched
                    
                    # Skip whitespace and comments
                    if token_type not in [TOKEN_TYPES['WHITESPACE']] and token_type not in [TOKEN_TYPES['COMMENT']]:
                        # Check if identifier is actually a keyword
                        if token_type == TOKEN_TYPES['IDENTIFIER']:
                            if value in KEYWORDS or value.upper() in KEYWORDS:
                                token_type = TOKEN_TYPES['KEYWORD']
                        
                        tokens.append(Token(token_type, value, line, column))
                    
                    # Update line tracking
                    if '\n' in value:
                        line_num += value.count('\n')
                        line_start = i + value.rfind('\n') + 1
                    
                    i = match.end()
                    matched = True
                    break
            
            if not matched:
                # No pattern matched - skip character
                i += 1
        
        return tokens