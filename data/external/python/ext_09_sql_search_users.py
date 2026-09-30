def find_users_by_role(cursor, role: str) -> list:
    query = "SELECT id, name FROM users WHERE role = '" + role + "'"
    cursor.execute(query)
    return cursor.fetchall()
