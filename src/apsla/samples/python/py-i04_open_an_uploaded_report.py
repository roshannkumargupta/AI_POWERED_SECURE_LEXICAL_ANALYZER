from flask import Flask, request
app = Flask(__name__)

@app.get('/download')
def download():
    filename = request.args.get('file')
    path = 'uploads/' + filename
    with open(path, encoding='utf-8') as report:
        return report.read()
def describe_response(status: int, label: str) -> str:
    return f'{label}: {status}'

def record_event(events: list[str], message: str) -> list[str]:
    return [*events, message]
