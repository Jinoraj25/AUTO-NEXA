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
per_file_cache_file = os.path.join("data", "per_file_cache.json")

# Purge all old stored per-file caches
for pf in [per_file_cache_file, "per_file_cache.json"]:
    if os.path.exists(pf):
        try: os.remove(pf)
        except Exception: pass

files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + glob.glob(os.path.join(stock_folder, "*.csv")))

daily_summaries = {}
dates_list = []

VALID_CATS = ['PRIMARY', 'SECONDARY', 'PL', 'OEM', 'CASTROL', 'LUBES', 'PAINT&CONS', 'ASSET']

def normalize_category(raw):
    if not raw or not isinstance(raw, str): return 'UNCATEGORIZED'
    u = raw.strip().upper()
    if u in VALID_CATS: return u
    if 'PRIMARY' in u: return 'PRIMARY'
    if 'SECONDARY' in u: return 'SECONDARY'
    if 'PAINT' in u or 'CONS' in u: return 'PAINT&CONS'
    if 'CASTROL' in u: return 'CASTROL'
    if 'LUBES' in u or 'LUBE' in u: return 'LUBES'
    if 'OEM' in u: return 'OEM'
    if 'PL' in u: return 'PL'
    if 'ASSET' in u: return 'ASSET'
    return 'UNCATEGORIZED'

print(f"FORCE REBUILDING PERFECT STOCK CACHE for {len(files)} files...\n")

for fpath in files:
    fname = os.path.basename(fpath)
    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    date_str = date_match.group(0) if date_match else fname
    t0 = time.time()

    shared_strings = []
    with zipfile.ZipFile(fpath, 'r') as z:
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_f = z.open('xl/sharedStrings.xml')
            for event, elem in ET.iterparse(ss_f, events=('end',)):
                if elem.tag.endswith('si'):
                    txt = ''.join([t.text for t in elem.findall('.//{*}t') if t.text])
                    shared_strings.append(txt)
                    elem.clear()

        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            sheets = [s for s in z.namelist() if s.startswith('xl/worksheets/sheet')]
            sheet_path = sheets[0] if sheets else ''

        f = z.open(sheet_path)

        total_skus, total_qty, total_val = 0, 0.0, 0.0
        cat_val = {}
        sample_items = []
        row_count = 0

        for event, elem in ET.iterparse(f, events=('end',)):
            if elem.tag.endswith('row'):
                row_count += 1
                if row_count == 1:
                    elem.clear()
                    continue

                col_data = {}
                for c in elem:
                    if c.tag.endswith('c'):
                        ref = c.attrib.get('r', '')
                        col_str = ''.join([ch for ch in ref if ch.isalpha()])
                        c_t = c.attrib.get('t', '')
                        v_elem = c.find('.//{*}v')
                        t_elem = c.find('.//{*}t')

                        val = ''
                        if c_t == 's' and v_elem is not None and v_elem.text and v_elem.text.isdigit():
                            idx = int(v_elem.text)
                            val = shared_strings[idx] if idx < len(shared_strings) else ''
                        elif c_t == 'inlineStr' and t_elem is not None and t_elem.text:
                            val = t_elem.text
                        elif v_elem is not None and v_elem.text:
                            val = v_elem.text
                        elif t_elem is not None and t_elem.text:
                            val = t_elem.text

                        col_data[col_str] = val

                raw_cat = col_data.get('J', '')
                cat = normalize_category(raw_cat)

                q = 0.0
                try: q = float(col_data.get('N', 0))
                except Exception: pass

                v = 0.0
                try: v = float(col_data.get('Q', 0))
                except Exception: pass

                cost_val = 0.0
                try: cost_val = float(col_data.get('O', 0))
                except Exception: pass

                mrp_val = 0.0
                try: mrp_val = float(col_data.get('P', 0))
                except Exception: pass

                age_val = 0
                try: age_val = int(float(col_data.get('T', col_data.get('S', 0))))
                except Exception: pass

                total_skus += 1
                total_qty += q
                total_val += v
                cat_val[cat] = cat_val.get(cat, 0.0) + v

                if len(sample_items) < 1000:
                    part_no = col_data.get('L', '') or col_data.get('K', '')
                    desc = col_data.get('M', '')
                    brand = col_data.get('I', '')
                    branch = col_data.get('C', '')
                    tag = col_data.get('G', 'CONSIDER')
                    line_code = col_data.get('H', '')

                    sample_items.append({
                        "partNo": str(part_no).strip(),
                        "itemId": str(col_data.get('K', '')).strip(),
                        "desc": str(desc).strip(),
                        "brand": str(brand).strip(),
                        "category": cat,
                        "lineCode": str(line_code).strip(),
                        "qty": q,
                        "unitCost": cost_val,
                        "mrp": mrp_val,
                        "valuation": v,
                        "ageDays": age_val,
                        "branchCode": str(branch).strip(),
                        "branchName": str(branch).strip(),
                        "tag": str(tag).strip()
                    })

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
    print(f"  Parsed {fname} ({date_str}) in {t1-t0:.2f}s | SKUs: {total_skus:,} | Categories: {list(cat_val.keys())}")

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

new_per_file_cache = {daily_summaries[d]["filename"]: {"summary": daily_summaries[d]} for d in daily_summaries}
with open(os.path.join("data", "per_file_cache.json"), "w", encoding="utf-8") as out:
    json.dump(new_per_file_cache, out, ensure_ascii=False, indent=2)

print(f"\n[COMPLETE SUCCESS] Perfect stock cache generated for all dates: {dates_list}")
