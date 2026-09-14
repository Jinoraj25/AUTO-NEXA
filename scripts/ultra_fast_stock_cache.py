import os
import glob
import json
import re
import time
import zipfile
import xml.etree.cElementTree as ET

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
data_cache_file = os.path.join("data", "stock_cache.json")
root_cache_file = "stock_cache.json"
per_file_cache_file = os.path.join("data", "per_file_cache.json")

os.makedirs("data", exist_ok=True)

print("Starting Ultra-Fast XML Stream Stock Cache Engine...")

per_file_cache = {}
if os.path.exists(per_file_cache_file):
    try:
        with open(per_file_cache_file, "r", encoding="utf-8") as pf:
            per_file_cache = json.load(pf)
    except Exception as e:
        print(f"Notice loading per-file cache: {e}")

files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + \
               glob.glob(os.path.join(stock_folder, "*.csv")))

daily_summaries = {}
dates_list = []
cache_modified = False

def parse_xlsx_fast(fpath):
    """Ultra-fast XML streaming parser for 50MB+ XLSX stock files (~0.5s)"""
    shared_strings = []
    with zipfile.ZipFile(fpath, 'r') as z:
        if 'xl/sharedStrings.xml' in z.namelist():
            with z.open('xl/sharedStrings.xml') as f:
                for event, elem in ET.iterparse(f, events=('end',)):
                    if elem.tag.endswith('t'):
                        shared_strings.append(elem.text or '')
                    elem.clear()

        # Find main sheet
        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            sheets = [s for s in z.namelist() if s.startswith('xl/worksheets/sheet')]
            sheet_path = sheets[0] if sheets else ''

        total_skus = 0
        total_qty = 0.0
        total_val = 0.0
        cat_val = {}
        cat_qty = {}
        cat_skus = {}
        sample_items = []

        with z.open(sheet_path) as f:
            headers = []
            col_part_idx = 10
            col_desc_idx = 12
            col_brand_idx = 8
            col_cat_idx = 9
            col_qty_idx = 13
            col_cost_idx = 14
            col_val_idx = 16
            col_loc_idx = 2

            row_cells = {}
            current_row = 0

            for event, elem in ET.iterparse(f, events=('start', 'end')):
                tag = elem.tag.split('}')[-1]

                if event == 'end' and tag == 'c':
                    r_ref = elem.attrib.get('r', '')
                    t_type = elem.attrib.get('t', '')
                    val = ''
                    v_elem = elem.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                    if v_elem is not None and v_elem.text:
                        v_str = v_elem.text
                        if t_type == 's' and v_str.isdigit():
                            s_idx = int(v_str)
                            val = shared_strings[s_idx] if s_idx < len(shared_strings) else ''
                        else:
                            val = v_str

                    # Col index from ref e.g. A1, B1, J1
                    col_str = ''.join([c for c in r_ref if c.isalpha()])
                    col_num = 0
                    for c_char in col_str:
                        col_num = col_num * 26 + (ord(c_char.upper()) - ord('A')) + 1
                    row_cells[col_num - 1] = val
                    elem.clear()

                elif event == 'end' and tag == 'row':
                    current_row += 1

                    if current_row == 1:
                        # Process header
                        for idx in sorted(row_cells.keys()):
                            h = str(row_cells[idx]).strip().lower()
                            if 'manpart' in h or 'itemid' in h: col_part_idx = idx
                            elif 'itemdesc' in h or 'desc' in h: col_desc_idx = idx
                            elif 'brand' in h: col_brand_idx = idx
                            elif 'category' in h or 'cat' in h: col_cat_idx = idx
                            elif 'qty' in h: col_qty_idx = idx
                            elif 'unitcost' in h or 'cost' in h: col_cost_idx = idx
                            elif 'val' in h: col_val_idx = idx
                            elif 'branch' in h: col_loc_idx = idx
                        row_cells = {}
                        elem.clear()
                        continue

                    try:
                        q_raw = row_cells.get(col_qty_idx, 0)
                        v_raw = row_cells.get(col_val_idx, 0)

                        q = float(q_raw) if q_raw else 0.0
                        v = float(v_raw) if v_raw else 0.0

                        total_skus += 1
                        total_qty += q
                        total_val += v

                        cat_name = str(row_cells.get(col_cat_idx, 'UNCATEGORIZED')).strip() or 'UNCATEGORIZED'
                        cat_val[cat_name] = cat_val.get(cat_name, 0.0) + v
                        cat_qty[cat_name] = cat_qty.get(cat_name, 0.0) + q
                        cat_skus[cat_name] = cat_skus.get(cat_name, 0) + 1

                        if len(sample_items) < 150:
                            c_raw = row_cells.get(col_cost_idx, 0)
                            sample_items.append({
                                "partNo": str(row_cells.get(col_part_idx, '')).strip(),
                                "desc": str(row_cells.get(col_desc_idx, '')).strip(),
                                "brand": str(row_cells.get(col_brand_idx, '')).strip(),
                                "category": cat_name,
                                "qty": q,
                                "unitCost": float(c_raw) if c_raw else 0.0,
                                "valuation": v,
                                "branch": str(row_cells.get(col_loc_idx, '')).strip()
                            })
                    except Exception:
                        pass

                    row_cells = {}
                    elem.clear()

        return total_skus, total_qty, total_val, cat_val, cat_qty, cat_skus, sample_items

for fpath in files:
    fname = os.path.basename(fpath)
    mtime = os.path.getmtime(fpath)
    size = os.path.getsize(fpath)

    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname

    if fname in per_file_cache and per_file_cache[fname].get("mtime") == mtime and per_file_cache[fname].get("size") == size:
        print(f"[CACHE HIT] {fname} ({date_str})")
        summary = per_file_cache[fname]["summary"]
        daily_summaries[date_str] = summary
        dates_list.append(date_str)
        continue

    print(f"[STREAM PARSING] {fname} ({date_str})...")
    t0 = time.time()
    try:
        total_skus, total_qty, total_val, cat_val, cat_qty, cat_skus, sample_items = parse_xlsx_fast(fpath)
        t1 = time.time()

        summary = {
            "date": date_str,
            "filename": fname,
            "totalSKUs": total_skus,
            "totalQty": total_qty,
            "totalValuation": total_val,
            "categoryValuation": cat_val,
            "categoryQty": cat_qty,
            "categorySKUs": cat_skus,
            "sampleItems": sample_items
        }

        daily_summaries[date_str] = summary
        dates_list.append(date_str)

        per_file_cache[fname] = {
            "mtime": mtime,
            "size": size,
            "summary": summary
        }
        cache_modified = True
        print(f" -> Done in {t1-t0:.2f}s! {fname}: {total_skus:,} SKUs, {total_qty:,.0f} Qty, Valuation: INR {total_val/10000000:.2f} Cr")
    except Exception as err:
        print(f" -> Error parsing {fname}: {err}")

if cache_modified:
    with open(per_file_cache_file, "w", encoding="utf-8") as out:
        json.dump(per_file_cache, out, ensure_ascii=False, indent=2)

latest_d = dates_list[-1] if dates_list else ""
prev_d = dates_list[-2] if len(dates_list) >= 2 else latest_d

dod_metrics = {}
if latest_d and prev_d and latest_d in daily_summaries and prev_d in daily_summaries:
    l_s = daily_summaries[latest_d]
    p_s = daily_summaries[prev_d]
    qty_diff = l_s["totalQty"] - p_s["totalQty"]
    val_diff = l_s["totalValuation"] - p_s["totalValuation"]
    dod_metrics = {
        "latestDate": latest_d,
        "prevDate": prev_d,
        "skusDiff": l_s["totalSKUs"] - p_s["totalSKUs"],
        "qtyDiff": qty_diff,
        "valDiff": val_diff,
        "addedQty": max(0, int(qty_diff)) if qty_diff > 0 else 0,
        "consumedQty": abs(int(qty_diff)) if qty_diff < 0 else 0
    }

wow_metrics = {
    "currWeekAvg": sum([daily_summaries[d]["totalQty"] for d in dates_list]) / max(1, len(dates_list)) if dates_list else 0,
    "daysCount": len(dates_list)
}

cache_data = {
    "status": "success",
    "stockFolderPath": stock_folder,
    "oneDriveLink": "https://tvsundramiyengar-my.sharepoint.com/personal/autoflash_tvs_in/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fautoflash%5Ftvs%5Fin%2FDocuments%2FConsolidateReports%2FConsolidateStock%2FInventory&ga=1",
    "dates": dates_list,
    "latestDate": latest_d,
    "pendingDate": "09-Sep-2026",
    "stockUpdateNotice": "⚡ Folder Auto-Sync Active | Displaying Latest Available Stock: " + latest_d,
    "dailySummaries": daily_summaries,
    "dodMetrics": dod_metrics,
    "wowMetrics": wow_metrics
}

with open(data_cache_file, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False, indent=2)

with open(root_cache_file, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False, indent=2)

print(f"SUCCESS: Stock Cache fully updated! Latest Date: {latest_d} ({len(dates_list)} dates total)")
