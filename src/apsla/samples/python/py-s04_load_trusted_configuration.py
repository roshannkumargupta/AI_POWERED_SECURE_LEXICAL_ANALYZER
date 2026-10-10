import hashlib
import secrets
import requests
import yaml

def load_settings(stream):
    return yaml.safe_load(stream)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def token() -> str:
    return secrets.token_hex(24)

def fetch() -> int:
    return requests.get('https://example.invalid/', timeout=2).status_code
