import pandas as pd, json, re

# Test files in Downloads
files = [
    r"C:\Users\SM0237\Downloads\FOR MAPPING SALES.xlsx",
    r"C:\Users\SM0237\Downloads\Catalogue_Cleaned_Component_Verified.xlsx",
    r"C:\Users\SM0237\Downloads\VEHICLE MASTER MHMT.xlsx"
]

def simulate_sheetjs_raw(fpath):
    print(f"\n================ File: {fpath} ================")
    df_raw = pd.read_excel(fpath, header=None)
    print(f"Raw Excel shape: {df_raw.shape}")
    print("Top 5 raw rows:")
    print(df_raw.head(5).to_string())

    # Check for header promotion (finding row with column names)
    header_idx = None
    for idx, row in df_raw.head(10).iterrows():
        vals = [str(v).lower().replace(' ', '').replace('_', '') for v in row.values if pd.notna(v)]
        if any(kw in v for v in vals for kw in ['itemcode', 'itemname', 'partno', 'partnumber', 'itemdesc', 'description', 'productnumber', 'productdescription', 'manpart', 'brand']):
            header_idx = idx
            break

    print(f"\nHeader row detected at index: {header_idx}")
    if header_idx is not None:
        headers = [str(v).strip() if pd.notna(v) and str(v).strip() else f"Col_{i}" for i, v in enumerate(df_raw.iloc[header_idx].values)]
        df_clean = df_raw.iloc[header_idx+1:].copy()
        df_clean.columns = headers
        print("Cleaned Columns:", headers)
        print("Cleaned Top 3 rows:")
        print(df_clean.head(3).to_string())
    else:
        print("WARNING: Could not find header row in top 10 rows!")

for f in files:
    try:
        simulate_sheetjs_raw(f)
    except Exception as e:
        print(f"Error reading {f}: {e}")
