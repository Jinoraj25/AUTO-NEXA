import os
import sys
import time
import re
import math
import glob
import json
import pymysql
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Jino@2003")
MYSQL_DB = os.environ.get("MYSQL_DB", "autonexa")

def clean_float(val, default=0.0):
    try:
        if val is None or pd.isna(val):
            return default
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (ValueError, TypeError):
        return default

def clean_str(val, default=""):
    if pd.isna(val) or val is None:
        return default
    s = str(val).strip()
    return default if s.lower() in ('nan', 'none', 'null') else s

def get_mysql_conn():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DB, charset='utf8mb4', autocommit=False
    )

def sync_stock_file(fpath):
    fname = os.path.basename(fpath)
    m1 = re.search(r'(\d{1,2})[\s_\-\.\']*([A-Za-z]{3})[\s_\-\.\']*\'?(\d{2,4})', fname)
    if m1:
        day = int(m1.group(1))
        mon_map = {'JAN':'Jan','FEB':'Feb','MAR':'Mar','APR':'Apr','MAY':'May','JUN':'Jun','JUL':'Jul','AUG':'Aug','SEP':'Sep','OCT':'Oct','NOV':'Nov','DEC':'Dec'}
        mon = mon_map.get(m1.group(2).upper(), 'Sep')
        yr = m1.group(3)
        if len(yr) == 2: yr = '20' + yr
        stock_date = f'{day:02d}-{mon}-{yr}'
    else:
        date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
        stock_date = date_match.group(0) if date_match else fname.replace('AllGoodStock_', '').replace('.xlsx', '').replace('.xlsb', '')

    print(f"⚡ AUTO-SYNC STOCK TO MYSQL: Processing {fname} (Date: {stock_date})...")
    t0 = time.time()

    try:
        df = pd.read_excel(fpath, engine='calamine')
    except Exception:
        df = pd.read_excel(fpath)

    df['ManPart'] = df.get('ManPart', '').fillna('')
    df['ItemDesc'] = df.get('ItemDesc', '').fillna('')
    df['BRAND'] = df.get('BRAND', 'GENERIC').fillna('GENERIC')
    df['CATEGORY'] = df.get('CATEGORY', 'OEM').fillna('OEM')
    df['Line Code'] = df.get('Line Code', '').fillna('')
    df['Branch'] = df.get('Branch', '').fillna('')
    df['BRANCH NAME'] = df.get('BRANCH NAME', '').fillna('')
    df['TAG'] = df.get('TAG', 'CONSIDER').fillna('CONSIDER')

    df['Qty'] = pd.to_numeric(df.get('Qty'), errors='coerce').fillna(0.0)
    df['UnitCost'] = pd.to_numeric(df.get('UnitCost'), errors='coerce').fillna(0.0)
    df['MRP'] = pd.to_numeric(df.get('MRP'), errors='coerce').fillna(0.0)
    df['Value'] = pd.to_numeric(df.get('Value'), errors='coerce').fillna(0.0)
    df['AgeDays'] = pd.to_numeric(df.get('AgeDays'), errors='coerce').fillna(0).astype(int)

    file_val_sum = float(df['Value'].sum())
    total_rows = len(df)

    conn = get_mysql_conn()
    cur = conn.cursor()

    # Clear previous snapshot for this exact date to prevent duplicates
    cur.execute("DELETE FROM daily_stock_telemetry WHERE stock_date = %s", (stock_date,))
    conn.commit()

    rows_batch = []
    for r in df.itertuples():
        rows_batch.append((
            stock_date, fname,
            clean_str(getattr(r, 'ManPart', '')),
            clean_str(getattr(r, 'ItemDesc', '')),
            clean_str(getattr(r, 'BRAND', 'GENERIC'), 'GENERIC'),
            clean_str(getattr(r, 'CATEGORY', 'OEM'), 'OEM'),
            clean_str(getattr(r, 'Line_Code', getattr(r, '_8', ''))),
            clean_str(getattr(r, 'Branch', '')),
            clean_str(getattr(r, 'BRANCH_NAME', getattr(r, '_3', ''))),
            clean_float(getattr(r, 'Qty', 0)),
            clean_float(getattr(r, 'UnitCost', 0)),
            clean_float(getattr(r, 'MRP', 0)),
            clean_float(getattr(r, 'Value', 0)),
            int(clean_float(getattr(r, 'AgeDays', 0))),
            clean_str(getattr(r, 'TAG', 'CONSIDER'), 'CONSIDER')
        ))

    batch_size = 10000
    for i in range(0, len(rows_batch), batch_size):
        chunk = rows_batch[i:i+batch_size]
        cur.executemany("""
            INSERT INTO daily_stock_telemetry 
            (stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, chunk)
        conn.commit()

    conn.close()
    print(f"✅ AUTO-SYNC COMPLETED: {total_rows:,} rows inserted for {stock_date} in {time.time()-t0:.2f}s! Valuation: RS {file_val_sum/1e7:.2f} Cr")
    return {"status": "success", "date": stock_date, "rowCount": total_rows, "valuation": file_val_sum}

def sync_sales_file(fpath, channel_type='RF'):
    fname = os.path.basename(fpath)
    print(f"⚡ AUTO-SYNC SALES TO MYSQL: Processing {fname} ({channel_type})...")
    t0 = time.time()

    try:
        df = pd.read_excel(fpath, engine='calamine')
    except Exception:
        try:
            df = pd.read_excel(fpath, engine='pyxlsb')
        except Exception:
            df = pd.read_csv(fpath)

    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    
    col_part = cols_lower.get('manpart', cols_lower.get('itemid(mytvs)', cols_lower.get('part_number', cols_lower.get('sku', df.columns[0]))))
    col_desc = cols_lower.get('itemdesc', cols_lower.get('description', cols_lower.get('part desc', df.columns[1] if len(df.columns)>1 else df.columns[0])))
    col_qty = cols_lower.get('qty', cols_lower.get('quantity', cols_lower.get('qty_sold', df.columns[2] if len(df.columns)>2 else df.columns[0])))
    col_price = cols_lower.get('unitprice', cols_lower.get('unit_price', cols_lower.get('rate', cols_lower.get('price', df.columns[3] if len(df.columns)>3 else df.columns[0]))))

    conn = get_mysql_conn()
    cur = conn.cursor()

    rows_batch = []
    total_rev = 0.0

    for _, r in df.iterrows():
        part_no = clean_str(r.get(col_part, ''))
        desc = clean_str(r.get(col_desc, ''))
        qty = clean_float(r.get(col_qty, 1), 1.0)
        price = clean_float(r.get(col_price, 250), 250.0)
        rev = qty * price
        total_rev += rev

        month_match = re.search(r'(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)', fname.upper())
        month_code = month_match.group(0) if month_match else 'SEP'
        tx_date = f"2026-{month_code}-15"

        rows_batch.append((
            tx_date, month_code, channel_type,
            'INV-DAILY-AUTO', part_no, desc,
            'GENERIC', 'Mechanical Parts', 'ENGINE', 'FILTERS', desc,
            qty, price, rev, rev * 0.15, 15.0, 'SOUTH', 'Daily Upload Auto-Sync'
        ))

    batch_size = 10000
    for i in range(0, len(rows_batch), batch_size):
        chunk = rows_batch[i:i+batch_size]
        cur.executemany("""
            INSERT INTO daily_sales_consolidated
            (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, chunk)
        conn.commit()

    conn.close()
    print(f"✅ AUTO-SYNC SALES COMPLETED: {len(rows_batch):,} rows inserted for {channel_type} in {time.time()-t0:.2f}s! Total Revenue: RS {total_rev/1e7:.2f} Cr")
    return {"status": "success", "rowCount": len(rows_batch), "revenue": total_rev}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        f_type = sys.argv[1]
        f_path = sys.argv[2]
        if f_type == 'stock':
            sync_stock_file(f_path)
        elif f_type == 'sales':
            c_type = sys.argv[3] if len(sys.argv) > 3 else 'RF'
            sync_sales_file(f_path, c_type)
