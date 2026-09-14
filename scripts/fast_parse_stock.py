import os
import glob
import json
import re
import openpyxl

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
output_cache = os.path.join("data", "stock_cache.json")
os.makedirs("data", exist_ok=True)

print(f"Ultra-fast parsing ALL GOOD STOCK folder: {stock_folder}...")

files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + \
               glob.glob(os.path.join(stock_folder, "*.xlsb")) + \
               glob.glob(os.path.join(stock_folder, "*.csv")))

daily_summaries = {}
dates_list = []

for fpath in files:
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname
    
    print(f"Reading {fname} ({date_str}) in read-only mode...")
    try:
        wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        sheet = wb.active

        total_skus = 0
        total_qty = 0.0
        total_val = 0.0

        headers = []
        sample_items = []

        for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
            if row_idx == 0:
                headers = [str(c).strip() for c in row if c is not None]
                # Map header indices
                col_part_idx = headers.index('ManPart') if 'ManPart' in headers else (headers.index('ItemID(myTVS)') if 'ItemID(myTVS)' in headers else 10)
                col_desc_idx = headers.index('ItemDesc') if 'ItemDesc' in headers else 12
                col_brand_idx = headers.index('BRAND') if 'BRAND' in headers else 8
                col_cat_idx = headers.index('CATEGORY') if 'CATEGORY' in headers else 9
                col_qty_idx = headers.index('Qty') if 'Qty' in headers else 13
                col_cost_idx = headers.index('UnitCost') if 'UnitCost' in headers else 14
                col_val_idx = headers.index('Value') if 'Value' in headers else 16
                col_loc_idx = headers.index('BRANCH NAME') if 'BRANCH NAME' in headers else 2
                continue

            if not row or len(row) <= max(col_qty_idx, col_val_idx):
                continue

            try:
                raw_qty = row[col_qty_idx]
                raw_val = row[col_val_idx]

                qty_val = float(raw_qty) if raw_qty is not None and str(raw_qty).strip() != '' else 0.0
                val_val = float(raw_val) if raw_val is not None and str(raw_val).strip() != '' else 0.0

                total_skus += 1
                total_qty += qty_val
                total_val += val_val

                if len(sample_items) < 150:
                    cost_val = float(row[col_cost_idx]) if row[col_cost_idx] is not None and str(row[col_cost_idx]).strip() != '' else 0.0
                    sample_items.append({
                        "partNo": str(row[col_part_idx] or '').strip(),
                        "desc": str(row[col_desc_idx] or '').strip(),
                        "brand": str(row[col_brand_idx] or '').strip(),
                        "category": str(row[col_cat_idx] or '').strip(),
                        "qty": qty_val,
                        "unitCost": cost_val,
                        "valuation": val_val,
                        "branch": str(row[col_loc_idx] or '').strip()
                    })

            except (ValueError, TypeError):
                continue

        wb.close()

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

print(f"SUCCESS: Generated ultra-fast stock cache {output_cache} with {len(daily_summaries)} daily reports!")
