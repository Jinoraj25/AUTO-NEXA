import os
import sys
import glob
import time
import sqlite3
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

CATALOGUE_DIR = r"D:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\OVERALL CATALOGUE"
PROJECT_DIR = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT"
DB_PATH = os.path.join(PROJECT_DIR, "data", "overall_catalogue.db")

def parse_excel_file(file_path):
    """
    Worker process function: Reads a single Excel file using openpyxl read_only mode
    and returns a list of tuples representing rows.
    """
    import openpyxl
    rows_data = []
    filename = os.path.basename(file_path)
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet = wb.active
        iterator = sheet.iter_rows(values_only=True)
        header = next(iterator, None) # skip header
        
        for row in iterator:
            if not row or not any(row):
                continue
            # Ensure row length is 21
            padded_row = list(row) + [None] * (21 - len(row)) if len(row) < 21 else list(row[:21])
            
            # Clean numerical values
            tax_rate = float(padded_row[5]) if padded_row[5] is not None and str(padded_row[5]).replace('.','',1).isdigit() else 0.0
            list_price = float(padded_row[8]) if padded_row[8] is not None and str(padded_row[8]).replace('.','',1).isdigit() else 0.0
            mrp_price = float(padded_row[9]) if padded_row[9] is not None and str(padded_row[9]).replace('.','',1).isdigit() else 0.0
            
            # Format row
            cleaned = (
                str(padded_row[0]).strip() if padded_row[0] is not None else '',
                str(padded_row[1]).strip() if padded_row[1] is not None else '',
                str(padded_row[2]).strip() if padded_row[2] is not None else '',
                str(padded_row[3]).strip() if padded_row[3] is not None else '',
                str(padded_row[4]).strip() if padded_row[4] is not None else '',
                tax_rate,
                str(padded_row[6]).strip() if padded_row[6] is not None else '',
                str(padded_row[7]).strip() if padded_row[7] is not None else '',
                list_price,
                mrp_price,
                str(padded_row[10]).strip() if padded_row[10] is not None else '',
                str(padded_row[11]).strip() if padded_row[11] is not None else '',
                str(padded_row[12]).strip() if padded_row[12] is not None else '',
                str(padded_row[13]).strip() if padded_row[13] is not None else '',
                str(padded_row[14]).strip() if padded_row[14] is not None else '',
                str(padded_row[15]).strip() if padded_row[15] is not None else '',
                str(padded_row[16]).strip() if padded_row[16] is not None else '',
                str(padded_row[17]).strip() if padded_row[17] is not None else '',
                str(padded_row[18]).strip() if padded_row[18] is not None else '',
                str(padded_row[19]).strip() if padded_row[19] is not None else '',
                str(padded_row[20]).strip() if padded_row[20] is not None else ''
            )
            rows_data.append(cleaned)
        wb.close()
        return filename, len(rows_data), rows_data, None
    except Exception as e:
        return filename, 0, [], str(e)

def init_db(conn):
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA cache_size = -128000;") # 128MB cache
    conn.execute("PRAGMA temp_store = MEMORY;")
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS overall_catalogue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        line_code TEXT,
        brand_name TEXT,
        line_code_part_number TEXT,
        part_description TEXT,
        hsn_code TEXT,
        tax_rate REAL,
        price_type TEXT,
        sales_uom TEXT,
        list_price REAL,
        mrp_price REAL,
        sales_price_group TEXT,
        vehicle_segment TEXT,
        vehicle_make TEXT,
        vehicle_model TEXT,
        vehicle_sub_model TEXT,
        vehicle_fuel_type TEXT,
        vehicle_from_year TEXT,
        vehicle_to_year TEXT,
        aggregate TEXT,
        sub_aggregate TEXT,
        components TEXT
    )
    """)
    conn.commit()

def create_indexes(conn):
    print("Building database B-Tree indexes for fast queries...")
    t0 = time.time()
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cat_part_no ON overall_catalogue(line_code_part_number);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cat_brand ON overall_catalogue(brand_name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cat_make ON overall_catalogue(vehicle_make);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cat_model ON overall_catalogue(vehicle_model);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cat_segment ON overall_catalogue(vehicle_segment);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cat_aggregate ON overall_catalogue(aggregate);")
    conn.commit()
    print(f"Indexes built in {time.time()-t0:.2f} seconds.")

    print("Building SQLite FTS5 Full-Text Search index...")
    t1 = time.time()
    conn.execute("DROP TABLE IF EXISTS overall_catalogue_fts;")
    conn.execute("""
    CREATE VIRTUAL TABLE overall_catalogue_fts USING fts5(
        part_description,
        line_code_part_number,
        brand_name,
        vehicle_make,
        vehicle_model,
        vehicle_sub_model,
        aggregate,
        sub_aggregate,
        components,
        content='overall_catalogue',
        content_rowid='id'
    );
    """)
    conn.execute("""
    INSERT INTO overall_catalogue_fts(rowid, part_description, line_code_part_number, brand_name, vehicle_make, vehicle_model, vehicle_sub_model, aggregate, sub_aggregate, components)
    SELECT id, part_description, line_code_part_number, brand_name, vehicle_make, vehicle_model, vehicle_sub_model, aggregate, sub_aggregate, components
    FROM overall_catalogue;
    """)
    conn.commit()
    print(f"FTS5 Search Index created successfully in {time.time()-t1:.2f} seconds.")

def main():
    start_time = time.time()
    files = sorted(glob.glob(os.path.join(CATALOGUE_DIR, "Sheet_*.xlsx")))
    if not files:
        print(f"Error: No Sheet_*.xlsx files found in {CATALOGUE_DIR}")
        return

    print(f"==========================================================")
    print(f"  Starting Ingestion for {len(files)} Catalogue Files")
    print(f"  Source: {CATALOGUE_DIR}")
    print(f"  Target DB: {DB_PATH}")
    print(f"==========================================================")

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        print(f"Removing existing database file at {DB_PATH} for fresh build...")
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    total_rows_inserted = 0
    completed_files = 0
    max_workers = min(os.cpu_count() or 4, 8) # Balance CPU memory
    print(f"Launching {max_workers} worker processes...")

    insert_sql = """
    INSERT INTO overall_catalogue (
        line_code, brand_name, line_code_part_number, part_description, hsn_code,
        tax_rate, price_type, sales_uom, list_price, mrp_price, sales_price_group,
        vehicle_segment, vehicle_make, vehicle_model, vehicle_sub_model,
        vehicle_fuel_type, vehicle_from_year, vehicle_to_year, aggregate,
        sub_aggregate, components
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(parse_excel_file, f): f for f in files}
        
        for future in as_completed(futures):
            filename, row_count, rows_data, err = future.result()
            completed_files += 1
            if err:
                print(f"[{completed_files}/{len(files)}] ERROR parsing {filename}: {err}")
            else:
                if rows_data:
                    conn.executemany(insert_sql, rows_data)
                    conn.commit()
                    total_rows_inserted += row_count
                elapsed = time.time() - start_time
                print(f"[{completed_files}/{len(files)}] Imported {filename}: {row_count:,} rows | Total: {total_rows_inserted:,} rows ({elapsed:.1f}s)")

    print(f"\nAll files imported successfully. Total rows inserted: {total_rows_inserted:,}")
    
    # Create Indexes
    create_indexes(conn)
    
    conn.close()

    db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    total_time = time.time() - start_time
    print(f"==========================================================")
    print(f"  INGESTION COMPLETE!")
    print(f"  Total Rows: {total_rows_inserted:,}")
    print(f"  DB Size: {db_size_mb:.2f} MB")
    print(f"  Total Time: {total_time/60:.2f} minutes")
    print(f"==========================================================")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
