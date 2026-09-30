import base64
def run_bootstrap():
    encoded = "cHJpbnQoJ2hlbGxvIHdvcmxkJyk="
    exec(base64.b64decode(encoded))
