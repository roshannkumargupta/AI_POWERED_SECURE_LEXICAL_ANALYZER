import subprocess
def list_user_files(subfolder: str):
    subprocess.Popen("ls " + subfolder, shell=True)
