import os
import json
import gzip
import time

t0 = time.time()
print("Compressing all project JSON databases to lightweight .json.gz for GitHub & Render...")

targets = [
    os.path.join('data', 'trained_mapping_db.json'),
    'trained_mapping_db.json',
    os.path.join('data', 'stock_cache.json'),
    'stock_cache.json'
]

for target in targets:
    if os.path.exists(target):
        orig_sz = os.path.getsize(target) / 1024 / 1024
        gz_path = target + '.gz'
        
        with open(target, 'r', encoding='utf-8') as f:
            db = json.load(f)

        # Minify JSON string
        min_str = json.dumps(db, ensure_ascii=False, separators=(',', ':'))
        min_bytes = min_str.encode('utf-8')

        # Gzip compress
        gz_bytes = gzip.compress(min_bytes, compresslevel=9)
        with open(gz_path, 'wb') as gf:
            gf.write(gz_bytes)

        gz_sz = os.path.getsize(gz_path) / 1024 / 1024
        print(f"Compressed {target} ({orig_sz:.2f} MB) ==> {gz_path} ({gz_sz:.2f} MB)")

t1 = time.time()
print(f"COMPRESSION SUCCESS! Finished in {t1-t0:.2f} seconds.")
