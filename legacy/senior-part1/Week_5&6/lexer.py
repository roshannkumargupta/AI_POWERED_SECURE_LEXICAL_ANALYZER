from token_spec import master_pattern
from secure_token import SecureToken

def tokenize(code):
    tokens = []
    line_no = 1

    for match in master_pattern.finditer(code):
        type_ = match.lastgroup
        value = match.group()

        if type_ == "WHITESPACE":
            continue

        token = SecureToken(type_, value, match.start())
        tokens.append(token)

    return tokens
