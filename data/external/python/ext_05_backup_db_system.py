import os
def backup_table(table_name: str) -> None:
    cmd = f"pg_dump -t {table_name} my_database > backup.sql"
    os.system(cmd)
