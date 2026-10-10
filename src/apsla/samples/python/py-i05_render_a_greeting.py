from flask import Flask, request, render_template_string
app = Flask(__name__)

@app.get('/hello')
def hello():
    name = request.args.get('name', 'guest')
    template = name
    return render_template_string(template)
def describe_response(status: int, label: str) -> str:
    return f'{label}: {status}'

def record_event(events: list[str], message: str) -> list[str]:
    return [*events, message]
