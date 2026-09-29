category = input()
cursor.execute("SELECT * FROM items WHERE cat = %s" % category)
