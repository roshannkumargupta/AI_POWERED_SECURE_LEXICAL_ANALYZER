records = [(1,), (2,)]
cursor.executemany("INSERT INTO t VALUES (%s)", records)
