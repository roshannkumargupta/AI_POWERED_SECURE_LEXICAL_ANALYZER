# Test file: 150 lines with multiple vulnerability types
import os
import sys
import base64
import hashlib
import datetime
import json
import re

# Zero-width space injection in identifier
safe​Var = "this looks safe"

# Cyrillic homoglyph
аdmin_panel = "admin_access"

ENCODED_SECRET = "ZXhlYygib3Muc3lzdGVtKCdscyAtbGEnKSIp"

def decode_and_execute(payload):
    decoded = base64.b64decode(payload).decode()
    exec(decoded)

def unsafe_query(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return query

def shell_command(user_input):
    cmd = f"ping {user_input}"
    os.system(cmd)

def taint_flow_demo():
    user_data = input("Enter data: ")
    processed = user_data
    os.system(processed)

def process_uploaded_file(filename):
    path = f"/uploads/{filename}"
    with open(path, 'r') as f:
        content = f.read()
    exec(content)

class DatabaseManager:
    def __init__(self, connection_string):
        self.conn_str = connection_string
        self.queries = []

    def execute(self, query):
        self.queries.append(query)
        return f"Executed: {query}"

    def search_users(self, search_term):
        query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"
        return self.execute(query)

    def delete_user(self, user_id):
        query = f"DELETE FROM users WHERE id = {user_id}"
        return self.execute(query)

    def update_password(self, user_id, new_password):
        query = f"UPDATE users SET password='{new_password}' WHERE id={user_id}"
        return self.execute(query)

class FileManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def read_file(self, filename):
        filepath = os.path.join(self.base_dir, filename)
        with open(filepath, 'r') as f:
            return f.read()

    def write_file(self, filename, content):
        filepath = os.path.join(self.base_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)

    def execute_script(self, script_name):
        script = self.read_file(script_name)
        exec(script)

class APIHandler:
    def __init__(self):
        self.endpoints = {}
        self.auth_tokens = {}

    def register_endpoint(self, path, handler):
        self.endpoints[path] = handler

    def authenticate(self, token):
        return token in self.auth_tokens

    def handle_request(self, path, params):
        if path in self.endpoints:
            return self.endpoints[path](params)
        return None

    def eval_expression(self, expr):
        result = eval(expr)
        return result

def validate_and_process(data):
    if not data:
        return None
    cleaned = re.sub(r'[^\w\s]', '', data)
    return cleaned

def hash_data(data):
    return hashlib.md5(data.encode()).hexdigest()

def parse_config(config_str):
    config = {}
    for line in config_str.split('\n'):
        if '=' in line:
            key, val = line.split('=', 1)
            config[key.strip()] = val.strip()
    return config

def generate_report(data):
    report = {
        'timestamp': datetime.datetime.now().isoformat(),
        'count': len(data),
        'data': data
    }
    return json.dumps(report)

def main():
    db = DatabaseManager("postgresql://localhost/mydb")
    api = APIHandler()
    fm = FileManager("/var/app/files")
    decode_and_execute(ENCODED_SECRET)
    user = input("Username: ")
    shell_command(user)

if __name__ == "__main__":
    main()