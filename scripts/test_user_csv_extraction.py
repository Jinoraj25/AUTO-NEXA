import pandas as pd
import json, re

csv_path = r'C:\Users\SM0237\Downloads\Mapped_Catalogue_Export_2026-09-22.csv'
df = pd.read_csv(csv_path)

print(f"Testing Smart Column Extractor on user file ({len(df):,} rows)...")

part_kws = ['partno', 'partnumber', 'part_number', 'itemcode', 'itemcode_rev', 'item_code_rev', 'itemcode', 'item code', 'manpart', 'material', 'sku', 'part']
desc_kws = ['itemname', 'item name', 'item_name', 'description', 'item description', 'item_description', 'part description', 'part_description', 'itemdesc', 'item desc', 'desc', 'detail', 'name']

def extract_row_fields(row):
    keys = list(row.keys())

    part_val = None
    desc_val = None

    # 1. Exact / Normalized key match
    for k in keys:
        k_norm = re.sub(r'[^a-z0-9]', '', k.lower())
        if not part_val:
            for pk in part_kws:
                pk_norm = re.sub(r'[^a-z0-9]', '', pk.lower())
                if pk_norm == k_norm or pk_norm in k_norm:
                    val = str(row[k]).strip()
                    if val and val != 'nan':
                        part_val = val
                        break
        if not desc_val:
            for dk in desc_kws:
                dk_norm = re.sub(r'[^a-z0-9]', '', dk.lower())
                if dk_norm == k_norm or dk_norm in k_norm:
                    val = str(row[k]).strip()
                    if val and val != 'nan':
                        desc_val = val
                        break

    # 2. Content fallback for desc_val if missing
    if not desc_val:
        candidates = [str(v).strip() for v in row.values() if pd.notna(v) and len(str(v).strip()) > 3]
        desc_candidates = [c for c in candidates if ' ' in c or any(char.isalpha() for char in c)]
        if desc_candidates:
            desc_val = max(desc_candidates, key=len)

    return part_val or 'UNKNOWN', desc_val or ''

print("\n=== EXTRACTED FIELD SAMPLES (First 15 Rows) ===")
for idx in range(15):
    row = df.iloc[idx].to_dict()
    p, d = extract_row_fields(row)
    print(f"{idx+1}. PartNo: \"{p}\" | Desc: \"{d}\"")
