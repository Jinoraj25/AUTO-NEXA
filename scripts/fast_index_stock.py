import os
import glob
import json
import re
import openpyxl

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
output_cache = os.path.join("data", "stock_cache.json")
per_file_cache_path = os.path.join("data", "per_file_cache.json")
os.makedirs("data", exist_ok=True)

print(f"Fast indexing stock reports from: {stock_folder}...")

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

for fpath in files:
    fname = os.path.basename(fpath)
    mtime = os.path.getmtime(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname

    # If cached and file mtime matches, reuse cached summary instantly
    if fname in per_file_cache and per_file_cache[fname].get("mtime") == mtime:
        print(f"Fast load from cache: {fname} ({date_str})")
        summary = per_file_cache[fname]["summary"]
        daily_summaries[date_str] = summary
        dates_list.append(date_str)
        continue

    print(f"Fast streaming parse for new file: {fname} ({date_str})...")
    try:
        wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        ws = wb.active

        row_iter = ws.iter_rows(values_only=True)
        headers_raw = list(next(row_iter))
        headers = [str(h).strip() if h is not None else '' for h in headers_raw]

        # Get column indices
        def get_idx(name, fallback):
            for i, h in enumerate(headers):
                if name.lower() in h.lower():
                    return i
            return fallback

        idx_source = get_idx('Source', 0)
        idx_branch = get_idx('Branch', 1)
        idx_bname = get_idx('BRANCH NAME', 2)
        idx_state = get_idx('STATE', 3)
        idx_region = get_idx('Region', 4)
        idx_tag = get_idx('TAG', 6)
        idx_line = get_idx('Line Code', 7)
        idx_brand = get_idx('BRAND', 8)
        idx_cat = get_idx('CATEGORY', 9)
        idx_itemid = get_idx('ItemID(myTVS)', 10)
        idx_part = get_idx('ManPart', 11)
        idx_desc = get_idx('ItemDesc', 12)
        idx_qty = get_idx('Qty', 13)
        idx_cost = get_idx('UnitCost', 14)
        idx_mrp = get_idx('MRP', 15)
        idx_val = get_idx('Value', 16)
        idx_age = get_idx('AgeDays', 19)

        total_skus = 0
        total_qty = 0.0
        total_val = 0.0
        cat_valuation = {}
        cat_qty = {}
        cat_skus = {}
        sample_items = []

        for row in row_iter:
            if not row or row[idx_part] is None and row[idx_desc] is None:
                continue

            total_skus += 1

            # Qty & Value parsing
            q_raw = row[idx_qty] if idx_qty < len(row) else 0
            v_raw = row[idx_val] if idx_val < len(row) else 0
            q_val = float(q_raw) if (q_raw is not None and str(q_raw).replace('.','',1).replace('-','',1).isdigit()) else 0.0
            v_val = float(v_raw) if (v_raw is not None and str(v_raw).replace('.','',1).replace('-','',1).isdigit()) else 0.0

            total_qty += q_val
            total_val += v_val

            # Category aggregation
            cat_name = str(row[idx_cat]).strip() if (idx_cat < len(row) and row[idx_cat] is not None) else 'UNCATEGORIZED'
            if not cat_name:
                cat_name = 'UNCATEGORIZED'

            cat_valuation[cat_name] = cat_valuation.get(cat_name, 0.0) + v_val
            cat_qty[cat_name] = cat_qty.get(cat_name, 0.0) + q_val
            cat_skus[cat_name] = cat_skus.get(cat_name, 0) + 1

            # Store sample items for search grid (first 350 items)
            if len(sample_items) < 350:
                cost_raw = row[idx_cost] if idx_cost < len(row) else 0
                mrp_raw = row[idx_mrp] if idx_mrp < len(row) else 0
                age_raw = row[idx_age] if idx_age < len(row) else 0

                sample_items.append({
                    "source": str(row[idx_source]).strip() if (idx_source < len(row) and row[idx_source]) else "",
                    "branchCode": str(row[idx_branch]).strip() if (idx_branch < len(row) and row[idx_branch]) else "WHM",
                    "branchName": str(row[idx_bname]).strip() if (idx_bname < len(row) and row[idx_bname]) else "MADURAI",
                    "state": str(row[idx_state]).strip() if (idx_state < len(row) and row[idx_state]) else "",
                    "region": str(row[idx_region]).strip() if (idx_region < len(row) and row[idx_region]) else "",
                    "tag": str(row[idx_tag]).strip() if (idx_tag < len(row) and row[idx_tag]) else "CONSIDER",
                    "lineCode": str(row[idx_line]).strip() if (idx_line < len(row) and row[idx_line]) else "",
                    "brand": str(row[idx_brand]).strip() if (idx_brand < len(row) and row[idx_brand]) else "GENERIC",
                    "category": cat_name,
                    "itemId": str(row[idx_itemid]).strip() if (idx_itemid < len(row) and row[idx_itemid]) else "",
                    "partNo": str(row[idx_part]).strip() if (idx_part < len(row) and row[idx_part]) else "",
                    "desc": str(row[idx_desc]).strip() if (idx_desc < len(row) and row[idx_desc]) else "",
                    "qty": q_val,
                    "unitCost": float(cost_raw) if (cost_raw is not None and str(cost_raw).replace('.','',1).replace('-','',1).isdigit()) else 0.0,
                    "mrp": float(mrp_raw) if (mrp_raw is not None and str(mrp_raw).replace('.','',1).replace('-','',1).isdigit()) else 0.0,
                    "valuation": v_val,
                    "ageDays": int(float(age_raw)) if (age_raw is not None and str(age_raw).replace('.','',1).isdigit()) else 0
                })

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
            "summary": summary
        }
        with open(per_file_cache_path, "w", encoding="utf-8") as pf:
            json.dump(per_file_cache, pf, ensure_ascii=False)

        cache_updated = True
        print(f" -> Successfully parsed & saved cache for {fname} ({date_str}): {total_skus:,} SKUs, INR {total_val/10000000:.2f} Cr")

    except Exception as err:
        print(f"Error streaming {fname}: {err}")

# Calculate Day-over-Day Category Valuation Variance
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

# Calculate Week-over-Week Category Valuation Variance
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
    "dailySummaries": daily_summaries,
    "dodMetrics": dod_metrics,
    "dodCategoryVariance": dod_category_variance,
    "wowMetrics": wow_metrics,
    "wowCategoryVariance": wow_category_variance
}

with open(output_cache, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False, indent=2)

print(f"FAST INDEX COMPLETE: Updated cache at {output_cache} with latest date {latest_d}")
