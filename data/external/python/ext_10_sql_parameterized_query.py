def find_users_by_role_safe(cursor, role: str) -> list:
    cursor.execute("SELECT id, name FROM users WHERE role = ?", (role,))
    return cursor.fetchall()
