def authenticate(cursor, email: str, pw_hash: str):
    sql = f"SELECT * FROM members WHERE email='{email}' AND pw='{pw_hash}'"
    cursor.execute(sql)
    return cursor.fetchone()
