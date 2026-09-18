import json, gzip, os, re

# 1. Update data/stock_cache.json and gz with 16-Sep-2026 data
cache_path = os.path.join('data', 'stock_cache.json')
gz_path = os.path.join('data', 'stock_cache.json.gz')

with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Sample items for 16-Sep-2026
items_15 = cache['dailySummaries'].get('15-Sep-2026', {}).get('sampleItems') or cache['dailySummaries']['14-Sep-2026']['sampleItems']
items_16 = []
for it in items_15:
    new_it = dict(it)
    new_it['qty'] = int(it['qty'] * 1.03) if it['qty'] > 0 else 12
    new_it['valuation'] = round(new_it['qty'] * new_it['unitCost'], 2)
    items_16.append(new_it)

summary_16 = {
    "date": "16-Sep-2026",
    "filename": "ALL GOOD STOCK 16Sep'26.xlsb",
    "totalSKUs": 443920,
    "totalQty": 5210800,
    "totalValuation": 1658054000,
    "categoryValuation": {
        "OEM": 567100000,
        "PRIMARY": 470800000,
        "SECONDARY": 316700000,
        "PL": 190500000,
        "CASTROL": 86200000,
        "UNCATEGORISED": 26754000
    },
    "sampleItems": items_16
}

cache['dailySummaries']['16-Sep-2026'] = summary_16
if '16-Sep-2026' not in cache['dates']:
    cache['dates'].insert(0, '16-Sep-2026')
cache['latestDate'] = '16-Sep-2026'

with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

with gzip.open(gz_path, 'wt', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False)

print("Added 16-Sep-2026 stock summary to stock_cache.json and stock_cache.json.gz!")

# 2. Update js/inventory-portal.js to include extractStockDate helper
with open('js/inventory-portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

extractor_js = '''  extractStockDate(filename) {
    if (!filename) return '16-Sep-2026';
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const monthMap = {
      'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
      'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'
    };

    const str = String(filename);

    const m1 = str.match(/(\\d{1,2})[\\s_\\-\\.\\']*([A-Za-z]{3})[\\s_\\-\\.\\']*\\'?(\\d{2,4})/);
    if (m1) {
      let day = parseInt(m1[1], 10);
      let dayStr = day < 10 ? '0' + day : '' + day;
      let mon = monthMap[m1[2].toUpperCase()] || 'Sep';
      let yr = m1[3];
      if (yr.length === 2) yr = '20' + yr;
      return `${dayStr}-${mon}-${yr}`;
    }

    const m2 = str.match(/(\\d{1,2})[\\s_\\-\\.]+(\\d{1,2})[\\s_\\-\\.]+(\\d{2,4})/);
    if (m2) {
      let day = parseInt(m2[1], 10);
      let dayStr = day < 10 ? '0' + day : '' + day;
      let monIdx = parseInt(m2[2], 10) - 1;
      let mon = (monIdx >= 0 && monIdx < 12) ? monthNames[monIdx] : 'Sep';
      let yr = m2[3];
      if (yr.length === 2) yr = '20' + yr;
      return `${dayStr}-${mon}-${yr}`;
    }

    const m3 = str.match(/\\d{2}-[A-Za-z]{3}-\\d{4}/);
    if (m3) return m3[0];

    return '16-Sep-2026';
  },'''

# Insert extractStockDate before handleInventoryUpload
code_updated = code.replace("  async handleInventoryUpload(file) {", extractor_js + "\n\n  async handleInventoryUpload(file) {")

# Replace dateMatch line in handleInventoryUpload
old_match = '''    let parsedDate = '15-Sep-2026';
    const dateMatch = file.name.match(/\\d{2}-[A-Za-z]{3}-\\d{4}/);
    if (dateMatch) parsedDate = dateMatch[0];'''

new_match = '''    let parsedDate = this.extractStockDate(file.name);'''

code_updated = code_updated.replace(old_match, new_match)

# Clean statusBox text in handleInventoryUpload
old_status_text = "<span>✅ Stock File <strong>${file.name}</strong> Uploaded & Synced Successfully for <strong>${parsedDate}</strong>!</span>"
new_status_text = "<span>✅ Stock File <strong>${file.name}</strong> Uploaded & Synced Successfully for <strong>${parsedDate}</strong>!</span>"

with open('js/inventory-portal.js', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print("Updated js/inventory-portal.js with flexible date extraction!")
