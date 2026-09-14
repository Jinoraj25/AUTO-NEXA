import zipfile
import re

for fname in ['AllGoodStock_01-Sep-2026.xlsx', 'AllGoodStock_11-Sep-2026.xlsx', 'AllGoodStock_12-Sep-2026.xlsx', 'AllGoodStock_14-Sep-2026.xlsx']:
    fpath = f"ALL GOOD STOCK/{fname}"
    with zipfile.ZipFile(fpath) as z:
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_data = z.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
            ss = re.findall(r'<t[^>]*>(.*?)</t>', ss_data, flags=re.DOTALL)
        
        sheet = z.read('xl/worksheets/sheet1.xml').decode('utf-8', errors='ignore')
        r1 = re.search(r'<row r="1"[^>]*>(.*?)</row>', sheet, re.DOTALL)
        if not r1:
            continue
        cells = re.findall(r'<c r="([A-Z]+)\d+"([^>]*)>(?:<is><t>(.*?)</t></is>)?(?:<f[^>]*>.*?</f>)?(?:<v>(.*?)</v>)?', r1.group(1), re.DOTALL)
        
        print(f"=== {fname} ===")
        for col_str, c_attrs, inlined, c_val in cells:
            val = ''
            if inlined:
                val = inlined
            elif 't="s"' in c_attrs and c_val and c_val.isdigit():
                idx = int(c_val)
                val = ss[idx] if idx < len(ss) else ''
            elif c_val:
                val = c_val
            
            c_num = 0
            for char in col_str:
                c_num = c_num * 26 + (ord(char.upper()) - ord('A')) + 1
            print(f"  Col {c_num-1} ({col_str}): '{val}'")
        print("\n")
