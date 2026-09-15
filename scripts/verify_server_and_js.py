import urllib.request
import json
import gzip
import io

urls = [
    "http://localhost:8000/",
    "http://localhost:8000/styles.css?v=25.0.0",
    "http://localhost:8000/js/data-engine.js?v=25.0.0",
    "http://localhost:8000/js/inventory-portal.js?v=25.0.0",
    "http://localhost:8000/js/analytics-portal.js?v=25.0.0",
    "http://localhost:8000/js/mapping-portal.js?v=25.0.0",
    "http://localhost:8000/js/deviation-portal.js?v=25.0.0",
    "http://localhost:8000/js/forecasting-portal.js?v=25.0.0",
    "http://localhost:8000/js/app.js?v=25.0.0",
    "http://localhost:8000/data/aggregate_master_rules.json.gz",
    "http://localhost:8000/sales_cache.json",
    "http://localhost:8000/stock_cache.json",
    "http://localhost:8000/api/db/stats"
]

print("--- Testing Server Endpoints ---")
for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read()
            length = len(content)
            print(f"URL: {url:<60} | Status: {status} | Size: {length:>10,d} bytes")
    except Exception as e:
        print(f"URL: {url:<60} | FAILED: {e}")

print("\nVerification complete!")
