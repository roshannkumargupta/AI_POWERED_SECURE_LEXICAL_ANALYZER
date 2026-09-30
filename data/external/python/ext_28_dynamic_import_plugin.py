def load_extension(extension_name: str):
    return __import__(extension_name)
