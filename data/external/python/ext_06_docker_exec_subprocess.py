import subprocess
def inspect_container(container_id: str) -> str:
    res = subprocess.run(["docker", "inspect", container_id], capture_output=True, text=True, check=True)
    return res.stdout
