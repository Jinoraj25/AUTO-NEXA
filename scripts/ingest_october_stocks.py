"""
AutoNexa Enterprise Inventory Ingestion Engine
=============================================
Processes all current October month stock files from 'ALL GOOD STOCK',
wipes out old/stale data, populates SQLite inventory tables with indexing,
computes comprehensive telemetry (DoD, WoW, aging, branch, brand, condition),
and builds the instant-load cache for the modern interactive dashboard.
"""

import os
import sys
import glob
import json
import re
import time
import zipfile
import gzip
import sqlite3
import xml.etree.cElementTree as ET

PROJECT_DIR = r"D:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT"
STOCK_DIR = os.path.join(PROJECT_DIR, "ALL GOOD STOCK")
DB_PATH = os.path.join(PROJECT_DIR, "data", "autonexa.db")
CACHE_FILE_JSON = os.path.join(PROJECT_DIR, "data", "stock_cache.json")
CACHE_FILE_GZ = os.path.join(PROJECT_DIR, "data", "stock_cache.json.gz")
ROOT_CACHE_JSON = os.path.join(PROJECT_DIR, "stock_cache.json")

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

def extract_stock_date(fname):
    m = re.search(r'(\d{2})-(Oct|OCT|oct)-(\d{4})', fname)
    if m:
        return f"{m.group(1)}-Oct-{m.group(3)}"
    m2 = re.search(r'(\d{1,2})[\s_\-\.\']*([A-Za-z]{3})[\s_\-\.\']*\'?(\d{2,4})', fname)
    if m2:
        d = int(m2.group(1))
        mon = m2.group(2).capitalize()
        yr = m2.group(3)
        if len(yr) == 2: yr = '20' + yr
        return f"{d:02d}-{mon}-{yr}"
    return fname

def stream_parse_october_file(fpath, date_str, is_latest=False):
    t0 = time.time()
    fname = os.path.basename(fpath)
    print(f"\n[STREAM INGEST] Parsing {fname} ({date_str})...")

    with zipfile.ZipFile(fpath, 'r') as z:
        sheets = [s for s in z.namelist() if s.startswith('xl/worksheets/sheet')]
        if not sheets:
            return None
        sheet_name = sheets[0]
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            with z.open('xl/sharedStrings.xml') as sf:
                for s_evt, s_elem in ET.iterparse(sf, events=('end',)):
                    if s_elem.tag.endswith('si'):
                        t_node = s_elem.find('.//{*}t')
                        shared_strings.append(t_node.text if t_node is not None and t_node.text else '')
                        s_elem.clear()

        total_skus = 0
        total_qty = 0.0
        total_val = 0.0
        good_qty = 0.0
        good_val = 0.0
        damage_qty = 0.0
        damage_val = 0.0

        cat_val = {}
        cat_qty = {}
        brand_val = {}
        brand_qty = {}
        branch_val = {}
        branch_qty = {}
        region_val = {}
        age_buckets = {
            "0-30": {"count": 0, "val": 0.0, "qty": 0.0},
            "31-60": {"count": 0, "val": 0.0, "qty": 0.0},
            "61-90": {"count": 0, "val": 0.0, "qty": 0.0},
            "91-180": {"count": 0, "val": 0.0, "qty": 0.0},
            "181-365": {"count": 0, "val": 0.0, "qty": 0.0},
            ">365": {"count": 0, "val": 0.0, "qty": 0.0}
        }

        sample_items = []
        top_items_pool = []
        db_rows_to_insert = []

        with z.open(sheet_name) as f:
            for event, elem in ET.iterparse(f, events=('end',)):
                if elem.tag.endswith('row'):
                    total_skus += 1
                    if total_skus == 1:
                        elem.clear()
                        continue

                    # Extract cell values with sharedStrings resolution
                    row_data = {}
                    for cell in elem:
                        ref = cell.attrib.get('r', '')
                        col = ''.join([c for c in ref if c.isalpha()])
                        t_attr = cell.attrib.get('t')
                        v = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        if v is not None and v.text:
                            if t_attr == 's' and shared_strings:
                                try:
                                    row_data[col] = shared_strings[int(v.text)]
                                except (IndexError, ValueError):
                                    row_data[col] = v.text
                            else:
                                row_data[col] = v.text
                        else:
                            t = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                            if t is not None and t.text:
                                row_data[col] = t.text

                    # Col Mappings:
                    # A: Source, B: Branch, C: Branch Name, D: State, E: Region, F: Status, G: Tag
                    # H: Line Code, I: Brand, J: Category, K: ItemID, L: ManPart, M: ItemDesc
                    # N: Qty, O: UnitCost, P: MRP, Q: Value, R: GRN, S: AgeDate, T: AgeDays, U: Location, V: Good/Damage, W: Cars
                    try:
                        qty = float(row_data.get('N', 0) or 0)
                    except Exception:
                        qty = 0.0

                    try:
                        val = float(row_data.get('Q', 0) or 0)
                    except Exception:
                        val = 0.0

                    try:
                        cost = float(row_data.get('O', 0) or 0)
                    except Exception:
                        cost = 0.0

                    try:
                        mrp = float(row_data.get('P', 0) or 0)
                    except Exception:
                        mrp = 0.0

                    try:
                        age = int(float(row_data.get('T', 0) or 0))
                    except Exception:
                        age = 0

                    raw_brand = (row_data.get('I', 'OTHER') or 'OTHER').strip().upper()
                    raw_cat = normalize_category(row_data.get('J', 'OEM'))
                    raw_branch = (row_data.get('C', 'UNKNOWN') or 'UNKNOWN').strip().upper()
                    raw_reg = (row_data.get('E', 'SOUTH') or 'SOUTH').strip().upper()
                    part_no = (row_data.get('L') or row_data.get('K') or '').strip()
                    desc = (row_data.get('M') or '').strip()
                    line_code = (row_data.get('H') or '').strip()
                    tag = (row_data.get('G') or 'CONSIDER').strip().upper()
                    condition = (row_data.get('V') or 'Good').strip().capitalize()

                    total_qty += qty
                    total_val += val

                    if 'Damage' in condition:
                        damage_qty += qty
                        damage_val += val
                    else:
                        good_qty += qty
                        good_val += val

                    # Category
                    cat_val[raw_cat] = cat_val.get(raw_cat, 0.0) + val
                    cat_qty[raw_cat] = cat_qty.get(raw_cat, 0.0) + qty

                    # Brand
                    brand_val[raw_brand] = brand_val.get(raw_brand, 0.0) + val
                    brand_qty[raw_brand] = brand_qty.get(raw_brand, 0.0) + qty

                    # Branch
                    branch_val[raw_branch] = branch_val.get(raw_branch, 0.0) + val
                    branch_qty[raw_branch] = branch_qty.get(raw_branch, 0.0) + qty

                    # Region
                    region_val[raw_reg] = region_val.get(raw_reg, 0.0) + val

                    # Age
                    if age <= 30: b_key = "0-30"
                    elif age <= 60: b_key = "31-60"
                    elif age <= 90: b_key = "61-90"
                    elif age <= 180: b_key = "91-180"
                    elif age <= 365: b_key = "181-365"
                    else: b_key = ">365"
                    age_buckets[b_key]["count"] += 1
                    age_buckets[b_key]["val"] += val
                    age_buckets[b_key]["qty"] += qty

                    item_obj = {
                        "source": row_data.get('A', 'Oracle') or 'Oracle',
                        "partNo": part_no,
                        "desc": desc,
                        "brand": raw_brand,
                        "category": raw_cat,
                        "lineCode": line_code,
                        "branchCode": (row_data.get('B') or '').strip(),
                        "branchName": raw_branch,
                        "qty": qty,
                        "unitCost": cost,
                        "mrp": mrp,
                        "valuation": val,
                        "ageDays": age,
                        "tag": tag,
                        "condition": condition,
                        "location": (row_data.get('U') or '').strip()
                    }

                    # Maintain sample items & top valuation items
                    if is_latest:
                        if len(sample_items) < 3000:
                            if total_skus % 160 == 0:
                                sample_items.append(item_obj)
                        if val > 10000 and len(top_items_pool) < 500:
                            top_items_pool.append(item_obj)

                        # Collect rows for sqlite batch insert (sample of 35,000 comprehensive representative items)
                        if total_skus % 14 == 0 or val > 5000:
                            db_rows_to_insert.append((
                                date_str, fname, part_no, desc, raw_brand, raw_cat, line_code,
                                row_data.get('B', ''), raw_branch, qty, cost, mrp, val, age, tag
                            ))

                    elem.clear()

        # Adjust total_skus for header
        real_skus = max(0, total_skus - 1)
        dur = time.time() - t0
        print(f"  Done in {dur:.1f}s | SKUs: {real_skus:,} | Qty: {total_qty:,.0f} | Val: INR {total_val/1e7:.2f} Cr")

        # Top 15 brands
        top_brands = sorted(brand_val.items(), key=lambda x: x[1], reverse=True)[:15]
        # Top 15 branches
        top_branches = sorted(branch_val.items(), key=lambda x: x[1], reverse=True)[:15]

        # Combine sample and high-value items
        final_samples = sample_items + sorted(top_items_pool, key=lambda x: x["valuation"], reverse=True)[:200]

        summary = {
            "date": date_str,
            "filename": fname,
            "totalSKUs": real_skus,
            "totalQty": round(total_qty, 1),
            "totalValuation": round(total_val, 2),
            "goodQty": round(good_qty, 1),
            "goodVal": round(good_val, 2),
            "damageQty": round(damage_qty, 1),
            "damageVal": round(damage_val, 2),
            "categoryValuation": {k: round(v, 2) for k, v in cat_val.items()},
            "categoryQty": {k: round(v, 1) for k, v in cat_qty.items()},
            "agingBuckets": age_buckets,
            "topBrands": [{"brand": b, "valuation": round(v, 2), "qty": round(brand_qty.get(b, 0), 1)} for b, v in top_brands],
            "topBranches": [{"branch": b, "valuation": round(v, 2), "qty": round(branch_qty.get(b, 0), 1)} for b, v in top_branches],
            "regions": {k: round(v, 2) for k, v in region_val.items()},
            "sampleItems": final_samples
        }

        return summary, db_rows_to_insert

def run_full_october_ingest():
    t_start = time.time()
    print("="*70)
    print("STARTING FULL REBUILD OF INVENTORY DATABASE (OCTOBER 2026)")
    print("="*70)

    # 1. Reset Database & Tables
    print("\n1. Resetting SQLite tables in autonexa.db...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Drop old telemetry and recreate fresh
    cur.execute("DROP TABLE IF EXISTS daily_stock_telemetry")
    cur.execute("""
    CREATE TABLE daily_stock_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_date TEXT,
        filename TEXT,
        part_number TEXT,
        description TEXT,
        brand TEXT,
        category TEXT,
        line_code TEXT,
        branch_code TEXT,
        branch_name TEXT,
        stock_qty REAL,
        unit_cost REAL,
        mrp REAL,
        total_valuation REAL,
        age_days INT,
        tag TEXT
    )
    """)

    cur.execute("DROP TABLE IF EXISTS inventory_daily_snapshots")
    cur.execute("""
    CREATE TABLE inventory_daily_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT UNIQUE,
        filename TEXT,
        total_skus INT,
        total_qty REAL,
        total_valuation REAL,
        good_qty REAL,
        damage_qty REAL,
        oem_val REAL,
        primary_val REAL,
        secondary_val REAL,
        pl_val REAL,
        castrol_val REAL,
        lubes_val REAL,
        aging_summary_json TEXT,
        top_brands_json TEXT,
        top_branches_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    print("  [OK] Cleaned and initialized fresh schema.")

    # 2. Find all October files
    oct_files = sorted(glob.glob(os.path.join(STOCK_DIR, "*Oct*.xlsx*")))
    print(f"\n2. Found {len(oct_files)} October stock files to ingest.")

    daily_summaries = {}
    dates_list = []
    latest_db_rows = []

    for idx, fpath in enumerate(oct_files):
        fname = os.path.basename(fpath)
        d_str = extract_stock_date(fname)
        is_latest = (idx == len(oct_files) - 1)

        res = stream_parse_october_file(fpath, d_str, is_latest=is_latest)
        if not res:
            continue
        summary, rows_to_insert = res
        daily_summaries[d_str] = summary
        dates_list.append(d_str)

        if is_latest:
            latest_db_rows = rows_to_insert

        # Insert snapshot summary into SQLite
        cv = summary["categoryValuation"]
        cur.execute("""
        INSERT INTO inventory_daily_snapshots (
            snapshot_date, filename, total_skus, total_qty, total_valuation,
            good_qty, damage_qty, oem_val, primary_val, secondary_val, pl_val, castrol_val, lubes_val,
            aging_summary_json, top_brands_json, top_branches_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d_str, fname, summary["totalSKUs"], summary["totalQty"], summary["totalValuation"],
            summary["goodQty"], summary["damageQty"],
            cv.get("OEM", 0.0), cv.get("PRIMARY", 0.0), cv.get("SECONDARY", 0.0),
            cv.get("PL", 0.0), cv.get("CASTROL", 0.0), cv.get("LUBES", 0.0),
            json.dumps(summary["agingBuckets"]),
            json.dumps(summary["topBrands"]),
            json.dumps(summary["topBranches"])
        ))
        conn.commit()

    # 3. Insert items into daily_stock_telemetry
    print(f"\n3. Inserting {len(latest_db_rows):,} indexed records into daily_stock_telemetry...")
    cur.executemany("""
    INSERT INTO daily_stock_telemetry (
        stock_date, filename, part_number, description, brand, category, line_code,
        branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, latest_db_rows)

    print("  Creating database indexes...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_part_no ON daily_stock_telemetry(part_number)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_brand ON daily_stock_telemetry(brand)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_branch ON daily_stock_telemetry(branch_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_category ON daily_stock_telemetry(category)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_date ON daily_stock_telemetry(stock_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_age ON daily_stock_telemetry(age_days)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_val ON daily_stock_telemetry(total_valuation)")
    conn.commit()
    conn.close()
    print("  [OK] Database successfully updated and indexed!")

    # 4. Compute DoD and WoW Metrics
    latest_d = dates_list[-1] if dates_list else ""
    prev_d = dates_list[-2] if len(dates_list) >= 2 else latest_d
    l_s = daily_summaries[latest_d]
    p_s = daily_summaries[prev_d]

    dod_metrics = {
        "latestDate": latest_d,
        "prevDate": prev_d,
        "skusDiff": l_s["totalSKUs"] - p_s["totalSKUs"],
        "qtyDiff": round(l_s["totalQty"] - p_s["totalQty"], 1),
        "valDiff": round(l_s["totalValuation"] - p_s["totalValuation"], 2),
        "valDiffPct": round(((l_s["totalValuation"] - p_s["totalValuation"]) / max(1, p_s["totalValuation"])) * 100, 2),
        "goodValDiff": round(l_s["goodVal"] - p_s["goodVal"], 2),
        "damageValDiff": round(l_s["damageVal"] - p_s["damageVal"], 2)
    }

    # Category DoD Breakdown
    dod_category_breakdown = {}
    for cat in VALID_CATS + ['UNCATEGORISED']:
        l_v = l_s["categoryValuation"].get(cat, 0.0)
        p_v = p_s["categoryValuation"].get(cat, 0.0)
        diff = l_v - p_v
        pct = (diff / max(1, p_v)) * 100 if p_v > 0 else 0.0
        dod_category_breakdown[cat] = {
            "prevVal": round(p_v, 2),
            "latestVal": round(l_v, 2),
            "diff": round(diff, 2),
            "diffPct": round(pct, 2)
        }
    dod_metrics["categoryBreakdown"] = dod_category_breakdown

    # WoW Metrics (7 days prior or earliest)
    wow_idx = max(0, len(dates_list) - 6)
    w_d = dates_list[wow_idx]
    w_s = daily_summaries[w_d]
    wow_metrics = {
        "latestDate": latest_d,
        "weekStartDate": w_d,
        "valDiff": round(l_s["totalValuation"] - w_s["totalValuation"], 2),
        "valDiffPct": round(((l_s["totalValuation"] - w_s["totalValuation"]) / max(1, w_s["totalValuation"])) * 100, 2),
        "qtyDiff": round(l_s["totalQty"] - w_s["totalQty"], 1)
    }
    wow_cat_breakdown = {}
    for cat in VALID_CATS + ['UNCATEGORISED']:
        l_v = l_s["categoryValuation"].get(cat, 0.0)
        w_v = w_s["categoryValuation"].get(cat, 0.0)
        diff = l_v - w_v
        pct = (diff / max(1, w_v)) * 100 if w_v > 0 else 0.0
        wow_cat_breakdown[cat] = {
            "weekStartVal": round(w_v, 2),
            "latestVal": round(l_v, 2),
            "diff": round(diff, 2),
            "diffPct": round(pct, 2)
        }
    wow_metrics["categoryBreakdown"] = wow_cat_breakdown

    # Consolidated Cache Payload
    cache_payload = {
        "status": "success",
        "month": "October 2026",
        "stockFolderPath": STOCK_DIR,
        "dates": dates_list,
        "latestDate": latest_d,
        "dailySummaries": daily_summaries,
        "dodMetrics": dod_metrics,
        "wowMetrics": wow_metrics,
        "autoSync": {
            "status": "ACTIVE",
            "lastSyncTime": time.strftime("%Y-%m-%d %H:%M:%S"),
            "latestFile": l_s["filename"],
            "totalIngestedFiles": len(dates_list),
            "schedule": "Every Day 08:30 AM (Morning Stock Drop)"
        }
    }

    # 5. Save Cache files
    print("\n5. Writing high-speed cache files...")
    with open(CACHE_FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(cache_payload, f, ensure_ascii=False)
    print(f"  [OK] Saved {CACHE_FILE_JSON} ({os.path.getsize(CACHE_FILE_JSON)/(1024*1024):.1f} MB)")

    with gzip.open(CACHE_FILE_GZ, "wt", encoding="utf-8") as f:
        json.dump(cache_payload, f, ensure_ascii=False)
    print(f"  [OK] Saved {CACHE_FILE_GZ} ({os.path.getsize(CACHE_FILE_GZ)/(1024*1024):.1f} MB)")

    with open(ROOT_CACHE_JSON, "w", encoding="utf-8") as f:
        json.dump(cache_payload, f, ensure_ascii=False)
    print(f"  [OK] Saved {ROOT_CACHE_JSON}")

    print(f"\n[DONE] Full October Stock Ingestion Finished in {time.time()-t_start:.1f}s!")

if __name__ == "__main__":
    run_full_october_ingest()
