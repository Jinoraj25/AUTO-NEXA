import os
import json
import re
import openpyxl

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
output_cache = os.path.join("data", "stock_cache.json")
os.makedirs("data", exist_ok=True)

fpath_8 = os.path.join(stock_folder, "AllGoodStock_08-Sep-2026.xlsx")
fpath_7 = os.path.join(stock_folder, "AllGoodStock_07-Sep-2026.xlsx")

def fast_parse_file(filepath):
    print(f"Streaming {os.path.basename(filepath)}...")
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    sheet = wb.active

    skus = 0
    total_qty = 0.0
    total_val = 0.0
    sample_items = []

    for idx, row in enumerate(sheet.iter_rows(values_only=True)):
        if idx == 0:
            headers = [str(c).strip() if c else '' for c in row]
            col_part = headers.index('ManPart') if 'ManPart' in headers else (headers.index('ItemID(myTVS)') if 'ItemID(myTVS)' in headers else 10)
            col_desc = headers.index('ItemDesc') if 'ItemDesc' in headers else 12
            col_brand = headers.index('BRAND') if 'BRAND' in headers else 8
            col_cat = headers.index('CATEGORY') if 'CATEGORY' in headers else 9
            col_qty = headers.index('Qty') if 'Qty' in headers else 13
            col_cost = headers.index('UnitCost') if 'UnitCost' in headers else 14
            col_val = headers.index('Value') if 'Value' in headers else 16
            col_loc = headers.index('BRANCH NAME') if 'BRANCH NAME' in headers else 2
            continue

        if not row or len(row) <= max(col_qty, col_val):
            continue

        try:
            q_val = float(row[col_qty]) if row[col_qty] is not None and str(row[col_qty]).strip() != '' else 0.0
            v_val = float(row[col_val]) if row[col_val] is not None and str(row[col_val]).strip() != '' else 0.0
            c_val = float(row[col_cost]) if row[col_cost] is not None and str(row[col_cost]).strip() != '' else 0.0

            skus += 1
            total_qty += q_val
            total_val += v_val

            if len(sample_items) < 200:
                sample_items.append({
                    "partNo": str(row[col_part] or '').strip(),
                    "desc": str(row[col_desc] or '').strip(),
                    "brand": str(row[col_brand] or '').strip(),
                    "category": str(row[col_cat] or '').strip(),
                    "qty": q_val,
                    "unitCost": c_val,
                    "valuation": v_val,
                    "branch": str(row[col_loc] or '').strip()
                })
        except Exception:
            continue

    wb.close()
    return skus, total_qty, total_val, sample_items

skus_8, qty_8, val_8, items_8 = fast_parse_file(fpath_8)
print(f"08-Sep-2026: {skus_8:,} SKUs, {qty_8:,.0f} units, ₹{val_8/10000000:,.2f} Cr")

skus_7, qty_7, val_7, items_7 = fast_parse_file(fpath_7)
print(f"07-Sep-2026: {skus_7:,} SKUs, {qty_7:,.0f} units, ₹{val_7/10000000:,.2f} Cr")

cache_data = {
    "status": "success",
    "stockFolderPath": stock_folder,
    "oneDriveLink": "https://tvsundramiyengar-my.sharepoint.com/personal/autoflash_tvs_in/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fautoflash%5Ftvs%5Fin%2FDocuments%2FConsolidateReports%2FConsolidateStock%2FInventory&ga=1",
    "dates": ["01-Sep-2026", "02-Sep-2026", "03-Sep-2026", "04-Sep-2026", "05-Sep-2026", "07-Sep-2026", "08-Sep-2026"],
    "latestDate": "08-Sep-2026",
    "dailySummaries": {
        "08-Sep-2026": {
            "date": "08-Sep-2026",
            "filename": "AllGoodStock_08-Sep-2026.xlsx",
            "totalSKUs": skus_8,
            "totalQty": qty_8,
            "totalValuation": val_8,
            "sampleItems": items_8
        },
        "07-Sep-2026": {
            "date": "07-Sep-2026",
            "filename": "AllGoodStock_07-Sep-2026.xlsx",
            "totalSKUs": skus_7,
            "totalQty": qty_7,
            "totalValuation": val_7,
            "sampleItems": items_7
        }
    },
    "dodMetrics": {
        "latestDate": "08-Sep-2026",
        "prevDate": "07-Sep-2026",
        "skusDiff": skus_8 - skus_7,
        "qtyDiff": qty_8 - qty_7,
        "valDiff": val_8 - val_7,
        "addedQty": max(0, int(qty_8 - qty_7)) if qty_8 > qty_7 else 0,
        "consumedQty": abs(int(qty_8 - qty_7)) if qty_8 < qty_7 else 0
    },
    "wowMetrics": {
        "currWeekAvg": round(qty_8, 1),
        "daysCount": 7
    }
}

with open(output_cache, "w", encoding="utf-8") as out:
    json.dump(cache_data, out, ensure_ascii=False)

print(f"SUCCESS: Written {output_cache}!")
