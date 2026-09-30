import os
def get_report(user_filename: str) -> str:
    path = "/var/reports/" + user_filename
    with open(path, "r") as f:
        return f.read()
