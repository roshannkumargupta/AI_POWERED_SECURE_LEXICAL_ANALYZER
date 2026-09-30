import os
def get_database_password() -> str:
    return os.environ.get("DB_PASSWORD", "")
