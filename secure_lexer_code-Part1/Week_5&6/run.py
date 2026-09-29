from ingestion import secure_ingestion

if __name__ == "__main__":
    tokens = secure_ingestion("Week_5&6/augmented_input.txt")

    print("=== TOKENS ===")
    for token in tokens:
        print(token)

    print("\nValidation log written to logs.txt")
