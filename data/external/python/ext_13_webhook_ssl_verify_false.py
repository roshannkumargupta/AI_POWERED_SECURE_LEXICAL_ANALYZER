import requests
def dispatch_webhook(url: str, data: dict) -> int:
    resp = requests.post(url, json=data, verify=False)
    return resp.status_code
