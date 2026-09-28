import pandas as pd, json, re

csv_path = r"C:\Users\SM0237\Downloads\Mapped_Catalogue_Export_2026-09-28.csv"
df = pd.read_csv(csv_path, low_memory=False)
print(f"Loaded {len(df):,} rows from {csv_path}")
print("Columns:", df.columns.tolist())

# Load TVS Master
with open('data/aggregate_master_rules.json', 'r') as f:
    master_data = json.load(f)
master = master_data.get('aggregateMaster', [])
print(f"Loaded {len(master)} TVS Aggregate Master entries.")

# Test exact matching of descriptions from user's file against JS token matching logic
tokens_map = {}
for m in master:
    comp = str(m.get('component', '')).strip()
    sub_agg = str(m.get('subAggregate', '')).strip()
    agg = str(m.get('aggregate', '')).strip()
    cat = str(m.get('category', 'Mechanical Parts')).strip()

    # Index tokens from component
    for tok in re.findall(r'[A-Z0-9]{3,}', comp.upper()):
        if tok not in tokens_map:
            tokens_map[tok] = (agg, sub_agg, comp, cat)

print(f"Built token map with {len(tokens_map)} unique tokens.")

# Test on first 20 rows of user file
print("\n--- Testing First 20 Rows ---")
for idx, r in df.head(20).iterrows():
    pno = str(r.get('Product_Number', '')).strip()
    desc = str(r.get('Product_Description', '')).strip()
    brand = str(r.get('Brand_Name', '')).strip()

    desc_clean = re.sub(r'^\.+', '', desc).strip().upper()
    tokens = re.findall(r'[A-Z0-9]{3,}', desc_clean)

    matched = None
    for t in tokens:
        if t in tokens_map:
            matched = tokens_map[t]
            break

    print(f"Row {idx+1}: Desc='{desc}' -> Clean='{desc_clean}' | Tokens={tokens} | Match={matched}")
