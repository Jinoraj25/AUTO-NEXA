import os
import sqlite3
import pymysql

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Jino@2003")
MYSQL_DB = os.environ.get("MYSQL_DB", "autonexa")

SQLITE_DB_PATH = os.path.join(os.getcwd(), 'data', 'autonexa.db')

def setup_mysql_database():
    print(f"Connecting to MySQL server at {MYSQL_HOST}:{MYSQL_PORT}...")
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        autocommit=True
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print(f"Database `{MYSQL_DB}` created/verified successfully.")
    conn.close()

def get_mysql_conn():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset='utf8mb4',
        autocommit=False
    )

def create_tables():
    conn = get_mysql_conn()
    cursor = conn.cursor()

    print("Dropping old table definitions if existing...")
    cursor.execute("DROP TABLE IF EXISTS mapping_reference_master;")
    cursor.execute("DROP TABLE IF EXISTS daily_stock_telemetry;")
    cursor.execute("DROP TABLE IF EXISTS daily_sales_consolidated;")

    print("Creating MySQL Table 1: mapping_reference_master...")
    cursor.execute("""
    CREATE TABLE mapping_reference_master (
        id INT AUTO_INCREMENT PRIMARY KEY,
        part_number VARCHAR(100),
        description VARCHAR(255),
        brand_make VARCHAR(100),
        category VARCHAR(100),
        aggregate VARCHAR(100),
        sub_aggregate VARCHAR(100),
        component VARCHAR(255),
        confidence VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_part_num (part_number),
        INDEX idx_agg (aggregate),
        INDEX idx_sub_agg (sub_aggregate),
        INDEX idx_comp (component(100))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    print("Creating MySQL Table 2: daily_stock_telemetry...")
    cursor.execute("""
    CREATE TABLE daily_stock_telemetry (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock_date VARCHAR(20),
        filename VARCHAR(255),
        part_number VARCHAR(100),
        description VARCHAR(255),
        brand VARCHAR(100),
        category VARCHAR(100),
        line_code VARCHAR(50),
        branch_code VARCHAR(50),
        branch_name VARCHAR(100),
        stock_qty DECIMAL(12, 2),
        unit_cost DECIMAL(12, 2),
        mrp DECIMAL(12, 2),
        total_valuation DECIMAL(15, 2),
        age_days INT,
        tag VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_stock_dt (stock_date),
        INDEX idx_stock_part (part_number),
        INDEX idx_stock_branch (branch_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    print("Creating MySQL Table 3: daily_sales_consolidated...")
    cursor.execute("""
    CREATE TABLE daily_sales_consolidated (
        id INT AUTO_INCREMENT PRIMARY KEY,
        transaction_date VARCHAR(20),
        month_code VARCHAR(20),
        channel_type VARCHAR(20),
        invoice_number VARCHAR(100),
        part_number VARCHAR(100),
        description VARCHAR(255),
        brand VARCHAR(100),
        category VARCHAR(100),
        aggregate VARCHAR(100),
        sub_aggregate VARCHAR(100),
        component VARCHAR(255),
        qty_sold DECIMAL(12, 2),
        unit_price DECIMAL(12, 2),
        total_revenue DECIMAL(15, 2),
        gross_margin DECIMAL(15, 2),
        margin_pct DECIMAL(8, 2),
        region VARCHAR(50),
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_sales_dt (transaction_date),
        INDEX idx_sales_channel (channel_type),
        INDEX idx_sales_part (part_number)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    conn.close()
    print("All 3 MySQL tables created successfully.")

def migrate_data():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"SQLite database not found at {SQLITE_DB_PATH}")
        return

    lite_conn = sqlite3.connect(SQLITE_DB_PATH)
    lite_cursor = lite_conn.cursor()

    mysql_conn = get_mysql_conn()
    mysql_cursor = mysql_conn.cursor()

    # 1. Migrate mapping_reference_master
    lite_cursor.execute("SELECT COUNT(*) FROM mapping_reference_master;")
    sqlite_map_count = lite_cursor.fetchone()[0]

    print(f"Migrating {sqlite_map_count} mapping_reference_master records to MySQL in batches of 10,000...")
    lite_cursor.execute("SELECT part_number, description, brand_make, category, aggregate, sub_aggregate, component, confidence FROM mapping_reference_master;")
    
    batch_size = 10000
    migrated = 0
    while True:
        rows = lite_cursor.fetchmany(batch_size)
        if not rows:
            break
        mysql_cursor.executemany("""
            INSERT INTO mapping_reference_master 
            (part_number, description, brand_make, category, aggregate, sub_aggregate, component, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, rows)
        mysql_conn.commit()
        migrated += len(rows)
        print(f"  -> Migrated {migrated}/{sqlite_map_count} mapping records...")

    # 2. Migrate daily_stock_telemetry
    lite_cursor.execute("SELECT COUNT(*) FROM daily_stock_telemetry;")
    sqlite_stock_count = lite_cursor.fetchone()[0]

    print(f"Migrating {sqlite_stock_count} daily_stock_telemetry records to MySQL...")
    lite_cursor.execute("SELECT stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag FROM daily_stock_telemetry;")
    
    rows = lite_cursor.fetchall()
    mysql_cursor.executemany("""
        INSERT INTO daily_stock_telemetry 
        (stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)
    mysql_conn.commit()
    print(f"  -> Migrated {len(rows)} daily stock records.")

    # 3. Migrate daily_sales_consolidated
    lite_cursor.execute("SELECT COUNT(*) FROM daily_sales_consolidated;")
    sqlite_sales_count = lite_cursor.fetchone()[0]

    print(f"Migrating {sqlite_sales_count} daily_sales_consolidated records to MySQL...")
    lite_cursor.execute("SELECT transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks FROM daily_sales_consolidated;")
    
    rows = lite_cursor.fetchall()
    mysql_cursor.executemany("""
        INSERT INTO daily_sales_consolidated 
        (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)
    mysql_conn.commit()
    print(f"  -> Migrated {len(rows)} daily sales records.")

    mysql_conn.close()
    lite_conn.close()
    print("🎉 MySQL Database Setup & Migration Completed Successfully!")

if __name__ == '__main__':
    setup_mysql_database()
    create_tables()
    migrate_data()
