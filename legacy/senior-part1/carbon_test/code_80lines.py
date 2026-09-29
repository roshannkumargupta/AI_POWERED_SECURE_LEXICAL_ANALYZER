# Test file: 80 lines with homoglyph + exec vulnerability
import os
import sys

def parse_config(filename):
    config = {}
    with open(filename, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key.strip()] = value.strip()
    return config

def validate_input(data):
    if not isinstance(data, str):
        return False
    if len(data) > 1000:
        return False
    return True

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def connect_database(host, port, name):
    connection_string = f"postgresql://{host}:{port}/{name}"
    return connection_string

def log_event(event_type, message, level="INFO"):
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{level}] {event_type}: {message}"
    return log_entry

# Homoglyph attack: Cyrillic 'а' looks like Latin 'a'
аdmin = "attacker_controlled"

def execute_command(cmd):
    exec(cmd)

def process_query(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

def sanitize_string(text):
    dangerous_chars = ['<', '>', '&', '"', "'"]
    for char in dangerous_chars:
        text = text.replace(char, '')
    return text

class UserManager:
    def __init__(self):
        self.users = {}

    def add_user(self, username, password):
        hashed = hash_password(password)
        self.users[username] = hashed

    def verify_user(self, username, password):
        if username in self.users:
            hashed = hash_password(password)
            return self.users[username] == hashed
        return False

    def get_all_users(self):
        return list(self.users.keys())

    def delete_user(self, username):
        if username in self.users:
            del self.users[username]
            return True
        return False

def calculate_metrics(data):
    if not data:
        return {}
    return {
        'count': len(data),
        'sum': sum(data),
        'average': sum(data) / len(data),
        'max': max(data),
        'min': min(data)
    }

def main():
    manager = UserManager()
    manager.add_user("alice", "password123")
    print(calculate_metrics([1, 2, 3, 4, 5]))

if __name__ == "__main__":
    main()