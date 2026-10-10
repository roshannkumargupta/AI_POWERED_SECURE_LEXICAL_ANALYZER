import sqlite3
name = input('Name: ')
conn = sqlite3.connect(':memory:')
conn.execute("SELECT * FROM users WHERE name='" + name + "'")
