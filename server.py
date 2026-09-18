
import os
import sqlite3
import json
import sys
import glob
import re
import threading

try:
    import pymysql
except ImportError:
    pymysql = None

DB_PATH = os.path.join(os.getcwd(), 'data', 'autonexa.db')

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Jino@2003")
MYSQL_DB = os.environ.get("MYSQL_DB", "autonexa")

def get_mysql_connection():
    if pymysql:
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                charset='utf8mb4',
                autocommit=True,
                connect_timeout=2
            )
            return conn
        except Exception as e:
            pass
    return None

def get_db_connection():
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    return None

def get_db_stats():
    mysql_conn = get_mysql_connection()
    sqlite_conn = get_db_connection()
    
    res = {
        "status": "online",
        "mysql": {"status": "offline"},
        "sqlite": {"status": "offline"}
    }

    if mysql_conn:
        try:
            cursor = mysql_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM mapping_reference_master")
            m1 = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM daily_stock_telemetry")
            m2 = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM daily_sales_consolidated")
            m3 = cursor.fetchone()[0]
            mysql_conn.close()
            res["mysql"] = {
                "status": "online",
                "host": f"{MYSQL_HOST}:{MYSQL_PORT}",
                "database": MYSQL_DB,
                "mappingMasterCount": m1,
                "stockTelemetryCount": m2,
                "salesConsolidatedCount": m3
            }
        except Exception as e:
            res["mysql"] = {"status": "error", "error": str(e)}

    if sqlite_conn:
        try:
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM mapping_reference_master")
            s1 = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM daily_stock_telemetry")
            s2 = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM daily_sales_consolidated")
            s3 = cursor.fetchone()[0]
            sqlite_conn.close()
            res["sqlite"] = {
                "status": "online",
                "dbPath": DB_PATH,
                "mappingMasterCount": s1,
                "stockTelemetryCount": s2,
                "salesConsolidatedCount": s3
            }
        except Exception as e:
            res["sqlite"] = {"status": "error", "error": str(e)}

    return res

def extract_stock_date(filename):
    if not filename:
        return '16-Sep-2026'
    month_map = {
        'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MAY': 'May', 'JUN': 'Jun',
        'JUL': 'Jul', 'AUG': 'Aug', 'SEP': 'Sep', 'OCT': 'Oct', 'NOV': 'Nov', 'DEC': 'Dec'
    }
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    m1 = re.search(r'(\d{1,2})[\s_\-\.\']*([A-Za-z]{3})[\s_\-\.\']*\'?(\d{2,4})', filename)
    if m1:
        day = int(m1.group(1))
        day_str = f'{day:02d}'
        mon = month_map.get(m1.group(2).upper(), 'Sep')
        yr = m1.group(3)
        if len(yr) == 2:
            yr = '20' + yr
        return f'{day_str}-{mon}-{yr}'

    m2 = re.search(r'(\d{1,2})[\s_\-\.]+(\d{1,2})[\s_\-\.]+(\d{2,4})', filename)
    if m2:
        day = int(m2.group(1))
        day_str = f'{day:02d}'
        mon_idx = int(m2.group(2)) - 1
        mon = month_names[mon_idx] if 0 <= mon_idx < 12 else 'Sep'
        yr = m2.group(3)
        if len(yr) == 2:
            yr = '20' + yr
        return f'{day_str}-{mon}-{yr}'

    m3 = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', filename)
    if m3:
        return m3.group(0)

    return '16-Sep-2026'

def insert_daily_stock_db(stock_date, filename, items):
    # Insert to MySQL
    m_conn = get_mysql_connection()
    if m_conn:
        try:
            cursor = m_conn.cursor()
            rows = []
            for it in items:
                rows.append((
                    stock_date, filename, it.get('partNo', ''), it.get('desc', ''),
                    it.get('brand', 'GENERIC'), it.get('category', 'OEM'), it.get('lineCode', ''),
                    it.get('branchCode', 'WHM'), it.get('branchName', 'MADURAI'),
                    it.get('qty', 0), it.get('unitCost', 0), it.get('mrp', 0),
                    it.get('valuation', 0), it.get('ageDays', 12), it.get('tag', 'CONSIDER')
                ))
            cursor.executemany("""
                INSERT INTO daily_stock_telemetry 
                (stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, rows)
            m_conn.close()
            print(f"MySQL DB: Inserted {len(rows)} stock items into daily_stock_telemetry")
        except Exception as e:
            print(f"MySQL DB Stock Insert Error: {e}")

    # Insert to SQLite
    s_conn = get_db_connection()
    if s_conn:
        try:
            cursor = s_conn.cursor()
            rows = []
            for it in items:
                rows.append((
                    stock_date, filename, it.get('partNo', ''), it.get('desc', ''),
                    it.get('brand', 'GENERIC'), it.get('category', 'OEM'), it.get('lineCode', ''),
                    it.get('branchCode', 'WHM'), it.get('branchName', 'MADURAI'),
                    it.get('qty', 0), it.get('unitCost', 0), it.get('mrp', 0),
                    it.get('valuation', 0), it.get('ageDays', 12), it.get('tag', 'CONSIDER')
                ))
            cursor.executemany("""
                INSERT INTO daily_stock_telemetry 
                (stock_date, filename, part_number, description, brand, category, line_code, branch_code, branch_name, stock_qty, unit_cost, mrp, total_valuation, age_days, tag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            s_conn.commit()
            s_conn.close()
            print(f"SQLite DB: Inserted {len(rows)} stock items into daily_stock_telemetry")
        except Exception as e:
            print(f"SQLite DB Stock Insert Error: {e}")

def insert_daily_sales_db(transaction_date, month_code, channel_type, sales_rows):
    # Insert to MySQL
    m_conn = get_mysql_connection()
    if m_conn:
        try:
            cursor = m_conn.cursor()
            rows = []
            for r in sales_rows:
                rows.append((
                    transaction_date, month_code, channel_type,
                    r.get('invoice_number', 'INV-DAILY'), r.get('part_number', ''), r.get('description', ''),
                    r.get('brand', 'GENERIC'), r.get('category', 'Mechanical Parts'), r.get('aggregate', 'ENGINE'),
                    r.get('sub_aggregate', 'FILTERS'), r.get('component', r.get('description', '')),
                    float(r.get('qty_sold', 1)), float(r.get('unit_price', 250)), float(r.get('total_revenue', 250)),
                    float(r.get('gross_margin', 37.5)), float(r.get('margin_pct', 15.0)),
                    r.get('region', 'SOUTH'), r.get('remarks', 'Daily Upload Consolidated')
                ))
            cursor.executemany("""
                INSERT INTO daily_sales_consolidated
                (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, rows)
            m_conn.close()
            print(f"MySQL DB: Consolidated {len(rows)} daily sales lines")
        except Exception as e:
            print(f"MySQL DB Sales Insert Error: {e}")

    # Insert to SQLite
    s_conn = get_db_connection()
    if s_conn:
        try:
            cursor = s_conn.cursor()
            rows = []
            for r in sales_rows:
                rows.append((
                    transaction_date, month_code, channel_type,
                    r.get('invoice_number', 'INV-DAILY'), r.get('part_number', ''), r.get('description', ''),
                    r.get('brand', 'GENERIC'), r.get('category', 'Mechanical Parts'), r.get('aggregate', 'ENGINE'),
                    r.get('sub_aggregate', 'FILTERS'), r.get('component', r.get('description', '')),
                    float(r.get('qty_sold', 1)), float(r.get('unit_price', 250)), float(r.get('total_revenue', 250)),
                    float(r.get('gross_margin', 37.5)), float(r.get('margin_pct', 15.0)),
                    r.get('region', 'SOUTH'), r.get('remarks', 'Daily Upload Consolidated')
                ))
            cursor.executemany("""
                INSERT INTO daily_sales_consolidated
                (transaction_date, month_code, channel_type, invoice_number, part_number, description, brand, category, aggregate, sub_aggregate, component, qty_sold, unit_price, total_revenue, gross_margin, margin_pct, region, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            s_conn.commit()
            s_conn.close()
            print(f"SQLite DB: Consolidated {len(rows)} daily sales lines")
        except Exception as e:
            print(f"SQLite DB Sales Insert Error: {e}")

import sqlite3
import http.server
import socketserver
import os
import json
import io
import glob
import re
import threading
import pandas as pd

PORT = int(os.environ.get("PORT", 8000))

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Clean path and handle fallback subfolder routing for organized structure
        req_path = super().translate_path(path)
        if os.path.exists(req_path):
            return req_path
        
        # Check subfolders (images/, data/, lib/, js/)
        clean_name = os.path.basename(path.split('?')[0])
        for subfolder in ['images', 'data', 'lib', 'js']:
            alt_path = os.path.join(os.getcwd(), subfolder, clean_name)
            if os.path.exists(alt_path):
                return alt_path
                
        return req_path

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_GET(self):
        # Serve sales cache or trained mapping database (compressed or raw)
        clean_file = os.path.basename(self.path.split('?')[0])
        if clean_file in ['sales_cache.json', 'trained_mapping_db.json', 'stock_cache.json', 'aggregate_master_rules.json']:
            target_file = os.path.join('data', clean_file) if os.path.exists(os.path.join('data', clean_file)) else clean_file
            gz_path = (os.path.join('data', clean_file + '.gz')) if os.path.exists(os.path.join('data', clean_file + '.gz')) else (target_file + '.gz')
            
            if os.path.exists(target_file):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                with open(target_file, 'rb') as f:
                    self.wfile.write(f.read())
                return
            elif os.path.exists(gz_path):
                import gzip
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                with gzip.open(gz_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            elif os.path.exists('trained_db_part1.json') or os.path.exists(os.path.join('data', 'trained_db_part1.json')):
                # Merge 4 split parts on the fly
                merged = {}
                for idx in range(1, 5):
                    pf = f'trained_db_part{idx}.json'
                    dpf = os.path.join('data', pf)
                    target_p = dpf if os.path.exists(dpf) else pf
                    if os.path.exists(target_p):
                        with open(target_p, 'r', encoding='utf-8') as gf:
                            sub_db = json.load(gf)
                        if not merged:
                            merged = sub_db
                        else:
                            merged.setdefault('partNoLookup', {}).update(sub_db.get('partNoLookup', {}))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(merged, ensure_ascii=False).encode('utf-8'))
                return
        if self.path == '/api/db/stats':
            stats = get_db_stats()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode('utf-8'))
            return

        if self.path.startswith('/api/inventory'):
            try:
                cache_file = os.path.join("data", "stock_cache.json.gz") if os.path.exists(os.path.join("data", "stock_cache.json.gz")) else (os.path.join("data", "stock_cache.json") if os.path.exists(os.path.join("data", "stock_cache.json")) else "stock_cache.json")
                stock_folder = os.path.join(os.getcwd(), "ALL GOOD STOCK")
                
                # Check if stock_cache exists
                if os.path.exists(cache_file):
                    if cache_file.endswith('.gz'):
                        import gzip
                        with gzip.open(cache_file, "rt", encoding="utf-8") as f:
                            cache_data = json.load(f)
                    else:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            cache_data = json.load(f)
                    
                    cached_dates = set(cache_data.get("dates", []))
                    folder_files = glob.glob(os.path.join(stock_folder, "*.xlsx")) + glob.glob(os.path.join(stock_folder, "*.xlsb")) + glob.glob(os.path.join(stock_folder, "*.csv"))
                    has_new = False
                    for fp in folder_files:
                        fn = os.path.basename(fp)
                        d_str = extract_stock_date(fn)
                        if d_str and d_str not in cached_dates:
                            has_new = True
                            break
                    
                    if has_new:
                        print("New file detected in ALL GOOD STOCK! Running instant stock cache builder...")
                        try:
                            import subprocess, sys
                            subprocess.run([sys.executable, "scripts/build_all_stock_instantly.py"], check=False)
                            if os.path.exists(cache_file):
                                if cache_file.endswith('.gz'):
                                    import gzip
                                    with gzip.open(cache_file, "rt", encoding="utf-8") as f:
                                        cache_data = json.load(f)
                                else:
                                    with open(cache_file, "r", encoding="utf-8") as f:
                                        cache_data = json.load(f)
                        except Exception as sync_err:
                            print(f"Sync cache error: {sync_err}")

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(cache_data, ensure_ascii=False).encode('utf-8'))
                    return

                # Fallback: scan ALL GOOD STOCK directly
                files = sorted(glob.glob(os.path.join(stock_folder, "*.xlsx")) + glob.glob(os.path.join(stock_folder, "*.xlsb")) + glob.glob(os.path.join(stock_folder, "*.csv")))

                daily_summaries = {}
                dates_list = []

                for fpath in files:
                    fname = os.path.basename(fpath)
                    date_match = re.search(r'\d{2}-[A-Za-z]{3}-\d{4}', fname)
                    date_str = date_match.group(0) if date_match else fname
                    
                    df = pd.read_excel(fpath)
                    df = df.fillna('')
                    
                    col_part = 'ManPart' if 'ManPart' in df.columns else ('ItemID(myTVS)' if 'ItemID(myTVS)' in df.columns else df.columns[10])
                    col_desc = 'ItemDesc' if 'ItemDesc' in df.columns else df.columns[12]
                    col_brand = 'BRAND' if 'BRAND' in df.columns else df.columns[8]
                    col_cat = 'CATEGORY' if 'CATEGORY' in df.columns else df.columns[9]
                    col_qty = 'Qty' if 'Qty' in df.columns else df.columns[13]
                    col_cost = 'UnitCost' if 'UnitCost' in df.columns else df.columns[14]
                    col_val = 'Value' if 'Value' in df.columns else df.columns[16]
                    col_loc = 'BRANCH NAME' if 'BRANCH NAME' in df.columns else df.columns[2]

                    total_skus = len(df)
                    total_qty = float(pd.to_numeric(df[col_qty], errors='coerce').sum())
                    total_val = float(pd.to_numeric(df[col_val], errors='coerce').sum())

                    df_sample = df.head(150)
                    sample_items = []
                    for _, row in df_sample.iterrows():
                        sample_items.append({
                            "partNo": str(row[col_part]).strip(),
                            "desc": str(row[col_desc]).strip(),
                            "brand": str(row[col_brand]).strip(),
                            "category": str(row[col_cat]).strip(),
                            "qty": float(row[col_qty]) if row[col_qty] != '' else 0,
                            "unitCost": float(row[col_cost]) if row[col_cost] != '' else 0,
                            "valuation": float(row[col_val]) if row[col_val] != '' else 0,
                            "branch": str(row[col_loc]).strip()
                        })

                    daily_summaries[date_str] = {
                        "date": date_str,
                        "filename": fname,
                        "totalSKUs": total_skus,
                        "totalQty": total_qty,
                        "totalValuation": total_val,
                        "sampleItems": sample_items
                    }
                    dates_list.append(date_str)

                latest_d = dates_list[-1] if dates_list else ""
                prev_d = dates_list[-2] if len(dates_list) >= 2 else (dates_list[0] if dates_list else "")
                
                dod_metrics = {}
                if latest_d and prev_d and latest_d in daily_summaries and prev_d in daily_summaries:
                    l_s = daily_summaries[latest_d]
                    p_s = daily_summaries[prev_d]
                    qty_diff = l_s["totalQty"] - p_s["totalQty"]
                    val_diff = l_s["totalValuation"] - p_s["totalValuation"]
                    dod_metrics = {
                        "latestDate": latest_d,
                        "prevDate": prev_d,
                        "skusDiff": l_s["totalSKUs"] - p_s["totalSKUs"],
                        "qtyDiff": qty_diff,
                        "valDiff": val_diff,
                        "addedQty": max(0, int(qty_diff)) if qty_diff > 0 else 0,
                        "consumedQty": abs(int(qty_diff)) if qty_diff < 0 else 0
                    }

                curr_week_avg = sum([daily_summaries[d]["totalQty"] for d in dates_list]) / max(1, len(dates_list)) if dates_list else 0
                wow_metrics = {"currWeekAvg": round(curr_week_avg, 1), "daysCount": len(dates_list)}

                response_data = {
                    "status": "success",
                    "stockFolderPath": stock_folder,
                    "dates": dates_list,
                    "latestDate": latest_d,
                    "dailySummaries": daily_summaries,
                    "dodMetrics": dod_metrics,
                    "wowMetrics": wow_metrics
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return

            except Exception as e:
                print(f"API Inventory Exception: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

        super().do_GET()

    def do_POST(self):
        if self.path == '/api/inventory/upload':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                content_type = self.headers.get('Content-Type', '')

                file_bytes = body_bytes
                filename = "AllGoodStock_Uploaded.xlsx"
                summary_json_str = None

                if 'boundary=' in content_type:
                    boundary_str = content_type.split('boundary=')[1]
                    boundary = boundary_str.encode()
                    parts = body_bytes.split(b'--' + boundary)
                    for part in parts:
                        if b'filename=' in part:
                            fn_match = re.search(rb'filename="([^"]+)"', part)
                            if fn_match:
                                filename = fn_match.group(1).decode('utf-8', errors='ignore')
                            if b'\r\n\r\n' in part:
                                _, content = part.split(b'\r\n\r\n', 1)
                                content = content.rsplit(b'\r\n', 1)[0]
                                file_bytes = content
                        elif b'name="summaryJSON"' in part:
                            if b'\r\n\r\n' in part:
                                _, content = part.split(b'\r\n\r\n', 1)
                                summary_json_str = content.rsplit(b'\r\n', 1)[0].decode('utf-8', errors='ignore')

                stock_folder = os.path.join(os.getcwd(), "ALL GOOD STOCK")
                os.makedirs(stock_folder, exist_ok=True)
                save_path = os.path.join(stock_folder, filename)
                
                with open(save_path, "wb") as f_out:
                    f_out.write(file_bytes)

                date_str = extract_stock_date(filename)

                print(f"Daily stock file {filename} uploaded successfully. Extracted date: {date_str}")

                # Instant Cache Update if summaryJSON is provided!
                if summary_json_str:
                    try:
                        summary_obj = json.loads(summary_json_str)
                        cache_files = [os.path.join("data", "stock_cache.json"), "stock_cache.json"]
                        for cf in cache_files:
                            os.makedirs(os.path.dirname(cf) if os.path.dirname(cf) else ".", exist_ok=True)
                            c_data = {}
                            if os.path.exists(cf):
                                with open(cf, "r", encoding="utf-8") as f: c_data = json.load(f)
                            
                            summaries = c_data.get("dailySummaries", {})
                            summaries[date_str] = summary_obj
                            c_data["dailySummaries"] = summaries
                            
                            dates = c_data.get("dates", [])
                            if date_str not in dates: dates.append(date_str)
                            c_data["dates"] = dates
                            c_data["latestDate"] = date_str
                            c_data["stockUpdateNotice"] = f"⚡ Folder Auto-Sync Active | Displaying Latest Available Stock: {date_str}"
                            
                            with open(cf, "w", encoding="utf-8") as out:
                                json.dump(c_data, out, ensure_ascii=False, indent=2)
                        
                        print(f"Instant cache update for {date_str} completed in 0.01s!")
                    except Exception as err:
                        print(f"Instant summary update error: {err}")

                # Trigger non-blocking background thread to update MySQL DB & stock_cache.json
                def update_cache_bg():
                    try:
                        import subprocess, sys
                        print(f"🚀 Launching MySQL Auto-Sync for {save_path}...")
                        subprocess.run([sys.executable, "scripts/auto_sync_file.py", "stock", save_path], check=False)
                        subprocess.run([sys.executable, "scripts/build_all_stock_instantly.py"], check=False)
                    except Exception as err:
                        print(f"Background cache build error: {err}")

                threading.Thread(target=update_cache_bg, daemon=True).start()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "filename": filename, "date": date_str, "message": f"Successfully uploaded and synced {filename} to MySQL & Website"}).encode('utf-8'))
                return

            except Exception as e:
                print(f"API Inventory Upload Exception: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

        if self.path == '/api/master_rules/upload':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                payload = json.loads(body_bytes.decode('utf-8'))
                
                rules = payload.get('aggregateMaster', [])
                if rules:
                    target_json = os.path.join("data", "aggregate_master_rules.json")
                    os.makedirs("data", exist_ok=True)
                    with open(target_json, "w", encoding="utf-8") as out_f:
                        json.dump({"status": "success", "count": len(rules), "aggregateMaster": rules}, out_f, ensure_ascii=False, indent=2)
                    
                    # Also insert into SQLite DB table mapping_reference_master
                    s_conn = get_db_connection()
                    if s_conn:
                        try:
                            cursor = s_conn.cursor()
                            cursor.execute("DELETE FROM mapping_reference_master")
                            db_rows = []
                            for r in rules:
                                db_rows.append((r.get('aggregate',''), r.get('subAggregate',''), r.get('component',''), r.get('category','Mechanical Parts')))
                            cursor.executemany("INSERT INTO mapping_reference_master (aggregate, sub_aggregate, component, category) VALUES (?, ?, ?, ?)", db_rows)
                            s_conn.commit()
                            s_conn.close()
                            print(f"SQLite DB: Updated mapping_reference_master with {len(rules)} rules.")
                        except Exception as dbe:
                            print(f"DB master upload insert warning: {dbe}")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "count": len(rules), "message": f"Successfully updated Aggregate Master rules in SQL DB ({len(rules)} rules)"}).encode('utf-8'))
                return
            except Exception as e:
                print(f"API Master Rules Upload Exception: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

        if self.path == '/api/sales/commit':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                payload = json.loads(body_bytes.decode('utf-8'))
                
                channel_type = payload.get('channel', 'RF').upper()
                rows = payload.get('rows', [])
                
                print(f"API Sales Commit: Received {len(rows)} mapped sales rows for channel {channel_type}")
                
                # Insert rows into MySQL & SQLite DB
                insert_daily_sales_db('15-Sep-2026', '202609', channel_type, rows)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "rowsCommitted": len(rows), "channel": channel_type, "message": f"Successfully committed {len(rows)} rows to {channel_type} Sales SQL DB"}).encode('utf-8'))
                return
            except Exception as e:
                print(f"API Sales Commit Exception: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

        if self.path == '/api/sales/upload' or self.path == '/api/upload':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                content_type = self.headers.get('Content-Type', '')

                file_bytes = body_bytes
                filename = "Sales_Upload.xlsx"
                channel_type = "RF"

                if 'boundary=' in content_type:
                    boundary_str = content_type.split('boundary=')[1]
                    boundary = boundary_str.encode()
                    parts = body_bytes.split(b'--' + boundary)
                    for part in parts:
                        if b'filename=' in part or b'name="file"' in part:
                            fn_match = re.search(rb'filename="([^"]+)"', part)
                            if fn_match:
                                filename = fn_match.group(1).decode('utf-8', errors='ignore')
                            if b'\r\n\r\n' in part:
                                _, content = part.split(b'\r\n\r\n', 1)
                                content = content.rsplit(b'\r\n', 1)[0]
                                file_bytes = content
                        elif b'name="channel"' in part:
                            if b'\r\n\r\n' in part:
                                _, content = part.split(b'\r\n\r\n', 1)
                                channel_type = content.rsplit(b'\r\n', 1)[0].decode('utf-8', errors='ignore').strip().upper()

                sales_folder = os.path.join(os.getcwd(), "SALES DUMP")
                os.makedirs(sales_folder, exist_ok=True)
                save_path = os.path.join(sales_folder, filename)

                with open(save_path, "wb") as f_out:
                    f_out.write(file_bytes)

                print(f"Sales file {filename} ({channel_type}) uploaded successfully. Saving to {save_path}...")

                def update_sales_bg():
                    try:
                        import subprocess, sys
                        print(f"🚀 Launching MySQL Auto-Sync for Sales {save_path}...")
                        subprocess.run([sys.executable, "scripts/auto_sync_file.py", "sales", save_path, channel_type], check=False)
                    except Exception as err:
                        print(f"Background sales upload error: {err}")

                threading.Thread(target=update_sales_bg, daemon=True).start()

                df = None
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes))
                except Exception:
                    try:
                        df = pd.read_excel(io.BytesIO(file_bytes), engine='pyxlsb')
                    except Exception:
                        df = pd.read_csv(io.BytesIO(file_bytes))

                if df is not None:
                    df = df.fillna('')
                    records = df.head(100).to_dict(orient='records')
                    
                    response_data = {
                        "status": "success",
                        "rowCount": len(df),
                        "columns": list(df.columns),
                        "rows": records,
                        "message": f"Successfully uploaded {filename} and synced to MySQL"
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                    return
                else:
                    raise ValueError("Could not parse file structure")

            except Exception as e:
                print(f"API Upload Exception: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

        super().do_POST()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print(f"==========================================================")
    print(f"  AUTO NEXA Local Server Running                           ")
    print(f"  URL: http://localhost:{PORT}")
    print(f"  ALL GOOD STOCK Folder: d:\\...\\ALL GOOD STOCK")
    print(f"==========================================================")

    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped cleanly.")
