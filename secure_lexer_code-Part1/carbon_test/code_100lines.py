# Test file: 100 lines with taint flow + base64 vulnerability
import os
import sys
import base64
import hashlib
import datetime

SECRET_KEY = "aGVsbG8gd29ybGQ="

def decode_payload(encoded):
    return base64.b64decode(encoded).decode('utf-8')

def get_user_input():
    user_cmd = input("Enter command: ")
    return user_cmd

def execute_user_command(cmd):
    os.system(cmd)

def process_template(template, data):
    for key, value in data.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template

def validate_json(json_string):
    import json
    try:
        parsed = json.loads(json_string)
        return True, parsed
    except json.JSONDecodeError as e:
        return False, str(e)

def encrypt_data(data, key):
    from itertools import cycle
    return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(data, cycle(key)))

def read_environment():
    api_key = os.environ.get('API_KEY', '')
    db_url  = os.environ.get('DATABASE_URL', '')
    return api_key, db_url

def send_request(url, data):
    import urllib.request
    import json
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, payload)
    return req

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.settings = {}

    def load(self):
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        self.settings[k.strip()] = v.strip()
        except FileNotFoundError:
            pass

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = str(value)

    def save(self):
        with open(self.config_file, 'w') as f:
            for k, v in self.settings.items():
                f.write(f"{k} = {v}\n")

class SecurityLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        self.entries = []

    def log(self, event, severity="INFO"):
        timestamp = datetime.datetime.now().isoformat()
        entry = {"time": timestamp, "event": event, "severity": severity}
        self.entries.append(entry)

    def get_critical(self):
        return [e for e in self.entries if e["severity"] == "CRITICAL"]

    def export(self):
        import json
        return json.dumps(self.entries, indent=2)

def taint_example():
    user_input = input("Enter your name: ")
    cmd = user_input
    os.system(cmd)

def sql_example(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

def main():
    config = ConfigManager("config.ini")
    config.load()
    logger = SecurityLogger("security.log")
    logger.log("Application started")
    taint_example()

if __name__ == "__main__":
    main()