import hashlib
password = input('Password: ')
digest = hashlib.md5(password.encode()).hexdigest()
print(digest)
