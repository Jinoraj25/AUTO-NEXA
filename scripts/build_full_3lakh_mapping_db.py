import os
import json
import re
import pandas as pd
import time

t0 = time.time()
print("Starting FULL 439,206 Record Automotive Knowledge Engine Extractor...")

excel_file = "mapping_training_data.xlsb"
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)
output_json = os.path.join(output_dir, "trained_mapping_db.json")
root_json = "trained_mapping_db.json"

def clean_str(val):
    if pd.isna(val): return ""
    s = str(val).strip()
    if s.endswith(".0"): s = s[:-2]
    return s

def clean_part_no(val):
    s = clean_str(val).upper()
    return re.sub(r'[^A-Z0-9]', '', s)

part_no_map = {}
aggregate_master = []
phrase_index = {}
token_index = {}

# Ambiguous single-word tokens to exclude from single-word indexing
DANGEROUS_SINGLE_TOKENS = {
    'OIL', 'BODY', 'CYLINDER', 'HEAD', 'TUBE', 'FLAP', 'JOINT', 'KIT', 'MANIFOLD', 
    'SHOE', 'PAD', 'DISC', 'HOSE', 'INNER', 'OUTER', 'TOP', 'BOTTOM', 'FRONT', 'REAR', 
    'LEFT', 'RIGHT', 'LH', 'RH', 'SET', 'ASSY', 'LINE', 'TYPE', 'PART', 'CAR', 'STD',
    'MINI', 'MAJOR', 'SMALL', 'BIG', 'PL', 'OEM', 'TVS', 'KBX', 'MYTVS', 'RBL', 'WSD'
}

with pd.ExcelFile(excel_file, engine='pyxlsb') as xls:
    # 1. AGGREGATE MASTER
    print("Reading AGGREGATE MASTER (923 taxonomy components)...")
    df_agg = pd.read_excel(xls, sheet_name='AGGREGATE MASTER')
    for _, row in df_agg.iterrows():
        agg = clean_str(row.get('AGGREGATE'))
        sub_agg = clean_str(row.get('SUB-AGGREGATE'))
        comp = clean_str(row.get('COMPONENT'))
        cat = clean_str(row.get('CATEGORY'))
        if comp:
            aggregate_master.append({
                "aggregate": agg,
                "subAggregate": sub_agg,
                "component": comp,
                "category": cat or "Mechanical Parts"
            })
    print(f"Loaded {len(aggregate_master)} aggregate master rules.")

    # 2. BRAND & MAKE SHEETS (MARUTI, HYUNDAI, MAHINDRA, TATA, CATALOGUE, SALES, STOCK)
    make_sheets = [
        ('MARUTI UNIQUE', 'MARUTI', 'PART_NO', 'DESCRIPTION', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONENT'),
        ('HYUNDAI UNIQUE', 'HYUNDAI', 'PART NUMBER', 'DESCRIPTION', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONANT'),
        ('MAHINDRA UNIQUE', 'MAHINDRA', 'PART_NO', 'DESCRIPTION', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONENT'),
        ('TATA', 'TATA', 'Ln-code-&Partnumber', 'Part-description', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONENT'),
        ('CATALOGUE UNIQUE', 'GENERIC', 'Product_Number', 'Product_Description', 'Aggregate', 'Sub_Aggregate', 'Components'),
        ('SALES MAPPED', 'SALES', 'Item Code', 'Item Name', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONENT'),
        ('STOCK MAPPED', 'STOCK', 'Item Code', 'Item Name', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONENT')
    ]

    total_indexed = 0

    for sheet, make_name, col_part, col_desc, col_agg, col_sub, col_comp in make_sheets:
        if sheet in xls.sheet_names:
            print(f"Indexing sheet {sheet} ({make_name})...")
            df = pd.read_excel(xls, sheet_name=sheet)
            cols = [str(c).strip() for c in df.columns]
            
            # Find column names matching flexibility
            actual_part = next((c for c in cols if col_part.lower() in c.lower() or 'part' in c.lower() or 'item code' in c.lower()), None)
            actual_desc = next((c for c in cols if col_desc.lower() in c.lower() or 'desc' in c.lower() or 'name' in c.lower()), None)
            actual_agg = next((c for c in cols if 'agg' in c.lower() and 'sub' not in c.lower()), None)
            actual_sub = next((c for c in cols if 'sub' in c.lower()), None)
            actual_comp = next((c for c in cols if 'comp' in c.lower()), None)

            count = 0
            for _, row in df.iterrows():
                raw_part = clean_str(row.get(actual_part)) if actual_part else ""
                norm_part = clean_part_no(raw_part)
                desc = clean_str(row.get(actual_desc)) if actual_desc else ""
                agg = clean_str(row.get(actual_agg)) if actual_agg else ""
                sub_agg = clean_str(row.get(actual_sub)) if actual_sub else ""
                comp = clean_str(row.get(actual_comp)) if actual_comp else ""

                if not comp: continue

                # Index exact part number
                if norm_part and norm_part not in part_no_map:
                    part_no_map[norm_part] = {
                        "rawPartNo": raw_part,
                        "make": make_name,
                        "desc": desc,
                        "agg": agg,
                        "subAgg": sub_agg,
                        "comp": comp
                    }
                    count += 1

                # Index multi-word phrase (2-gram & 3-gram)
                if desc:
                    words = [w for w in re.split(r'[^A-Z0-9]+', desc.upper()) if len(w) >= 2]
                    for i in range(len(words) - 1):
                        bigram = f"{words[i]} {words[i+1]}"
                        if bigram not in phrase_index:
                            phrase_index[bigram] = comp
                        if i < len(words) - 2:
                            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                            if trigram not in phrase_index:
                                phrase_index[trigram] = comp

                    # Index single high-precision tokens
                    for w in words:
                        if len(w) >= 3 and w not in DANGEROUS_SINGLE_TOKENS and w not in token_index:
                            token_index[w] = comp

            total_indexed += count
            print(f"Indexed {count:,} part numbers from {sheet}.")

db_data = {
    "aggregateMaster": aggregate_master,
    "partNoLookup": part_no_map,
    "phraseIndex": phrase_index,
    "tokenIndex": token_index,
    "stats": {
        "totalIndexedParts": len(part_no_map),
        "totalPhrases": len(phrase_index),
        "totalSingleTokens": len(token_index)
    }
}

print(f"\nWriting database with {len(part_no_map):,} part numbers, {len(phrase_index):,} multi-word phrases, and {len(token_index):,} clean tokens...")

with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(db_data, f, ensure_ascii=False)

with open(root_json, 'w', encoding='utf-8') as f:
    json.dump(db_data, f, ensure_ascii=False)

t1 = time.time()
print(f"SUCCESS! Built 3 Lakh+ Automotive Knowledge Database in {t1-t0:.2f} seconds.")
