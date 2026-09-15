import os
import sqlite3
import pymysql
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Jino@2003")
MYSQL_DB = os.environ.get("MYSQL_DB", "autonexa")

SQLITE_DB_PATH = os.path.join(os.getcwd(), 'data', 'autonexa.db')

RF_FILE = "C:/Users/SM0237/Downloads/Mapped_RF_SALES_JAN26-AUG26_Output.xlsx"
CF_SALES_FILE = "C:/Users/SM0237/Downloads/CF SALES JAN'26-AUG'26.xlsb"
CF_MAPPED_FILE = "C:/Users/SM0237/Downloads/CF SALES JAN-AUG MAPPED.xlsx"

state_to_region = {
    'TAMIL NADU': 'SOUTH', 'KARNATAKA': 'SOUTH', 'KERALA': 'SOUTH', 'TELANGANA': 'SOUTH', 'ANDHRA PRADESH': 'SOUTH',
    'MAHARASHTRA': 'WEST', 'GUJARAT': 'WEST', 'GOA': 'WEST',
    'DELHI': 'NORTH', 'HARYANA': 'NORTH', 'UTTAR PRADESH': 'NORTH', 'MADHYA PRADESH': 'NORTH', 'RAJASTHAN': 'NORTH', 'PUNJAB': 'NORTH',
    'WEST BENGAL': 'EAST', 'ODISHA': 'EAST', 'ASSAM': 'EAST', 'BIHAR': 'EAST', 'JHARKHAND': 'EAST'
}

def get_mysql_conn():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DB, charset='utf8mb4', autocommit=False
    )

def run_import():
    m_conn = get_mysql_conn()
    m_cursor = m_conn.cursor()
    m_cursor.execute("TRUNCATE TABLE daily_sales_consolidated;")
    m_conn.commit()

    print("1. Reading RF Sales Dataset...")
    rf_cols = ['InvoiceDate', 'Month', 'InvoiceNumber', 'ItemCode', 'ItemName', 'Brand', 'Category', 'Aggregate', 'Sub-Aggregate', 'Component', 'SaleQty', 'SaleValue', 'Margin', 'Margin%', 'Region', 'Remarks']
    df_rf = pd.read_excel(RF_FILE, usecols=lambda c: c in rf_cols)
    print(f"   -> Loaded {len(df_rf):,} RF sales rows.")

    rf_rows = []
    for _, r in df_rf.iterrows():
        tx_d = str(r.get('InvoiceDate', '2026-08-01'))[:10]
        m_str = str(r.get('Month', 'AUG')).upper()[:3]
        qty = float(pd.to_numeric(r.get('SaleQty'), errors='coerce') or 1.0)
        tot_rev = float(pd.to_numeric(r.get('SaleValue'), errors='coerce') or 0.0)
        u_price = round(tot_rev / qty, 2) if qty else tot_rev
        mar = float(pd.to_numeric(r.get('Margin'), errors='coerce') or 0.0)
        mar_p = float(pd.to_numeric(r.get('Margin%'), errors='coerce') or 0.0)

        rf_rows.append((
            tx_d, m_str, 'RF', str(r.get('InvoiceNumber', 'INV-RF')),
            str(r.get('ItemCode', '')), str(r.get('ItemName', '')),
            str(r.get('Brand', 'GENERIC')), str(r.get('Category', 'Mechanical Parts')),
            str(r.get('Aggregate', 'ENGINE')), str(r.get('Sub-Aggregate', 'FILTERS')),
            str(r.get('Component', '')), qty, u_price, tot_rev, mar, mar_p,
            str(r.get('Region', 'SOUTH')).upper(), str(r.get('Remarks', 'RF Daily Sales Dump'))
        ))

    print(f"   -> Inserting {len(rf_rows):,} RF rows into MySQL...")
    batch_size = 10000
    for i in range(0, len(rf_rows), batch_size):
        chunk = rf_rows[i:i+batch_size]
        m_cursor.executemany("""
            INSERT INTO daily_sales_consolidated 
            (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, chunk)
        m_conn.commit()
        print(f"      * MySQL RF: Inserted {min(i+batch_size, len(rf_rows)):,}/{len(rf_rows):,}")

    # Free memory
    del df_rf, rf_rows

    print("\n2. Reading CF Sales Datasets...")
    df_cf_sales = pd.read_excel(CF_SALES_FILE, engine='pyxlsb')
    df_cf_mapped = pd.read_excel(CF_MAPPED_FILE)
    print(f"   -> Loaded {len(df_cf_sales):,} CF sales rows.")

    df_cf = df_cf_sales.copy()
    if len(df_cf_mapped) == len(df_cf):
        df_cf['Aggregate'] = df_cf_mapped['Aggregate']
        df_cf['Sub-Aggregate'] = df_cf_mapped['Sub-Aggregate']
        df_cf['Component'] = df_cf_mapped['Component']
        df_cf['Category'] = df_cf_mapped['Category']
        df_cf['Remarks'] = df_cf_mapped['Remarks']

    del df_cf_sales, df_cf_mapped

    cf_rows = []
    for _, r in df_cf.iterrows():
        raw_date = r.get('Month')
        try:
            d_val = pd.to_datetime(raw_date, origin='1899-12-30', unit='D', errors='coerce')
            tx_d = d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else '2026-08-01'
            m_str = d_val.strftime('%b').upper() if pd.notnull(d_val) else 'AUG'
        except:
            tx_d = '2026-08-01'
            m_str = 'AUG'

        qty = float(pd.to_numeric(r.get('Sale Qty'), errors='coerce') or 1.0)
        tot_rev = float(pd.to_numeric(r.get('Total Sale Amount'), errors='coerce') or 0.0)
        u_price = round(tot_rev / qty, 2) if qty else tot_rev
        mar = float(pd.to_numeric(r.get('Margin'), errors='coerce') or 0.0)
        mar_p = float(pd.to_numeric(r.get('Margin %'), errors='coerce') or 0.0)
        st_upper = str(r.get('Outlet State', '')).upper().strip()
        reg = state_to_region.get(st_upper, 'SOUTH')

        cf_rows.append((
            tx_d, m_str, 'CF', str(r.get('Invoice No', 'INV-CF')),
            str(r.get('Item Code', '')), str(r.get('Item Name', '')),
            str(r.get('Make', 'GENERIC')), str(r.get('Category', 'Mechanical Parts')),
            str(r.get('Aggregate', 'ENGINE')), str(r.get('Sub-Aggregate', 'FILTERS')),
            str(r.get('Component', '')), qty, u_price, tot_rev, mar, mar_p,
            reg, str(r.get('Remarks', 'CF Daily Sales Dump'))
        ))

    print(f"   -> Inserting {len(cf_rows):,} CF rows into MySQL...")
    for i in range(0, len(cf_rows), batch_size):
        chunk = cf_rows[i:i+batch_size]
        m_cursor.executemany("""
            INSERT INTO daily_sales_consolidated 
            (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, chunk)
        m_conn.commit()
        print(f"      * MySQL CF: Inserted {min(i+batch_size, len(cf_rows)):,}/{len(cf_rows):,}")

    m_conn.close()

    # Sync to SQLite
    if os.path.exists(SQLITE_DB_PATH):
        print("\n3. Syncing to SQLite database...")
        m_conn = get_mysql_conn()
        m_cur = m_conn.cursor()
        m_cur.execute("SELECT transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks FROM daily_sales_consolidated;")
        
        s_conn = sqlite3.connect(SQLITE_DB_PATH)
        s_cur = s_conn.cursor()
        s_cur.execute("DELETE FROM daily_sales_consolidated;")
        
        while True:
            chunk = m_cur.fetchmany(10000)
            if not chunk: break
            s_cur.executemany("""
                INSERT INTO daily_sales_consolidated 
                (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, chunk)
            s_conn.commit()
            
        m_conn.close()
        s_conn.close()
        print("   -> SQLite Sync Completed!")

    print("\nSUCCESS! FULL JAN-AUG SALES DUMP (5.74 LAKH ROWS) IMPORTED TO MYSQL!")

if __name__ == '__main__':
    run_import()
