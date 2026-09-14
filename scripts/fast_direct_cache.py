import os
import glob
import json
import re
import time
import openpyxl

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
data_cache = os.path.join("data", "stock_cache.json")
root_cache = "stock_cache.json"

# Load existing cache
c_data = {}
for cf in [data_cache, root_cache]:
    if os.path.exists(cf):
        try:
            with open(cf, "r", encoding="utf-8") as f:
                c_data = json.load(f)
                break
        except Exception:
            pass

summaries = c_data.get("dailySummaries", {})
dates_list = c_data.get("dates", [])

files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + glob.glob(os.path.join(stock_folder, "*.csv")))

for fpath in files:
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname

    if date_str in summaries:
        print(f"[CACHE OK] {fname} ({date_str}) already in stock_cache.json")
        continue

    print(f"[PARSING NEW FILE] {fname} ({date_str})...")
    t0 = time.time()
    wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
    ws = wb.active

    headers = None
    cat_idx, qty_idx, val_idx, part_idx, desc_idx, brand_idx, cost_idx, loc_idx = -1, -1, -1, -1, -1, -1, -1, -1
    total_skus, total_qty, total_val = 0, 0.0, 0.0
    cat_val = {}
    sample_items = []

    for idx, row in enumerate(ws.iter_rows(values_only=True)):
        if idx == 0:
            headers = [str(c or '').strip() for c in row]
            for c_i, h in enumerate(headers):
                h_l = h.lower()
                if 'manpart' in h_l or 'itemid' in h_l: part_idx = c_i
                elif 'itemdesc' in h_l or 'desc' in h_l: desc_idx = c_i
                elif 'brand' in h_l: brand_idx = c_i
                elif 'category' in h_l or 'cat' in h_l: cat_idx = c_i
                elif 'qty' in h_l: qty_idx = c_i
                elif 'unitcost' in h_l or 'cost' in h_l: cost_idx = c_i
                elif 'value' in h_l or 'valuation' in h_l: val_idx = c_i
                elif 'branch' in h_l: loc_idx = c_i
            continue

        q = float(row[qty_idx]) if qty_idx >= 0 and row[qty_idx] is not None else 0.0
        v = float(row[val_idx]) if val_idx >= 0 and row[val_idx] is not None else 0.0
        cat = str(row[cat_idx] or 'Mechanical Parts').strip() if cat_idx >= 0 else 'Mechanical Parts'

        total_skus += 1
        total_qty += q
        total_val += v
        cat_val[cat] = cat_val.get(cat, 0.0) + v

        if len(sample_items) < 150:
            sample_items.append({
                "partNo": str(row[part_idx] or '').strip() if part_idx >= 0 else '',
                "desc": str(row[desc_idx] or '').strip() if desc_idx >= 0 else '',
                "brand": str(row[brand_idx] or '').strip() if brand_idx >= 0 else '',
                "category": cat,
                "qty": q,
                "unitCost": float(row[cost_idx]) if cost_idx >= 0 and row[cost_idx] is not None else 0.0,
                "valuation": v,
                "branch": str(row[loc_idx] or '').strip() if loc_idx >= 0 else ''
            })

    wb.close()
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

    summaries[date_str] = summary_obj
    if date_str not in dates_list:
        dates_list.append(date_str)

    print(f"Parsed {fname} ({date_str}) in {t1-t0:.2f}s: SKUs={total_skus:,}, Qty={total_qty:,.0f}, Val=INR {total_val/10000000:.2f} Cr")

# Chronological sorting function for date strings like 12-Sep-2026
def date_sort_key(d):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    parts = d.split('-')
    if len(parts) == 3 and parts[1] in months:
        return (int(parts[2]), months.index(parts[1]) + 1, int(parts[0]))
    return (0, 0, 0)

dates_list = sorted(list(set(dates_list)), key=date_sort_key)
latest_d = dates_list[-1] if dates_list else ""
prev_d = dates_list[-2] if len(dates_list) >= 2 else latest_d

dod_metrics = {}
if latest_d and prev_d and latest_d in summaries and prev_d in summaries:
    l_s = summaries[latest_d]
    p_s = summaries[prev_d]
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
    "currWeekAvg": sum([summaries[d]["totalQty"] for d in dates_list]) / max(1, len(dates_list)) if dates_list else 0,
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
    "dailySummaries": summaries,
    "dodMetrics": dod_metrics,
    "wowMetrics": wow_metrics
}

for cf in [data_cache, root_cache]:
    os.makedirs(os.path.dirname(cf) if os.path.dirname(cf) else ".", exist_ok=True)
    with open(cf, "w", encoding="utf-8") as out:
        json.dump(cache_data, out, ensure_ascii=False, indent=2)

print(f"\n🎉 DONE! Cache file updated. Latest Date: {latest_d}. Total Dates: {len(dates_list)}")
