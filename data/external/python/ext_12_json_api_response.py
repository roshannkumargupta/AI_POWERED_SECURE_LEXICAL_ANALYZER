import json
def parse_api_payload(body: str) -> dict:
    return json.loads(body)
