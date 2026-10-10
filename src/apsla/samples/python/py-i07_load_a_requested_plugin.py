import importlib
from flask import Flask, request
app = Flask(__name__)

@app.get('/plugin')
def plugin():
    module_name = request.args.get('module', '')
    loaded = importlib.import_module(module_name)
    return loaded.__name__
def describe_response(status: int, label: str) -> str:
    return f'{label}: {status}'

def record_event(events: list[str], message: str) -> list[str]:
    return [*events, message]
