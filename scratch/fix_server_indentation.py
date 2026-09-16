with open('server.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = '''                if self.path == '/api/master_rules/upload':
            try:'''

new_block = '''        if self.path == '/api/master_rules/upload':
            try:'''

code_updated = code.replace(old_block, new_block)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print("Fixed indentation error in server.py!")
