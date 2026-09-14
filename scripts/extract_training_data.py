import os
import json
import pandas as pd
import re

print("Starting training data extraction from mapping_training_data.xlsb...")

excel_file = "mapping_training_data.xlsb"
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)
output_json = os.path.join(output_dir, "trained_mapping_db.json")

def clean_str(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def clean_part_no(val):
    s = clean_str(val).upper()
    return re.sub(r'[^A-Z0-9]', '', s)

part_no_map = {}
aggregate_master = []
sales_sample = []
stock_sample = []
make_stats = {}

with pd.ExcelFile(excel_file, engine='pyxlsb') as xls:
    # 1. AGGREGATE MASTER
    print("Reading AGGREGATE MASTER...")
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

    # Helper for make sheets
    make_sheets = [
        ('MARUTI UNIQUE', 'MARUTI', 'PART_NO', 'DESCRIPTION', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONENT'),
        ('HYUNDAI UNIQUE', 'HYUNDAI', 'PART NUMBER', 'DESCRIPTION', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONANT'),
        ('MAHINDRA UNIQUE', 'MAHINDRA', 'PART_NO', 'DESCRIPTION', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONENT'),
        ('TATA', 'TATA', 'Ln-code-&Partnumber', 'Part-description', 'AGGREGATE', 'SUB-AGGREGATE', 'COMPONENT'),
        ('CATALOGUE UNIQUE', 'GENERIC', 'Product_Number', 'Product_Description', 'Aggregate', 'Sub_Aggregate', 'Components')
    ]

    for sheet, make_name, col_part, col_desc, col_agg, col_sub, col_comp in make_sheets:
        if sheet in xls.sheet_names:
            print(f"Processing sheet {sheet} ({make_name})...")
            df = pd.read_excel(xls, sheet_name=sheet)
            count = 0
            for _, row in df.iterrows():
                raw_part = clean_str(row.get(col_part))
                norm_part = clean_part_no(raw_part)
                desc = clean_str(row.get(col_desc))
                agg = clean_str(row.get(col_agg))
                sub_agg = clean_str(row.get(col_sub))
                comp = clean_str(row.get(col_comp))

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
            make_stats[make_name] = count
            print(f"Indexed {count} unique parts for {make_name}")

    # 2. SALES MAPPED SAMPLE
    if 'SALES MAPPED' in xls.sheet_names:
        print("Processing SALES MAPPED...")
        df_sales = pd.read_excel(xls, sheet_name='SALES MAPPED')
        for idx, row in df_sales.iterrows():
            if idx >= 5000:  # Sample for initial fast load performance
                break
            ln = clean_str(row.get('LN CODE'))
            brand = clean_str(row.get('BRAND'))
            item_code = clean_str(row.get('Item Code'))
            item_name = clean_str(row.get('Item Name'))
            agg = clean_str(row.get('AGGREGATE'))
            sub_agg = clean_str(row.get('SUB-AGGREGATE'))
            comp = clean_str(row.get('COMPONENT'))
            parts_cat = clean_str(row.get('PARTS CATEGORY'))
            
            if item_code or item_name:
                sales_sample.append({
                    "id": f"SLS-{idx+1000}",
                    "lineCode": ln,
                    "brand": brand or "GENERIC",
                    "itemCode": item_code,
                    "itemName": item_name,
                    "aggregate": agg,
                    "subAggregate": sub_agg,
                    "component": comp,
                    "partsCategory": parts_cat,
                    "qty": (idx % 18) + 1,
                    "unitPrice": round(50 + ((idx * 37) % 4500), 2),
                    "invoiceDate": f"2026-08-{(idx % 28) + 1:02d}"
                })
        print(f"Processed {len(sales_sample)} sample sales records.")

    # 3. STOCK MAPPED SAMPLE
    if 'STOCK MAPPED' in xls.sheet_names:
        print("Processing STOCK MAPPED...")
        df_stock = pd.read_excel(xls, sheet_name='STOCK MAPPED')
        for idx, row in df_stock.iterrows():
            if idx >= 2000:
                break
            vals = [clean_str(v) for v in row.values]
            if len(vals) >= 10 and vals[1] and vals[1] != 'BRAND':
                line_code = vals[0]
                brand = vals[1]
                category = vals[2]
                item_code = vals[3]
                item_name = vals[4]
                agg = vals[7] if len(vals) > 7 else ""
                sub_agg = vals[8] if len(vals) > 8 else ""
                comp = vals[9] if len(vals) > 9 else ""

                if item_code:
                    stock_sample.append({
                        "itemCode": item_code,
                        "normPartNo": clean_part_no(item_code),
                        "brand": brand,
                        "category": category,
                        "itemName": item_name,
                        "aggregate": agg,
                        "subAggregate": sub_agg,
                        "component": comp,
                        "currentStock": (idx * 13 % 140) + 5,
                        "unitCost": round(40 + ((idx * 29) % 3800), 2),
                        "binLocation": f"BIN-{(idx%15)+1:02d}-{(idx%8)+1}"
                    })
        print(f"Processed {len(stock_sample)} stock records.")

# Token index building for NLP fallback matching
print("Building keyword token index for NLP fallback mapping...")
desc_tokens = {}
for norm_part, data in part_no_map.items():
    desc = data.get("desc", "")
    comp = data.get("comp", "")
    if desc and comp:
        words = re.findall(r'[A-Z0-9]{3,}', desc.upper())
        for w in words:
            if w not in desc_tokens:
                desc_tokens[w] = {}
            desc_tokens[w][comp] = desc_tokens[w].get(comp, 0) + 1

# Limit token map size for compact JSON payload
compact_tokens = {}
for word, comp_counts in desc_tokens.items():
    if len(word) >= 3:
        best_comp = max(comp_counts.items(), key=lambda x: x[1])[0]
        compact_tokens[word] = best_comp

output_data = {
    "aggregateMaster": aggregate_master,
    "partNoLookup": part_no_map,
    "tokenIndex": compact_tokens,
    "makeStats": make_stats,
    "salesSample": sales_sample,
    "stockSample": stock_sample
}

print(f"Writing dataset to {output_json}...")
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False)

print(f"SUCCESS: Generated {output_json} (Total part numbers indexed: {len(part_no_map)})")
