import os
import glob
import time
import openpyxl

fpath = r"ALL GOOD STOCK/AllGoodStock_12-Sep-2026.xlsx"
t0 = time.time()
print(f"Loading {fpath} with openpyxl read_only=True...")
wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
ws = wb.active

headers = None
cat_idx, qty_idx, val_idx, part_idx, desc_idx, brand_idx, cost_idx, loc_idx = -1, -1, -1, -1, -1, -1, -1, -1

total_skus = 0
total_qty = 0.0
total_val = 0.0
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
        print("Header indices:", {"cat": cat_idx, "qty": qty_idx, "val": val_idx, "part": part_idx})
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
print(f"DONE in {t1-t0:.2f}s! SKUs: {total_skus:,}, Qty: {total_qty:,.0f}, Val: INR {total_val/10000000:.2f} Cr")
