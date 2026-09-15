import os
import sqlite3
import pymysql
import pandas as pd
import numpy as np
import math
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Jino@2003")
MYSQL_DB = os.environ.get("MYSQL_DB", "autonexa")

SQLITE_DB_PATH = os.path.join(os.getcwd(), 'data', 'autonexa.db')

DL_DIR = r"C:\Users\SM0237\Downloads"
RF_FILE = os.path.join(DL_DIR, "RF SALES JAN'26-AUG'26.xlsx")
CF_FILE = os.path.join(DL_DIR, "CF SALES JAN'26-AUG'26.xlsb")
CF_MAPPED_FILE = os.path.join(DL_DIR, "CF SALES JAN-AUG MAPPED.xlsx")

state_to_region = {
    'TAMIL NADU': 'SOUTH', 'KARNATAKA': 'SOUTH', 'KERALA': 'SOUTH', 'TELANGANA': 'SOUTH', 'ANDHRA PRADESH': 'SOUTH',
    'MAHARASHTRA': 'WEST', 'GUJARAT': 'WEST', 'GOA': 'WEST',
    'DELHI': 'NORTH', 'HARYANA': 'NORTH', 'UTTAR PRADESH': 'NORTH', 'MADHYA PRADESH': 'NORTH', 'RAJASTHAN': 'NORTH', 'PUNJAB': 'NORTH',
    'WEST BENGAL': 'EAST', 'ODISHA': 'EAST', 'ASSAM': 'EAST', 'BIHAR': 'EAST', 'JHARKHAND': 'EAST'
}

months_order = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG']

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

def upload_monthwise():
    print("=================================================================")
    print("  STARTING MONTH-WISE SALES DUMP UPLOAD TO MYSQL (`autonexa`)    ")
    print("=================================================================")

    # 1. Reset Tables
    m_conn = get_mysql_conn()
    m_cursor = m_conn.cursor()
    m_cursor.execute("TRUNCATE TABLE daily_sales_consolidated;")
    m_conn.commit()

    # 2. Process RF Sales File
    print(f"\n📁 Reading RF Sales Spreadsheet: {RF_FILE}")
    t0 = time.time()
    df_rf = pd.read_excel(RF_FILE)
    print(f"   -> Loaded {len(df_rf):,} raw RF rows in {time.time()-t0:.2f}s.")

    df_rf['MonthStr'] = pd.to_datetime(df_rf.get('InvoiceDate'), errors='coerce').dt.strftime('%b').str.upper()
    df_rf['MonthKey'] = df_rf['MonthStr'].fillna('AUG')

    # 3. Process CF Sales File
    print(f"\n📁 Reading CF Sales Spreadsheet: {CF_FILE}")
    t1 = time.time()
    df_cf = pd.read_excel(CF_FILE, engine='pyxlsb')
    print(f"   -> Loaded {len(df_cf):,} raw CF rows in {time.time()-t1:.2f}s.")

    if os.path.exists(CF_MAPPED_FILE):
        print("   -> Merging CF Mappings...")
        df_cf_mapped = pd.read_excel(CF_MAPPED_FILE)
        if len(df_cf_mapped) == len(df_cf):
            df_cf['Aggregate'] = df_cf_mapped['Aggregate']
            df_cf['Sub-Aggregate'] = df_cf_mapped['Sub-Aggregate']
            df_cf['Component'] = df_cf_mapped['Component']
            df_cf['Category'] = df_cf_mapped['Category']
            df_cf['Remarks'] = df_cf_mapped['Remarks']

    df_cf['Date'] = pd.to_datetime(df_cf.get('Month'), origin='1899-12-30', unit='D', errors='coerce')
    df_cf['MonthKey'] = df_cf['Date'].dt.strftime('%b').str.upper().fillna('AUG')
    df_cf['StateUpper'] = df_cf.get('Outlet State', '').astype(str).str.upper().str.strip()
    df_cf['RegionKey'] = df_cf['StateUpper'].map(state_to_region).fillna('SOUTH')

    print("\n=================================================================")
    print("  UPLOADING MONTH BY MONTH (JAN -> FEB -> MAR -> ... -> AUG)     ")
    print("=================================================================")

    grand_total_rows = 0
    grand_total_revenue = 0.0

    for m in months_order:
        rf_m = df_rf[df_rf['MonthKey'] == m]
        cf_m = df_cf[df_cf['MonthKey'] == m]
        
        m_rows = []
        
        # Build RF tuples for month m
        for r in rf_m.itertuples():
            tx_d = clean_str(getattr(r, 'InvoiceDate', '2026-08-01'))[:10]
            qty = clean_float(getattr(r, 'SaleQty', 1.0), 1.0)
            tot_rev = clean_float(getattr(r, 'SaleValue', 0.0), 0.0)
            u_price = round(tot_rev / qty, 2) if qty > 0 else tot_rev
            mar = clean_float(getattr(r, 'Margin', 0.0), 0.0)
            mar_p = clean_float(getattr(r, 'Margin_pct', getattr(r, '_30', 0.0)), 0.0)

            m_rows.append((
                tx_d, m, 'RF', clean_str(getattr(r, 'InvoiceNumber', 'INV-RF'), 'INV-RF'),
                clean_str(getattr(r, 'ItemCode', '')), clean_str(getattr(r, 'ItemName', '')),
                clean_str(getattr(r, 'Brand', 'GENERIC'), 'GENERIC'), clean_str(getattr(r, 'Category', 'Mechanical Parts'), 'Mechanical Parts'),
                clean_str(getattr(r, 'Aggregate', 'ENGINE'), 'ENGINE'), clean_str(getattr(r, 'Sub_Aggregate', getattr(r, '_37', 'FILTERS')), 'FILTERS'),
                clean_str(getattr(r, 'Component', getattr(r, 'ItemName', ''))), qty, u_price, tot_rev, mar, mar_p,
                clean_str(getattr(r, 'Region', 'SOUTH'), 'SOUTH').upper(), clean_str(getattr(r, 'Remarks', 'RF Sales Dump'), 'RF Sales Dump')
            ))

        # Build CF tuples for month m
        for r in cf_m.itertuples():
            d_val = getattr(r, 'Date', None)
            tx_d = d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else '2026-08-01'
            qty = clean_float(getattr(r, '_17', 1.0) if hasattr(r, '_17') else 1.0, 1.0)
            tot_rev = clean_float(getattr(r, '_18', 0.0) if hasattr(r, '_18') else 0.0, 0.0)
            u_price = round(tot_rev / qty, 2) if qty > 0 else tot_rev
            mar = clean_float(getattr(r, '_20', 0.0) if hasattr(r, '_20') else 0.0, 0.0)
            mar_p = clean_float(getattr(r, '_21', 0.0) if hasattr(r, '_21') else 0.0, 0.0)
            reg = clean_str(getattr(r, 'RegionKey', 'SOUTH'), 'SOUTH')

            m_rows.append((
                tx_d, m, 'CF', clean_str(getattr(r, '_4', 'INV-CF'), 'INV-CF'),
                clean_str(getattr(r, '_12', '')), clean_str(getattr(r, '_13', '')),
                clean_str(getattr(r, 'Make', 'GENERIC'), 'GENERIC'), clean_str(getattr(r, 'Category', 'Mechanical Parts'), 'Mechanical Parts'),
                clean_str(getattr(r, 'Aggregate', 'ENGINE'), 'ENGINE'), clean_str(getattr(r, 'Sub_Aggregate', 'FILTERS'), 'FILTERS'),
                clean_str(getattr(r, 'Component', getattr(r, '_13', ''))), qty, u_price, tot_rev, mar, mar_p,
                reg, clean_str(getattr(r, 'Remarks', 'CF Sales Dump'), 'CF Sales Dump')
            ))

        m_rev = sum(r[13] for r in m_rows)
        m_cnt = len(m_rows)
        grand_total_rows += m_cnt
        grand_total_revenue += m_rev

        print(f"\n▶ Uploading Month: {m} (2026)")
        print(f"   • Total Line Items: {m_cnt:,} (RF: {len(rf_m):,}, CF: {len(cf_m):,})")
        print(f"   • Month Sales Valuation: ₹{m_rev/1e7:.2f} Cr (₹{m_rev:,.2f})")

        # Batch insert to MySQL for month m
        batch_size = 10000
        for i in range(0, len(m_rows), batch_size):
            chunk = m_rows[i:i+batch_size]
            m_cursor.executemany("""
                INSERT INTO daily_sales_consolidated 
                (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, chunk)
            m_conn.commit()
            print(f"     -> MySQL: Inserted batch {i+len(chunk):,}/{m_cnt:,} for {m}")

    m_conn.close()

    # Sync top 50,000 to SQLite for offline fallback
    if os.path.exists(SQLITE_DB_PATH):
        print("\nSyncing MySQL month-wise records to local SQLite fallback database...")
        m_conn = get_mysql_conn()
        m_cur = m_conn.cursor()
        m_cur.execute("SELECT transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks FROM daily_sales_consolidated LIMIT 50000;")
        
        s_conn = sqlite3.connect(SQLITE_DB_PATH)
        s_cur = s_conn.cursor()
        s_cur.execute("DELETE FROM daily_sales_consolidated;")
        
        chunk = m_cur.fetchall()
        s_cur.executemany("""
            INSERT INTO daily_sales_consolidated 
            (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, chunk)
        s_conn.commit()
        m_conn.close()
        s_conn.close()
        print(" -> SQLite Sync Completed!")

    print("\n=================================================================")
    print(f"🎉 MONTH-WISE UPLOAD COMPLETED SUCCESSFULLY!")
    print(f"   • Total Months Uploaded: 8 Months (Jan 2026 to Aug 2026)")
    print(f"   • Total Sales Rows in MySQL: {grand_total_rows:,} rows")
    print(f"   • Total Revenue Consolidated: ₹{grand_total_revenue/1e7:.2f} Cr")
    print("=================================================================")

if __name__ == '__main__':
    upload_monthwise()
