import zipfile
import re
import xml.etree.ElementTree as ET

for fname in ['AllGoodStock_01-Sep-2026.xlsx', 'AllGoodStock_11-Sep-2026.xlsx', 'AllGoodStock_12-Sep-2026.xlsx', 'AllGoodStock_14-Sep-2026.xlsx']:
    fpath = f"ALL GOOD STOCK/{fname}"
    with zipfile.ZipFile(fpath) as z:
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_data = z.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
            ss = re.findall(r'<t[^>]*>(.*?)</t>', ss_data, flags=re.DOTALL)
        
        sheet = z.read('xl/worksheets/sheet1.xml').decode('utf-8', errors='ignore')
        
        # Check first 50 rows for category values
        f = z.open('xl/worksheets/sheet1.xml')
        valid_targets = {'PRIMARY', 'SECONDARY', 'PL', 'OEM', 'CASTROL', 'LUBES', 'PAINT&CONS', 'ASSET'}
        col_matches = {}
        row_c = 0
        for ev, el in ET.iterparse(f, events=('end',)):
            if el.tag.endswith('row'):
                row_c += 1
                if row_c == 1: el.clear(); continue
                for c in el:
                    c_ref = c.attrib.get('r', '')
                    c_t = c.attrib.get('t', '')
                    col_str = re.sub(r'\d+', '', c_ref)
                    t_elem = c.find('.//{*}t')
                    v_elem = c.find('.//{*}v')
                    val = ''
                    if c_t == 'inlineStr' and t_elem is not None and t_elem.text: val = t_elem.text
                    elif c_t == 's' and v_elem is not None and v_elem.text and v_elem.text.isdigit():
                        idx = int(v_elem.text)
                        val = ss[idx] if idx < len(ss) else ''
                    elif v_elem is not None and v_elem.text: val = v_elem.text
                    elif t_elem is not None and t_elem.text: val = t_elem.text

                    if val.strip().upper() in valid_targets:
                        col_matches[col_str] = col_matches.get(col_str, 0) + 1
                if row_c > 500: break
                el.clear()
        print(f"=== {fname} ===")
        print("  Real Category Matches by Column:", col_matches)
