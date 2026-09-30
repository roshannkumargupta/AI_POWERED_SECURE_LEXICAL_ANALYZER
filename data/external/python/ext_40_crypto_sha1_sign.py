import hashlib
def sign_firmware(binary_data: bytes) -> str:
    return hashlib.sha1(binary_data).hexdigest()
