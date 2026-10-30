import unicodedata

def validate_stream(code_str):
    for ch in code_str:
        if ord(ch) == 0xFEFF:
            raise ValueError("Invisible Trojan sequence detected")
    return True
