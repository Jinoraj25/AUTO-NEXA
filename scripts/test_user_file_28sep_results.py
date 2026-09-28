import pandas as pd, json, re

csv_path = r"C:\Users\SM0237\Downloads\Mapped_Catalogue_Export_2026-09-28.csv"
df = pd.read_csv(csv_path, low_memory=False)
records = df.to_dict(orient='records')
print(f"Loaded {len(records):,} records from {csv_path}")

# Load TVS Master
with open('data/aggregate_master_rules.json', 'r') as f:
    master_data = json.load(f)
master = master_data.get('aggregateMaster', [])

part_lookup = {str(m.get('partNo','')).strip().upper().replace('-','').replace('.',''): m for m in master if m.get('partNo')}

# Build Token Index
token_index = {}
for entry in master:
    comp = str(entry.get('component', '')).strip().upper()
    tokens = [t for t in re.findall(r'[A-Z0-9]{3,}', comp) if len(t) >= 3]
    for tok in tokens:
        if tok not in token_index:
            token_index[tok] = entry

print(f"Built token index with {len(token_index)} tokens.")

results = []
for r in records:
    pno = str(r.get('Product_Number', '')).strip()
    desc = str(r.get('Product_Description', '')).strip()
    brand = str(r.get('Brand_Name', '')).strip()

    # Clean description
    desc_clean = re.sub(r'^\.+', '', desc).strip().upper()

    mapped = None
    # 1. Part Lookup
    norm_part = re.sub(r'[^A-Z0-9]', '', pno.upper())
    if norm_part in part_lookup:
        m = part_lookup[norm_part]
        mapped = (m['aggregate'], m['subAggregate'], m['component'], 'EXACT_PART_NO')

    # 2. Token Index matching
    if not mapped and desc_clean:
        tokens = [t for t in re.findall(r'[A-Z0-9]{3,}', desc_clean) if len(t) >= 3]
        for t in tokens:
            if t in token_index:
                m = token_index[t]
                mapped = (m['aggregate'], m['subAggregate'], m['component'], 'NLP_KEYWORD_TOKEN')
                break

    # 3. Fuzzy matching
    if not mapped and desc_clean:
        tokens = [t for t in re.findall(r'[A-Z0-9]{3,}', desc_clean) if len(t) >= 3]
        best_score = 0
        best_entry = None
        for entry in master:
            comp_u = str(entry.get('component', '')).upper()
            sub_u = str(entry.get('subAggregate', '')).upper()
            agg_u = str(entry.get('aggregate', '')).upper()
            score = 0
            for dt in tokens:
                if dt in comp_u: score += 4
                elif dt in sub_u: score += 2
                elif dt in agg_u: score += 1
            if score > best_score:
                best_score = score
                best_entry = entry
        if best_entry and best_score >= 2:
            mapped = (best_entry['aggregate'], best_entry['subAggregate'], best_entry['component'], 'FUZZY_MATCH')

    if not mapped:
        mapped = ('CHILD PARTS', 'BOLT & NUT', 'BOLT', 'FALLBACK')

    results.append(mapped)

res_df = pd.DataFrame(results, columns=['Aggregate', 'SubAggregate', 'Component', 'Method'])
print('\n=== Top 15 Aggregates Mapped ===')
print(res_df['Aggregate'].value_counts().head(15))

print('\n=== Match Method Breakdown ===')
print(res_df['Method'].value_counts())
