import os, sys, glob, re, time, zipfile, json, gzip
import pandas as pd

stock_folder = r"ALL GOOD STOCK"
data_cache_file = os.path.join("data", "stock_cache.json")
gz_cache_file = os.path.join("data", "stock_cache.json.gz")
root_cache_file = "stock_cache.json"

os.makedirs("data", exist_ok=True)

VALID_CATS = ['PRIMARY', 'SECONDARY', 'PL', 'OEM', 'CASTROL', 'LUBES', 'PAINT&CONS', 'ASSET']

def normalize_category(raw):
    if not raw or not isinstance(raw, str): return 'UNCATEGORISED'
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
    return 'UNCATEGORISED'

def extract_date_from_name(fname):
    m1 = re.search(r'(\d{1,2})[\s_\-\.\']*([A-Za-z]{3})[\s_\-\.\']*\'?(\d{2,4})', fname)
    if m1:
        day = int(m1.group(1))
        day_str = f'{day:02d}'
        mon_map = {'JAN':'Jan','FEB':'Feb','MAR':'Mar','APR':'Apr','MAY':'May','JUN':'Jun','JUL':'Jul','AUG':'Aug','SEP':'Sep','OCT':'Oct','NOV':'Nov','DEC':'Dec'}
        mon = mon_map.get(m1.group(2).upper(), 'Sep')
        yr = m1.group(3)
        if len(yr) == 2: yr = '20' + yr
        return f'{day_str}-{mon}-{yr}'
    m2 = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
    if m2: return m2.group(0)
    return fname

def parse_stock_file_pandas(fpath, date_str):
    t0 = time.time()
    fname = os.path.basename(fpath)
    try:
        df = pd.read_excel(fpath, engine='calamine')
    except Exception:
        df = pd.read_excel(fpath)
    
    col_part = 'ManPart' if 'ManPart' in df.columns else ('ItemID(myTVS)' if 'ItemID(myTVS)' in df.columns else df.columns[10])
    col_desc = 'ItemDesc' if 'ItemDesc' in df.columns else df.columns[12]
    col_brand = 'BRAND' if 'BRAND' in df.columns else df.columns[8]
    col_cat = 'CATEGORY' if 'CATEGORY' in df.columns else df.columns[9]
    col_qty = 'Qty' if 'Qty' in df.columns else df.columns[13]
    col_cost = 'UnitCost' if 'UnitCost' in df.columns else df.columns[14]
    col_mrp = 'MRP' if 'MRP' in df.columns else df.columns[15]
    col_val = 'Value' if 'Value' in df.columns else df.columns[16]
    col_line = 'Line Code' if 'Line Code' in df.columns else ('LineCode' if 'LineCode' in df.columns else '')
    col_branch_code = 'BRANCH' if 'BRANCH' in df.columns else ('Branch' if 'Branch' in df.columns else '')
    col_branch_name = 'Branch Name' if 'Branch Name' in df.columns else ('BRANCH NAME' if 'BRANCH NAME' in df.columns else '')
    col_tag = 'TAG' if 'TAG' in df.columns else ('Tag' if 'Tag' in df.columns else '')

    total_skus = len(df)
    total_qty = float(pd.to_numeric(df[col_qty], errors='coerce').fillna(0).sum())
    total_val = float(pd.to_numeric(df[col_val], errors='coerce').fillna(0).sum())

    cat_val = {}
    sample_items = []
    step = max(1, total_skus // 2000)

    for idx, row in df.iterrows():
        raw_val = float(row[col_val]) if pd.notna(row[col_val]) else 0.0
        raw_cat = str(row[col_cat]) if pd.notna(row[col_cat]) else 'OEM'
        cat = normalize_category(raw_cat)
        cat_val[cat] = cat_val.get(cat, 0.0) + raw_val

        if idx < 100 or (idx % step == 0 and len(sample_items) < 2500):
            sample_items.append({
                "source": "myTVS",
                "partNo": str(row[col_part]).strip() if col_part and pd.notna(row[col_part]) else '',
                "desc": str(row[col_desc]).strip() if col_desc and pd.notna(row[col_desc]) else '',
                "brand": str(row[col_brand]).strip() if col_brand and pd.notna(row[col_brand]) else 'GENERIC',
                "category": cat,
                "lineCode": str(row[col_line]).strip() if col_line and pd.notna(row[col_line]) else '',
                "qty": float(row[col_qty]) if pd.notna(row[col_qty]) else 0.0,
                "unitCost": float(row[col_cost]) if pd.notna(row[col_cost]) else 0.0,
                "mrp": float(row[col_mrp]) if col_mrp and pd.notna(row[col_mrp]) else 0.0,
                "valuation": raw_val,
                "ageDays": 12,
                "branchCode": str(row[col_branch_code]).strip() if col_branch_code and pd.notna(row[col_branch_code]) else 'WHM',
                "branchName": str(row[col_branch_name]).strip() if col_branch_name and pd.notna(row[col_branch_name]) else 'MADURAI',
                "tag": str(row[col_tag]).strip() if col_tag and pd.notna(row[col_tag]) else 'CONSIDER'
            })

    t1 = time.time()
    print(f"Parsed {fname} ({date_str}) in {t1-t0:.2f}s | SKUs: {total_skus:,} | Valuation: INR {total_val/1e7:.2f} Cr")
    return {
        "date": date_str,
        "filename": fname,
        "totalSKUs": total_skus,
        "totalQty": total_qty,
        "totalValuation": total_val,
        "categoryValuation": cat_val,
        "sampleItems": sample_items
    }

def parse_stock_file_fast(fpath):
    fname = os.path.basename(fpath)
    date_str = extract_date_from_name(fname)

    if fpath.endswith('.xlsb'):
        return parse_stock_file_pandas(fpath, date_str)

    try:
        t0 = time.time()
        shared_strings = []
        with zipfile.ZipFile(fpath, 'r') as z:
            if 'xl/sharedStrings.xml' in z.namelist():
                ss_data = z.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
                si_blocks = re.findall(r'<si.*?>(.*?)</si>', ss_data, flags=re.DOTALL)
                for block in si_blocks:
                    t_matches = re.findall(r'<t[^>]*>(.*?)</t>', block, flags=re.DOTALL)
                    shared_strings.append(''.join(t_matches))

            sheet_path = 'xl/worksheets/sheet1.xml'
            if sheet_path not in z.namelist():
                sheets = [s for s in z.namelist() if s.startswith('xl/worksheets/sheet')]
                sheet_path = sheets[0] if sheets else ''

            sheet_str = z.read(sheet_path).decode('utf-8', errors='ignore')

        row_cats = {}
        cat_matches = re.finditer(r'<c r="J(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str)
        for m in cat_matches:
            r_num = int(m.group(1))
            attrs = m.group(2)
            v_val = m.group(3)
            t_val = m.group(4)

            raw_str = ''
            if t_val: raw_str = t_val
            elif 't="s"' in attrs and v_val and v_val.isdigit():
                idx = int(v_val)
                raw_str = shared_strings[idx] if idx < len(shared_strings) else ''
            elif v_val: raw_str = v_val

            row_cats[r_num] = normalize_category(raw_str)

        row_qty = {}
        row_cost = {}
        row_mrp = {}
        row_val = {}
        row_part = {}
        row_desc = {}
        row_brand = {}
        row_branch_code = {}
        row_branch_name = {}
        row_tag = {}
        row_line = {}
        row_age = {}

        def extract_cell_values(pattern, storage_dict, is_float=False, is_str=False):
            for m in re.finditer(pattern, sheet_str):
                r_num = int(m.group(1))
                if r_num == 1: continue
                attrs = m.group(2)
                v_val = m.group(3)
                t_val = m.group(4) if len(m.groups()) >= 4 else None

                val = ''
                if t_val: val = t_val
                elif 't="s"' in attrs and v_val and v_val.isdigit():
                    idx = int(v_val)
                    val = shared_strings[idx] if idx < len(shared_strings) else ''
                elif v_val: val = v_val

                if is_float:
                    try: storage_dict[r_num] = float(val)
                    except: storage_dict[r_num] = 0.0
                else:
                    storage_dict[r_num] = val

        extract_cell_values(r'<c r="N(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_qty, is_float=True)
        extract_cell_values(r'<c r="Q(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_val, is_float=True)
        extract_cell_values(r'<c r="O(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_cost, is_float=True)
        extract_cell_values(r'<c r="P(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_mrp, is_float=True)
        extract_cell_values(r'<c r="L(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_part, is_str=True)
        extract_cell_values(r'<c r="M(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_desc, is_str=True)
        extract_cell_values(r'<c r="I(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_brand, is_str=True)
        extract_cell_values(r'<c r="B(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_branch_code, is_str=True)
        extract_cell_values(r'<c r="C(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_branch_name, is_str=True)
        extract_cell_values(r'<c r="G(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_tag, is_str=True)
        extract_cell_values(r'<c r="H(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_line, is_str=True)
        extract_cell_values(r'<c r="T(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', row_age, is_float=True)

        all_rnums = sorted(list(row_val.keys()))
        total_skus = len(all_rnums)
        total_qty = sum(row_qty.values())
        total_val = sum(row_val.values())

        cat_val = {}
        sample_items = []
        step = max(1, total_skus // 2000)

        for idx, r_num in enumerate(all_rnums):
            v = row_val.get(r_num, 0.0)
            cat = row_cats.get(r_num, 'UNCATEGORISED')
            cat_val[cat] = cat_val.get(cat, 0.0) + v

            if idx < 100 or (idx % step == 0 and len(sample_items) < 2500):
                sample_items.append({
                    "source": "myTVS",
                    "partNo": str(row_part.get(r_num, '')).strip(),
                    "desc": str(row_desc.get(r_num, '')).strip(),
                    "brand": str(row_brand.get(r_num, '')).strip(),
                    "category": cat,
                    "lineCode": str(row_line.get(r_num, '')).strip(),
                    "qty": row_qty.get(r_num, 0.0),
                    "unitCost": row_cost.get(r_num, 0.0),
                    "mrp": row_mrp.get(r_num, 0.0),
                    "valuation": v,
                    "ageDays": int(row_age.get(r_num, 12)),
                    "branchCode": str(row_branch_code.get(r_num, '')).strip(),
                    "branchName": str(row_branch_name.get(r_num, '')).strip(),
                    "tag": str(row_tag.get(r_num, 'CONSIDER')).strip()
                })

        t1 = time.time()
        print(f"Parsed {fname} ({date_str}) in {t1-t0:.2f}s | SKUs: {total_skus:,} | Valuation: INR {total_val/1e7:.2f} Cr")
        return {
            "date": date_str,
            "filename": fname,
            "totalSKUs": total_skus,
            "totalQty": total_qty,
            "totalValuation": total_val,
            "categoryValuation": cat_val,
            "sampleItems": sample_items
        }
    except Exception as err:
        print(f"Fast zip parse failed for {fname}, falling back to pandas calamine: {err}")
        return parse_stock_file_pandas(fpath, date_str)

def main():
    t_start = time.time()
    files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + glob.glob(os.path.join(stock_folder, "*.xlsb")) + glob.glob(os.path.join(stock_folder, "*.csv")))
    print(f"Building Instant Stock Cache for {len(files)} files...")

    daily_summaries = {}
    dates_list = []

    for fpath in files:
        summary = parse_stock_file_fast(fpath)
        d_str = summary["date"]
        daily_summaries[d_str] = summary
        if d_str not in dates_list:
            dates_list.append(d_str)

    months = {'JAN':0, 'FEB':1, 'MAR':2, 'APR':3, 'MAY':4, 'JUN':5, 'JUL':6, 'AUG':7, 'SEP':8, 'OCT':9, 'NOV':10, 'DEC':11}
    def parse_d(s):
        parts = String(s).split('-')
        if len(parts) == 3:
            day = int(parts[0])
            mon = months.get(parts[1].upper(), 0)
            yr = int(parts[2])
            return yr * 10000 + mon * 100 + day
        return 0

    dates_list.sort(key=lambda s: (int(s.split('-')[2]) if len(s.split('-'))==3 else 2026, months.get(s.split('-')[1].upper(), 0) if len(s.split('-'))==3 else 0, int(s.split('-')[0]) if len(s.split('-'))==3 else 0), reverse=True)

    latest_d = dates_list[0] if dates_list else ""
    prev_d = dates_list[1] if len(dates_list) >= 2 else (dates_list[0] if dates_list else "")

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
        "dates": dates_list,
        "latestDate": latest_d,
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

    with gzip.open(gz_cache_file, "wt", encoding="utf-8") as out:
        json.dump(cache_data, out, ensure_ascii=False)

    new_per_file_cache = {daily_summaries[d]["filename"]: {"summary": daily_summaries[d]} for d in daily_summaries}
    with open(os.path.join("data", "per_file_cache.json"), "w", encoding="utf-8") as out:
        json.dump(new_per_file_cache, out, ensure_ascii=False, indent=2)

    t_end = time.time()
    print(f"\n[COMPLETE SUCCESS] Stock cache generated in {t_end - t_start:.2f} seconds for dates: {dates_list}")

if __name__ == '__main__':
    main()
