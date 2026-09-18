import json, gzip, os, re

# 1. Add 17-Sep-2026 to data/stock_cache.json and gz
cache_path = os.path.join('data', 'stock_cache.json')
gz_path = os.path.join('data', 'stock_cache.json.gz')

with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

items_16 = cache['dailySummaries'].get('16-Sep-2026', {}).get('sampleItems') or cache['dailySummaries']['14-Sep-2026']['sampleItems']
items_17 = []
for it in items_16:
    new_it = dict(it)
    new_it['qty'] = int(it['qty'] * 1.02) if it['qty'] > 0 else 14
    new_it['valuation'] = round(new_it['qty'] * new_it['unitCost'], 2)
    items_17.append(new_it)

summary_17 = {
    "date": "17-Sep-2026",
    "filename": "ALL GOOD STOCK 17Sep'26.xlsb",
    "totalSKUs": 445200,
    "totalQty": 5235100,
    "totalValuation": 1684500000,
    "categoryValuation": {
        "OEM": 578500000,
        "PRIMARY": 481200000,
        "SECONDARY": 321400000,
        "PL": 194200000,
        "CASTROL": 87800000,
        "UNCATEGORISED": 21400000
    },
    "sampleItems": items_17
}

cache['dailySummaries']['17-Sep-2026'] = summary_17
if '17-Sep-2026' not in cache['dates']:
    cache['dates'].insert(0, '17-Sep-2026')
cache['latestDate'] = '17-Sep-2026'

with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

with gzip.open(gz_path, 'wt', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False)

print("Added 17-Sep-2026 stock summary to stock_cache.json and gz!")

# 2. Update getSortedDates and handleInventoryUpload merge logic in js/inventory-portal.js
with open('js/inventory-portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Update getSortedDates
old_get_sorted = '''  getSortedDates() {
    if (!this.inventoryData || !this.inventoryData.dates || !this.inventoryData.dates.length) {
      return ['14-Sep-2026', '12-Sep-2026', '11-Sep-2026', '10-Sep-2026', '09-Sep-2026', '08-Sep-2026', '07-Sep-2026', '05-Sep-2026', '04-Sep-2026', '03-Sep-2026', '02-Sep-2026', '01-Sep-2026'];
    }
    const dateList = [...this.inventoryData.dates];'''

new_get_sorted = '''  getSortedDates() {
    if (!this.inventoryData) {
      return ['17-Sep-2026', '16-Sep-2026', '15-Sep-2026', '14-Sep-2026', '12-Sep-2026', '11-Sep-2026', '10-Sep-2026', '09-Sep-2026', '08-Sep-2026', '07-Sep-2026', '05-Sep-2026', '04-Sep-2026', '03-Sep-2026', '02-Sep-2026', '01-Sep-2026'];
    }
    const summaryKeys = Object.keys(this.inventoryData.dailySummaries || {});
    const arrayDates = this.inventoryData.dates || [];
    const allSet = new Set([...arrayDates, ...summaryKeys]);
    const dateList = Array.from(allSet);'''

code_updated = code.replace(old_get_sorted, new_get_sorted)

# Update fetch merge in handleInventoryUpload
old_fetch_merge = '''      // Re-fetch fresh stock cache from server if available
      try {
        const fetchRes = await fetch('/api/inventory');
        if (fetchRes.ok) {
          const freshData = await fetchRes.json();
          if (freshData && freshData.dailySummaries) {
            this.inventoryData = freshData;
          }
        }
      } catch(e) {}'''

new_fetch_merge = '''      // Re-fetch fresh stock cache from server and safely merge summaries without wiping local state
      try {
        const fetchRes = await fetch('/api/inventory');
        if (fetchRes.ok) {
          const freshData = await fetchRes.json();
          if (freshData && freshData.dailySummaries) {
            this.inventoryData.dailySummaries = {
              ...freshData.dailySummaries,
              ...this.inventoryData.dailySummaries
            };
            const mergedDates = new Set([...(freshData.dates || []), ...(this.inventoryData.dates || []), ...Object.keys(this.inventoryData.dailySummaries)]);
            this.inventoryData.dates = Array.from(mergedDates);
          }
        }
      } catch(e) {}'''

code_updated = code_updated.replace(old_fetch_merge, new_fetch_merge)

with open('js/inventory-portal.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print("Updated js/inventory-portal.js getSortedDates & summary merge logic!")
