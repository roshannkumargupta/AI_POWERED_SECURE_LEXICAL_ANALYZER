import math
from collections import Counter
#augumented data set or pre-existing data set.

class SecureToken:
    def __init__(self, type_, value, position):
        self.type = type_
        self.value = value
        self.position = position                                                                                                                   
        self.entropy = self.calculate_entropy()
        self.valid = self.validate()

    def calculate_entropy(self):
        if not self.value:
            return 0
        counter = Counter(self.value)
        length = len(self.value)
        entropy = -sum((count/length) * math.log2(count/length)
                       for count in counter.values())
        return round(entropy, 3)

    def validate(self):
        # Basic Unicode validation
        if any(ord(c) < 32 for c in self.value):
            return False

        # Identifier
        if self.type == "IDENTIFIER":
            if not self.value[0].isalpha() and self.value[0] != '_':
                return False

        # Suspicious entropy checking
        if self.entropy > 2.5:
            return False

        return True

    def __repr__(self):
        return f"{self.type}: {self.value} (Entropy={self.entropy}, Valid={self.valid})"
