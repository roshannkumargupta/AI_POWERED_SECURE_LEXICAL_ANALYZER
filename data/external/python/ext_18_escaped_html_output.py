import markupsafe
def build_safe_welcome(user_name: str) -> str:
    escaped = markupsafe.escape(user_name)
    return f"<h1>Welcome, {escaped}</h1>"
