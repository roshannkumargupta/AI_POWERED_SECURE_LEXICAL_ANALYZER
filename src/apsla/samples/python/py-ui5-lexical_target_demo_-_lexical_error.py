import os
name = request.args.get('q')
os.system('ls ' + name)
pw = 'admin123'
msg = "hello with no closing quote.
