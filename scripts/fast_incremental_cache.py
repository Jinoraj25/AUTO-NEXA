import os
import glob
import json
import re
import openpyxl

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
data_cache_file = os.path.join("data", "stock_cache.json")
root_cache_file = "stock_cache.json"
per_file_cache_file = os.path.join("data", "per_file_cache.json")

os.makedirs("data", exist_ok=True)

print("Starting Fast Incremental Stock Cache Engine...")

# Load per-file cache
per_file_cache = {}
if os.path.exists(per_file_cache_file):
    try:
        with open(per_file_cache_file, "r", encoding="utf-8") as pf:
            per_file_cache = json.load(pf)
    except Exception as e:
        print(f"Notice loading per-file cache: {e}")

files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + \
               glob.glob(os.path.join(stock_folder, "*.xlsb")) + \
               glob.glob(os.path.join(stock_folder, "*.csv")))

daily_summaries = {}
dates_list = []
cache_modified = False

for fpath in files:
    fname = os.path.basename(fpath)
    mtime = os.path.getmtime(fpath)
    size = os.path.getsize(fpath)

    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname

    # Fast path: check if cached
    cached_entry = per_file_cache.get(fname, {})
    if cached_entry.get("mtime") == mtime and cached_entry.get("size") == size and "summary" in cached_entry:
        print(f"[CACHE HIT] {fname} ({date_str})")
        summary = cached_entry["summary"]
        daily_summaries[date_str] = summary
        dates_list.append(date_str)
        continue

    # Parse new or modified file
    print(f"[PARSING NEW FILE] {fname} ({date_str})...")
    try:
        wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        sheet = wb.active

        total_skus = 0
        total_qty = 0.0
        total_val = 0.0

        headers = []
        sample_items = []
        cat_valuation = {}
        cat_qty = {}
        cat_skus = {}

        col_part_idx = 10
        col_desc_idx = 12
        col_brand_idx = 8
        col_cat_idx = 9
        col_qty_idx = 13
        col_cost_idx = 14
        col_val_idx = 16
        col_loc_idx = 2

        for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
            if row_idx == 0:
                headers = [str(c).strip() if c is not None else '' for c in row]
                for idx, h in enumerate(headers):
                    h_lower = h.lower()
                    if 'manpart' in h_lower or 'itemid' in h_lower: col_part_idx = idx
                    elif 'itemdesc' in h_lower or 'desc' in h_lower: col_desc_idx = idx
                    elif 'brand' in h_lower: col_brand_idx = idx
                    elif 'category' in h_lower or 'cat' in h_lower: col_cat_idx = idx
                    elif 'qty' in h_lower: col_qty_idx = idx
                    elif 'unitcost' in h_lower or 'cost' in h_lower: col_cost_idx = idx
                    elif 'val' in h_lower: col_val_idx = idx
                    elif 'branch' in h_lower: col_loc_idx = idx
                continue

            if not row or len(row) <= max(col_qty_idx, col_val_idx):
                continue

            try:
                raw_qty = row[col_qty_idx]
                raw_val = row[col_val_idx]

                q = float(raw_qty) if raw_qty is not None and str(raw_qty).strip() != '' else 0.0
                v = float(raw_val) if raw_val is not None and str(raw_val).strip() != '' else 0.0

                total_skus += 1
                total_qty += q
                total_val += v

                cat_name = str(row[col_cat_idx] or 'UNCATEGORIZED').strip() if col_cat_idx < len(row) else 'UNCATEGORIZED'
                cat_valuation[cat_name] = cat_valuation.get(cat_name, 0.0) + v
                cat_qty[cat_name] = cat_qty.get(cat_name, 0.0) + q
                cat_skus[cat_name] = cat_skus.get(cat_name, 0) + 1

                if len(sample_items) < 150:
                    cost_val = float(row[col_cost_idx]) if col_cost_idx < len(row) and row[col_cost_idx] is not None and str(row[col_cost_idx]).strip() != '' else 0.0
                    sample_items.append({
                        "partNo": str(row[col_part_idx] or '').strip() if col_part_idx < len(row) else '',
                        "desc": str(row[col_desc_idx] or '').strip() if col_desc_idx < len(row) else '',
                        "brand": str(row[col_brand_idx] or '').strip() if col_brand_idx < len(row) else '',
                        "category": cat_name,
                        "qty": q,
                        "unitCost": cost_val,
                        "valuation": v,
                        "branch": str(row[col_loc_idx] or '').strip() if col_loc_idx < len(row) else ''
                    })
            except Exception:
                continue

        wb.close()

        summary = {
            "date": date_str,
            "filename": fname,
            "totalSKUs": total_skus,
            "totalQty": total_qty,
            "totalValuation": total_val,
            "categoryValuation": cat_valuation,
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
        print(f" -> Parsed {fname}: {total_skus:,} SKUs, {total_qty:,.0f} Qty, Valuation: INR {total_val/10000000:.2f} Cr")

    except Exception as err:
        print(f" -> Error parsing {fname}: {err}")

# Save updated per-file cache
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
    "stockUpdateNotice": "Folder Auto-Sync Active | Displaying Latest Available Stock: " + latest_d,
    "dailySummaries": daily_summaries,
    "dodMetrics": dod_metrics,
    "wowMetrics": wow_metrics
}

# Write BOTH data/stock_cache.json and root stock_cache.json
with open(data_cache_file, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False, indent=2)

with open(root_cache_file, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False, indent=2)

print(f"SUCCESS: Updated stock_cache.json with latest date: {latest_d} ({len(dates_list)} dates total)!")
