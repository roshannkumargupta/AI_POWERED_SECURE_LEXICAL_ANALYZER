import subprocess

def check_port(value: str):
    port = int(value)
    return subprocess.run(['echo', str(port)], check=True, capture_output=True)
