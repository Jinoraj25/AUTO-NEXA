import zipfile
import re
import xml.etree.ElementTree as ET

fpath = r"ALL GOOD STOCK/AllGoodStock_14-Sep-2026.xlsx"

with zipfile.ZipFile(fpath, 'r') as z:
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        ss_data = z.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
        ss = re.findall(r'<t[^>]*>(.*?)</t>', ss_data, flags=re.DOTALL)
    
    f = z.open('xl/worksheets/sheet1.xml')
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

    row_count = 0
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
                    c_idx = c_num - 1
                    
                    val = ''
                    t_elem = c.find('.//{*}t')
                    v_elem = c.find('.//{*}v')

                    if c_t == 'inlineStr' and t_elem is not None and t_elem.text:
                        val = t_elem.text
                    elif c_t == 's' and v_elem is not None and v_elem.text and v_elem.text.isdigit():
                        s_idx = int(v_elem.text)
                        val = ss[s_idx] if s_idx < len(ss) else ''
                    elif v_elem is not None and v_elem.text:
                        val = v_elem.text
                    elif t_elem is not None and t_elem.text:
                        val = t_elem.text

                    row_cells[c_idx] = val

            print(f"Row {r_num}:")
            for c_i in range(min(23, max(row_cells.keys())+1 if row_cells else 0)):
                print(f"  Col {c_i} ({chr(65+c_i)}): {repr(row_cells.get(c_i, ''))}")
            
            row_count += 1
            if row_count >= 5:
                break
            elem.clear()
