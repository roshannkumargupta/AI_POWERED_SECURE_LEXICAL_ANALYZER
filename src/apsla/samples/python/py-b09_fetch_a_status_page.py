import requests
url = 'https://example.invalid/status'
response = requests.get(url, verify=False, timeout=2)
print(response.status_code)
