import os
def get_safe_report(user_filename: str) -> str:
    safe_name = os.path.basename(user_filename)
    path = os.path.join("/var/reports", safe_name)
    with open(path, "r") as f:
        return f.read()
