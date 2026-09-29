"""
Downloads all data sources needed for dataset building.
Run this once from the secure_lexer folder.
"""
import os
import urllib.request

os.makedirs("data/sources/payloads", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

print("Downloading data sources...\n")

sources = {
    # Unicode confusables — official Unicode Consortium
    "data/sources/confusables.txt": (
        "https://www.unicode.org/Public/security/latest/confusables.txt"
    ),

    # PayloadsAllTheThings — now in markdown format
    "data/sources/payloads/sql.md": (
        "https://raw.githubusercontent.com/swisskyrepo/"
        "PayloadsAllTheThings/master/SQL%20Injection/README.md"
    ),
    "data/sources/payloads/cmd.md": (
        "https://raw.githubusercontent.com/swisskyrepo/"
        "PayloadsAllTheThings/master/Command%20Injection/README.md"
    ),
    "data/sources/payloads/xss.md": (
        "https://raw.githubusercontent.com/swisskyrepo/"
        "PayloadsAllTheThings/master/XSS%20Injection/README.md"
    ),
}

for filepath, url in sources.items():
    print(f"  Downloading {filepath}...")
    try:
        urllib.request.urlretrieve(url, filepath)
        size = os.path.getsize(filepath)
        print(f"  OK — {size:,} bytes\n")
    except Exception as e:
        print(f"  FAILED: {e}\n")

print("Done. Now run: python data/build_dataset.py")