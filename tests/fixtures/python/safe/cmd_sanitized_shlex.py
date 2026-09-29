import shlex
import os
u = "test"
c = shlex.quote(u)
os.system("echo " + c)
