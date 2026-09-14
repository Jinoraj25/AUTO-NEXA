import os
import glob
import json
import re
import time
import zipfile
import xml.etree.ElementTree as ET

stock_folder = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\ALL GOOD STOCK"
data_cache = os.path.join("data", "stock_cache.json")
root_cache = "stock_cache.json"

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

print(f"Checking {len(files)} stock files in ALL GOOD STOCK...")

for fpath in files:
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname

    if date_str in summaries:
        print(f"[CACHE OK] {date_str} already indexed.")
        continue

    print(f"[FAST XML PARSING] {fname} ({date_str})...")
    t0 = time.time()
    
    # 1. Read shared strings for header and sample items
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
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

        col_part_idx, col_desc_idx, col_brand_idx, col_cat_idx, col_qty_idx, col_cost_idx, col_val_idx, col_loc_idx = 11, 13, 9, 10, 14, 15, 17, 3
        total_skus, total_qty, total_val = 0, 0.0, 0.0
        cat_val = {}
        sample_items = []

        for event, elem in ET.iterparse(f, events=('end',)):
            if elem.tag.endswith('row'):
                r_num_str = elem.attrib.get('r', '0')
                r_num = int(r_num_str) if r_num_str.isdigit() else 0

                row_cells = {}
                for c in elem:
                    if c.tag.endswith('c'):
                        c_ref = c.attrib.get('r', '')
                        c_t = c.attrib.get('t', '')
                        col_str = re.sub(r'\d+', '', c_ref)
                        c_num = 0
                        for char in col_str:
                            c_num = c_num * 26 + (ord(char.upper()) - ord('A')) + 1
                        
                        v_elem = c.find(f'{ns}v')
                        if v_elem is None:
                            v_elem = c.find('v')
                        
                        val = ''
                        if v_elem is not None and v_elem.text:
                            v_text = v_elem.text
                            if c_t == 's' and v_text.isdigit():
                                s_idx = int(v_text)
                                val = shared_strings[s_idx] if s_idx < len(shared_strings) else ''
                            else:
                                val = v_text
                        row_cells[c_num] = val

                if r_num == 1:
                    for c_idx, h_text in row_cells.items():
                        h_l = str(h_text).strip().lower()
                        if 'manpart' in h_l or 'itemid' in h_l: col_part_idx = c_idx
                        elif 'itemdesc' in h_l or 'desc' in h_l: col_desc_idx = c_idx
                        elif 'brand' in h_l: col_brand_idx = c_idx
                        elif 'category' in h_l or 'cat' in h_l: col_cat_idx = c_idx
                        elif 'qty' in h_l: col_qty_idx = c_idx
                        elif 'unitcost' in h_l or 'cost' in h_l: col_cost_idx = c_idx
                        elif 'val' in h_l: col_val_idx = c_idx
                        elif 'branch' in h_l: col_loc_idx = c_idx
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

                    cat_name = str(row_cells.get(col_cat_idx, 'Mechanical Parts')).strip() or 'Mechanical Parts'
                    cat_val[cat_name] = cat_val.get(cat_name, 0.0) + v

                    if len(sample_items) < 150:
                        cost_raw = row_cells.get(col_cost_idx, 0)
                        sample_items.append({
                            "partNo": str(row_cells.get(col_part_idx, '')).strip(),
                            "desc": str(row_cells.get(col_desc_idx, '')).strip(),
                            "brand": str(row_cells.get(col_brand_idx, '')).strip(),
                            "category": cat_name,
                            "qty": q,
                            "unitCost": float(cost_raw) if cost_raw else 0.0,
                            "valuation": v,
                            "branch": str(row_cells.get(col_loc_idx, '')).strip()
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
    summaries[date_str] = summary_obj
    if date_str not in dates_list:
        dates_list.append(date_str)

    print(f"DONE {fname} ({date_str}) in {t1-t0:.2f}s! SKUs: {total_skus:,}, Qty: {total_qty:,.0f}, Val: INR {total_val/10000000:.2f} Cr")

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

print(f"\n🎉 DONE! All stock dates updated: {dates_list}. Latest: {latest_d}")
