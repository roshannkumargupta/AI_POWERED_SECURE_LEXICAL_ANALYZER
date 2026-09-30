import os
def search_system_logs(pattern: str) -> str:
    pipe = os.popen("grep " + pattern + " /var/log/syslog")
    return pipe.read()
