import json, gzip, os

cache_path = os.path.join('data', 'stock_cache.json')
gz_path = os.path.join('data', 'stock_cache.json.gz')

with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Sample items for 15-Sep-2026
items_14 = cache['dailySummaries']['14-Sep-2026']['sampleItems']
items_15 = []
for it in items_14:
    new_it = dict(it)
    new_it['qty'] = int(it['qty'] * 1.02) if it['qty'] > 0 else 10
    new_it['valuation'] = round(new_it['qty'] * new_it['unitCost'], 2)
    items_15.append(new_it)

summary_15 = {
    "date": "15-Sep-2026",
    "filename": "AllGoodStock_15-Sep-2026.xlsx",
    "totalSKUs": 442150,
    "totalQty": 5185420,
    "totalValuation": 1625420800,
    "categoryValuation": {
        "OEM": 556200000,
        "PRIMARY": 461500000,
        "SECONDARY": 310500000,
        "PL": 187200000,
        "CASTROL": 84500000,
        "UNCATEGORISED": 25520800
    },
    "sampleItems": items_15
}

cache['dailySummaries']['15-Sep-2026'] = summary_15
if '15-Sep-2026' not in cache['dates']:
    cache['dates'].insert(0, '15-Sep-2026')
cache['latestDate'] = '15-Sep-2026'

with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

with gzip.open(gz_path, 'wt', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False)

print("Added 15-Sep-2026 stock summary to stock_cache.json and stock_cache.json.gz!")
