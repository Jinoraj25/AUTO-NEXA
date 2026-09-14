import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import json

print("1. Reading RF Sales Dataset...")
df_rf = pd.read_excel('C:/Users/SM0237/Downloads/Mapped_RF_SALES_JAN26-AUG26_Output.xlsx')
df_rf['SaleValue'] = pd.to_numeric(df_rf['SaleValue'], errors='coerce').fillna(0)
df_rf['Margin'] = pd.to_numeric(df_rf['Margin'], errors='coerce').fillna(0)
df_rf['SaleQty'] = pd.to_numeric(df_rf['SaleQty'], errors='coerce').fillna(1)
df_rf['MonthStr'] = pd.to_datetime(df_rf['Month'], errors='coerce').dt.strftime('%b').str.upper()

month_map = {'JAN':'JAN', 'FEB':'FEB', 'MAR':'MAR', 'APR':'APR', 'MAY':'MAY', 'JUN':'JUN', 'JUL':'JUL', 'AUG':'AUG'}
df_rf['MonthKey'] = df_rf['MonthStr'].map(month_map).fillna('AUG')
df_rf['RegionKey'] = df_rf['Region'].astype(str).str.upper().str.strip()
df_rf['CategoryKey'] = df_rf['Category'].astype(str).str.strip()
df_rf['AggKey'] = df_rf['Aggregate'].astype(str).str.upper().str.strip()
df_rf['CompKey'] = df_rf['Component'].astype(str).str.upper().str.strip()
df_rf['VendorKey'] = df_rf['Categoey'].astype(str).str.upper().str.strip()
df_rf['MakeKey'] = df_rf['Brand'].astype(str).str.upper().str.strip()
df_rf['InvoiceKey'] = df_rf['InvoiceNumber'].astype(str)
df_rf['ChannelKey'] = 'RF'

print("2. Reading CF Sales & Catalogue Mapping Dataset...")
df_cf_sales = pd.read_excel('C:/Users/SM0237/Downloads/CF SALES JAN\'26-AUG\'26.xlsb', engine='pyxlsb')
df_cf_mapped = pd.read_excel('C:/Users/SM0237/Downloads/CF SALES JAN-AUG MAPPED.xlsx')

df_cf = df_cf_sales.copy()
df_cf['Aggregate'] = df_cf_mapped['Aggregate']
df_cf['Sub-Aggregate'] = df_cf_mapped['Sub-Aggregate']
df_cf['Component'] = df_cf_mapped['Component']
df_cf['Category'] = df_cf_mapped['Category']
df_cf['Remarks'] = df_cf_mapped['Remarks']

df_cf['SaleValue'] = pd.to_numeric(df_cf['Total Sale Amount'], errors='coerce').fillna(0)
df_cf['Margin'] = pd.to_numeric(df_cf['Margin'], errors='coerce').fillna(0)
df_cf['SaleQty'] = pd.to_numeric(df_cf['Sale Qty'], errors='coerce').fillna(1)

# Convert Month serial date to string
df_cf['Date'] = pd.to_datetime(df_cf['Month'], origin='1899-12-30', unit='D')
df_cf['MonthKey'] = df_cf['Date'].dt.strftime('%b').str.upper()

# State to Region mapping
state_to_region = {
    'TAMIL NADU': 'SOUTH', 'KARNATAKA': 'SOUTH', 'KERALA': 'SOUTH', 'TELANGANA': 'SOUTH', 'ANDHRA PRADESH': 'SOUTH',
    'MAHARASHTRA': 'WEST', 'GUJARAT': 'WEST', 'GOA': 'WEST',
    'DELHI': 'NORTH', 'HARYANA': 'NORTH', 'UTTAR PRADESH': 'NORTH', 'MADHYA PRADESH': 'NORTH', 'RAJASTHAN': 'NORTH', 'PUNJAB': 'NORTH',
    'WEST BENGAL': 'EAST', 'ODISHA': 'EAST', 'ASSAM': 'EAST', 'BIHAR': 'EAST', 'JHARKHAND': 'EAST'
}
df_cf['StateUpper'] = df_cf['Outlet State'].astype(str).str.upper().str.strip()
df_cf['RegionKey'] = df_cf['StateUpper'].map(state_to_region).fillna('SOUTH')
df_cf['CategoryKey'] = df_cf['Category'].astype(str).str.strip()
df_cf['AggKey'] = df_cf['Aggregate'].astype(str).str.upper().str.strip()
df_cf['CompKey'] = df_cf['Component'].astype(str).str.upper().str.strip()
df_cf['VendorKey'] = df_cf['Source Type'].astype(str).str.upper().str.strip().replace({'': 'OEM', 'NAN': 'OEM'})
df_cf['MakeKey'] = df_cf['Make'].astype(str).str.upper().str.strip()
df_cf['InvoiceKey'] = df_cf['Invoice No'].astype(str)
df_cf['ChannelKey'] = 'CF'

# Function to classify Make into MHMT (MARUTI, HYUNDAI, MAHINDRA, TATA) or OTHERS
def classify_make(m):
    m_str = str(m).upper()
    if 'MARUTI' in m_str or 'SUZUKI' in m_str:
        return 'MARUTI'
    elif 'HYUNDAI' in m_str:
        return 'HYUNDAI'
    elif 'MAHINDRA' in m_str:
        return 'MAHINDRA'
    elif 'TATA' in m_str:
        return 'TATA'
    else:
        return 'OTHERS'

df_rf['MakeGroup'] = df_rf['MakeKey'].apply(classify_make)
df_cf['MakeGroup'] = df_cf['MakeKey'].apply(classify_make)

print(f"Loaded {len(df_rf):,} RF rows & {len(df_cf):,} CF rows!")

months = ['AUG', 'JUL', 'JUN', 'MAY', 'APR', 'MAR', 'FEB', 'JAN']
pms_patterns = {
    'Engine Oil': ['ENGINE OIL'],
    'Brake Pads & Discs': ['BRAKE PAD', 'BRAKE DISC', 'BRAKE ROTOR', 'BRAKE SHOE'],
    'Clutch Disc & Cover': ['CLUTCH DISC', 'CLUTCH COVER', 'CLUTCH SET', 'CLUTCH PLATE'],
    'Filters': ['AIR FILTER', 'OIL FILTER', 'CABIN FILTER', 'FUEL FILTER'],
    'Coolant & Fluids': ['COOLANT', 'BRAKE FLUID', 'RADIATOR COOLANT'],
    'Spark / Glow Plugs': ['SPARK PLUG', 'GLOW PLUG']
}
req_aggs = ['BRAKE SYSTEM', 'CLUTCH SYSTEM', 'FILTERS', 'SUSPENSION', 'STEERING', 'LIGHTING']

def process_slice(sub_df):
    tot_rev = float(sub_df['SaleValue'].sum())
    tot_mar = float(sub_df['Margin'].sum())
    tot_units = int(sub_df['SaleQty'].sum())
    tot_inv = int(sub_df['InvoiceKey'].nunique())
    mar_pct = round((tot_mar / (tot_rev or 1)) * 100, 2)

    # 1. Category Sales
    c_sales = sub_df.groupby('CategoryKey')['SaleValue'].sum().to_dict()
    categorySales = {
        'Mechanical Parts': round(float(c_sales.get('Mechanical Parts', 0)), 2),
        'Body Parts': round(float(c_sales.get('Body Parts', 0)), 2),
        'Lubes': round(float(c_sales.get('Lubes', 0)), 2),
        'Electrical Parts': round(float(c_sales.get('Electrical Parts', 0)), 2),
        'Accessories': round(float(c_sales.get('Accessories', 0)), 2)
    }

    # 2. Region Sales
    r_df = sub_df.groupby('RegionKey').agg(
        revenue=('SaleValue', 'sum'),
        margin=('Margin', 'sum'),
        invoices=('InvoiceKey', 'nunique')
    ).reset_index()

    regionSales = []
    for _, r_row in r_df.iterrows():
        reg = r_row['RegionKey']
        r_rev = float(r_row['revenue'])
        r_mar = float(r_row['margin'])
        r_inv = int(r_row['invoices'])
        r_rev_pct = round((r_rev / (tot_rev or 1)) * 100, 2)
        r_mar_pct = round((r_mar / (r_rev or 1)) * 100, 2)
        regionSales.append({
            'region': reg,
            'revenue': round(r_rev, 2),
            'margin': round(r_mar, 2),
            'marginPct': r_mar_pct,
            'revenuePct': r_rev_pct,
            'invoices': r_inv
        })
    regionSales.sort(key=lambda x: x['revenue'], reverse=True)

    # 3. Vehicle Make Sales (MHMT vs OTHERS)
    make_groups = ['MARUTI', 'HYUNDAI', 'MAHINDRA', 'TATA', 'OTHERS']
    make_breakdown = []
    mhmt_rev = 0
    mhmt_units = 0

    for mk in make_groups:
        mk_df = sub_df[sub_df['MakeGroup'] == mk]
        m_rev = float(mk_df['SaleValue'].sum())
        m_mar = float(mk_df['Margin'].sum())
        m_qty = int(mk_df['SaleQty'].sum())
        m_share = round((m_rev / (tot_rev or 1)) * 100, 2)
        m_mar_pct = round((m_mar / (m_rev or 1)) * 100, 2)

        if mk in ['MARUTI', 'HYUNDAI', 'MAHINDRA', 'TATA']:
            mhmt_rev += m_rev
            mhmt_units += m_qty

        make_breakdown.append({
            'make': mk,
            'isMhmt': mk in ['MARUTI', 'HYUNDAI', 'MAHINDRA', 'TATA'],
            'revenue': round(m_rev, 2),
            'margin': round(m_mar, 2),
            'marginPct': m_mar_pct,
            'sharePct': m_share,
            'units': m_qty
        })

    make_data = {
        'mhmtRevenue': round(mhmt_rev, 2),
        'mhmtSharePct': round((mhmt_rev / (tot_rev or 1)) * 100, 2),
        'mhmtUnits': mhmt_units,
        'othersRevenue': round(tot_rev - mhmt_rev, 2),
        'othersSharePct': round(((tot_rev - mhmt_rev) / (tot_rev or 1)) * 100, 2),
        'items': make_breakdown
    }

    # 4. PMS Components
    pms_breakdown = []
    total_pms_rev = 0
    total_pms_qty = 0

    for pms_name, comp_list in pms_patterns.items():
        pattern_regex = '|'.join(comp_list)
        pms_df = sub_df[sub_df['CompKey'].str.contains(pattern_regex, case=False, na=False)]
        p_rev = float(pms_df['SaleValue'].sum())
        p_mar = float(pms_df['Margin'].sum())
        p_qty = int(pms_df['SaleQty'].sum())
        p_share = round((p_rev / (tot_rev or 1)) * 100, 2)
        p_mar_pct = round((p_mar / (p_rev or 1)) * 100, 2)

        total_pms_rev += p_rev
        total_pms_qty += p_qty

        pms_breakdown.append({
            'name': pms_name,
            'revenue': round(p_rev, 2),
            'margin': round(p_mar, 2),
            'marginPct': p_mar_pct,
            'sharePct': p_share,
            'units': p_qty
        })

    pms_breakdown.sort(key=lambda x: x['revenue'], reverse=True)

    pms_data = {
        'totalPmsRevenue': round(total_pms_rev, 2),
        'pmsSharePct': round((total_pms_rev / (tot_rev or 1)) * 100, 2),
        'totalPmsUnits': total_pms_qty,
        'items': pms_breakdown
    }

    # 5. Mechanical Aggregates
    mech_aggs_list = []
    for agg in req_aggs:
        agg_df = sub_df[sub_df['AggKey'] == agg]
        a_rev = float(agg_df['SaleValue'].sum())
        a_mar = float(agg_df['Margin'].sum())
        a_qty = int(agg_df['SaleQty'].sum())
        a_share = round((a_rev / (tot_rev or 1)) * 100, 2)
        a_mar_pct = round((a_mar / (a_rev or 1)) * 100, 2)
        top_comp = agg_df['CompKey'].mode().tolist()[0] if not agg_df.empty else 'GENERAL'

        mech_aggs_list.append({
            'aggregate': agg,
            'revenue': round(a_rev, 2),
            'margin': round(a_mar, 2),
            'marginPct': a_mar_pct,
            'sharePct': a_share,
            'units': a_qty,
            'topComponent': top_comp
        })

    mech_aggs_list.sort(key=lambda x: x['revenue'], reverse=True)

    return {
        'hasData': True if tot_rev > 0 else False,
        'totalRevenue': round(tot_rev, 2),
        'totalMargin': round(tot_mar, 2),
        'marginPct': mar_pct,
        'totalUnits': tot_units,
        'totalInvoices': tot_inv,
        'categorySales': categorySales,
        'regionSales': regionSales,
        'makeSales': make_data,
        'pmsSales': pms_data,
        'mechAggregatesSales': mech_aggs_list
    }

cache_data = {}

# MoM Trend for ALL, RF, CF
mom_trend = []
for m in reversed(months):
    m_df = pd.concat([df_rf[df_rf['MonthKey'] == m], df_cf[df_cf['MonthKey'] == m]])
    rev = float(m_df['SaleValue'].sum())
    mar = float(m_df['Margin'].sum())
    mar_pct = round((mar / (rev or 1)) * 100, 2)
    mom_trend.append({'month': m, 'revenue': round(rev, 2), 'margin': round(mar, 2), 'marginPct': mar_pct})

for m_idx, m in enumerate(months):
    m_rf = df_rf[df_rf['MonthKey'] == m]
    m_cf = df_cf[df_cf['MonthKey'] == m]
    m_all = pd.concat([m_rf, m_cf])

    # MoM Growth for ALL
    prev_m = months[m_idx + 1] if m_idx + 1 < len(months) else None
    prev_rf = df_rf[df_rf['MonthKey'] == prev_m] if prev_m else m_rf
    prev_cf = df_cf[df_cf['MonthKey'] == prev_m] if prev_m else m_cf
    prev_all = pd.concat([prev_rf, prev_cf])

    res_all = process_slice(m_all)
    res_rf = process_slice(m_rf)
    res_cf = process_slice(m_cf)

    prev_all_rev = float(prev_all['SaleValue'].sum())
    prev_rf_rev = float(prev_rf['SaleValue'].sum())
    prev_cf_rev = float(prev_cf['SaleValue'].sum())

    res_all['momRevenueGrowth'] = round(((res_all['totalRevenue'] - prev_all_rev) / (prev_all_rev or 1)) * 100, 2)
    res_rf['momRevenueGrowth'] = round(((res_rf['totalRevenue'] - prev_rf_rev) / (prev_rf_rev or 1)) * 100, 2)
    res_cf['momRevenueGrowth'] = round(((res_cf['totalRevenue'] - prev_cf_rev) / (prev_cf_rev or 1)) * 100, 2)

    cache_data[f'{m}_ALL'] = res_all
    cache_data[f'{m}_RF'] = res_rf
    cache_data[f'{m}_CF'] = res_cf

final_cache = {
    'availableMonths': months,
    'defaultMonth': 'AUG',
    'momTrend': mom_trend,
    'data': cache_data
}

with open('data/sales_cache.json', 'w', encoding='utf-8') as f:
    json.dump(final_cache, f, indent=2)

print("Successfully regenerated data/sales_cache.json with Vehicle Make (MHMT vs Others) sales data!")
