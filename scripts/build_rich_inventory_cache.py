import os
import glob
import json
import re
import pandas as pd

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
output_cache = os.path.join("data", "stock_cache.json")
per_file_cache_path = os.path.join("data", "per_file_cache.json")
os.makedirs("data", exist_ok=True)

print(f"Building fast incremental stock cache from: {stock_folder}...")

# Load existing per-file cache if available
per_file_cache = {}
if os.path.exists(per_file_cache_path):
    try:
        with open(per_file_cache_path, "r", encoding="utf-8") as pf:
            per_file_cache = json.load(pf)
    except Exception as e:
        print(f"Notice: Could not load per-file cache: {e}")

files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + \
               glob.glob(os.path.join(stock_folder, "*.xlsb")) + \
               glob.glob(os.path.join(stock_folder, "*.csv")))

daily_summaries = {}
dates_list = []
cache_updated = False

# Relevant columns to load for max speed
relevant_cols = [
    'Source', 'Branch', 'BRANCH NAME', 'STATE', 'Region', 'TAG', 'Line Code', 
    'BRAND', 'CATEGORY', 'ItemID(myTVS)', 'ManPart', 'ItemDesc', 'Qty', 
    'UnitCost', 'MRP', 'Value', 'AgeDays'
]

for fpath in files:
    fname = os.path.basename(fpath)
    mtime = os.path.getmtime(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname

    # Check if we have a valid cached summary for this exact file version
    if fname in per_file_cache and per_file_cache[fname].get("mtime") == mtime:
        print(f"Fast load from cache: {fname} ({date_str})")
        summary = per_file_cache[fname]["summary"]
        daily_summaries[date_str] = summary
        dates_list.append(date_str)
        continue

    print(f"Parsing new/updated file: {fname} ({date_str})...")
    try:
        if fpath.endswith('.csv'):
            df = pd.read_csv(fpath)
        else:
            # Optimize read by specifying sheet 0 and lambda filter for relevant columns
            df = pd.read_excel(fpath, sheet_name=0, usecols=lambda c: any(rc.lower() in c.lower() for rc in relevant_cols))

        df = df.fillna('')
        
        col_source = [c for c in df.columns if 'source' in c.lower()][0] if any('source' in c.lower() for c in df.columns) else ''
        col_branch_code = [c for c in df.columns if c.lower() == 'branch'][0] if any(c.lower() == 'branch' for c in df.columns) else ''
        col_branch_name = [c for c in df.columns if 'branch name' in c.lower()][0] if any('branch name' in c.lower() for c in df.columns) else ''
        col_state = [c for c in df.columns if 'state' in c.lower()][0] if any('state' in c.lower() for c in df.columns) else ''
        col_region = [c for c in df.columns if 'region' in c.lower()][0] if any('region' in c.lower() for c in df.columns) else ''
        col_tag = [c for c in df.columns if 'tag' in c.lower()][0] if any('tag' in c.lower() for c in df.columns) else ''
        col_line_code = [c for c in df.columns if 'line' in c.lower()][0] if any('line' in c.lower() for c in df.columns) else ''
        col_brand = [c for c in df.columns if 'brand' in c.lower()][0] if any('brand' in c.lower() for c in df.columns) else ''
        col_cat = [c for c in df.columns if 'cat' in c.lower()][0] if any('cat' in c.lower() for c in df.columns) else ''
        col_item_id = [c for c in df.columns if 'itemid' in c.lower()][0] if any('itemid' in c.lower() for c in df.columns) else ''
        col_part = [c for c in df.columns if 'manpart' in c.lower()][0] if any('manpart' in c.lower() for c in df.columns) else (col_item_id or df.columns[0])
        col_desc = [c for c in df.columns if 'desc' in c.lower()][0] if any('desc' in c.lower() for c in df.columns) else df.columns[1]
        col_qty = [c for c in df.columns if 'qty' in c.lower()][0] if any('qty' in c.lower() for c in df.columns) else df.columns[2]
        col_cost = [c for c in df.columns if 'unitcost' in c.lower() or 'cost' in c.lower()][0] if any('cost' in c.lower() for c in df.columns) else df.columns[3]
        col_mrp = [c for c in df.columns if 'mrp' in c.lower()][0] if any('mrp' in c.lower() for c in df.columns) else ''
        col_val = [c for c in df.columns if 'val' in c.lower()][0] if any('val' in c.lower() for c in df.columns) else df.columns[4]
        col_age = [c for c in df.columns if 'age' in c.lower()][0] if any('age' in c.lower() for c in df.columns) else ''

        total_skus = len(df)
        total_qty = float(pd.to_numeric(df[col_qty], errors='coerce').sum()) if col_qty else 0.0
        total_val = float(pd.to_numeric(df[col_val], errors='coerce').sum()) if col_val else 0.0

        # Category-wise metrics
        cat_group = df.groupby(col_cat) if col_cat else None
        category_valuation = {}
        category_qty = {}
        category_skus = {}

        if cat_group is not None:
            for cat_name, group in cat_group:
                c_name = str(cat_name).strip() or 'UNCATEGORIZED'
                c_val = float(pd.to_numeric(group[col_val], errors='coerce').sum()) if col_val else 0.0
                c_q = float(pd.to_numeric(group[col_qty], errors='coerce').sum()) if col_qty else 0.0
                c_s = len(group)
                category_valuation[c_name] = c_val
                category_qty[c_name] = c_q
                category_skus[c_name] = c_s

        # Sample item records - Excluded: STATUS, GRN, Location, GRN/AgeDate, Good/Damage, CARS
        df_sample = df.head(300)
        sample_items = []
        for _, row in df_sample.iterrows():
            sample_items.append({
                "source": str(row[col_source]).strip() if col_source else "",
                "branchCode": str(row[col_branch_code]).strip() if col_branch_code else "",
                "branchName": str(row[col_branch_name]).strip() if col_branch_name else "",
                "state": str(row[col_state]).strip() if col_state else "",
                "region": str(row[col_region]).strip() if col_region else "",
                "tag": str(row[col_tag]).strip() if col_tag else "CONSIDER",
                "lineCode": str(row[col_line_code]).strip() if col_line_code else "",
                "brand": str(row[col_brand]).strip() if col_brand else "GENERIC",
                "category": str(row[col_cat]).strip() if col_cat else "UNCATEGORIZED",
                "itemId": str(row[col_item_id]).strip() if col_item_id else "",
                "partNo": str(row[col_part]).strip() if col_part else "",
                "desc": str(row[col_desc]).strip() if col_desc else "",
                "qty": float(row[col_qty]) if (col_qty and row[col_qty] != '') else 0,
                "unitCost": float(row[col_cost]) if (col_cost and row[col_cost] != '') else 0,
                "mrp": float(row[col_mrp]) if (col_mrp and row[col_mrp] != '') else 0,
                "valuation": float(row[col_val]) if (col_val and row[col_val] != '') else 0,
                "ageDays": int(row[col_age]) if (col_age and str(row[col_age]).isdigit()) else 0
            })

        summary = {
            "date": date_str,
            "filename": fname,
            "totalSKUs": total_skus,
            "totalQty": total_qty,
            "totalValuation": total_val,
            "categoryValuation": category_valuation,
            "categoryQty": category_qty,
            "categorySKUs": category_skus,
            "sampleItems": sample_items
        }

        daily_summaries[date_str] = summary
        dates_list.append(date_str)

        # Update per-file cache memory
        per_file_cache[fname] = {
            "mtime": mtime,
            "summary": summary
        }
        cache_updated = True
        print(f" -> {date_str}: {total_skus:,} SKUs, {total_qty:,.0f} Qty, INR {total_val/10000000:,.2f} Cr")

    except Exception as err:
        print(f"Error parsing {fname}: {err}")

# Save updated per-file cache if modified
if cache_updated:
    with open(per_file_cache_path, "w", encoding="utf-8") as pf:
        json.dump(per_file_cache, pf, ensure_ascii=False)

# Calculate Day-over-Day Category Valuation Variance (Latest vs Prev Date)
dod_category_variance = []
if len(dates_list) >= 2:
    latest_d = dates_list[-1]
    prev_d = dates_list[-2]

    l_cat_val = daily_summaries[latest_d].get("categoryValuation", {})
    p_cat_val = daily_summaries[prev_d].get("categoryValuation", {})
    all_cats = sorted(set(list(l_cat_val.keys()) + list(p_cat_val.keys())))

    for cat in all_cats:
        curr_v = l_cat_val.get(cat, 0.0)
        prev_v = p_cat_val.get(cat, 0.0)
        diff_v = curr_v - prev_v
        pct_v = (diff_v / prev_v * 100.0) if prev_v > 0 else 0.0

        curr_q = daily_summaries[latest_d].get("categoryQty", {}).get(cat, 0.0)
        prev_q = daily_summaries[prev_d].get("categoryQty", {}).get(cat, 0.0)
        diff_q = curr_q - prev_q

        dod_category_variance.append({
            "category": cat,
            "prevDate": prev_d,
            "latestDate": latest_d,
            "prevValuation": prev_v,
            "latestValuation": curr_v,
            "valDiff": diff_v,
            "pctDiff": round(pct_v, 2),
            "prevQty": prev_q,
            "latestQty": curr_q,
            "qtyDiff": diff_q
        })

# Calculate Week-over-Week Category Valuation Variance (Latest vs 01-Sep / Start Date)
wow_category_variance = []
if len(dates_list) >= 2:
    latest_d = dates_list[-1]
    start_d = dates_list[0]

    l_cat_val = daily_summaries[latest_d].get("categoryValuation", {})
    s_cat_val = daily_summaries[start_d].get("categoryValuation", {})
    all_cats = sorted(set(list(l_cat_val.keys()) + list(s_cat_val.keys())))

    for cat in all_cats:
        curr_v = l_cat_val.get(cat, 0.0)
        start_v = s_cat_val.get(cat, 0.0)
        diff_v = curr_v - start_v
        pct_v = (diff_v / start_v * 100.0) if start_v > 0 else 0.0

        curr_q = daily_summaries[latest_d].get("categoryQty", {}).get(cat, 0.0)
        start_q = daily_summaries[start_d].get("categoryQty", {}).get(cat, 0.0)
        diff_q = curr_q - start_q

        wow_category_variance.append({
            "category": cat,
            "startDate": start_d,
            "latestDate": latest_d,
            "startValuation": start_v,
            "latestValuation": curr_v,
            "valDiff": diff_v,
            "pctDiff": round(pct_v, 2),
            "startQty": start_q,
            "latestQty": curr_q,
            "qtyDiff": diff_q
        })

latest_d = dates_list[-1] if dates_list else ""
prev_d = dates_list[-2] if len(dates_list) >= 2 else latest_d

qty_diff_total = (daily_summaries[latest_d]["totalQty"] - daily_summaries[prev_d]["totalQty"]) if (latest_d and prev_d) else 0
val_diff_total = (daily_summaries[latest_d]["totalValuation"] - daily_summaries[prev_d]["totalValuation"]) if (latest_d and prev_d) else 0

dod_metrics = {
    "latestDate": latest_d,
    "prevDate": prev_d,
    "skusDiff": (daily_summaries[latest_d]["totalSKUs"] - daily_summaries[prev_d]["totalSKUs"]) if (latest_d and prev_d) else 0,
    "qtyDiff": qty_diff_total,
    "valDiff": val_diff_total,
    "addedQty": max(0, int(qty_diff_total)) if qty_diff_total > 0 else 0,
    "consumedQty": abs(int(qty_diff_total)) if qty_diff_total < 0 else 0
}

wow_metrics = {
    "startDate": dates_list[0] if dates_list else "",
    "latestDate": latest_d,
    "daysCount": len(dates_list),
    "totalValuationStart": daily_summaries[dates_list[0]]["totalValuation"] if dates_list else 0,
    "totalValuationLatest": daily_summaries[latest_d]["totalValuation"] if latest_d else 0,
    "totalValDiff": (daily_summaries[latest_d]["totalValuation"] - daily_summaries[dates_list[0]]["totalValuation"]) if (dates_list and latest_d) else 0
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
    "dodCategoryVariance": dod_category_variance,
    "wowMetrics": wow_metrics,
    "wowCategoryVariance": wow_category_variance
}

with open(output_cache, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False, indent=2)

print(f"FAST SYNC COMPLETE: Generated stock cache {output_cache} in seconds!")
