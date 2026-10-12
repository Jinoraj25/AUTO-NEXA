import sqlite3
import os

DB_PATH = r"d:\SM0237 Onedrive\OneDrive - TVS Mobility Private Limited\Documents\PROJECT\data\overall_catalogue.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check count before update
cur.execute("SELECT COUNT(*) FROM overall_catalogue WHERE line_code = '201' AND brand_name = 'FIAT / JEEP'")
fiat_jeep_201_count = cur.fetchone()[0]
print(f"Found {fiat_jeep_201_count:,} rows with line_code = '201' and brand_name = 'FIAT / JEEP'")

# Update database
print("Updating brand_name = 'TATA' for all line_code = '201'...")
cur.execute("UPDATE overall_catalogue SET brand_name = 'TATA' WHERE line_code = '201' AND brand_name = 'FIAT / JEEP'")
updated_rows = cur.rowcount
conn.commit()

print(f"Successfully updated {updated_rows:,} rows in overall_catalogue.db!")

# Verify total brands and SKU counts
cur.execute("SELECT COUNT(DISTINCT brand_name) FROM overall_catalogue WHERE brand_name IS NOT NULL AND brand_name != ''")
distinct_brands = cur.fetchone()[0]

cur.execute("SELECT COUNT(DISTINCT line_code_part_number) FROM overall_catalogue WHERE brand_name IS NOT NULL AND brand_name != ''")
global_unique_skus = cur.fetchone()[0]

cur.execute("""
    SELECT SUM(unique_sku_count) FROM (
        SELECT brand_name, COUNT(DISTINCT line_code_part_number) AS unique_sku_count
        FROM overall_catalogue
        WHERE brand_name IS NOT NULL AND brand_name != ''
        GROUP BY brand_name
    )
""")
sum_brand_skus = cur.fetchone()[0]

conn.close()

print(f"\nPost-Update Database Metrics:")
print(f"Total Standardized Brands: {distinct_brands}")
print(f"Global Unique SKUs: {global_unique_skus:,}")
print(f"Sum of Brand-Wise Unique SKUs: {sum_brand_skus:,}")
print(f"Difference: {sum_brand_skus - global_unique_skus}")
