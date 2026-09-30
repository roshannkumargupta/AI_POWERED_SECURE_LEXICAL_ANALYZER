import ast
def parse_literal_config(raw_text: str) -> dict:
    return ast.literal_eval(raw_text)
