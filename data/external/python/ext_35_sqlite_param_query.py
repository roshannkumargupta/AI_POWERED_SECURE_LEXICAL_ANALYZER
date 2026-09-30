def authenticate_safe(cursor, email: str, pw_hash: str):
    sql = "SELECT * FROM members WHERE email=? AND pw=?"
    cursor.execute(sql, (email, pw_hash))
    return cursor.fetchone()
