import os
import glob
import json
import re
import time
import zipfile

stock_folder = r"ALL GOOD STOCK"
data_cache_file = os.path.join("data", "stock_cache.json")
root_cache_file = "stock_cache.json"
per_file_cache_file = os.path.join("data", "per_file_cache.json")

os.makedirs("data", exist_ok=True)

VALID_CATS = ['PRIMARY', 'SECONDARY', 'PL', 'OEM', 'CASTROL', 'LUBES', 'PAINT&CONS', 'ASSET']

def normalize_category(raw):
    if not raw or not isinstance(raw, str): return 'UNCATEGORIZED'
    u = raw.strip().upper()
    if u in VALID_CATS: return u
    if 'PRIMARY' in u: return 'PRIMARY'
    if 'SECONDARY' in u: return 'SECONDARY'
    if 'PAINT' in u or 'CONS' in u: return 'PAINT&CONS'
    if 'CASTROL' in u: return 'CASTROL'
    if 'LUBES' in u or 'LUBE' in u: return 'LUBES'
    if 'OEM' in u: return 'OEM'
    if 'PL' in u: return 'PL'
    if 'ASSET' in u: return 'ASSET'
    return 'UNCATEGORIZED'

t_start = time.time()
files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + glob.glob(os.path.join(stock_folder, "*.csv")))
print(f"Writing Clean Stock Cache for {len(files)} files...")

daily_summaries = {}
dates_list = []

for fpath in files:
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname
    t0 = time.time()

    shared_strings = []
    with zipfile.ZipFile(fpath, 'r') as z:
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_data = z.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
            si_blocks = re.findall(r'<si.*?>(.*?)</si>', ss_data, flags=re.DOTALL)
            for block in si_blocks:
                t_matches = re.findall(r'<t[^>]*>(.*?)</t>', block, flags=re.DOTALL)
                shared_strings.append(''.join(t_matches))

        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            sheets = [s for s in z.namelist() if s.startswith('xl/worksheets/sheet')]
            sheet_path = sheets[0] if sheets else ''

        sheet_str = z.read(sheet_path).decode('utf-8', errors='ignore')

    # 1. Map row number -> Category J
    row_cats = {}
    cat_matches = re.finditer(r'<c r="J(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str)
    for m in cat_matches:
        r_num = int(m.group(1))
        attrs = m.group(2)
        v_val = m.group(3)
        t_val = m.group(4)

        raw_str = ''
        if t_val: raw_str = t_val
        elif 't="s"' in attrs and v_val and v_val.isdigit():
            idx = int(v_val)
            raw_str = shared_strings[idx] if idx < len(shared_strings) else ''
        elif v_val: raw_str = v_val

        row_cats[r_num] = normalize_category(raw_str)

    # 2. Extract Values Q and Qty N
    row_val = {}
    for m in re.finditer(r'<c r="Q(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str):
        r_num = int(m.group(1))
        if r_num == 1: continue
        try: row_val[r_num] = float(m.group(3) or m.group(4) or 0)
        except: row_val[r_num] = 0.0

    row_qty = {}
    for m in re.finditer(r'<c r="N(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str):
        r_num = int(m.group(1))
        if r_num == 1: continue
        try: row_qty[r_num] = float(m.group(3) or m.group(4) or 0)
        except: row_qty[r_num] = 0.0

    # 3. Extract sample items for search grid
    row_part = {}
    for m in re.finditer(r'<c r="L(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str):
        r_num = int(m.group(1))
        if r_num == 1: continue
        v_val = m.group(3); t_val = m.group(4); attrs = m.group(2)
        val = t_val if t_val else (shared_strings[int(v_val)] if 't="s"' in attrs and v_val and v_val.isdigit() and int(v_val)<len(shared_strings) else v_val)
        row_part[r_num] = val or ''

    row_desc = {}
    for m in re.finditer(r'<c r="M(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str):
        r_num = int(m.group(1))
        if r_num == 1: continue
        v_val = m.group(3); t_val = m.group(4); attrs = m.group(2)
        val = t_val if t_val else (shared_strings[int(v_val)] if 't="s"' in attrs and v_val and v_val.isdigit() and int(v_val)<len(shared_strings) else v_val)
        row_desc[r_num] = val or ''

    row_brand = {}
    for m in re.finditer(r'<c r="I(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str):
        r_num = int(m.group(1))
        if r_num == 1: continue
        v_val = m.group(3); t_val = m.group(4); attrs = m.group(2)
        val = t_val if t_val else (shared_strings[int(v_val)] if 't="s"' in attrs and v_val and v_val.isdigit() and int(v_val)<len(shared_strings) else v_val)
        row_brand[r_num] = val or ''

    row_cost = {}
    for m in re.finditer(r'<c r="O(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str):
        r_num = int(m.group(1))
        if r_num == 1: continue
        try: row_cost[r_num] = float(m.group(3) or m.group(4) or 0)
        except: row_cost[r_num] = 0.0

    row_mrp = {}
    for m in re.finditer(r'<c r="P(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str):
        r_num = int(m.group(1))
        if r_num == 1: continue
        try: row_mrp[r_num] = float(m.group(3) or m.group(4) or 0)
        except: row_mrp[r_num] = 0.0

    all_rnums = sorted(list(row_val.keys()))
    total_skus = len(all_rnums)
    total_qty = sum(row_qty.values())
    total_val = sum(row_val.values())

    cat_val = {}
    sample_items = []

    for r_num in all_rnums:
        v = row_val.get(r_num, 0.0)
        cat = row_cats.get(r_num, 'UNCATEGORIZED')
        cat_val[cat] = cat_val.get(cat, 0.0) + v

        if len(sample_items) < 1000:
            sample_items.append({
                "partNo": str(row_part.get(r_num, '')).strip(),
                "desc": str(row_desc.get(r_num, '')).strip(),
                "brand": str(row_brand.get(r_num, '')).strip(),
                "category": cat,
                "qty": row_qty.get(r_num, 0.0),
                "unitCost": row_cost.get(r_num, 0.0),
                "mrp": row_mrp.get(r_num, 0.0),
                "valuation": v,
                "ageDays": 0,
                "branchCode": "WHM",
                "branchName": "MADURAI",
                "tag": "CONSIDER"
            })

    t1 = time.time()
    summary_obj = {
        "date": date_str,
        "filename": fname,
        "totalSKUs": total_skus,
        "totalQty": total_qty,
        "totalValuation": total_val,
        "categoryValuation": cat_val,
        "sampleItems": sample_items
    }
    daily_summaries[date_str] = summary_obj
    if date_str not in dates_list: dates_list.append(date_str)
    print(f"Parsed {fname} ({date_str}) in {t1-t0:.2f}s | SKUs: {total_skus:,} | Valuation: INR {total_val/1e7:.2f} Cr")

def date_sort_key(d):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    parts = d.split('-')
    if len(parts) == 3 and parts[1] in months:
        return (int(parts[2]), months.index(parts[1]) + 1, int(parts[0]))
    return (0, 0, 0)

dates_list = sorted(list(set(dates_list)), key=date_sort_key)
latest_d = dates_list[-1] if dates_list else ""
prev_d = dates_list[-2] if len(dates_list) >= 2 else latest_d

dod_category_variance = []
if latest_d and prev_d and latest_d in daily_summaries and prev_d in daily_summaries:
    l_s = daily_summaries[latest_d]
    p_s = daily_summaries[prev_d]
    l_cats = l_s.get("categoryValuation", {})
    p_cats = p_s.get("categoryValuation", {})
    all_cats = sorted(list(set(list(l_cats.keys()) + list(p_cats.keys()))))

    for c in all_cats:
        v_curr = l_cats.get(c, 0.0)
        v_prev = p_cats.get(c, 0.0)
        diff = v_curr - v_prev
        pct = round((diff / (v_prev if v_prev != 0 else 1.0)) * 100, 2)
        dod_category_variance.append({
            "category": c,
            "prevValuation": v_prev,
            "latestValuation": v_curr,
            "valDiff": diff,
            "pctDiff": pct
        })

qty_diff = daily_summaries[latest_d]["totalQty"] - daily_summaries[prev_d]["totalQty"] if latest_d and prev_d else 0
val_diff = daily_summaries[latest_d]["totalValuation"] - daily_summaries[prev_d]["totalValuation"] if latest_d and prev_d else 0

cache_data = {
    "status": "success",
    "stockFolderPath": stock_folder,
    "oneDriveLink": "https://tvsundramiyengar-my.sharepoint.com/personal/autoflash_tvs_in/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fautoflash%5Ftvs%5Fin%2FDocuments%2FConsolidateReports%2FConsolidateStock%2FInventory&ga=1",
    "dates": dates_list,
    "latestDate": latest_d,
    "pendingDate": "09-Sep-2026",
    "stockUpdateNotice": "⚡ Folder Auto-Sync Active | Displaying Latest Available Stock: " + latest_d,
    "dailySummaries": daily_summaries,
    "dodCategoryVariance": dod_category_variance,
    "dodMetrics": {
        "latestDate": latest_d,
        "prevDate": prev_d,
        "skusDiff": daily_summaries[latest_d]["totalSKUs"] - daily_summaries[prev_d]["totalSKUs"] if latest_d and prev_d else 0,
        "qtyDiff": qty_diff,
        "valDiff": val_diff
    },
    "wowMetrics": {
        "currWeekAvg": sum([daily_summaries[d]["totalQty"] for d in dates_list]) / max(1, len(dates_list)),
        "daysCount": len(dates_list)
    }
}

for cf in [data_cache_file, root_cache_file]:
    with open(cf, "w", encoding="utf-8") as out:
        json.dump(cache_data, out, ensure_ascii=False, indent=2)

new_per_file_cache = {daily_summaries[d]["filename"]: {"summary": daily_summaries[d]} for d in daily_summaries}
with open(os.path.join("data", "per_file_cache.json"), "w", encoding="utf-8") as out:
    json.dump(new_per_file_cache, out, ensure_ascii=False, indent=2)

t_end = time.time()
print(f"\n[COMPLETE SUCCESS] Perfect clean stock cache generated in {t_end - t_start:.2f} seconds for dates: {dates_list}")
