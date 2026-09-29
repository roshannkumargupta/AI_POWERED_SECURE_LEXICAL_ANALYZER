import re
import os

def count_payloads(filepath):
    if not os.path.exists(filepath):
        print(f"NOT FOUND: {filepath}")
        return

    with open(filepath, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
    count = 0
    for block in blocks:
        for line in block.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and 2 < len(line) < 150:
                count += 1

    inline = re.findall(r'`([^`\n]{2,80})`', content)
    count += len(inline)
    print(f"{filepath}: {count} payloads extracted")

count_payloads("data/sources/payloads/sql.md")
count_payloads("data/sources/payloads/cmd.md")
count_payloads("data/sources/payloads/xss.md")