import hashlib
def sign_firmware_safe(binary_data: bytes) -> str:
    return hashlib.sha256(binary_data).hexdigest()
