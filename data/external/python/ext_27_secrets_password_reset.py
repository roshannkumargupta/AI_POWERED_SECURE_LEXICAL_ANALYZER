import secrets
def generate_safe_pin() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))
