import pickle
def load_session_cookie(raw_cookie_bytes: bytes) -> dict:
    return pickle.loads(raw_cookie_bytes)
