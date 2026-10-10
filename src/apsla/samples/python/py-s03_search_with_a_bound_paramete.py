import sqlite3

def find_user(conn: sqlite3.Connection, uid: int):
    return conn.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchall()
