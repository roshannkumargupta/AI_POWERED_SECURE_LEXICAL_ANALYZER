import markupsafe
def build_welcome_banner(user_name: str) -> markupsafe.Markup:
    return markupsafe.Markup("<h1>Welcome, " + user_name + "</h1>")
