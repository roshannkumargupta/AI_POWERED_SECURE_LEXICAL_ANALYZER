import os
from flask import Flask, request
app = Flask(__name__)

@app.get('/diagnose')
def diagnose():
    if request.args.get('remote'):
        target = request.args.get('host', '')
    else:
        target = '127.0.0.1'
    command = 'echo ' + target
    os.system(command)
    return 'done'
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
