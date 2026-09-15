import os
import sqlite3
import pymysql
import pandas as pd
import numpy as np

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

def load_rf_sales():
    print("Reading RF Sales spreadsheet...")
    df = pd.read_excel(RF_FILE)
    print(f"Loaded {len(df):,} raw RF sales rows.")
    
    rows = []
    for _, r in df.iterrows():
        tx_date = str(r.get('InvoiceDate', '2026-08-01'))[:10]
        month_str = str(r.get('Month', 'AUG')).upper()[:3]
        inv_no = str(r.get('InvoiceNumber', 'INV-RF'))
        part_no = str(r.get('ItemCode', ''))
        desc = str(r.get('ItemName', ''))
        brand = str(r.get('Brand', 'GENERIC'))
        cat = str(r.get('Category', 'Mechanical Parts'))
        agg = str(r.get('Aggregate', 'ENGINE'))
        sub_agg = str(r.get('Sub-Aggregate', 'FILTERS'))
        comp = str(r.get('Component', desc))
        
        qty = float(pd.to_numeric(r.get('SaleQty'), errors='coerce') or 1.0)
        tot_rev = float(pd.to_numeric(r.get('SaleValue'), errors='coerce') or 0.0)
        unit_price = round(tot_rev / qty, 2) if qty else tot_rev
        margin = float(pd.to_numeric(r.get('Margin'), errors='coerce') or 0.0)
        margin_pct = float(pd.to_numeric(r.get('Margin%'), errors='coerce') or 0.0)
        region = str(r.get('Region', 'SOUTH')).upper()
        remarks = str(r.get('Remarks', 'RF Daily Sales Dump'))

        rows.append((
            tx_date, month_str, 'RF', inv_no, part_no, desc, brand, cat,
            agg, sub_agg, comp, qty, unit_price, tot_rev, margin, margin_pct, region, remarks
        ))
    return rows

def load_cf_sales():
    print("Reading CF Sales spreadsheet & mapping...")
    df_cf_sales = pd.read_excel(CF_SALES_FILE, engine='pyxlsb')
    df_cf_mapped = pd.read_excel(CF_MAPPED_FILE)
    print(f"Loaded {len(df_cf_sales):,} raw CF sales rows.")

    df_cf = df_cf_sales.copy()
    if len(df_cf_mapped) == len(df_cf):
        df_cf['Aggregate'] = df_cf_mapped['Aggregate']
        df_cf['Sub-Aggregate'] = df_cf_mapped['Sub-Aggregate']
        df_cf['Component'] = df_cf_mapped['Component']
        df_cf['Category'] = df_cf_mapped['Category']
        df_cf['Remarks'] = df_cf_mapped['Remarks']

    rows = []
    for _, r in df_cf.iterrows():
        # Handle Excel serial dates
        raw_date = r.get('Month')
        try:
            d_val = pd.to_datetime(raw_date, origin='1899-12-30', unit='D', errors='coerce')
            tx_date = d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else '2026-08-01'
            month_str = d_val.strftime('%b').upper() if pd.notnull(d_val) else 'AUG'
        except:
            tx_date = '2026-08-01'
            month_str = 'AUG'

        inv_no = str(r.get('Invoice No', 'INV-CF'))
        part_no = str(r.get('Item Code', ''))
        desc = str(r.get('Item Name', ''))
        brand = str(r.get('Make', 'GENERIC'))
        cat = str(r.get('Category', 'Mechanical Parts'))
        agg = str(r.get('Aggregate', 'ENGINE'))
        sub_agg = str(r.get('Sub-Aggregate', 'FILTERS'))
        comp = str(r.get('Component', desc))
        
        qty = float(pd.to_numeric(r.get('Sale Qty'), errors='coerce') or 1.0)
        tot_rev = float(pd.to_numeric(r.get('Total Sale Amount'), errors='coerce') or 0.0)
        unit_price = round(tot_rev / qty, 2) if qty else tot_rev
        margin = float(pd.to_numeric(r.get('Margin'), errors='coerce') or 0.0)
        margin_pct = float(pd.to_numeric(r.get('Margin %'), errors='coerce') or 0.0)
        
        st_upper = str(r.get('Outlet State', '')).upper().strip()
        region = state_to_region.get(st_upper, 'SOUTH')
        remarks = str(r.get('Remarks', 'CF Daily Sales Dump'))

        rows.append((
            tx_date, month_str, 'CF', inv_no, part_no, desc, brand, cat,
            agg, sub_agg, comp, qty, unit_price, tot_rev, margin, margin_pct, region, remarks
        ))
    return rows

def import_all_sales():
    rf_rows = load_rf_sales()
    cf_rows = load_cf_sales()
    all_rows = rf_rows + cf_rows

    print(f"\nTotal combined Jan-Aug Sales rows to import: {len(all_rows):,}")

    # 1. Update MySQL
    print("Connecting to MySQL...")
    m_conn = pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DB, charset='utf8mb4', autocommit=False
    )
    m_cursor = m_conn.cursor()
    m_cursor.execute("TRUNCATE TABLE daily_sales_consolidated;")
    
    batch_size = 5000
    migrated = 0
    for i in range(0, len(all_rows), batch_size):
        chunk = all_rows[i:i+batch_size]
        m_cursor.executemany("""
            INSERT INTO daily_sales_consolidated 
            (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, chunk)
        m_conn.commit()
        migrated += len(chunk)
        print(f"  -> MySQL: Imported {migrated:,}/{len(all_rows):,} sales records...")

    m_conn.close()

    # 2. Update SQLite
    if os.path.exists(SQLITE_DB_PATH):
        print("Updating SQLite daily_sales_consolidated...")
        s_conn = sqlite3.connect(SQLITE_DB_PATH)
        s_cursor = s_conn.cursor()
        s_cursor.execute("DELETE FROM daily_sales_consolidated;")
        
        s_cursor.executemany("""
            INSERT INTO daily_sales_consolidated 
            (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, all_rows)
        s_conn.commit()
        s_conn.close()
        print("  -> SQLite: Sales table synced!")

    print("\nALL LAKHS OF SALES RECORDS (JAN TO AUG) SUCCESSFULLY IMPORTED TO MYSQL & SQLITE!")

if __name__ == '__main__':
    import_all_sales()
