import os, re

print("=== Applying Genome Endpoint Fix and Domain Rule Expansion (v69) ===")

# 1. Update server.py
server_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\server.py"
with open(server_path, "r", encoding="utf-8") as f:
    server_code = f.read()

old_get_block = """        clean_file = os.path.basename(self.path.split('?')[0])
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
                return"""

new_get_block = """        clean_file = os.path.basename(self.path.split('?')[0])
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
                return"""

if old_get_block in server_code:
    server_code = server_code.replace(old_get_block, new_get_block, 1)
    print("Updated server.py to serve .gz files with Content-Encoding: gzip")
else:
    print("WARNING: Target block not found in server.py")

with open(server_path, "w", encoding="utf-8") as f:
    f.write(server_code)


# 2. Update js/data-engine.js inspectColumnsByContent to include Product_Number and Product_Description
data_engine_path = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\js\data-engine.js"
with open(data_engine_path, "r", encoding="utf-8") as f:
    js_code = f.read()

# Update keywords inside inspectColumnsByContent and processSalesUpload
js_code = js_code.replace(
    "kNorm.includes('itemcode') || kNorm.includes('partnumber') || kNorm.includes('partno')",
    "kNorm.includes('itemcode') || kNorm.includes('partnumber') || kNorm.includes('partno') || kNorm.includes('productnumber') || kNorm.includes('productno') || kNorm.includes('productnum')"
)

js_code = js_code.replace(
    "kNorm.includes('itemname') || kNorm.includes('itemdescription') || kNorm.includes('partdescription')",
    "kNorm.includes('itemname') || kNorm.includes('itemdescription') || kNorm.includes('partdescription') || kNorm.includes('productdescription') || kNorm.includes('productdesc')"
)

# Update partKeywords array in processSalesUpload
js_code = js_code.replace(
    "const partKeywords = ['itemcode_rev', 'item_code_rev', 'item code_rev', 'itemcoderev', 'partno', 'part number', 'part_number', 'itemcode', 'item code', 'item_code', 'manpart', 'material', 'sku', 'productno', 'article', 'lncode', 'part'];",
    "const partKeywords = ['product_number', 'product number', 'product_no', 'productno', 'productnumber', 'itemcode_rev', 'item_code_rev', 'item code_rev', 'itemcoderev', 'partno', 'part number', 'part_number', 'itemcode', 'item code', 'item_code', 'manpart', 'material', 'sku', 'article', 'lncode', 'part'];"
)

js_code = js_code.replace(
    "const descKeywords = ['itemname', 'item name', 'item_name', 'description', 'item description', 'item_description', 'part description', 'part_description', 'itemdesc', 'item desc', 'desc', 'detail', 'specification', 'title', 'part name', 'product name'];",
    "const descKeywords = ['product_description', 'product description', 'product_desc', 'productdesc', 'itemname', 'item name', 'item_name', 'description', 'item description', 'item_description', 'part description', 'part_description', 'itemdesc', 'item desc', 'desc', 'detail', 'specification', 'title', 'part name', 'product name'];"
)

with open(data_engine_path, "w", encoding="utf-8") as f:
    f.write(js_code)

print("Done updating server.py and js/data-engine.js!")
