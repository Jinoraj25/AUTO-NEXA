import urllib.request
import os

url = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
target = 'cloudflared_final.exe'

print(f"Downloading {url} to {target}...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response, open(target, 'wb') as out_file:
    data = response.read()
    out_file.write(data)

print(f"SUCCESS: Downloaded {os.path.getsize(target)} bytes to {target}")
