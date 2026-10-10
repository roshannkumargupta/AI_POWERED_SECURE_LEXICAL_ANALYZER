import os
import shlex

def show_term(user: str) -> None:
    quoted = shlex.quote(user)
    os.system('echo ' + quoted)
