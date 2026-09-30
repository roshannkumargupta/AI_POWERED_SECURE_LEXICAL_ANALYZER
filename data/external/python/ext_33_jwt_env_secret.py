import os
def sign_jwt_safe(claims: dict) -> str:
    secret = os.environ.get("JWT_SECRET")
    return f"{claims}.{secret}"
