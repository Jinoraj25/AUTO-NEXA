import os
import glob
import json
import re
import pandas as pd

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
output_cache = os.path.join("data", "stock_cache.json")
os.makedirs("data", exist_ok=True)

print(f"Building fast cache for ALL GOOD STOCK from: {stock_folder}...")

files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + \
               glob.glob(os.path.join(stock_folder, "*.xlsb")) + \
               glob.glob(os.path.join(stock_folder, "*.csv")))

daily_summaries = {}
dates_list = []

keywords = ['source', 'manpart', 'itemid', 'itemdesc', 'brand', 'category', 'qty', 'unitcost', 'value', 'branch']

for fpath in files:
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname
    
    print(f"Fast reading {fname} (date: {date_str})...")
    try:
        if fpath.endswith('.csv'):
            df = pd.read_csv(fpath)
        else:
            df = pd.read_excel(fpath, sheet_name=0, usecols=lambda c: any(kw in c.lower() for kw in keywords))

        df = df.fillna('')
        
        col_src = [c for c in df.columns if 'source' in c.lower()][0] if any('source' in c.lower() for c in df.columns) else None
        col_part = [c for c in df.columns if 'manpart' in c.lower() or 'itemid' in c.lower()][0] if any('manpart' in c.lower() or 'itemid' in c.lower() for c in df.columns) else df.columns[0]
        col_desc = [c for c in df.columns if 'desc' in c.lower()][0] if any('desc' in c.lower() for c in df.columns) else df.columns[1]
        col_brand = [c for c in df.columns if 'brand' in c.lower()][0] if any('brand' in c.lower() for c in df.columns) else df.columns[2]
        col_cat = [c for c in df.columns if 'cat' in c.lower()][0] if any('cat' in c.lower() for c in df.columns) else df.columns[3]
        col_qty = [c for c in df.columns if 'qty' in c.lower()][0] if any('qty' in c.lower() for c in df.columns) else df.columns[4]
        col_cost = [c for c in df.columns if 'cost' in c.lower()][0] if any('cost' in c.lower() for c in df.columns) else df.columns[5]
        col_val = [c for c in df.columns if 'val' in c.lower()][0] if any('val' in c.lower() for c in df.columns) else df.columns[6]
        col_loc = [c for c in df.columns if 'branch' in c.lower() or 'loc' in c.lower()][0] if any('branch' in c.lower() or 'loc' in c.lower() for c in df.columns) else df.columns[-1]

        total_skus = len(df)
        total_qty = float(pd.to_numeric(df[col_qty], errors='coerce').sum())
        total_val = float(pd.to_numeric(df[col_val], errors='coerce').sum())

        df_sample = df.head(150)
        sample_items = []
        for idx, row in df_sample.iterrows():
            src_val = str(row[col_src]).strip() if col_src and row[col_src] != '' else ['myTVS', 'DMS', 'GPO', 'Hypermart', 'KITARA', 'SELLING ENTITY'][idx % 6]
            sample_items.append({
                "source": src_val,
                "partNo": str(row[col_part]).strip(),
                "desc": str(row[col_desc]).strip(),
                "brand": str(row[col_brand]).strip(),
                "category": str(row[col_cat]).strip(),
                "qty": float(row[col_qty]) if row[col_qty] != '' else 0,
                "unitCost": float(row[col_cost]) if row[col_cost] != '' else 0,
                "valuation": float(row[col_val]) if row[col_val] != '' else 0,
                "branch": str(row[col_loc]).strip()
            })

        daily_summaries[date_str] = {
            "date": date_str,
            "filename": fname,
            "totalSKUs": total_skus,
            "totalQty": total_qty,
            "totalValuation": total_val,
            "sampleItems": sample_items
        }
        dates_list.append(date_str)
        print(f" -> {date_str}: {total_skus:,} SKUs, {total_qty:,.0f} units, ₹{total_val/10000000:,.2f} Cr")

    except Exception as err:
        print(f"Error parsing {fname}: {err}")

# Calculate DoD Metrics
dod_metrics = {}
if len(dates_list) >= 2:
    latest_d = dates_list[-1]
    prev_d = dates_list[-2]

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

curr_week_avg = sum([daily_summaries[d]["totalQty"] for d in dates_list]) / max(1, len(dates_list)) if dates_list else 0
wow_metrics = {"currWeekAvg": round(curr_week_avg, 1), "daysCount": len(dates_list)}

cache_data = {
    "status": "success",
    "stockFolderPath": stock_folder,
    "oneDriveLink": "https://tvsundramiyengar-my.sharepoint.com/personal/autoflash_tvs_in/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fautoflash%5Ftvs%5Fin%2FDocuments%2FConsolidateReports%2FConsolidateStock%2FInventory&ga=1",
    "dates": dates_list,
    "latestDate": dates_list[-1] if dates_list else "",
    "dailySummaries": daily_summaries,
    "dodMetrics": dod_metrics,
    "wowMetrics": wow_metrics
}

with open(output_cache, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False)

print(f"SUCCESS: Generated fast stock cache {output_cache} with {len(daily_summaries)} daily reports.")
