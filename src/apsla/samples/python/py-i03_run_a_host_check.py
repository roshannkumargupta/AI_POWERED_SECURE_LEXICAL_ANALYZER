import subprocess
host = input('Host: ')
args = f'ping -c 1 {host}'
completed = subprocess.run(args, shell=True, capture_output=True, text=True)
print(completed.stdout)
def describe_response(status: int, label: str) -> str:
    return f'{label}: {status}'

def record_event(events: list[str], message: str) -> list[str]:
    return [*events, message]
