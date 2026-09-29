"""
Simple lexer demonstration
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lexer.tokenizer import SimpleTokenizer

def main():
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            code = f.read()
    else:
        # Use sample code
        code = """
        # Sample vulnerable code
        user_input = $_GET['id'];
        query = "SELECT * FROM users WHERE id='" + user_input + "'";
        result = mysql_query(query);
        
        # Another vulnerability
        system("rm " + filename);
        """
    
    tokenizer = SimpleTokenizer()
    tokens = tokenizer.tokenize(code)
    
    print("=" * 60)
    print("TOKEN STREAM:")
    print("=" * 60)
    for i, token in enumerate(tokens):
        print(f"{i+1:3d}: [{token.line:3d}:{token.column:3d}] "
              f"{token.type:12s} '{token.value}'")
    
    print(f"\nTotal tokens: {len(tokens)}")

if __name__ == "__main__":
    main()