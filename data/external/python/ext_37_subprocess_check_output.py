import subprocess
def search_system_logs_safe(pattern: str) -> str:
    out = subprocess.check_output(["grep", pattern, "/var/log/syslog"], text=True)
    return out
