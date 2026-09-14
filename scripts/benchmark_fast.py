import zipfile
import re
import time
import os

VALID_CATS = ['PRIMARY', 'SECONDARY', 'PL', 'OEM', 'CASTROL', 'LUBES', 'PAINT&CONS', 'ASSET']

def normalize_category(raw):
    if not raw or not isinstance(raw, str): return 'UNCATEGORIZED'
    u = raw.strip().upper()
    if u in VALID_CATS: return u
    if 'PRIMARY' in u: return 'PRIMARY'
    if 'SECONDARY' in u: return 'SECONDARY'
    if 'PAINT' in u or 'CONS' in u: return 'PAINT&CONS'
    if 'CASTROL' in u: return 'CASTROL'
    if 'LUBES' in u or 'LUBE' in u: return 'LUBES'
    if 'OEM' in u: return 'OEM'
    if 'PL' in u: return 'PL'
    if 'ASSET' in u: return 'ASSET'
    return 'UNCATEGORIZED'

t0 = time.time()
fpath = r"ALL GOOD STOCK\AllGoodStock_12-Sep-2026.xlsx"
with zipfile.ZipFile(fpath, 'r') as z:
    shared_strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        ss_data = z.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
        si_blocks = re.findall(r'<si.*?>(.*?)</si>', ss_data, flags=re.DOTALL)
        for block in si_blocks:
            t_matches = re.findall(r'<t[^>]*>(.*?)</t>', block, flags=re.DOTALL)
            shared_strings.append(''.join(t_matches))

    sheet = [s for s in z.namelist() if 'sheet' in s][0]
    sheet_str = z.read(sheet).decode('utf-8', errors='ignore')

t1 = time.time()

# 1. Map row number -> category
row_cats = {}
cat_matches = re.finditer(r'<c r="J(\d+)"([^>]*)>(?:<v>(.*?)</v>|<is><t>(.*?)</t></is>)', sheet_str)
for m in cat_matches:
    r_num = int(m.group(1))
    attrs = m.group(2)
    v_val = m.group(3)
    t_val = m.group(4)

    raw_str = ''
    if t_val:
        raw_str = t_val
    elif 't="s"' in attrs and v_val and v_val.isdigit():
        idx = int(v_val)
        raw_str = shared_strings[idx] if idx < len(shared_strings) else ''
    elif v_val:
        raw_str = v_val

    row_cats[r_num] = normalize_category(raw_str)

# 2. Map row number -> valuation & total up
cat_val = {}
total_val = 0.0
total_skus = 0

val_matches = re.finditer(r'<c r="Q(\d+)"[^>]*><v>(.*?)</v>', sheet_str)
for m in val_matches:
    r_num = int(m.group(1))
    if r_num == 1: continue
    v = 0.0
    try: v = float(m.group(2))
    except Exception: pass

    cat = row_cats.get(r_num, 'UNCATEGORIZED')
    cat_val[cat] = cat_val.get(cat, 0.0) + v
    total_val += v
    total_skus += 1

t2 = time.time()

print(f"Read Zip into RAM: {t1-t0:.2f}s")
print(f"Regex Matched {total_skus:,} rows in {t2-t1:.2f}s | Total Val = INR {total_val/1e7:.2f} Cr")
print("Category Breakdown:")
for k, v in sorted(cat_val.items(), key=lambda x:x[1], reverse=True):
    print(f"  {k}: INR {v/1e7:.2f} Cr ({(v/total_val)*100:.1f}%)")
