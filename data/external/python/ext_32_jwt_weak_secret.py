def sign_jwt(claims: dict) -> str:
    secret = "secret"
    return f"{claims}.{secret}"
