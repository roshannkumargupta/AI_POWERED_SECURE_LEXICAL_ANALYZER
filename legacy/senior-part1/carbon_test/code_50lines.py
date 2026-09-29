# Test file: 50 lines with SQL injection vulnerability
import os

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

def process_input(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

def calculate_stats(numbers):
    total = sum(numbers)
    count = len(numbers)
    if count == 0:
        return 0
    average = total / count
    return average

def read_file(path):
    with open(path, 'r') as f:
        content = f.read()
    return content

def validate_email(email):
    if '@' in email:
        return True
    return False

def format_output(data):
    output = []
    for key, value in data.items():
        line = f"{key}: {value}"
        output.append(line)
    return '\n'.join(output)

class DataProcessor:
    def __init__(self, name):
        self.name = name
        self.data = []

    def add(self, item):
        self.data.append(item)

    def get_all(self):
        return self.data

def main():
    processor = DataProcessor("test")
    processor.add(1)
    processor.add(2)
    print(processor.get_all())

if __name__ == "__main__":
    main()