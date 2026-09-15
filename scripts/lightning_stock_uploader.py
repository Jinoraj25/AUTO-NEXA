import os
import sqlite3
import pymysql
import pandas as pd
import numpy as np
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

def run():
    print("=================================================================")
    print("  LIGHTNING RUST-POWERED STOCK UPLOAD (SEP 01 - SEP 14)          ")
    print("=================================================================")

    # 1. Truncate Table
    m_conn = get_mysql_conn()
    m_cursor = m_conn.cursor()
    m_cursor.execute("TRUNCATE TABLE daily_stock_telemetry;")
    m_conn.commit()

    files = sorted(glob.glob(os.path.join(STOCK_DIR, "*.xlsx")))
    print(f"Found {len(files)} daily stock spreadsheets.")

    total_rows_imported = 0
    total_val_sum_cr = 0.0

    for fpath in files:
        fname = os.path.basename(fpath)
        date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
        stock_date = date_match.group(0) if date_match else fname.replace('AllGoodStock_', '').replace('.xlsx', '')

        print(f"\n⚡ Reading File: {fname} (Stock Date: {stock_date})...")
        t0 = time.time()

        # Read with Calamine Rust engine (50x faster)
        df = pd.read_excel(fpath, engine='calamine')
        read_time = time.time() - t0
        print(f"   -> Read {len(df):,} rows in {read_time:.2f} seconds!")

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
        file_val_cr = file_val_sum / 1e7
        total_val_sum_cr += file_val_cr
        total_rows_imported += len(df)

        print(f"   • Valuation on {stock_date}: ₹{file_val_cr:.2f} Cr (₹{file_val_sum:,.2f})")
        print(f"   • Uploading {len(df):,} rows to MySQL in batches of 10,000...")

        t1 = time.time()
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
            m_cursor.executemany("""
                INSERT INTO daily_stock_telemetry 
                (stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, chunk)
            m_conn.commit()

        print(f"   -> MySQL Upload Completed in {time.time()-t1:.2f} seconds!")
        del df, rows_batch

    m_conn.close()

    # Sync top 50,000 to SQLite for fallback
    if os.path.exists(SQLITE_DB_PATH):
        print("\nSyncing top stock records to SQLite fallback database...")
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
    print(f"🎉 ALL FULL DAILY STOCK FILES (SEP 01 - SEP 14) UPLOADED TO MYSQL!")
    print(f"   • Total Stock Telemetry Rows in MySQL: {total_rows_imported:,} rows")
    print(f"   • Total Stock Dates Uploaded: {len(files)} dates")
    print("=================================================================")

if __name__ == '__main__':
    run()
