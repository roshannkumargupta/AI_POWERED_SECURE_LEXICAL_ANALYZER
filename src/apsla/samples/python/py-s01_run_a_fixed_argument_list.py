import subprocess

def list_directory(path: str) -> str:
    result = subprocess.run(['ls', '-l', path], check=True, capture_output=True, text=True)
    return result.stdout
