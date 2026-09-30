import random
def generate_pin() -> str:
    return str(random.randint(100000, 999999))
