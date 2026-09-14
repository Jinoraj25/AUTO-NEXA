import zipfile
import time
import re
import xml.etree.ElementTree as ET

fpath = r"ALL GOOD STOCK/AllGoodStock_12-Sep-2026.xlsx"
t0 = time.time()

# 1. Shared strings
shared_strings = []
with zipfile.ZipFile(fpath, 'r') as z:
    if 'xl/sharedStrings.xml' in z.namelist():
        ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
        shared_strings = re.findall(r'<t[^>]*>(.*?)</t>', ss_xml, flags=re.DOTALL)
    print(f"Loaded {len(shared_strings):,} shared strings in {time.time()-t0:.2f}s")

    t1 = time.time()
    col_part_idx, col_desc_idx, col_brand_idx, col_cat_idx, col_qty_idx, col_cost_idx, col_val_idx, col_loc_idx = 11, 13, 9, 10, 14, 15, 17, 3
    
    total_skus = 0
    total_qty = 0.0
    total_val = 0.0
    cat_val = {}
    sample_items = []

    f = z.open('xl/worksheets/sheet1.xml')
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

    for event, elem in ET.iterparse(f, events=('end',)):
        if elem.tag.endswith('row'):
            r_num_str = elem.attrib.get('r', '0')
            r_num = int(r_num_str) if r_num_str.isdigit() else 0

            row_cells = {}
            for c in elem:
                if c.tag.endswith('c'):
                    c_ref = c.attrib.get('r', '')
                    c_t = c.attrib.get('t', '')
                    col_str = re.sub(r'\d+', '', c_ref)
                    c_num = 0
                    for char in col_str:
                        c_num = c_num * 26 + (ord(char.upper()) - ord('A')) + 1
                    
                    v_elem = c.find(f'{ns}v')
                    if v_elem is None:
                        v_elem = c.find('v')
                    
                    val = ''
                    if v_elem is not None and v_elem.text:
                        v_text = v_elem.text
                        if c_t == 's' and v_text.isdigit():
                            s_idx = int(v_text)
                            val = shared_strings[s_idx] if s_idx < len(shared_strings) else ''
                        else:
                            val = v_text
                    row_cells[c_num] = val

            if r_num == 1:
                for c_idx, h_text in row_cells.items():
                    h_l = str(h_text).strip().lower()
                    if 'manpart' in h_l or 'itemid' in h_l: col_part_idx = c_idx
                    elif 'itemdesc' in h_l or 'desc' in h_l: col_desc_idx = c_idx
                    elif 'brand' in h_l: col_brand_idx = c_idx
                    elif 'category' in h_l or 'cat' in h_l: col_cat_idx = c_idx
                    elif 'qty' in h_l: col_qty_idx = c_idx
                    elif 'unitcost' in h_l or 'cost' in h_l: col_cost_idx = c_idx
                    elif 'val' in h_l: col_val_idx = c_idx
                    elif 'branch' in h_l: col_loc_idx = c_idx
                elem.clear()
                continue

            try:
                q_raw = row_cells.get(col_qty_idx, 0)
                v_raw = row_cells.get(col_val_idx, 0)
                q = float(q_raw) if q_raw else 0.0
                v = float(v_raw) if v_raw else 0.0

                total_skus += 1
                total_qty += q
                total_val += v

                cat_name = str(row_cells.get(col_cat_idx, 'Mechanical Parts')).strip() or 'Mechanical Parts'
                cat_val[cat_name] = cat_val.get(cat_name, 0.0) + v

                if len(sample_items) < 150:
                    cost_raw = row_cells.get(col_cost_idx, 0)
                    sample_items.append({
                        "partNo": str(row_cells.get(col_part_idx, '')).strip(),
                        "desc": str(row_cells.get(col_desc_idx, '')).strip(),
                        "brand": str(row_cells.get(col_brand_idx, '')).strip(),
                        "category": cat_name,
                        "qty": q,
                        "unitCost": float(cost_raw) if cost_raw else 0.0,
                        "valuation": v,
                        "branch": str(row_cells.get(col_loc_idx, '')).strip()
                    })
            except Exception:
                pass

            elem.clear()

t2 = time.time()
print(f"Parsed sheet1.xml in {t2-t1:.2f}s! Total time: {t2-t0:.2f}s")
print(f"SKUs: {total_skus:,}, Qty: {total_qty:,.0f}, Val: INR {total_val/10000000:.2f} Cr")
