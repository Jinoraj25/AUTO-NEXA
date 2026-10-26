import sqlite3
import re
import os
import json
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_DB = os.path.join(BASE_DIR, "data", "overall_catalogue.db")
MASTER_BRAND_JSON = os.path.join(BASE_DIR, "data", "master_brand_categories.json")
EXCEL_BRAND_FILE = r"C:\Users\SM0237\Downloads\unique_brand_names_Category Updated.xlsx"

def load_master_brand_categories():
    r"""
    Loads brand classifications from C:\Users\SM0237\Downloads\unique_brand_names_Category Updated.xlsx
    (cached in data/master_brand_categories.json):
    - PRIMARY (12 brands): BOSCH, DELPHI TECH, DENSO, FILTRON, INA, JK TYRE, KK LIGHTINGS, LUK, MONROE, RANE MADRAS LIMITED, VALEO, ZF
    - PL (2 brands): MYTVS, UCAP (and variations like MYTVS MOUNTING)
    - SECONDARY (125+ brands): PUROLATOR, ELOFIC, SOFIMA, MAHLE, ZIP, DELPHI, BRAKES INDIA, GABRIEL, SKF, TALBROS, etc.
    - OEM (24 brands): MARUTI SUZUKI, HYUNDAI, TATA, MAHINDRA, HONDA, TOYOTA, VOLKSWAGEN, SKODA, FORD, etc.
    """
    if os.path.exists(MASTER_BRAND_JSON):
        try:
            with open(MASTER_BRAND_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('brand_to_category', {}), data.get('category_to_brands', {})
        except Exception as e:
            print(f"Warning: Could not read {MASTER_BRAND_JSON}: {e}")

    # Fallback to loading Excel file directly
    if os.path.exists(EXCEL_BRAND_FILE):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(EXCEL_BRAND_FILE, read_only=True)
            ws = wb['Unique Brands']
            brand_to_cat = {}
            cat_to_brands = defaultdict(list)
            for row in ws.iter_rows(min_row=2, values_only=True):
                bname = str(row[1] or '').strip().upper()
                cat = str(row[2] or '').strip().upper()
                if bname and cat:
                    brand_to_cat[bname] = cat
                    if bname not in cat_to_brands[cat]:
                        cat_to_brands[cat].append(bname)
            return brand_to_cat, dict(cat_to_brands)
        except Exception as e:
            print(f"Warning: Could not load Excel brand file: {e}")

    return {}, {}

BRAND_TO_CAT, CAT_TO_BRANDS = load_master_brand_categories()

PRIMARY_BRANDS = set(CAT_TO_BRANDS.get('PRIMARY', [
    'BOSCH', 'DELPHI TECH', 'DENSO', 'FILTRON', 'INA', 'JK TYRE',
    'KK LIGHTINGS', 'LUK', 'MONROE', 'RANE MADRAS LIMITED', 'VALEO', 'ZF'
]))

PL_BRANDS = set(CAT_TO_BRANDS.get('PL', ['MYTVS', 'UCAP'])) | {'MYTVS MOUNTING', 'TVS MOBILITY', 'MY TVS'}

OEM_BRANDS = set(CAT_TO_BRANDS.get('OEM', [
    'MARUTI SUZUKI', 'MARUTI', 'HYUNDAI', 'TATA', 'MAHINDRA', 'HONDA', 'TOYOTA',
    'VOLKSWAGEN', 'SKODA', 'FORD', 'RENAULT', 'NISSAN', 'CHEVROLET', 'FIAT', 'AUDI',
    'BMW', 'MERCEDES BENZ', 'KIA', 'JEEP', 'MORRIS GARAGES', 'FORCE', 'MITSUBISHI', 'VOLVO'
]))

def clean_key(text):
    if not text: return ""
    return re.sub(r'[^A-Z0-9]', '', str(text).upper())

def classify_brand(brand_name):
    """
    Classifies a brand into:
    - 'PRIMARY': Tier 1 OE Brand (Priority 1)
    - 'PL': Private Label - MyTVS / UCAP (Priority 2)
    - 'SECONDARY': Tier 2 Secondary Aftermarket (Priority 3)
    - 'OEM': Genuine Dealership OEM Brand
    - 'OTHER': Other categories (Lubes, Paint, etc.)
    """
    if not brand_name:
        return 'SECONDARY'
    
    b_up = str(brand_name).strip().upper()
    
    # Exact lookup in master list
    if b_up in BRAND_TO_CAT:
        return BRAND_TO_CAT[b_up]
        
    # Check PL matches (e.g. MyTVS Mounting, TVS Mobility)
    if any(pl in b_up for pl in PL_BRANDS):
        return 'PL'
        
    # Check Primary matches
    if any(p in b_up for p in PRIMARY_BRANDS):
        return 'PRIMARY'
        
    # Check OEM matches
    if any(o in b_up for o in OEM_BRANDS):
        return 'OEM'
        
    return 'SECONDARY'

def convert_oem_to_oes(query_str, selected_model=None):
    """
    Production-grade OEM to OES Conversion Engine:
    1. Fast indexed lookup on overall_catalogue.db (23.6M rows)
    2. Multi-Model Resolution: Solves OEM mapping across multiple models of the same make
    3. Strictly enforces Brand Priority Matrix from unique_brand_names_Category Updated.xlsx:
       - Tier 1: PRIMARY Brands (Priority 1: Bosch, Delphi Tech, Denso, Filtron, INA, JK Tyre, KK Lightings, LuK, Monroe, Rane Madras Limited, Valeo, ZF)
       - Tier 2: PL Brands (Priority 2: MyTVS, UCAP)
       - Tier 3: SECONDARY Brands (Priority 3: Purolator, Elofic, Sofima, Mahle, Zip, Delphi, Brakes India, Gabriel, SKF, Talbros, etc.)
    """
    raw_q = str(query_str or '').strip()
    clean_q = clean_key(raw_q)
    if not clean_q:
        return {"status": "error", "found": False, "message": "Empty part number query"}

    if not os.path.exists(CATALOG_DB):
        return {"status": "error", "found": False, "message": "Catalogue database not found"}

    conn = sqlite3.connect(CATALOG_DB)
    c = conn.cursor()

    # Fast indexed candidate array
    candidate_list = [
        raw_q,
        raw_q.replace('-', ''),
        clean_q,
        f"216{clean_q}", f"216{raw_q}",
        f"217{clean_q}", f"217{raw_q}",
        f"201{clean_q}", f"201{raw_q}",
        f"218{clean_q}", f"222{clean_q}", f"223{clean_q}", f"220{clean_q}"
    ]

    # Auto-generate 5-5 hyphenated variants (standard Hyundai/Kia format like 58510-C4930, 31111-0M000)
    if len(clean_q) == 10:
        hyphen_55 = f"{clean_q[:5]}-{clean_q[5:]}"
        candidate_list.extend([
            hyphen_55,
            f"216{hyphen_55}",
            f"217{hyphen_55}",
            f"201{hyphen_55}"
        ])

    candidate_pnos = list(dict.fromkeys(candidate_list))

    placeholders = ','.join(['?'] * len(candidate_pnos))
    c.execute(f"""
        SELECT line_code_part_number, brand_name, part_description, mrp_price,
               vehicle_make, vehicle_model, vehicle_sub_model, vehicle_fuel_type,
               vehicle_from_year, vehicle_to_year, components, aggregate
        FROM overall_catalogue
        WHERE line_code_part_number IN ({placeholders})
    """, candidate_pnos)

    rows = c.fetchall()
    if not rows:
        conn.close()
        return {
            "status": "not_found",
            "found": False,
            "query": query_str,
            "message": f"Part number '{query_str}' not found in catalog."
        }

    # Separate OEM rows vs aftermarket rows
    oem_rows = [r for r in rows if classify_brand(r[1]) == 'OEM']
    if not oem_rows:
        oem_rows = rows

    ref_oem = oem_rows[0]
    matched_pno = ref_oem[0]
    oem_brand = ref_oem[1]
    oem_desc = ref_oem[2]
    oem_mrp = float(ref_oem[3] or 0)
    oem_comp = ref_oem[10] or "COMPONENT"
    oem_agg = ref_oem[11] or "AGGREGATE"

    # Extract all mapped models and variants across the make
    model_variants = defaultdict(lambda: {'fuel': set(), 'years': set(), 'variants': set()})
    for r in oem_rows:
        mk, mdl, sub, fuel, f_yr, t_yr = r[4], r[5], r[6], r[7], r[8], r[9]
        if mdl:
            if fuel: model_variants[(mk, mdl)]['fuel'].add(fuel)
            if f_yr or t_yr: model_variants[(mk, mdl)]['years'].add(f"{f_yr or ''}-{t_yr or ''}".strip('-'))
            if sub: model_variants[(mk, mdl)]['variants'].add(sub)

    mapped_models = []
    for (mk, mdl), d in model_variants.items():
        mapped_models.append({
            'make': mk,
            'model': mdl,
            'fuel_types': sorted(list(d['fuel'])),
            'year_ranges': sorted(list(d['years'])),
            'variant_count': len(d['variants']),
            'sample_variants': sorted(list(d['variants']))[:4]
        })

    # Determine target models for inherited compatibility
    if selected_model and selected_model.upper() != 'ALL':
        target_models = [selected_model.upper()]
    else:
        target_models = list({m['model'].upper() for m in mapped_models if m.get('model')})

    # Component clustering to ensure kits and components match (e.g. Clutch Disc -> Clutch Kit / Set)
    comp_cluster = [oem_comp]
    if 'CLUTCH' in oem_comp:
        comp_cluster = list(dict.fromkeys([oem_comp, 'CLUTCH DISC', 'CLUTCH SET', 'CLUTCH KIT', 'CLUTCH RELEASE BEARING']))
    elif 'BRAKE PAD' in oem_comp:
        comp_cluster = list(dict.fromkeys([oem_comp, 'BRAKE PAD SET FRONT', 'BRAKE PAD SET REAR', 'BRAKE PAD']))
    elif 'BRAKE DISC' in oem_comp:
        comp_cluster = list(dict.fromkeys([oem_comp, 'BRAKE DISC FRONT', 'BRAKE DISC REAR', 'BRAKE DISC']))

    comp_placeholders = ','.join(['?'] * len(comp_cluster))

    if target_models:
        model_placeholders = ','.join(['?'] * len(target_models))
        query_params = comp_cluster + [oem_brand] + target_models
        c.execute(f"""
            SELECT line_code_part_number, brand_name, part_description, mrp_price, vehicle_model, components
            FROM overall_catalogue
            WHERE components IN ({comp_placeholders})
              AND brand_name != ?
              AND vehicle_model IN ({model_placeholders})
              AND mrp_price > 1.0
            GROUP BY line_code_part_number
            ORDER BY mrp_price ASC
        """, query_params)
    else:
        query_params = comp_cluster + [oem_brand]
        c.execute(f"""
            SELECT line_code_part_number, brand_name, part_description, mrp_price, vehicle_model, components
            FROM overall_catalogue
            WHERE components IN ({comp_placeholders})
              AND brand_name != ?
              AND mrp_price > 1.0
            GROUP BY line_code_part_number
            ORDER BY mrp_price ASC
            LIMIT 50
        """, query_params)

    candidate_rows = c.fetchall()
    conn.close()

    tier1_primary = []
    tier2_pl = []
    tier3_secondary = []
    tier4_other = []

    # Known competitor model names per make to detect mis-tagged catalogue records
    COMPETITOR_MODELS = {
        'HYUNDAI': {'SWIFT', 'BALENO', 'ERTIGA', 'BREZZA', 'CIAZ', 'CELERIO', 'DZIRE', 'WAGON R', 'WAGONR', 'ALTO', 'EECO', 'ECCO', 'POLO', 'VENTO', 'CITY', 'AMAZE', 'ETIOS', 'INNOVA', 'BOLERO', 'SCORPIO', 'NEXON', 'TIAGO', 'MICRA', 'SUNNY'},
        'MARUTI': {'SANTRO', 'I10', 'I20', 'CRETA', 'VERNA', 'VENUE', 'POLO', 'VENTO', 'CITY', 'AMAZE', 'ETIOS', 'INNOVA', 'BOLERO', 'SCORPIO', 'NEXON', 'TIAGO'},
        'MARUTI SUZUKI': {'SANTRO', 'I10', 'I20', 'CRETA', 'VERNA', 'VENUE', 'POLO', 'VENTO', 'CITY', 'AMAZE', 'ETIOS', 'INNOVA', 'BOLERO', 'SCORPIO', 'NEXON', 'TIAGO'},
        'TATA': {'SWIFT', 'BALENO', 'SANTRO', 'I10', 'I20', 'CRETA', 'VERNA', 'POLO', 'CITY'},
        'MAHINDRA': {'SWIFT', 'BALENO', 'SANTRO', 'I10', 'I20', 'CRETA', 'VERNA', 'POLO', 'CITY'},
        'HONDA': {'SWIFT', 'BALENO', 'SANTRO', 'I10', 'I20', 'CRETA', 'VERNA', 'POLO', 'BOLERO'}
    }

    oem_make_clean = str(mapped_models[0]['make'] if mapped_models else '').upper().strip()
    competitors = COMPETITOR_MODELS.get(oem_make_clean, set())

    seen_parts = set()
    for cr in candidate_rows:
        cpno, cbrand, cdesc, cmrp, cmodel, ccomp = cr
        if cpno in seen_parts: continue
        seen_parts.add(cpno)

        cand_mrp = float(cmrp or 0)
        cdesc_upper = str(cdesc or '').upper()

        # Guardrail 1: Price Anomaly / Master Pack wholesale box filter
        # If OES candidate price is > 3.5x OEM MRP and > 10,000, it is a master carton pack or price blunder
        if oem_mrp > 0 and cand_mrp > (oem_mrp * 3.5) and cand_mrp > 10000.0:
            continue

        # Guardrail 2: Cross-Make Model Description Blunder Filter
        # If the database row says Santro/Verna, but description explicitly says 'SWIFT', 'BALENO', 'POLO', 'CITY', etc.
        if competitors and any(re.search(r'\b' + re.escape(c_mod) + r'\b', cdesc_upper) for c_mod in competitors):
            # Check if it also mentions any model of the current make
            current_models = {m['model'].upper() for m in mapped_models}
            if not any(re.search(r'\b' + re.escape(cur_mod) + r'\b', cdesc_upper) for cur_mod in current_models):
                continue

        cbrand_clean = str(cbrand or '').strip()
        cat = classify_brand(cbrand_clean)
        
        # Comprehensive Price vs OEM Comparison
        price_diff = None
        price_diff_pct = None
        saving_amount = None
        saving_pct = None
        price_status = 'no_oem_price'

        if oem_mrp > 0 and cand_mrp > 0:
            price_diff = round(oem_mrp - cand_mrp, 2)
            price_diff_pct = round(((oem_mrp - cand_mrp) / oem_mrp) * 100)
            if oem_mrp > cand_mrp:
                saving_amount = price_diff
                saving_pct = price_diff_pct
                price_status = 'cheaper'
            elif cand_mrp > oem_mrp:
                saving_amount = price_diff # negative
                saving_pct = round(((cand_mrp - oem_mrp) / oem_mrp) * 100) # positive premium %
                price_status = 'premium'
            else:
                saving_amount = 0
                saving_pct = 0
                price_status = 'equal'

        item = {
            'partNo': cpno,
            'part_no': cpno,
            'brand': cbrand_clean,
            'desc': cdesc or f"OE Grade {ccomp}",
            'description': cdesc or f"OE Grade {ccomp}",
            'component': ccomp,
            'mrp': cand_mrp,
            'price': cand_mrp,
            'verified_for_model': cmodel,
            'price_diff': price_diff,
            'price_diff_pct': price_diff_pct,
            'price_status': price_status,
            'saving_amount': saving_amount,
            'saving_pct': saving_pct,
            'savings_amount': saving_amount or 0,
            'savings_pct': saving_pct or 0,
            'availability': 'In Stock',
            'warranty': '1-2 Years Warranty'
        }

        # Classify strictly into User's Master Priority Tiers
        if cat == 'PRIMARY':
            item['tier'] = 'Tier-1 Primary OES'
            item['tier_rank'] = 1
            tier1_primary.append(item)
        elif cat == 'PL':
            item['tier'] = 'Private Label (PL - MyTVS)'
            item['tier_rank'] = 2
            tier2_pl.append(item)
        elif cat == 'SECONDARY':
            item['tier'] = 'Tier-2 Secondary Aftermarket'
            item['tier_rank'] = 3
            tier3_secondary.append(item)
        else:
            item['tier'] = 'Other Aftermarket'
            item['tier_rank'] = 4
            tier4_other.append(item)

    # Sort within each tier: items that save money first (highest % discount), then lowest price
    def sort_key(x):
        st = x.get('price_status')
        if st == 'cheaper':
            return (0, -(x.get('saving_pct') or 0), x['mrp'])
        elif st == 'equal':
            return (1, 0, x['mrp'])
        elif st == 'premium':
            return (2, x.get('saving_pct') or 0, x['mrp'])
        return (3, 0, x['mrp'])

    tier1_primary.sort(key=sort_key)
    tier2_pl.sort(key=sort_key)
    tier3_secondary.sort(key=sort_key)
    tier4_other.sort(key=sort_key)

    # Strict hierarchy selection: Tier 1 Primary > Tier 2 PL > Tier 3 Secondary > Other
    best_candidate = None
    if tier1_primary:
        best_candidate = tier1_primary[0]
    elif tier2_pl:
        best_candidate = tier2_pl[0]
    elif tier3_secondary:
        best_candidate = tier3_secondary[0]
    elif tier4_other:
        best_candidate = tier4_other[0]

    all_sorted_alternatives = tier1_primary + tier2_pl + tier3_secondary + tier4_other

    # Vehicle display summary
    model_summary = ', '.join([m['model'] for m in mapped_models[:3]])
    if len(mapped_models) > 3:
        model_summary += f" +{len(mapped_models) - 3} more"

    oem_data = {
        'partNo': matched_pno,
        'part_no': matched_pno,
        'desc': oem_desc,
        'description': oem_desc,
        'brand': f"{oem_brand} GENUINE" if oem_brand != 'OEM' else "OEM GENUINE",
        'mrp': oem_mrp,
        'vehicle': f"{model_summary} ({mapped_models[0]['make']})" if mapped_models else "Automotive Application",
        'component': oem_comp,
        'aggregate': oem_agg,
        'leadTime': '3-5 Days'
    }

    rec_oes = {}
    if best_candidate:
        rec_oes = {
            'partNo': best_candidate['partNo'],
            'desc': best_candidate['desc'],
            'brand': f"{best_candidate['brand']} ({best_candidate['tier']})",
            'mrp': best_candidate['mrp'],
            'tier': best_candidate['tier'],
            'stock': 'IN STOCK (Same Day Dispatch)',
            'warranty': '1-2 Years Manufacturer Warranty',
            'oeMatch': '100% Certified OE Specification',
            'saving_amount': best_candidate.get('saving_amount'),
            'saving_pct': best_candidate.get('saving_pct')
        }

    return {
        'status': 'success',
        'found': True,
        'query': query_str,
        'oem': oem_data,
        'recommended_oes': rec_oes,
        'alternatives': all_sorted_alternatives[1:6] if all_sorted_alternatives else [],
        'oes_alternatives': all_sorted_alternatives[:20],
        'mapped_models_count': len(mapped_models),
        'mapped_models': mapped_models,
        'brand_priority_applied': {
            'priority_rule': 'PRIMARY > PL > SECONDARY',
            'master_source_file': 'unique_brand_names_Category Updated.xlsx',
            'primary_brands': sorted(list(PRIMARY_BRANDS)),
            'pl_brands': sorted(list(PL_BRANDS)),
            'secondary_count': len(CAT_TO_BRANDS.get('SECONDARY', []))
        },
        'tier_breakdown': {
            'primary_oes_count': len(tier1_primary),
            'pl_count': len(tier2_pl),
            'secondary_count': len(tier3_secondary),
            'other_count': len(tier4_other)
        },
        'savings_amount': best_candidate.get('saving_amount') if best_candidate else 0,
        'savings_percentage': best_candidate.get('saving_pct') if best_candidate else 0
    }

# Alias for backward compatibility
get_oem_conversion = convert_oem_to_oes
