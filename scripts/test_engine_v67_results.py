import pandas as pd, json, re

# Read FOR MAPPING SALES.xlsx
df = pd.read_excel(r'C:\Users\SM0237\Downloads\FOR MAPPING SALES.xlsx')
records = df.to_dict(orient='records')
print(f"Loaded {len(records):,} records from FOR MAPPING SALES.xlsx")

# Simulate DataEngine.processSalesUpload with updated inspectColumnsByContent logic
keys = list(records[0].keys())
print("Keys in upload:", keys)

part_col = None
desc_col = None
brand_col = None

for k in keys:
    k_norm = re.sub(r'[^a-z0-9]', '', k.lower())
    if not desc_col and any(kw in k_norm for kw in ['itemname', 'itemdescription', 'partdescription', 'description', 'itemdesc', 'desc', 'title']):
        desc_col = k
    if not part_col and any(kw in k_norm for kw in ['itemcode', 'partnumber', 'partno', 'itemcoderev', 'partcode', 'sku', 'manpart', 'part']):
        part_col = k
    if not brand_col and any(kw in k_norm for kw in ['brand', 'make', 'vendor', 'oem']):
        brand_col = k

print(f"Detected columns -> partCol: {part_col}, descCol: {desc_col}, brandCol: {brand_col}")

# Load TVS master rules from json
with open('data/aggregate_master_rules.json', 'r') as f:
    master_data = json.load(f)
master = master_data.get('aggregateMaster', [])

part_lookup = {str(m.get('partNo','')).strip().upper().replace('-','').replace('.',''): m for m in master if m.get('partNo')}

results = []
for r in records:
    part_no = str(r.get(part_col, '')).strip()
    desc = str(r.get(desc_col, '')).strip()
    brand = str(r.get(brand_col, '')).strip()

    # Rule matching
    mapped = None
    norm_part = re.sub(r'[^A-Z0-9]', '', part_no.upper())
    if norm_part in part_lookup:
        m = part_lookup[norm_part]
        mapped = (m['aggregate'], m['subAggregate'], m['component'], 'EXACT_PART_NO')

    if not mapped and desc:
        d = desc.upper()
        if 'BRAKE SHOE' in d or 'DRUM BRAKE' in d:
            mapped = ('BRAKE SYSTEM', 'DRUM BRAKE', 'BRAKE SHOE', 'DOMAIN_RULE')
        elif 'DISC PAD' in d or 'BRAKE PAD' in d:
            mapped = ('BRAKE SYSTEM', 'DISC BRAKE', 'BRAKE PAD', 'DOMAIN_RULE')
        elif 'OIL SEAL' in d:
            mapped = ('CHILD PARTS', 'SEALS & GASKETS', 'OIL SEAL', 'DOMAIN_RULE')
        elif 'OIL FILTER' in d:
            mapped = ('ENGINE', 'FILTERS', 'OIL FILTER', 'DOMAIN_RULE')
        elif 'AIR FILTER' in d:
            mapped = ('ENGINE', 'FILTERS', 'AIR FILTER', 'DOMAIN_RULE')
        elif 'FUEL FILTER' in d:
            mapped = ('ENGINE', 'FILTERS', 'FUEL FILTER', 'DOMAIN_RULE')
        elif 'HOSE' in d:
            mapped = ('COOLING SYSTEM', 'RADIATOR & FLUIDS', 'COOLANT & HEATER HOSE', 'DOMAIN_RULE')
        elif 'SPARK PLUG' in d or 'SPARK' in d:
            mapped = ('ELECTRICALS AND ELECTRONICS', 'IGNITION SYSTEM', 'SPARK PLUG', 'DOMAIN_RULE')
        elif 'DISC' in d or 'SHEET' in d or 'ABRASIVE' in d or 'HOOKIT' in d:
            mapped = ('CHILD PARTS', 'GENERAL SPARES', 'HARDWARE & CONSUMABLES', 'DOMAIN_RULE')

    if not mapped and desc:
        tokens = [t for t in re.findall(r'[A-Z0-9]{4,}', desc.upper()) if len(t) >= 4]
        for t in tokens:
            for m in master:
                comp = str(m.get('component','')).upper()
                if t in comp:
                    mapped = (m['aggregate'], m['subAggregate'], m['component'], 'TOKEN_MATCH')
                    break
            if mapped:
                break

    if not mapped:
        mapped = ('CHILD PARTS', 'BOLT & NUT', 'BOLT', 'FALLBACK')

    results.append(mapped)

res_df = pd.DataFrame(results, columns=['Aggregate', 'SubAggregate', 'Component', 'Method'])
print('\n=== Top 15 Aggregates mapped ===')
print(res_df['Aggregate'].value_counts().head(15))

print('\n=== Top 15 Components mapped ===')
print(res_df['Component'].value_counts().head(15))

print('\n=== Match Method Breakdown ===')
print(res_df['Method'].value_counts())
