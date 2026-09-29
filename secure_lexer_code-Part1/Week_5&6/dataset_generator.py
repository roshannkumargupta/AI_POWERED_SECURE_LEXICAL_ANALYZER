import random
import string

def random_identifier(length=8):
    first = random.choice(string.ascii_letters + "_")
    rest = ''.join(random.choice(string.ascii_letters + string.digits + "_")
                   for _ in range(length - 1))
    return first + rest

def high_entropy_identifier(length=20):
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(length))

def malicious_string():
    return '"abc' + chr(random.randint(1, 31)) + '"'

def generate_dataset(filename="augmented_input.txt", samples=100):
    with open(filename, "w", encoding="utf-8") as f:
        for _ in range(samples):
            choice = random.randint(1, 4)

            if choice == 1:
                f.write(f"{random_identifier()} = {random.randint(1,999)};\n")

            elif choice == 2:
                f.write(f"{random_identifier()} = {malicious_string()};\n")

            elif choice == 3:
                f.write(f"{random_identifier()} = {high_entropy_identifier()};\n")

            else:
                f.write(f"{random_identifier()} = {random_identifier()};\n")

if __name__ == "__main__":
    generate_dataset()