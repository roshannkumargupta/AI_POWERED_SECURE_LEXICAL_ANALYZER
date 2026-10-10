from flask import Flask, request
import sqlite3
app = Flask(__name__)

@app.get('/search')
def search():
    name = request.args.get('name', '')
    query = f"SELECT * FROM accounts WHERE name = '{name}'"
    db = sqlite3.connect(':memory:')
    return str(db.execute(query).fetchall())
def describe_response(status: int, label: str) -> str:
    return f'{label}: {status}'

def record_event(events: list[str], message: str) -> list[str]:
    return [*events, message]
