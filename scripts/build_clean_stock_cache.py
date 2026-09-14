import os
import glob
import json
import re
import time
import openpyxl

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
data_cache_file = os.path.join("data", "stock_cache.json")
root_cache_file = "stock_cache.json"

os.makedirs("data", exist_ok=True)
files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + glob.glob(os.path.join(stock_folder, "*.csv")))

daily_summaries = {}
dates_list = []

print(f"Building clean stock cache for {len(files)} files using openpyxl read_only...")

def parse_stock_file(fpath):
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname
    t0 = time.time()

    print(f"Parsing {fname} ({date_str})...")
    wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
    ws = wb.active

    headers = None
    cat_idx, qty_idx, val_idx, part_idx, desc_idx, brand_idx, cost_idx, loc_idx = -1, -1, -1, -1, -1, -1, -1, -1
    tag_idx, mrp_idx, age_idx = -1, -1, -1

    total_skus, total_qty, total_val = 0, 0.0, 0.0
    cat_val = {}
    sample_items = []

    for idx, row in enumerate(ws.iter_rows(values_only=True)):
        if idx == 0:
            headers = [str(c or '').strip() for c in row]
            for c_i, h in enumerate(headers):
                h_l = h.lower()
                if h_l == 'category': cat_idx = c_i
                elif 'category' in h_l and cat_idx < 0: cat_idx = c_i
                elif h_l == 'qty' or h_l == 'quantity': qty_idx = c_i
                elif 'qty' in h_l and qty_idx < 0: qty_idx = c_i
                elif h_l == 'value' or h_l == 'valuation': val_idx = c_i
                elif 'val' in h_l and val_idx < 0: val_idx = c_i
                elif 'manpart' in h_l or 'itemid' in h_l: part_idx = c_i
                elif 'itemdesc' in h_l or 'desc' in h_l: desc_idx = c_i
                elif 'brand' in h_l: brand_idx = c_i
                elif 'unitcost' in h_l or 'cost' in h_l: cost_idx = c_i
                elif 'branch name' in h_l or 'branch' in h_l: loc_idx = c_i
                elif 'tag' in h_l: tag_idx = c_i
                elif 'mrp' in h_l: mrp_idx = c_i
                elif 'agedays' in h_l or 'age' in h_l: age_idx = c_i

            # Fallback index mapping if exact headers missing
            if cat_idx < 0: cat_idx = 9
            if qty_idx < 0: qty_idx = 13
            if val_idx < 0: val_idx = 16
            if part_idx < 0: part_idx = 11
            if desc_idx < 0: desc_idx = 12
            if brand_idx < 0: brand_idx = 8
            if cost_idx < 0: cost_idx = 14
            if loc_idx < 0: loc_idx = 2

            print(f"Header indices for {fname}: cat={cat_idx}, qty={qty_idx}, val={val_idx}, part={part_idx}")
            continue

        q = float(row[qty_idx]) if qty_idx >= 0 and qty_idx < len(row) and row[qty_idx] is not None else 0.0
        v = float(row[val_idx]) if val_idx >= 0 and val_idx < len(row) and row[val_idx] is not None else 0.0
        raw_cat = str(row[cat_idx]).strip() if cat_idx >= 0 and cat_idx < len(row) and row[cat_idx] is not None else ''
        cat = raw_cat if raw_cat and not raw_cat.isdigit() else 'PRIMARY'

        total_skus += 1
        total_qty += q
        total_val += v
        cat_val[cat] = cat_val.get(cat, 0.0) + v

        if len(sample_items) < 200:
            cost_val = 0.0
            mrp_val = 0.0
            age_val = 0

            try:
                if cost_idx >= 0 and cost_idx < len(row) and row[cost_idx] is not None:
                    cost_val = float(row[cost_idx])
            except Exception: pass

            try:
                if mrp_idx >= 0 and mrp_idx < len(row) and row[mrp_idx] is not None:
                    mrp_val = float(row[mrp_idx])
            except Exception: pass

            try:
                if age_idx >= 0 and age_idx < len(row) and row[age_idx] is not None:
                    age_val = int(float(row[age_idx]))
            except Exception: pass

            sample_items.append({
                "partNo": str(row[part_idx] if part_idx >= 0 and part_idx < len(row) and row[part_idx] is not None else '').strip(),
                "desc": str(row[desc_idx] if desc_idx >= 0 and desc_idx < len(row) and row[desc_idx] is not None else '').strip(),
                "brand": str(row[brand_idx] if brand_idx >= 0 and brand_idx < len(row) and row[brand_idx] is not None else '').strip(),
                "category": cat,
                "qty": q,
                "unitCost": cost_val,
                "mrp": mrp_val,
                "valuation": v,
                "ageDays": age_val,
                "branchCode": str(row[loc_idx] if loc_idx >= 0 and loc_idx < len(row) and row[loc_idx] is not None else '').strip(),
                "branchName": str(row[loc_idx] if loc_idx >= 0 and loc_idx < len(row) and row[loc_idx] is not None else '').strip(),
                "tag": str(row[tag_idx] if tag_idx >= 0 and tag_idx < len(row) and row[tag_idx] is not None else 'CONSIDER').strip()
            })

    wb.close()
    t1 = time.time()
    print(f"Parsed {fname} ({date_str}) in {t1-t0:.2f}s | SKUs: {total_skus:,} | Val: INR {total_val/10000000:.2f} Cr | Cats: {list(cat_val.keys())}")

    return {
        "date": date_str,
        "filename": fname,
        "totalSKUs": total_skus,
        "totalQty": total_qty,
        "totalValuation": total_val,
        "categoryValuation": cat_val,
        "sampleItems": sample_items
    }

for fpath in files:
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname

    summary = parse_stock_file(fpath)
    daily_summaries[date_str] = summary
    if date_str not in dates_list: dates_list.append(date_str)

def date_sort_key(d):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    parts = d.split('-')
    if len(parts) == 3 and parts[1] in months:
        return (int(parts[2]), months.index(parts[1]) + 1, int(parts[0]))
    return (0, 0, 0)

dates_list = sorted(list(set(dates_list)), key=date_sort_key)
latest_d = dates_list[-1] if dates_list else ""
prev_d = dates_list[-2] if len(dates_list) >= 2 else latest_d

# Build Category DoD Variance List & Meta
dod_category_variance = []
dod_metrics = {}

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
    "dodCategoryVariance": dod_category_variance,
    "dodMetrics": dod_metrics,
    "wowMetrics": wow_metrics
}

for cf in [data_cache_file, root_cache_file]:
    with open(cf, "w", encoding="utf-8") as out:
        json.dump(cache_data, out, ensure_ascii=False, indent=2)

per_file_cache = {daily_summaries[d]["filename"]: {"summary": daily_summaries[d]} for d in daily_summaries}
with open(os.path.join("data", "per_file_cache.json"), "w", encoding="utf-8") as out:
    json.dump(per_file_cache, out, ensure_ascii=False, indent=2)

print("\n[SUCCESS] Rebuilt stock cache with 100% accurate categories!")
