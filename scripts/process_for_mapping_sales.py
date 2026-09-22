import os, json, re
import pandas as pd

def map_for_mapping_sales():
    filepath = r'C:\Users\SM0237\Downloads\FOR MAPPING SALES.xlsx'
    out_filepath = r'C:\Users\SM0237\Downloads\FOR MAPPING SALES_MAPPED.xlsx'

    print(f"Loading {filepath}...")
    df = pd.read_excel(filepath)
    print(f"Total Rows: {len(df):,}")

    with open('data/aggregate_master_rules.json', 'r', encoding='utf-8') as f:
        master_rules = json.load(f)['aggregateMaster']

    part_lookup = {}
    if os.path.exists('data/trained_mapping_db.json'):
        with open('data/trained_mapping_db.json', 'r', encoding='utf-8') as f:
            full_db = json.load(f)
            part_lookup = full_db.get('partNoLookup', {})

    print(f"Loaded {len(master_rules)} master rules and {len(part_lookup):,} part lookup genome entries.")

    def clean_part(raw):
        if not raw or pd.isna(raw): return ''
        return str(raw).upper().replace('-', '').replace(' ', '').replace('.', '').replace('/', '')

    fallback_entry = next(m for m in master_rules if m['aggregate'] == 'CHILD PARTS' and m['component'] == 'BOLT')

    def map_single_row(part_no, desc, brand):
        p_norm = clean_part(part_no)
        
        # 1. Exact Part Number Genome Lookup
        if p_norm and p_norm in part_lookup:
            match = part_lookup[p_norm]
            comp_target = match.get('comp', '').upper()
            found = next((m for m in master_rules if m['component'].upper() == comp_target), None)
            if found:
                return {
                    'aggregate': found['aggregate'],
                    'subAggregate': found['subAggregate'],
                    'component': found['component'],
                    'category': found['category'],
                    'confidence': 'HIGH',
                    'score': 98,
                    'method': 'EXACT_PART_NO',
                    'remarks': 'Auto Mapped (Part No Genome Match)'
                }

        # 2. Text NLP Token Matching against 923 TVS Aggregate Master definitions
        d = str(desc or '').upper().strip()
        if d and d != 'NAN':
            d_tokens = [t for t in re.split(r'[^A-Z0-9]+', d) if len(t) >= 3]
            if d_tokens:
                best_score = 0
                best_m = None
                for entry in master_rules:
                    comp_str = entry['component'].upper()
                    sub_str = entry['subAggregate'].upper()
                    agg_str = entry['aggregate'].upper()

                    score = 0
                    for dt in d_tokens:
                        if dt in comp_str: score += 4
                        elif dt in sub_str: score += 2
                        elif dt in agg_str: score += 1

                    if score > best_score:
                        best_score = score
                        best_m = entry

                if best_m and best_score >= 1:
                    return {
                        'aggregate': best_m['aggregate'],
                        'subAggregate': best_m['subAggregate'],
                        'component': best_m['component'],
                        'category': best_m['category'],
                        'confidence': 'HIGH' if best_score >= 4 else 'MEDIUM',
                        'score': 88 if best_score >= 4 else 75,
                        'method': 'NLP_TOKEN_MATCH',
                        'remarks': 'Auto Mapped (Token Master Match)'
                    }

        # 3. Master Fallback
        return {
            'aggregate': fallback_entry['aggregate'],
            'subAggregate': fallback_entry['subAggregate'],
            'component': fallback_entry['component'],
            'category': fallback_entry['category'],
            'confidence': 'LOW',
            'score': 50,
            'method': 'MASTER_FALLBACK',
            'remarks': 'Auto Mapped (Master Fallback)'
        }

    mapped_rows = []
    for _, r in df.iterrows():
        brand = r.get('Brand', '')
        part_no = r.get('Item Code_rev', '')
        desc = r.get('Item Name', '')

        m = map_single_row(part_no, desc, brand)

        row_dict = r.to_dict()
        row_dict['MAPPED_AGGREGATE'] = m['aggregate']
        row_dict['MAPPED_SUB_AGGREGATE'] = m['subAggregate']
        row_dict['MAPPED_COMPONENT'] = m['component']
        row_dict['MAPPED_CATEGORY'] = m['category']
        row_dict['MAPPED_CONFIDENCE'] = m['confidence']
        row_dict['CONFIDENCE_SCORE'] = m['score']
        row_dict['MATCH_METHOD'] = m['method']
        row_dict['MAPPING_REMARKS'] = m['remarks']
        mapped_rows.append(row_dict)

    df_out = pd.DataFrame(mapped_rows)

    print("\n=== MAPPING SUMMARY FOR FOR MAPPING SALES.xlsx ===")
    print(f"Total Rows Mapped: {len(df_out):,}")
    print(f"Unique Aggregates ({df_out['MAPPED_AGGREGATE'].nunique()}):")
    print(df_out['MAPPED_AGGREGATE'].value_counts())
    print("\nMatch Method Distribution:")
    print(df_out['MATCH_METHOD'].value_counts())

    print(f"\nWriting mapped output to {out_filepath}...")
    df_out.to_excel(out_filepath, index=False)
    print("Mapped Excel file created successfully!")

if __name__ == '__main__':
    map_for_mapping_sales()
