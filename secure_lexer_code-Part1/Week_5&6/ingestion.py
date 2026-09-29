from lexer import tokenize

def secure_ingestion(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()

    tokens = tokenize(code)

    with open("logs.txt", "w") as log:
        for token in tokens:
            if not token.valid:
                log.write(f"ERROR at {token.position}: {token}\n")

    return tokens
