import os
import glob
import json
import re
import time
import zipfile
import xml.etree.ElementTree as ET

stock_folder = r"ALL GOOD STOCK"
data_cache_file = os.path.join("data", "stock_cache.json")
root_cache_file = "stock_cache.json"

os.makedirs("data", exist_ok=True)
files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + glob.glob(os.path.join(stock_folder, "*.csv")))

daily_summaries = {}
dates_list = []

print(f"Executing Clean Stock Cache Builder for {len(files)} files...")

for fpath in files:
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname
    t0 = time.time()

    shared_strings = []
    with zipfile.ZipFile(fpath, 'r') as z:
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_data = z.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
            shared_strings = re.findall(r'<t[^>]*>(.*?)</t>', ss_data, flags=re.DOTALL)

        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            sheets = [s for s in z.namelist() if s.startswith('xl/worksheets/sheet')]
            sheet_path = sheets[0] if sheets else ''

        f = z.open(sheet_path)
        
        # Verified 0-indexed column constants:
        col_brand_idx = 8    # Col I
        col_cat_idx = 9      # Col J
        col_part_idx = 11    # Col L
        col_desc_idx = 12    # Col M
        col_qty_idx = 13     # Col N
        col_cost_idx = 14    # Col O
        col_mrp_idx = 15     # Col P
        col_val_idx = 16     # Col Q
        col_age_idx = 19     # Col T
        col_loc_idx = 2      # Col C (BRANCH NAME)

        total_skus, total_qty, total_val = 0, 0.0, 0.0
        cat_val = {}
        sample_items = []
        row_count = 0

        for event, elem in ET.iterparse(f, events=('end',)):
            if elem.tag.endswith('row'):
                row_count += 1

                row_cells = {}
                for c in elem:
                    if c.tag.endswith('c'):
                        c_ref = c.attrib.get('r', '')
                        c_t = c.attrib.get('t', '')
                        col_str = re.sub(r'\d+', '', c_ref)
                        c_num = 0
                        for char in col_str:
                            c_num = c_num * 26 + (ord(char.upper()) - ord('A')) + 1
                        
                        c_idx = c_num - 1
                        val = ''
                        t_elem = c.find('.//{*}t')
                        v_elem = c.find('.//{*}v')

                        if c_t == 'inlineStr' and t_elem is not None and t_elem.text:
                            val = t_elem.text
                        elif c_t == 's' and v_elem is not None and v_elem.text and v_elem.text.isdigit():
                            s_idx = int(v_elem.text)
                            val = shared_strings[s_idx] if s_idx < len(shared_strings) else ''
                        elif v_elem is not None and v_elem.text:
                            val = v_elem.text
                        elif t_elem is not None and t_elem.text:
                            val = t_elem.text

                        row_cells[c_idx] = val

                if row_count == 1:
                    elem.clear()
                    continue

                try:
                    q_raw = row_cells.get(col_qty_idx, 0)
                    v_raw = row_cells.get(col_val_idx, 0)
                    q = float(q_raw) if q_raw else 0.0
                    v = float(v_raw) if v_raw else 0.0

                    total_skus += 1
                    total_qty += q
                    total_val += v

                    raw_cat = str(row_cells.get(col_cat_idx, 'PRIMARY')).strip()
                    cat_name = raw_cat if raw_cat and not raw_cat.isdigit() else 'PRIMARY'
                    cat_val[cat_name] = cat_val.get(cat_name, 0.0) + v

                    if len(sample_items) < 200:
                        cost_raw = row_cells.get(col_cost_idx, 0)
                        mrp_raw = row_cells.get(col_mrp_idx, 0)
                        age_raw = row_cells.get(col_age_idx, 0)

                        cost_val, mrp_val, age_val = 0.0, 0.0, 0
                        try: cost_val = float(cost_raw) if cost_raw else 0.0
                        except Exception: pass
                        try: mrp_val = float(mrp_raw) if mrp_raw else 0.0
                        except Exception: pass
                        try: age_val = int(float(age_raw)) if age_raw else 0
                        except Exception: pass

                        sample_items.append({
                            "partNo": str(row_cells.get(col_part_idx, '')).strip(),
                            "desc": str(row_cells.get(col_desc_idx, '')).strip(),
                            "brand": str(row_cells.get(col_brand_idx, '')).strip(),
                            "category": cat_name,
                            "qty": q,
                            "unitCost": cost_val,
                            "mrp": mrp_val,
                            "valuation": v,
                            "ageDays": age_val,
                            "branchCode": str(row_cells.get(col_loc_idx, '')).strip(),
                            "branchName": str(row_cells.get(col_loc_idx, '')).strip(),
                            "tag": "CONSIDER"
                        })
                except Exception:
                    pass

                elem.clear()

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
    daily_summaries[date_str] = summary_obj
    if date_str not in dates_list: dates_list.append(date_str)
    print(f"Parsed {fname} ({date_str}) in {t1-t0:.2f}s | SKUs: {total_skus:,} | Categories: {list(cat_val.keys())[:6]}")

def date_sort_key(d):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    parts = d.split('-')
    if len(parts) == 3 and parts[1] in months:
        return (int(parts[2]), months.index(parts[1]) + 1, int(parts[0]))
    return (0, 0, 0)

dates_list = sorted(list(set(dates_list)), key=date_sort_key)
latest_d = dates_list[-1] if dates_list else ""
prev_d = dates_list[-2] if len(dates_list) >= 2 else latest_d

dod_category_variance = []
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

qty_diff = daily_summaries[latest_d]["totalQty"] - daily_summaries[prev_d]["totalQty"] if latest_d and prev_d else 0
val_diff = daily_summaries[latest_d]["totalValuation"] - daily_summaries[prev_d]["totalValuation"] if latest_d and prev_d else 0

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
    "dodMetrics": {
        "latestDate": latest_d,
        "prevDate": prev_d,
        "skusDiff": daily_summaries[latest_d]["totalSKUs"] - daily_summaries[prev_d]["totalSKUs"] if latest_d and prev_d else 0,
        "qtyDiff": qty_diff,
        "valDiff": val_diff
    },
    "wowMetrics": {
        "currWeekAvg": sum([daily_summaries[d]["totalQty"] for d in dates_list]) / max(1, len(dates_list)),
        "daysCount": len(dates_list)
    }
}

for cf in [data_cache_file, root_cache_file]:
    with open(cf, "w", encoding="utf-8") as out:
        json.dump(cache_data, out, ensure_ascii=False, indent=2)

per_file_cache = {daily_summaries[d]["filename"]: {"summary": daily_summaries[d]} for d in daily_summaries}
with open(os.path.join("data", "per_file_cache.json"), "w", encoding="utf-8") as out:
    json.dump(per_file_cache, out, ensure_ascii=False, indent=2)

print("\n[SUCCESS] Rebuilt 100% CLEAN stock_cache.json for ALL files!")
print(f"Latest Date ({latest_d}) Categories: {list(daily_summaries[latest_d]['categoryValuation'].keys())}")
