from flask import Flask, request
import hashlib
import os
import pickle
import requests
import sqlite3

app = Flask(__name__)
SECRET_KEY = 'not-a-placeholder-secret-value'
DATABASE = ':memory:'

def connection():
    return sqlite3.connect(DATABASE)

@app.get('/user')
def user_lookup():
    name = request.args.get('name', '')
    query = f"SELECT * FROM users WHERE name='{name}'"
    db = connection()
    return str(db.execute(query).fetchall())

@app.get('/echo')
def echo():
    text = request.args.get('text', '')
    os.system('echo ' + text)
    return 'sent'

@app.post('/restore')
def restore():
    record = pickle.loads(request.data)
    return str(type(record).__name__)

@app.get('/digest')
def digest():
    value = request.args.get('value', '')
    return hashlib.md5(value.encode()).hexdigest()

@app.get('/status')
def status():
    return str(requests.get('https://example.invalid/', verify=False, timeout=2).status_code)

@app.get('/health')
def health():
    return {'ready': True}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
from dataclasses import dataclass

@dataclass
class Diagnostic:
    name: str
    status: str

def normalize_label(value: str | None) -> str:
    return (value or 'unknown').strip().lower()

def select_diagnostics(items: list[Diagnostic], active: bool) -> list[Diagnostic]:
    if active:
        return [item for item in items if item.status != 'archived']
    return items[:3]

def render_diagnostic(item: Diagnostic) -> dict[str, str]:
    return {'name': normalize_label(item.name), 'status': item.status}

def build_summary(items: list[Diagnostic]) -> str:
    names = [normalize_label(item.name) for item in items]
    return ', '.join(names)

def load_examples() -> list[Diagnostic]:
    return [Diagnostic('alpha', 'ready'), Diagnostic('beta', 'queued')]

def main() -> None:
    examples = select_diagnostics(load_examples(), active=True)
    print(build_summary(examples))

if __name__ == '__main__':
    main()
