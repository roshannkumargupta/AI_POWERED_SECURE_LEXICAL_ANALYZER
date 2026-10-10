@decorate
def parse_record(raw: bytes):
    text = rf"value={raw!r}; nested={ {'key': f"{len(raw)}"} }"
    triple = """a triple string with 'quotes'"""
    blob = rb"\x41"
    count = 1_000 + 0x1F + 0b101 + 1e3 + 2j
    matrix = [[(x := item * 2) for item in range(3)] for _ in range(2)]
    mapper = lambda value: value @ count
    return text, triple, blob, matrix, mapper

async def read_all(items):
    return [await item for item in items]
