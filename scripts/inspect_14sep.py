import zipfile
import re

fpath = r"ALL GOOD STOCK/AllGoodStock_14-Sep-2026.xlsx"
with zipfile.ZipFile(fpath, 'r') as z:
    sheet = z.read('xl/worksheets/sheet1.xml').decode('utf-8', errors='ignore')
    r1 = re.search(r'<row r="1"[^>]*>(.*?)</row>', sheet, re.DOTALL)
    if r1:
        print("Row 1 raw XML:")
        print(r1.group(1)[:1000])
    
    r2 = re.search(r'<row r="2"[^>]*>(.*?)</row>', sheet, re.DOTALL)
    if r2:
        print("\nRow 2 raw XML:")
        print(r2.group(1)[:1000])
