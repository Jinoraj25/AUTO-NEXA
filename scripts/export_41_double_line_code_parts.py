import os
import sqlite3
import pandas as pd

DB_PATH = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\data\overall_catalogue.db"
OUTPUT_EXCEL = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\Double_Line_Code_41_Part_Numbers.xlsx"

# 41 Single-Line-Code Part Numbers identified from Sheet_1.xlsx
single_parts_41 = [
    '2450C010000250', '2450C020000250', '2450C030000250', '2450C040000250',
    '2450C050000250', '2450C060000250', '2450C070000250', '2450C080000250',
    '2450C090000250', '2450C100000250', '2450C110000250', '2450C140000250',
    '2450C150000120', '2450C160000122', '2450C170000122', '24533400000210',
    '2453206J295210', '24533360000',    '24532970000210', '24532750000210',
    '24532660000210', '24532490000210', '24532460000250', '2453207R206133',
    '2453207A489210', '2453206J291210', '2453204J279210', '2453204A514210',
    '2453203R197210', '24532020US0210', '2452K933',        '24562326196210',
    '24562410000250', '2456214J283210', '2456231M901210', '2453S80',
    '24541191424210', '24541200000200', '24541460000210', '24549120801210',
    '24541250000120'
]

# Corresponding double line code variants stored in DB
double_parts_41 = [f"245{p}" for p in single_parts_41]

print(f"Connecting to {DB_PATH}...")
conn = sqlite3.connect(DB_PATH)

# Construct SQL IN query for all double line code SKUs
placeholders = ','.join('?' for _ in double_parts_41)
query = f"""
    SELECT 
        line_code AS line_code,
        brand_name,
        line_code_part_number AS db_line_code_part_number_double,
        part_description,
        hsn_code,
        tax_rate,
        price_type,
        sales_uom,
        list_price,
        mrp_price,
        sales_price_group,
        vehicle_segment,
        vehicle_make,
        vehicle_model,
        vehicle_sub_model,
        vehicle_fuel_type,
        vehicle_from_year,
        vehicle_to_year,
        aggregate,
        sub_aggregate,
        components
    FROM overall_catalogue 
    WHERE line_code_part_number IN ({placeholders})
"""

df_db = pd.read_sql_query(query, conn, params=double_parts_41)
conn.close()

print(f"Retrieved {len(df_db):,} records from database for the 41 double line code part numbers.")

# Add Original Single Line Code Part Number column for clarity
mapping = dict(zip(double_parts_41, single_parts_41))
df_db.insert(2, 'original_single_line_code_part_number', df_db['db_line_code_part_number_double'].map(mapping))

# Save to Excel
df_db.to_excel(OUTPUT_EXCEL, index=False)
print(f"Excel file successfully generated at: {OUTPUT_EXCEL}")
print(f"File size: {round(os.path.getsize(OUTPUT_EXCEL)/(1024*1024), 2)} MB")
