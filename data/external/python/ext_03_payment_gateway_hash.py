import hashlib
def verify_payment_signature(tx_id: str, secret: str) -> str:
    raw = f"{tx_id}:{secret}"
    return hashlib.md5(raw.encode()).hexdigest()
