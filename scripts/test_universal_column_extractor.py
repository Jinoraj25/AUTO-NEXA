import pandas as pd, re

files = [
    r"C:\Users\SM0237\Downloads\Mapped_Catalogue_Export_2026-09-28.csv",
    r"C:\Users\SM0237\Downloads\FOR MAPPING SALES.xlsx"
]

def extract_part_no_and_desc(row):
    part_no = ""
    desc = ""
    brand = ""

    # 1. Keyword check
    for k, v in row.items():
        v_str = str(v or '').strip()
        if not v_str or v_str.lower() == 'nan':
            continue
        k_norm = re.sub(r'[^a-z0-9]', '', k.lower())

        if not desc and any(kw in k_norm for kw in ['description', 'desc', 'itemname', 'partname', 'productname', 'title', 'detail', 'specification']):
            desc = v_str
        if not part_no and any(kw in k_norm for kw in ['partnumber', 'productnumber', 'itemcode', 'partno', 'partcode', 'sku', 'manpart', 'material', 'productno', 'productnum']) or k_norm in ['part', 'code']:
            part_no = v_str
        if not brand and any(kw in k_norm for kw in ['brand', 'make', 'vendor', 'oem', 'manufacturer']):
            brand = v_str

    # 2. Content fallback
    if not desc or not part_no:
        entries = [(k, str(v or '').strip()) for k, v in row.items() if str(v or '').strip() and str(v or '').lower() != 'nan' and k != brand]
        if not desc:
            desc_cand = next((v for k, v in entries if (' ' in v or len(v) > 10) and not v.isdigit()), None)
            if desc_cand: desc = desc_cand

        if not part_no:
            part_cand = next((v for k, v in entries if v != desc and re.match(r'^[A-Z0-9\-\.\/]{4,30}$', v, re.I) and re.search(r'\d', v)), None)
            if part_cand: part_no = part_cand

    return part_no, desc, brand

for fpath in files:
    print(f"\n================ File: {fpath} ================")
    if fpath.endswith('.csv'):
        df = pd.read_csv(fpath, low_memory=False)
    else:
        df = pd.read_excel(fpath)

    for idx, r in df.head(5).iterrows():
        p, d, b = extract_part_no_and_desc(r.to_dict())
        print(f"Row {idx+1}: PartNo='{p}' | Desc='{d}' | Brand='{b}'")
