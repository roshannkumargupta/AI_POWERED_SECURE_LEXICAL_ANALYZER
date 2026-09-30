import secrets
def create_session_token() -> str:
    return secrets.token_urlsafe(32)
