with open('server.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_code = '''                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(merged, ensure_ascii=False).encode('utf-8'))
        if self.path == '/api/db/stats':'''

new_code = '''                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(merged, ensure_ascii=False).encode('utf-8'))
                return
        if self.path == '/api/db/stats':'''

code_updated = code.replace(old_code, new_code)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print("Added missing return on line 278 of server.py!")
