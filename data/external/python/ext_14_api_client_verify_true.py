import requests
def fetch_status(endpoint: str) -> dict:
    resp = requests.get(endpoint, timeout=10, verify=True)
    return resp.json()
