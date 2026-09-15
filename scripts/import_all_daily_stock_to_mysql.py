import os
import sqlite3
import pymysql
import openpyxl
import math
import sys
import glob
import time
import re

sys.stdout.reconfigure(encoding='utf-8')

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Jino@2003")
MYSQL_DB = os.environ.get("MYSQL_DB", "autonexa")

SQLITE_DB_PATH = os.path.join(os.getcwd(), 'data', 'autonexa.db')
STOCK_DIR = r"C:\Users\SM0237\Downloads\STOCK_SEP_TEMP"

def clean_float(val, default=0.0):
    try:
        if val is None:
            return default
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (ValueError, TypeError):
        return default

def clean_str(val, default=""):
    if val is None:
        return default
    s = str(val).strip()
    return default if s.lower() in ('nan', 'none', 'null') else s

def get_mysql_conn():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DB, charset='utf8mb4', autocommit=False
    )

def run_import():
    print("=================================================================")
    print("  UPLOADING ALL DAILY STOCK FILES (SEP 01 - SEP 14) TO MYSQL     ")
    print("=================================================================")

    # 1. Truncate Table
    m_conn = get_mysql_conn()
    m_cursor = m_conn.cursor()
    m_cursor.execute("TRUNCATE TABLE daily_stock_telemetry;")
    m_conn.commit()

    files = sorted(glob.glob(os.path.join(STOCK_DIR, "*.xlsx")))
    print(f"Found {len(files)} daily stock spreadsheets in temp folder.")

    total_rows_imported = 0
    total_val_sum_cr = 0.0

    for fpath in files:
        fname = os.path.basename(fpath)
        # Extract stock date e.g. 01-Sep-2026
        date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
        stock_date = date_match.group(0) if date_match else fname.replace('AllGoodStock_', '').replace('.xlsx', '')

        print(f"\n📁 Processing File: {fname} (Stock Date: {stock_date})")
        t0 = time.time()

        wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
        sheet = wb.active

        # Extract Header map
        headers = [str(c.value).strip() if c.value else '' for c in next(sheet.iter_rows(max_row=1))]
        hmap = {name: idx for idx, name in enumerate(headers)}

        idx_part = hmap.get('ManPart', 11)
        idx_desc = hmap.get('ItemDesc', 12)
        idx_brand = hmap.get('BRAND', 8)
        idx_cat = hmap.get('CATEGORY', 9)
        idx_line = hmap.get('Line Code', 7)
        idx_bcode = hmap.get('Branch', 1)
        idx_bname = hmap.get('BRANCH NAME', 2)
        idx_qty = hmap.get('Qty', 13)
        idx_ucost = hmap.get('UnitCost', 14)
        idx_mrp = hmap.get('MRP', 15)
        idx_val = hmap.get('Value', 16)
        idx_age = hmap.get('AgeDays', 19)
        idx_tag = hmap.get('TAG', 6)

        rows_batch = []
        date_val_sum = 0.0

        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row): continue
            
            part_no = clean_str(row[idx_part] if idx_part < len(row) else '')
            desc = clean_str(row[idx_desc] if idx_desc < len(row) else '')
            brand = clean_str(row[idx_brand] if idx_brand < len(row) else 'GENERIC')
            cat = clean_str(row[idx_cat] if idx_cat < len(row) else 'OEM')
            line_c = clean_str(row[idx_line] if idx_line < len(row) else '')
            b_code = clean_str(row[idx_bcode] if idx_bcode < len(row) else '')
            b_name = clean_str(row[idx_bname] if idx_bname < len(row) else '')
            
            qty = clean_float(row[idx_qty] if idx_qty < len(row) else 0)
            ucost = clean_float(row[idx_ucost] if idx_ucost < len(row) else 0)
            mrp = clean_float(row[idx_mrp] if idx_mrp < len(row) else 0)
            val = clean_float(row[idx_val] if idx_val < len(row) else 0)
            age = int(clean_float(row[idx_age] if idx_age < len(row) else 0))
            tag = clean_str(row[idx_tag] if idx_tag < len(row) else 'CONSIDER')

            date_val_sum += val

            rows_batch.append((
                stock_date, fname, part_no, desc, brand, cat, line_c, b_code, b_name,
                qty, ucost, mrp, val, age, tag
            ))

        file_rows = len(rows_batch)
        total_rows_imported += file_rows
        file_val_cr = date_val_sum / 1e7
        total_val_sum_cr += file_val_cr

        print(f"   • Extracted {file_rows:,} stock items in {time.time()-t0:.2f}s.")
        print(f"   • Stock Valuation on {stock_date}: ₹{file_val_cr:.2f} Cr (₹{date_val_sum:,.2f})")

        # Commit to MySQL in batches of 10,000
        batch_size = 10000
        for i in range(0, len(rows_batch), batch_size):
            chunk = rows_batch[i:i+batch_size]
            m_cursor.executemany("""
                INSERT INTO daily_stock_telemetry 
                (stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, chunk)
            m_conn.commit()

        wb.close()
        del rows_batch

    m_conn.close()

    # Sync top 50,000 stock rows to SQLite for fallback
    if os.path.exists(SQLITE_DB_PATH):
        print("\nSyncing latest stock records to SQLite fallback database...")
        m_conn = get_mysql_conn()
        m_cur = m_conn.cursor()
        m_cur.execute("SELECT stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag FROM daily_stock_telemetry LIMIT 50000;")
        
        s_conn = sqlite3.connect(SQLITE_DB_PATH)
        s_cur = s_conn.cursor()
        s_cur.execute("DELETE FROM daily_stock_telemetry;")
        
        chunk = m_cur.fetchall()
        s_cur.executemany("""
            INSERT INTO daily_stock_telemetry 
            (stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, chunk)
        s_conn.commit()
        m_conn.close()
        s_conn.close()
        print(" -> SQLite Stock Sync Completed!")

    print("\n=================================================================")
    print(f"🎉 ALL DAILY STOCK FILES (SEP 01 - SEP 14) UPLOADED TO MYSQL!")
    print(f"   • Total Stock Telemetry Rows in MySQL: {total_rows_imported:,} rows")
    print(f"   • Total Stock Dates Uploaded: {len(files)} dates")
    print("=================================================================")

if __name__ == '__main__':
    run_import()
