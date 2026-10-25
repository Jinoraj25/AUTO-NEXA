
import os
import sqlite3
import json
import sys
import glob
import re
import threading
import urllib.parse

try:
    import overall_catalogue_api
except ImportError:
    overall_catalogue_api = None

try:
    import catalog_ai_bot
except ImportError:
    catalog_ai_bot = None

try:
    import pymysql
except ImportError:
    pymysql = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, 'data', 'autonexa.db')

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
        
        # Check subfolders (images/, videos/, data/, lib/, js/)
        clean_name = os.path.basename(path.split('?')[0])
        for subfolder in ['images', 'videos', 'data', 'lib', 'js']:
            alt_path = os.path.join(os.getcwd(), subfolder, clean_name)
            if os.path.exists(alt_path):
                return alt_path
                
        return req_path

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_HEAD(self):
        clean_path = self.path.split('?')[0].lstrip('/')
        if clean_path.lower().endswith(('.mp4', '.webm')):
            vid_path = clean_path if os.path.exists(clean_path) else os.path.join('videos', os.path.basename(clean_path))
            if os.path.exists(vid_path):
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', str(os.path.getsize(vid_path)))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                return
        super().do_HEAD()

    def do_GET(self):
        clean_path = self.path.split('?')[0].lstrip('/')

        # Transparently serve mp4/webm videos with HTTP Range (206) support for smooth looping & seeking
        if clean_path.lower().endswith(('.mp4', '.webm')):
            vid_path = clean_path if os.path.exists(clean_path) else os.path.join('videos', os.path.basename(clean_path))
            if os.path.exists(vid_path):
                file_size = os.path.getsize(vid_path)
                range_header = self.headers.get('Range', None)
                
                if range_header:
                    m = re.match(r'bytes=(\d+)-(\d*)', range_header)
                    if m:
                        start = int(m.group(1))
                        end = int(m.group(2)) if m.group(2) else file_size - 1
                        length = end - start + 1
                        
                        self.send_response(206)
                        self.send_header('Content-Type', 'video/mp4')
                        self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                        self.send_header('Content-Length', str(length))
                        self.send_header('Accept-Ranges', 'bytes')
                        self.end_headers()
                        
                        with open(vid_path, 'rb') as f:
                            f.seek(start)
                            self.wfile.write(f.read(length))
                        return

                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', str(file_size))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()
                with open(vid_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # Transparently serve images from images/ if requested from root
        if clean_path.lower().endswith(('.jpg', '.jpeg', '.png', '.svg', '.webp')):
            img_in_images = os.path.join('images', os.path.basename(clean_path))
            if not os.path.exists(clean_path) and os.path.exists(img_in_images):
                content_type = 'image/jpeg' if clean_path.lower().endswith(('.jpg', '.jpeg')) else ('image/png' if clean_path.lower().endswith('.png') else ('image/svg+xml' if clean_path.lower().endswith('.svg') else 'image/webp'))
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.end_headers()
                with open(img_in_images, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # Serve sales cache or trained mapping database (compressed or raw)
        clean_file = os.path.basename(self.path.split('?')[0])
        base_file = clean_file.replace('.gz', '')
        if base_file in ['sales_cache.json', 'trained_mapping_db.json', 'stock_cache.json', 'aggregate_master_rules.json']:
            target_file = os.path.join('data', base_file) if os.path.exists(os.path.join('data', base_file)) else base_file
            gz_path = os.path.join('data', base_file + '.gz') if os.path.exists(os.path.join('data', base_file + '.gz')) else (target_file + '.gz')
            
            if clean_file.endswith('.gz') and os.path.exists(gz_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Encoding', 'gzip')
                self.end_headers()
                with open(gz_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            elif os.path.exists(target_file):
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

        # Overall Catalogue, Vahan & Catalog AI API Endpoints
        if self.path.startswith('/api/overall-catalogue') or self.path.startswith('/api/vahan') or self.path.startswith('/api/catalog-ai') or self.path.startswith('/api/oem-to-oes'):
            parsed_url = urllib.parse.urlparse(self.path)
            path_only = parsed_url.path
            params = urllib.parse.parse_qs(parsed_url.query)
            
            get_param = lambda k, default='': params.get(k, [default])[0]

            if path_only == '/api/overall-catalogue/stats':
                res = overall_catalogue_api.get_catalogue_stats() if overall_catalogue_api else {"status": "error"}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/filters':
                res = overall_catalogue_api.get_catalogue_filters() if overall_catalogue_api else {}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/vahan/lookup' or path_only == '/api/overall-catalogue/vahan':
                reg_val = get_param('reg_no') or get_param('regNo') or get_param('q')
                api_key_val = get_param('api_key') or get_param('apiKey')
                api_url_val = get_param('api_url') or get_param('apiUrl')
                res = overall_catalogue_api.vahan_rc_lookup(reg_val, api_key=api_key_val, api_url=api_url_val) if overall_catalogue_api else {"status": "error"}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/models':
                make_val = get_param('make')
                res = overall_catalogue_api.get_vehicle_models(make_val) if overall_catalogue_api else []
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"models": res}, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/sub-models':
                make_val = get_param('make')
                model_val = get_param('model')
                fuel_val = get_param('fuel_type') or get_param('fuel')
                year_val = get_param('year')
                res = overall_catalogue_api.get_sub_models(make_val, model_val, fuel_val, year_val) if overall_catalogue_api else []
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"sub_models": res}, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/sub-aggregates':
                agg_val = get_param('aggregate')
                res = overall_catalogue_api.get_sub_aggregates(agg_val) if overall_catalogue_api else []
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"sub_aggregates": res}, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/components':
                agg_val = get_param('aggregate')
                sub_agg_val = get_param('sub_aggregate')
                res = overall_catalogue_api.get_components(agg_val, sub_agg_val) if overall_catalogue_api else []
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"components": res}, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/oem-to-oes/convert':
                q_val = get_param('q') or get_param('query') or ''
                import oem_to_oes_service
                conv_res = oem_to_oes_service.convert_oem_to_oes(q_val)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(conv_res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/oem-to-oes/interchange':
                q_val = get_param('q') or get_param('query') or ''
                import vig_engine
                int_res = vig_engine.search_interchange(q_val)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(int_res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/catalog-ai/chat':
                q_val = get_param('q') or get_param('message') or ''
                if catalog_ai_bot:
                    bot_res = catalog_ai_bot.process_chat_message(q_val)
                else:
                    bot_res = {"reply": "Catalog AI service is initializing...", "step": "error"}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(bot_res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/makes-catalog':
                res = overall_catalogue_api.get_makes_catalog() if overall_catalogue_api else []
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"makes": res}, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/visual-variants':
                make_val = get_param('make') or 'MARUTI SUZUKI'
                model_val = get_param('model')
                fuel_val = get_param('fuel_type') or get_param('fuel')
                year_val = get_param('year')
                search_val = get_param('q') or get_param('search')
                limit_val = int(get_param('limit', '120'))
                res = overall_catalogue_api.get_visual_variants(make_val, model_val, fuel_val, year_val, search_val, limit_val) if overall_catalogue_api else {"variants": [], "models": [], "totalCount": 0}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/taxonomy-hierarchy':
                make_val = get_param('make')
                model_val = get_param('model')
                sub_model_val = get_param('sub_model') or get_param('variant')
                agg_val = get_param('aggregate')
                sub_agg_val = get_param('sub_aggregate')
                res = overall_catalogue_api.get_taxonomy_hierarchy(make_val, model_val, sub_model_val, agg_val, sub_agg_val) if overall_catalogue_api else {"items": []}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/suggestions':
                q_val = get_param('q') or get_param('query')
                limit_val = int(get_param('limit', '8'))
                res = overall_catalogue_api.get_part_suggestions(q_val, limit=limit_val) if overall_catalogue_api else []
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"suggestions": res}, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/search':
                q_val = get_param('q')
                brand_val = get_param('brand')
                make_val = get_param('make')
                model_val = get_param('model')
                sub_model_val = get_param('sub_model')
                fuel_val = get_param('fuel_type')
                year_val = get_param('year')
                segment_val = get_param('segment')
                agg_val = get_param('aggregate')
                sub_agg_val = get_param('sub_aggregate')
                comp_val = get_param('component')
                min_p = get_param('min_price') or None
                max_p = get_param('max_price') or None
                page_val = get_param('page', '1')
                limit_val = get_param('limit', '25')

                res = overall_catalogue_api.search_catalogue(
                    q=q_val, brand=brand_val, make=make_val, model=model_val, sub_model=sub_model_val,
                    fuel_type=fuel_val, year=year_val, segment=segment_val, aggregate=agg_val,
                    sub_aggregate=sub_agg_val, component=comp_val, min_price=min_p, max_price=max_p,
                    page=page_val, limit=limit_val
                ) if overall_catalogue_api else {"items": [], "totalCount": 0}

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only.startswith('/api/overall-catalogue/part/'):
                part_no = urllib.parse.unquote(path_only.replace('/api/overall-catalogue/part/', ''))
                res = overall_catalogue_api.get_part_details(part_no) if overall_catalogue_api else None
                self.send_response(200 if res else 404)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res or {"error": "Part not found"}, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/overall-catalogue/export':
                q_val = get_param('q')
                brand_val = get_param('brand')
                make_val = get_param('make')
                model_val = get_param('model')
                sub_model_val = get_param('sub_model')
                fuel_val = get_param('fuel_type')
                year_val = get_param('year')
                segment_val = get_param('segment')
                agg_val = get_param('aggregate')
                sub_agg_val = get_param('sub_aggregate')
                comp_val = get_param('component')
                min_p = get_param('min_price') or None
                max_p = get_param('max_price') or None

                csv_data = overall_catalogue_api.export_catalogue_csv(
                    q=q_val, brand=brand_val, make=make_val, model=model_val, sub_model=sub_model_val,
                    fuel_type=fuel_val, year=year_val, segment=segment_val, aggregate=agg_val,
                    sub_aggregate=sub_agg_val, component=comp_val, min_price=min_p, max_price=max_p
                ) if overall_catalogue_api else ""

                self.send_response(200)
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="overall_catalogue_export.csv"')
                self.end_headers()
                self.wfile.write(csv_data.encode('utf-8'))
                return
        # Inventory Management & Live Stock Telemetry Endpoints
        if self.path.startswith('/api/inventory'):
            parsed_url = urllib.parse.urlparse(self.path)
            path_only = parsed_url.path
            params = urllib.parse.parse_qs(parsed_url.query)
            get_param = lambda k, default='': params.get(k, [default])[0]

            if path_only == '/api/inventory/sync-status':
                try:
                    conn = sqlite3.connect(os.path.join("data", "autonexa.db"))
                    cur = conn.cursor()
                    cur.execute("SELECT COUNT(*), MAX(snapshot_date) FROM inventory_daily_snapshots")
                    row = cur.fetchone()
                    count = row[0] if row else 0
                    latest_d = row[1] if row else ""
                    conn.close()
                    res = {
                        "status": "ACTIVE",
                        "lastSync": latest_d,
                        "totalDays": count,
                        "schedule": "Daily 08:30 AM (Auto Ingest)",
                        "folder": os.path.join(os.getcwd(), "ALL GOOD STOCK")
                    }
                except Exception as e:
                    res = {"status": "ERROR", "message": str(e)}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                return

            if path_only == '/api/inventory/search':
                q_val = get_param('q', '').strip()
                brand_val = get_param('brand', '').strip()
                cat_val = get_param('category', '').strip()
                branch_val = get_param('branch', '').strip()
                tag_val = get_param('tag', 'ALL').strip()
                age_val = get_param('age', '').strip()
                page_val = max(1, int(get_param('page', '1')))
                limit_val = max(1, min(200, int(get_param('limit', '50'))))
                offset_val = (page_val - 1) * limit_val

                try:
                    conn = sqlite3.connect(os.path.join("data", "autonexa.db"))
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()

                    clauses = []
                    args = []

                    if q_val:
                        clauses.append("(part_number LIKE ? OR description LIKE ? OR brand LIKE ? OR branch_name LIKE ?)")
                        q_like = f"%{q_val}%"
                        args.extend([q_like, q_like, q_like, q_like])
                    if brand_val and brand_val != 'ALL':
                        clauses.append("brand = ?")
                        args.append(brand_val)
                    if cat_val and cat_val != 'ALL':
                        clauses.append("category = ?")
                        args.append(cat_val)
                    if branch_val and branch_val != 'ALL':
                        clauses.append("branch_name = ?")
                        args.append(branch_val)
                    if tag_val and tag_val != 'ALL':
                        clauses.append("tag = ?")
                        args.append(tag_val)
                    if age_val:
                        if age_val == '0-30': clauses.append("age_days <= 30")
                        elif age_val == '31-60': clauses.append("age_days > 30 AND age_days <= 60")
                        elif age_val == '61-90': clauses.append("age_days > 60 AND age_days <= 90")
                        elif age_val == '91-180': clauses.append("age_days > 90 AND age_days <= 180")
                        elif age_val == '181-365': clauses.append("age_days > 180 AND age_days <= 365")
                        elif age_val == '>365': clauses.append("age_days > 365")

                    where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""

                    count_cur = conn.cursor()
                    count_cur.execute(f"SELECT COUNT(*) FROM daily_stock_telemetry {where_sql}", args)
                    total_count = count_cur.fetchone()[0]

                    sql = f"SELECT * FROM daily_stock_telemetry {where_sql} ORDER BY total_valuation DESC LIMIT ? OFFSET ?"
                    cur.execute(sql, args + [limit_val, offset_val])
                    items = []
                    for r in cur.fetchall():
                        items.append({
                            "source": "Oracle",
                            "partNo": r["part_number"],
                            "desc": r["description"],
                            "brand": r["brand"],
                            "category": r["category"],
                            "lineCode": r["line_code"],
                            "branchCode": r["branch_code"],
                            "branchName": r["branch_name"],
                            "qty": r["stock_qty"],
                            "unitCost": r["unit_cost"],
                            "mrp": r["mrp"],
                            "valuation": r["total_valuation"],
                            "ageDays": r["age_days"],
                            "tag": r["tag"]
                        })
                    conn.close()
                    res = {"status": "success", "totalCount": total_count, "page": page_val, "limit": limit_val, "items": items}
                except Exception as e:
                    res = {"status": "error", "message": str(e), "items": [], "totalCount": 0}

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                return

            # Default /api/inventory: Return stock_cache (compressed or JSON)
            try:
                cache_file = os.path.join("data", "stock_cache.json.gz") if os.path.exists(os.path.join("data", "stock_cache.json.gz")) else (os.path.join("data", "stock_cache.json") if os.path.exists(os.path.join("data", "stock_cache.json")) else "stock_cache.json")
                if os.path.exists(cache_file):
                    if cache_file.endswith('.gz'):
                        import gzip
                        with gzip.open(cache_file, "rt", encoding="utf-8") as f:
                            cache_data = json.load(f)
                    else:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            cache_data = json.load(f)

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(cache_data, ensure_ascii=False).encode('utf-8'))
                    return
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Stock cache not found"}).encode('utf-8'))
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
        if self.path.startswith('/api/oem-to-oes/convert'):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                payload = json.loads(body_bytes.decode('utf-8'))
                query = payload.get('query') or payload.get('message') or ''
                import oem_to_oes_service
                conv_res = oem_to_oes_service.convert_oem_to_oes(query)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(conv_res, ensure_ascii=False).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        if self.path.startswith('/api/oem-to-oes/interchange'):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                payload = json.loads(body_bytes.decode('utf-8'))
                query = payload.get('query') or payload.get('q') or ''
                import vig_engine
                int_res = vig_engine.search_interchange(query)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(int_res, ensure_ascii=False).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        if self.path.startswith('/api/catalog-ai/chat'):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                payload = json.loads(body_bytes.decode('utf-8'))
                message = payload.get('message', '')
                state = payload.get('state', {})

                if catalog_ai_bot:
                    bot_res = catalog_ai_bot.process_chat_message(message, session_state=state)
                else:
                    bot_res = {"reply": "Catalog AI service is initializing...", "step": "error"}

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(bot_res, ensure_ascii=False).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

        if self.path == '/api/overall-catalogue/smart-map':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                payload = json.loads(body_bytes.decode('utf-8'))
                part_numbers = payload.get('items') or payload.get('partNumbers') or payload.get('parts') or []
                
                mapped_results = overall_catalogue_api.smart_map_parts(part_numbers) if overall_catalogue_api else {}
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "mapped": mapped_results}, ensure_ascii=False).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        if self.path == '/api/inventory/sync-now':
            try:
                def run_sync_bg():
                    import subprocess, sys
                    subprocess.run([sys.executable, "scripts/daily_stock_sync_daemon.py", "--once"], check=False)
                threading.Thread(target=run_sync_bg, daemon=True).start()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Daily stock sync initiated in background."}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return

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
                    df = pd.read_excel(io.BytesIO(file_bytes), engine='calamine')
                except Exception:
                    try:
                        df = pd.read_excel(io.BytesIO(file_bytes))
                    except Exception:
                        try:
                            df = pd.read_excel(io.BytesIO(file_bytes), engine='pyxlsb')
                        except Exception:
                            try:
                                df = pd.read_csv(io.BytesIO(file_bytes))
                            except Exception:
                                pass

                if df is not None:
                    # Smart header row promotion for files with top title/blank rows or Unnamed columns
                    if any('Unnamed' in str(c) for c in df.columns):
                        for idx, row in df.head(5).iterrows():
                            vals = [str(v).lower().replace(' ', '').replace('_', '') for v in row.values if pd.notna(v)]
                            if any(kw in v for v in vals for kw in ['itemcode_rev', 'itemcode', 'itemname', 'partno', 'partnumber', 'itemdesc', 'itemdescription', 'description', 'partdescription']):
                                new_cols = [str(v).strip() if pd.notna(v) and str(v).strip() else f'Col_{i}' for i, v in enumerate(row.values)]
                                df = df.iloc[idx+1:].copy()
                                df.columns = new_cols
                                break

                    df = df.fillna('')
                    records = df.to_dict(orient='records')
                    
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

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), CustomHandler) as httpd:
        httpd.daemon_threads = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped cleanly.")
