import os
import glob
import json
import re
import pandas as pd

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
output_cache = os.path.join("data", "stock_cache.json")
os.makedirs("data", exist_ok=True)

print(f"Scanning ALL GOOD STOCK folder: {stock_folder}...")

files = glob.glob(os.path.join(stock_folder, "*.xlsx")) + \
        glob.glob(os.path.join(stock_folder, "*.xlsb")) + \
        glob.glob(os.path.join(stock_folder, "*.csv"))

files = sorted(files)
print(f"Found {len(files)} daily stock files in ALL GOOD STOCK:")
for f in files:
    print(" -", os.path.basename(f))

daily_summaries = {}
daily_top_variances = []
dates_list = []

for fpath in files:
    fname = os.path.basename(fpath)
    # Extract date string like '01-Sep-2026'
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname.replace('.xlsx','').replace('.xlsb','').replace('.csv','')
    
    print(f"Processing stock file for date {date_str}...")
    try:
        if fpath.endswith('.csv'):
            df = pd.read_csv(fpath)
        elif fpath.endswith('.xlsb'):
            df = pd.read_excel(fpath, engine='pyxlsb')
        else:
            df = pd.read_excel(fpath)

        df = df.fillna('')
        
        # Determine columns
        col_part = 'ManPart' if 'ManPart' in df.columns else ('ItemID(myTVS)' if 'ItemID(myTVS)' in df.columns else df.columns[10])
        col_desc = 'ItemDesc' if 'ItemDesc' in df.columns else df.columns[12]
        col_brand = 'BRAND' if 'BRAND' in df.columns else df.columns[8]
        col_cat = 'CATEGORY' if 'CATEGORY' in df.columns else df.columns[9]
        col_qty = 'Qty' if 'Qty' in df.columns else df.columns[13]
        col_cost = 'UnitCost' if 'UnitCost' in df.columns else df.columns[14]
        col_val = 'Value' if 'Value' in df.columns else df.columns[16]
        col_loc = 'BRANCH NAME' if 'BRANCH NAME' in df.columns else df.columns[2]

        total_skus = len(df)
        total_qty = float(pd.to_numeric(df[col_qty], errors='coerce').sum())
        total_val = float(pd.to_numeric(df[col_val], errors='coerce').sum())

        # Category breakdown
        cat_counts = df[col_cat].value_counts().head(5).to_dict()
        brand_counts = df[col_brand].value_counts().head(5).to_dict()

        # Extract top 100 sample items for table rendering
        df_sample = df.head(200)
        sample_items = []
        for _, row in df_sample.iterrows():
            sample_items.append({
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
            "topCategories": cat_counts,
            "topBrands": brand_counts,
            "sampleItems": sample_items
        }
        dates_list.append(date_str)
        print(f" -> Date {date_str}: {total_skus} SKUs, {total_qty:,.0f} units, ₹{total_val/100000:,.2f} Lakhs")

    except Exception as err:
        print(f"Error parsing {fname}: {err}")

# Calculate Day-over-Day and Week-over-Week analytics
dod_metrics = {}
wow_metrics = {}

if len(dates_list) >= 2:
    latest_d = dates_list[-1]
    prev_d = dates_list[-2]

    latest_s = daily_summaries[latest_d]
    prev_s = daily_summaries[prev_d]

    skus_diff = latest_s["totalSKUs"] - prev_s["totalSKUs"]
    qty_diff = latest_s["totalQty"] - prev_s["totalQty"]
    val_diff = latest_s["totalValuation"] - prev_s["totalValuation"]

    dod_metrics = {
        "latestDate": latest_d,
        "prevDate": prev_d,
        "skusDiff": skus_diff,
        "qtyDiff": qty_diff,
        "valDiff": val_diff,
        "addedQty": max(0, int(qty_diff)) if qty_diff > 0 else 0,
        "consumedQty": abs(int(qty_diff)) if qty_diff < 0 else 0
    }

if len(dates_list) >= 1:
    curr_week_avg = sum([daily_summaries[d]["totalQty"] for d in dates_list]) / len(dates_list)
    wow_metrics = {
        "currWeekAvg": round(curr_week_avg, 1),
        "daysCount": len(dates_list)
    }

cache_data = {
    "status": "success",
    "stockFolderPath": stock_folder,
    "dates": dates_list,
    "latestDate": dates_list[-1] if dates_list else "",
    "dailySummaries": daily_summaries,
    "dodMetrics": dod_metrics,
    "wowMetrics": wow_metrics
}

print(f"Writing stock cache to {output_cache}...")
with open(output_cache, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False)

print(f"SUCCESS: Generated {output_cache} with {len(daily_summaries)} daily stock reports!")
