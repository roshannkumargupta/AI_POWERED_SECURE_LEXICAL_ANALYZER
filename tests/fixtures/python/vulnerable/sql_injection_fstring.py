user = input()
cursor.execute(f"SELECT * FROM accounts WHERE name = '{user}'")
