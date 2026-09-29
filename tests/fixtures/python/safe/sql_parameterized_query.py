user_id = 42
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
