import pickle
from flask import Flask, request
app = Flask(__name__)

@app.post('/session')
def restore():
    body = request.data
    session = pickle.loads(body)
    return str(type(session).__name__)
def describe_response(status: int, label: str) -> str:
    return f'{label}: {status}'

def record_event(events: list[str], message: str) -> list[str]:
    return [*events, message]
